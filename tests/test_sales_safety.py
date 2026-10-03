from copy import deepcopy
from fractions import Fraction
import unittest

from inventory_intelligence import intermittent
from inventory_intelligence.sales_safety import simulate_arm, summarize
from scripts.public_safety_benchmark import aggregate, compact, decode, paired
from scripts.public_sales_benchmark import canonical
from scripts.public_sales_benchmark import digest
from scripts.public_safety_audit import audit_arm
from pathlib import Path


class SalesSafetyOracles(unittest.TestCase):
    def test_signed_nearest_rank_calibration_and_adjacent_targets(self):
        for q, expected in ((Fraction(1, 2), 2), (Fraction(9, 10), 4), (Fraction(19, 20), 4)):
            calibrated = intermittent.calibrate([0] * 7 + [1, 2, 3, 4], method="zero",
                horizon=1, quantile=q, min_train=7, min_samples=4)
            self.assertEqual(calibrated["origins"], [7, 8, 9, 10])
            self.assertEqual(calibrated["errors"], [1, 2, 3, 4])
            self.assertEqual(calibrated["safety_qty"], expected)
        negative = intermittent.calibrate([9] * 7 + [0] * 4, method="mean", horizon=1,
            quantile=Fraction(19, 20), min_train=7, min_samples=4)
        self.assertLess(negative["quantile_error"], 0)
        self.assertEqual(negative["safety_qty"], 0)
        with self.assertRaises(ValueError):
            intermittent.calibrate([0] * 7 + [1] * 4, method="zero", horizon=1,
                quantile=Fraction(19, 20), min_train=7, min_samples=8)

    def test_exact_paid_warmup_holdout_and_settlement(self):
        simulation = intermittent.simulate([1] * 28, [1, 1], method="naive", on_hand=0,
            lead_days=1, review_days=1, holding_cost=1, backlog_cost=10, order_cost=2)
        result = summarize(simulation, [1, 1], warmup_days=1, review_days=1,
                           quantile=None, common_end=4)
        # Day0 buys2, misses1; day1 receives2, clears1 old and fills1 new, buys1.
        # Settlement has one paid piece held on days2 and3; no residual credit.
        self.assertEqual(result["costs"]["warmup"], dict(acquisition=4, holding=0, backlog=10, setup=2, total=16))
        self.assertEqual(result["costs"]["holdout"], dict(acquisition=2, holding=0, backlog=0, setup=2, total=4))
        self.assertEqual(result["costs"]["settlement"], dict(acquisition=0, holding=2, backlog=0, setup=0, total=2))
        self.assertEqual(result["full_cost"], 22)
        self.assertEqual(result["boundary_state"], dict(on_hand=0, backlog=1, outstanding_qty=2))
        self.assertEqual(result["holdout"]["demand_units"], 1)
        self.assertEqual(result["holdout"]["eventual_units"], 1)  # Excludes old due-day0.
        self.assertEqual(result["warmup"]["immediate_fill"], 0)
        self.assertEqual(result["holdout"]["immediate_fill"], 1)
        self.assertEqual(result["holdout"]["protection_origins"], 0)
        extended = summarize(simulation, [1, 1], warmup_days=1, review_days=1,
                             quantile=None, common_end=7)
        self.assertEqual(extended["costs"]["settlement"]["holding"], 5)
        self.assertEqual(extended["full_cost"], 25)

    def test_exact_holdout_coverage_pinball_and_completed_targets(self):
        simulation = intermittent.simulate([0] * 28, [0, 1, 0, 0], method="zero", on_hand=0,
            lead_days=1, review_days=1, holding_cost=1, backlog_cost=10, order_cost=2)
        result = summarize(simulation, [0, 1, 0, 0], warmup_days=1, review_days=1,
                           quantile=Fraction(19, 20), common_end=6)
        # Holdout reviews1,2 have complete two-day targets; review3 is excluded.
        self.assertEqual(result["holdout"]["protection_origins"], 2)
        self.assertEqual(result["holdout"]["protection_covered"], 1)
        self.assertEqual(result["holdout"]["protection_coverage"], Fraction(1, 2))
        self.assertEqual(result["holdout"]["pinball_loss"], Fraction(19, 40))
        self.assertEqual(result["holdout"]["eventual_units"], 1)
        self.assertEqual(result["holdout"]["immediate_units"], 0)

    def test_future_sales_cannot_change_warm_state_or_first_holdout_decision(self):
        args = dict(method="sba", quantile=Fraction(19, 20), lead_days=2, delay=3)
        history = [3] * 289
        left, summary = simulate_arm(history, [3] * 84, **args)
        right, changed = simulate_arm(history, [3] * 56 + [99] * 28, **args)
        self.assertEqual(left["days"][:56], right["days"][:56])
        self.assertEqual(summary["boundary_state"], changed["boundary_state"])
        self.assertEqual(summary["costs"]["warmup"], changed["costs"]["warmup"])
        self.assertEqual(left["reviews"][:9], right["reviews"][:9])  # Includes origin56.
        fixed, _ = simulate_arm(history, [3] * 84, **dict(args, delay=0))
        self.assertEqual([(r["forecast"], r["safety_qty"]) for r in left["reviews"] if not r["runoff"]],
                         [(r["forecast"], r["safety_qty"]) for r in fixed["reviews"] if not r["runoff"]])

    def test_null_fill_cycle_denominators_and_exact_aggregates(self):
        _, zero = simulate_arm([0] * 289, [0] * 84, method="mean", quantile=Fraction(19, 20), lead_days=2, delay=0)
        _, constant = simulate_arm([3] * 289, [3] * 84, method="mean", quantile=Fraction(19, 20), lead_days=2, delay=0)
        report = aggregate([dict(summary=zero), dict(summary=constant)], Fraction(19, 20))
        holdout = report["periods"]["holdout"]
        self.assertEqual(holdout["demand_units"], 84)
        self.assertEqual((holdout["defined_fill_items"], holdout["undefined_fill_items"]), (1, 1))
        self.assertEqual((holdout["cycles"], holdout["protection_origins"]), (8, 6))
        self.assertEqual(holdout["immediate_fill"], 1)
        self.assertEqual(holdout["macro_immediate_fill"], 1)
        self.assertEqual(holdout["nominal_fill_pass_items"], 1)
        self.assertEqual(holdout["nominal_cycle_pass_items"], 2)
        self.assertEqual(report["full_cost"], zero["full_cost"] + constant["full_cost"])
        self.assertEqual(report["mean_full_cost"], Fraction(report["full_cost"], 2))

    def test_residual_receipts_roundtrip_and_paired_nulls(self):
        simulation, summary = simulate_arm([0] * 289, [0] * 84, method="mean",
                                           quantile=Fraction(19, 20), lead_days=2, delay=0)
        before = deepcopy(simulation)
        residuals = {}
        compact(simulation, residuals)
        for original, compressed in zip(before["reviews"], simulation["reviews"]):
            if original.get("calibration") is not None:
                current = compressed["calibration"]
                bundle = residuals[current["residuals_sha256"]]
                self.assertEqual(bundle["errors"], original["calibration"]["errors"])
                self.assertEqual(bundle["origins"], original["calibration"]["origins"])
        self.assertEqual(decode(canonical(dict(simulation=simulation, residuals=residuals))),
                         dict(simulation=simulation, residuals=residuals))
        arms = [dict(summary=summary)]
        differences = paired(arms, arms)
        self.assertEqual(differences["fill_undefined"], 1)
        self.assertEqual(differences["cost_equal"], 1)
        self.assertEqual(differences["lower_cost_without_fill_or_cycle_regression"], 0)

    def test_fail_closed_accounting_boundaries(self):
        simulation = intermittent.simulate([1] * 28, [1, 1], method="naive", on_hand=0,
            lead_days=1, review_days=1, holding_cost=1, backlog_cost=10, order_cost=2)
        args = dict(warmup_days=1, review_days=1, quantile=None, common_end=4)
        for replacement in (dict(warmup_days=2), dict(common_end=3), dict(quantile=True)):
            with self.assertRaises(ValueError): summarize(simulation, [1, 1], **dict(args, **replacement))
        changed = deepcopy(simulation)
        changed["days"][0]["backlog_cost"] = 0
        with self.assertRaises(ValueError): summarize(changed, [1, 1], **args)
        with self.assertRaises(ValueError): simulate_arm([1] * 289, [1] * 84, method="mean",
            quantile=None, lead_days=10, delay=0)

    def test_audit_detects_mutations_even_with_recomputed_hashes(self):
        config = dict(method="mean", quantile=Fraction(19, 20), lead_days=2, delay=0)
        record = dict(history=[3] * 289, demand=[3] * 84)
        simulation, summary = simulate_arm(record["history"], record["demand"], **config)
        residuals = {}
        compact(simulation, residuals)
        arm = dict(simulation=simulation, summary=summary, trajectory_sha256=digest(simulation),
                   input_sha256=digest(dict(record, config=config)))
        audit_arm(record, arm, config, residuals)
        mutations = (
            lambda value: value["simulation"]["days"][1].__setitem__("receipts", 2),
            lambda value: value["summary"]["holdout"].__setitem__("immediate_units", 999),
            lambda value: value["summary"]["costs"]["warmup"].__setitem__("acquisition", 0),
            lambda value: value["summary"]["holdout"].__setitem__("protection_covered", 0),
            lambda value: value["simulation"]["reviews"][0]["calibration"].__setitem__("quantile_error", 1),
        )
        for mutate in mutations:
            changed = deepcopy(arm); mutate(changed)
            changed["trajectory_sha256"] = digest(changed["simulation"])
            with self.assertRaises(ValueError): audit_arm(record, changed, config, residuals)
        changed = deepcopy(arm); bundles = deepcopy(residuals)
        review = changed["simulation"]["reviews"][0]
        bundle = deepcopy(bundles[review["calibration"]["residuals_sha256"]])
        bundle["origins"][-1] = 999  # A future label with freshly recomputed receipt hashes.
        identity = digest(bundle); bundles[identity] = bundle
        review["calibration"]["residuals_sha256"] = identity
        changed["trajectory_sha256"] = digest(changed["simulation"])
        with self.assertRaises(ValueError): audit_arm(record, changed, config, bundles)

    def test_public_aggregate_denominators_and_parent_subset_are_consistent(self):
        root = Path(__file__).resolve().parents[1]
        report = decode((root / "docs/review/public-sales-safety-v1.json").read_text())
        parent = decode((root / "docs/review/public-sales-forecast-v1.json").read_text())
        self.assertEqual(report["subset_sha256"], parent["subset_sha256"])
        self.assertEqual((report["arms"], report["paired_contrasts"]), (768, 512))
        self.assertTrue(report["exploratory_consumed_sales"])
        self.assertEqual(report["availability"], "unknown")
        forbidden = {"items", "history", "demand", "residuals", "reviews", "fulfillments", "customer_id"}
        def inspect(value):
            if isinstance(value, dict):
                # Aggregate 'items' is only an integer count, never item identities.
                self.assertFalse((set(value) - {"items"}) & forbidden)
                if "items" in value: self.assertIs(type(value["items"]), int)
                for child in value.values(): inspect(child)
            elif isinstance(value, list):
                for child in value: inspect(child)
        inspect(report)
        for groups in report["aggregate_scores"].values():
            overall = groups["overall"]
            self.assertEqual(overall["items"], 32)
            score = overall["periods"]["holdout"]
            self.assertEqual((score["demand_units"], score["cycles"], score["protection_origins"]), (15373, 128, 96))
            self.assertEqual((score["defined_fill_items"], score["undefined_fill_items"]), (30, 2))
            self.assertEqual(score["immediate_fill"], Fraction(score["immediate_units"], 15373))
            self.assertEqual(score["cycle_service"], Fraction(score["shortage_free_cycles"], 128))
            self.assertEqual(score["protection_coverage"], Fraction(score["protection_covered"], 96))
            self.assertEqual(overall["full_cost"], sum(period["total"] for period in overall["costs"].values()))
            self.assertEqual(overall["full_cost"], sum(group["full_cost"] for name, group in groups.items() if name != "overall"))


if __name__ == "__main__":
    unittest.main()
