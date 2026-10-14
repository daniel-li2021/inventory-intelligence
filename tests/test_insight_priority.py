from copy import deepcopy
from pathlib import Path
import unittest

from inventory_intelligence.insights import discover
from inventory_intelligence.product import load_catalog


class PriorityTests(unittest.TestCase):
    def test_priority_and_independent_factor_values_preserve_rule_identity(self):
        catalog = load_catalog(Path(__file__).resolve().parents[1] / 'docs/review/dynamic-replay-v1.json.gz')
        result = discover(catalog, '2026-04-06')
        finding = next(f for f in result['findings'] if f['rule_id'] == 'I206')
        factors = finding['contributing_factors']
        self.assertEqual(factors['stock_pieces'], '10')
        self.assertEqual(factors['accepted_daily'], dict(numerator='3', denominator='1'))
        self.assertEqual(factors['reservation_pieces'], '3')
        self.assertEqual(factors['confirmed_inbound_pieces'], '5')
        self.assertEqual(factors['safety_pieces'], '2')
        self.assertEqual(factors['proposal_pieces'], '6')
        self.assertEqual(factors['pre_arrival_shortage_days'], '0')
        self.assertEqual([f['priority']['rank'] for f in result['findings']], list(range(1, len(result['findings']) + 1)))
        categories = [f['category'] for f in result['findings']]
        self.assertEqual(categories, sorted(categories, key=lambda c: {'risk':0,'opportunity':1}[c]))
        changed = deepcopy(catalog)
        changed['cutoffs'][0]['keys'].reverse()
        reordered = discover(changed, '2026-04-06')
        self.assertEqual(result['findings'], reordered['findings'])
        current = discover(catalog, '2026-04-13')['findings']
        self.assertTrue(all('causal effects' in f['contributing_factors']['boundary'] for f in current))
        self.assertTrue(all(f['missing_evidence'] for f in current))


if __name__ == '__main__':
    unittest.main()
