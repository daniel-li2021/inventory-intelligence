"""Independent offline Decision Lab oracles; no database or model calls."""
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from inventory_intelligence import lab


def rehash_archive(evidence):
    """Rebuild transport hashes independently, leaving semantic validation to SUT."""
    def digest(value):
        return hashlib.sha256(json.dumps(value, sort_keys=True,
                              separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    for report in (evidence['forecast'], *evidence['plans'].values()):
        result = report['result']
        inputs = result['training'] if report['kind'] == 'forecast' else {
            key: result[key] for key in ('inventory', 'supply', 'training')}
        report['input_digest'] = digest(dict(context=report['context'], inputs=inputs))
    evidence['digest'] = digest({key: value for key, value in evidence.items() if key != 'digest'})
    return evidence


class DecisionLabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = lab.load_evidence()

    def evaluate(self, changes=None):
        return lab.evaluate(changes, evidence=self.evidence)

    def assert_plan(self, side, *, raw, order, without, with_order):
        self.assertEqual(side["status"], "assessable")
        plan = side["plan"]
        self.assertEqual(Fraction(plan["unrounded_need"]), raw)
        self.assertEqual(plan["whole_piece_need"], raw)
        self.assertEqual(plan["proposed_order_qty"], order)
        self.assertEqual(plan["rounding_extra"], order - raw)
        self.assertEqual([Fraction(d["balance_without_order"]) for d in plan["projection"]], without)
        self.assertEqual([Fraction(d["balance_with_order"]) for d in plan["projection"]], with_order)

    def assert_blocked(self, side):
        self.assertEqual(side["status"], "not_assessable")
        self.assertTrue(side["reasons"])
        for field in ("plan", "simulation", "costs", "risk"):
            self.assertIsNone(side[field], field)

    def test_baseline_prefix_projection_hand_calculation(self):
        result = self.evaluate()
        # 10 stock - 3 prior reservation - 4/day + confirmed 5 on day 1.
        # At the final horizon day -8 remains: safety 2 requires 10, pack 6 => 12.
        self.assert_plan(result["baseline"], raw=10, order=12,
                         without=[3, 4, 0, -4, -8], with_order=[3, 4, 12, 8, 4])
        self.assertEqual(result["baseline"], result["scenario"])
        self.assertEqual(result["baseline"]["plan"]["pre_arrival_shortage_days"], [])
        self.assertEqual(result["baseline"]["plan"]["inventory_position"], 12)
        json.dumps(result, allow_nan=False)

    def test_baseline_simulation_service_cost_and_conservation_oracle(self):
        side = self.evaluate()["baseline"]
        sim = side["simulation"]
        days, metrics = sim["days"], sim["metrics"]
        # Periodic simulation replenishes repeatedly; it does not execute just
        # the prefix proposal. Day 0 orders 12, followed by nine orders of 12.
        self.assertEqual([d["on_hand"] for d in days[:28]], [3, 4, 12] + [8, 4, 12] * 8 + [8])
        self.assertEqual([r["order_qty"] for r in sim["reviews"] if not r["runoff"]], [12] * 10)
        expected = dict(new_demand_units=112, immediately_filled_units=112,
                        eventually_filled_units=112, prior_commitment_units=3,
                        on_time_prior_units=3, complete_cycles=9, shortage_free_cycles=9,
                        shortage_days=0, backlog_piece_days=0, on_hand_piece_days=219,
                        order_count=10, runoff_order_count=0, end_on_hand=8, end_backlog=0)
        for name, value in expected.items():
            self.assertEqual(metrics[name], value, name)
        for name in ("immediate_fill_rate", "eventual_fill_rate", "on_time_prior_fill_rate", "cycle_service"):
            self.assertEqual(Fraction(metrics[name]), 1, name)
        self.assertEqual(Fraction(metrics["average_on_hand"]), Fraction(219, 28))
        self.assertEqual(Fraction(metrics["scored_cost"]), 239)
        self.assertEqual(Fraction(metrics["runoff_cost"]), 88)
        self.assertEqual(Fraction(metrics["total_cost"]), 327)
        self.assertEqual(Fraction(side["costs"]["scored"]["holding"]), 219)
        self.assertEqual(Fraction(side["costs"]["scored"]["setup"]), 20)
        self.assertEqual(Fraction(side["costs"]["scored"]["backlog"]), 0)
        self.assertEqual(Fraction(side["costs"]["total"]), 327)
        self.assertEqual(sim["terminal"]["on_hand"], 20)
        self.assertEqual(sim["terminal"]["backlog"], 0)
        self.assertEqual(sim["terminal"]["outstanding_qty"], 0)
        self.assertEqual(10 + sum(d["receipts"] for d in days),
                         sum(d["fulfilled_units"] for d in days) + 20)
        self.assertEqual(sum(d["fulfilled_units"] for d in days), 115)

    def test_demand_increase_decrease_and_round_up_whole_pieces(self):
        for percent, per_day, raw, order, without, with_order in (
            (150, 6, 20, 24, [1, 0, -6, -12, -18], [1, 0, 18, 12, 6]),
            (50, 2, 0, 0, [5, 8, 6, 4, 2], [5, 8, 6, 4, 2]),
            (101, 5, 15, 18, [2, 2, -3, -8, -13], [2, 2, 15, 10, 5]),
        ):
            with self.subTest(percent=percent):
                result = self.evaluate({"demand_percent": percent})
                self.assert_plan(result["scenario"], raw=raw, order=order,
                                 without=without, with_order=with_order)
                self.assertEqual([d["new_demand"] for d in result["scenario"]["simulation"]["days"][:28]], [per_day] * 28)
                self.assertEqual([d["quantity"] for d in result["scenario"]["forecast"]["training"]],
                                 [per_day] * len(result["scenario"]["forecast"]["training"]))
                self.assertEqual([d["source_quantity"] for d in result["scenario"]["forecast"]["training"]],
                                 [4] * len(result["scenario"]["forecast"]["training"]))
                self.assertEqual(result["baseline"]["plan"]["proposed_order_qty"], 12)
                comparison = result["comparison"]["proposed_order_qty"]
                self.assertEqual(Fraction(comparison["delta"]), order - 12)

    def test_policy_reservation_and_timing_oracles(self):
        cases = [
            ({"lead_days": 3}, 14, 18, [3, 4, 0, -4, -8, -12], [3, 4, 0, 14, 10, 6]),
            ({"reservation_qty": 8}, 15, 18, [-2, -1, -5, -9, -13], [-2, -1, 13, 9, 5]),
            ({"safety_qty": 8}, 16, 18, [3, 4, 0, -4, -8], [3, 4, 18, 14, 10]),
            ({"pack_size": 4}, 10, 12, [3, 4, 0, -4, -8], [3, 4, 12, 8, 4]),
            ({"moq": 25}, 10, 30, [3, 4, 0, -4, -8], [3, 4, 30, 26, 22]),
            ({"inbound_day": 4}, 11, 12, [3, -1, -5, -9, -8], [3, -1, 7, 3, 4]),
        ]
        for changes, raw, order, without, with_order in cases:
            with self.subTest(changes=changes):
                side = self.evaluate(changes)["scenario"]
                self.assert_plan(side, raw=raw, order=order, without=without, with_order=with_order)
        late = self.evaluate({"inbound_day": 4})["scenario"]
        self.assertEqual(len(late["plan"]["pre_arrival_shortage_days"]), 1)
        self.assertEqual(late["simulation"]["days"][1]["backlog"], 1)
        self.assertEqual(late["simulation"]["days"][1]["immediately_filled_units"], 3)

    def test_zero_demand_preserves_null_denominators(self):
        side = self.evaluate({"demand_percent": 0, "reservation_qty": 0})["scenario"]
        sim = side["simulation"]
        self.assertEqual(side["plan"]["proposed_order_qty"], 0)
        self.assertEqual(sim["metrics"]["new_demand_units"], 0)
        for name in ("immediate_fill_rate", "eventual_fill_rate", "on_time_prior_fill_rate", "forecast_wape"):
            self.assertIsNone(sim["metrics"][name], name)
        self.assertEqual(sim["metrics"]["shortage_days"], 0)
        self.assertIsNone(side["risk"]["meets_service_target"])
        self.assertEqual(sim["terminal"]["on_hand"], 15)

    def test_supplier_delay_hidden_from_ordering_and_changes_receipts(self):
        result = self.evaluate({"supplier_delay_days": 3})
        baseline, scenario = result["baseline"], result["scenario"]
        self.assertEqual(baseline["plan"], scenario["plan"])
        self.assertEqual(baseline["simulation"]["reviews"][0], scenario["simulation"]["reviews"][0])
        self.assertEqual(scenario["simulation"]["days"][2]["receipts"], 0)
        self.assertEqual(scenario["simulation"]["days"][5]["receipts"], 12)
        self.assertEqual([d["backlog"] for d in scenario["simulation"]["days"][:6]], [0, 0, 0, 4, 8, 0])
        self.assertEqual(scenario["simulation"]["metrics"]["newly_unmet_units"], 68)
        self.assertEqual(scenario["simulation"]["metrics"]["shortage_days"], 17)
        self.assertEqual(scenario["simulation"]["metrics"]["backlog_piece_days"], 100)
        self.assertEqual(Fraction(scenario["simulation"]["metrics"]["immediate_fill_rate"]), Fraction(11, 28))
        self.assertEqual(Fraction(scenario["costs"]["scored"]["total"]), 1027)
        self.assertEqual(Fraction(scenario["costs"]["runoff"]["total"]), 144)
        self.assertEqual(Fraction(scenario["costs"]["total"]), 1171)
        self.assertEqual(Fraction(result["comparison"]["total_cost"]["delta"]), 844)
        self.assertEqual(Fraction(result["comparison"]["average_on_hand"]["delta"]), Fraction(-53, 7))

    def test_every_scenario_day_preserves_pieces_and_exact_cost_ledger(self):
        for change in ({}, {"demand_percent": 200}, {"supplier_delay_days": 14},
                       {"inbound_day": 27, "reservation_qty": 100},
                       {"safety_qty": 100, "moq": 100, "pack_size": 24}):
            with self.subTest(change=change):
                sim = self.evaluate(change)["scenario"]["simulation"]
                receipts = fulfilled = obligations = 0
                for day in sim["days"]:
                    receipts += day["receipts"]
                    fulfilled += day["fulfilled_units"]
                    obligations += day["new_demand"] + day["prior_demand"]
                    self.assertEqual(10 + receipts - fulfilled, day["on_hand"])
                    self.assertEqual(obligations - fulfilled, day["backlog"])
                    self.assertEqual(Fraction(day["holding_cost"]), day["on_hand"])
                    self.assertEqual(Fraction(day["backlog_cost"]), 10 * day["backlog"])
                    self.assertEqual(Fraction(day["order_cost"]), 2 if day["order_qty"] else 0)
                    self.assertEqual(Fraction(day["total_cost"]),
                                     day["on_hand"] + 10 * day["backlog"] + (2 if day["order_qty"] else 0))
                self.assertEqual(Fraction(sim["metrics"]["total_cost"]),
                                 sum(Fraction(d["total_cost"]) for d in sim["days"]))
                self.assertEqual(obligations, fulfilled)
                self.assertEqual(sim["terminal"]["outstanding_qty"], 0)

    def test_pairing_is_immutable_and_identifiers_deterministic(self):
        original = deepcopy(self.evidence)
        first = self.evaluate({"safety_qty": 7, "pack_size": 4})
        second = self.evaluate({"pack_size": 4, "safety_qty": 7})
        self.assertEqual(first, second)
        self.assertEqual(self.evidence, original)
        self.assertEqual(first["baseline"], self.evaluate()["baseline"])
        self.assertNotEqual(first["baseline"]["run_id"], first["scenario"]["run_id"])
        for side in (first["baseline"], first["scenario"]):
            self.assertTrue(side["run_id"])
            self.assertNotIn(side["run_id"], json.dumps(self.evidence["plans"]))
            stages = [node["stage"] for node in side["trace"]]
            self.assertEqual(len(stages), len(set(stages)))
            self.assertEqual(stages, ["reliability", "inventory", "demand_forecast", "supply", "policy",
                                      "raw_requirement", "rounding", "recommendation", "simulation"])
            for node in side["trace"]:
                self.assertTrue(node["label"])
                self.assertTrue(node["explanation"])
                self.assertTrue(node["references"])
                self.assertIn("data", node)
                if node["stage"] in ("demand_forecast", "raw_requirement", "rounding", "recommendation", "simulation"):
                    self.assertIn(dict(source="lab.calculation", id=side["run_id"]), node["references"])

    def test_incomplete_supply_suppresses_outputs_and_retains_baseline(self):
        result = self.evaluate({"evidence_case": "incomplete_supply"})
        self.assert_blocked(result["scenario"])
        self.assertEqual(result["baseline"], self.evaluate()["baseline"])
        def assert_null_deltas(values):
            for value in values.values():
                if "scenario" in value:
                    self.assertIsNone(value["scenario"])
                    self.assertIsNone(value["delta"])
                else:
                    assert_null_deltas(value)
        assert_null_deltas(result["comparison"])

    def test_corrupt_and_semantically_malformed_archive_fail_closed(self):
        bad_digest = deepcopy(self.evidence)
        bad_digest["future_demand"]["quantities"][0] = 99
        invalid_archives = [None, {}, {"digest": "x"}, bad_digest]
        # Recomputing the outer transport hash cannot approve invalid business
        # observations or a deleted validated source report.
        for change in (lambda d: d.update(synthetic=False),
                       lambda d: d["future_demand"].update(quantities=[True] * 28),
                       lambda d: d["plans"].pop("clean"),
                       lambda d: d["plans"]["clean"]["result"].update(proposed_order_qty=999)):
            malformed = deepcopy(self.evidence)
            change(malformed)
            malformed["digest"] = lab.archive_digest(malformed)
            invalid_archives.append(malformed)
        for archive in invalid_archives[1:]:
            with self.subTest(archive=str(archive)[:80]):
                result = lab.evaluate(evidence=archive)
                self.assert_blocked(result["baseline"])
                self.assert_blocked(result["scenario"])
                self.assertIn("invalid_evidence_archive", result["baseline"]["reasons"])
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "bad.json"
                    path.write_text(json.dumps(archive))
                    with self.assertRaises(ValueError):
                        lab.load_evidence(path)

    def test_invalid_adapter_controls_rejected_before_calculation(self):
        for change in ({"demand_percent": True}, {"lead_days": 1.0}, {"moq": "10"},
                       {"pack_size": 0}, {"inbound_day": 28}, {"unknown": 1}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.evaluate(change)

    def test_rehashed_supply_archive_requires_complete_consistent_manifest(self):
        changes = {
            'wrong key': lambda s: s['batch'].update(sku_id='other'),
            'wrong cutoff': lambda s: s['batch'].update(as_of='2026-01-03T08:00:00+00:00'),
            'missing status': lambda s: s['batch'].pop('status'),
            'wrong declared count': lambda s: s['batch'].update(expected_inbound=999),
            'boolean declared count': lambda s: s['batch'].update(expected_reservations=True),
            'missing observation': lambda s: s['inbound'][0].pop('observed_at'),
            'clock inversion': lambda s: s['inbound'][0].update(observed_at='2026-01-01T08:00:00+00:00'),
            'null receipt identity': lambda s: s['inbound'][0].update(inbound_id=None),
            'duplicate receipt identity': lambda s: s['inbound'][1].update(inbound_id='confirmed'),
            'duplicate row identity': lambda s: s['inbound'][1].update(row_id=s['inbound'][0]['row_id']),
            'invented clean reason': lambda s: s.update(reasons=['incomplete_or_mismatched_supply']),
        }
        for label, change in changes.items():
            with self.subTest(label=label):
                archive = deepcopy(self.evidence)
                change(archive['plans']['clean']['result']['supply'])
                rehash_archive(archive)
                self.assert_blocked(lab.evaluate(evidence=archive)['baseline'])

    def test_rehashed_inventory_archive_reconciles_every_saved_key(self):
        changes = {
            'unreconciled other key': lambda s: s['snapshots'][1].update(on_hand_qty=999),
            'future snapshot cutoff': lambda s: s['snapshots'][0].update(as_of='2026-01-03T08:00:00+00:00'),
            'missing observation': lambda s: s['snapshots'][0].pop('observed_at'),
            'duplicate source row': lambda s: s['snapshots'][1].update(row_id=s['snapshots'][0]['row_id']),
            'wrong watermark': lambda s: s['snapshots'][0].update(watermark=1),
            'wrong count': lambda s: s['batches'][1].update(expected_row_count=99),
            'missing other coverage': lambda s: s['coverage'].pop(1),
            'wrong opening batch': lambda s: s['opening_balances'][0].update(batch_id='planning-demo:snapshot'),
        }
        for label, change in changes.items():
            with self.subTest(label=label):
                archive = deepcopy(self.evidence)
                for report in archive['plans'].values():
                    change(report['result']['inventory']['source'])
                rehash_archive(archive)
                self.assert_blocked(lab.evaluate(evidence=archive)['baseline'])

    def test_rehashed_demand_archive_preserves_unique_observation_lineage(self):
        changes = {
            'duplicate row identity': lambda t: t['days'][1]['order_records'][0].update(
                row_id=t['days'][0]['order_records'][0]['row_id']),
            'duplicate order line': lambda t: t['days'][1]['order_records'][0].update(
                order_id=t['days'][0]['order_records'][0]['order_id']),
            'boolean expected lines': lambda t: t['days'][0]['day_record'].update(expected_lines=True),
            'boolean revision': lambda t: t['days'][0]['day_record'].update(revision=True),
            'order before acceptance': lambda t: t['days'][0]['order_records'][0].update(
                source_recorded_at='2025-12-05T08:00:00+00:00'),
        }
        for label, change in changes.items():
            with self.subTest(label=label):
                archive = deepcopy(self.evidence)
                for report in (archive['forecast'], *archive['plans'].values()):
                    change(report['result']['training'])
                archive['plans']['clean']['result']['forecast']['training'] = deepcopy(
                    archive['plans']['clean']['result']['training'])
                rehash_archive(archive)
                self.assert_blocked(lab.evaluate(evidence=archive)['baseline'])

    def test_rehashed_report_links_and_gate_remain_consistent(self):
        changes = {
            'wrong horizon': lambda e: e['plans']['clean']['context'].update(horizon=99),
            'wrong policy': lambda e: e['plans']['clean']['context'].update(policy_version='other'),
            'reused run identity': lambda e: e['forecast'].update(run_id=e['plans']['clean']['run_id']),
            'blocked forecast leaked': lambda e: e['plans']['incomplete_supply']['result'].update(
                forecast=e['plans']['clean']['result']['forecast']),
            'blocked reason invented': lambda e: e['plans']['incomplete_supply']['result'].update(
                reasons=['incomplete_or_mismatched_supply', 'invented']),
        }
        for label, change in changes.items():
            with self.subTest(label=label):
                archive = deepcopy(self.evidence)
                change(archive)
                rehash_archive(archive)
                self.assert_blocked(lab.evaluate(evidence=archive)['baseline'])


if __name__ == "__main__":
    unittest.main()
