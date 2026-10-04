"""Independent hand controls for the continuation's oracle and frozen query guard."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.engineering_confirmation import expected_backtest
from scripts.engineering_benchmark import worker, Pilot, Budget
from scripts.engineering_network import driver


class ConfirmationControls(unittest.TestCase):
    def test_hand_first_fold_predictions_and_truth(self):
        first=expected_backtest(180)["folds"][0]
        self.assertEqual(first["origin_day"],"2025-08-03")
        self.assertEqual(first["training"],([0]*3+[10]*7)*2+[0]*3+[10]*5)
        self.assertEqual(first["actual"],[10,10]+([0]*3+[10]*7)*2+[0]*3+[10]*3)
        self.assertEqual(first["predictions"]["naive"],["10"]*28)
        self.assertEqual(first["predictions"]["mean"],["95/14"]*28)
        self.assertEqual(first["predictions"]["seasonal_naive"],(["0","0"]+["10"]*5)*4)

    def test_fractional_zero_quota_is_declared_and_global_allocation_exact(self):
        single=expected_backtest(365)["folds"][-1]
        self.assertEqual((single["training"]+single["actual"]).count(0),109)
        counts=[]
        for key in range(10):
            fold=expected_backtest(365,10,key)["folds"][-1]
            counts.append((fold["training"]+fold["actual"]).count(0))
        self.assertEqual(counts,[110]*5+[109]*5)
        self.assertEqual(sum(counts),1095)

    def test_unchanged_holdout_does_not_enter_selection(self):
        oracle=expected_backtest(180)
        self.assertEqual(len(oracle["folds"]),15)
        self.assertEqual(oracle["selection"]["28"]["scored_points"],14*28)
        self.assertEqual(oracle["holdout_scores"]["28"]["scored_points"],28)

    def test_changed_frozen_sql_rejected_before_connection(self):
        with tempfile.TemporaryDirectory() as directory:
            query=Path(directory)/"query.sql"; query.write_text("changed")
            path=Path(directory)/"spec.json"
            path.write_text(json.dumps(dict(query_path=str(query),query_sha256="0"*64)))
            with self.assertRaisesRegex(ValueError,"frozen comparison SQL changed"):
                worker(path)

    def test_measurement_labels_cannot_hide_a_failed_observation(self):
        pilot=object.__new__(Pilot)
        with self.assertRaisesRegex(ValueError,"cannot override observed outcomes"):
            pilot.measure("case","run_checks",{},measurement_context=dict(status="completed",oracle="pass"))

    def test_fast_client_observes_the_entire_offered_window(self):
        fake=dict(route="evidence",http_status=200,outcome="succeeded",scheduler_lag_ns=0,planned_ns=0,
            issued_to_complete_ns=1,scheduled_to_complete_ns=1)
        with tempfile.TemporaryDirectory() as directory, patch('scripts.engineering_network.request',return_value=fake):
            path=Path(directory)/"window.jsonl"
            driver("http://unused",path,1,1,"evidence",0)
            r=json.loads(path.with_suffix('.summary.json').read_text())
        self.assertEqual(r['issued'],1)
        self.assertGreaterEqual(r['elapsed_seconds'],1)
        self.assertTrue(r['observation_window_closed'])

    def test_completed_request_survives_clock_interruption(self):
        fake=dict(route='evidence',planned_ns=0,outcome='succeeded')
        with tempfile.TemporaryDirectory() as directory, patch('scripts.engineering_network.request',return_value=fake), \
                patch('scripts.engineering_network.time.time',side_effect=[100,100,103]):
            path=Path(directory)/'interrupted.jsonl'
            with self.assertRaisesRegex(RuntimeError,'clock discontinuity'):
                driver('http://unused',path,1,1,'evidence',0)
            self.assertFalse(path.exists())
            self.assertEqual(json.loads(path.with_suffix('.partial.jsonl').read_text()),fake)

    def test_wall_budget_counts_time_omitted_by_active_clock(self):
        budget=object.__new__(Budget)
        budget.start=200; budget.wall_start=100; budget.wall_seconds=60
        with patch('scripts.engineering_benchmark.time.monotonic',return_value=210), \
                patch('scripts.engineering_benchmark.time.time',return_value=161):
            with self.assertRaisesRegex(RuntimeError,'wall budget exhausted'): budget.guard()


if __name__=="__main__": unittest.main()
