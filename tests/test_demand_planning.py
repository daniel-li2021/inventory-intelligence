"""Independent future-only arithmetic and source-bound HTTP regression controls."""
from copy import deepcopy
from datetime import date, timedelta
from fractions import Fraction
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from inventory_intelligence.demand_planning import calculate, DemandPlanningError, _weeks
from inventory_intelligence.forecasting import forecast
from inventory_intelligence.lab_api import create_app
from inventory_intelligence.lab_hosted import HostedLab
from inventory_intelligence.product import load_catalog, _report, archive_digest, scenario


def rational(value):
    return Fraction(int(value['numerator']), int(value['denominator'])) if isinstance(value, dict) else Fraction(value)


class DemandPlanningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog()
        cls.cutoff = '2026-01-05'
        cls.key = ('product:sku-00', 'product:harbor')

    def plan(self, **kw):
        return calculate(self.catalog, self.cutoff, *self.key, **kw)

    def adjustment(self, kind='percent', value=25, start_day='2026-01-05', end_day='2026-02-01'):
        return dict(kind=kind, value=value, start_day=start_day, end_day=end_day)

    def test_default_matches_saved_forecasts_and_exact_projections_at_every_key(self):
        for binding in self.catalog['cutoffs']:
            for key in binding['keys']:
                with self.subTest(cutoff=binding['cutoff'], sku=key['sku_id'], wh=key['warehouse_id']):
                    result = calculate(self.catalog, binding['cutoff'], key['sku_id'], key['warehouse_id'])
                    saved = _report(self.catalog, key['plan_run_id'])['result']
                    fc = _report(self.catalog, key['forecast_run_id'])['result']['predictions']
                    self.assertEqual(result['forecast_status'], 'assessable' if fc is not None else 'not_assessable')
                    self.assertEqual([rational(r['baseline']) for r in result['daily'][28:]] if fc is not None else None,
                                     [Fraction(q) for q in fc] if fc is not None else None)
                    self.assertEqual(result['impact']['baseline']['proposed_order_qty'] if result['impact']['baseline'] else None,
                                     str(saved['proposed_order_qty']) if saved['proposed_order_qty'] is not None else None)
                    self.assertEqual(result['impact']['baseline'], result['impact']['adjusted'])
                    if result['impact']['baseline']:
                        for actual, expected in zip(result['impact']['baseline']['projection'], saved['projection']):
                            for field in ('balance_without_order', 'balance_with_order', 'forecast'):
                                self.assertEqual(rational(actual[field]), Fraction(expected[field]))

    def test_percent_and_quantity_future_only_with_independent_expected_order(self):
        before = archive_digest(self.catalog)
        baseline = self.plan()
        percent = self.plan(adjustment=self.adjustment())
        pieces = self.plan(adjustment=self.adjustment('pieces', 1))
        self.assertEqual(percent['totals'], pieces['totals'])
        self.assertEqual(rational(percent['totals']['baseline']), 112)
        self.assertEqual(rational(percent['totals']['adjusted']), 140)
        self.assertEqual(percent['daily'][:28], baseline['daily'][:28])
        self.assertEqual([rational(r['adjusted']) for r in percent['daily'][28:]], [5]*28)
        # Stock10, reservation3, confirmed inbound5 on day1: baseline balances
        # 3,4,0,-4,-8. With 5/day: 2,2,-3,-8,-13; safety2 needs15 -> pack6 =>18.
        self.assertEqual(percent['impact']['baseline']['proposed_order_qty'], '12')
        self.assertEqual(percent['impact']['adjusted']['proposed_order_qty'], '18')
        self.assertEqual([rational(r['balance_without_order']) for r in percent['impact']['adjusted']['projection']], [2,2,-3,-8,-13])
        self.assertEqual(archive_digest(self.catalog), before)

    def test_fractional_expectations_are_not_ceiled_as_physical_pieces(self):
        result = self.plan(adjustment=self.adjustment(value=1))
        self.assertEqual(rational(result['daily'][28]['adjusted']), Fraction(101,25))
        self.assertEqual(rational(result['totals']['adjusted']), Fraction(2828,25))

    def test_noop_zero_and_signed_reduction(self):
        for kind in ('percent', 'pieces'):
            result = self.plan(adjustment=self.adjustment(kind, 0))
            self.assertEqual(result['impact']['baseline'], result['impact']['adjusted'])
            self.assertEqual(rational(result['totals']['delta']), 0)
        zero = self.plan(adjustment=self.adjustment(value=-100))
        self.assertEqual(rational(zero['totals']['adjusted']), 0)
        lower = self.plan(adjustment=self.adjustment('pieces', -1))
        self.assertEqual(rational(lower['totals']['adjusted']), 84)

    def test_outside_protection_changes_outlook_without_changing_proposal(self):
        result = self.plan(adjustment=self.adjustment(start_day='2026-01-10'))
        self.assertEqual(result['impact']['effect'], 'outside_protection_window')
        self.assertEqual(result['impact']['baseline'], result['impact']['adjusted'])
        self.assertEqual(rational(result['totals']['adjusted']), 135)
        self.assertEqual(result['protection_days'], 5)

    def test_all_methods_and_horizons_use_existing_kernel_and_no_accuracy_claim(self):
        for horizon in (7,14,28):
            for method in ('naive','mean','seasonal_naive'):
                result = self.plan(method=method,horizon=horizon)
                self.assertEqual([rational(r['baseline']) for r in result['daily'][28:]], forecast([4]*28,method=method,horizon=horizon))
                self.assertEqual(result['operational_default'], 'mean')
                self.assertIsNone(result['accuracy']['mae'])
                self.assertIsNone(result['accuracy']['wape'])

    def test_calendar_weeks_and_partial_origin_periods_do_not_cross_boundary(self):
        rows = [dict(day=(date(2026,1,6)+timedelta(days=i)).isoformat(),period='history' if i<2 else 'forecast',
                     history=2 if i<2 else None,baseline=Fraction(1,3) if i>=2 else None,
                     adjusted=Fraction(2,3) if i>=2 else None) for i in range(9)]
        weeks = _weeks(rows)
        self.assertEqual([(r['period'],r['day_count'],r['partial']) for r in weeks], [('history',2,True),('forecast',4,True),('forecast',3,True)])
        self.assertEqual([r['baseline'] for r in weeks], [None,Fraction(4,3),1])
        self.assertEqual(sum(r['adjusted'] for r in weeks if r['period']=='forecast'), Fraction(14,3))
        rows[2]['baseline'] = None
        self.assertIsNone(_weeks(rows)[1]['baseline'])
        for horizon in (7,14,28):
            result=self.plan(horizon=horizon)
            self.assertEqual(sum(rational(r['baseline']) for r in result['weekly'] if r['period']=='forecast'), rational(result['totals']['baseline']))

    def test_nonconstant_library_control_distinguishes_all_three_methods(self):
        # A hand-specified library input, not a new source artifact or model study.
        original = __import__('inventory_intelligence.product',fromlist=['_report'])._report
        def control(catalog, run_id):
            report=deepcopy(original(catalog,run_id))
            if report.get('kind')=='replenishment':
                for i,row in enumerate(report['result']['training']['days']): row['quantity']=i%7+1
            return report
        with patch('inventory_intelligence.product._report',side_effect=control):
            expected={'mean':[4]*7,'naive':[7]*7,'seasonal_naive':[1,2,3,4,5,6,7]}
            for method,values in expected.items():
                result=self.plan(method=method,horizon=7)
                self.assertEqual([rational(r['baseline']) for r in result['daily'][28:]],values)

    def test_missing_demand_and_incomplete_supply_preserve_separate_gates(self):
        # Existing incomplete supply control has valid demand: forecasts remain useful.
        result=calculate(self.catalog,'2026-01-19','product:sku-02','product:upland')
        self.assertEqual(result['forecast_status'],'assessable')
        self.assertIsNone(result['impact']['adjusted'])
        blocked=next((b,k) for b in self.catalog['cutoffs'] for k in b['keys']
                     if _report(self.catalog,k['forecast_run_id'])['status']!='assessable')
        result=calculate(self.catalog,blocked[0]['cutoff'],blocked[1]['sku_id'],blocked[1]['warehouse_id'])
        self.assertIsNone(result['totals']['baseline'])
        self.assertTrue(any(r['history'] is None for r in result['daily'][:28]))
        self.assertIsNone(result['impact']['adjusted'])

    def test_invalid_ranges_negative_results_and_unbounded_inputs_reject(self):
        invalid=[self.adjustment('pieces',-5),self.adjustment(value=-101),self.adjustment(value=101),
                 self.adjustment(value=True),self.adjustment(value=1.5),self.adjustment('pieces',1001),
                 self.adjustment(start_day='2026-01-04'),self.adjustment(end_day='2026-02-02'),
                 self.adjustment(start_day='2026-01-07',end_day='2026-01-06'),
                 self.adjustment(start_day='20260105'),self.adjustment()|dict(extra=True)]
        for adjustment in invalid:
            with self.subTest(adjustment=adjustment),self.assertRaises(DemandPlanningError):
                self.plan(adjustment=adjustment)

    def test_deterministic_identity_binds_method_horizon_adjustment_and_archive(self):
        a=self.plan(adjustment=self.adjustment())
        self.assertEqual(a,self.plan(adjustment=self.adjustment()))
        others=[self.plan(method='naive'),self.plan(horizon=7),self.plan(),self.plan(adjustment=self.adjustment(value=24))]
        self.assertEqual(len({r['calculation_digest'] for r in [a]+others}),5)


class DemandApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=load_catalog()
        cls.body=dict(cutoff='2026-01-05',sku_id='product:sku-00',warehouse_id='product:harbor',
                      archive_digest=cls.catalog['digest'],horizon=28,method='mean')
        cls.client=TestClient(HostedLab(create_app(),burst=200))

    @classmethod
    def tearDownClass(cls): cls.client.close()

    def test_hosted_readonly_routes_source_binding_and_no_database(self):
        path=Path('src/inventory_intelligence/product_evidence.json.gz')
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        with patch('psycopg.connect',side_effect=AssertionError('no database')):
            result=self.client.get('/api/product/demand',params=self.body)
            self.assertEqual(result.status_code,200)
            self.assertEqual(result.headers['cache-control'],'no-store')
            self.assertEqual(self.client.post('/api/product/demand-scenario',json=self.body).json(),result.json())
            self.assertEqual(self.client.post('/api/product/purchase-event',json={}).status_code,404)
            old=self.client.post('/api/product/scenario',json={k:v for k,v in self.body.items() if k not in ('horizon','method')}|dict(overrides={'demand_percent':125}))
            self.assertEqual(old.status_code,200)
            self.assertEqual(old.json(),scenario(self.catalog,self.body['cutoff'],self.body['sku_id'],self.body['warehouse_id'],{'demand_percent':125}))
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),digest)

    def test_rejects_unknown_repeated_stale_and_invalid_requests(self):
        self.assertEqual(self.client.get('/api/product/demand',params=self.body|dict(extra=1)).status_code,422)
        self.assertEqual(self.client.get('/api/product/demand',params=list(self.body.items())+[('method','naive')]).status_code,422)
        self.assertEqual(self.client.get('/api/product/demand',params=self.body|dict(archive_digest='0'*64)).status_code,409)
        self.assertEqual(self.client.post('/api/product/demand-scenario',json=self.body|dict(archive_digest='0'*64)).status_code,409)
        for field,value in [('method','new_model'),('horizon',90),('horizon',7.0),('horizon',8),('horizon',True),('extra',1)]:
            self.assertEqual(self.client.post('/api/product/demand-scenario',json=self.body|{field:value}).status_code,422)
        for value in (True,1.5,'25',1001):
            adjustment=dict(kind='pieces',value=value,start_day='2026-01-05',end_day='2026-02-01')
            self.assertEqual(self.client.post('/api/product/demand-scenario',json=self.body|dict(adjustment=adjustment)).status_code,422)
        negative=self.client.post('/api/product/demand-scenario',json=self.body|dict(adjustment=dict(kind='pieces',value=-5,start_day='2026-01-05',end_day='2026-02-01')))
        self.assertEqual(negative.status_code,422)
        self.assertIn('negative',negative.json()['detail'])
