"""Small local orchestration check; independent PostgreSQL acceptance is separate.

Run with: python -m inventory_intelligence.selfcheck
"""

from copy import deepcopy
from datetime import datetime, timezone
import json
import os
import unittest

import psycopg

from .__main__ import _timestamp, markdown
from .reliability import _finish_report, _sql, _utc, run_checks


class ReportCheck(unittest.TestCase):
    def test_outcomes_and_stability(self):
        checks = [{"rule_id": f"R00{i}", "status": "pass"} for i in range(1, 6)]
        finding = dict(rule_id="R001", reason="quantity_mismatch", sku_id="sku", warehouse_id="wh",
                       source_row_ids=["z", "a"], expected_qty=9007199254740993,
                       observed_qty=9007199254740992, delta_qty=-1, evidence={})
        result = _finish_report(dict(checks=deepcopy(checks), findings=[]))
        self.assertEqual(result["overall_status"], "pass")
        checks[0]["status"] = "not_assessable"
        result = _finish_report(dict(checks=deepcopy(checks), findings=[]))
        self.assertEqual(result["overall_status"], "not_assessable")
        checks[0]["status"] = "fail"
        result = _finish_report(dict(checks=deepcopy(checks), findings=[deepcopy(finding)]))
        again = _finish_report(dict(checks=list(reversed(deepcopy(checks))), findings=[deepcopy(finding)]))
        self.assertEqual(result, again)
        self.assertEqual(result["overall_status"], "fail")
        self.assertEqual(result["findings"][0]["source_row_ids"], ["a", "z"])
        result.update(run_id="test", ledger_batch_id="ledger", snapshot_batch_id="snapshot",
                      as_of="cutoff", evaluated_at="evaluation")
        self.assertIn('"expected_qty": 9007199254740993', markdown(result))

    def test_timestamps_and_sql_assets(self):
        timestamp = datetime(2026, 10, 2, tzinfo=timezone.utc)
        self.assertEqual(_timestamp("2026-10-01T17:00:00-07:00"), timestamp)
        self.assertEqual(_utc(timestamp), "2026-10-02T00:00:00+00:00")
        with self.assertRaises(ValueError):
            _utc(timestamp.replace(tzinfo=None))
        query = _sql()
        self.assertIn("WITH", query)
        self.assertIn("'R005'", query)

    @unittest.skipUnless(os.environ.get("ENGINE_CLEAN_CONTEXT"), "no preloaded clean database context")
    def test_preloaded_clean_database(self):
        context = json.loads(os.environ["ENGINE_CLEAN_CONTEXT"])
        for name in ("as_of", "evaluated_at"):
            context[name] = _timestamp(context[name])
        with psycopg.connect(os.environ["DATABASE_URL"], autocommit=True) as conn:
            first = run_checks(conn, **context)
            second = run_checks(conn, **context)
            expected = [{"rule_id": f"R00{i}", "status": "pass"} for i in range(1, 6)]
            self.assertEqual(first["checks"], expected)
            self.assertEqual(first["findings"], [])
            self.assertEqual(first["overall_status"], "pass")
            self.assertNotEqual(first["run_id"], second["run_id"])
            self.assertEqual({k: v for k, v in first.items() if k != "run_id"},
                             {k: v for k, v in second.items() if k != "run_id"})
            persisted = conn.execute("""
                SELECT rule_id, status FROM reliability.check_results
                WHERE run_id = %s ORDER BY rule_id
            """, (first["run_id"],)).fetchall()
            self.assertEqual(persisted, [(c["rule_id"], c["status"]) for c in expected])


if __name__ == "__main__":
    unittest.main()
