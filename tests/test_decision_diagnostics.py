"""Hand-calculated startup and accounting oracles, independent of model selection."""

from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest

from inventory_intelligence.decision import simulate
from inventory_intelligence.decision_diagnostics import common_window_costs, startup_feasibility
from inventory_intelligence.planning_runs import exact_json
from scripts.feasibility_diagnostic import build_report


class StartupOracles(unittest.TestCase):
    def bound(self, demand, **changes):
        params = dict(on_hand=0, lead_days=2, review_days=1)
        params.update(changes)
        return startup_feasibility(demand, **params)

    def test_clean_and_zero_controls(self):
        result = self.bound([2, 2, 2], on_hand=4)
        self.assertEqual(result["earliest_possible_order_receipt_day"], 2)
        self.assertEqual(result["inevitable_new_missed_units"], 0)
        self.assertEqual(result["immediate_fill_ceiling"], 1)
        self.assertIsNone(self.bound([0, 0])["immediate_fill_ceiling"])

    def test_backlog_precedes_today_prior_then_new_demand(self):
        result = self.bound([3, 0, 1], on_hand=2, lead_days=3,
            commitments=[dict(id="first", due_day=0, quantity=1),
                         dict(id="later", due_day=1, quantity=2)],
            inbound=[dict(id="receipt", arrival_day=1, quantity=2)])
        # Day0: prior1 then new1 fill, new2 miss. Day1 inbound2 clears old new
        # backlog; today's prior2 miss. Day2 new1 misses. Receipt earliest day3.
        self.assertEqual([row["new_missed_units"] for row in result["days"]], [2, 0, 1])
        self.assertEqual([row["prior_missed_units"] for row in result["days"]], [0, 2, 0])
        self.assertEqual(result["inevitable_prior_missed_units"], 2)
        self.assertEqual(result["immediate_fill_ceiling"], Fraction(1, 4))

    def test_later_known_inbound_cannot_repair_immediate_misses(self):
        result = self.bound([4, 0, 4], on_hand=2, lead_days=3,
                            inbound=[dict(id="receipt", arrival_day=2, quantity=4)])
        self.assertEqual([row["new_missed_units"] for row in result["days"]], [2, 0, 2])
        self.assertEqual(result["immediate_fill_ceiling"], Fraction(1, 2))

    def test_later_review_can_arrive_before_first_review(self):
        result = self.bound([0, 3, 0, 0, 0, 0, 0], on_hand=1, review_days=2,
                            supplier_delays=[5, 0, 0, 0, 0, 0, 0, 0])
        self.assertEqual(result["earliest_possible_order_receipt_day"], 4)
        self.assertEqual(result["inevitable_new_missed_units"], 2)
        self.assertEqual(result["immediate_fill_ceiling"], Fraction(1, 3))

    def test_receipt_boundary_and_no_scored_review(self):
        # New policy receipts on day2 precede day2 demand, so it is outside startup.
        result = self.bound([0, 0, 9])
        self.assertEqual(result["startup_days"], 2)
        self.assertEqual(result["inevitable_new_missed_units"], 0)
        result = self.bound([2], lead_days=1, review_days=3, review_phase=2)
        self.assertIsNone(result["earliest_possible_order_receipt_day"])
        self.assertEqual(result["startup_days"], 1)
        self.assertEqual(result["immediate_fill_ceiling"], 0)

    def test_possible_receipt_does_not_depend_on_actual_order(self):
        sim = simulate([0], [0, 0, 1], method="zero", on_hand=0, lead_days=1, review_days=1)
        self.assertEqual(next(row["day"] for row in sim["reviews"] if row["order_qty"]), 3)
        result = self.bound([0, 0, 1], lead_days=1)
        self.assertEqual(result["earliest_possible_order_receipt_day"], 1)
        self.assertEqual(result["inevitable_new_missed_units"], 0)

    def test_invalid_inputs_fail_instead_of_becoming_zero(self):
        for changes in (dict(on_hand=True), dict(lead_days=0), dict(review_phase=1),
                        dict(supplier_delays=[0]), dict(supplier_delays=[False] * 5),
                        dict(inbound=[dict(id="x", arrival_day=0, quantity=1)] * 2),
                        dict(commitments=[dict(id="x", due_day=3, quantity=1)])):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.bound([1, 1], **changes)
        for demand in ([], [None], [False], [1.0], [-1]):
            with self.subTest(demand=demand), self.assertRaises(ValueError):
                self.bound(demand)


class CommonAccountingOracles(unittest.TestCase):
    def setUp(self):
        # Three scored days with two pieces, plus two zero-demand runoff days.
        # No orders/backlog: cost = 2 * 1/2 * 5 = 5, terminal stock remains 2.
        self.sim = simulate([0], [0, 0, 0], method="zero", on_hand=2,
                            lead_days=1, review_days=1, holding_cost=Fraction(1, 2))

    def test_rational_extension_and_longer_no_demand_ledger(self):
        original = deepcopy(self.sim)
        result = common_window_costs(self.sim, holding_cost=Fraction(1, 2), end_day=8)
        self.assertEqual(result["scored_cost"], 3)
        self.assertEqual(result["original_runoff_cost"], 2)
        self.assertEqual(result["extension_holding_cost"], 3)
        self.assertEqual(result["common_runoff_cost"], 5)
        self.assertEqual(result["common_total_cost"], 8)
        self.assertEqual(self.sim, original)
        longer = simulate([0], [0] * 6, method="zero", on_hand=2,
                          lead_days=1, review_days=1, holding_cost=Fraction(1, 2))
        self.assertEqual(result["common_total_cost"], sum(d["total_cost"] for d in longer["days"]))
        self.assertEqual(result, common_window_costs(exact_json(self.sim),
                         holding_cost=Fraction(1, 2), end_day=8))

    def test_equal_window_is_identity(self):
        result = common_window_costs(self.sim, holding_cost=Fraction(1, 2), end_day=5)
        self.assertEqual(result["extension_days"], 0)
        self.assertEqual(result["common_total_cost"], 5)

    def test_unsettled_short_and_inexact_inputs_are_rejected(self):
        for changes in (dict(backlog=1), dict(outstanding_qty=1), dict(orders=[{}]), dict(on_hand=3)):
            sim = deepcopy(self.sim)
            sim["terminal"].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                common_window_costs(sim, holding_cost=1, end_day=8)
        for args in (dict(holding_cost=0.5, end_day=8), dict(holding_cost=1, end_day=4),
                     dict(holding_cost=1, end_day=True)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                common_window_costs(self.sim, **args)
        sim = deepcopy(self.sim)
        sim["days"][0]["total_cost"] = 1.0
        with self.assertRaises(ValueError):
            common_window_costs(sim, holding_cost=1, end_day=8)


class ReplayDiagnosticOracles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = build_report()
        cls.controls = {row["name"]: row for row in cls.report["controls"]}

    def test_lab_costs_preserved_and_delay_cost_gap_changes_by_sixty(self):
        base, delay = (self.controls[name] for name in ("baseline", "delay3"))
        self.assertEqual(base["accounting"]["original_total_cost"], "327")
        self.assertEqual(base["accounting"]["terminal_on_hand"], 20)
        # Baseline: original 33 days + 3 days * terminal20 * holding1 = 387.
        self.assertEqual(base["accounting"]["extension_holding_cost"], "60")
        self.assertEqual(base["accounting"]["common_total_cost"], "387")
        self.assertEqual(delay["accounting"]["original_total_cost"], "1171")
        self.assertEqual(delay["accounting"]["common_total_cost"], "1171")
        self.assertEqual(delay["common_cost_delta_vs_baseline"], "784")

    def test_delay_startup_bound_and_later_misses(self):
        delay = self.controls["delay3"]
        # Initial10 + inbound5 - prior3 supports only12 of the first20 units
        # before day5. Eight misses are inevitable; 60 of 68 occur later.
        self.assertEqual(delay["feasibility"]["inevitable_new_missed_units"], 8)
        self.assertEqual(delay["feasibility"]["immediate_fill_ceiling"], "13/14")
        self.assertEqual(delay["realized"]["startup_new_missed_units"], 8)
        self.assertEqual(delay["realized"]["later_new_missed_units"], 60)
        self.assertEqual(delay["realized"]["startup_new_demand_units"], 20)
        self.assertEqual(delay["realized"]["later_new_demand_units"], 92)
        self.assertEqual(delay["realized"]["immediate_fill_rate"], "11/28")

    def test_null_and_blocked_controls_retained(self):
        self.assertIsNone(self.controls["zero"]["feasibility"]["immediate_fill_ceiling"])
        self.assertIsNone(self.controls["zero"]["realized"]["immediate_fill_rate"])
        blocked = self.controls["incomplete_supply"]
        self.assertEqual(blocked["status"], "not_assessable")
        self.assertTrue(blocked["reasons"])
        for field in ("inputs", "feasibility", "realized", "accounting", "common_cost_delta_vs_baseline"):
            self.assertIsNone(blocked[field])
        self.assertEqual(len(self.report["controls"]), 5)

    def test_invalid_archive_cannot_become_an_evaluation(self):
        from inventory_intelligence.lab import load_evidence
        evidence = load_evidence()
        evidence["future_demand"]["quantities"][0] = None
        with self.assertRaises(ValueError):
            build_report(evidence)

    def test_cli_reproduces_exact_report(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "report.json"
            subprocess.run([sys.executable, str(root / "scripts/feasibility_diagnostic.py"),
                            "--output", str(output)], cwd=root, check=True, capture_output=True)
            self.assertEqual(json.loads(output.read_text()), self.report)


if __name__ == "__main__":
    unittest.main()
