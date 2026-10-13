"""Generate committed-protocol synthetic planner research once in a disposable DB."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess

import psycopg
from inventory_intelligence.planner_loop import run_case
from inventory_intelligence.planner_loop_audit import audit_archive

ROOT=Path(__file__).resolve().parents[1]
SOURCES=('src/inventory_intelligence/planner_loop.py','src/inventory_intelligence/planner_loop_audit.py',
         'scripts/export_planner_loop.py','tests/test_planner_loop.py','docs/CONTRACT_PLANNER_LOOP_V1.md',
         'docs/examples/planner-loop-manual-v1.json','docs/examples/planner-quality-stress-v1.json',
         'docs/examples/planner-loop-errata-v1.json',
         'src/inventory_intelligence/replenishment.py','src/inventory_intelligence/reliability.py',
         'src/inventory_intelligence/demand.py','src/inventory_intelligence/copilot_planning.py',
         'src/inventory_intelligence/planning_runs.py','src/inventory_intelligence/forecasting.py','sql/checks.sql','sql/views.sql')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--audit',action='store_true')
    args=parser.parse_args()
    manual=json.loads((ROOT/'docs/examples/planner-loop-manual-v1.json').read_text())
    manual.update(json.loads((ROOT/'docs/examples/planner-loop-errata-v1.json').read_text()))
    stress=json.loads((ROOT/'docs/examples/planner-quality-stress-v1.json').read_text())
    if args.audit:
        archive=json.loads(gzip.decompress(args.output.read_bytes()))
        for path,expected in archive['source_hashes'].items():
            raw=subprocess.check_output(['git','show',archive['code_commit']+':'+path],cwd=ROOT)
            if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('Historical source binding changed')
        print(json.dumps(audit_archive(archive,manual,stress),sort_keys=True));return
    if args.output.exists():raise ValueError('Refuse to overwrite saved study')
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    hashes={}
    for path in SOURCES:
        raw=(ROOT/path).read_bytes()
        if raw!=subprocess.check_output(['git','show',commit+':'+path],cwd=ROOT):
            raise ValueError('Commit protocol, implementation and oracles before exporting')
        hashes[path]=hashlib.sha256(raw).hexdigest()
    archive=dict(version='planner-loop-evidence-v1',synthetic_only=True,code_commit=commit,source_hashes=hashes,
                 manual={},stress={})
    configurations={
        'clean':{},'zero':dict(demand=[0]*9,history=[0]*28),
        'cold-shortage':dict(initial_stock=0),'spike':dict(demand=[12]+[3]*8),
        'missing':dict(missing_day_zero=True),
        'notified-delay':dict(first_order_delay=3),
        'unannounced-delay':dict(first_order_delay=3,notification=False)}
    with psycopg.connect(os.environ['FIXTURE_DATABASE_URL'],autocommit=True) as owner, \
            psycopg.connect(os.environ['DATABASE_URL'],autocommit=True) as runner:
        if runner.execute('SELECT current_user').fetchone()[0]!='ii_runner':raise ValueError('Restricted runner required')
        archive['runtime']=dict(server_version=runner.info.server_version,runner='ii_runner')
        for name,config in configurations.items():
            archive['manual'][name]=run_case(owner,runner,namespace='manual:'+name,
                code_version=commit,**(dict(demand=[3]*9)|config))
        for trace in stress['traces']:
            archive['stress'][trace['id']]={policy:run_case(owner,runner,
                namespace='stress:'+trace['id']+':'+policy,policy=policy,code_version=commit,
                demand=trace['demand'],history=stress['history'],initial_stock=stress['initial_stock'],
                **{k:trace[k] for k in ('first_order_delay','notification','missing_day_zero')})
                for policy in stress['policies']}
    receipt=audit_archive(archive,manual,stress)
    raw=json.dumps(archive,sort_keys=True,separators=(',', ':')).encode()
    with args.output.open('xb') as f:f.write(gzip.compress(raw,mtime=0))
    print(json.dumps(receipt|dict(output=str(args.output),raw_bytes=len(raw),sha256=hashlib.sha256(args.output.read_bytes()).hexdigest()),sort_keys=True))


if __name__=='__main__':main()
