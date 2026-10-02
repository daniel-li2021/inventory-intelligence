"""Repeat synthetic end-to-end benchmarks on an already bootstrapped acceptance DB.

Run acceptance once first. No existing source row is updated or deleted.
"""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
from random import Random
from statistics import median
from time import perf_counter

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from inventory_intelligence import copilot
from inventory_intelligence.demand import midnight
from inventory_intelligence.forecasting import backtest
from inventory_intelligence.planning_runs import exact_json, run_benchmark
from inventory_intelligence.reliability import run_checks
from inventory_intelligence.replenishment import run_plan
from synthetic.demand import START, END
from synthetic.planning_demo import _insert


def source_digest(conn):
    digest = hashlib.sha256()
    for schema in ('operational_fixture', 'planning_input'):
        tables = conn.execute('SELECT tablename FROM pg_tables WHERE schemaname=%s ORDER BY tablename',
                              (schema,)).fetchall()
        for table in tables:
            name = table['tablename']
            rows = conn.execute(sql.SQL('SELECT to_jsonb(t) AS row FROM {}.{} t ORDER BY to_jsonb(t)::text')
                                .format(sql.Identifier(schema), sql.Identifier(name))).fetchall()
            digest.update(json.dumps(exact_json([schema, name, rows]), sort_keys=True).encode())
    return digest.hexdigest()


def load_review_demand(owner):
    batch = 'review-demand-v1'
    if owner.execute('SELECT 1 FROM planning_input.demand_batches WHERE batch_id=%s', (batch,)).fetchone():
        return
    rng = Random(42)
    groups = [('drifting', 'tee-m', [2+i//14 for i in range(180)]),
              ('irregular', 'hoodie-l', [rng.choice([0,0,0,2,5,9]) for _ in range(180)])]
    orders, days = [], []
    for group, sku, values in groups:
        for i, qty in enumerate(values):
            day = START + timedelta(days=i)
            known = midnight(day+timedelta(days=1))
            days.append(dict(row_id=f'{batch}:{group}:day:{i}', batch_id=batch,
                sku_id='planning-demo:'+sku, warehouse_id='planning-demo:harbor', business_day=day,
                revision=1, source_recorded_at=known, observed_at=known, coverage='complete',
                availability='available', expected_lines=int(qty>0)))
            if qty:
                orders.append(dict(row_id=f'{batch}:{group}:order:{i}', batch_id=batch,
                    source_system='review-synthetic', order_id=f'{group}:{i}', line_id='1', revision=1,
                    sku_id='planning-demo:'+sku, warehouse_id='planning-demo:harbor', accepted_qty=qty,
                    status='accepted', accepted_at=midnight(day)+timedelta(hours=12),
                    source_recorded_at=known, observed_at=known))
    with owner.transaction():
        _insert(owner, 'planning_input', 'demand_batches', [dict(batch_id=batch, version_id=batch,
            business_timezone='America/Los_Angeles', start_day=START, end_day=END,
            assembled_at=midnight(END), status='complete', expected_orders=len(orders), expected_days=len(days))])
        _insert(owner, 'planning_input', 'order_versions', orders)
        _insert(owner, 'planning_input', 'day_observations', days)


def run(owner, runner, repeats):
    load_review_demand(owner)
    before = source_digest(owner)
    measurements, results, semantics = {}, {}, {}
    def measure(name, operation):
        start = perf_counter()
        result = operation()
        measurements.setdefault(name, []).append((perf_counter()-start)*1000)
        if name.startswith(('stage1_', 'stage2_')):
            semantic={k:v for k,v in result.items() if k not in ('run_id','created_at')}
            if name in semantics:
                assert semantic==semantics[name], f'{name} changed across repetitions'
            semantics[name]=semantic
        return result
    stock = owner.execute("SELECT run_id FROM reliability.runs WHERE code_version='stage2-demo-v1' ORDER BY run_id LIMIT 1").fetchone()['run_id']
    demo_origin = midnight(END)
    simple = backtest([1,2,3,4,5,6,7]*5)
    for _ in range(repeats):
        stage1 = {}
        for scenario in ('clean', 'combined'):
            report = measure('stage1_'+scenario, lambda: run_checks(runner,
                ledger_batch_id=scenario+':ledger', snapshot_batch_id=scenario+':snapshot',
                as_of=datetime(2026,1,2,tzinfo=timezone.utc), evaluated_at=datetime(2026,1,2,2,tzinfo=timezone.utc),
                code_version='three-stage-review'))
            stage1[scenario] = report
            explained = measure('stage3_'+scenario, lambda: copilot.answer(intent='reliability', report=copilot.load_run(runner,report['run_id'])))
            assert [c['data'] for c in explained['citations'][1:]] == report['findings']
        assert stage1['clean']['overall_status']=='pass' and stage1['clean']['findings']==[]
        assert [(f['rule_id'], f['reason']) for f in stage1['combined']['findings']] == [
            ('R001','quantity_mismatch'),('R002','duplicate_movement_key'),('R004','invalid_transfer')]
        assert [(f['expected_qty'],f['observed_qty'],f['delta_qty']) for f in stage1['combined']['findings'] if f['rule_id']=='R001']==[(25,26,1)]
        results['stage1'] = stage1
        groups = [('constant','tee-m','harbor'),('weekly','hoodie-l','harbor'),
                  ('intermittent','jacket-m','harbor'),('zero','tee-l','harbor'),('blocked','tee-m','upland'),
                  ('drifting','tee-m','harbor'),('irregular','hoodie-l','harbor')]
        benchmarks = []
        for group, sku, wh in groups:
            report = measure('stage2_benchmark_'+group, lambda: run_benchmark(runner,
                batch_id='review-demand-v1' if group in ('drifting','irregular') else 'planning-demo:demand',
                sku_id='planning-demo:'+sku, warehouse_id='planning-demo:'+wh, group=group,
                start_day=START,end_day=END,evaluated_at=demo_origin+timedelta(days=10),code_version='three-stage-review'))
            r = report['result']
            def fold_data(f):
                if f is None:
                    return None
                return dict(origin=f['origin'], status=f['status'], actual=f['actual'], predictions=f['predictions'],
                    training_known_at=f['training']['known_at'],truth_known_at=f['truth']['known_at'],
                    training_quantities=[d['quantity'] for d in f['training']['days']],
                    training_reasons=f['training']['reasons'],truth_reasons=f['truth']['reasons'],
                    day_issues=[dict(day=d['day'],reasons=d['reasons']) for source in ('training','truth')
                                for d in f[source]['days'] if d['reasons']])
            benchmarks.append(dict(group=group,run_id=report['run_id'],input_digest=report['input_digest'],
                status=r['status'],chosen_method=r['chosen_method'],selection=r['selection'],holdout_scores=r['holdout_scores'],
                context=report['context'],folds=[fold_data(f) for f in r['candidates']],holdout=fold_data(r['holdout']),
                included_origins=sum(f['status']=='assessable' for f in r['candidates']),
                excluded_origins=sum(f['status']!='assessable' for f in r['candidates'])))
        results['stage2_benchmarks']=benchmarks
        plans=[]
        for label in ('complete','incomplete'):
            report = measure('stage2_plan_'+label,lambda: run_plan(runner,batch_id='planning-demo:demand',
                sku_id='planning-demo:tee-m',warehouse_id='planning-demo:harbor',start_day=START,origin_day=END,
                method='mean',reliability_run_id=str(stock),supply_batch_id='planning-demo:supply:'+label,
                code_version='three-stage-review'))
            r=report['result']
            plans.append(dict(label=label,run_id=report['run_id'],status=r['status'],proposed_order_qty=r['proposed_order_qty'],
                              reasons=r['reasons'],projection=r['projection']))
        assert [(p['status'],p['proposed_order_qty']) for p in plans]==[('assessable',12),('not_assessable',None)]
        results['stage2_proposals']=plans
        results['stage3_baseline']=measure('stage3_baseline_benchmark',lambda:copilot.answer(intent='benchmark',benchmark=simple))
        if (Path(__file__).resolve().parents[1]/'src/inventory_intelligence/copilot_planning.py').exists():
            from inventory_intelligence.copilot_planning import load_planning_run, answer_planning
            b = measure('stage3_persisted_benchmark',lambda:answer_planning(
                load_planning_run(runner,benchmarks[1]['run_id'])))
            p = measure('stage3_persisted_proposal',lambda:answer_planning(
                load_planning_run(runner,plans[0]['run_id'])))
            assert b['status']==p['status']=='answered'
            assert b['citations'][0]['data']['result']['selection']==benchmarks[1]['selection']
            assert p['citations'][0]['data']['result']['proposed_order_qty']==12
            assert p['proposed_order_qty'] is None
            results['stage3_adapter']='passed: exact stored scores and historical 12-piece proposal; no decision approval'
        else:
            results['stage3_adapter']='unavailable: no persisted planning adapter'
    after=source_digest(owner)
    assert before==after, 'benchmark mutated source inputs'
    return exact_json(dict(business_data='synthetic only; live PostgreSQL execution',repeats=repeats,
        generated_at=datetime.now(timezone.utc),source_digest_before=before,source_digest_after=after,
        timings={name:dict(samples_ms=values,median_ms=median(values),min_ms=min(values),max_ms=max(values))
                 for name,values in measurements.items()},results=results))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    parser.add_argument('--repeats',type=int,default=3)
    args=parser.parse_args()
    if args.repeats<2:
        parser.error('use at least two repetitions')
    with psycopg.connect(os.environ['TEST_DATABASE_URL'],autocommit=True,row_factory=dict_row) as owner, \
         psycopg.connect(os.environ['DATABASE_URL'],autocommit=True,row_factory=dict_row) as runner:
        report=run(owner,runner,args.repeats)
    Path(args.output).write_text(json.dumps(report,sort_keys=True,separators=(',',':'))+'\n')
    print(f'Wrote {args.output}; source digest unchanged; {args.repeats} repetitions')
