"""Fresh synthetic Stage 2 demo: replay benchmark, trusted stock, clean/blocked plans."""

import argparse
from datetime import timedelta
import json
import os

import psycopg
from psycopg import sql

from inventory_intelligence.demand import midnight
from inventory_intelligence.planning_runs import exact_json, run_benchmark
from inventory_intelligence.reliability import run_checks
from inventory_intelligence.replenishment import run_plan
from synthetic.demand import load_demand, START, END
from synthetic.generate import _scenario_data


def _insert(conn, schema, table, rows):
    columns = list(rows[0])
    with conn.cursor() as cur:
        cur.executemany(sql.SQL("INSERT INTO {}.{} ({}) VALUES ({})").format(
            sql.Identifier(schema), sql.Identifier(table), sql.SQL(",").join(map(sql.Identifier, columns)),
            sql.SQL(",").join(sql.Placeholder() for _ in columns)),
            [tuple(r[c] for c in columns) for r in rows])


def load_inputs(owner):
    """Refuse reload through PKs; never update an existing demo or operational row."""
    prefix = "planning-demo"
    origin = midnight(END)
    data, _ = _scenario_data("clean")
    with owner.transaction():
        for table in ("styles", "skus", "warehouses"):
            rows = [{k:v.replace("clean:",prefix+":") if isinstance(v,str) else v
                     for k,v in r.items()} for r in data[table]]
            _insert(owner,"operational_fixture",table,rows)
        manifests, coverage, openings, snapshots = [],[],[],[]
        for kind in ("ledger","snapshot"):
            manifests.append(dict(batch_id=prefix+":"+kind,kind=kind,status="complete",
                baseline_at=origin-timedelta(days=1) if kind=="ledger" else None,as_of=origin,
                watermark=0,observed_at=origin,expected_row_count=0 if kind=="ledger" else 5))
            for i, original in enumerate(data["snapshots"]):
                sku, wh = (original[k].replace("clean:",prefix+":") for k in ("sku_id","warehouse_id"))
                qty = 0 if sku.endswith(":tee-l") else 10
                coverage.append(dict(row_id=f"{prefix}:coverage:{kind}:{i}",batch_id=prefix+":"+kind,
                                     sku_id=sku,warehouse_id=wh))
                if kind=="ledger":
                    openings.append(dict(row_id=f"{prefix}:opening:{i}",batch_id=prefix+":ledger",
                        sku_id=sku,warehouse_id=wh,quantity=qty,as_of=origin-timedelta(days=1),baseline_ref="synthetic-count"))
                else:
                    snapshots.append(dict(row_id=f"{prefix}:snapshot:{i}",batch_id=prefix+":snapshot",
                        sku_id=sku,warehouse_id=wh,on_hand_qty=qty,as_of=origin,watermark=0,observed_at=origin))
        for table, rows in (("batches",manifests),("coverage",coverage),("opening_balances",openings),("snapshots",snapshots)):
            _insert(owner,"operational_fixture",table,rows)
        for label, complete in (("complete",True),("incomplete",False)):
            batch=prefix+":supply:"+label
            _insert(owner,"planning_input","supply_batches",[dict(batch_id=batch,version_id="demo-supply-v1",
                sku_id=prefix+":tee-m",warehouse_id=prefix+":harbor",as_of=origin,observed_at=origin,
                status="complete",reservations_complete=complete,inbound_complete=True,
                expected_reservations=1,expected_inbound=2)])
            _insert(owner,"planning_input","policies",[dict(row_id=batch+":policy",batch_id=batch,
                lead_days=2,review_days=3,safety_qty=2,pack_size=6,moq=10,source_recorded_at=origin,observed_at=origin)])
            _insert(owner,"planning_input","reservations",[dict(row_id=batch+":reservation",batch_id=batch,
                source_system="synthetic",reservation_id="remaining-commitment",remaining_qty=3,due_day=END,
                status="open",source_recorded_at=origin,observed_at=origin)])
            _insert(owner,"planning_input","inbound",[dict(row_id=batch+":"+name,batch_id=batch,
                source_system="synthetic",inbound_id=name,remaining_qty=qty,arrival_day=END+timedelta(days=day),
                status=status,source_recorded_at=origin,observed_at=origin)
                for name,qty,day,status in (("confirmed",5,1,"confirmed"),("pending",100,0,"pending"))])
    return load_demand(owner,batch_id=prefix+":demand",source_prefix=prefix)


def run_demo(owner,runner):
    inputs=load_inputs(owner)
    origin=midnight(END)
    stock=run_checks(runner,ledger_batch_id="planning-demo:ledger",snapshot_batch_id="planning-demo:snapshot",
                     as_of=origin,evaluated_at=origin,code_version="stage2-demo-v1")
    if stock["overall_status"] != "pass":
        raise RuntimeError("synthetic inventory clean control must pass")
    benchmarks=[]
    for key in inputs["groups"]:
        report=run_benchmark(runner,batch_id=inputs["batch_id"],**key,start_day=START,end_day=END,
                             evaluated_at=origin+timedelta(days=10),code_version="stage2-demo-v1")
        r=report["result"]
        benchmarks.append(dict(group=key["group"],run_id=report["run_id"],status=report["status"],
            chosen_method=r["chosen_method"],selection=r["selection"],holdout_scores=r["holdout_scores"],
            included_origins=sum(f["status"]=="assessable" for f in r["candidates"]),
            excluded_origins=sum(f["status"]!="assessable" for f in r["candidates"])))
    proposals=[]
    for label in ("complete","incomplete"):
        report=run_plan(runner,batch_id=inputs["batch_id"],sku_id="planning-demo:tee-m",warehouse_id="planning-demo:harbor",
            start_day=START,origin_day=END,method="mean",reliability_run_id=stock["run_id"],
            supply_batch_id="planning-demo:supply:"+label,code_version="stage2-demo-v1")
        r=report["result"]
        proposals.append(dict(label=label,run_id=report["run_id"],status=r["status"],reasons=r["reasons"],
                             proposed_order_qty=r["proposed_order_qty"],projection=r["projection"]))
    return dict(business_data="synthetic only",stage2_status="implementation awaiting integration acceptance",
                inventory_run_id=stock["run_id"],benchmarks=benchmarks,proposals=proposals)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format",choices=("json","markdown"),default="json")
    args=parser.parse_args()
    with psycopg.connect(os.environ["FIXTURE_DATABASE_URL"],autocommit=True) as owner, \
         psycopg.connect(os.environ["DATABASE_URL"],autocommit=True) as runner:
        report=run_demo(owner,runner)
    if args.format=="json":
        print(json.dumps(exact_json(report),indent=2,sort_keys=True))
    else:
        print("# Synthetic Stage 2 acceptance demo\n\n| Group | Status | Selected baseline | Included / excluded origins |\n| --- | --- | --- | --- |")
        for b in report["benchmarks"]:
            print(f"| {b['group']} | {b['status']} | {b['chosen_method'] or '—'} | {b['included_origins']} / {b['excluded_origins']} |")
        print("\n| Supply | Status | Order pieces |\n| --- | --- | --- |")
        for p in report["proposals"]:
            print(f"| {p['label']} | {p['status']} | {p['proposed_order_qty'] if p['proposed_order_qty'] is not None else '—'} |")
        print("\nSafety stock is declared; proposals are advisory. Stage 2 integration acceptance remains pending.")


if __name__=="__main__":
    main()
