"""Independent frozen arithmetic and durable conservation/negative controls."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from inventory_intelligence.transfers import compare, TransferJournal
from inventory_intelligence.supplier_feasibility import example_profile


class TransfersTest(unittest.TestCase):
    def setUp(self):
        self.profile = dict(version_id='control-v1', known_day='2026-06-01', transit_days=1,
                            capacity=24, setup_cost=4, per_piece_cost=1)
        self.supplier = example_profile('2026-06-01', 'a', 'recipient')
        for row in self.supplier['capacity']: row['capacity'] = 24
        policy = dict(lead_days=2, review_days=3, safety_qty=2, pack_size=6, moq=6)
        def location(stock, demand, order, digest):
            return dict(stock=stock, demand=demand+[0]*23, reservations=[], inbound=[], report=dict(
                run_id=digest, input_digest=digest, result=dict(inventory=dict(on_hand=stock),
                proposed_order_qty=order, supply=dict(policy=policy, inbound=[], reservations=[]),
                forecast=dict(predictions=[3]*5))))
        self.donor = location(30, [1]*5, 0, 'd')
        self.recipient = location(0, [3]*5, 18, 'r')

    def calculation(self, quantity=12, recipient='recipient', supplier=True):
        with patch('inventory_intelligence.transfers._inputs', side_effect=lambda c,d,s,w:deepcopy(self.donor if w=='donor' else self.recipient)):
            return compare(dict(digest='a'*64), '2026-06-01', 'a', 'donor', recipient, quantity,
                           self.profile, self.supplier if supplier else None)

    def test_frozen_arithmetic_network_donor_and_costs(self):
        expected = json.loads(Path('docs/examples/transfer-controls-v1.json').read_text())['independent_expected']
        result = self.calculation()
        self.assertEqual(int(result['safe_surplus']), expected['safe_surplus'])
        for name in ('no_action', 'purchase_only', 'transfer_before_purchase'):
            arm = result['arms'][name]
            self.assertEqual(int(arm['total_cost']), expected[name+'_total_cost'])
            self.assertEqual(arm['donor']['immediate_fulfilled'], '5')
            self.assertEqual(int(arm['network_pieces']), int(arm['terminal_pieces'])+int(arm['donor']['consumed'])+int(arm['recipient']['consumed']))
        arm = result['arms']['transfer_before_purchase']
        self.assertEqual(arm['purchase_quantity'], '6')
        self.assertEqual(arm['donor']['terminal_stock'], '13')
        self.assertEqual(arm['recipient']['terminal_stock'], '3')

    def test_transport_economics_retains_losing_transfer(self):
        self.profile['setup_cost'] = 2000
        result = self.calculation()
        self.assertGreater(int(result['arms']['transfer_before_purchase']['total_cost']),
                           int(result['arms']['purchase_only']['total_cost']))

    def test_unsafe_capacity_missing_and_future(self):
        self.assertEqual(self.calculation(24)['status'], 'not_assessable')
        self.profile['capacity'] = 11
        self.assertIsNone(self.calculation()['arms'])
        self.profile['capacity'] = 24
        missing = self.calculation(supplier=False)
        self.assertEqual(missing['arms']['purchase_only']['status'], 'not_assessable')
        self.assertEqual(missing['arms']['no_action']['total_cost'], '5545')
        self.profile['known_day'] = '2026-06-02'
        with self.assertRaises(ValueError): self.calculation()
        with self.assertRaises(ValueError): self.calculation(True)

    def test_durable_partial_history_idempotency_and_negative(self):
        with TemporaryDirectory() as folder:
            path = Path(folder)/'journal.sqlite'; journal = TransferJournal(path)
            result = self.calculation(); admitted = journal._reserve(result); identity = admitted['id']
            self.assertEqual(journal._reserve(result), admitted)
            self.assertEqual(journal.supply_effects('2026-06-03','a','donor')['reservations'][0]['due_day'],'2026-06-01')
            self.assertEqual(journal.snapshot('2026-05-31')['transfers'], [])
            journal.record(identity, 'dispatch', 'dispatch', '2026-06-01')
            with self.assertRaises(ValueError): journal.record(identity, 'early', 'receipt', '2026-06-01', 1)
            journal.record(identity, 'part', 'receipt', '2026-06-02', 5)
            self.assertEqual(TransferJournal(path).snapshot('2026-06-02')['transfers'][0]['in_transit'], '7')
            journal.record(identity, 'part', 'receipt', '2026-06-02', 5)
            with self.assertRaises(ValueError): journal.record(identity, 'excess', 'receipt', '2026-06-02', 8)
            journal.record(identity, 'rest', 'receipt', '2026-06-03', 7)
            self.assertEqual(journal.snapshot('2026-06-03')['transfers'][0]['received'], '12')
            self.assertEqual(journal.snapshot('2026-06-01')['transfers'][0]['in_transit'], '12')
            changed = deepcopy(result); changed['donor_input_digest'] = 'new'
            changed['binding']['cutoff'] = '2026-06-04'
            with self.assertRaises(ValueError): journal._reserve(changed)
            with sqlite3.connect(path) as conn:
                with self.assertRaises(sqlite3.IntegrityError): conn.execute('DELETE FROM transfers')
                with self.assertRaises(sqlite3.IntegrityError): conn.execute('UPDATE transfer_events SET known_day="2026-07-01"')

    def test_conflicting_transport_version_cannot_relabel_new_route(self):
        with TemporaryDirectory() as folder:
            journal=TransferJournal(Path(folder)/'journal.sqlite')
            first=self.calculation();journal._reserve(first)
            second=deepcopy(first);second['binding']['recipient_id']='recipient-two'
            second['binding']['transport_profile']['transit_days']='2'
            with self.assertRaisesRegex(ValueError,'Conflicting immutable transport version'):
                journal._reserve(second)
            self.assertEqual(len(journal.snapshot('2026-06-01')['transfers']),1)

    def test_concurrent_donor_reservations_and_rollback(self):
        with TemporaryDirectory() as folder:
            path = Path(folder)/'journal.sqlite'; journal = TransferJournal(path)
            a = self.calculation(); b = deepcopy(a)
            b['binding']['recipient_id'] = 'recipient-two'
            def reserve(result):
                try: journal._reserve(result); return 'admitted'
                except ValueError: return 'blocked'
            with ThreadPoolExecutor(2) as pool:
                self.assertEqual(sorted(pool.map(reserve, [a,b])), ['admitted','blocked'])
            snapshot = journal.snapshot('2026-06-01')
            self.assertEqual(len(snapshot['transfers']), 1)
            with sqlite3.connect(path) as conn:
                conn.execute("CREATE TRIGGER fail_dispatch BEFORE INSERT ON transfer_events WHEN json_extract(NEW.payload,'$.kind')='dispatch' BEGIN SELECT RAISE(ABORT,'forced failure'); END")
            with self.assertRaises(sqlite3.IntegrityError): journal.record(snapshot['transfers'][0]['id'], 'fail', 'dispatch', '2026-06-01')
            self.assertEqual(journal.snapshot('2026-06-01'), snapshot)

    def test_reservation_cannot_bypass_full_event_envelope(self):
        with TemporaryDirectory() as folder:
            path=Path(folder)/'journal.sqlite';journal=TransferJournal(path)
            result=self.calculation();admitted=journal._reserve(result)
            journal.record(admitted['id'],'dispatch','dispatch','2026-06-01')
            for i in range(254):
                journal.record(admitted['id'],f'notice-{i}','eta','2026-06-01',eta='2026-06-02')
            before=journal.snapshot('2026-06-01')
            self.assertEqual(len(before['events']),256)
            another=deepcopy(result);another['binding']['sku_id']='another-item'
            with self.assertRaisesRegex(ValueError,'Transfer event limit'):
                journal._reserve(another)
            reopened=TransferJournal(path)
            self.assertEqual(reopened.snapshot('2026-06-01'),before)
            self.assertEqual(reopened._reserve(result),admitted)

    def test_real_catalog_adapter_and_missing_donor(self):
        from inventory_intelligence.product import load_catalog
        catalog = load_catalog(Path('docs/review/dynamic-replay-v1.json.gz'))
        result = compare(catalog, '2026-04-06', 'product-dynamic:a', 'product-dynamic:upland', 'product-dynamic:harbor', 12,
                         dict(self.profile, known_day='2026-04-06'), None)
        self.assertEqual(result['status'], 'not_assessable')
        self.assertEqual(result['safe_surplus'], '0')
        blocked = compare(catalog, '2026-04-06', 'product-dynamic:b', 'product-dynamic:upland', 'product-dynamic:harbor', 1,
                          dict(self.profile, known_day='2026-04-06'), None)
        self.assertEqual(blocked['status'], 'not_assessable')
        self.assertIsNone(blocked['arms'])


if __name__ == '__main__': unittest.main()
