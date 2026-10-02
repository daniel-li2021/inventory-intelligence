"""Independent date/eligibility oracles against real PostgreSQL."""

from datetime import date, datetime, timedelta, timezone
import os
import unittest
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row

from inventory_intelligence.demand import midnight, read_series
from tests.planning_oracle import manual_demand, put, START, ORIGIN
from synthetic.demand import load_demand, END


class Demand(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.owner = psycopg.connect(os.environ["TEST_DATABASE_URL"], autocommit=True, row_factory=dict_row)
        cls.runner = psycopg.connect(os.environ["DATABASE_URL"], autocommit=True, row_factory=dict_row)
        cls.addClassCleanup(cls.owner.close)
        cls.addClassCleanup(cls.runner.close)

    def setUp(self):
        self.prefix = "demand:" + str(uuid4())
        _, self.args = manual_demand(self.owner, self.prefix)

    def read(self, **overrides):
        with self.runner.transaction():
            self.runner.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
            return read_series(self.runner, **(self.args | overrides))

    def test_complete_zero_missing_and_constrained_days(self):
        report = self.read()
        self.assertEqual(report["status"], "eligible")
        self.assertEqual([d["quantity"] for d in report["days"]], [0, 2, 4, 6, 8, 10, 12])
        for field, value, reason in (("coverage", "incomplete", "incomplete_day"),
                                     ("availability", "stockout", "constrained_or_unknown_availability"),
                                     ("availability", "unknown", "constrained_or_unknown_availability"),
                                     ("expected_lines", 1, "line_count_mismatch")):
            row = dict(self.owner.execute("SELECT * FROM planning_input.day_observations WHERE row_id=%s",
                                         (self.prefix + ":day:0",)).fetchone())
            put(self.owner, "day_observations", **(row | dict(row_id=str(uuid4()), revision=2, **{field: value})))
            self.owner.execute("UPDATE planning_input.demand_batches SET expected_days=expected_days+1 WHERE batch_id=%s",
                               (self.args["batch_id"],))
            blocked = self.read()
            self.assertEqual(blocked["status"], "not_assessable")
            self.assertIsNone(blocked["days"][0]["quantity"])
            self.assertIn(reason, blocked["days"][0]["reasons"])
            self.owner.execute("DELETE FROM planning_input.day_observations WHERE revision=2 AND batch_id=%s", (self.args["batch_id"],))
            self.owner.execute("UPDATE planning_input.demand_batches SET expected_days=7 WHERE batch_id=%s", (self.args["batch_id"],))
        self.owner.execute("DELETE FROM planning_input.day_observations WHERE row_id=%s", (self.prefix + ":day:0",))
        self.owner.execute("UPDATE planning_input.demand_batches SET expected_days=6 WHERE batch_id=%s", (self.args["batch_id"],))
        missing = self.read()
        self.assertIsNone(missing["days"][0]["quantity"])
        self.assertEqual(missing["days"][0]["reasons"], ["missing_day_evidence"])

    def test_late_correction_cancellation_and_two_knowledge_clocks(self):
        row = dict(self.owner.execute("SELECT * FROM planning_input.order_versions WHERE row_id=%s", (self.prefix + ":order:1",)).fetchone())
        correction = row | dict(row_id=self.prefix + ":revision", revision=2, accepted_qty=9,
                                status="cancelled", source_recorded_at=ORIGIN + timedelta(days=1),
                                observed_at=ORIGIN + timedelta(days=2))
        put(self.owner, "order_versions", **correction)
        self.owner.execute("UPDATE planning_input.demand_batches SET expected_orders=7 WHERE batch_id=%s", (self.args["batch_id"],))
        for knowledge, expected in ((ORIGIN, 2), (ORIGIN + timedelta(days=1), 2),
                                     (ORIGIN + timedelta(days=2), 9)):
            report = self.read(known_at=knowledge)
            self.assertEqual(report["status"], "eligible")
            self.assertEqual(report["days"][1]["quantity"], expected)
        # Future recording time must remain invisible even if ingestion is earlier.
        self.owner.execute("UPDATE planning_input.order_versions SET source_recorded_at=%s, observed_at=%s WHERE row_id=%s",
                           (ORIGIN + timedelta(days=3), ORIGIN, correction["row_id"]))
        self.assertEqual(self.read()["days"][1]["quantity"], 2)

    def test_duplicate_identity_changed_key_and_manifest_do_not_pass(self):
        row = dict(self.owner.execute("SELECT * FROM planning_input.order_versions WHERE row_id=%s", (self.prefix + ":order:1",)).fetchone())
        put(self.owner, "order_versions", **(row | dict(row_id=self.prefix + ":duplicate")))
        self.owner.execute("UPDATE planning_input.demand_batches SET expected_orders=7 WHERE batch_id=%s", (self.args["batch_id"],))
        self.assertEqual(self.read()["reasons"], ["duplicate_or_invalid_revision"])
        self.owner.execute("UPDATE planning_input.order_versions SET revision=2, warehouse_id=%s WHERE row_id=%s",
                           (self.prefix + ":b", self.prefix + ":duplicate"))
        self.assertEqual(self.read()["reasons"], ["changed_order_identity"])
        self.assertEqual(self.read(batch_id="absent")["reasons"], ["missing_batch"])
        self.assertIn("unknown_reference_or_unit", self.read(sku_id="absent")["reasons"])

    def test_business_calendar_dst_and_unfinished_day(self):
        self.assertEqual(midnight(date(2026, 3, 8)), datetime(2026, 3, 8, 8, tzinfo=timezone.utc))
        self.assertEqual(midnight(date(2026, 3, 9)) - midnight(date(2026, 3, 8)), timedelta(hours=23))
        self.assertEqual(midnight(date(2026, 11, 2)) - midnight(date(2026, 11, 1)), timedelta(hours=25))
        unfinished = self.read(known_at=ORIGIN - timedelta(microseconds=1))
        self.assertIn("unfinished_day", unfinished["days"][-1]["reasons"])
        # 01:00 UTC Jan 1 is still Dec 31 Pacific.
        self.owner.execute("UPDATE planning_input.order_versions SET accepted_at=%s, source_recorded_at=%s, observed_at=%s WHERE row_id=%s",
                           (datetime(2026, 1, 1, 1, tzinfo=timezone.utc),) * 3 + (self.prefix + ":order:3",))
        self.assertEqual(self.read()["days"][3]["quantity"], 6)

    def test_deterministic_180_day_groups_and_input_permissions(self):
        # Unique Stage 1 scenario is not required; reuse its legitimate existing refs.
        # Scenario clean is loaded by the Stage 1 suite; for focused runs use a distinct
        # source namespace through the existing scenario-data helper.
        from synthetic.generate import _scenario_data
        from psycopg import sql
        data, _ = _scenario_data("clean")
        source = self.prefix + ":source"
        for table in ("styles", "skus", "warehouses"):
            for original in data[table]:
                row = {k: (v.replace("clean:", source + ":") if isinstance(v, str) else v) for k, v in original.items()}
                self.owner.execute(sql.SQL("INSERT INTO operational_fixture.{} ({}) VALUES ({})").format(
                    sql.Identifier(table), sql.SQL(",").join(map(sql.Identifier, row)),
                    sql.SQL(",").join(sql.Placeholder() for _ in row)), tuple(row.values()))
        fixture = load_demand(self.owner, batch_id=self.prefix + ":180", source_prefix=source)
        for group, expected in zip(fixture["groups"], ([4]*180, [1,2,3,4,5,6,7]*25+[1,2,3,4,5],
                                    [0,0,0,0,0,0,7]*25+[0]*5, [0]*180, None)):
            result = self.read(batch_id=fixture["batch_id"], sku_id=group["sku_id"], warehouse_id=group["warehouse_id"],
                               start_day=fixture["start_day"], end_day=END, known_at=midnight(END)+timedelta(days=10))
            if expected is not None:
                self.assertEqual(result["status"], "eligible")
                self.assertEqual([d["quantity"] for d in result["days"]], expected)
            else:
                self.assertEqual(result["status"], "not_assessable")
                self.assertIn("duplicate_or_invalid_revision", result["reasons"])
        with self.assertRaises(psycopg.errors.UniqueViolation):
            load_demand(self.owner, batch_id=fixture["batch_id"], source_prefix=source)
        for table in ("demand_batches", "order_versions", "day_observations"):
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                self.runner.execute(sql.SQL("DELETE FROM planning_input.{} WHERE false").format(sql.Identifier(table)))
