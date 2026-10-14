"""Independent arithmetic, split-boundary and saved actual-execution controls."""
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import unittest

from inventory_intelligence.forecast_decision_study import accuracy, audit, conclusions, METHODS

ROOT=Path(__file__).resolve().parents[1]


class ForecastDecisionStudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol=json.loads((ROOT/'docs/examples/forecast-decision-study-v1.json').read_text())
        cls.report=json.loads(gzip.decompress((ROOT/'docs/review/forecast-decision-study-v1.json.gz').read_bytes()))

    def test_saved_actual_restricted_execution_matches_independent_oracles(self):
        receipt=audit(self.report,self.protocol)
        self.assertEqual((receipt['loops'],receipt['reviews'],receipt['independent_paths']),(48,144,16))
        self.assertEqual(self.report['runtime']['server_version']//10000,17)
        self.assertIsNone(self.report['conclusions']['promoted_policy'])

    def test_compact_workbench_summary_binds_exact_original_report(self):
        summary=json.loads((ROOT/'docs/review/forecast-decision-summary-v1.json').read_text())
        self.assertEqual(summary['source_artifact_sha256'],hashlib.sha256((ROOT/'docs/review/forecast-decision-study-v1.json.gz').read_bytes()).hexdigest())
        self.assertEqual(summary['protocol_sha256'],self.report['protocol_sha256'])
        self.assertEqual(len(summary['families']),8)
        for row in summary['families']:
            for method,arm in row['arms'].items():
                cell=self.report['cells'][row['family']+':evaluation'][method]
                self.assertEqual({k:arm[k] for k in cell['case']['summary']},cell['case']['summary'])
                self.assertEqual(arm['accuracy'],cell['accuracy'])
                self.assertEqual(arm['selection_accuracy'],self.report['cells'][row['family']+':selection'][method]['accuracy'])

    def test_selection_and_evaluation_are_fresh_distinct_paths(self):
        by_id={r['id']:r for r in self.protocol['traces']}
        for family in {r['family'] for r in by_id.values()}:
            self.assertNotEqual(by_id[family+':selection']['history'],by_id[family+':evaluation']['history'])

    def test_accuracy_independent_of_kernel_and_exact_zero_denominator(self):
        for trace in self.protocol['traces']:
            for method in METHODS:self.assertEqual(accuracy(trace,method),accuracy(trace,method,independent=True))
        quiet=dict(history=[0]*28,demand=[0]*9)
        self.assertEqual(accuracy(quiet,'mean')['mae'],'0')
        self.assertIsNone(accuracy(quiet,'mean')['wape'])

    def test_evaluation_never_reselects(self):
        cells=deepcopy(self.report['cells'])
        for key,arms in cells.items():
            if key.endswith(':evaluation'):
                for method,arm in arms.items():arm['accuracy']['mae']='0' if method=='naive' else '9999'
        before=conclusions(self.report['cells'],self.protocol)
        after=conclusions(cells,self.protocol)
        self.assertEqual([r['selected_from_selection'] for r in before['families']],
                         [r['selected_from_selection'] for r in after['families']])

    def test_losing_policy_and_negative_controls_cannot_be_removed(self):
        changed=deepcopy(self.report);del changed['cells']['weekly:evaluation']['mean']
        with self.assertRaisesRegex(ValueError,'Losing policy'):audit(changed,self.protocol)
        blocked=self.report['cells']['blocked-recovery:evaluation']
        self.assertTrue(all(all(r['report']['status']=='not_assessable' for r in arm['case']['reviews']) for arm in blocked.values()))
        self.assertTrue(any(r['unique_cost_winner'] is None for r in self.report['conclusions']['families']))

    def test_forecast_cost_and_selection_corruption_reject(self):
        for field in ('forecast','cost','score','selection'):
            changed=deepcopy(self.report);cell=changed['cells']['weekly:evaluation']['seasonal_naive']
            if field=='forecast':cell['case']['reviews'][0]['report']['result']['forecast']['predictions'][0]='999'
            elif field=='cost':cell['case']['days'][0]['cost']['purchase']+=1
            elif field=='score':cell['accuracy']['mae']='999'
            else:changed['conclusions']['families'][0]['selected_from_selection']='invented'
            with self.subTest(field=field),self.assertRaises(ValueError):audit(changed,self.protocol)


if __name__=='__main__':unittest.main()
