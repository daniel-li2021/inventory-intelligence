"""Independent cost reuse and frozen intermittent artifact checks."""

from fractions import Fraction
import hashlib
import json
import subprocess
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import intermittent_benchmark as benchmark


class IntermittentBenchmarkTests(unittest.TestCase):
    def test_saved_choices_use_selection_and_compare_frozen_references(self):
        """Independently audit every saved choice; never re-fit consumed holdouts."""
        report = json.loads((ROOT / "docs/review/intermittent-benchmark.json").read_text())
        order = report["configuration_order"]
        baseline_methods = {"naive", "mean", "seasonal_naive", "zero"}

        def eligible(metrics):
            return all(metrics[key] is not None and Fraction(**metrics[key]) >= floor
                       for key, floor in (("immediate_fill_rate", Fraction(9, 10)),
                                          ("cycle_service", Fraction(4, 5))))

        for row in report["scenarios"]:
            choices = {}
            for subset in ("overall", "baseline", "new_method"):
                options = [key for key in order
                           if (subset == "overall"
                               or (report["configurations"][key]["method"] in baseline_methods)
                               == (subset == "baseline"))
                           and eligible(row["selection"][key]["metrics"])]
                choices[subset] = min(options, key=lambda key: Fraction(**row["selection"][key]["metrics"]["total_cost"])) if options else None
            self.assertEqual(row["selected"], choices)
            for label, candidate_id, reference_id in (
                    ("overall_vs_fixed_mean", choices["overall"], "mean:fixed0"),
                    ("overall_vs_selected_baseline", choices["overall"], choices["baseline"]),
                    ("new_vs_selected_baseline", choices["new_method"], choices["baseline"])):
                passes = False
                if candidate_id is not None and reference_id is not None:
                    candidate = row["holdout"][candidate_id]["metrics"]
                    reference = row["holdout"][reference_id]["metrics"]
                    reference_cost = Fraction(**reference["total_cost"])
                    passes = (reference_cost > 0 and eligible(candidate)
                              and Fraction(**candidate["total_cost"]) <= reference_cost * Fraction(19, 20)
                              and all(candidate[key] is not None and reference[key] is not None
                                      and Fraction(**candidate[key]) >= Fraction(**reference[key])
                                      for key in ("immediate_fill_rate", "cycle_service")))
                self.assertEqual(row["comparisons"][label]["passed"], passes)
                self.assertEqual(row["comparisons"][label]["reference"], reference_id)
        self.assertEqual(report["summary"]["no_overall_selection"],
                         sum(row["selected"]["overall"] is None for row in report["scenarios"]))
        self.assertEqual(report["summary"]["both_reference_passes"], sum(
            row["comparisons"]["overall_vs_fixed_mean"]["passed"]
            and row["comparisons"]["overall_vs_selected_baseline"]["passed"]
            for row in report["scenarios"]))
        self.assertEqual(report["summary"]["new_vs_baseline_passes"], sum(
            row["comparisons"]["new_vs_selected_baseline"]["passed"]
            for row in report["scenarios"]))

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
        # Consumed evidence binds one complete original source, including deleted docs.
        snapshot = "f6d3d16034af038eda4c8687ea4f1ed6d2445ef6"
        artifact = "docs/review/intermittent-benchmark.json"
        self.assertEqual((ROOT / artifact).read_bytes(),
                         subprocess.check_output(["git", "show", f"{snapshot}:{artifact}"], cwd=ROOT))
        for name, expected in report["source_sha256"].items():
            raw = subprocess.check_output(["git", "show", f"{snapshot}:{name}"], cwd=ROOT)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), expected)
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
