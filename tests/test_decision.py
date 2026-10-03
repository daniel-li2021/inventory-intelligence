"""Independent, hand-calculated whole-piece and exact-cost decision oracles.

Run with: PYTHONPATH=src python3 -m unittest tests.test_decision
"""
from fractions import Fraction
import unittest

from inventory_intelligence.decision import simulate


class DecisionOracleTests(unittest.TestCase):
    def run_case(self, demand, **kwargs):
        inputs = dict(method="zero", on_hand=0, lead_days=1, review_days=1)
        inputs.update(kwargs)
        return simulate(inputs.pop("history", [0] * 7), demand, **inputs)

    def assert_metrics(self, result, **expected):
        for key, value in expected.items():
            with self.subTest(metric=key):
                self.assertEqual(result["metrics"][key], value)

    def assert_terminal(self, result, stock=0):
        self.assertEqual(result["terminal"]["on_hand"], stock)
        self.assertEqual(result["terminal"]["backlog"], 0)
        self.assertEqual(result["terminal"]["outstanding_qty"], 0)
        self.assertEqual(result["terminal"]["orders"], [])
        for day in result["days"]:
            for key in ("on_hand", "backlog", "outstanding_qty"):
                self.assertIs(type(day[key]), int)
                self.assertGreaterEqual(day[key], 0)

    def test_full_event_sequence_fifo_and_rational_costs(self):
        result = self.run_case(
            [3, 0, 1], on_hand=2,
            commitments=({"id": "first", "due_day": 0, "quantity": 1},
                         {"id": "later", "due_day": 1, "quantity": 2}),
            inbound=({"id": "confirmed", "arrival_day": 1, "quantity": 2},),
            holding_cost=Fraction(1, 2), backlog_cost=Fraction(5, 2),
            order_cost=Fraction(3, 2))
        self.assertEqual(result["contract_version"], "decision-benchmark-v1")
        # (receipt, prior due, new demand, immediate fill, end stock/backlog,
        #  new unmet, order, pipeline, total daily cost), all calculated by hand.
        expected = [
            (0, 1, 3, 1, 0, 2, 2, 0, 2, Fraction(5)),
            (2, 2, 0, 0, 0, 2, 2, 2, 2, Fraction(13, 2)),
            (2, 0, 1, 0, 0, 1, 1, 0, 0, Fraction(5, 2)),
            (0, 0, 0, 0, 0, 1, 0, 1, 1, Fraction(4)),
            (1, 0, 0, 0, 0, 0, 0, 0, 0, Fraction(0)),
        ]
        keys = ("receipts", "prior_demand", "new_demand", "immediately_filled_units",
                "on_hand", "backlog", "newly_unmet_units", "order_qty",
                "outstanding_qty", "total_cost")
        self.assertEqual([tuple(day[k] for k in keys) for day in result["days"]], expected)
        self.assertEqual([day["holding_cost"] for day in result["days"]], [0] * 5)
        self.assertEqual([day["backlog_cost"] for day in result["days"]],
                         [5, 5, Fraction(5, 2), Fraction(5, 2), 0])
        self.assertEqual([day["order_cost"] for day in result["days"]],
                         [0, Fraction(3, 2), 0, Fraction(3, 2), 0])
        self.assertEqual([day["scored"] for day in result["days"]], [True] * 3 + [False] * 2)
        self.assertEqual([day["shortage"] for day in result["days"]], [True] * 4 + [False])
        # Yesterday's new backlog takes precedence over today's prior commitment.
        self.assertEqual(result["days"][1]["fulfillments"],
                         [{"id": "new:0", "kind": "new", "due_day": 0, "quantity": 2}])
        self.assert_metrics(result, new_demand_units=4, immediately_filled_units=1,
                            immediate_fill_rate=Fraction(1, 4), eventually_filled_units=4,
                            eventual_fill_rate=1, prior_commitment_units=3,
                            on_time_prior_units=1, on_time_prior_fill_rate=Fraction(1, 3),
                            shortage_days=3, newly_unmet_units=5, backlog_piece_days=5,
                            on_hand_piece_days=0, average_on_hand=0, complete_cycles=3,
                            shortage_free_cycles=0, cycle_service=0, end_on_hand=0,
                            end_backlog=1, order_count=1, runoff_order_count=1,
                            scored_cost=14, runoff_cost=4, total_cost=18)
        self.assertEqual(sum(day["fulfilled_units"] for day in result["days"]), 7)
        self.assert_terminal(result)

    def test_prior_identity_tie_order_and_no_early_fulfillment(self):
        result = self.run_case(
            [1, 0], on_hand=2,
            commitments=({"id": "z", "due_day": 0, "quantity": 2},
                         {"id": "a", "due_day": 0, "quantity": 1}))
        self.assertEqual(result["days"][0]["fulfillments"], [
            {"id": "a", "kind": "prior", "due_day": 0, "quantity": 1},
            {"id": "z", "kind": "prior", "due_day": 0, "quantity": 1}])
        self.assert_metrics(result, on_time_prior_units=2, immediately_filled_units=0)
        future = self.run_case(
            [0] * 4, on_hand=8,
            commitments=({"id": "soon", "due_day": 1, "quantity": 3},
                         {"id": "later", "due_day": 3, "quantity": 5}))
        self.assertEqual([day["on_hand"] for day in future["days"][:4]], [8, 5, 5, 0])
        self.assertEqual(future["days"][0]["fulfillments"], [])
        ordered = self.run_case(
            [0] * 4,
            commitments=({"id": "soon", "due_day": 1, "quantity": 3},
                         {"id": "later", "due_day": 3, "quantity": 5}))
        self.assertEqual([review["target"] for review in ordered["reviews"][:4]], [3, 0, 5, 0])
        self.assertEqual([day["order_qty"] for day in ordered["days"][:4]], [3, 0, 5, 0])
        self.assert_metrics(ordered, on_time_prior_units=8, shortage_days=0)
        self.assert_terminal(ordered)

    def test_lead_time_shortage_and_terminal_holding_are_not_erased(self):
        result = self.run_case([1, 1, 1], history=[1], method="naive", lead_days=2)
        self.assertEqual([day["receipts"] for day in result["days"]], [0, 0, 3, 1, 1, 0])
        self.assertEqual([day["backlog"] for day in result["days"]], [1, 2, 0, 0, 0, 0])
        self.assertEqual([day["order_qty"] for day in result["days"]], [3, 1, 1, 0, 0, 0])
        self.assert_metrics(result, immediately_filled_units=1, immediate_fill_rate=Fraction(1, 3),
                            eventual_fill_rate=1, shortage_days=2, backlog_piece_days=3,
                            scored_cost=30, runoff_cost=5, total_cost=35, runoff_order_count=0)
        self.assert_terminal(result, stock=2)

    def test_delayed_pipeline_prevents_repeat_orders_and_counts_zero_slots(self):
        result = self.run_case([0] * 4, safety_qty=4, supplier_delays=[2, 0, 0, 0, 0, 0, 0, 0])
        self.assertEqual(len(result["days"]), 8)  # N + L + max delay + R.
        self.assertEqual([day["receipts"] for day in result["days"]], [0, 0, 0, 4, 0, 0, 0, 0])
        self.assertEqual([review["inventory_position"] for review in result["reviews"][:4]], [0, 4, 4, 4])
        self.assertEqual([review["order_qty"] for review in result["reviews"]], [4] + [0] * 7)
        self.assert_metrics(result, order_count=1, scored_cost=4, runoff_cost=16, total_cost=20)
        self.assert_terminal(result, stock=4)
        # Slot zero has no order: the first positive order must use delay[1].
        slotted = self.run_case([1, 0, 0], supplier_delays=[0, 2, 0, 0, 0, 0, 0])
        self.assertEqual([day["order_qty"] for day in slotted["days"]], [0, 1, 0, 0, 0, 0, 0])
        self.assertEqual([day["receipts"] for day in slotted["days"]], [0, 0, 0, 0, 1, 0, 0])
        self.assert_metrics(slotted, immediate_fill_rate=0, eventual_fill_rate=1,
                            shortage_days=3, scored_cost=30, runoff_cost=10, total_cost=40)
        self.assert_terminal(slotted)

    def test_pack_moq_rounding_and_fixed_runoff_no_forecast(self):
        result = self.run_case([0], history=[1, 0], method="mean", review_days=2,
                               pack_size=4, moq=5, holding_cost=Fraction(1, 3),
                               backlog_cost=Fraction(2, 3), order_cost=Fraction(5, 7))
        self.assertEqual(result["reviews"][0]["target"], Fraction(3, 2))
        self.assertEqual(result["reviews"][0]["order_qty"], 8)
        self.assertEqual(result["reviews"][1]["forecast"], [])
        self.assertEqual(result["reviews"][1]["order_qty"], 0)
        self.assert_metrics(result, scored_cost=Fraction(5, 7), runoff_cost=8,
                            total_cost=Fraction(61, 7), forecast_origins=0, forecast_points=0,
                            forecast_mae=None, forecast_bias=None, forecast_wape=None,
                            forecast_cumulative_mae=None, forecast_cumulative_bias=None)
        self.assert_terminal(result, stock=8)
        no_need = self.run_case([0], pack_size=4, moq=5)
        self.assert_metrics(no_need, order_count=0, runoff_order_count=0, total_cost=0)
        safety = self.run_case([0], safety_qty=4, review_days=2)
        self.assertEqual([review["order_qty"] for review in safety["reviews"]], [4, 0])
        self.assert_terminal(safety, stock=4)

    def test_clean_zero_rates_null_and_empty_shelf_not_shortage(self):
        result = self.run_case([0] * 4, method="naive", review_days=2)
        self.assert_metrics(result, new_demand_units=0, immediate_fill_rate=None,
                            eventual_fill_rate=None, on_time_prior_fill_rate=None,
                            shortage_days=0, newly_unmet_units=0, backlog_piece_days=0,
                            on_hand_piece_days=0, average_on_hand=0, complete_cycles=2,
                            shortage_free_cycles=2, cycle_service=1, total_cost=0,
                            forecast_origins=1, forecast_points=3, forecast_actual_units=0,
                            forecast_mae=0, forecast_bias=0, forecast_wape=None,
                            forecast_cumulative_mae=0, forecast_cumulative_bias=0)
        self.assertFalse(any(day["shortage"] for day in result["days"]))
        self.assert_terminal(result)

    def test_cycle_denominator_excludes_phase_prefix_and_incomplete_suffix(self):
        result = self.run_case(
            [1, 0, 0, 0, 0, 1], review_days=2, review_phase=1,
            inbound=({"id": "confirmed", "arrival_day": 1, "quantity": 1},))
        self.assertEqual([day["shortage"] for day in result["days"][:6]],
                         [True, False, False, False, False, True])
        self.assert_metrics(result, complete_cycles=2, shortage_free_cycles=2,
                            cycle_service=1, shortage_days=2, immediate_fill_rate=0,
                            eventual_fill_rate=1, scored_cost=20, runoff_cost=20, total_cost=40)
        self.assert_terminal(result)
        incomplete = self.run_case([0], review_days=2, review_phase=1)
        self.assert_metrics(incomplete, complete_cycles=0, shortage_free_cycles=0, cycle_service=None)

    def test_forecast_daily_and_cumulative_scores_use_complete_origins(self):
        result = self.run_case([1, 3, 0, 2, 4, 0], history=[2], method="naive", review_days=2)
        self.assertEqual([review["forecast"] for review in result["reviews"][:3]],
                         [[Fraction(2)] * 3, [Fraction(3)] * 3, [Fraction(2)] * 3])
        # Origin 0 errors (1,-1,2); origin 2 errors (3,1,-1).
        self.assert_metrics(result, forecast_origins=2, forecast_points=6, forecast_actual_units=10,
                            forecast_mae=Fraction(3, 2), forecast_bias=Fraction(5, 6),
                            forecast_wape=Fraction(9, 10), forecast_cumulative_mae=Fraction(5, 2),
                            forecast_cumulative_bias=Fraction(5, 2))

    def test_future_observations_and_hidden_trace_are_not_policy_inputs(self):
        first = self.run_case([1, 0, 0, 0], history=[2], method="mean", review_days=2)
        changed_future = self.run_case([1, 0, 99, 99], history=[2], method="mean", review_days=2)
        self.assertEqual(first["reviews"][0], changed_future["reviews"][0])
        self.assertEqual(first["reviews"][1], changed_future["reviews"][1])
        self.assertEqual(first["reviews"][0]["forecast"], [Fraction(2)] * 3)
        self.assertEqual(first["reviews"][1]["forecast"], [Fraction(1)] * 3)
        # Equal physical state and history at day zero: unseen arrival delays cannot
        # change its forecast, target, position or order. Later receipts may differ.
        slow = self.run_case([0] * 4, safety_qty=4, supplier_delays=[2, 0, 0, 0, 0, 0, 0, 0])
        fast = self.run_case([0] * 4, safety_qty=4, supplier_delays=[0, 0, 0, 0, 0, 0])
        self.assertEqual(slow["reviews"][0], fast["reviews"][0])

    def test_invalid_trust_boundary_inputs_are_rejected(self):
        invalid = []
        for name in ("history", "demand"):
            for value in ([], [True], [1.0], [None], [-1], [{"day": 0, "quantity": 1}]):
                invalid.append({name: value})
        for name in ("lead_days", "review_days", "pack_size", "moq"):
            for value in (0, -1, True, 1.0, None):
                invalid.append({name: value})
        for name in ("on_hand", "safety_qty", "review_phase"):
            for value in (-1, True, 1.0, None):
                invalid.append({name: value})
        invalid += [{"review_phase": 1}, {"lead_days": 366}, {"method": "unknown"},
                    {"method": "seasonal_naive", "history": [1] * 6}]
        for name in ("holding_cost", "backlog_cost", "order_cost"):
            for value in (-1, Fraction(-1, 2), True, 1.0, "1", None):
                invalid.append({name: value})
        for name, day_key in (("commitments", "due_day"), ("inbound", "arrival_day")):
            valid = {"id": "a", day_key: 0, "quantity": 1}
            for value in (None, {}, {"id": "a", day_key: 0}):
                invalid.append({name: [value]})
            for field, values in (("id", ("", None, 1)),
                                  (day_key, (-1, 2, True, 0.0, None)),
                                  ("quantity", (0, -1, True, 1.0, None))):
                for value in values:
                    invalid.append({name: [{**valid, field: value}]})
            invalid.append({name: [valid, dict(valid)]})
        for value in ([0], [0] * 5, [0, -1, 0, 0], [False] * 4, [0.0] * 4, [None] * 4):
            invalid.append({"supplier_delays": value})
        for change in invalid:
            with self.subTest(inputs=change):
                inputs = dict(history=[0] * 7, demand=[0, 0], method="zero", on_hand=0,
                              lead_days=1, review_days=1)
                inputs.update(change)
                history, demand = inputs.pop("history"), inputs.pop("demand")
                with self.assertRaises((ValueError, TypeError)):
                    simulate(history, demand, **inputs)


if __name__ == "__main__":
    unittest.main()
