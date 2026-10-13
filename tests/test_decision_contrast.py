"""Hand-calculated common-window controls, separate from efficacy evidence."""
from pathlib import Path
from copy import deepcopy
import unittest
from inventory_intelligence.product import load_catalog, archive_digest, _report, normalize_report
from inventory_intelligence.decision_contrast import compare
from inventory_intelligence.planner_loop import fulfil_fifo


class ContrastTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.catalog=load_catalog(Path(__file__).resolve().parents[1]/'docs/review/dynamic-replay-v1.json.gz')

    def contrast(self,**kwargs):return compare(self.catalog,'2026-04-06','product-dynamic:a','product-dynamic:harbor',**kwargs)

    def test_frozen_paid_cost_and_backlog_oracles(self):
        r=self.contrast(quantity=12)
        expected={'no_action':('18039','100',dict(purchase='30',holding='7',backlog='18000',setup='2')),
                  'actual_proposal':('16281','94',dict(purchase='42',holding='15',backlog='16220',setup='4')),
                  'alternative':('14609','88',dict(purchase='54',holding='31',backlog='14520',setup='4'))}
        self.assertEqual(r['common_days'],33)
        for name,(cost,backlog,components) in expected.items():
            arm=r['arms'][name];self.assertEqual((arm['total_cost'],arm['terminal_backlog'],arm['terminal_stock']),(cost,backlog,'0'))
            self.assertEqual(arm['cost_components'],components)
            self.assertEqual(len(arm['days']),33)
            self.assertTrue(all(d['accepted']=='0' for d in arm['days'][28:]))

    def test_supplier_delay_conserves_pieces_and_full_window(self):
        r=self.contrast(delay_days=3)['arms']['actual_proposal']
        self.assertEqual((r['total_cost'],r['immediate_fulfilled'],r['eventual_fulfilled']),('16373','12','18'))
        self.assertEqual(r['cost_components'],dict(purchase='42',holding='7',backlog='16320',setup='4'))
        self.assertEqual(r['arrival_day'],'5')
        received=sum(int(d['receipts']) for d in r['days'])
        fulfilled=sum(int(f['quantity']) for d in r['days'] for f in d['fulfilled'])
        self.assertEqual(10+received-fulfilled,int(r['terminal_stock']))
        self.assertEqual(112+3-fulfilled,int(r['terminal_backlog']))

    def test_order_constraints_and_strict_controls(self):
        for options in ({'quantity':5},{'quantity':7},{'quantity':True},{'quantity':1.0},{'quantity':2001},{'delay_days':-1},{'delay_days':4},{'delay_days':True}):
            with self.assertRaises(ValueError):self.contrast(**options)
        zero=self.contrast(quantity=0)['arms']
        self.assertEqual(zero['alternative'],zero['no_action'])

    def test_blocked_and_undefined_fill(self):
        blocked=compare(self.catalog,'2026-04-20','product-dynamic:b','product-dynamic:upland',12)
        self.assertIsNone(blocked['arms']);self.assertEqual(blocked['status'],'not_assessable')
        quiet=compare(self.catalog,'2026-04-06','product-dynamic:b','product-dynamic:harbor',12)['arms']
        self.assertIsNone(quiet['actual_proposal']['immediate_fill'])
        self.assertGreater(int(quiet['alternative']['total_cost']),int(quiet['no_action']['total_cost']))

    def test_fifo_old_reserved_before_new_acceptance(self):
        queue=[dict(id='old',day=0,remaining=5),dict(id='reserved',day=1,remaining=3,kind='reservation'),dict(id='new',day=1,remaining=4)]
        stock,remaining,filled,new,total=fulfil_fifo(10,queue,1)
        self.assertEqual((stock,new,total),(0,2,10))
        self.assertEqual([r['quantity'] for r in filled],[5,3,2])
        self.assertEqual(remaining,[dict(id='new',day=1,remaining=2)])

    def test_no_source_or_future_mutation(self):
        before=archive_digest(self.catalog)
        self.assertEqual(self.contrast(quantity=12),self.contrast(quantity=12))
        self.assertEqual(archive_digest(self.catalog),before)

    def test_out_of_window_source_blocks_complete_cost(self):
        c=deepcopy(self.catalog);key=c['cutoffs'][0]['keys'][0];r=deepcopy(_report(c,key['plan_run_id']))
        r['result']['supply']['inbound'][0]['arrival_day']='2026-06-01'
        c['reports'][r['run_id']]['report']=normalize_report(r,c['objects'])
        result=compare(c,'2026-04-06','product-dynamic:a','product-dynamic:harbor')
        self.assertEqual(result['reasons'],['source_outside_common_window']);self.assertIsNone(result['arms'])

if __name__=='__main__':unittest.main()
