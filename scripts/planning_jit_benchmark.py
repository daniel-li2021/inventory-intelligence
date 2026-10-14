#!/usr/bin/env python3
"""Frozen actual-planner JIT experiment on fresh immutable-after-setup inputs."""
import argparse
from datetime import date
import hashlib
import json
import os
from pathlib import Path
from statistics import median
from time import perf_counter

import psycopg
from psycopg.types.json import Jsonb
from inventory_intelligence.reliability import run_checks
from inventory_intelligence.replenishment import run_plan
from inventory_intelligence.copilot_planning import load_planning_run
from scripts.engineering_fixtures import (ORIGIN,ORIGIN_DAY,START,inventory_manifest,
    load_inventory,load_demand,load_supply,source_digest)

ROOT=Path(__file__).resolve().parents[1]


class LocalJitOff:
    """Experiment-only equivalent of the proposed one-line transaction setting."""
    def __init__(self,connection):self.connection=connection
    def __getattr__(self,name):return getattr(self.connection,name)
    def execute(self,query,*args,**kwargs):
        result=self.connection.execute(query,*args,**kwargs)
        if query=="SET LOCAL TIME ZONE 'UTC'":self.connection.execute('SET LOCAL jit=off')
        return result


def semantic(report):
    return {k:v for k,v in report.items() if k not in ('run_id','created_at')}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise ValueError('Refuse to overwrite experiment')
    protocol=json.loads((ROOT/'docs/examples/planning-jit-v1.json').read_text())
    start=perf_counter();samples=[];cells=[]
    with psycopg.connect(os.environ['TEST_DATABASE_URL'],autocommit=True) as owner, psycopg.connect(os.environ['DATABASE_URL'],autocommit=True) as runner:
        if runner.execute('SELECT current_user').fetchone()[0]!='ii_runner':raise ValueError('Restricted runner required')
        runner.execute('SET statement_timeout=30000')
        runtime=dict(server_version=runner.info.server_version,jit=runner.execute('SHOW jit').fetchone()[0],python=os.sys.version)
        for keys in protocol['keys']:
            for state in protocol['states']:
                prefix=f"{protocol['namespace']}:{keys}:{state}"
                manifest=inventory_manifest(prefix,keys,0,opening=20,cutoff=ORIGIN)
                load_inventory(owner,manifest);load_demand(owner,prefix,keys);load_supply(owner,prefix,keys,7)
                owner.execute('ANALYZE')
                trusted=run_checks(runner,ledger_batch_id=prefix+':ledger',snapshot_batch_id=prefix+':snapshot',
                    as_of=ORIGIN,evaluated_at=ORIGIN,code_version=protocol['version'])
                if state!='clean':owner.execute('UPDATE operational_fixture.snapshots SET on_hand_qty=on_hand_qty+1 WHERE row_id=%s',(prefix+':s:0',))
                before=source_digest(owner)
                params=dict(batch_id=prefix+':demand',sku_id=prefix+':sku:0',warehouse_id=prefix+':wh:0',
                    start_day=START,origin_day=ORIGIN_DAY,method='mean',reliability_run_id=trusted['run_id'],
                    supply_batch_id=prefix+':supply:7:0',code_version=protocol['version'])
                reference=None
                for phase,repeats in (('warmup',2),('measured',6)):
                    for pair in range(repeats):
                        arms=protocol['arms'] if pair%2==0 else list(reversed(protocol['arms']))
                        for arm in arms:
                            if perf_counter()-start>protocol['wall_cap_seconds']:raise RuntimeError('Frozen wall budget reached')
                            operation=runner if arm=='default-jit' else LocalJitOff(runner)
                            elapsed=perf_counter();report=run_plan(operation,**params);elapsed=perf_counter()-elapsed
                            if load_planning_run(runner,report['run_id'])!=report:raise AssertionError('Persisted report changed')
                            value=semantic(report)
                            if reference is None:reference=value
                            elif reference!=value:raise AssertionError('Exact JIT semantics changed')
                            if state=='clean' and (report['status']!='assessable' or report['result']['proposed_order_qty']!=30):raise AssertionError('Independent 30-piece oracle failed')
                            if state!='clean' and (report['status']!='not_assessable' or report['result']['proposed_order_qty'] is not None):raise AssertionError('Contradiction did not block')
                            if runner.execute('SHOW jit').fetchone()[0]!=runtime['jit']:raise AssertionError('Transaction JIT setting leaked')
                            samples.append(dict(keys=keys,state=state,phase=phase,pair=pair,arm=arm,seconds=elapsed,
                                report=report,semantic_sha256=hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()))
                after=source_digest(owner)
                if before!=after:raise AssertionError('Experiment changed inputs')
                values={arm:[s['seconds'] for s in samples if s['keys']==keys and s['state']==state and s['phase']=='measured' and s['arm']==arm] for arm in protocol['arms']}
                medians={arm:median(v) for arm,v in values.items()}
                cells.append(dict(keys=keys,state=state,source_before=before,source_after=after,median_seconds=medians,
                    reduction_fraction=1-medians['transaction-local-jit-off']/medians['default-jit'],
                    added_seconds=medians['transaction-local-jit-off']-medians['default-jit']))
        hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('docs/examples/planning-jit-v1.json','scripts/planning_jit_benchmark.py','src/inventory_intelligence/replenishment.py','sql/checks.sql','sql/views.sql')}
        large=next(c for c in cells if c['keys']==1000 and c['state']=='clean')
        small=next(c for c in cells if c['keys']==1 and c['state']=='clean')
        report=dict(version=protocol['version'],protocol=protocol,runtime=runtime,cells=cells,samples=samples,
            source_hashes=hashes,wall_seconds=perf_counter()-start,exact_semantics_equal=True,setting_leak=False,
            adoption_gate_passed=large['reduction_fraction']>=.2 and small['added_seconds']<=.01,
            measurement='Local counterbalanced calls on identical sources; persisted-read audit outside timed interval')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    import gzip
    with args.output.open('xb') as f:f.write(gzip.compress(json.dumps(report,sort_keys=True,separators=(',',':')).encode(),mtime=0))
    print(json.dumps({k:v for k,v in report.items() if k not in ('samples','protocol')},sort_keys=True))


if __name__=='__main__':main()
