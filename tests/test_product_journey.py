"""Independent synthetic product controls, frozen before adapter implementation.

Expected business values below are hand arithmetic from product-contract.md; no
production calculator is used to manufacture an expected result.
"""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from inventory_intelligence import product
from inventory_intelligence.lab_api import create_app


CUTOFFS = ('2026-01-05', '2026-01-12', '2026-01-19')
KEYS = [(f'product:sku-{index // 2:02}',
         'product:harbor' if index % 2 == 0 else 'product:upland') for index in range(8)]
PROPOSALS = (('12', '0', '0', '0', '12', '12', None, '18'),
             ('18', '12', '0', '0', '12', '12', '0', '18'),
             ('0', '12', '0', '0', '12', None, '0', '18'))
CATEGORY_COUNTS = (dict(risk=49, opportunity=26, evidence=12, none=13),
                   dict(risk=62, opportunity=25, evidence=0, none=13),
                   dict(risk=37, opportunity=25, evidence=12, none=26))
CATEGORIES = (('risk', 'opportunity', 'opportunity', 'none', 'risk', 'risk', 'evidence', 'risk'),
              ('risk', 'risk', 'opportunity', 'none', 'risk', 'risk', 'opportunity', 'risk'),
              ('none', 'risk', 'opportunity', 'none', 'risk', 'evidence', 'opportunity', 'risk'))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def repackage(catalog, reports):
    """Test-only rehashing: retain bindings while bypassing integrity checks."""
    result = deepcopy(catalog)
    result['objects'] = {}
    result['reports'] = {}
    for run_id, report in reports.items():
        if 'kind' in report:
            values = report['result']
            inputs = (values['training'] if report['kind'] == 'forecast' else
                      {key: values[key] for key in ('inventory', 'supply', 'training')})
            report['input_digest'] = digest(dict(context=report['context'], inputs=inputs))
        result['reports'][run_id] = {'digest': digest(report),
                                   'report': product.normalize_report(report, result['objects'])}
    result['digest'] = product.archive_digest(result)
    return result


class ProductJourneyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = product.load_catalog()
        cls.client = TestClient(create_app())

    def test_frozen_first_eight_proposals_and_full_category_sets(self):
        for cutoff, proposals, expected, categories in zip(CUTOFFS, PROPOSALS, CATEGORY_COUNTS, CATEGORIES):
            with self.subTest(cutoff=cutoff):
                items = product.explore(self.catalog, cutoff, {}, page_size=100)['items']
                self.assertEqual(len(items), 100)
                self.assertEqual({category: sum(item['category'] == category for item in items)
                                  for category in expected}, expected)
                by_key = {(item['sku_id'], item['warehouse_id']): item for item in items}
                for index in range(100):
                    key = (f'product:sku-{index // 2:02}',
                           'product:harbor' if index % 2 == 0 else 'product:upland')
                    self.assertEqual(by_key[key]['category'], categories[index % 8], key)
                    self.assertEqual(by_key[key]['proposed_order_qty'], proposals[index % 8], key)
                for key, quantity in zip(KEYS, proposals):
                    self.assertEqual(by_key[key]['proposed_order_qty'], quantity, key)
                self.assertEqual(by_key[KEYS[3]]['on_hand'], '0')
                self.assertEqual(by_key[KEYS[3]]['category'], 'none')

    def test_history_new_persistent_worsening_improved_unknown(self):
        expected = (('unknown', 'worsening', 'improved'),
                    ('unknown', 'new', 'persistent'),
                    ('unknown', 'persistent', 'persistent'),
                    ('unknown', 'persistent', 'persistent'),
                    ('unknown', 'persistent', 'persistent'),
                    ('unknown', 'persistent', 'unknown'),
                    ('unknown', 'new', 'persistent'),
                    ('unknown', 'persistent', 'persistent'))
        for key, states in zip(KEYS, expected):
            with self.subTest(key=key):
                points = product.history(self.catalog, *key)['points']
                self.assertEqual(tuple(point['item']['history_state'] for point in points), states)
        # Later disappearance under missing reservations cannot masquerade as resolved.
        missing = product.detail(self.catalog, CUTOFFS[-1], *KEYS[5])
        self.assertEqual(missing['status'], 'not_assessable')
        self.assertEqual(missing['history_state'], 'unknown')
        self.assertIsNone(missing['proposed_order_qty'])

    def test_preset_manual_filter_totals_and_zero_are_exact(self):
        for cutoff, counts in zip(CUTOFFS, CATEGORY_COUNTS):
            for category, count in counts.items():
                result = product.explore(self.catalog, cutoff, {'category': category}, page_size=100)
                self.assertEqual(result['total'], count)
                self.assertEqual(len(result['items']), count)
                self.assertTrue(all(item['category'] == category for item in result['items']))
        empty = product.explore(self.catalog, CUTOFFS[0], {'search': 'no-such-sku'}, page_size=20)
        self.assertEqual(empty['total'], 0)
        self.assertEqual(empty['items'], [])

    def test_filtered_matrix_zero_unknown_stock_totals_and_business_clocks(self):
        for cutoff, stock_total, blocked_count in zip(CUTOFFS, (2010, 1542, 1776), (12, 0, 12)):
            result = product.explore(self.catalog, cutoff, {}, page_size=20)
            self.assertEqual(len(result['items']), 20)
            self.assertEqual(len(result['matrix']), 100)
            self.assertEqual(sum(int(cell['on_hand']) for cell in result['matrix']), stock_total)
            self.assertEqual(sum(cell['on_hand'] == '0' for cell in result['matrix']), 13)
            self.assertEqual(sum(cell['status'] == 'not_assessable' for cell in result['matrix']), blocked_count)
            self.assertLess(len(json.dumps(result).encode()), 2*1024*1024)
            selected = product.detail(self.catalog, cutoff, *KEYS[0])
            self.assertEqual(selected['clocks']['business_cutoff'], cutoff+'T08:00:00+00:00')
            self.assertEqual(selected['clocks']['decision_known_at'], cutoff+'T08:00:00+00:00')
        filtered = product.explore(self.catalog, CUTOFFS[0], {'category': 'opportunity'}, page_size=20)
        self.assertEqual(len(filtered['matrix']), 26)
        self.assertTrue(all(cell['category'] == 'opportunity' for cell in filtered['matrix']))
        self.assertEqual(sum(int(cell['on_hand']) for cell in filtered['matrix']), 1040)

    def test_incomplete_evidence_and_unsupported_alternatives_suppress_values(self):
        result = product.scenario(self.catalog, CUTOFFS[-1], *KEYS[5], {})
        for side in ('baseline', 'scenario'):
            self.assertEqual(result[side]['status'], 'not_assessable')
            for field in ('plan', 'simulation', 'risk', 'costs'):
                self.assertIsNone(result[side][field])
        self.assertFalse(result['comparison']['compatible'])
        for field in result['comparison']['fields'].values():
            self.assertIsNone(field['baseline'])
            self.assertIsNone(field['scenario'])
            self.assertIsNone(field['delta'])
            self.assertFalse(field['compatible'])
        for name in ('transfer', 'expedite', 'markdown', 'purchase_execution', 'commercial_savings'):
            self.assertFalse(result['capabilities'][name]['supported'])

    def test_pending_inbound_is_never_confirmed_supply(self):
        detail = product.detail(self.catalog, CUTOFFS[0], *KEYS[7])
        self.assertEqual(detail['proposed_order_qty'], '18')
        self.assertEqual(detail['forecast_daily'], {'numerator': '4', 'denominator': '1'})

    def test_api_unknown_selector_clock_key_bounds_and_archive_binding(self):
        selection = dict(cutoff=CUTOFFS[0], sku_id=KEYS[0][0], warehouse_id=KEYS[0][1])
        good = self.client.get('/api/product/detail', params=selection)
        self.assertEqual(good.status_code, 200, good.text)
        for replacement in (dict(cutoff='2026-01-06T00:00:00+00:00'),
                            dict(sku_id=KEYS[0][0]+'-unknown'),
                            dict(warehouse_id='missing-location'), dict(unexpected='ignored')):
            with self.subTest(replacement=replacement):
                self.assertEqual(self.client.get('/api/product/detail',
                                                params=selection | replacement).status_code, 422)
        stale = self.client.get('/api/product/detail', params=selection | {'archive_digest': '0'*64})
        self.assertEqual(stale.status_code, 409)
        duplicate = self.client.get('/api/product/explore?category=risk&category=opportunity')
        self.assertEqual(duplicate.status_code, 422)
        for params in ({'page': 0}, {'page_size': 101}, {'style_id': 'unknown'},
                       {'sort': 'unsupported'}, {'status': 'resolved'}):
            self.assertEqual(self.client.get('/api/product/explore', params=params).status_code, 422)
        scenario = selection | {'archive_digest': self.catalog['digest'], 'overrides': {}}
        for overrides in ({'demand_percent': True}, {'unknown': 1}, {'demand_percent': 201},
                          {'demand_percent': '125'}, {'evidence_case': 'unknown'}):
            self.assertEqual(self.client.post('/api/product/scenario',
                                             json=scenario | {'overrides': overrides}).status_code, 422)
        self.assertEqual(self.client.post('/api/product/scenario',
                                         json=scenario | {'archive_digest': '0'*64}).status_code, 409)
        self.assertEqual(self.client.post('/api/product/scenario',
                                         json=selection | {'overrides': {}}).status_code, 422)

    def test_invalid_archive_and_app_copy_fail_closed(self):
        bad = TestClient(create_app(product_evidence={'synthetic': True}))
        for path in ('/api/product/overview', '/api/product/explore', '/health/ready'):
            response = bad.get(path)
            self.assertEqual(response.status_code, 503)
            self.assertNotIn('proposed_order_qty', response.text)
        injected = deepcopy(self.catalog)
        isolated = TestClient(create_app(product_evidence=injected))
        injected['digest'] = '0'*64
        self.assertEqual(isolated.get('/api/product/overview').status_code, 200)

    def test_same_size_archive_replacement_invalidates_validated_cache(self):
        original = Path(product.__file__).with_name('product_evidence.json.gz').read_bytes()
        with tempfile.TemporaryDirectory(prefix='ii-product-cache-') as temporary:
            directory = Path(temporary)
            archive = directory/'product_evidence.json.gz'
            archive.write_bytes(original)
            with patch.object(product, '__file__', str(directory/'product.py')):
                client = TestClient(create_app())
                first = client.get('/api/product/overview')
                self.assertEqual(first.status_code, 200)
                stat = archive.stat()
                archive.write_bytes(b'\x00'*len(original))
                # Preserve size and mtime; ctime/inode must still invalidate trust.
                os.utime(archive, ns=(stat.st_atime_ns, stat.st_mtime_ns))
                failed = client.get('/api/product/overview')
                self.assertEqual(failed.status_code, 503)
                self.assertNotIn('proposed_order_qty', failed.text)
                archive.write_bytes(original)
                restored = client.get('/api/product/overview')
                self.assertEqual(restored.status_code, 200)
                self.assertEqual(restored.json(), first.json())

    def test_rehashed_cross_key_and_cross_cutoff_bindings_are_rejected(self):
        # Rehashing bypasses byte-integrity checks deliberately: the semantic
        # key/clock binding must reject independently valid but wrong reports.
        for field, source_cutoff, source_key in (('plan_run_id', 0, 1),
                                                ('forecast_run_id', 0, 1),
                                                ('plan_run_id', 1, 0)):
            changed = deepcopy(self.catalog)
            changed['cutoffs'][0]['keys'][0][field] = changed['cutoffs'][source_cutoff]['keys'][source_key][field]
            changed['digest'] = product.archive_digest(changed)
            with self.subTest(field=field, source_cutoff=source_cutoff):
                client = TestClient(create_app(product_evidence=changed))
                response = client.get('/api/product/detail', params=dict(cutoff=CUTOFFS[0],
                                            sku_id=KEYS[0][0], warehouse_id=KEYS[0][1]))
                self.assertEqual(response.status_code, 503, response.text)
                self.assertNotIn('proposed_order_qty', response.text)

    def test_rehashed_calculation_corruption_and_future_knowledge_fail_closed(self):
        original_digest = digest(self.catalog)
        for corruption in ('projection', 'future_knowledge'):
            reports = deepcopy({run_id: product._report(self.catalog, run_id) for run_id in self.catalog['reports']})
            binding = self.catalog['cutoffs'][0]['keys'][0]
            if corruption == 'projection':
                reports[binding['plan_run_id']]['result']['projection'][0]['balance_with_order'] = '999'
            else:
                # A later observed revision is not eligible at the earlier cutoff,
                # even after an attacker recomputes all content/input digests.
                for field in ('plan_run_id', 'forecast_run_id'):
                    reports[binding[field]]['result']['training']['day_versions'][0]['observed_at'] = '2026-01-06T08:00:00+00:00'
            changed = repackage(self.catalog, reports)
            with self.subTest(corruption=corruption):
                client = TestClient(create_app(product_evidence=changed))
                self.assertEqual(client.get('/api/product/overview').status_code, 503)
            self.assertEqual(digest(self.catalog), original_digest)

    def test_quantities_above_javascript_integer_limit_survive_public_transport(self):
        original_digest = digest(self.catalog)
        quantity = 9007199254740993
        reports = deepcopy({run_id: product._report(self.catalog, run_id) for run_id in self.catalog['reports']})
        chosen = self.catalog['cutoffs'][0]['keys'][0]
        key = (chosen['sku_id'], chosen['warehouse_id'])
        for report in reports.values():
            result = report.get('result', {})
            inventory = result.get('inventory')
            if not inventory or report['context']['origin_day'] != CUTOFFS[0]:
                continue
            for table, field in (('opening_balances', 'quantity'), ('snapshots', 'on_hand_qty')):
                for row in inventory['source'][table]:
                    if (row['sku_id'], row['warehouse_id']) == key:
                        row[field] = quantity
            if (report['context']['sku_id'], report['context']['warehouse_id']) == key:
                inventory['on_hand'] = quantity
                # Independent prefix arithmetic: -7,-6,-10,-14,-18, no order.
                result.update(inventory_position=quantity+2, end_projected_balance=str(quantity-18),
                              proposed_order_qty=0, unrounded_need='0', whole_piece_need=0,
                              rounding_extra=0, pre_arrival_shortage_days=[])
                for row, offset in zip(result['projection'], (7, 6, 10, 14, 18)):
                    row['balance_without_order'] = row['balance_with_order'] = str(quantity-offset)
        changed = repackage(self.catalog, reports)
        client = TestClient(create_app(product_evidence=changed))
        response = client.get('/api/product/detail', params=dict(cutoff=CUTOFFS[0],
                              sku_id=key[0], warehouse_id=key[1]))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['on_hand'], '9007199254740993')
        self.assertEqual(response.json()['proposed_order_qty'], '0')
        self.assertEqual(response.json()['exposure'], {'numerator': '9007199254740973', 'denominator': '1'})
        self.assertEqual(digest(self.catalog), original_digest)

    def test_source_catalog_is_immutable_under_reads_and_scenarios(self):
        before = digest(self.catalog)
        legacy = Path(__file__).resolve().parents[1]/'src/inventory_intelligence/lab_evidence.json'
        original = hashlib.sha256(legacy.read_bytes()).hexdigest()
        product.detail(self.catalog, CUTOFFS[0], *KEYS[0])
        product.history(self.catalog, *KEYS[0])
        product.scenario(self.catalog, CUTOFFS[0], *KEYS[0], {'demand_percent': 125})
        self.assertEqual(digest(self.catalog), before)
        self.assertEqual(hashlib.sha256(legacy.read_bytes()).hexdigest(), original)

    def test_original_report_hashes_and_isolated_global_failure_gate(self):
        for run_id, saved in self.catalog['reports'].items():
            self.assertEqual(digest(product._report(self.catalog, run_id)), saved['digest'])
        control = self.catalog['controls']['duplicate_inventory']
        failure = product._report(self.catalog, control['reliability_run_id'])
        blocked = product._report(self.catalog, control['plan_run_id'])
        self.assertEqual(failure['overall_status'], 'fail')
        self.assertTrue(failure['findings'])
        self.assertEqual(blocked['status'], 'not_assessable')
        self.assertIsNone(blocked['result']['proposed_order_qty'])
        changed = deepcopy(self.catalog)
        changed['cutoffs'][0]['reliability_run_id'] = control['reliability_run_id']
        changed['digest'] = product.archive_digest(changed)
        client = TestClient(create_app(product_evidence=changed))
        self.assertEqual(client.get('/api/product/explore').status_code, 503)
        self.assertEqual(client.get('/api/product/overview').status_code, 503)

    def test_inspectable_duplicate_control_has_exact_rows_and_does_not_poison_catalog(self):
        before = self.client.get('/api/product/overview', params={'cutoff': CUTOFFS[-1]}).json()
        response = self.client.get('/api/product/control', params={
            'name': 'duplicate_inventory', 'archive_digest': self.catalog['digest']})
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertTrue(result['synthetic'])
        self.assertEqual(result['archive_digest'], self.catalog['digest'])
        reliability = result['reliability']
        self.assertEqual(reliability['overall_status'], 'fail')
        self.assertEqual(next(check['status'] for check in reliability['checks']
                              if check['rule_id'] == 'R005'), 'fail')
        finding = next(finding for finding in reliability['findings']
                       if finding['reason'] == 'duplicate_snapshot')
        for field in ('expected_qty', 'observed_qty', 'delta_qty'):
            self.assertIsNone(finding[field])
        rows = finding['evidence']['source_records']
        self.assertEqual(len(rows), 2)
        self.assertEqual([row['record']['on_hand_qty'] for row in rows], ['22', '22'])
        self.assertEqual({(row['record']['sku_id'], row['record']['warehouse_id']) for row in rows},
                         {KEYS[0]})
        self.assertEqual(len({row['record']['row_id'] for row in rows}), 2)
        blocked = result['blocked_plan']
        self.assertEqual(blocked['status'], 'not_assessable')
        self.assertIsNone(blocked['proposed_order_qty'])
        self.assertIsNone(blocked['projection'])
        self.assertIn('nonpassing_or_missing_inventory_run', blocked['reasons'])
        self.assertEqual(blocked['run_id'], self.catalog['controls']['duplicate_inventory']['plan_run_id'])
        self.assertEqual(reliability['run_id'], self.catalog['controls']['duplicate_inventory']['reliability_run_id'])
        self.assertEqual(before['summary']['assessable'], 88)
        self.assertEqual(self.client.get('/api/product/overview', params={'cutoff': CUTOFFS[-1]}).json(), before)
        self.assertEqual(self.client.get('/api/product/control', params={'name': 'unknown'}).status_code, 422)
        self.assertEqual(self.client.get('/api/product/control', params={
            'name': 'duplicate_inventory', 'archive_digest': '0'*64}).status_code, 409)

    def test_legacy_lab_12_18_12_and_zero_denominator_remain_correct(self):
        baseline = self.client.get('/api/lab').json()
        self.assertEqual(baseline['baseline']['plan']['proposed_order_qty'], 12)
        spike = self.client.post('/api/scenarios', json={'demand_percent': 125}).json()
        self.assertEqual(spike['scenario']['plan']['proposed_order_qty'], 18)
        delay = self.client.post('/api/scenarios', json={'supplier_delay_days': 3}).json()
        self.assertEqual(delay['scenario']['plan']['proposed_order_qty'], 12)
        self.assertEqual(delay['scenario']['simulation']['metrics']['immediate_fill_rate'], '11/28')
        zero = self.client.post('/api/scenarios', json={'demand_percent': 0,
                                                     'reservation_qty': 0}).json()
        self.assertIsNone(zero['scenario']['simulation']['metrics']['immediate_fill_rate'])
        self.assertEqual(zero['scenario']['costs']['total'], '490')


if __name__ == '__main__':
    unittest.main()
