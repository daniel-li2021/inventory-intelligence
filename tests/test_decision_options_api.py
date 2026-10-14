"""User-visible source binding, feasibility and local lifecycle negative controls."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from fastapi.testclient import TestClient
from inventory_intelligence.lab_api import create_app
from inventory_intelligence.lab_hosted import HostedLab
from inventory_intelligence.product import load_catalog

CATALOG=Path('docs/review/generalization-v1/generalization-two-site-v1.json.gz')


class DecisionOptionsApiTests(unittest.TestCase):
    def setUp(self):
        self.folder=TemporaryDirectory()
        self.data=load_catalog(CATALOG)
        self.client=TestClient(create_app(catalog_path=CATALOG,journal_path=Path(self.folder.name)/'journal.sqlite'),base_url='http://127.0.0.1')
        self.base=dict(cutoff='2026-05-04',sku_id='product-coast:sku-0',warehouse_id='product-coast:site-0',archive_digest=self.data['digest'])
        self.config=self.client.get('/api/product/decision-context',params=self.base).json()
        self.purchase=self.base|dict(quantity=12,supplier=self.config['supplier'])
        self.transfer=self.purchase|dict(donor_id='product-coast:site-1',transport=self.config['transport'])

    def tearDown(self):self.client.close();self.folder.cleanup()

    def test_feasible_capacity_and_no_action_with_complete_paid_cost(self):
        r=self.client.post('/api/product/supplier-contrast',json=self.purchase)
        self.assertEqual(r.status_code,200)
        result=r.json();self.assertEqual(result['common_days'],33)
        # Purchase18 + setup2 + stock-days30 + backlog-days285*10 =2900.
        self.assertEqual(result['arms']['actual_proposal']['total_cost'],'2900')
        self.assertEqual(result['arms']['actual_proposal']['feasibility']['promised_day'],'2026-05-05')
        blocked=deepcopy(self.purchase)
        for row in blocked['supplier']['capacity']:row['capacity']=5
        arms=self.client.post('/api/product/supplier-contrast',json=blocked).json()['arms']
        self.assertIsNone(arms['actual_proposal']['total_cost'])
        self.assertIsNone(arms['alternative']['days'])
        self.assertIsNotNone(arms['no_action']['total_cost'])
        del blocked['supplier']
        self.assertEqual(self.client.post('/api/product/supplier-contrast',json=blocked).status_code,422)
        bad=self.purchase|dict(archive_digest='0'*64)
        self.assertEqual(self.client.post('/api/product/supplier-contrast',json=bad).status_code,409)
        self.assertEqual(self.client.post('/api/product/supplier-contrast',json=self.purchase|dict(quantity=1.5)).status_code,422)

    def test_real_source_bound_transfer_reservation_dispatch_partial_eta_and_history(self):
        result=self.client.post('/api/product/transfer-contrast',json=self.transfer).json()
        self.assertEqual(result['safe_surplus'],'51')
        self.assertEqual([result['arms'][k]['total_cost'] for k in ('no_action','purchase_only','transfer_before_purchase')],['6763','5154','3533'])
        self.assertEqual(result['arms']['transfer_before_purchase']['donor']['immediate_fulfilled'],'28')
        reserved=self.client.post('/api/product/transfer-reserve',json=self.transfer)
        self.assertEqual(reserved.status_code,200)
        identity=reserved.json()['id']
        self.assertEqual(self.client.post('/api/product/transfer-reserve',json=self.transfer).json()['id'],identity)
        def event(event_id,kind,day,**fields):
            return self.client.post('/api/product/transfer-event',json=dict(archive_digest=self.data['digest'],transfer_id=identity,event_id=event_id,kind=kind,known_day=day,**fields))
        self.assertEqual(event('early','receipt','2026-05-04',quantity=1).status_code,422)
        self.assertEqual(event('dispatch','dispatch','2026-05-04').status_code,200)
        self.assertEqual(event('partial','receipt','2026-05-05',quantity=5).status_code,200)
        self.assertEqual(event('eta','eta','2026-05-06',eta='2026-05-07').status_code,200)
        self.assertEqual(event('excess','receipt','2026-05-07',quantity=8).status_code,422)
        self.assertEqual(event('rest','receipt','2026-05-07',quantity=7).status_code,200)
        def snapshot(day):return self.client.get('/api/product/transfer-history',params=dict(as_of=day,archive_digest=self.data['digest'])).json()
        self.assertEqual(snapshot('2026-05-04')['transfers'][0]['in_transit'],'12')
        self.assertEqual(snapshot('2026-05-05')['transfers'][0]['in_transit'],'7')
        self.assertEqual(snapshot('2026-05-07')['transfers'][0]['received'],'12')
        self.assertEqual(snapshot('2026-05-03')['transfers'],[])
        self.assertEqual(event('back','dispatch','2026-05-04').status_code,422)

    def test_supplier_commitment_receipts_and_unknown_source_block(self):
        admitted=self.client.post('/api/product/supplier-admit',json=self.purchase)
        self.assertEqual(admitted.status_code,200)
        identity=admitted.json()['id']
        self.assertEqual(self.client.post('/api/product/supplier-admit',json=self.purchase).json()['id'],identity)
        args=dict(archive_digest=self.data['digest'],decision_id=identity,event_id='partial',kind='receipt',known_day='2026-05-05',quantity=5)
        self.assertEqual(self.client.post('/api/product/purchase-event',json=args).status_code,200)
        history=self.client.get('/api/product/purchase-history',params=dict(as_of='2026-05-05',archive_digest=self.data['digest'])).json()
        self.assertEqual(history['pending_pieces'],'7')
        blocked=self.transfer|dict(sku_id='product-coast:sku-1')
        self.assertEqual(self.client.post('/api/product/transfer-contrast',json=blocked).json()['status'],'not_assessable')
        self.assertEqual(self.client.post('/api/product/transfer-reserve',json=blocked).status_code,422)
        denied=self.client.post('/api/product/supplier-admit',json=self.purchase,headers={'origin':'https://foreign.test'})
        self.assertEqual(denied.status_code,403)

    def test_review_state_never_suppresses_or_repairs_a_finding(self):
        params=dict(cutoff=self.base['cutoff'],archive_digest=self.data['digest'])
        before=self.client.get('/api/product/insights',params=params).json()
        bindings=self.client.get('/api/product/reviews',params=params).json()['bindings']
        b=bindings[0]
        body=params|dict(finding_id=b['finding_id'],calculation_digest=b['calculation_digest'],event_id='resolved-test',status='resolved',note='Synthetic review; stock risk still visible',reviewed_at=b['known_at'])
        self.assertEqual(self.client.post('/api/product/review',json=body).status_code,200)
        self.assertEqual(self.client.get('/api/product/insights',params=params).json(),before)
        history=self.client.get('/api/product/reviews',params=params).json()['history']
        self.assertEqual(history['reviews'][0]['status'],'resolved')
        self.assertEqual(self.client.post('/api/product/review',json=body|dict(calculation_digest='0'*64)).status_code,422)

    def test_packaged_host_bounds_new_paths_and_keeps_writes_disabled(self):
        with TestClient(HostedLab(create_app(catalog_path=CATALOG)),base_url='http://127.0.0.1') as readonly:
            self.assertEqual(readonly.post('/api/product/transfer-reserve',json=self.transfer).status_code,404)
            self.assertEqual(readonly.post('/api/product/transfer-contrast',json=self.transfer).status_code,200)
            self.assertEqual(readonly.post('/api/product/transfer-contrast',content=b'x'*4097,headers={'content-type':'application/json'}).status_code,413)
            evaluation=readonly.get('/api/product/evaluation').json()
            self.assertEqual(evaluation['reviews'],144)
            self.assertEqual(evaluation['decision_gate_passes'],2)
            self.assertEqual(evaluation['global_winner'],None)


if __name__=='__main__':unittest.main()
