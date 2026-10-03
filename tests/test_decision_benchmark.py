"""Independent selection boundaries and retained offline evidence checks."""

from fractions import Fraction
import hashlib
import json
from pathlib import Path
import unittest

from scripts import decision_benchmark as benchmark


class DecisionBenchmarkTests(unittest.TestCase):
    def test_selection_floors_ties_and_holdout_cannot_reselect(self):
        scores = {method: dict(total_cost=100, immediate_fill_rate=Fraction(9, 10),
                               cycle_service=Fraction(4, 5))
                  for method in benchmark.CANDIDATES}
        self.assertEqual(benchmark.select(scores), "naive")
        scores["zero"]["total_cost"] = 1
        scores["zero"]["immediate_fill_rate"] = None
        scores["naive"]["cycle_service"] = Fraction(79, 100)
        self.assertEqual(benchmark.select(scores), "mean")
        scores["seasonal_naive"]["total_cost"] = 95
        chosen = benchmark.select(scores)
        self.assertEqual(chosen, "seasonal_naive")
        holdout = {method: dict(values) for method, values in scores.items()}
        holdout[chosen]["immediate_fill_rate"] = Fraction(89, 100)
        self.assertFalse(benchmark.promotion(chosen, holdout)["passed"])
        self.assertEqual(benchmark.select(scores), chosen)
        for values in scores.values():
            values["cycle_service"] = None
        self.assertIsNone(benchmark.select(scores))
        self.assertEqual(benchmark.promotion(None, holdout)["failures"],
                         ["no_selection_eligible_method"])

    def test_promotion_exact_cost_boundary_and_service_regression(self):
        scores = {method: dict(total_cost=100, immediate_fill_rate=1,
                               cycle_service=1) for method in benchmark.CANDIDATES}
        scores["naive"]["total_cost"] = 95
        result = benchmark.promotion("naive", scores)
        self.assertTrue(result["passed"])
        self.assertIs(type(result["relative_cost_reduction"]), Fraction)
        self.assertEqual(result["relative_cost_reduction"], Fraction(1, 20))
        scores["naive"]["total_cost"] = Fraction(951, 10)
        self.assertEqual(benchmark.promotion("naive", scores)["failures"],
                         ["cost_reduction_below_5_percent_or_zero_reference"])
        scores["naive"]["total_cost"] = 90
        scores["naive"]["cycle_service"] = Fraction(9, 10)
        self.assertEqual(benchmark.promotion("naive", scores)["failures"],
                         ["cycle_service_regression_or_unavailable"])
        scores["mean"]["total_cost"] = 0
        self.assertFalse(benchmark.promotion("mean", scores)["passed"])

    def test_retained_artifact_inputs_hashes_and_settled_obligations(self):
        root = Path(__file__).resolve().parents[1]
        report = json.loads((root / "docs/review/decision-benchmark.json").read_text())
        self.assertEqual(report["protocol_version"], "decision-benchmark-v1")
        self.assertEqual(len(report["scenarios"]), 60)
        self.assertEqual(report["summary"]["candidate_split_runs"], 480)
        for name, expected in report["source_sha256"].items():
            self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), expected)
        for row in report["scenarios"]:
            inputs = row["inputs"]
            encoded = json.dumps(inputs, sort_keys=True, separators=(",", ":")).encode()
            self.assertEqual(hashlib.sha256(encoded).hexdigest(), row["input_sha256"])
            self.assertEqual(inputs["selection_history"], inputs["train"])
            self.assertEqual(inputs["holdout_history"], inputs["train"] + inputs["selection"])
            self.assertEqual([len(inputs[key]) for key in ("train", "selection", "holdout")],
                             [56, 56, 56])
            for split in ("selection", "holdout"):
                self.assertEqual(set(row[split]), set(benchmark.CANDIDATES))
                for result in row[split].values():
                    terminal = result["terminal"]
                    self.assertEqual((terminal["backlog"], terminal["outstanding_qty"],
                                      terminal["orders"]), (0, 0, []))
                    costs = [Fraction(**result["metrics"][key])
                             for key in ("scored_cost", "runoff_cost", "total_cost")]
                    self.assertEqual(costs[0] + costs[1], costs[2])


if __name__ == "__main__":
    unittest.main()
