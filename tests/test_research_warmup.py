"""Independent hand-calculated warmup, acquisition and paired-calendar oracles."""

from fractions import Fraction
import unittest

from inventory_intelligence.research_warmup import paired_trial, supplier_slots, window_metrics
from scripts.warmup_benchmark import observations, supplier_trace


class WarmupOracles(unittest.TestCase):
    def pair(self, warmup=(2, 2), score=(2, 2), **changes):
        params = dict(method="naive", on_hand=0, lead_days=1, review_days=1,
                      pack_size=1, moq=1, unit_cost=2, holding_cost=1,
                      backlog_cost=10, order_cost=2)
        params.update(changes)
        return paired_trial([2], warmup, score, [0] * 30, **params)

    def test_seamless_pipeline_and_full_acquisition_accounting(self):
        pair, sims = self.pair()
        warm, cold = pair["arms"]["warm"], pair["arms"]["cold"]
        self.assertEqual(warm["score_start_state"], dict(on_hand=0, backlog=0, pipeline=2))
        self.assertEqual(cold["score_start_state"], dict(on_hand=0, backlog=0, pipeline=0))
        self.assertEqual([day["order_qty"] for day in sims["warm"]["days"]], [4, 2, 2, 2, 0, 0])
        self.assertEqual(warm["warmup"]["missed_units"], 2)
        self.assertEqual(warm["score"]["immediate_fill_rate"], 1)
        self.assertEqual(cold["score"]["immediate_fill_rate"], Fraction(1, 2))
        self.assertEqual(warm["accounting"]["warmup_operating_cost"], 24)
        self.assertEqual(warm["accounting"]["warmup_order_acquisition_cost"], 12)
        self.assertEqual(warm["accounting"]["score_operating_cost"], 4)
        self.assertEqual(warm["accounting"]["all_order_acquisition_cost"], 20)
        self.assertEqual(warm["accounting"]["full_intervention_cost"], 52)
        self.assertEqual(cold["accounting"]["full_intervention_cost"], 40)
        self.assertEqual(pair["warm_minus_cold"]["full_intervention_cost"], 12)
        self.assertEqual(pair["warm_minus_cold"]["operating_cost"], -20)
        # Warm score service improves while complete intervention is more costly.
        self.assertEqual(warm["score"]["complete_cycles"], 2)
        self.assertEqual(warm["score"]["shortage_free_cycles"], 2)
        self.assertEqual(cold["score"]["shortage_free_cycles"], 1)

    def test_backlog_carries_across_boundary_and_reduces_cycle_service(self):
        pair, sims = self.pair(warmup=(2,), lead_days=2)
        warm = pair["arms"]["warm"]
        self.assertEqual(warm["score_start_state"], dict(on_hand=0, backlog=2, pipeline=6))
        self.assertEqual([row["backlog"] for row in sims["warm"]["days"][:3]], [2, 4, 0])
        self.assertEqual(warm["score"]["missed_units"], 2)
        self.assertEqual(warm["score"]["cycle_service"], Fraction(1, 2))
        self.assertEqual(pair["arms"]["cold"]["feasibility"]["inevitable_new_missed_units"], 4)

    def test_initial_stock_is_paid_zero_service_is_null_and_holding_is_exact(self):
        pair, _ = self.pair(warmup=(0, 0), score=(0, 0), method="zero", on_hand=2,
                            unit_cost=Fraction(3, 2), holding_cost=Fraction(1, 2))
        warm, cold = pair["arms"]["warm"], pair["arms"]["cold"]
        self.assertEqual(warm["accounting"]["initial_acquisition_cost"], 3)
        self.assertEqual(warm["accounting"]["full_intervention_cost"], 9)
        self.assertEqual(cold["accounting"]["full_intervention_cost"], 7)
        self.assertIsNone(warm["score"]["immediate_fill_rate"])
        self.assertIsNone(pair["warm_minus_cold"]["immediate_fill_rate"])
        self.assertEqual(warm["score"]["cycle_service"], 1)
        self.assertIsNone(warm["score"]["target_pinball_loss"])

    def test_common_end_extends_terminal_holding_and_not_free_inventory(self):
        # A daily delay3 on a non-review day lengthens the declared common end,
        # but is never seen by this R2 policy; original runoff remains L1+R2.
        pair, _ = paired_trial([0], [0, 0], [0, 0], [0, 3] + [0] * 20,
            method="zero", on_hand=2, lead_days=1, review_days=2, unit_cost=2)
        for arm in pair["arms"].values():
            self.assertEqual(arm["accounting"]["extension_days"], 3)
            self.assertEqual(arm["accounting"]["extension_holding_cost"], 6)
            self.assertEqual(arm["accounting"]["initial_acquisition_cost"], 4)
        self.assertEqual(pair["warm_minus_cold"]["full_intervention_cost"], 4)

    def test_calendar_slot_alignment_includes_zero_order_reviews(self):
        trace = [0] * 30
        trace[4] = 3
        warm = supplier_slots(trace, start_day=0, demand_days=8, lead_days=1, review_days=2)
        cold = supplier_slots(trace, start_day=4, demand_days=4, lead_days=1, review_days=2)
        self.assertEqual(warm[2], 3)
        self.assertEqual(warm[2:], cold)
        self.assertEqual(warm, (0, 0, 3, 0, 0, 0, 0))
        with self.assertRaises(ValueError):
            supplier_slots([0] * 4, start_day=0, demand_days=4, lead_days=1, review_days=1)

    def test_future_demand_or_supplier_changes_cannot_change_prior_decisions(self):
        _, before = self.pair(score=(2, 2, 2, 2))
        _, after = self.pair(score=(2, 2, 2, 999))
        for arm, cutoff in (("cold", 3), ("warm", 5)):
            self.assertEqual(before[arm]["days"][:cutoff], after[arm]["days"][:cutoff])
            self.assertEqual([row for row in before[arm]["reviews"] if row["day"] <= cutoff],
                             [row for row in after[arm]["reviews"] if row["day"] <= cutoff])
        trace = [0] * 30
        trace[5] = 3
        _, delayed = paired_trial([2], [2, 2], [2] * 4, trace, method="naive", on_hand=0,
                                   lead_days=1, review_days=1, pack_size=1, moq=1)
        self.assertEqual(before["warm"]["days"][:6], delayed["warm"]["days"][:6])

    def test_nominal_coverage_and_pinball_do_not_equal_inventory_service(self):
        # All-zero history estimates safety0; an unanticipated demand2 on day0
        # misses before receipt. Complete H2 target is zero against actual2.
        pair, _ = paired_trial([0] * 44, [0, 0], [2, 0], [0] * 20,
            method="zero", safety_quantile=Fraction(9, 10), on_hand=0,
            lead_days=1, review_days=1, pack_size=1, moq=1)
        metrics = pair["arms"]["cold"]["score"]
        self.assertEqual(metrics["forecast_origins"], 1)
        self.assertEqual(metrics["target_covered"], 0)
        self.assertEqual(metrics["target_pinball_loss"], Fraction(9, 5))
        self.assertEqual(metrics["nominal_gaps"]["immediate_fill_rate"], Fraction(-9, 10))
        self.assertEqual(metrics["calibration_min_count"], 9)

    def test_invalid_and_missing_inputs_never_become_clean_trials(self):
        for changes in (dict(warmup=()), dict(score=(None,)), dict(unit_cost=-1),
                        dict(review_days=3), dict(unit_cost=2.0)):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.pair(**changes)
        _, sims = self.pair()
        for start, end in ((True, 2), (2, 2), (0, 5)):
            with self.assertRaises(ValueError):
                window_metrics(sims["cold"], start_day=start, end_day=end, review_days=1, horizon=2)


class FrozenTraceOracles(unittest.TestCase):
    def test_control_and_lifecycle_transitions(self):
        self.assertEqual(observations("constant", 1301), [3] * 420)
        self.assertEqual(observations("weekly", 1301), [0, 1, 2, 3, 4, 5, 6] * 60)
        self.assertEqual(observations("zero", 1301), [0] * 420)
        self.assertEqual(observations("pause", 1301)[252:280], [0] * 28)
        self.assertGreater(sum(observations("pause", 1301)[280:308]), 0)
        self.assertEqual(observations("obsolescence", 1301)[280:], [0] * 140)
        with self.assertRaises(ValueError):
            observations("unknown", 1301)

    def test_seed_namespaces_and_reproducibility(self):
        self.assertEqual(observations("lumpy", 1301), observations("lumpy", 1301))
        self.assertNotEqual(observations("lumpy", 1301), observations("lumpy", 1709))
        self.assertEqual(supplier_trace("lumpy", 1301, "selection"),
                         supplier_trace("lumpy", 1301, "selection"))
        self.assertNotEqual(supplier_trace("lumpy", 1301, "selection"),
                            supplier_trace("lumpy", 1301, "holdout"))


if __name__ == "__main__":
    unittest.main()
