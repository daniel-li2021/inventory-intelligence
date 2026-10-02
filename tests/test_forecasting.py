"""Independent, hand-calculated baseline checks; no database or external models."""

from fractions import Fraction
import unittest

from inventory_intelligence.forecasting import backtest, forecast


class Baselines(unittest.TestCase):
    def test_forecasts_and_fractional_expected_demand(self):
        self.assertEqual(forecast([0, 1], method="naive", horizon=3), [1, 1, 1])
        self.assertEqual(forecast([0, 1], method="mean", horizon=3), [Fraction(1, 2)] * 3)
        self.assertEqual(forecast([99, 1, 2, 3], method="seasonal_naive",
                                  horizon=8, season_length=3), [1, 2, 3, 1, 2, 3, 1, 2])
        large = 2 ** 53 + 1
        self.assertEqual(forecast([large, large + 1], method="mean", horizon=1),
                         [Fraction(2 * large + 1, 2)])

    def test_weekly_golden_scores_and_common_origins(self):
        report = backtest([1, 2, 3, 4, 5, 6, 7] * 5)
        self.assertEqual([f["origin"] for f in report["folds"]], [14, 21, 28])
        self.assertEqual(report["scored_points"], 21)
        self.assertEqual(report["scores"], {
            "naive": dict(mae=Fraction(3), bias=Fraction(3), wape=Fraction(3, 4)),
            "mean": dict(mae=Fraction(12, 7), bias=Fraction(0), wape=Fraction(3, 7)),
            "seasonal_naive": dict(mae=Fraction(0), bias=Fraction(0), wape=Fraction(0)),
        })
        for fold in report["folds"]:
            self.assertEqual(fold["actual"], [1, 2, 3, 4, 5, 6, 7])
            self.assertEqual(fold["predictions"], {
                "naive": [7] * 7, "mean": [4] * 7,
                "seasonal_naive": [1, 2, 3, 4, 5, 6, 7],
            })

    def test_future_values_cannot_change_earlier_predictions(self):
        original = [1, 2, 3, 4, 5, 6, 7] * 4
        changed = original[:14] + [1000] * 14
        first = backtest(original)["folds"][0]
        second = backtest(changed)["folds"][0]
        self.assertEqual(first["predictions"], second["predictions"])
        self.assertNotEqual(first["actual"], second["actual"])

    def test_zero_and_intermittent_observations(self):
        zero = backtest([0] * 21)
        for score in zero["scores"].values():
            self.assertEqual(score, dict(mae=0, bias=0, wape=None))
        sparse = backtest([0, 0, 0, 0, 0, 0, 7] * 3)
        self.assertEqual(sparse["scores"]["seasonal_naive"]["mae"], 0)
        self.assertEqual(sparse["scores"]["mean"]["mae"], Fraction(12, 7))

    def test_invalid_or_insufficient_data_is_not_a_zero_forecast(self):
        for values in ([], [None], [-1], [True], [1.0], ["1"]):
            with self.subTest(values=values), self.assertRaises(ValueError):
                forecast(values, method="mean", horizon=1)
        for kwargs in (dict(horizon=0), dict(horizon=True), dict(season_length=0),
                       dict(method="unknown")):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                forecast([1], **(dict(method="naive", horizon=1) | kwargs))
        with self.assertRaises(ValueError):
            forecast([1, 2], method="seasonal_naive", horizon=1)
        for values, kwargs in (([0] * 20, {}), ([0] * 21, dict(min_train=6)),
                               ([0] * 21, dict(step=0)), ([0] * 21, dict(horizon=1.0))):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                backtest(values, **kwargs)


if __name__ == "__main__":
    unittest.main()
