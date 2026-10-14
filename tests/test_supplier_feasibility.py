"""Independent frozen arithmetic and failure controls for synthetic promises."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from inventory_intelligence.decision_contrast import compare
from inventory_intelligence.product import archive_digest,load_catalog
from inventory_intelligence.supplier_feasibility import example_profile,promise
from inventory_intelligence.workflow import Journal

ROOT=Path(__file__).resolve().parents[1]
SKU='product-dynamic:a'
WAREHOUSE='product-dynamic:harbor'
CUTOFF='2026-04-06'


class SupplierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=load_catalog(ROOT/'docs/review/dynamic-replay-v1.json.gz')
        cls.controls=json.loads((ROOT/'docs/examples/supplier-feasibility-controls-v1.json').read_text())

    def profile(self,cutoff=CUTOFF):return example_profile(cutoff,SKU,WAREHOUSE)

    def compare(self,**kwargs):
        return compare(self.catalog,CUTOFF,SKU,WAREHOUSE,supplier=kwargs.pop('supplier',self.profile()),**kwargs)

    def test_frozen_calendar_cutoff_and_capacity(self):
        for c in self.controls['calendar_controls']:
            profile=self.profile(c['origin']);profile['receipt_weekdays']=list(range(5))
            r=promise(profile,c['origin'],SKU,WAREHOUSE,c['quantity'],c['lead_days'],c['order_minute'])
            if 'blocked_reason' in c:self.assertEqual(r['reasons'],[c['blocked_reason']])
            else:self.assertEqual((r['status'],r['accepted_day'],r['promised_day']),('feasible',c['accepted_day'],c['promised_day']))

    def test_frozen_common_paid_cost_and_partial_service(self):
        for c in self.controls['saved_harbor_controls']:
            r=self.compare(order_minute=c.get('order_minute',540),
                           deliveries={'actual_proposal':c['deliveries']} if 'deliveries' in c else None)
            arm=r['arms']['actual_proposal']
            self.assertEqual(int(arm['total_cost']),c['total_cost'],c['name'])
            self.assertEqual(arm['cost_components'],dict(purchase='42',setup='4',holding=str(c['holding']),backlog=str(c['backlog_cost'])))
            self.assertEqual((int(arm['immediate_fulfilled']),int(arm['eventual_fulfilled']),int(arm['terminal_backlog'])),
                             (c['immediate'],c['eventual'],c['terminal_backlog']))
            self.assertEqual(r['arms']['no_action']['total_cost'],'18039')
            fulfilled=sum(int(f['quantity']) for d in arm['days'] for f in d['fulfilled'])
            receipts=sum(int(d['receipts']) for d in arm['days'])
            self.assertEqual(10+receipts-fulfilled,int(arm['terminal_stock']))
            self.assertEqual(115-fulfilled,int(arm['terminal_backlog']))

    def test_capacity_blocks_only_infeasible_arm_and_preserves_no_action(self):
        r=self.compare(quantity=18)
        self.assertEqual(r['arms']['alternative']['feasibility']['reasons'],['dispatch_capacity_exceeded'])
        self.assertIsNone(r['arms']['alternative']['total_cost'])
        self.assertEqual(r['arms']['no_action']['total_cost'],'18039')
        self.assertEqual(r['arms']['actual_proposal']['total_cost'],'16281')
        p=self.profile();p['capacity'][0]['reserved']=7
        r=self.compare(supplier=p)
        self.assertIsNone(r['arms']['actual_proposal']['days'])
        self.assertEqual(r['arms']['no_action']['total_cost'],'18039')

    def test_missing_future_wrong_key_and_missing_capacity_block(self):
        missing=promise(None,CUTOFF,SKU,WAREHOUSE,6,2)
        self.assertEqual(missing['reasons'],['supplier_profile_missing'])
        for change,reason in (({'known_day':'2026-04-07'},'supplier_profile_not_yet_known'),
                              ({'sku_id':'other'},'supplier_key_mismatch'),({'capacity':[]},'dispatch_capacity_missing')):
            p=self.profile();p.update(change)
            r=self.compare(supplier=p)
            self.assertEqual(r['arms']['actual_proposal']['feasibility']['reasons'],[reason])
            self.assertIsNone(r['arms']['actual_proposal']['total_cost'])
        blocked=compare(self.catalog,'2026-04-20','product-dynamic:b','product-dynamic:upland',
                        supplier=example_profile('2026-04-20','product-dynamic:b','product-dynamic:upland'))
        self.assertEqual(blocked['status'],'not_assessable');self.assertIsNone(blocked['arms'])

    def test_strict_shapes_and_receipt_paths(self):
        changes=[{'cutoff_minute':True},{'order_weekdays':[]},{'receipt_weekdays':[True]},
                 {'synthetic_only':False},{'extra':1},{'capacity':[dict(day=CUTOFF,capacity=12,reserved=13)]},
                 {'capacity':[dict(day=CUTOFF,capacity=12.0,reserved=0)]},
                 {'capacity':[dict(day=CUTOFF,capacity=12,reserved=0)]*2}]
        for change in changes:
            p=self.profile();p.update(change)
            with self.assertRaises(ValueError,msg=str(change)):self.compare(supplier=p)
        for options in ({'order_minute':True},{'order_minute':1440},{'delay_days':1},
                        {'deliveries':{'unknown':[]}},
                        {'deliveries':{'actual_proposal':[dict(arrival_day='2026-04-07',quantity=6)]}},
                        {'deliveries':{'actual_proposal':[dict(arrival_day='2026-04-08',quantity=5)]}},
                        {'deliveries':{'actual_proposal':[dict(arrival_day='2026-04-08',quantity=True)]}}):
            with self.assertRaises(ValueError,msg=str(options)):self.compare(**options)
        p=self.profile();p['receipt_weekdays']=list(range(5))
        with self.assertRaises(ValueError):self.compare(supplier=p,deliveries={'actual_proposal':[dict(arrival_day='2026-04-11',quantity=6)]})

    def test_source_digest_determinism_and_legacy_results(self):
        before=archive_digest(self.catalog);profile=self.profile();original=deepcopy(profile)
        r=self.compare(quantity=12)
        self.assertEqual(r,self.compare(quantity=12))
        self.assertEqual(archive_digest(self.catalog),before);self.assertEqual(profile,original)
        legacy=compare(self.catalog,CUTOFF,SKU,WAREHOUSE,12)
        for name,arm in legacy['arms'].items():
            self.assertEqual(r['arms'][name]['total_cost'],arm['total_cost'])

    def test_zero_action_decisions_cannot_bypass_journal_budget(self):
        import json
        with TemporaryDirectory() as tmp:
            journal=Journal(Path(tmp)/'journal.sqlite')
            terms=self.profile()
            original=journal.admit_supplier(self.catalog,cutoff=CUTOFF,sku_id=SKU,warehouse_id=WAREHOUSE,supplier=terms,arm='no_action')
            with journal._connection() as conn:
                rows=[]
                for i in range(255):
                    payload=dict(original,id='budget-fixture:'+str(i))
                    rows.append((payload['id'],'synthetic-budget-fixture',json.dumps(payload)))
                conn.executemany('INSERT INTO decisions VALUES (?,?,?)',rows)
            changed=deepcopy(terms);changed['supplier_id']='new-supplier'
            with self.assertRaisesRegex(ValueError,'decision envelope'):
                journal.admit_supplier(self.catalog,cutoff=CUTOFF,sku_id=SKU,warehouse_id=WAREHOUSE,supplier=changed,arm='no_action')
            self.assertEqual(journal.admit_supplier(self.catalog,cutoff=CUTOFF,sku_id=SKU,warehouse_id=WAREHOUSE,supplier=terms,arm='no_action'),original)
            self.assertEqual(len(journal.snapshot(CUTOFF)['decisions']),256)

    def test_conflicting_global_capacity_profiles_do_not_expand_allocations(self):
        with TemporaryDirectory() as tmp:
            journal=Journal(Path(tmp)/'journal.sqlite')
            first=example_profile(CUTOFF,SKU,WAREHOUSE)
            journal.admit_supplier(self.catalog,cutoff=CUTOFF,sku_id=SKU,warehouse_id=WAREHOUSE,supplier=first)
            second_warehouse='product-dynamic:upland'
            different=example_profile(CUTOFF,SKU,second_warehouse)
            for row in different['capacity']:row['capacity']=24
            before=journal.snapshot(CUTOFF)
            with self.assertRaisesRegex(ValueError,'Conflicting shared supplier/day capacity'):
                journal.admit_supplier(self.catalog,cutoff=CUTOFF,sku_id=SKU,warehouse_id=second_warehouse,
                                       supplier=different,quantity=6,arm='alternative')
            self.assertEqual(journal.snapshot(CUTOFF),before)

    def test_journal_bound_promises_partial_eta_and_exact_history(self):
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/'journal.sqlite';journal=Journal(path)
            args=dict(cutoff=CUTOFF,sku_id=SKU,warehouse_id=WAREHOUSE,supplier=self.profile())
            decision=journal.admit_supplier(self.catalog,**args)
            self.assertEqual(decision,journal.admit_supplier(self.catalog,**args))
            self.assertEqual(journal.snapshot(CUTOFF)['orders'][0]['eta'],'2026-04-08')
            with self.assertRaises(ValueError):journal.record(decision_id=decision['id'],event_id='early',kind='receipt',known_day='2026-04-07',quantity=1)
            journal.record(decision_id=decision['id'],event_id='partial',kind='receipt',known_day='2026-04-08',quantity=3)
            journal.record(decision_id=decision['id'],event_id='eta',kind='eta',known_day='2026-04-08',eta='2026-04-10')
            at_day2=journal.snapshot('2026-04-08')
            self.assertEqual((at_day2['orders'][0]['received'],at_day2['orders'][0]['remaining'],at_day2['orders'][0]['eta']),(3,3,'2026-04-10'))
            journal.record(decision_id=decision['id'],event_id='final',kind='receipt',known_day='2026-04-10',quantity=3)
            self.assertEqual(journal.snapshot('2026-04-08'),at_day2)
            self.assertEqual(Journal(path).snapshot('2026-04-10')['received_pieces'],6)
            self.assertEqual(journal.inbound('2026-04-08')[0]['remaining_qty'],3)
            self.assertEqual(journal.inbound('2026-04-10'),[])
            with self.assertRaises(ValueError):journal.admit_supplier(self.catalog,**args,quantity=12,arm='alternative')
            with journal._connection() as conn:
                with self.assertRaises(sqlite3.IntegrityError):conn.execute('DELETE FROM decisions')

    def test_journal_atomic_capacity_and_rejected_admissions(self):
        with TemporaryDirectory() as tmp:
            journal=Journal(Path(tmp)/'journal.sqlite')
            args=dict(cutoff=CUTOFF,sku_id=SKU,warehouse_id=WAREHOUSE,supplier=self.profile())
            for changes in ({'quantity':18,'arm':'alternative'},{'supplier':None}):
                with self.assertRaises(ValueError):journal.admit_supplier(self.catalog,**(args|changes))
            with ThreadPoolExecutor(max_workers=2) as pool:
                admitted=list(pool.map(lambda _:journal.admit_supplier(self.catalog,**args),range(2)))
            self.assertEqual(admitted[0],admitted[1])
            self.assertEqual(journal.snapshot(CUTOFF)['pending_pieces'],6)
            changed=self.profile();changed['capacity'][7]['capacity']=18
            with self.assertRaisesRegex(ValueError,'immutable supplier profile'):
                journal.admit_supplier(self.catalog,cutoff='2026-04-13',sku_id=SKU,
                    warehouse_id=WAREHOUSE,supplier=changed,quantity=6,arm='alternative')
            p=example_profile(CUTOFF,SKU,'product-dynamic:upland');p['capacity'][0]['capacity']=6
            with self.assertRaises(ValueError):journal.admit_supplier(self.catalog,cutoff=CUTOFF,sku_id=SKU,
                warehouse_id='product-dynamic:upland',supplier=p,quantity=6,arm='alternative')
            self.assertEqual(len(journal.snapshot(CUTOFF)['decisions']),1)


if __name__=='__main__':unittest.main()
