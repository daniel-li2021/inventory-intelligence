"""Delivery identity, historical kernel binding and rehashed graph corruption."""
import copy
import unittest

from scripts import research_lineage as study


class ResearchLineageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.manifest=study.build()

    def test_complete_deliveries_and_independent_historical_kernel_binding(self):
        m=self.manifest
        self.assertEqual(set(m['deliveries']),{str(n) for n in range(14,24)})
        self.assertEqual(m['summary']['artifacts'],24)
        self.assertEqual(m['summary']['source_maps'],17)
        self.assertEqual(m['summary']['parent_bindings'],5)
        self.assertEqual(m['source_snapshots']['docs/review/intermittent-benchmark.json'],study.BASE)
        drift=m['historical_current_drift']
        self.assertEqual(len(drift),13)
        self.assertEqual({r['source'] for r in drift},{'src/inventory_intelligence/decision.py','pyproject.toml'})
        kernel=[r for r in drift if r['source'].endswith('/decision.py')]
        self.assertEqual(len(kernel),12)
        self.assertTrue(all(r['historical_sha256']=='f68d13d43b74c1233d94e2c67cfc7a709298c14c8b5a4b5a349c65bc5d1e57db' for r in kernel))
        self.assertEqual(study.audit(m),m['summary'])

    def test_parent_edges_bind_actual_retained_reports(self):
        nodes=self.manifest['nodes']
        self.assertIn('artifact:docs/review/public-sales-forecast-v1.json',nodes['artifact:docs/review/public-sales-safety-v1.json']['depends_on'])
        self.assertIn('artifact:docs/review/public-calibration-freeze-v1.json',nodes['artifact:docs/review/public-calibration-v1.json']['depends_on'])
        self.assertEqual(nodes['artifact:src/inventory_intelligence/lab_evidence.json']['delivery'],'core')
        self.assertTrue(all(n['local_verification']=='not performed by manifest' for n in nodes.values() if n['kind']=='declared_external_fingerprint'))

    def test_changed_bindings_graph_counts_and_candidate_fail(self):
        def rejected(change):
            m=copy.deepcopy(self.manifest);change(m)
            with self.assertRaises(ValueError): study.audit(m)
        rejected(lambda m:m.update(candidate_commit=study.BASE))
        rejected(lambda m:m['summary'].update(artifacts=23))
        rejected(lambda m:m.update(historical_current_drift=[]))
        rejected(lambda m:m['nodes']['artifact:docs/review/public-sales-safety-v1.json'].update(sha256='0'*64))
        rejected(lambda m:m['nodes']['artifact:docs/review/public-sales-safety-v1.json'].update(depends_on=[]))
        rejected(lambda m:m['nodes']['artifact:docs/review/public-sales-safety-v1.json']['depends_on'].append('missing'))
        rejected(lambda m:m['nodes']['artifact:docs/review/public-sales-safety-v1.json']['depends_on'].append('artifact:docs/review/public-sales-safety-v1.json'))

    def test_source_paths_cannot_escape_repository(self):
        for name in ('../private-data','/tmp/source','docs/../../secret'):
            self.assertFalse(study.path_ok(name))
        self.assertTrue(study.path_ok('src/inventory_intelligence/decision.py'))
