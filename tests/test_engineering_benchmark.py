"""Hand arithmetic, source containment and frozen fixture/runner smoke."""
import os
import unittest
from uuid import uuid4

import psycopg

from scripts.engineering_fixtures import (CUTOFF, ORIGIN, ORIGIN_DAY, START,
    inventory_manifest, load_inventory, load_demand, load_supply, source_digest,
    verify_inventory)
from inventory_intelligence.reliability import run_checks
from inventory_intelligence.planning_runs import run_forecast
from inventory_intelligence.replenishment import run_plan


class EngineeringPilot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.owner=psycopg.connect(os.environ["TEST_DATABASE_URL"],autocommit=True)
        cls.runner=psycopg.connect(os.environ["DATABASE_URL"],autocommit=True)
        cls.addClassCleanup(cls.owner.close); cls.addClassCleanup(cls.runner.close)

    def fixture(self,shape="uniform",defects=0,warehouses=1):
        p="pilot-test-"+str(uuid4())
        m=inventory_manifest(p,2,200,shape=shape,defect_rows=defects,warehouses=warehouses)
        load_inventory(self.owner,m)
        return p,m

    def check(self,p,m):
        return run_checks(self.runner,ledger_batch_id=p+":ledger",snapshot_batch_id=p+":snapshot",
            as_of=CUTOFF,evaluated_at=CUTOFF)

    def test_every_quantity_clean_control_and_immutable_repeat(self):
        p,m=self.fixture()
        before=source_digest(self.owner)
        verify_inventory(self.check(p,m),m)
        verify_inventory(self.check(p,m),m)
        self.assertEqual(source_digest(self.owner),before)
        self.owner.execute("UPDATE operational_fixture.snapshots SET on_hand_qty=on_hand_qty+1 WHERE batch_id=%s",(p+":snapshot",))
        findings=self.check(p,m)["findings"]
        self.assertEqual([(f["rule_id"],f["reason"],f["sku_id"],f["expected_qty"],f["observed_qty"],f["delta_qty"])
            for f in findings],[("R001","quantity_mismatch",f"{p}:sku:{k}",1100,1101,1) for k in range(2)])
        for f in findings: self.assertEqual(len(f["source_row_ids"]),102)

    def test_exact_disjoint_exclusions_and_transfer_pair_quantities(self):
        for shape,wh,expected in (("exclusions",1,[1085,1085]),("transfer",2,[1020,1140])):
            p,m=self.fixture(shape,warehouses=wh)
            verify_inventory(self.check(p,m),m)
            self.owner.execute("UPDATE operational_fixture.snapshots SET on_hand_qty=on_hand_qty+1 WHERE batch_id=%s",(p+":snapshot",))
            findings=self.check(p,m)["findings"]
            self.assertEqual([f["expected_qty"] for f in findings],expected)
            self.assertEqual([f["delta_qty"] for f in findings],[1,1])
        skew=inventory_manifest("skew",1000,100000,shape="skew")
        self.assertEqual(skew["counts"][:10],[8000]*10)
        self.assertEqual(skew["counts"][10:210],[21]*200)
        self.assertEqual(skew["counts"][210:],[20]*790)

    def test_duplicate_exact_groups_and_cross_batch_scope(self):
        p,m=self.fixture(defects=4)
        report=self.check(p,m)
        verify_inventory(report,m)
        self.assertEqual([f["source_row_ids"] for f in report["findings"]],
            [[p+":m:0",p+":m:1"],[p+":m:2",p+":m:3"]])
        other=inventory_manifest(p+"-other",2,200,defect_rows=4)
        load_inventory(self.owner,other,natural_prefix=p)
        self.assertEqual(self.check(p,m)["findings"],report["findings"])

    def test_demand_clocks_mean_and_independent_daily_plan(self):
        p="pilot-demand-"+str(uuid4())
        m=inventory_manifest(p,10,0,opening=20,cutoff=ORIGIN)
        load_inventory(self.owner,m); load_demand(self.owner,p,10)
        for h in (7,28,90): load_supply(self.owner,p,10,h)
        checked=run_checks(self.runner,ledger_batch_id=p+":ledger",snapshot_batch_id=p+":snapshot",
            as_of=ORIGIN,evaluated_at=ORIGIN)
        self.assertEqual(self.owner.execute("SELECT count(*) FROM planning_input.order_versions WHERE batch_id=%s",(p+":demand",)).fetchone()[0],1335)
        args=dict(batch_id=p+":demand",sku_id=p+":sku:0",warehouse_id=p+":wh:0",
            start_day=START,origin_day=ORIGIN_DAY,method="mean")
        before=source_digest(self.owner)
        for h,order,need in ((7,30,"29"),(28,180,"176"),(90,612,"610")):
            r=run_forecast(self.runner,**args,horizon=h)
            self.assertEqual(r["result"]["predictions"],["7"]*h)
            self.assertEqual([d["quantity"] for d in r["result"]["training"]["days"]],([0]*3+[10]*7)*18)
            planned=run_plan(self.runner,**args,reliability_run_id=checked["run_id"],supply_batch_id=f"{p}:supply:{h}:0")["result"]
            self.assertEqual(planned["proposed_order_qty"],order)
            self.assertEqual(planned["unrounded_need"],need)
            self.assertEqual([d["balance_without_order"] for d in planned["projection"]],list(map(str,[10,8]+[22-7*(i+1) for i in range(2,h)])))
        self.assertEqual(source_digest(self.owner),before)
        self.owner.execute("UPDATE planning_input.day_observations SET availability='stockout' WHERE row_id=%s",(p+":day:0:0",))
        blocked=run_forecast(self.runner,**args,horizon=7)
        self.assertEqual(blocked["status"],"not_assessable")
        self.assertIsNone(blocked["result"]["predictions"])


if __name__=="__main__": unittest.main()
