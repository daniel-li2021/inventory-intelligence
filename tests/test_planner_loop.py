"""Actual restricted PostgreSQL execution versus preimplementation hand controls."""
from copy import deepcopy
import json
import os
from pathlib import Path
import unittest
import tempfile
from uuid import uuid4

import psycopg
from inventory_intelligence.planner_loop import Admission, run_case
from inventory_intelligence.planner_loop_audit import audit_case
from inventory_intelligence.replenishment import run_plan
from inventory_intelligence.workflow import Journal


class PlannerLoopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.owner=psycopg.connect(os.environ['TEST_DATABASE_URL'],autocommit=True)
        cls.runner=psycopg.connect(os.environ['DATABASE_URL'],autocommit=True)
        cls.addClassCleanup(cls.owner.close);cls.addClassCleanup(cls.runner.close)
        if cls.runner.execute('SELECT current_user').fetchone()[0]!='ii_runner':raise RuntimeError('Restricted runner required')
        cls.manual=json.loads((Path(__file__).resolve().parents[1]/'docs/examples/planner-loop-manual-v1.json').read_text())
        cls.corrected=cls.manual|json.loads((Path(__file__).resolve().parents[1]/'docs/examples/planner-loop-errata-v1.json').read_text())
        configs={'clean':{},'zero':dict(demand=[0]*9,history=[0]*28),
            'cold-shortage':dict(initial_stock=0),'spike':dict(demand=[12]+[3]*8),'missing':dict(missing_day_zero=True),
            'notified-delay':dict(first_order_delay=3),'unannounced-delay':dict(first_order_delay=3,notification=False)}
        cls.cases={name:run_case(cls.owner,cls.runner,namespace=str(uuid4()),**(dict(demand=[3]*9)|config)) for name,config in configs.items()}

    def test_seven_manual_quantities_costs_service_and_conservation(self):
        for name,case in self.cases.items():
            with self.subTest(name=name):audit_case(case,self.corrected[name])
        with self.assertRaises(ValueError):audit_case(self.cases['cold-shortage'],self.manual['cold-shortage'])

    def test_idempotent_review_new_uuid_and_conflicting_binding(self):
        report=self.cases['clean']['reviews'][0]['report'];context=report['context'];admission=Admission()
        first,fresh=admission.admit('review',report,context);self.assertTrue(fresh)
        repeated=deepcopy(report);repeated['run_id']=str(uuid4())
        self.assertEqual(admission.admit('review',repeated,context),(first,False))
        for key in ('batch_id','origin','supply_batch_id','reliability_run_id'):
            wrong=context|{key:'wrong'}
            with self.subTest(key=key),self.assertRaises(ValueError):admission.admit('other',report,wrong)
        corrupted=deepcopy(report);corrupted['result']['proposed_order_qty']=18
        with self.assertRaises(ValueError):admission.admit('other',corrupted,context)
        changed=deepcopy(report);changed['input_digest']='0'*64
        with self.assertRaises(ValueError):admission.admit('other',changed,context)
        with self.assertRaises(ValueError):admission.admit('review',report,context,'fixed-18')

    def test_hidden_future_and_delay_never_in_first_origin_sources(self):
        def first(case):
            report=deepcopy(case['reviews'][0]['report']);prefix=case['namespace']
            # Compare exact origin-known quantities and promises, ignoring source namespaces/UUIDs.
            return report['result']['proposed_order_qty'],[r['quantity'] for r in report['result']['training']['days']],report['result']['supply']['inbound']
        for name in ('clean','spike','notified-delay','unannounced-delay'):
            self.assertEqual(first(self.cases[name]),(12,[3]*28,[]))
        self.assertEqual(self.cases['missing']['reviews'][1]['decision']['quantity'],18)
        self.assertIn('overdue_inbound',self.cases['unannounced-delay']['reviews'][1]['report']['result']['reasons'])
        self.assertIn('ineligible_or_unavailable_forecast',self.cases['cold-shortage']['reviews'][2]['report']['result']['reasons'])

    def test_saved_auditor_rejects_conservation_fifo_cost_and_source_corruption(self):
        for mutation in ('stock','receipt','cost','future','summary','source','decision'):
            case=deepcopy(self.cases['clean'])
            if mutation=='stock':case['days'][0]['end_stock']+=1
            elif mutation=='receipt':case['days'][2]['receipts'][0]['quantity']+=1
            elif mutation=='cost':case['days'][0]['cost']['purchase']=0;case['days'][0]['cost']['holding']+=24
            elif mutation=='future':case['sources'][0]['planning']['day_observations'][0]['observed_at']='2099-01-01T00:00:00+00:00'
            elif mutation=='summary':case['summary']['immediate_fulfilled']-=1
            elif mutation=='source':case['reviews'][0]['report']['context']['batch_id']='wrong'
            else:case['reviews'][0]['decision']['id']='wrong'
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):audit_case(case)

    def test_fresh_database_namespace_equivalent_physical_outputs_and_dst(self):
        repeated=run_case(self.owner,self.runner,namespace=str(uuid4()),demand=[3]*9)
        audit_case(repeated,self.manual['clean'])
        self.assertEqual(repeated['summary'],self.cases['clean']['summary'])
        self.assertEqual([(d['end_stock'],d['end_backlog'],d['cost']) for d in repeated['days']],
                         [(d['end_stock'],d['end_backlog'],d['cost']) for d in self.cases['clean']['days']])
        origins=[r['report']['context']['origin'] for r in repeated['reviews']]
        self.assertEqual(origins,['2026-03-07T08:00:00+00:00','2026-03-10T07:00:00+00:00','2026-03-13T07:00:00+00:00'])

    def test_durable_commitment_new_supply_reduces_actual_planner_proposal(self):
        case=self.cases['clean'];report=case['reviews'][0]['report'];context=report['context']
        with tempfile.TemporaryDirectory() as directory:
            journal=Journal(Path(directory)/'journal.sqlite');journal.admit(case,0)
            policy={k:report['result']['supply']['policy'][k] for k in ('lead_days','review_days','safety_qty','pack_size','moq')}
            batch='journal-feedback:'+str(uuid4())
            staged=journal.publish_supply(self.owner,batch_id=batch,sku_id=context['sku_id'],
                warehouse_id=context['warehouse_id'],as_of=context['origin_day'],reservations=[],policy=policy)
            self.assertEqual([r['remaining_qty'] for r in staged['inbound']],[12])
            from datetime import date
            options={k:context[k] for k in ('batch_id','sku_id','warehouse_id','method','reliability_run_id')}
            options.update(start_day=date.fromisoformat(context['start_day']),origin_day=date.fromisoformat(context['origin_day']),supply_batch_id=batch)
            new=run_plan(self.runner,**options)
            self.assertEqual(new['result']['proposed_order_qty'],0)
            self.assertEqual([p['balance_without_order'] for p in new['result']['projection']],['7','4','13','10','7'])
            old=self.owner.execute('SELECT result FROM planning.runs WHERE run_id=%s',(report['run_id'],)).fetchone()[0]
            self.assertEqual(old['proposed_order_qty'],12)


if __name__=='__main__':unittest.main()
