"""Expected-delay, signed intervention and common-cost-window oracles."""

from fractions import Fraction
import unittest

from scripts.supply_sensitivity_benchmark import PROFILES, REFERENCE, difference, fresh_inputs, intervention_grid, trial


class SupplySensitivityOracles(unittest.TestCase):
    def test_profiles_have_equal_expected_delay_and_different_variance(self):
        expected_variance = dict(low=0, medium=Fraction(2, 3), high=Fraction(7, 3))
        for name, profile in PROFILES.items():
            self.assertEqual(Fraction(sum(profile), len(profile)), 1)
            self.assertEqual(sum((Fraction(delay) - 1) ** 2 for delay in profile) / len(profile),
                             expected_variance[name])

    def test_grid_keeps_one_factor_controls_explicit(self):
        grid = intervention_grid()
        self.assertEqual(len(grid), 13)
        ref = grid[REFERENCE]
        for name, field in (("initial0", "on_hand"), ("initial40", "on_hand"), ("review1", "review_days")):
            self.assertEqual({key: value for key, value in grid[name].items() if key != field}, ref)
        self.assertEqual(grid["pack1:moq1"]["pack_size"], 1)
        self.assertEqual(grid["pack1:moq1"]["moq"], 1)

    def test_common_twenty_one_day_tail_and_paid_initial_stock(self):
        physical = dict(history=[0], warmup_demand=[0, 0], score_demand=[0, 0], daily_delays=[0] * 40)
        params = dict(on_hand=2, lead_days=1, review_days=1, pack_size=1, moq=1,
                      holding_cost=1, backlog_cost=10, order_cost=2, unit_cost=2)
        pair = trial(physical, dict(method="zero"), params)
        cold, warm = [pair["arms"][arm] for arm in ("cold", "warm")]
        self.assertEqual(cold["accounting"]["common_days"], 23)
        self.assertEqual(warm["accounting"]["common_days"], 25)
        self.assertEqual(cold["accounting"]["full_intervention_cost"], 50)
        self.assertEqual(warm["accounting"]["full_intervention_cost"], 54)
        self.assertEqual(pair["warm_minus_cold"]["full_intervention_cost"], 4)
        slower = trial(physical, dict(method="zero"), dict(params, lead_days=2))
        self.assertEqual(slower["arms"]["cold"]["accounting"]["full_intervention_cost"], 50)
        self.assertIsNone(pair["warm_minus_cold"]["immediate_fill_rate"])

    def test_signed_effect_keeps_regressions_and_undefined_service(self):
        ref = dict(score=dict(missed_units=3, immediate_fill_rate=Fraction(7, 10),
                             cycle_service=Fraction(1, 2), backlog_piece_days=5),
                   accounting=dict(full_intervention_cost=100))
        c = dict(score=dict(missed_units=4, immediate_fill_rate=Fraction(3, 5),
                           cycle_service=None, backlog_piece_days=7),
                 accounting=dict(full_intervention_cost=90))
        self.assertEqual(difference(c, ref), dict(missed_units=1, immediate_fill_rate=Fraction(-1, 10),
                                                cycle_service=None, backlog_piece_days=2,
                                                full_intervention_cost=-10))

    def test_shock_and_demand_namespaces_are_reproducible_and_fresh(self):
        from scripts.warmup_benchmark import observations
        inp = fresh_inputs("lumpy", 5301)
        self.assertEqual(inp, fresh_inputs("lumpy", 5301))
        self.assertNotEqual(inp["daily_shocks"], fresh_inputs("lumpy", 5709)["daily_shocks"])
        self.assertEqual(len(inp["daily_shocks"]), 133)
        self.assertTrue(all(0 <= shock < 6 for shock in inp["daily_shocks"]))
        self.assertNotEqual(inp["history"], observations("lumpy", 1301)[:252])


if __name__ == "__main__":
    unittest.main()
