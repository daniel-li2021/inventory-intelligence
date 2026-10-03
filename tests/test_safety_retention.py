"""Hand-computed residual retention and identical-forecast simulation controls."""

from fractions import Fraction
import unittest

from inventory_intelligence.safety_retention import calibrate, retained_quantile, simulate
from scripts.safety_retention_benchmark import fresh_inputs, gate


class RetentionOracles(unittest.TestCase):
    def test_recent_quantile_truncates_old_labels_and_clips_negative_safety(self):
        errors = [-6, 4, -8, 3]
        low = retained_quantile(errors, quantile=Fraction(1, 2), retention="recent", window=2, min_samples=2)
        self.assertEqual(low["errors"], [-8, 3])
        self.assertEqual(low["count"], 2)
        self.assertEqual(low["source_count"], 4)
        self.assertEqual(low["quantile_error"], -8)
        self.assertEqual(low["safety_qty"], 0)
        high = retained_quantile(errors, quantile=Fraction(3, 4), retention="recent", window=2, min_samples=2)
        self.assertEqual(high["rank"], 2)
        self.assertEqual(high["safety_qty"], 3)
        self.assertEqual(high["effective_sample_count"], 2)

    def test_weighted_rank_effective_count_and_recency_direction(self):
        # Weights [1/4,1/2,1], mass7/4, threshold21/16. The two most recent
        # zero errors have mass3/2, so weighted q75 is0; unweighted q75 is10.
        args = dict(quantile=Fraction(3, 4), min_samples=3)
        weighted = retained_quantile([10, 0, 0], retention="decay", decay=Fraction(1, 2), **args)
        self.assertEqual(weighted["weights"], [Fraction(1, 4), Fraction(1, 2), 1])
        self.assertEqual(weighted["threshold_mass"], Fraction(21, 16))
        self.assertEqual(weighted["effective_sample_count"], Fraction(7, 3))
        self.assertEqual(weighted["safety_qty"], 0)
        self.assertEqual(retained_quantile([10, 0, 0], retention="expanding", **args)["safety_qty"], 10)
        self.assertEqual(retained_quantile([0, 0, 10], retention="decay", decay=Fraction(1, 2), **args)["safety_qty"], 10)
        self.assertEqual(retained_quantile([10, 0, 0], retention="decay", decay=1, **args)["safety_qty"], 10)

    def test_fractional_ceiling_and_weighted_threshold_equality(self):
        result = retained_quantile([Fraction(1, 3), Fraction(2, 3)], quantile=1,
                                    retention="recent", min_samples=2)
        self.assertEqual(result["quantile_error"], Fraction(2, 3))
        self.assertEqual(result["safety_qty"], 1)
        result = retained_quantile([1, 2], quantile=Fraction(1, 3), retention="decay",
                                    decay=Fraction(1, 2), min_samples=2)
        self.assertEqual(result["quantile_error"], 1)

    def test_completed_targets_only_with_global_fit_origins_preserved(self):
        history = [4, 1, 1, 2, 4, 0, 0, 3, 0]
        args = dict(method="naive", horizon=2, quantile=Fraction(3, 4),
                    retention="recent", window=2, min_train=1, min_samples=2)
        result = calibrate(history, **args)
        self.assertEqual(result["origins"], [5, 7])
        self.assertEqual(result["errors"], [-8, 3])
        self.assertEqual(result, calibrate(history + [999], **args))

    def test_minimum_and_invalid_inputs_fail_instead_of_zero_safety(self):
        for changes in (dict(errors=[]), dict(errors=[None] * 8), dict(errors=[1.0] * 8),
                        dict(retention="unknown"), dict(window=7), dict(decay=0),
                        dict(quantile=True), dict(window=True), dict(min_samples=0)):
            args = dict(errors=[1] * 8, quantile=Fraction(9, 10), retention="recent")
            args.update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                retained_quantile(**args)
        with self.assertRaises(ValueError):
            simulate([0] * 43, [1], retention="recent", on_hand=0, lead_days=1, review_days=1)

    def test_point_forecast_and_prefix_invariance_across_retention_policies(self):
        history = [0, 0, 8, 0] * 12
        args = dict(on_hand=2, lead_days=1, review_days=1)
        results = {name: simulate(history, [0, 2, 0, 1, 0, 0], retention=name, **args)
                   for name in ("expanding", "recent", "decay")}
        original_forecasts = [r["forecast"] for r in results["expanding"]["reviews"]]
        for name, result in results.items():
            self.assertEqual([r["forecast"] for r in result["reviews"]], original_forecasts)
            changed = simulate(history, [0, 2, 0, 1, 0, 999], retention=name, **args)
            self.assertEqual(result["days"][:5], changed["days"][:5])
            self.assertEqual([r for r in result["reviews"] if r["day"] <= 5],
                             [r for r in changed["reviews"] if r["day"] <= 5])

    def test_cost_gain_cannot_override_service_or_undefined_evidence(self):
        ref = dict(score=dict(immediate_fill_rate=1, cycle_service=1),
                   accounting=dict(full_intervention_cost=100))
        good = dict(score=dict(immediate_fill_rate=1, cycle_service=1),
                    accounting=dict(full_intervention_cost=95))
        self.assertTrue(gate(good, {"ref": ref})["passed"])
        for rate in (Fraction(4, 5), None):
            bad = dict(score=dict(immediate_fill_rate=rate, cycle_service=1),
                       accounting=dict(full_intervention_cost=1))
            self.assertFalse(gate(bad, {"ref": ref})["passed"])

    def test_new_inputs_differ_from_consumed_warmup_paths(self):
        from scripts.warmup_benchmark import observations
        inputs = fresh_inputs("lumpy", 3301)
        self.assertEqual(inputs, fresh_inputs("lumpy", 3301))
        values = inputs["history"] + inputs["warmup_demand"] + inputs["score_demand"]
        self.assertEqual(len(values), 420)
        self.assertNotEqual(values, observations("lumpy", 1301))
        self.assertNotEqual(inputs["daily_delays"], fresh_inputs("lumpy", 3709)["daily_delays"])


if __name__ == "__main__":
    unittest.main()
