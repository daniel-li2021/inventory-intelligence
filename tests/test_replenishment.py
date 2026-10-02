"""Independent full-path inventory/proposal oracles, not count-only acceptance."""

from datetime import timedelta
import os
import unittest
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from inventory_intelligence.replenishment import run_plan
from tests.planning_oracle import manual_plan, put
from inventory_intelligence.demand import midnight


class Replenishment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.owner = psycopg.connect(os.environ["TEST_DATABASE_URL"], autocommit=True, row_factory=dict_row)
        cls.runner = psycopg.connect(os.environ["DATABASE_URL"], autocommit=True, row_factory=dict_row)
        cls.addClassCleanup(cls.owner.close)
        cls.addClassCleanup(cls.runner.close)

    def setUp(self):
        self.prefix = "plan:"+str(uuid4())
        self.args = manual_plan(self.owner, self.runner, self.prefix)

    def plan(self, **overrides):
        return run_plan(self.runner, **(self.args | overrides))

    def test_exact_manual_projection_order_and_immutable_inputs(self):
        def inputs():
            return {t:self.owner.execute(sql.SQL("SELECT jsonb_agg(to_jsonb(t) ORDER BY row_id) AS rows FROM planning_input.{} t WHERE batch_id=%s")
                    .format(sql.Identifier(t)), (self.args["supply_batch_id"],)).fetchone()["rows"]
                    for t in ("policies","inbound","reservations")}
        before = inputs()
        report = self.plan()
        r = report["result"]
        self.assertEqual(r["status"], "assessable")
        self.assertEqual(r["inventory"]["on_hand"], 10)
        self.assertEqual(r["forecast"]["predictions"], ["4"]*5)
        self.assertEqual([d["balance_without_order"] for d in r["projection"]], ["3","4","0","-4","-8"])
        self.assertEqual([d["balance_with_order"] for d in r["projection"]], ["3","4","12","8","4"])
        self.assertEqual([d["inbound"] for d in r["projection"]], [0,5,0,0,0])
        self.assertEqual([d["reservations"] for d in r["projection"]], [3,0,0,0,0])
        self.assertEqual((r["unrounded_need"],r["whole_piece_need"],r["proposed_order_qty"],r["rounding_extra"]), ("10",10,12,2))
        self.assertEqual(r["inventory_position"],12)
        self.assertEqual(r["end_projected_balance"],"-8")
        self.assertEqual(r["order_arrival_day"],(self.args["origin_day"]+timedelta(days=2)).isoformat())
        self.assertEqual(r["pre_arrival_shortage_days"],[])
        self.assertEqual(inputs(), before)
        other = self.plan()
        semantic = lambda x:{k:v for k,v in x.items() if k not in ("run_id","created_at")}
        self.assertEqual(semantic(report),semantic(other))
        self.assertNotEqual(report["run_id"],other["run_id"])
        self.assertEqual(self.owner.execute("SELECT result FROM planning.runs WHERE run_id=%s", (report["run_id"],)).fetchone()["result"],r)

    def test_late_inbound_does_not_mask_prefix_shortage(self):
        self.owner.execute("UPDATE planning_input.inbound SET remaining_qty=100, arrival_day=%s WHERE row_id=%s",
                           (self.args["origin_day"]+timedelta(days=4),self.prefix+":confirmed"))
        r=self.plan()["result"]
        # Without order [3,-1,-5,-9,87]; final surplus does not cover day 3.
        self.assertEqual([d["balance_without_order"] for d in r["projection"]], ["3","-1","-5","-9","87"])
        self.assertEqual(r["end_projected_balance"],"87")
        self.assertEqual(r["unrounded_need"],"11")
        self.assertEqual(r["proposed_order_qty"],12)
        self.assertEqual(r["pre_arrival_shortage_days"],[(self.args["origin_day"]+timedelta(days=1)).isoformat()])
        self.assertEqual([d["balance_with_order"] for d in r["projection"]], ["3","-1","7","3","99"])

    def test_fraction_ceiling_zero_moq_and_exact_big_pieces(self):
        # Keep counted accepted lines but use 14 zeros/14 ones => forecast 1/2.
        for i in range(28):
            self.owner.execute("UPDATE planning_input.order_versions SET accepted_qty=%s WHERE row_id=%s", (i%2,self.prefix+f":order:{i}"))
        self.owner.execute("UPDATE planning_input.policies SET safety_qty=14, pack_size=1, moq=1 WHERE batch_id=%s", (self.args["supply_batch_id"],))
        r=self.plan()["result"]
        # End balance 10+5-3-5/2=19/2, safety14 => 9/2 pieces => 5.
        self.assertEqual(r["end_projected_balance"],"19/2")
        self.assertEqual((r["unrounded_need"],r["whole_piece_need"],r["proposed_order_qty"]), ("9/2",5,5))
        self.owner.execute("UPDATE planning_input.policies SET moq=10, pack_size=6 WHERE batch_id=%s",(self.args["supply_batch_id"],))
        self.assertEqual(self.plan()["result"]["proposed_order_qty"],12)
        self.owner.execute("UPDATE planning_input.order_versions SET accepted_qty=0 WHERE batch_id=%s",(self.args["batch_id"],))
        self.owner.execute("UPDATE planning_input.policies SET safety_qty=0, moq=100, pack_size=6 WHERE batch_id=%s",(self.args["supply_batch_id"],))
        zero=self.plan()["result"]
        self.assertEqual((zero["proposed_order_qty"],zero["unrounded_need"]),(0,"0"))
        self.owner.execute("UPDATE planning_input.order_versions SET accepted_qty=%s WHERE batch_id=%s",(2**53+1,self.args["batch_id"],))
        huge=self.plan()["result"]
        # 5*(2^53+1)-12, rounded to the next multiple of six, all integer arithmetic.
        self.assertEqual(huge["whole_piece_need"],45035996273704953)
        self.assertEqual(huge["proposed_order_qty"],45035996273704956)

    def test_completeness_policy_and_time_gates_have_no_recommendation(self):
        origin=midnight(self.args["origin_day"])
        cases = (
            ("supply_batches","reservations_complete",False,"batch_id",self.args["supply_batch_id"],"incomplete_or_mismatched_supply"),
            ("supply_batches","inbound_complete",False,"batch_id",self.args["supply_batch_id"],"incomplete_or_mismatched_supply"),
            ("supply_batches","expected_inbound",99,"batch_id",self.args["supply_batch_id"],"incomplete_or_mismatched_supply"),
            ("policies","lead_days",0,"row_id",self.prefix+":policy","missing_or_invalid_policy"),
            ("policies","lead_days",367,"row_id",self.prefix+":policy","missing_or_invalid_policy"),
            ("inbound","observed_at",origin+timedelta(microseconds=1),"row_id",self.prefix+":confirmed","supply_not_known_at_origin"),
            ("inbound","remaining_qty",-1,"row_id",self.prefix+":confirmed","invalid_inbound"),
            ("inbound","arrival_day",self.args["origin_day"]-timedelta(days=1),"row_id",self.prefix+":confirmed","overdue_inbound"),
            ("reservations","due_day",self.args["origin_day"]-timedelta(days=1),"row_id",self.prefix+":reservation","overdue_reservations"),
        )
        for table,field,value,key,ident,reason in cases:
            with self.subTest(table=table,field=field):
                original=self.owner.execute(sql.SQL("SELECT {} FROM planning_input.{} WHERE {}=%s").format(sql.Identifier(field),sql.Identifier(table),sql.Identifier(key)),(ident,)).fetchone()[field]
                self.owner.execute(sql.SQL("UPDATE planning_input.{} SET {}=%s WHERE {}=%s").format(sql.Identifier(table),sql.Identifier(field),sql.Identifier(key)),(value,ident))
                try:
                    r=self.plan()["result"]
                    self.assertEqual(r["status"],"not_assessable")
                    self.assertIsNone(r["proposed_order_qty"])
                    self.assertIsNone(r["projection"])
                    self.assertIn(reason,r["reasons"])
                finally:
                    self.owner.execute(sql.SQL("UPDATE planning_input.{} SET {}=%s WHERE {}=%s").format(sql.Identifier(table),sql.Identifier(field),sql.Identifier(key)),(original,ident))
        self.owner.execute("DELETE FROM planning_input.policies WHERE batch_id=%s",(self.args["supply_batch_id"],))
        self.assertIn("missing_or_invalid_policy",self.plan()["result"]["reasons"])
        self.assertIsNone(self.plan(supply_batch_id="absent")["result"]["proposed_order_qty"])

    def test_stage1_run_coverage_freshness_and_revalidation(self):
        # Source mutation after a stored pass must not silently become trusted stock.
        self.owner.execute("UPDATE operational_fixture.snapshots SET on_hand_qty=11 WHERE row_id=%s",(self.prefix+":snapshot:shirt:a",))
        r=self.plan()["result"]
        self.assertIn("current_inventory_revalidation_failed",r["reasons"])
        self.assertIsNone(r["proposed_order_qty"])
        self.owner.execute("UPDATE operational_fixture.snapshots SET on_hand_qty=10 WHERE row_id=%s",(self.prefix+":snapshot:shirt:a",))
        origin=midnight(self.args["origin_day"])
        for field,value in (("as_of",origin-timedelta(days=2)),("evaluated_at",origin+timedelta(microseconds=1)),("overall_status","fail")):
            with self.subTest(field=field):
                original=self.owner.execute(sql.SQL("SELECT {} FROM reliability.runs WHERE run_id=%s").format(sql.Identifier(field)),(self.args["reliability_run_id"],)).fetchone()[field]
                self.owner.execute(sql.SQL("UPDATE reliability.runs SET {}=%s WHERE run_id=%s").format(sql.Identifier(field)),(value,self.args["reliability_run_id"]))
                self.assertIsNone(self.plan()["result"]["proposed_order_qty"])
                self.owner.execute(sql.SQL("UPDATE reliability.runs SET {}=%s WHERE run_id=%s").format(sql.Identifier(field)),(original,self.args["reliability_run_id"]))
        self.assertIsNone(self.plan(reliability_run_id=str(uuid4()))["result"]["proposed_order_qty"])
        self.owner.execute("UPDATE operational_fixture.snapshots SET observed_at=%s WHERE row_id=%s",(origin+timedelta(microseconds=1),self.prefix+":snapshot:shirt:a"))
        self.assertIn("inventory_not_known_at_origin",self.plan()["result"]["reasons"])

    def test_duplicate_supply_and_stockout_block_while_preserving_history(self):
        passed=self.plan()
        row=self.owner.execute("SELECT * FROM planning_input.inbound WHERE row_id=%s",(self.prefix+":confirmed",)).fetchone()
        put(self.owner,"inbound",**(dict(row)|dict(row_id=self.prefix+":duplicate")))
        self.owner.execute("UPDATE planning_input.supply_batches SET expected_inbound=5 WHERE batch_id=%s",(self.args["supply_batch_id"],))
        self.assertIn("duplicate_inbound",self.plan()["result"]["reasons"])
        self.owner.execute("DELETE FROM planning_input.inbound WHERE row_id=%s",(self.prefix+":duplicate",))
        self.owner.execute("UPDATE planning_input.supply_batches SET expected_inbound=4 WHERE batch_id=%s",(self.args["supply_batch_id"],))
        self.owner.execute("UPDATE planning_input.day_observations SET availability='stockout' WHERE row_id=%s",(self.prefix+":day:0",))
        self.assertIsNone(self.plan()["result"]["proposed_order_qty"])
        self.assertEqual(self.owner.execute("SELECT result FROM planning.runs WHERE run_id=%s",(passed["run_id"],)).fetchone()["result"],passed["result"])
        for table in ("supply_batches","policies","reservations","inbound"):
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                self.runner.execute(sql.SQL("DELETE FROM planning_input.{} WHERE false").format(sql.Identifier(table)))

    def test_synthetic_demo_downstream_benchmark_and_both_supply_outcomes(self):
        from synthetic.planning_demo import run_demo
        demo=run_demo(self.owner,self.runner)
        self.assertEqual([(r["group"],r["status"],r["chosen_method"],r["included_origins"],r["excluded_origins"])
                          for r in demo["benchmarks"]], [
            ("constant","assessable","naive",14,0),
            ("weekly","assessable","seasonal_naive",14,0),
            ("intermittent","assessable","seasonal_naive",14,0),
            ("zero","assessable","naive",14,0),
            ("blocked","not_assessable",None,0,14),
        ])
        self.assertEqual(demo["benchmarks"][1]["selection"]["28"]["scores"]["mean"],
                         dict(mae="12/7",bias="0",wape="3/7"))
        self.assertEqual(demo["benchmarks"][3]["selection"]["28"]["scores"]["mean"],
                         dict(mae="0",bias="0",wape=None))
        self.assertEqual([(p["status"],p["proposed_order_qty"]) for p in demo["proposals"]],
                         [("assessable",12),("not_assessable",None)])
        self.assertEqual([str(d["balance_without_order"]) for d in demo["proposals"][0]["projection"]],
                         ["3","4","0","-4","-8"])
