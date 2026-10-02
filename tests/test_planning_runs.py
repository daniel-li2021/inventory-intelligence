"""Manual forecast/backtest, knowledge-time, holdout and persistence oracles."""

from datetime import timedelta
import os
import unittest
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row

from inventory_intelligence.demand import midnight
from inventory_intelligence.planning_runs import run_forecast, run_benchmark
from tests.planning_oracle import manual_demand, put, START


class PlanningRuns(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.owner = psycopg.connect(os.environ["TEST_DATABASE_URL"], autocommit=True, row_factory=dict_row)
        cls.runner = psycopg.connect(os.environ["DATABASE_URL"], autocommit=True, row_factory=dict_row)
        cls.addClassCleanup(cls.owner.close)
        cls.addClassCleanup(cls.runner.close)

    def setUp(self):
        self.prefix = "runs:" + str(uuid4())
        _, series = manual_demand(self.owner, self.prefix, values=[1,2,3,4,5,6,7]*12)
        self.args = {k: series[k] for k in ("batch_id", "sku_id", "warehouse_id", "start_day")}
        self.forecast_args = self.args | dict(origin_day=START+timedelta(days=28), method="mean", horizon=7)
        self.benchmark_args = self.args | dict(group="weekly", end_day=series["end_day"],
                                              evaluated_at=series["known_at"]+timedelta(days=10))

    def test_forecast_exact_history_and_blocked_result(self):
        a = run_forecast(self.runner, **self.forecast_args)
        b = run_forecast(self.runner, **self.forecast_args)
        self.assertEqual(a["status"], "assessable")
        self.assertEqual(a["result"]["predictions"], ["4"]*7)
        semantic = lambda x: {k:v for k,v in x.items() if k not in ("run_id", "created_at")}
        self.assertEqual(semantic(a), semantic(b))
        self.assertNotEqual(a["run_id"], b["run_id"])
        for report in (a,b):
            saved = self.owner.execute("SELECT * FROM planning.runs WHERE run_id=%s", (report["run_id"],)).fetchone()
            self.assertEqual(saved["result"], report["result"])
            self.assertEqual(saved["context"], report["context"])
            self.assertEqual(saved["input_digest"], report["input_digest"])
        blocked = run_forecast(self.runner, **(self.forecast_args | dict(batch_id="missing")))
        self.assertEqual(blocked["status"], "not_assessable")
        self.assertIsNone(blocked["result"]["predictions"])
        self.assertEqual(self.owner.execute("SELECT result FROM planning.runs WHERE run_id=%s", (a["run_id"],)).fetchone()["result"], a["result"])

    def test_shared_origins_scores_and_temporal_holdout(self):
        r = run_benchmark(self.runner, **self.benchmark_args)["result"]
        self.assertEqual(r["status"], "assessable")
        self.assertEqual([f["origin_day"] for f in r["candidates"]], [(START+timedelta(days=28)).isoformat()])
        self.assertEqual(r["holdout"]["origin_day"], (START+timedelta(days=56)).isoformat())
        self.assertEqual(r["chosen_method"], "seasonal_naive")
        expected = {
            "naive": dict(mae="3", bias="3", wape="3/4"),
            "mean": dict(mae="12/7", bias="0", wape="3/7"),
            "seasonal_naive": dict(mae="0", bias="0", wape="0"),
        }
        for horizon in (7,14,28):
            self.assertEqual(r["selection"][str(horizon)], dict(scored_points=horizon, scores=expected))
            self.assertEqual(r["holdout_scores"][str(horizon)], dict(scored_points=horizon, scores=expected))
        # Corrupt only final truth. Model choice and selection scores must not change.
        self.owner.execute("UPDATE planning_input.order_versions SET accepted_qty=100 WHERE batch_id=%s AND accepted_at >= %s",
                           (self.args["batch_id"], midnight(START+timedelta(days=56))))
        changed = run_benchmark(self.runner, **self.benchmark_args)["result"]
        self.assertEqual(changed["selection"], r["selection"])
        self.assertEqual(changed["chosen_method"], "seasonal_naive")
        self.assertNotEqual(changed["holdout_scores"], r["holdout_scores"])

    def test_late_revision_replayed_at_each_origin_not_present_day(self):
        before = run_benchmark(self.runner, **self.benchmark_args)["result"]
        row = self.owner.execute("SELECT * FROM planning_input.order_versions WHERE row_id=%s", (self.prefix+":order:0",)).fetchone()
        put(self.owner, "order_versions", **(dict(row) | dict(row_id=self.prefix+":late", revision=2,
            accepted_qty=700, source_recorded_at=midnight(START+timedelta(days=40)),
            observed_at=midnight(START+timedelta(days=45)))))
        self.owner.execute("UPDATE planning_input.demand_batches SET expected_orders=85 WHERE batch_id=%s", (self.args["batch_id"],))
        after = run_benchmark(self.runner, **self.benchmark_args)["result"]
        self.assertEqual(after["candidates"][0]["predictions"], before["candidates"][0]["predictions"])
        self.assertEqual(after["candidates"][0]["training"]["days"][0]["quantity"], 1)
        self.assertEqual(after["holdout"]["training"]["days"][0]["quantity"], 700)
        self.assertEqual(after["holdout"]["predictions"]["mean"], ["923/56"]*28)

    def test_common_exclusion_zero_wape_and_no_selection(self):
        # A gap in the longest truth horizon removes this origin for ALL horizons.
        self.owner.execute("UPDATE planning_input.day_observations SET availability='stockout' WHERE row_id=%s", (self.prefix+":day:50",))
        r = run_benchmark(self.runner, **self.benchmark_args)["result"]
        self.assertEqual(r["status"], "not_assessable")
        self.assertIsNone(r["chosen_method"])
        for h in ("7","14","28"):
            self.assertEqual(r["selection"][h], dict(scored_points=0, scores=None))
        # Explicitly counted accepted zero-quantity order lines are valid too.
        self.owner.execute("UPDATE planning_input.day_observations SET availability='available' WHERE row_id=%s", (self.prefix+":day:50",))
        self.owner.execute("UPDATE planning_input.order_versions SET accepted_qty=0 WHERE batch_id=%s", (self.args["batch_id"],))
        zero = run_benchmark(self.runner, **self.benchmark_args)["result"]
        self.assertEqual(zero["chosen_method"], "naive")
        self.assertEqual(zero["selection"]["28"]["scores"]["mean"], dict(mae="0", bias="0", wape=None))

    def test_selection_truth_cannot_use_revisions_learned_during_holdout(self):
        before = run_benchmark(self.runner, **self.benchmark_args)["result"]
        row = self.owner.execute("SELECT * FROM planning_input.order_versions WHERE row_id=%s",
                                 (self.prefix+":order:41",)).fetchone()
        put(self.owner, "order_versions", **(dict(row) | dict(row_id=self.prefix+":holdout-revision",
            revision=2, accepted_qty=700,
            source_recorded_at=midnight(START+timedelta(days=60)),
            observed_at=midnight(START+timedelta(days=60)))))
        self.owner.execute("UPDATE planning_input.demand_batches SET expected_orders=85 WHERE batch_id=%s",
                           (self.args["batch_id"],))
        after = run_benchmark(self.runner, **self.benchmark_args)["result"]
        self.assertEqual(after["selection"], before["selection"])
        self.assertEqual(after["chosen_method"], before["chosen_method"])
        self.assertEqual(after["candidates"][0]["truth"]["days"][13]["quantity"], 7)
        self.assertEqual(after["holdout"]["predictions"], before["holdout"]["predictions"])
        self.assertEqual(after["holdout"]["training"]["order_versions"],
                         before["holdout"]["training"]["order_versions"])

    def test_atomic_failure_and_append_only_role(self):
        before = self.owner.execute("SELECT count(*) AS n FROM planning.runs").fetchone()["n"]
        self.owner.execute("ALTER TABLE planning.runs ADD CONSTRAINT reject_test CHECK (kind <> 'forecast') NOT VALID")
        try:
            with self.assertRaises(psycopg.errors.CheckViolation):
                run_forecast(self.runner, **self.forecast_args)
            self.assertEqual(self.owner.execute("SELECT count(*) AS n FROM planning.runs").fetchone()["n"], before)
        finally:
            self.owner.execute("ALTER TABLE planning.runs DROP CONSTRAINT reject_test")
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            self.runner.execute("UPDATE planning.runs SET status='assessable' WHERE false")
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            self.runner.execute("DELETE FROM planning.runs WHERE false")
        for kwargs in (dict(horizon=0), dict(horizon=True), dict(method="unknown")):
            with self.assertRaises(ValueError):
                run_forecast(self.runner, **(self.forecast_args | kwargs))
