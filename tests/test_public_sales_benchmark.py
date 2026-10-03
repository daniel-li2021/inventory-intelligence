"""Independent split, train-only subset and aggregate forecast score oracles."""

from copy import deepcopy
from fractions import Fraction
import json
import unittest

from scripts.public_sales_benchmark import END, HOLDOUT_START, aggregate, canonical, evaluate, scores, select_items


class PublicBenchmarkOracles(unittest.TestCase):
    def test_large_exact_rationals_round_trip_without_decimal_limit_changes(self):
        import sys
        before = sys.get_int_max_str_digits()
        value = Fraction(-(10 ** 5000 + 1), 7)
        encoded = json.loads(canonical(dict(value=value)))
        decoded = encoded["value"]
        self.assertEqual(Fraction(int(decoded["numerator_hex"], 16), int(decoded["denominator_hex"], 16)), value)
        self.assertEqual(sys.get_int_max_str_digits(), before)

    def extraction(self):
        return dict(audit=dict(status="assessable"), series={"constant": [3] * (END + 1),
            "weekly": ([0, 1, 2, 3, 4, 5, 6] * 54)[:END + 1], "zero": [0] * (END + 1)},
            source_seen_days={key: ["2010-12-01"] for key in ("constant", "weekly", "zero")})

    def test_exact_error_totals_and_denominators(self):
        result = scores([1] * 7 + [3] * 7, method="mean", start=7, end=14, horizon=7)
        self.assertEqual((result["origins"], result["points"], result["actual_units"]), (1, 7, 21))
        score = aggregate([result])
        self.assertEqual(score["mae"], 2)
        self.assertEqual(score["bias"], -2)
        self.assertEqual(score["wape"], Fraction(2, 3))
        self.assertEqual(score["cumulative_mae"], 14)
        self.assertEqual(score["cumulative_bias"], -14)
        zero = aggregate([scores([1] * 7 + [0] * 7, method="mean", start=7, end=14, horizon=7)])
        self.assertIsNone(zero["wape"])
        self.assertEqual(zero["mae"], 1)

    def test_training_only_subset_does_not_depend_on_future_items_or_volume(self):
        original = self.extraction()
        before = select_items(original)
        changed = deepcopy(original)
        for series in changed["series"].values():
            series[HOLDOUT_START:] = [999] * (END + 1 - HOLDOUT_START)
        changed["series"]["future_only"] = [888] * (END + 1)
        changed["source_seen_days"]["future_only"] = ["2011-11-11"]
        self.assertEqual(before, select_items(changed))
        self.assertNotIn("future_only", before["selected"])

    def test_hand_control_selection_and_final_partial_day_excluded(self):
        adapted = self.extraction()
        report, local = evaluate(adapted)
        self.assertEqual(local["item_results"]["constant"]["selected_method"], "naive")
        self.assertEqual(local["item_results"]["weekly"]["selected_method"], "seasonal_naive")
        self.assertEqual(local["item_results"]["zero"]["selected_method"], "naive")
        self.assertEqual(report["aggregate_scores"]["holdout"]["28"]["overall"]["selection_chosen"]["mae"], 0)
        self.assertEqual(report["aggregate_scores"]["holdout"]["28"]["overall"]["selection_chosen"]["origins"], 3)
        for values in adapted["series"].values(): values[-1] = 999999
        changed, _ = evaluate(adapted)
        self.assertEqual(report, changed)

    def test_holdout_cannot_reselect_model_or_change_selection_scores(self):
        adapted = self.extraction()
        _, before = evaluate(adapted)
        adapted["series"]["constant"][HOLDOUT_START:] = [0] * (END + 1 - HOLDOUT_START)
        _, after = evaluate(adapted)
        old, new = before["item_results"]["constant"], after["item_results"]["constant"]
        self.assertEqual(old["selected_method"], new["selected_method"])
        self.assertEqual(old["scores"]["selection"], new["scores"]["selection"])

    def test_nonoverlapping_split_targets_and_overlapping_fold_denominators(self):
        result = scores([1] * 28, method="naive", start=7, end=28, horizon=14)
        self.assertEqual((result["origins"], result["points"], result["actual_units"]), (2, 28, 28))
        self.assertTrue(all(row["origin"] + 14 <= 28 for row in result["origin_receipts"]))
        missing = self.extraction(); missing["audit"]["status"] = "not_assessable"
        with self.assertRaises(ValueError): select_items(missing)
        for h in (0, True):
            with self.assertRaises(ValueError): scores([1] * 28, method="naive", start=7, end=28, horizon=h)


if __name__ == "__main__":
    unittest.main()
