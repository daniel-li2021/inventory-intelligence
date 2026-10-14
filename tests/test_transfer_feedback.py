"""Actual PostgreSQL planner feedback from reserved/dispatched/partial transfer evidence."""
from copy import deepcopy
from datetime import date
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from uuid import uuid4
import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict,make_conninfo
from inventory_intelligence.synthetic_replay import replay
from inventory_intelligence.product import _key,_report
from inventory_intelligence.replenishment import run_plan
from inventory_intelligence.transfers import TransferJournal
from inventory_intelligence.supplier_feasibility import example_profile

ROOT=Path(__file__).resolve().parents[1]


class TransferFeedbackTests(unittest.TestCase):
    def test_actual_planner_pending_partial_overdue_and_revised_known_eta(self):
        owner_options=conninfo_to_dict(os.environ['TEST_DATABASE_URL'])
        runner_options=conninfo_to_dict(os.environ['DATABASE_URL'])
        db='ii_transfer_feedback_'+uuid4().hex[:12]
        with psycopg.connect(make_conninfo(**(owner_options|dict(dbname='postgres'))),autocommit=True) as admin:
            admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(db)))
            try:
                with psycopg.connect(make_conninfo(**(owner_options|dict(dbname=db))),autocommit=True) as owner, psycopg.connect(make_conninfo(**(runner_options|dict(dbname=db))),autocommit=True) as runner, TemporaryDirectory() as directory:
                    for name in ('schema.sql','planning_schema.sql'):owner.execute((ROOT/'sql'/name).read_text())
                    source=json.loads((ROOT/'docs/examples/generalization-two-site-v1.json').read_text())[0]
                    catalog=replay(owner,runner,[source])
                    sku='product-coast:sku-0';donor='product-coast:site-1';recipient='product-coast:site-0';cutoff='2026-05-04'
                    _,key=_key(catalog,cutoff,sku,recipient);report=_report(catalog,key['plan_run_id'])
                    self.assertEqual(report['result']['proposed_order_qty'],6)
                    journal=TransferJournal(Path(directory)/'transfer.sqlite')
                    terms=dict(version_id='feedback-transport-v1',known_day=cutoff,transit_days=1,capacity=24,setup_cost=4,per_piece_cost=1)
                    transfer=journal.reserve(catalog,cutoff,sku,donor,recipient,12,terms,example_profile(cutoff,sku,recipient))
                    identity=transfer['id']
                    self.assertEqual(journal.supply_effects(cutoff,sku,donor)['reservations'][0]['remaining_qty'],12)
                    self.assertEqual(journal.supply_effects(cutoff,sku,recipient)['inbound'],[])
                    journal.record(identity,'dispatch','dispatch',cutoff)
                    policy=report['result']['supply']['policy']
                    policy={k:policy[k] for k in ('lead_days','review_days','safety_qty','pack_size','moq')}
                    def plan(saved,batch):
                        context=saved['context']
                        return run_plan(runner,batch_id=context['batch_id'],sku_id=sku,warehouse_id=recipient,
                            start_day=date.fromisoformat(context['start_day']),origin_day=date.fromisoformat(context['origin_day']),
                            method=context['method'],reliability_run_id=context['reliability_run_id'],supply_batch_id=batch,code_version='transfer-feedback-test')
                    journal.publish_supply(owner,batch_id='transfer-pending',sku_id=sku,warehouse_id=recipient,as_of=cutoff,reservations=[],inbound=[],policy=policy)
                    self.assertEqual(plan(report,'transfer-pending')['result']['proposed_order_qty'],0)
                    self.assertEqual(report['result']['proposed_order_qty'],6)
                    journal.record(identity,'partial','receipt','2026-05-05',5)
                    self.assertEqual(journal.supply_effects('2026-05-05',sku,recipient)['inbound'][0]['remaining_qty'],7)
                    # Independent observed count: 3 -1 -1 +5=6; donor80 -12 -1 -1=66.
                    later=deepcopy(source);later.update(version_id='transfer-count-may6',cutoff='2026-05-06',known_at='2026-05-06T07:00:00+00:00')
                    for row in later['keys']:
                        if row['sku_id']==sku:
                            row['stock']=6 if row['warehouse_id']==recipient else 66
                            row['demand'][-2:]=[1,1]
                    new=replay(owner,runner,[source,later])
                    _,newkey=_key(new,'2026-05-06',sku,recipient);newreport=_report(new,newkey['plan_run_id'])
                    self.assertEqual(newreport['result']['proposed_order_qty'],4)
                    journal.publish_supply(owner,batch_id='transfer-overdue',sku_id=sku,warehouse_id=recipient,as_of='2026-05-06',reservations=[],inbound=[],policy=policy)
                    blocked=plan(newreport,'transfer-overdue')
                    self.assertEqual(blocked['status'],'not_assessable');self.assertIsNone(blocked['result']['proposed_order_qty'])
                    self.assertIn('overdue_inbound',blocked['result']['reasons'])
                    journal.record(identity,'eta','eta','2026-05-06',eta='2026-05-07')
                    journal.publish_supply(owner,batch_id='transfer-revised',sku_id=sku,warehouse_id=recipient,as_of='2026-05-06',reservations=[],inbound=[],policy=policy)
                    self.assertEqual(plan(newreport,'transfer-revised')['result']['proposed_order_qty'],0)
                    self.assertEqual(journal.snapshot('2026-05-05')['transfers'][0]['eta'],'2026-05-05')
                    self.assertEqual(journal.snapshot('2026-05-06')['transfers'][0]['eta'],'2026-05-07')
                    # Journal projection inserted supply only; source counts stayed independently declared.
                    self.assertEqual(_report(new,newkey['plan_run_id'])['result']['inventory']['on_hand'],6)
            finally:admin.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(db)))


if __name__=='__main__':unittest.main()
