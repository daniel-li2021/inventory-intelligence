"""Contract-v1 acceptance against a dedicated, already bootstrapped PostgreSQL 17 DB.

Missing dependencies, URLs, schema, or database are errors, never skipped passes.
"""

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from datetime import timedelta
from uuid import UUID, uuid4

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from inventory_intelligence.reliability import run_checks
from tests.golden import BASELINE, CUTOFF, EXPECTED, insert, load_golden

ROOT = Path(__file__).resolve().parents[1]
RULES = [f"R00{i}" for i in range(1, 6)]


class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.admin = psycopg.connect(os.environ["TEST_DATABASE_URL"], autocommit=True,
                                   row_factory=dict_row)
        cls.runner = psycopg.connect(os.environ["DATABASE_URL"], autocommit=True,
                                    row_factory=dict_row)
        version = int(cls.admin.execute("SHOW server_version_num").fetchone()["server_version_num"])
        if not 170000 <= version < 180000:
            raise RuntimeError(f"Acceptance requires PostgreSQL 17, got {version}")
        if cls.runner.execute("SELECT current_user AS name").fetchone()["name"] != "ii_runner":
            raise RuntimeError("DATABASE_URL must use the restricted ii_runner role")
        cls.addClassCleanup(cls.admin.close)
        cls.addClassCleanup(cls.runner.close)

    def setUp(self):
        self.prefix = f"acceptance:{uuid4()}"
        self.context = load_golden(self.admin, self.prefix)

    def key(self, name):
        return f"{self.prefix}:{name}"

    def update(self, table, row_id, **fields):
        identifier = "batch_id" if table == "batches" else "row_id"
        self.admin.execute(sql.SQL("UPDATE operational_fixture.{} SET {} WHERE {} = %s").format(
            sql.Identifier(table), sql.SQL(", ").join(
                sql.SQL("{} = %s").format(sql.Identifier(name)) for name in fields),
            sql.Identifier(identifier)), (*fields.values(), self.key(row_id)))

    def clone(self, table, row_id, new_id, **changes):
        row = self.admin.execute(sql.SQL("SELECT * FROM operational_fixture.{} WHERE row_id = %s")
                                 .format(sql.Identifier(table)), (self.key(row_id),)).fetchone()
        insert(self.admin, table, **(row | changes | {"row_id": self.key(new_id)}))

    def recount(self, kind):
        table = "movements" if kind == "ledger" else "snapshots"
        count = self.admin.execute(sql.SQL("SELECT count(*) AS n FROM operational_fixture.{} "
                                          "WHERE batch_id = %s").format(sql.Identifier(table)),
                                   (self.key(kind),)).fetchone()["n"]
        self.update("batches", kind, expected_row_count=count)

    def check(self, **overrides):
        report = run_checks(self.runner, **(self.context | overrides), code_version="acceptance-v1")
        self.assertEqual(set(report), {"run_id", "contract_version", "code_version", "ledger_batch_id",
                                      "snapshot_batch_id", "as_of", "evaluated_at", "overall_status", "checks", "findings"})
        order = [(f["rule_id"], f["reason"], f["sku_id"] or "", f["warehouse_id"] or "",
                  f["source_row_ids"]) for f in report["findings"]]
        self.assertEqual(order, sorted(order))
        for finding in report["findings"]:
            self.assertEqual(set(finding), {"finding_id", "rule_id", "severity", "reason", "sku_id",
                                           "warehouse_id", "source_row_ids", "expected_qty", "observed_qty", "delta_qty", "evidence"})
            self.assertEqual(finding["severity"], "error")
            self.assertEqual(finding["source_row_ids"], sorted(finding["source_row_ids"]))
            if finding["rule_id"] != "R001":
                self.assertEqual((finding["expected_qty"], finding["observed_qty"], finding["delta_qty"]),
                                 (None, None, None))
        return report

    def assert_checks(self, report, *, fail=(), blocked=()):
        self.assertEqual(report["checks"], [dict(rule_id=rule, status=
                         "fail" if rule in fail else "not_assessable" if rule in blocked else "pass")
                         for rule in RULES])
        self.assertEqual(report["overall_status"], "fail" if fail else
                         "not_assessable" if blocked else "pass")

    def expected_finding(self, rule, reason, rows=(), sku=None, wh=None,
                         expected=None, observed=None, delta=None):
        return (rule, reason, self.key(sku) if sku else None, self.key(wh) if wh else None,
                sorted(self.key(row) for row in rows), expected, observed, delta)

    def assert_findings(self, report, expected):
        actual = [(f["rule_id"], f["reason"], f["sku_id"], f["warehouse_id"],
                   f["source_row_ids"], f["expected_qty"], f["observed_qty"], f["delta_qty"])
                  for f in report["findings"]]
        self.assertCountEqual(actual, expected)
        self.assertEqual(len({f["finding_id"] for f in report["findings"]}), len(actual))
        for f in report["findings"]:
            self.assertEqual(f["severity"], "error")
            self.assertIsInstance(f["evidence"], dict)
            self.assertEqual(f["source_row_ids"], sorted(f["source_row_ids"]))
            if f["rule_id"] != "R001":
                self.assertEqual((f["expected_qty"], f["observed_qty"], f["delta_qty"]),
                                 (None, None, None))

    def assert_reasons(self, report, expected, *, fail=(), blocked=()):
        """Manifest evidence layout is not prescribed; rule/reason multiplicity is."""
        self.assertCountEqual([(f["rule_id"], f["reason"]) for f in report["findings"]], expected)
        self.assert_checks(report, fail=fail, blocked=blocked)
        for f in report["findings"]:
            self.assertEqual(f["severity"], "error")
            self.assertEqual((f["expected_qty"], f["observed_qty"], f["delta_qty"]), (None, None, None))

    def test_manual_golden_clean_and_temporal_controls(self):
        report = self.check()
        self.assert_checks(report)
        self.assert_findings(report, [])
        UUID(report["run_id"])
        self.assertEqual(report["contract_version"], "1")
        self.assertEqual(report["code_version"], "acceptance-v1")
        self.assertEqual(report["ledger_batch_id"], self.key("ledger"))
        self.assertEqual(report["snapshot_batch_id"], self.key("snapshot"))
        self.assertEqual(report["as_of"], CUTOFF.isoformat())
        self.assertEqual(report["evaluated_at"], (CUTOFF + timedelta(hours=24)).isoformat())
        # Force arithmetic to be observable, even if an engine accidentally emits no R001 at all.
        for sku, wh in EXPECTED:
            self.update("snapshots", f"snapshot:{sku}:{wh}", on_hand_qty=EXPECTED[sku, wh] + 1)
        report = self.check()
        self.assert_checks(report, fail=("R001",))
        self.assertCountEqual([(f["sku_id"], f["warehouse_id"], f["expected_qty"],
                               f["observed_qty"], f["delta_qty"]) for f in report["findings"]],
                              [(self.key(s), self.key(w), q, q + 1, 1)
                               for (s, w), q in EXPECTED.items()])
        self.assertTrue(all(f["rule_id"] == "R001" and f["reason"] == "quantity_mismatch"
                            for f in report["findings"]))

    def test_exact_quantity_evidence(self):
        self.update("snapshots", "snapshot:shirt:a", on_hand_qty=107)
        report = self.check()
        self.assert_checks(report, fail=("R001",))
        self.assertEqual(len(report["findings"]), 1)
        f = report["findings"][0]
        self.assertEqual((f["rule_id"], f["reason"], f["sku_id"], f["warehouse_id"],
                          f["expected_qty"], f["observed_qty"], f["delta_qty"]),
                         ("R001", "quantity_mismatch", self.key("shirt"), self.key("a"), 109, 107, -2))
        self.assertEqual(f["source_row_ids"], sorted(self.key(n) for n in (
            "snapshot:shirt:a", "opening:shirt:a", "receipt", "shipment", "transfer-out", "reversal", "return")))

    def test_whole_piece_arithmetic_above_float_precision(self):
        opening = 2 ** 53 + 1
        self.update("opening_balances", "opening:coat:a", quantity=opening)
        self.update("snapshots", "snapshot:coat:a", on_hand_qty=opening + 6)
        report = self.check()
        self.assert_checks(report, fail=("R001",))
        f = report["findings"][0]
        self.assertEqual((f["expected_qty"], f["observed_qty"], f["delta_qty"]),
                         (opening + 5, opening + 6, 1))
        self.assertTrue(all(type(f[field]) is int for field in
                            ("expected_qty", "observed_qty", "delta_qty")))

    def test_identical_and_conflicting_duplicates_block_quantity(self):
        for quantity in (10, 99):
            with self.subTest(quantity=quantity):
                self.clone("movements", "receipt", f"duplicate-{quantity}", quantity=quantity)
                self.recount("ledger")
                report = self.check()
                self.assert_checks(report, fail=("R002",), blocked=("R001",))
                duplicates = ["receipt", "duplicate-10"]
                if quantity == 99:
                    duplicates.append("duplicate-99")
                # The whole natural-key group, including every conflicting row, must be exposed.
                self.assert_findings(report, [self.expected_finding(
                    "R002", "duplicate_movement_key", duplicates)])
                records = report["findings"][0]["evidence"]["source_records"]
                self.assertEqual({(r["record"]["sku_id"], r["record"]["warehouse_id"])
                                  for r in records}, {(self.key("shirt"), self.key("a"))})

    def test_unknown_reference_blocks_affected_bucket_only(self):
        self.update("movements", "receipt", sku_id=self.key("unknown"))
        # A known clean bucket with its own defect still produces an assessable quantity finding.
        self.update("snapshots", "snapshot:coat:a", on_hand_qty=14)
        report = self.check()
        self.assert_checks(report, fail=("R001", "R003"))
        self.assert_findings(report, [
            self.expected_finding("R001", "quantity_mismatch",
                                  ["opening:coat:a", "snapshot:coat:a", "line-1", "line-2"],
                                  "coat", "a", 15, 14, -1),
            self.expected_finding("R001", "quantity_mismatch",
                                  ["opening:shirt:a", "snapshot:shirt:a", "shipment",
                                   "transfer-out", "reversal", "return"],
                                  "shirt", "a", 99, 109, 10),
            self.expected_finding("R003", "unknown_reference", ["receipt"], "unknown", "a"),
        ])
        unknown = [f for f in report["findings"] if f["rule_id"] == "R003"]
        self.assertEqual(len(unknown), 1)
        self.assertEqual(unknown[0]["reason"], "unknown_reference")
        self.assertEqual(unknown[0]["source_row_ids"], [self.key("receipt")])
        self.assertIn("sku_id", json.dumps(unknown[0]["evidence"]))
        mismatches = [f for f in report["findings"] if f["rule_id"] == "R001"]
        self.assertTrue(any(f["sku_id"] == self.key("coat") and
                            (f["expected_qty"], f["observed_qty"], f["delta_qty"]) == (15, 14, -1)
                            for f in mismatches))
        # The unknown movement's declared key is unassessable, never a fabricated delta.
        self.assertFalse(any(f["sku_id"] == self.key("unknown") for f in mismatches))

    def test_unknown_opening_and_snapshot_references(self):
        for table, row_id, expected_rule in (("opening_balances", "opening:shirt:a", "R003"),
                                             ("snapshots", "snapshot:shirt:a", "R003")):
            with self.subTest(table=table):
                self.update(table, row_id, warehouse_id=self.key("unknown"))
                report = self.check()
                findings = [f for f in report["findings"] if f["reason"] == "unknown_reference"]
                self.assertEqual([(f["rule_id"], f["source_row_ids"]) for f in findings],
                                 [(expected_rule, [self.key(row_id)])])
                self.assertIn("warehouse_id", json.dumps(findings[0]["evidence"]))
                self.assertFalse(any(f["rule_id"] == "R001" and f["sku_id"] == self.key("shirt")
                                     and f["warehouse_id"] == self.key("a") for f in report["findings"]))
                self.update(table, row_id, warehouse_id=self.key("a"))

    def test_missing_duplicate_and_wrong_baseline_openings(self):
        self.admin.execute("DELETE FROM operational_fixture.opening_balances WHERE row_id = %s",
                           (self.key("opening:shirt:a"),))
        self.clone("opening_balances", "opening:coat:a", "duplicate-opening")
        self.update("opening_balances", "opening:shirt:b", as_of=BASELINE + timedelta(microseconds=1))
        report = self.check()
        self.assert_checks(report, fail=("R003",), blocked=("R001",))
        self.assert_findings(report, [
            self.expected_finding("R003", "missing_opening_balance", [], "shirt", "a"),
            self.expected_finding("R003", "duplicate_opening_balance",
                                  ["opening:coat:a", "duplicate-opening"], "coat", "a"),
            self.expected_finding("R003", "opening_cutoff_mismatch", ["opening:shirt:b"], "shirt", "b"),
        ])

    def test_invalid_transfer_blocks_both_buckets(self):
        self.update("movements", "transfer-in", quantity=4)
        report = self.check()
        self.assert_checks(report, fail=("R004",), blocked=("R001",))
        self.assertEqual(len(report["findings"]), 1)
        f = report["findings"][0]
        self.assertEqual((f["rule_id"], f["reason"], f["source_row_ids"]),
                         ("R004", "invalid_transfer", sorted([self.key("transfer-in"), self.key("transfer-out")])))
        self.assertIn(self.key("transfer"), json.dumps(f["evidence"]))
        self.assertEqual((f["expected_qty"], f["observed_qty"], f["delta_qty"]), (None, None, None))
        self.assertTrue(f["evidence"])

    def test_every_transfer_condition(self):
        for field, value, original in (
            ("sku_id", self.key("coat"), self.key("shirt")),
            ("effective_at", BASELINE + timedelta(hours=3, microseconds=1), BASELINE + timedelta(hours=3)),
            ("source_seq", 4, 3),
            ("warehouse_id", self.key("a"), self.key("b")),
            ("quantity", 0, 5),
        ):
            with self.subTest(field=field):
                self.update("movements", "transfer-in", **{field: value})
                try:
                    report = self.check()
                    transfers = [f for f in report["findings"] if f["rule_id"] == "R004"]
                    self.assertEqual([(f["reason"], f["source_row_ids"]) for f in transfers],
                                     [("invalid_transfer", sorted([self.key("transfer-in"), self.key("transfer-out")]))])
                    # The original source bucket may become assessable when a leg names another key;
                    # all buckets actually named by invalid legs must still suppress R001.
                    buckets = {(self.key("shirt"), self.key("a")),
                               (value if field == "sku_id" else self.key("shirt"),
                                value if field == "warehouse_id" else self.key("b"))}
                    self.assertFalse(any(f["rule_id"] == "R001" and
                                         (f["sku_id"], f["warehouse_id"]) in buckets for f in report["findings"]))
                    self.assertEqual((transfers[0]["expected_qty"], transfers[0]["observed_qty"],
                                      transfers[0]["delta_qty"]), (None, None, None))
                finally:
                    self.update("movements", "transfer-in", **{field: original})

    def test_missing_transfer_leg_and_incomplete_extraction(self):
        self.admin.execute("DELETE FROM operational_fixture.movements WHERE row_id = %s",
                           (self.key("transfer-in"),))
        self.recount("ledger")
        complete = self.check()
        self.assert_checks(complete, fail=("R001", "R004"))
        # Without the absent leg's destination, only the remaining leg's bucket is blocked.
        mismatch = next(f for f in complete["findings"] if f["rule_id"] == "R001")
        self.assertEqual((mismatch["sku_id"], mismatch["warehouse_id"], mismatch["expected_qty"],
                          mismatch["observed_qty"], mismatch["delta_qty"]),
                         (self.key("shirt"), self.key("b"), 20, 25, 5))
        self.assertCountEqual([(f["rule_id"], f["reason"]) for f in complete["findings"]],
                              [("R001", "quantity_mismatch"), ("R004", "invalid_transfer")])
        self.update("batches", "ledger", status="incomplete")
        incomplete = self.check()
        self.assert_reasons(incomplete, [("R005", "incomplete_batch")],
                            fail=("R005",), blocked=("R001", "R002", "R003", "R004"))

    def test_missing_and_duplicate_snapshots(self):
        self.admin.execute("DELETE FROM operational_fixture.snapshots WHERE row_id = %s",
                           (self.key("snapshot:shirt:a"),))
        self.clone("snapshots", "snapshot:coat:a", "duplicate-snapshot")
        self.recount("snapshot")
        report = self.check()
        self.assert_checks(report, fail=("R005",), blocked=("R001",))
        self.assert_findings(report, [
            self.expected_finding("R005", "missing_snapshot", [], "shirt", "a"),
            self.expected_finding("R005", "duplicate_snapshot",
                                  ["snapshot:coat:a", "duplicate-snapshot"], "coat", "a"),
        ])

    def test_staleness_boundary_and_future_snapshot(self):
        self.assert_checks(self.check())  # Exactly 24 hours is fresh.
        stale = self.check(evaluated_at=CUTOFF + timedelta(hours=24, microseconds=1))
        self.assert_reasons(stale, [("R005", "stale_snapshot")], fail=("R005",), blocked=("R001",))
        future = self.check(evaluated_at=CUTOFF - timedelta(microseconds=1))
        self.assert_reasons(future, [("R005", "metadata_mismatch")] * 2,
                            fail=("R005",), blocked=("R001",))

    def test_each_manifest_incomplete_and_count_mismatch(self):
        for kind in ("ledger", "snapshot"):
            for field, value, reason in (("status", "incomplete", "incomplete_batch"),
                                          ("expected_row_count", 999, "count_mismatch")):
                with self.subTest(kind=kind, fault=reason):
                    self.update("batches", kind, **{field: value})
                    try:
                        report = self.check()
                        blocked = ("R001", "R002", "R003", "R004") if kind == "ledger" else (
                            ("R001", "R003") if field == "status" else ("R001",))
                        self.assert_reasons(report, [("R005", reason)], fail=("R005",), blocked=blocked)
                    finally:
                        self.update("batches", kind, status="complete", expected_row_count=12 if kind == "ledger" else 4)

    def test_each_missing_manifest(self):
        for kind in ("ledger", "snapshot"):
            with self.subTest(kind=kind):
                report = self.check(**{f"{kind}_batch_id": self.key("absent")})
                # The surviving manifest declares four keys absent from the other selected input.
                expected = [("R005", "missing_batch"), ("R005", "coverage_mismatch")]
                expected += [("R003", "missing_opening_balance") if kind == "ledger" else
                             ("R005", "missing_snapshot")] * 4
                self.assert_reasons(report, expected,
                                    fail=("R003", "R005") if kind == "ledger" else ("R005",),
                                    blocked=("R001", "R002", "R004") if kind == "ledger"
                                    else ("R001", "R003"))
                absent_rows = [f for f in report["findings"] if f["reason"] in
                               ("missing_opening_balance", "missing_snapshot")]
                self.assertCountEqual([(f["sku_id"], f["warehouse_id"], f["source_row_ids"])
                                       for f in absent_rows],
                                      [(self.key(sku), self.key(wh), []) for sku, wh in EXPECTED])

    def test_manifest_cutoff_watermark_and_snapshot_row_metadata(self):
        for kind in ("ledger", "snapshot"):
            for field, value in (("as_of", CUTOFF + timedelta(microseconds=1)), ("watermark", 9)):
                with self.subTest(kind=kind, field=field):
                    self.update("batches", kind, **{field: value})
                    try:
                        report = self.check()
                        # A mismatching snapshot manifest also disagrees with all unchanged rows.
                        self.assert_reasons(report, [("R005", "metadata_mismatch")], fail=("R005",),
                                            blocked=("R001", "R002", "R003", "R004")
                                            if kind == "ledger" and field == "as_of" else ("R001",))
                    finally:
                        self.update("batches", kind, as_of=CUTOFF, watermark=10)
        self.update("snapshots", "snapshot:shirt:a", as_of=CUTOFF - timedelta(microseconds=1))
        report = self.check()
        self.assert_reasons(report, [("R005", "metadata_mismatch")], fail=("R005",), blocked=("R001",))

    def test_coverage_and_unexpected_snapshot_keys(self):
        self.admin.execute("DELETE FROM operational_fixture.coverage WHERE row_id = %s",
                           (self.key("snapshot:coverage:zero:a"),))
        report = self.check()
        self.assertTrue(any(f["rule_id"] == "R005" and f["reason"] == "coverage_mismatch"
                            for f in report["findings"]))
        self.assert_checks(report, fail=("R005",), blocked=("R001",))
        self.assertFalse(any(f["rule_id"] == "R001" for f in report["findings"]))

    def test_empty_coverage_cannot_pass(self):
        for table in ("coverage", "opening_balances", "movements", "snapshots"):
            self.admin.execute(sql.SQL("DELETE FROM operational_fixture.{} WHERE batch_id IN (%s, %s)")
                               .format(sql.Identifier(table)),
                               (self.key("ledger"), self.key("snapshot")))
        for kind in ("ledger", "snapshot"):
            self.recount(kind)
        report = self.check()
        self.assert_reasons(report, [("R005", "coverage_mismatch")] * 2,
                            fail=("R005",), blocked=("R001",))
        self.assertEqual({f["evidence"]["batch_id"] for f in report["findings"]},
                         {self.key("ledger"), self.key("snapshot")})
        for finding in report["findings"]:
            self.assertEqual(finding["source_row_ids"], [])
            self.assertEqual(finding["evidence"]["problems"], [dict(
                sku_id=None, warehouse_id=None, row_id=None, problem="empty_coverage")])

    def test_uncovered_movement_cannot_escape_reconciliation(self):
        # Both references exist, but coat/b has no declared balance coverage.
        self.clone("movements", "receipt", "uncovered", event_id=self.key("uncovered-event"),
                   sku_id=self.key("coat"), warehouse_id=self.key("b"))
        self.recount("ledger")
        report = self.check()
        self.assert_reasons(report, [("R005", "coverage_mismatch")],
                            fail=("R005",), blocked=("R001",))
        finding = report["findings"][0]
        self.assertEqual(finding["source_row_ids"], [self.key("uncovered")])
        self.assertEqual(finding["evidence"]["problems"], [dict(
            sku_id=self.key("coat"), warehouse_id=self.key("b"),
            row_id=self.key("uncovered"), problem="unexpected_movement_key")])

    def test_repeat_run_history_and_operational_inputs_unchanged(self):
        self.update("snapshots", "snapshot:shirt:a", on_hand_qty=107)
        tables = ("styles", "skus", "warehouses", "batches", "coverage",
                  "opening_balances", "movements", "snapshots")
        def inputs():
            return [self.admin.execute(sql.SQL("SELECT jsonb_agg(to_jsonb(t) ORDER BY to_jsonb(t)::text) "
                                               "AS rows FROM operational_fixture.{} t")
                                       .format(sql.Identifier(table))).fetchone()["rows"] for table in tables]
        before = inputs()
        first, second = self.check(), self.check()
        self.assertNotEqual(first["run_id"], second["run_id"])
        semantic = lambda r: {k: v for k, v in r.items() if k != "run_id"}
        self.assertEqual(semantic(first), semantic(second))
        self.assertEqual(before, inputs())
        for report in (first, second):
            run = self.admin.execute("SELECT * FROM reliability.runs WHERE run_id = %s",
                                     (report["run_id"],)).fetchone()
            self.assertEqual(run["ledger_batch_id"], self.key("ledger"))
            self.assertEqual(run["snapshot_batch_id"], self.key("snapshot"))
            self.assertEqual(run["as_of"], CUTOFF)
            self.assertEqual(run["overall_status"], "fail")
            checks = self.admin.execute("SELECT rule_id, status FROM reliability.check_results "
                                        "WHERE run_id = %s ORDER BY rule_id", (report["run_id"],)).fetchall()
            self.assertEqual(checks, report["checks"])
            findings = self.admin.execute("SELECT * FROM reliability.findings WHERE run_id = %s",
                                          (report["run_id"],)).fetchall()
            self.assertEqual([{k: v for k, v in f.items() if k != "run_id"} for f in findings], report["findings"])

    def test_runtime_role_cannot_mutate_operational_inputs(self):
        for table in ("styles", "skus", "warehouses", "batches", "coverage",
                      "opening_balances", "movements", "snapshots"):
            for statement in ("DELETE FROM {} WHERE false", "TRUNCATE {}"):
                with self.subTest(table=table, statement=statement):
                    with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                        self.runner.execute(sql.SQL(statement).format(sql.Identifier("operational_fixture", table)))
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            self.runner.execute("CREATE TABLE operational_fixture.forbidden (id integer)")
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            self.runner.execute("INSERT INTO operational_fixture.styles VALUES ('forbidden', 'forbidden', 'synthetic')")
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            self.runner.execute("UPDATE operational_fixture.styles SET name = 'forbidden' WHERE false")
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            self.runner.execute("DELETE FROM reliability.runs WHERE false")
        self.assert_checks(self.check())  # A denial must not poison the idle runner connection.

    def test_persistence_failure_rolls_back_the_entire_run(self):
        def history():
            return [self.admin.execute(sql.SQL("SELECT count(*) AS n FROM reliability.{}")
                                       .format(sql.Identifier(t))).fetchone()["n"]
                    for t in ("runs", "check_results", "findings")]
        before = history()
        # Fail after runs and the first two check_results have already been inserted.
        self.admin.execute("ALTER TABLE reliability.check_results ADD CONSTRAINT acceptance_reject "
                           "CHECK (rule_id <> 'R003') NOT VALID")
        try:
            with self.assertRaises(psycopg.errors.CheckViolation):
                self.check()
            self.assertEqual(history(), before)
        finally:
            self.admin.execute("ALTER TABLE reliability.check_results DROP CONSTRAINT acceptance_reject")
        self.assert_checks(self.check())

    def cli(self, format="json", env=None):
        return subprocess.run([sys.executable, "-m", "inventory_intelligence", "--ledger-batch",
                               self.context["ledger_batch_id"], "--snapshot-batch",
                               self.context["snapshot_batch_id"], "--as-of", CUTOFF.isoformat(),
                               "--evaluated-at", self.context["evaluated_at"].isoformat(), "--format", format],
                              cwd=ROOT, env=env, text=True, capture_output=True, timeout=30)

    def test_cli_pass_dirty_markdown_and_configuration_error(self):
        clean = self.cli()
        self.assertEqual(clean.returncode, 0, clean.stderr)
        self.assert_checks(json.loads(clean.stdout))
        self.assertEqual(clean.stderr, "")
        self.update("snapshots", "snapshot:shirt:a", on_hand_qty=107)
        dirty = self.cli()
        self.assertEqual(dirty.returncode, 1, dirty.stderr)
        self.assert_checks(json.loads(dirty.stdout), fail=("R001",))
        markdown = self.cli("markdown")
        self.assertEqual(markdown.returncode, 1, markdown.stderr)
        self.assertIn("quantity_mismatch", markdown.stdout)
        env = dict(os.environ)
        env.pop("DATABASE_URL", None)
        error = self.cli(env=env)
        self.assertEqual(error.returncode, 2)
        self.assertEqual(error.stdout, "")
        self.assertTrue(error.stderr)


    def test_named_scenarios(self):
        from synthetic.generate import load_scenario
        for name, failed, blocked in (
            ("clean", (), ()),
            ("quantity_mismatch", ("R001",), ()),
            ("duplicate_movement", ("R002",), ("R001",)),
            ("unknown_reference", ("R003",), ("R001",)),
            ("invalid_transfer", ("R004",), ("R001",)),
            ("stale_snapshot", ("R005",), ("R001",)),
            ("missing_snapshot", ("R005",), ("R001",)),
            ("combined", ("R001", "R002", "R004"), ()),
        ):
            with self.subTest(scenario=name):
                self.prefix = name
                self.context = load_scenario(self.admin, name)
                report = self.check()
                self.assert_checks(report, fail=failed, blocked=blocked)
                expected = []
                if name in ("quantity_mismatch", "combined"):
                    expected.append(("R001", "quantity_mismatch"))
                    f = next(f for f in report["findings"] if f["rule_id"] == "R001")
                    self.assertEqual((f["sku_id"], f["warehouse_id"], f["expected_qty"],
                                      f["observed_qty"], f["delta_qty"]),
                                     (self.key("jacket-m"), self.key("harbor"), 25, 26, 1))
                    self.assertEqual(f["source_row_ids"], sorted(self.key(row) for row in
                                     ("opening:jacket-m:harbor", "movement:adjustment-jacket",
                                      "snapshot:jacket-m:harbor")))
                if name in ("duplicate_movement", "combined"):
                    expected.append(("R002", "duplicate_movement_key"))
                    f = next(f for f in report["findings"] if f["rule_id"] == "R002")
                    self.assertEqual((f["sku_id"], f["warehouse_id"], f["source_row_ids"]),
                                     (None, None, sorted(self.key(row) for row in
                                      ("movement:receipt-hoodie", "movement:receipt-hoodie-copy"))))
                    self.assertEqual({(r["record"]["sku_id"], r["record"]["warehouse_id"])
                                      for r in f["evidence"]["source_records"]},
                                     {(self.key("hoodie-l"), self.key("harbor"))})
                if name in ("invalid_transfer", "combined"):
                    expected.append(("R004", "invalid_transfer"))
                    f = next(f for f in report["findings"] if f["rule_id"] == "R004")
                    self.assertEqual(f["source_row_ids"], sorted(self.key(row) for row in
                                     ("movement:transfer-in", "movement:transfer-out")))
                    self.assertIn(self.key("transfer-001"), str(f["evidence"]))
                if name == "unknown_reference":
                    expected.append(("R003", "unknown_reference"))
                    f = report["findings"][0]
                    self.assertEqual((f["sku_id"], f["warehouse_id"], f["source_row_ids"]),
                                     (self.key("unknown-sku"), self.key("harbor"), [self.key("movement:unknown-sku")]))
                    self.assertIn("sku_id", str(f["evidence"]))
                if name == "stale_snapshot":
                    expected.append(("R005", "stale_snapshot"))
                if name == "missing_snapshot":
                    expected.append(("R005", "missing_snapshot"))
                    self.assertEqual((report["findings"][0]["sku_id"], report["findings"][0]["warehouse_id"],
                                      report["findings"][0]["source_row_ids"]),
                                     (self.key("tee-l"), self.key("harbor"), []))
                self.assertCountEqual([(f["rule_id"], f["reason"]) for f in report["findings"]], expected)
                for f in report["findings"]:
                    self.assertEqual(f["severity"], "error")
                    if f["rule_id"] != "R001":
                        self.assertEqual((f["expected_qty"], f["observed_qty"], f["delta_qty"]),
                                         (None, None, None))
                with self.assertRaises(ValueError):
                    load_scenario(self.admin, name)
                repeated = self.check()
                self.assertNotEqual(report["run_id"], repeated["run_id"])
                self.assertEqual({k: v for k, v in report.items() if k != "run_id"},
                                 {k: v for k, v in repeated.items() if k != "run_id"})


if __name__ == "__main__":
    unittest.main()
