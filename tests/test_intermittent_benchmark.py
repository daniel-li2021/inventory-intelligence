"""Independent cost reuse and frozen intermittent artifact checks."""

from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import intermittent_benchmark as benchmark


class IntermittentBenchmarkTests(unittest.TestCase):
    def test_exact_repricing_reuses_physical_outcomes_without_mutation(self):
        summary = dict(metrics=dict(scored_cost=99, immediate_fill_rate=Fraction(2, 3)),
                       exposures=dict(scored=dict(on_hand=3, backlog=2, orders=1),
                                      runoff=dict(on_hand=1, backlog=1, orders=0)))
        rates = dict(holding_cost=Fraction(1, 2), backlog_cost=Fraction(5, 2),
                     order_cost=Fraction(3, 2))
        actual = benchmark.reprice(summary, rates)
        self.assertEqual(actual["scored_cost"], 8)
        self.assertEqual(actual["runoff_cost"], 3)
        self.assertEqual(actual["total_cost"], 11)
        self.assertEqual(actual["immediate_fill_rate"], Fraction(2, 3))
        self.assertEqual(summary["metrics"]["scored_cost"], 99)
        actual["immediate_fill_rate"] = 0
        self.assertEqual(summary["metrics"]["immediate_fill_rate"], Fraction(2, 3))

    def test_reference_absence_and_holdout_service_cannot_change_selection(self):
        configs = ["mean", "sba"]
        selection = dict(mean=dict(total_cost=100, immediate_fill_rate=1, cycle_service=1),
                         sba=dict(total_cost=95, immediate_fill_rate=1, cycle_service=1))
        self.assertEqual(benchmark.select(selection, configs), "sba")
        self.assertTrue(benchmark.compare("sba", "mean", selection)["passed"])
        holdout = {key: dict(value) for key, value in selection.items()}
        holdout["sba"]["cycle_service"] = Fraction(1, 2)
        self.assertFalse(benchmark.compare("sba", "mean", holdout)["passed"])
        self.assertEqual(benchmark.select(selection, configs), "sba")
        self.assertEqual(benchmark.compare("sba", None, holdout)["failures"],
                         ["no_selection_eligible_baseline"])
        self.assertFalse(benchmark.compare(None, "mean", holdout)["passed"])

    def test_retained_protocol_provenance_completed_calibration_and_terminals(self):
        report = json.loads((ROOT / "docs/review/intermittent-benchmark.json").read_text())
        self.assertEqual(report["protocol_version"], "intermittent-research-v1")
        self.assertEqual((len(report["scenarios"]), len(report["configurations"])), (84, 33))
        self.assertEqual(report["summary"]["candidate_split_results"], 5544)
        for path, expected in report["source_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), expected)
        for row in report["scenarios"]:
            inputs = row["inputs"]
            encoded = json.dumps(inputs, sort_keys=True, separators=(",", ":")).encode()
            self.assertEqual(hashlib.sha256(encoded).hexdigest(), row["input_sha256"])
            self.assertEqual(inputs["selection_history"], inputs["train"])
            self.assertEqual(inputs["holdout_history"], inputs["train"] + inputs["selection"])
            self.assertEqual([len(inputs[key]) for key in ("train", "selection", "holdout")],
                             [112, 56, 56])
            self.assertEqual(inputs["train"] + inputs["selection"] + inputs["holdout"],
                             benchmark.observations(inputs["family"], inputs["seed"]))
            for split in ("selection", "holdout"):
                for value in row[split].values():
                    self.assertEqual((value["terminal"]["backlog"], value["terminal"]["outstanding_qty"]),
                                     (0, 0))
                    costs = [Fraction(**value["metrics"][key])
                             for key in ("scored_cost", "runoff_cost", "total_cost")]
                    self.assertEqual(costs[0] + costs[1], costs[2])
                for reviews in row["review_evidence"][split].values():
                    for review in reviews:
                        calibration = review.get("calibration")
                        if calibration is not None:
                            known = len(inputs[f"{split}_history"]) + review["day"]
                            self.assertTrue(all(origin + 9 <= known
                                                for origin in calibration["origins"]))
                            self.assertGreaterEqual(calibration["count"], 8)


if __name__ == "__main__":
    unittest.main()
