"""Independent Stage 1 → Stage 2 → Stage 3 PostgreSQL evidence checks."""
from copy import deepcopy
from datetime import timedelta
import os
import subprocess
import sys
import unittest
from unittest.mock import patch
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row

from inventory_intelligence import copilot_planning as cp
from inventory_intelligence.demand import midnight
from inventory_intelligence.planning_runs import run_benchmark, run_forecast
from inventory_intelligence.replenishment import run_plan
from tests.planning_oracle import manual_demand, manual_plan, START


class CopilotPlanning(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.owner = psycopg.connect(os.environ['TEST_DATABASE_URL'],autocommit=True,row_factory=dict_row)
        cls.runner = psycopg.connect(os.environ['DATABASE_URL'],autocommit=True,row_factory=dict_row)
        cls.addClassCleanup(cls.owner.close)
        cls.addClassCleanup(cls.runner.close)

    def plan(self):
        args=manual_plan(self.owner,self.runner,'copilot-plan:'+str(uuid4()))
        return args,run_plan(self.runner,**args)

    def test_exact_proposal_blocked_inputs_and_no_new_history(self):
        args,report=self.plan()
        before=self.owner.execute('SELECT count(*) AS n FROM planning.runs').fetchone()['n']
        validate=cp._validate
        def in_readonly(r):
            self.assertEqual(self.runner.execute('SHOW transaction_read_only').fetchone()['transaction_read_only'],'on')
            self.assertEqual(self.runner.execute('SHOW transaction_isolation').fetchone()['transaction_isolation'],'repeatable read')
            validate(r)
        with patch.object(cp,'_validate',side_effect=in_readonly):
            loaded=cp.load_planning_run(self.runner,report['run_id'])
        self.assertEqual(loaded,report)
        explained=cp.answer_planning(loaded)
        self.assertEqual(explained['status'],'answered')
        self.assertEqual(explained['citations'][0]['data'],report)
        self.assertEqual(explained['citations'][0]['data']['result']['proposed_order_qty'],12)
        self.assertEqual(explained['citations'][0]['data']['result']['unrounded_need'],'10')
        self.assertEqual([d['balance_with_order'] for d in explained['citations'][0]['data']['result']['projection']],['3','4','12','8','4'])
        self.assertIsNone(explained['proposed_order_qty'])
        self.assertEqual(cp.answer_planning(cp.load_planning_run(self.runner,report['run_id'])),explained)
        self.assertEqual(self.owner.execute('SELECT count(*) AS n FROM planning.runs').fetchone()['n'],before)
        blocked=run_plan(self.runner,**(args|dict(supply_batch_id='missing')))
        answer=cp.answer_planning(cp.load_planning_run(self.runner,blocked['run_id']))
        self.assertEqual(answer['citations'][0]['data']['result']['reasons'],['ineligible_or_unavailable_forecast','missing_or_invalid_policy','missing_supply_batch'])
        self.assertIsNone(answer['citations'][0]['data']['result']['proposed_order_qty'])

    def test_shared_horizons_holdout_scores_and_contradiction(self):
        _,args=manual_demand(self.owner,'copilot-benchmark:'+str(uuid4()),values=[1,2,3,4,5,6,7]*12)
        r=run_benchmark(self.runner,**{k:args[k] for k in ('batch_id','sku_id','warehouse_id','start_day','end_day')},
                        group='weekly',evaluated_at=args['known_at']+timedelta(days=10))
        answer=cp.answer_planning(cp.load_planning_run(self.runner,r['run_id']))
        data=answer['citations'][0]['data']
        self.assertEqual(data['context'],r['context'])
        expected={'naive':dict(mae='3',bias='3',wape='3/4'),
                  'mean':dict(mae='12/7',bias='0',wape='3/7'),
                  'seasonal_naive':dict(mae='0',bias='0',wape='0')}
        for h in (7,14,28):
            self.assertEqual(data['result']['selection'][str(h)],dict(scored_points=h,scores=expected))
            self.assertEqual(data['result']['holdout_scores'][str(h)],dict(scored_points=h,scores=expected))
        self.assertEqual(data['result']['chosen_method'],'seasonal_naive')
        corrupt=deepcopy(r)
        corrupt['result']['selection']['28']['scores']['mean']['mae']='0'
        with self.assertRaises(ValueError):
            cp.answer_planning(corrupt)
        forecast=run_forecast(self.runner,**{k:args[k] for k in ('batch_id','sku_id','warehouse_id','start_day')},
                              origin_day=START+timedelta(days=28),method='mean',horizon=7)
        explained=cp.answer_planning(cp.load_planning_run(self.runner,forecast['run_id']))
        self.assertEqual(explained['citations'][0]['data']['result']['predictions'],['4']*7)
        self.assertIsNone(explained['proposed_order_qty'])

    def test_corrupt_orders_float_pieces_and_evidence_limits(self):
        _,r=self.plan()
        for mutate in (lambda x:x['result'].update(proposed_order_qty=6),
                       lambda x:x['result'].update(proposed_order_qty=12.0),
                       lambda x:x['result']['projection'][1].update(inbound=5.0),
                       lambda x:x['result']['projection'][2].update(balance_with_order='999'),
                       lambda x:x['result']['inventory']['run'].update(overall_status='fail'),
                       lambda x:x.update(contract_version='future'),
                       lambda x:x.update(status='not_assessable')):
            corrupt=deepcopy(r); mutate(corrupt)
            with self.assertRaises(ValueError):
                cp.answer_planning(corrupt)
        with patch.object(cp,'MAX_PLANNING_BYTES',1),self.assertRaises(ValueError):
            cp.load_planning_run(self.runner,r['run_id'])
        for run_id in ('not-a-uuid',None,str(uuid4())):
            with self.assertRaises(ValueError):
                cp.load_planning_run(self.runner,run_id)
        with self.assertRaises(ValueError):
            cp.load_planning_run(self.owner,r['run_id'])
        with self.runner.transaction(),self.assertRaises(ValueError):
            cp.load_planning_run(self.runner,r['run_id'])

    def test_assessable_forecast_requires_contiguous_known_training_for_its_key(self):
        _,args=manual_demand(self.owner,'copilot-evidence:'+str(uuid4()),values=[4]*28)
        r=run_forecast(self.runner,**{k:args[k] for k in ('batch_id','sku_id','warehouse_id','start_day')},
                       origin_day=START+timedelta(days=28),method='mean',horizon=7)
        self.assertEqual(cp.answer_planning(r)['citations'][0]['data']['result']['predictions'],['4']*7)
        def duplicate_selected(x):
            series=x['result']['training']; day=series['days'][0]
            day['order_records'].append(deepcopy(day['order_records'][0]))
            day['quantity']=8; day['day_record']['expected_lines']=2
            next(v for v in series['day_versions'] if v['row_id']==day['day_record']['row_id'])['expected_lines']=2
        for mutate in (
                duplicate_selected,
                lambda x:x['result']['training']['days'][0].update(quantity=None),
                lambda x:x['result']['training']['days'][0].update(quantity=True),
                lambda x:x['result']['training']['days'][0].update(reasons=['missing_day_evidence']),
                lambda x:x['result']['training']['days'][0]['day_record'].update(availability='stockout'),
                lambda x:x['result']['training']['days'][0]['day_record'].update(expected_lines=0),
                lambda x:x['result']['training']['days'][0]['order_records'][0].update(accepted_qty=0),
                lambda x:x['result']['training']['days'][0]['order_records'][0].update(observed_at='2026-01-26T08:00:00+00:00'),
                lambda x:x['result']['training']['days'][0]['order_records'][0].update(revision=0),
                lambda x:x['result']['training']['day_versions'].clear(),
                lambda x:x['result']['training']['order_versions'].clear(),
                lambda x:x['result']['training']['batch'].update(status='incomplete'),
                lambda x:x['result']['training']['batch'].update(business_timezone='UTC'),
                lambda x:x['result']['training']['batch'].update(start_day='2025-12-29'),
                lambda x:x['result']['training']['batch'].update(end_day='2026-01-24'),
                lambda x:x['result']['training']['days'][1].update(day=x['result']['training']['days'][0]['day']),
                lambda x:x['result']['training'].update(sku_id='another-sku'),
                lambda x:x['result']['training'].update(known_at='2026-01-26T08:00:00+00:00'),
                lambda x:x['context'].update(origin='2026-01-26T08:00:00+00:00'),
                lambda x:x['context'].update(method='unsupported')):
            corrupt=deepcopy(r); mutate(corrupt)
            with self.assertRaises(ValueError):
                cp.answer_planning(corrupt)
        for field in ('source_system','order_id','line_id'):
            corrupt=deepcopy(r); series=corrupt['result']['training']; order=series['days'][0]['order_records'][0]
            order[field]=' '
            next(v for v in series['order_versions'] if v['row_id']==order['row_id'])[field]=' '
            with self.assertRaises(ValueError):
                cp.answer_planning(corrupt)

    def test_scores_cannot_contradict_cited_truth_or_temporal_fold_schedule(self):
        _,args=manual_demand(self.owner,'copilot-fold-evidence:'+str(uuid4()),values=[4]*84)
        r=run_benchmark(self.runner,**{k:args[k] for k in ('batch_id','sku_id','warehouse_id','start_day','end_day')},
                        group='constant',evaluated_at=args['known_at']+timedelta(days=10))
        self.assertEqual(cp.answer_planning(r)['citations'][0]['data']['result']['selection']['28']['scores']['mean']['mae'],'0')
        # Scores/actual/predictions stay mutually consistent. Only the cited
        # source truth, training or schedule contradicts them.
        for mutate in (
                lambda x:x['result']['candidates'][0]['truth']['days'][0].update(quantity=99),
                lambda x:x['result']['holdout']['truth']['days'][0].update(quantity=None),
                lambda x:x['result']['holdout']['training'].update(known_at=x['context']['evaluated_at']),
                lambda x:x['result']['candidates'][0].update(origin_day=x['context']['holdout_day']),
                lambda x:x['result']['candidates'].clear(),
                lambda x:x['context'].update(end_day='2026-03-23')):
            corrupt=deepcopy(r); mutate(corrupt)
            with self.assertRaises(ValueError):
                cp.answer_planning(corrupt)

    def test_replenishment_cannot_cite_other_or_null_training(self):
        _,r=self.plan()
        for mutate in (
                lambda x:x['result']['forecast']['training']['days'][0].update(quantity=None),
                lambda x:x['result']['training'].update(warehouse_id='another-warehouse'),
                lambda x:x['context'].update(horizon=6)):
            corrupt=deepcopy(r); mutate(corrupt)
            with self.assertRaises(ValueError):
                cp.answer_planning(corrupt)

    def test_cli_planning_reads_persisted_run_and_requires_explicit_intent(self):
        _,r=self.plan()
        args=[sys.executable,'-m','inventory_intelligence.copilot','--language-model','offline',
              '--planning-run-id',r['run_id']]
        good=subprocess.run(args+['--intent','planning'],capture_output=True,text=True)
        self.assertEqual(good.returncode,0,good.stderr)
        import json
        self.assertEqual(json.loads(good.stdout)['citations'][0]['data']['result']['proposed_order_qty'],12)
        for extra in (['--intent','readiness'],['--intent','benchmark']):
            bad=subprocess.run(args+extra,capture_output=True,text=True)
            self.assertEqual(bad.returncode,2)
            self.assertEqual(bad.stdout,'')
