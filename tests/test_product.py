"""Focused adapter boundary and deterministic comparison tests."""
from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path
import tempfile
import unittest

from inventory_intelligence.product import (archive_digest, load_catalog, normalize_report,
    validate_catalog, overview, explore, detail, evidence, history, scenario, _report)


class ProductTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=load_catalog()
        cls.cutoff='2026-01-05'
        cls.key=('product:sku-00','product:harbor')

    def test_catalog_dimensions_exact_known_and_blocked_stock(self):
        result=overview(self.catalog,self.cutoff)
        self.assertEqual(result['summary']['keys'],100)
        self.assertEqual(len(result['dimensions']['skus']),50)
        blocked=detail(self.catalog,'2026-01-19','product:sku-02','product:upland')
        self.assertEqual((blocked['inventory_status'],blocked['on_hand']),('assessable','10'))
        self.assertIsNone(blocked['proposed_order_qty'])
        self.assertEqual(explore(self.catalog,'2026-01-12',{'category':'evidence'})['total'],0)

    def test_limited_evidence_preserves_selected_key_sources_and_clocks(self):
        for section in ('inventory','training','supply','plan','forecast','reliability'):
            result=evidence(self.catalog,self.cutoff,*self.key,section,page_size=2)
            self.assertLessEqual(len(result['rows']),2)
            self.assertEqual(result['archive_digest'],self.catalog['digest'])
        result=evidence(self.catalog,self.cutoff,*self.key,'inventory',page_size=100)
        self.assertEqual(len(result['rows']),6)
        for row in result['rows']:
            if 'sku_id' in row: self.assertEqual((row['sku_id'],row['warehouse_id']),self.key)
        result=evidence(self.catalog,self.cutoff,*self.key,'training',page_size=100)
        self.assertEqual(len(result['rows']),28)
        self.assertTrue(all(row['quantity']=='4' for row in result['rows']))
        # Future revisions exist in original fixture but none appears in origin-known report.
        self.assertTrue(all(':future' not in json.dumps(row) for row in result['rows']))

    def test_selected_defaults_noorder_prefix_and_periodic_separation(self):
        result=scenario(self.catalog,self.cutoff,*self.key,{})
        plan=result['baseline']['plan']
        self.assertEqual(plan['proposed_order_qty'],'12')
        self.assertEqual([r['balance_without_order'] for r in plan['projection']],
            [{'numerator':str(n),'denominator':'1'} for n in (3,4,0,-4,-8)])
        self.assertEqual([r['balance_with_order'] for r in plan['projection']],
            [{'numerator':str(n),'denominator':'1'} for n in (3,4,12,8,4)])
        self.assertEqual(result['baseline']['simulation']['metrics']['new_demand_units'],'112')
        refs=result['baseline']['trace'][0]['references']
        self.assertTrue(any(r['source']=='product.calculation' and r['id']==result['baseline']['run_id'] for r in refs))
        self.assertTrue(any(r['source']=='planning.runs.inputs' for r in refs))
        self.assertFalse(result['capabilities']['purchase_execution']['supported'])

    def test_incomparable_total_cost_with_comparable_scored_window(self):
        result=scenario(self.catalog,self.cutoff,*self.key,{'supplier_delay_days':3})
        compare=result['comparison']
        self.assertFalse(compare['fields']['total_cost']['compatible'])
        self.assertIsNone(compare['fields']['total_cost']['delta'])
        self.assertTrue(compare['fields']['scored_total_cost']['compatible'])
        self.assertEqual((compare['scored_days'],compare['baseline_runoff_days'],compare['scenario_runoff_days']),(28,5,8))
        same=scenario(self.catalog,self.cutoff,*self.key,{'demand_percent':125})
        self.assertTrue(same['comparison']['fields']['total_cost']['compatible'])
        self.assertEqual(same['scenario']['plan']['proposed_order_qty'],'18')

    def test_zero_demand_undefined_fill_and_current_missing_evidence(self):
        zero=scenario(self.catalog,self.cutoff,'product:sku-01','product:upland',{})
        self.assertEqual(zero['baseline']['plan']['proposed_order_qty'],'0')
        self.assertIsNone(zero['baseline']['simulation']['metrics']['immediate_fill_rate'])
        missing=scenario(self.catalog,'2026-01-19','product:sku-02','product:upland',{'evidence_case':'clean'})
        self.assertIsNone(missing['scenario']['plan'])
        simulated_missing=scenario(self.catalog,self.cutoff,*self.key,{'evidence_case':'incomplete_supply'})
        self.assertEqual(simulated_missing['baseline']['status'],'assessable')
        self.assertIsNone(simulated_missing['scenario']['plan'])
        restored=history(self.catalog,'product:sku-03','product:harbor')['points'][1]
        self.assertEqual(restored['state'],'new')
        self.assertFalse(restored['comparable'])
        self.assertIsNone(restored['stock_delta'])

    def test_readonly_deterministic_calculations(self):
        digest=archive_digest(self.catalog)
        first=scenario(self.catalog,self.cutoff,*self.key,{'demand_percent':125})
        second=scenario(self.catalog,self.cutoff,*self.key,{'demand_percent':125})
        self.assertEqual(first,second)
        self.assertEqual(archive_digest(self.catalog),digest)
        before=detail(self.catalog,self.cutoff,*self.key)
        scenario(self.catalog,'2026-01-19',*self.key,{'demand_percent':200})
        self.assertEqual(detail(self.catalog,self.cutoff,*self.key),before)

    def test_strict_selectors_and_integer_controls(self):
        invalid=[lambda:explore(self.catalog,filters={'unknown':'x'}),
                 lambda:explore(self.catalog,page=True),lambda:explore(self.catalog,page_size=101),
                 lambda:explore(self.catalog,sort='cost'),
                 lambda:detail(self.catalog,'2026-01-05T08:00:00+00:00',*self.key),
                 lambda:detail(self.catalog,None,'missing',self.key[1]),
                 lambda:scenario(self.catalog,self.cutoff,*self.key,{'pack_size':True}),
                 lambda:scenario(self.catalog,self.cutoff,*self.key,{'demand_percent':100.0}),
                 lambda:evidence(self.catalog,self.cutoff,*self.key,'unknown')]
        for call in invalid:
            with self.assertRaises(ValueError):call()

    def test_rehashed_malformed_supply_manifest_and_identities(self):
        # Rehash authentic reports after independently specified bad source fields;
        # byte integrity alone cannot establish booleans or source identities.
        for corruption in ('integer_completeness','null_source','blank_natural_id','duplicate_row_id','multiple_reservations'):
            changed=deepcopy(self.catalog)
            run_id=changed['cutoffs'][0]['keys'][0]['plan_run_id']
            report=deepcopy(_report(changed,run_id)); supply=report['result']['supply']
            if corruption=='integer_completeness': supply['batch']['reservations_complete']=1
            elif corruption=='null_source': supply['reservations'][0]['source_system']=None
            elif corruption=='blank_natural_id': supply['inbound'][0]['inbound_id']=' '
            elif corruption=='multiple_reservations':
                supply['reservations'].append(supply['reservations'][0]|dict(row_id='another-row',reservation_id='another-reservation',remaining_qty=0))
                supply['batch']['expected_reservations']=2
            else: supply['inbound'][0]['row_id']=supply['policy']['row_id']
            inputs={k:report['result'][k] for k in ('inventory','supply','training')}
            report['input_digest']=archive_digest(dict(context=report['context'],inputs=inputs),exclude_digest=False)
            changed['reports'][run_id]=dict(digest=archive_digest(report,exclude_digest=False),report=normalize_report(report,changed['objects']))
            changed['digest']=archive_digest(changed)
            with self.subTest(corruption=corruption),self.assertRaises(ValueError):validate_catalog(changed)

    def test_rehashed_duplicate_control_requires_actual_snapshot_evidence(self):
        changed=deepcopy(self.catalog)
        control=changed['controls']['duplicate_inventory']
        defect=deepcopy(_report(changed,control['reliability_run_id']))
        blocked=deepcopy(_report(changed,control['plan_run_id']))
        defect['findings'][0]['evidence']['source_records'][0]['record']['on_hand_qty']=23
        blocked['result']['inventory']['findings'][0]['evidence']['source_records'][0]['record']['on_hand_qty']=23
        inputs={k:blocked['result'][k] for k in ('inventory','supply','training')}
        blocked['input_digest']=archive_digest(dict(context=blocked['context'],inputs=inputs),exclude_digest=False)
        for report in (defect,blocked):
            changed['reports'][report['run_id']]=dict(digest=archive_digest(report,exclude_digest=False),report=normalize_report(report,changed['objects']))
        changed['digest']=archive_digest(changed)
        with self.assertRaises(ValueError):validate_catalog(changed)

    def test_changed_saved_policy_has_unknown_history_comparability(self):
        # Build a valid later producer report using the existing kernel. Expected
        # scope behavior is independently unknown; no business quantity is graded.
        from datetime import date
        from inventory_intelligence.planning_runs import exact_json
        from inventory_intelligence.replenishment import project
        changed=deepcopy(self.catalog)
        run_id=changed['cutoffs'][1]['keys'][0]['plan_run_id']
        report=deepcopy(_report(changed,run_id)); result=report['result']; supply=result['supply']
        supply['policy']['safety_qty']=3
        supply['policies'][0]['safety_qty']=3
        quantities=[Fraction(q) for q in result['forecast']['predictions']]
        recalculated=project(on_hand=result['inventory']['on_hand'],forecasts=quantities,
            reservations=[r|dict(due_day=date.fromisoformat(r['due_day'])) for r in supply['reservations']],
            inbound=[r|dict(arrival_day=date.fromisoformat(r['arrival_day'])) for r in supply['inbound']],
            origin_day=date.fromisoformat(report['context']['origin_day']),policy=supply['policy'])
        result.update(exact_json(recalculated))
        inputs={k:result[k] for k in ('inventory','supply','training')}
        report['input_digest']=archive_digest(dict(context=report['context'],inputs=inputs),exclude_digest=False)
        changed['reports'][run_id]=dict(digest=archive_digest(report,exclude_digest=False),report=normalize_report(report,changed['objects']))
        changed['digest']=archive_digest(changed)
        validate_catalog(changed)
        point=history(changed,*self.key)['points'][1]
        self.assertEqual(point['state'],'unknown')
        self.assertFalse(point['comparable'])
        self.assertIsNone(point['stock_delta'])
        self.assertEqual(point['comparison_reason'],'incompatible_comparison_basis')
        self.assertEqual(detail(changed,'2026-01-12',*self.key)['history_state'],'unknown')

    def test_archive_corruption_bounds_and_semantic_bindings(self):
        changed=deepcopy(self.catalog);changed['cutoffs'][0]['keys'][0]['plan_run_id']=changed['cutoffs'][1]['keys'][0]['plan_run_id'];changed['digest']=archive_digest(changed)
        with self.assertRaises(ValueError):validate_catalog(changed)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'bad.json';path.write_text('{"synthetic":true}')
            with self.assertRaises(ValueError):load_catalog(path)
        changed=deepcopy(self.catalog);changed['objects'][next(iter(changed['objects']))]['unknown']=0;changed['digest']=archive_digest(changed)
        with self.assertRaises(ValueError):validate_catalog(changed)


if __name__=='__main__':unittest.main()
