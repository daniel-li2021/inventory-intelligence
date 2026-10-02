"""Focused real PostgreSQL retrieval checks; use the existing acceptance DB setup."""

import os
from datetime import timedelta
import unittest
from unittest.mock import patch
from uuid import uuid4

import psycopg
from psycopg.pq import TransactionStatus

from inventory_intelligence import copilot
from inventory_intelligence.reliability import run_checks
from tests.golden import load_golden


class CopilotDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.admin = psycopg.connect(os.environ["TEST_DATABASE_URL"], autocommit=True)
        cls.addClassCleanup(cls.admin.close)
        cls.runner = psycopg.connect(os.environ["DATABASE_URL"], autocommit=True)
        cls.addClassCleanup(cls.runner.close)

    def test_exact_persisted_report_readonly_snapshot_and_no_new_history(self):
        prefix = "copilot:" + str(uuid4())
        context = load_golden(self.admin, prefix)
        self.admin.execute("""UPDATE operational_fixture.snapshots SET on_hand_qty = 107
                              WHERE row_id = %s""", (prefix + ":snapshot:shirt:a",))
        expected = run_checks(self.runner, **context, code_version="copilot-oracle")
        self.assertEqual([(f["rule_id"], f["reason"], f["expected_qty"], f["observed_qty"], f["delta_qty"])
                          for f in expected["findings"]], [("R001", "quantity_mismatch", 109, 107, -2)])
        before = self.admin.execute("SELECT count(*) FROM reliability.runs").fetchone()[0]
        validate = copilot._validate_report

        def validate_in_readonly_transaction(report):
            self.assertEqual(self.runner.execute("SHOW transaction_read_only").fetchone()[0], "on")
            self.assertEqual(self.runner.execute("SHOW transaction_isolation").fetchone()[0], "repeatable read")
            validate(report)

        with patch.object(copilot, "_validate_report", side_effect=validate_in_readonly_transaction):
            loaded = copilot.load_run(self.runner, expected["run_id"])
        self.assertEqual(loaded, expected)
        first = copilot.answer(intent="finding", report=loaded, finding_id=loaded["findings"][0]["finding_id"])
        self.assertEqual(first["citations"][1]["data"], expected["findings"][0])
        again = copilot.load_run(self.runner, expected["run_id"])
        self.assertEqual(copilot.answer(intent="finding", report=again,
                                       finding_id=again["findings"][0]["finding_id"]), first)
        self.assertEqual(self.admin.execute("SELECT count(*) FROM reliability.runs").fetchone()[0], before)
        self.assertEqual(self.admin.execute("SELECT on_hand_qty FROM operational_fixture.snapshots WHERE row_id = %s",
                                           (prefix + ":snapshot:shirt:a",)).fetchone()[0], 107)
        self.assertEqual(self.runner.info.transaction_status, TransactionStatus.IDLE)

    def test_absent_run_invalid_id_role_and_nonidle_connection(self):
        for run_id in (str(uuid4()), "not-a-uuid", "'; DELETE FROM reliability.runs; --"):
            with self.subTest(run_id=run_id), self.assertRaises(ValueError):
                copilot.load_run(self.runner, run_id)
            self.assertEqual(self.runner.info.transaction_status, TransactionStatus.IDLE)
        with self.assertRaises(ValueError):
            copilot.load_run(self.admin, str(uuid4()))
        with self.runner.transaction():
            with self.assertRaises(ValueError):
                copilot.load_run(self.runner, str(uuid4()))

    def test_engine_future_cutoff_is_explainable_failed_evidence(self):
        context = load_golden(self.admin, "copilot:" + str(uuid4()))
        context["evaluated_at"] = context["as_of"] - timedelta(microseconds=1)
        expected = run_checks(self.runner, **context, code_version="copilot-future-oracle")
        self.assertEqual([(f["rule_id"], f["reason"]) for f in expected["findings"]],
                         [("R005", "metadata_mismatch"), ("R005", "metadata_mismatch")])
        loaded = copilot.load_run(self.runner, expected["run_id"])
        self.assertEqual(loaded, expected)
        result = copilot.answer(intent="reliability", report=loaded)
        self.assertEqual(result["status"], "answered")
        self.assertEqual(result["citations"][0]["data"]["overall_status"], "fail")


if __name__ == "__main__":
    unittest.main()
