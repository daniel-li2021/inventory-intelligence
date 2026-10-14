"""Retained counterbalanced real-planner reports, independent exact controls."""
from collections import defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


class PlanningJitSavedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(gzip.decompress((ROOT/'docs/review/planning-jit-v1.json.gz').read_bytes()))
        cls.protocol=json.loads((ROOT/'docs/examples/planning-jit-v1.json').read_text())

    def test_frozen_grid_and_unchanged_sources(self):
        self.assertEqual(self.report['protocol'],self.protocol)
        self.assertEqual(len(self.report['samples']),64)
        self.assertEqual(self.report['runtime']['server_version'],170009)
        self.assertLess(self.report['wall_seconds'],self.protocol['wall_cap_seconds'])
        self.assertFalse(self.report['setting_leak'])
        for cell in self.report['cells']:self.assertEqual(cell['source_before'],cell['source_after'])
        self.assertEqual(self.report['source_hashes']['docs/examples/planning-jit-v1.json'],
                         hashlib.sha256((ROOT/'docs/examples/planning-jit-v1.json').read_bytes()).hexdigest())

    def test_independent_order_and_negative_source_controls(self):
        for sample in self.report['samples']:
            report=sample['report'];result=report['result']
            if sample['state']=='clean':
                self.assertEqual(report['status'],'assessable')
                self.assertEqual(result['proposed_order_qty'],30)
                self.assertEqual([p['balance_without_order'] for p in result['projection']],['10','8','1','-6','-13','-20','-27'])
            else:
                self.assertEqual(report['status'],'not_assessable')
                self.assertIsNone(result['proposed_order_qty'])
                self.assertIn('current_inventory_revalidation_failed',result['reasons'])

    def test_every_arm_has_equal_exact_persisted_semantics(self):
        groups=defaultdict(list)
        for sample in self.report['samples']:
            value={k:v for k,v in sample['report'].items() if k not in ('run_id','created_at')}
            self.assertEqual(sample['semantic_sha256'],hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest())
            groups[(sample['keys'],sample['state'])].append(value)
        for values in groups.values():self.assertTrue(all(v==values[0] for v in values))

    def test_negative_adoption_finding_is_retained(self):
        large=next(c for c in self.report['cells'] if c['keys']==1000 and c['state']=='clean')
        small=next(c for c in self.report['cells'] if c['keys']==1 and c['state']=='clean')
        gate=large['reduction_fraction']>=.2 and small['added_seconds']<=.01
        self.assertEqual(self.report['adoption_gate_passed'],gate)
        self.assertFalse(gate)


if __name__=='__main__':unittest.main()
