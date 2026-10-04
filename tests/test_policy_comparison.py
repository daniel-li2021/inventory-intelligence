import unittest
from fractions import Fraction
from pathlib import Path
import types
import hashlib
import json
import subprocess

from inventory_intelligence.decision import _simulate, simulate
from inventory_intelligence.policy_comparison import simulate_policy
from scripts.policy_benchmark import full_cost, scenarios


class PolicyComparisonTests(unittest.TestCase):
    def test_default_kernel_matches_attested_historical_source(self):
        root = Path(__file__).resolve().parents[1]
        original = types.ModuleType("inventory_intelligence._archived_decision")
        original.__package__ = "inventory_intelligence"
        source = root / "docs/review/decision-v1-source.py.txt"
        exec(compile(source.read_bytes(), str(source), "exec"), original.__dict__)
        for method in ("mean", "seasonal_naive", "zero"):
            for delays in ([], [2, 0, 1, 2, 0, 1, 2, 0, 1]):
                args = dict(method=method, on_hand=3, lead_days=2, review_days=1,
                            commitments=[dict(id="p", due_day=1, quantity=4)],
                            inbound=[dict(id="i", arrival_day=3, quantity=7)],
                            supplier_delays=delays, safety_qty=2, pack_size=2, moq=3,
                            holding_cost=Fraction(1, 3), backlog_cost=2, order_cost=1)
                self.assertEqual(simulate([0, 2, 0, 3, 1, 0, 2], [4, 0, 1, 2], **args),
                                 original.simulate([0, 2, 0, 3, 1, 0, 2], [4, 0, 1, 2], **args))

    def test_known_late_inbound_does_not_cover_early_prefix_shortage(self):
        parameters = dict(method="naive", on_hand=2, lead_days=1, review_days=2,
                          inbound=[dict(id="late", arrival_day=5, quantity=20)])
        reference = simulate_policy([2], [2] * 14, policy="periodic_up_to", **parameters)
        prefix = simulate_policy([2], [2] * 14, policy="prefix_projection", **parameters)
        threshold = simulate_policy([2], [2] * 14, policy="periodic_sS", **parameters)
        # At review 0, aggregate position is 22; three-day target is only 6.
        # Prefix balances are 0,-2,-4 with no arrival inside those three days.
        self.assertEqual(reference["reviews"][0]["order_qty"], 0)
        self.assertEqual(threshold["reviews"][0]["order_qty"], 0)
        first = prefix["reviews"][0]
        self.assertEqual(first["ordering"]["need"], 4)
        self.assertEqual(first["order_qty"], 4)
        self.assertEqual([row["immediately_filled_units"] for row in reference["days"][:2]], [2, 0])
        self.assertEqual([row["immediately_filled_units"] for row in prefix["days"][:2]], [2, 2])

    def test_periodic_threshold_changes_only_trigger(self):
        parameters = dict(method="naive", on_hand=5, lead_days=1, review_days=2)
        up = simulate_policy([2], [2] * 7, policy="periodic_up_to", **parameters)
        ss = simulate_policy([2], [2] * 7, policy="periodic_sS", **parameters)
        self.assertEqual(up["reviews"][0]["order_qty"], 1)  # target6 − position5
        self.assertEqual(ss["reviews"][0]["order_qty"], 0)  # position5 > trigger2
        self.assertEqual(ss["reviews"][1]["ordering"]["trigger"], 2)
        self.assertEqual(ss["reviews"][1]["order_qty"], 5)  # position1 <= trigger2
        self.assertEqual([row["forecast"] for row in up["reviews"]],
                         [row["forecast"] for row in ss["reviews"]])

    def test_due_backlog_preserves_identity_and_is_charged_once(self):
        result = simulate_policy([0], [0] * 5, policy="prefix_projection", method="zero",
                                 on_hand=0, lead_days=1, review_days=1,
                                 commitments=[dict(id="prior-A", due_day=0, quantity=3)])
        review = result["reviews"][0]
        self.assertEqual(review["ordering"]["carryover"],
                         [dict(id="prior-A", due_day=0, quantity=3, kind="prior")])
        self.assertEqual(review["order_qty"], 3)
        self.assertEqual(result["days"][1]["fulfillments"],
                         [dict(id="prior-A", due_day=0, quantity=3, kind="prior")])
        self.assertEqual(result["metrics"]["on_time_prior_units"], 0)
        self.assertEqual(sum(row["order_qty"] for row in result["days"]), 3)
        self.assertEqual(result["terminal"]["on_hand"], 0)

    def test_common_rounding_and_settlement(self):
        for policy in ("periodic_up_to", "periodic_sS", "prefix_projection"):
            result = simulate_policy([1], [1], policy=policy, method="naive", on_hand=0,
                                     lead_days=1, review_days=1, pack_size=4, moq=5)
            self.assertEqual(result["reviews"][0]["order_qty"], 8)
            self.assertEqual(result["terminal"], dict(on_hand=7, backlog=0, outstanding_qty=0, orders=[]))
            self.assertTrue(all("ordering" not in row for row in result["reviews"] if row["runoff"]))

    def test_order_hook_copies_state_and_hides_realized_delay(self):
        observed = []
        def provider(state):
            observed.append(state)
            need = max(Fraction(0), state["target"] - state["inventory_position"])
            state["backlog"].clear()  # Cannot alter actual FIFO or pending quantity.
            state["commitments"].clear()
            if state["inbound"]:
                state["inbound"][0]["quantity"] = 999
            return dict(need=need)
        args = dict(method="naive", on_hand=0, lead_days=2, review_days=1,
                    supplier_delays=[2] * 9)
        result = _simulate([1], [1] * 4, _order_provider=provider, **args)
        reference = simulate([1], [1] * 4, **args)
        self.assertEqual(result["days"], reference["days"])
        self.assertEqual(result["metrics"], reference["metrics"])
        self.assertEqual(observed[1]["inbound"][0]["arrival_day"], 2)  # Actual is day4.
        self.assertNotIn("demand", observed[0])
        self.assertNotIn("supplier_delays", observed[0])

    def test_validation_and_no_future_demand_leakage(self):
        args = dict(method="naive", on_hand=0, lead_days=1, review_days=1)
        for bad in (-1, True, 1.5, None):
            with self.assertRaises(ValueError):
                _simulate([1], [1], _order_provider=lambda state: dict(need=bad), **args)
        with self.assertRaises(ValueError):
            simulate_policy([1], [1], policy="prefix_projection", supplier_delays=[1], **args)
        with self.assertRaises(ValueError):
            simulate_policy([1], [1], policy="invented", **args)
        left = simulate_policy([2], [2, 0, 0], policy="prefix_projection", **args)
        right = simulate_policy([2], [2, 9, 9], policy="prefix_projection", **args)
        self.assertEqual(left["reviews"][:2], right["reviews"][:2])

    def test_frozen_grid_and_paid_initial_inventory_cost(self):
        grid = list(scenarios())
        self.assertEqual(len(grid), 10)
        self.assertEqual(len({row["seed"] for row in grid if row["family"] == "lumpy"}), 3)
        zero = next(row for row in grid if row["family"] == "zero")
        self.assertEqual(zero["history"], [0] * 84)
        self.assertEqual(zero["demand"], [0] * 56)
        result = simulate_policy([0], [0, 0], policy="periodic_up_to", method="zero",
                                 on_hand=3, lead_days=1, review_days=1,
                                 holding_cost=1, backlog_cost=10, order_cost=2)
        receipt = full_cost(dict(parameters=dict(on_hand=3, inbound=[])), result)
        # Four accounting days * three pieces + paid stock 3*2 = 18.
        self.assertEqual(receipt["holding_cost"], 12)
        self.assertEqual(receipt["acquisition_cost"], 6)
        self.assertEqual(receipt["full_cost"], 18)
        self.assertIsNone(result["metrics"]["immediate_fill_rate"])

    def test_saved_evidence_costs_forecast_equality_and_hashes(self):
        root = Path(__file__).resolve().parents[1]
        report = json.loads((root / "docs/review/policy-comparison-v1.json").read_text())
        def encoded(value):
            return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        def rational(value):
            return Fraction(**value) if isinstance(value, dict) else Fraction(value)
        self.assertEqual(len(report["scenarios"]), 40)
        self.assertEqual(len(report["pairs"]), 80)
        # Consumed evidence binds one complete original source, including deleted docs.
        snapshot = "39bf64d7e70b9221afbe1d697fe49fd348fcdc04"
        artifact = "docs/review/policy-comparison-v1.json"
        self.assertEqual((root / artifact).read_bytes(),
                         subprocess.check_output(["git", "show", f"{snapshot}:{artifact}"], cwd=root))
        for name, expected in report["source_sha256"].items():
            raw = subprocess.check_output(["git", "show", f"{snapshot}:{name}"], cwd=root)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), expected)
        for cell in report["scenarios"]:
            self.assertEqual(hashlib.sha256(encoded(cell["inputs"])).hexdigest(), cell["input_sha256"])
            forecasts = None
            for arm in cell["arms"].values():
                simulation = arm["simulation"]
                self.assertEqual(hashlib.sha256(encoded(simulation)).hexdigest(), arm["trajectory_sha256"])
                receipts = [(row["day"], row["forecast"]) for row in simulation["reviews"]]
                if forecasts is not None:
                    self.assertEqual(receipts, forecasts)
                forecasts = receipts
                self.assertEqual(len(simulation["days"]), 65)
                self.assertEqual(simulation["terminal"]["backlog"], 0)
                self.assertEqual(simulation["terminal"]["outstanding_qty"], 0)
                days = simulation["days"]
                inputs = cell["inputs"]["parameters"]
                purchased = sum(day["order_qty"] for day in days)
                initial = inputs["on_hand"] + sum(row["quantity"] for row in inputs["inbound"])
                observed = sum(cell["inputs"]["demand"]) + sum(row["quantity"] for row in inputs["commitments"])
                self.assertEqual(initial + purchased, observed + simulation["terminal"]["on_hand"])
                # Independent arithmetic: prices + each end-stock/backlog day + setups.
                expected = 2 * (initial + purchased) + sum(
                    day["on_hand"] + 10 * day["backlog"] + 2 * bool(day["order_qty"])
                    for day in days)
                self.assertEqual(rational(arm["cost"]["full_cost"]), expected)
                metrics = simulation["metrics"]
                demand = sum(cell["inputs"]["demand"])
                fill = sum(day["immediately_filled_units"] for day in days[:56])
                self.assertEqual(rational(metrics["immediate_fill_rate"]) if demand else None,
                                 Fraction(fill, demand) if demand else None)
        cells = {row["input_sha256"]: row for row in report["scenarios"]}
        for pair in report["pairs"]:
            arms = cells[pair["input_sha256"]]["arms"]
            expected = rational(arms[pair["policy"]]["cost"]["full_cost"]) - rational(arms["periodic_up_to"]["cost"]["full_cost"])
            self.assertEqual(rational(pair["differences"]["full_cost"]), expected)


if __name__ == "__main__":
    unittest.main()
