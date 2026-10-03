"""Independent event, economic, conservation and rehashed-mutation oracles."""

from copy import deepcopy
from fractions import Fraction
import unittest

from inventory_intelligence import decision, lost_sales
from scripts.lost_sales_benchmark import summarize, contrast, digest, supplier
from scripts.lost_sales_audit import audit_arm


class LostSalesOracles(unittest.TestCase):
    def record(self,kind='lost_sales'):
        args=dict(method='naive',on_hand=0,lead_days=1,review_days=1,
                  supplier_delays=[0]*4,holding_cost=1,order_cost=2)
        history,demand=[2],[2,2]
        kernel=decision if kind=='backlog' else lost_sales
        simulation=kernel.simulate(history,demand,**args)
        return dict(inputs=dict(history=history,demand=demand,parameters=args,semantics=kind),
            simulation=simulation,trajectory_sha256=digest(simulation),
            summary=summarize(simulation,demand,semantics=kind,initial_stock=0,
                              warmup_days=1,review_days=1,common_end=4))

    def test_lost_units_never_become_later_fulfillment_and_ordering_diverges(self):
        lost=self.record();back=self.record('backlog')
        simulation=lost['simulation'];days=simulation['days']
        self.assertEqual([r['order_qty'] for r in days],[4,0,0,0])
        self.assertEqual([r['receipts'] for r in days],[0,4,0,0])
        self.assertEqual([r['lost_units'] for r in days],[2,0,0,0])
        self.assertEqual(days[1]['fulfillments'],[dict(id='new:1',kind='new',due_day=1,quantity=2)])
        self.assertEqual(simulation['metrics']['immediate_fill_rate'],Fraction(1,2))
        self.assertEqual(simulation['metrics']['eventual_fill_rate'],Fraction(1,2))
        self.assertEqual(simulation['terminal']['on_hand'],2)
        self.assertEqual(simulation['metrics']['total_cost'],28)
        self.assertEqual(back['simulation']['days'][1]['order_qty'],2)
        self.assertEqual([r['forecast'] for r in simulation['reviews']],
                         [r['forecast'] for r in back['simulation']['reviews']])
        self.assertEqual(back['simulation']['metrics']['eventual_fill_rate'],1)

    def test_paid_periods_common_settlement_and_penalty_break_even(self):
        lost=self.record();back=self.record('backlog')
        a,b=lost['summary'],back['summary']
        self.assertEqual(a['purchased_pieces'],4);self.assertEqual(b['purchased_pieces'],6)
        self.assertEqual(a['full_cost10'],36);self.assertEqual(a['full_cost40'],96)
        self.assertEqual(b['full_cost10'],40);self.assertEqual(b['full_cost40'],40)
        self.assertEqual(a['costs']['warmup'],dict(acquisition=8,holding=0,setup=2,
            penalty10=20,penalty40=80,total10=30,total40=90))
        self.assertEqual(a['costs']['score']['total10'],2)
        self.assertEqual(a['costs']['settlement']['total10'],4)
        self.assertEqual(a['boundary_state'],dict(on_hand=0,backlog=0,outstanding_qty=4))
        differences=contrast(b,a)
        self.assertEqual(differences['first_order_difference'],0)
        self.assertEqual(differences['ordered_pieces_difference'],-2)
        self.assertEqual(differences['cost10_difference'],-4)
        self.assertEqual(differences['cost40_difference'],56)
        self.assertEqual(differences['break_even_lost_unit_penalty'],12)
        extended=summarize(lost['simulation'],[2,2],semantics='lost_sales',initial_stock=0,
                           warmup_days=1,review_days=1,common_end=6)
        self.assertEqual(extended['full_cost10'],40)  # Two owned pieces held two more days.
        self.assertEqual(a['periods']['score']['demand_units'],2)
        self.assertEqual(a['periods']['score']['eventual_units'],2)  # Does not include lost warmup units.

    def test_known_inbound_receives_today_but_never_restores_yesterdays_lost_sale(self):
        result=lost_sales.simulate([1],[1,1],method='naive',on_hand=0,lead_days=2,review_days=1,
            inbound=[dict(id='confirmed',arrival_day=1,quantity=2)])
        self.assertEqual(result['reviews'][0]['inventory_position'],2)
        self.assertEqual(result['reviews'][0]['order_qty'],1)
        self.assertEqual(result['days'][1]['receipts'],2)
        self.assertEqual(result['days'][1]['fulfillments'],[dict(id='new:1',kind='new',due_day=1,quantity=1)])
        self.assertEqual(result['metrics']['lost_units'],1)
        self.assertEqual(result['metrics']['eventual_fill_rate'],Fraction(1,2))
        self.assertEqual(result['terminal']['on_hand'],2)

    def test_delay_is_calendar_slot_even_after_zero_order_and_nonzero_phase(self):
        result=lost_sales.simulate([1],[0,0,0,1,1,0,0,0],method='naive',on_hand=0,
            lead_days=1,review_days=3,review_phase=1,supplier_delays=[2,0,0,0,0])
        self.assertEqual(result['reviews'][0]['day'],1)
        self.assertEqual(result['reviews'][0]['order_qty'],0)
        self.assertEqual(result['days'][4]['order_qty'],4)
        self.assertEqual(result['days'][5]['receipts'],4)
        self.assertEqual(result['days'][7]['receipts'],0)

    def test_future_attempts_cannot_change_earlier_review_and_delay_cannot_change_forecasts(self):
        args=dict(method='mean',on_hand=0,lead_days=2,review_days=7)
        original=lost_sales.simulate([3]*14,[3]*14,**args)
        changed=lost_sales.simulate([3]*14,[3]*7+[99]*7,**args)
        self.assertEqual(original['reviews'][:2],changed['reviews'][:2])
        # Delay slots cover the native 14+2+3+7 day calendar: days0,7,14,21.
        delayed=lost_sales.simulate([3]*14,[3]*14,supplier_delays=[3]*4,**args)
        self.assertEqual([r['forecast'] for r in original['reviews'] if not r['runoff']],
                         [r['forecast'] for r in delayed['reviews'] if not r['runoff']])

    def test_fractional_target_pack_moq_zero_null_and_empty_shelf(self):
        rounded=lost_sales.simulate([0,1],[0],method='mean',on_hand=0,lead_days=1,review_days=1,
            pack_size=3,moq=4,holding_cost=Fraction(1,2),lost_cost=Fraction(3,2))
        self.assertEqual(rounded['reviews'][0]['target'],1)
        self.assertEqual(rounded['reviews'][0]['order_qty'],6)
        zero=lost_sales.simulate([0],[0,0],method='zero',on_hand=0,lead_days=1,review_days=1)
        self.assertIsNone(zero['metrics']['immediate_fill_rate'])
        self.assertIsNone(zero['metrics']['eventual_fill_rate'])
        self.assertEqual(zero['metrics']['cycle_service'],1)
        self.assertTrue(all(not r['shortage'] and not r['order_qty'] for r in zero['days']))

    def test_piece_conservation_across_stock_delay_and_spikes(self):
        for stock in (0,3,10):
            for delay in (0,2):
                values=[0,7,0,1,9,0,0]
                stop=7+2+delay+3;slots=len(range(0,stop,3))
                r=lost_sales.simulate([1]*7,values,method='mean',on_hand=stock,lead_days=2,review_days=3,
                    supplier_delays=[delay]*slots,pack_size=2,moq=4)
                served=sum(d['fulfilled_units'] for d in r['days']);lost=sum(d['lost_units'] for d in r['days'])
                self.assertEqual(sum(values),served+lost)
                self.assertEqual(stock+sum(d['receipts'] for d in r['days']),served+r['terminal']['on_hand'])
                self.assertTrue(all(d['on_hand']>=0 and d['backlog']==0 for d in r['days']))

    def test_contract_rejects_accepted_obligations_and_incomplete_invalid_inputs(self):
        base=dict(method='mean',on_hand=0,lead_days=1,review_days=1)
        mutations=(dict(commitments=[dict(id='accepted',due_day=0,quantity=1)]),dict(commitments=None),
            dict(supplier_delays=[0]),dict(supplier_delays=[True]*3),dict(on_hand=True),dict(lost_cost=1.0),
            dict(lost_cost=-1),dict(lead_days=0),dict(review_phase=1),dict(method='unknown'),
            dict(inbound=[dict(id='x',arrival_day=0,quantity=1)]*2),
            dict(inbound=[dict(id='x',arrival_day=1,quantity=1)]))
        for change in mutations:
            with self.assertRaises(ValueError): lost_sales.simulate([1],[1],**dict(base,**change))
        for demand in ([],[None],[1.0],[True],[-1]):
            with self.assertRaises(ValueError): lost_sales.simulate([1],demand,**base)
        with self.assertRaises(ValueError):
            summarize(self.record()['simulation'],[2,2],semantics='lost_sales',initial_stock=0,
                      warmup_days=2,review_days=1,common_end=4)

    def test_independent_audit_rejects_rehashed_receipt_restoration_forecast_and_cost_faults(self):
        original=self.record()
        audit_arm(original,warmup=1,common_end=4)
        audit_arm(self.record('backlog'),warmup=1,common_end=4)
        for mutate in ('receipt','restored_sale','forecast','cost','lost_quantity','native_metric'):
            record=deepcopy(original);sim=record['simulation']
            if mutate=='receipt': sim['days'][0]['receipts']=1
            elif mutate=='restored_sale': sim['days'][1]['fulfillments'][0]['id']='new:0'
            elif mutate=='forecast': sim['reviews'][0]['forecast'][0]+=1
            elif mutate=='lost_quantity': sim['days'][0]['lost_units']=0
            elif mutate=='native_metric': sim['metrics']['lost_units']=0
            else: record['summary']['costs']['warmup']['total10']+=1
            record['trajectory_sha256']=digest(sim)
            with self.assertRaises(ValueError): audit_arm(record,warmup=1,common_end=4)

    def test_independent_supplier_namespace_and_block_maximum(self):
        trace=supplier('lumpy',9101,'variable')
        self.assertEqual(sorted(trace[:6]),[0,0,1,1,2,4])
        self.assertEqual(len(trace),15)
        self.assertNotEqual(trace,supplier('lumpy',9127,'variable'))
        self.assertEqual(supplier('lumpy',9101,'fixed'),[0]*15)


if __name__=='__main__': unittest.main()
