"""Independent exact intermittent forecasts, cumulative calibration and decisions.

Run: PYTHONPATH=src python3 -m unittest tests.test_intermittent
"""
from fractions import Fraction
import unittest

from inventory_intelligence.intermittent import calibrate, forecast, simulate


class IntermittentOracleTests(unittest.TestCase):
    def test_initialization_leading_zeros_and_all_zero(self):
        for method in ("naive", "mean", "seasonal_naive", "zero", "croston", "sba", "tsb"):
            with self.subTest(method=method):
                self.assertEqual(forecast([0] * 7, method=method, horizon=3), [Fraction(0)] * 3)
        for history, expected in (([4], {"croston": 4, "sba": 3, "tsb": 4}),
                                  ([0, 0, 6], {"croston": 2, "sba": Fraction(3, 2), "tsb": 2})):
            for method, value in expected.items():
                with self.subTest(history=history, method=method):
                    actual = forecast(history, method=method, horizon=2,
                                      alpha=Fraction(1, 2), beta=Fraction(1, 2))
                    self.assertEqual(actual, [value, value])
                    self.assertTrue(all(type(point) is Fraction for point in actual))

    def test_gap_updates_sba_factor_and_trailing_zero_tsb_decay(self):
        # First size=6, interval=3, p=1/3; next size=8, interval=5/2,
        # p=7/12 after one zero and one arrival. Subsequent zero halves p only.
        expected = {
            "croston": (Fraction(16, 5), Fraction(16, 5)),
            "sba": (Fraction(12, 5), Fraction(12, 5)),
            "tsb": (Fraction(14, 3), Fraction(7, 3)),
        }
        for method, (after_arrival, after_zero) in expected.items():
            for history, value in (([0, 0, 6, 0, 10], after_arrival),
                                   ([0, 0, 6, 0, 10, 0], after_zero)):
                with self.subTest(method=method, history=history):
                    self.assertEqual(forecast(history, method=method, horizon=3,
                                              alpha=Fraction(1, 2), beta=Fraction(1, 2)), [value] * 3)
        # A later gap of three updates interval to 11/4 and size to 5.
        for method, value in (("croston", Fraction(20, 11)), ("sba", Fraction(15, 11)),
                              ("tsb", Fraction(275, 96))):
            self.assertEqual(forecast([0, 0, 6, 0, 10, 0, 0, 2], method=method, horizon=1,
                                      alpha=Fraction(1, 2), beta=Fraction(1, 2)), [value])
        self.assertEqual(forecast([0, 0, 6, 0, 0], method="tsb", horizon=1,
                                  beta=Fraction(1, 2)), [Fraction(1, 2)])

        for method, value in (("croston", 4), ("sba", Fraction(7, 2)),
                              ("tsb", Fraction(65, 16))):
            self.assertEqual(forecast([4, 0, 8], method=method, horizon=1,
                                      alpha=Fraction(1, 4), beta=Fraction(3, 4)), [value])
        self.assertEqual(forecast([4, 0, 8], method="tsb", horizon=1, alpha=1, beta=1),
                         [Fraction(8)])

    def test_baselines_and_large_quantities_remain_exact(self):
        self.assertEqual(forecast([0, 2, 0], method="mean", horizon=2), [Fraction(2, 3)] * 2)
        self.assertEqual(forecast([0, 2, 0], method="naive", horizon=2), [Fraction(0)] * 2)
        self.assertEqual(forecast([1, 2, 3, 4, 5, 6, 7], method="seasonal_naive", horizon=9),
                         [Fraction(i) for i in (1, 2, 3, 4, 5, 6, 7, 1, 2)])
        huge = 10 ** 50 + 1
        for method, value in (("croston", Fraction(huge + 1, 2)),
                              ("sba", Fraction(3 * (huge + 1), 8)),
                              ("tsb", Fraction(5 * (huge + 1), 8))):
            with self.subTest(method=method):
                self.assertEqual(forecast([0, huge, 0, huge + 2], method=method, horizon=1,
                                          alpha=Fraction(1, 2), beta=Fraction(1, 2)), [value])

    def test_cumulative_quantile_ranks_sign_and_only_completed_labels(self):
        # Nonoverlapping H=2 actual sums 2,6,0,3; naive prefix forecasts 8,2,8,0.
        history = [4, 1, 1, 2, 4, 0, 0, 3, 0]
        for q, error, safety in ((Fraction(1, 2), -6, 0), (Fraction(3, 4), 3, 3),
                                  (Fraction(5, 8), 3, 3), (1, 4, 4)):
            with self.subTest(quantile=q):
                result = calibrate(history, method="naive", horizon=2, quantile=q,
                                   min_train=1, min_samples=4)
                self.assertEqual(result["origins"], [1, 3, 5, 7])
                self.assertEqual(result["errors"], [-6, 4, -8, 3])
                self.assertEqual(result["count"], 4)
                self.assertEqual(result["quantile_error"], error)
                self.assertEqual(result["safety_qty"], safety)
                partial = calibrate(history + [999], method="naive", horizon=2, quantile=q,
                                    min_train=1, min_samples=4)
                self.assertEqual(partial, result)  # Origin 9 has no completed two-day label.

    def test_fractional_calibration_ceiling_and_insufficient_samples(self):
        result = calibrate([1, 0, 0, 1], method="mean", horizon=1, quantile=1,
                           min_train=1, min_samples=3)
        self.assertEqual(result["origins"], [1, 2, 3])
        self.assertEqual(result["errors"], [-1, Fraction(-1, 2), Fraction(2, 3)])
        self.assertEqual(result["quantile_error"], Fraction(2, 3))
        self.assertEqual(result["safety_qty"], 1)
        for history in ([0] * 28, [0] * 43):
            with self.subTest(length=len(history)), self.assertRaises(ValueError):
                calibrate(history, method="zero", horizon=2, quantile=Fraction(9, 10))
        enough = calibrate([0] * 44, method="zero", horizon=2, quantile=Fraction(9, 10))
        self.assertEqual(enough["origins"], [28, 30, 32, 34, 36, 38, 40, 42])
        self.assertEqual(enough["count"], 8)
        self.assertEqual(enough["safety_qty"], 0)

    def test_wrapper_preserves_event_timing_costs_and_conservation(self):
        result = simulate([1], [1, 1, 1], method="naive", on_hand=0,
                          lead_days=2, review_days=1)
        self.assertEqual(result["research_version"], "intermittent-research-v1")
        self.assertEqual(result["parameters"]["method"], "naive")
        self.assertIsNone(result["parameters"]["safety_quantile"])
        self.assertEqual([d["receipts"] for d in result["days"]], [0, 0, 3, 1, 1, 0])
        self.assertEqual([d["order_qty"] for d in result["days"]], [3, 1, 1, 0, 0, 0])
        self.assertEqual([d["backlog"] for d in result["days"]], [1, 2, 0, 0, 0, 0])
        metrics = result["metrics"]
        self.assertEqual((metrics["scored_cost"], metrics["runoff_cost"], metrics["total_cost"]),
                         (30, 5, 35))
        self.assertEqual(metrics["immediate_fill_rate"], Fraction(1, 3))
        self.assertEqual(metrics["eventual_fill_rate"], 1)
        self.assertEqual(sum(d["fulfilled_units"] for d in result["days"]), 3)
        self.assertEqual(sum(d["receipts"] for d in result["days"]), 5)
        self.assertEqual(result["terminal"]["on_hand"], 2)
        self.assertEqual(result["terminal"]["backlog"], 0)
        self.assertEqual(result["terminal"]["outstanding_qty"], 0)
        self.assertIsNone(metrics["protection_target_pinball_loss"])
        for day in result["days"]:
            self.assertIs(type(day["on_hand"]), int)
            self.assertIs(type(day["backlog"]), int)
            self.assertGreaterEqual(day["on_hand"], 0)
            self.assertGreaterEqual(day["backlog"], 0)

    def test_wrapper_rounded_protection_pinball_and_completed_dynamic_calibration(self):
        # The trailing historical 1 is initially outside every complete calibration
        # label. Mean H forecast=2/45; ceil target=1 covers scored cumulative demand=1.
        result = simulate([0] * 44 + [1], [1, 0], method="mean", on_hand=0,
                          lead_days=1, review_days=1, safety_quantile=Fraction(9, 10))
        reviews = result["reviews"]
        self.assertEqual(reviews[0]["forecast"], [Fraction(1, 45)] * 2)
        self.assertEqual(reviews[0]["calibration"]["count"], 8)
        self.assertEqual(reviews[0]["safety_qty"], 0)
        self.assertEqual(reviews[0]["protection_target"], 1)
        # After day 0 completes, origin 44 becomes a complete label of two units.
        self.assertEqual(reviews[1]["calibration"]["count"], 9)
        self.assertEqual(reviews[1]["calibration"]["errors"], [0] * 8 + [2])
        self.assertEqual(reviews[1]["safety_qty"], 2)
        self.assertEqual(reviews[1]["protection_target"], 3)
        metrics = result["metrics"]
        self.assertEqual(metrics["protection_target_origins"], 1)
        self.assertEqual(metrics["protection_target_covered"], 1)
        self.assertEqual(metrics["protection_target_coverage"], 1)
        self.assertEqual(metrics["protection_target_pinball_loss"], 0)
        self.assertEqual(metrics["immediate_fill_rate"], 0)  # Coverage is not inventory service.
        self.assertEqual((metrics["scored_cost"], metrics["runoff_cost"], metrics["total_cost"]),
                         (10, 6, 16))
        self.assertEqual(result["terminal"]["on_hand"], 3)
        for review in reviews[2:]:
            self.assertTrue(review["runoff"])
            self.assertEqual(review["forecast"], [])
            self.assertIsNone(review.get("calibration"))

    def test_wrapper_nonzero_pinball_no_future_or_hidden_supplier_leak(self):
        inputs = dict(method="zero", on_hand=0, lead_days=1, review_days=1,
                      safety_quantile=Fraction(9, 10))
        result = simulate([0] * 44, [1, 0, 0], **inputs)
        future_changed = simulate([0] * 44, [1, 0, 99], **inputs)
        self.assertEqual(result["reviews"][:3], future_changed["reviews"][:3])
        self.assertEqual([r["safety_qty"] for r in result["reviews"][:3]], [0, 0, 1])
        metrics = result["metrics"]
        self.assertEqual(metrics["protection_target_origins"], 2)
        self.assertEqual(metrics["protection_target_covered"], 1)
        self.assertEqual(metrics["protection_target_coverage"], Fraction(1, 2))
        self.assertEqual(metrics["protection_target_pinball_loss"], Fraction(9, 20))
        delayed = simulate([0] * 44, [1, 0, 0], supplier_delays=[0, 1, 0, 0, 0, 0], **inputs)
        self.assertEqual(result["reviews"][:3], delayed["reviews"][:3])
        over = simulate([0] * 44 + [1], [0, 0], method="mean", on_hand=0,
                        lead_days=1, review_days=1, safety_quantile=Fraction(9, 10))
        self.assertEqual(over["reviews"][0]["protection_target"], 1)
        self.assertEqual(over["metrics"]["protection_target_pinball_loss"], Fraction(1, 10))
        short = simulate([0] * 44, [0], **inputs)
        self.assertEqual(short["metrics"]["protection_target_origins"], 0)
        self.assertIsNone(short["metrics"]["protection_target_coverage"])
        self.assertIsNone(short["metrics"]["protection_target_pinball_loss"])

    def test_invalid_parameters_and_unsafe_calibration_are_rejected(self):
        for name in ("alpha", "beta"):
            for value in (0, -1, Fraction(3, 2), True, 0.5, "1/2", None):
                with self.subTest(parameter=name, value=value), self.assertRaises((ValueError, TypeError)):
                    forecast([1, 0], method="croston", horizon=2, **{name: value})
        for name, values in (("history", ([], [True], [1.0], [None], [-1])),
                              ("horizon", (0, -1, True, 1.0, None)),
                              ("method", ("unknown",))):
            for value in values:
                inputs = dict(history=[1], method="croston", horizon=1)
                inputs[name] = value
                with self.subTest(parameter=name, value=value), self.assertRaises((ValueError, TypeError)):
                    forecast(**inputs)
        for name in ("quantile", "min_train", "min_samples"):
            values = (0, -1, True, 0.5, "1", None)
            if name == "quantile":
                values += (Fraction(3, 2),)
            for value in values:
                inputs = dict(method="zero", horizon=2, quantile=Fraction(9, 10),
                              min_train=28, min_samples=8)
                inputs[name] = value
                with self.subTest(parameter=name, value=value), self.assertRaises((ValueError, TypeError)):
                    calibrate([0] * 44, **inputs)
        inputs = dict(method="zero", on_hand=0, lead_days=1, review_days=1,
                      safety_quantile=Fraction(9, 10))
        with self.assertRaises(ValueError):
            simulate([0] * 44, [0, 0], safety_qty=1, **inputs)
        with self.assertRaises(ValueError):
            simulate([0] * 43, [0, 0], **inputs)


if __name__ == "__main__":
    unittest.main()
