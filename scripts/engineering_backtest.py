"""Supplemental constant-demand backtest growth control, not the 30%-zero grid."""
import argparse
from datetime import datetime, timedelta
from hashlib import sha256
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time
from zoneinfo import ZoneInfo
import psycopg

from scripts.engineering_benchmark import Budget,connect,history
from scripts.engineering_fixtures import START,copy_rows,encoded,grain,inventory_manifest,load_inventory,source_digest
from inventory_intelligence.planning_runs import run_benchmark
from inventory_intelligence.copilot_planning import load_planning_run

ROOT=Path(__file__).resolve().parents[1]


def midnight(day):
    return datetime.combine(day,datetime.min.time(),ZoneInfo("America/Los_Angeles"))


def worker(spec_path):
    spec=json.loads(spec_path.read_text()); days=spec["days"]
    with connect("DATABASE_URL") as conn:
        begin=time.perf_counter_ns(); cpu=time.process_time_ns()
        try:
            r=run_benchmark(conn,batch_id=spec["prefix"]+":demand",sku_id=spec["prefix"]+":sku:0",
                warehouse_id=spec["prefix"]+":wh:0",group="constant-control",start_day=START,
                end_day=START+timedelta(days=days),evaluated_at=midnight(START+timedelta(days=days)),code_version=spec["code"])
            elapsed=time.perf_counter_ns()-begin; cpu=time.process_time_ns()-cpu
            result=r["result"]
            expected_origins=spec["expected_origins"]
            assert [f["origin_day"] for f in result["candidates"]]==[(START+timedelta(days=i)).isoformat() for i in expected_origins]
            assert result["chosen_method"]=="naive" and result["status"]=="assessable"
            for fold in result["candidates"]+[result["holdout"]]:
                assert fold["actual"]==[4]*28
                assert all(p==["4"]*28 for p in fold["predictions"].values())
                assert all(d["quantity"]==4 for d in fold["training"]["days"])
            for label,n in (("selection",len(expected_origins)),("holdout_scores",1)):
                for h in (7,14,28):
                    score=result[label][str(h)]
                    assert score["scored_points"]==n*h
                    assert all(s==dict(mae="0",bias="0",wape="0") for s in score["scores"].values())
            raw=encoded(r); spec_path.with_suffix(".report.json").write_bytes(raw+b"\n")
            begin_reader=time.perf_counter_ns()
            try:
                loaded=load_planning_run(conn,r["run_id"]); assert loaded==r
                reader="completed"
            except ValueError: reader="rejected"
            value=dict(status="completed",oracle="pass",run_id=r["run_id"],elapsed_ns=elapsed,cpu_ns=cpu,
                report_bytes=len(raw),report_sha256=sha256(raw).hexdigest(),candidate_origins=len(expected_origins),
                reader_status=reader,reader_ns=time.perf_counter_ns()-begin_reader,
                process_high_water_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=="darwin" else 1024))
        except psycopg.Error as error:
            value=dict(status="error",error_type=type(error).__name__,error=str(error),elapsed_ns=time.perf_counter_ns()-begin)
        except AssertionError:
            value=dict(status="incorrect",run_id=r["run_id"],oracle="fail",elapsed_ns=time.perf_counter_ns()-begin)
        spec_path.with_suffix(".result.json").write_bytes(encoded(value)+b"\n")


def controller(output,pgdata,wall_seconds):
    output.mkdir(parents=True,exist_ok=False); budget=Budget(output,pgdata,wall_seconds)
    code=sha256(Path(__file__).read_bytes()).hexdigest()
    protocol=dict(version="engineering-backtest-control-v1",profile="constant accepted quantity 4/day, all methods have zero error",
        history_days=[180,365,730],archive_keys=[1,10],selected_keys=1,known_revisions="every 20th one-based line",
        late_revisions="every 100th line; both clocks after evaluation",repeats=1,
        code_sha256=code,confirmation=False,canonical_30_percent_zero_workload=False)
    (output/"protocol.json").write_bytes(encoded(protocol)+b"\n"); cases=[]
    with connect("TEST_DATABASE_URL") as conn:
        if any(history(conn).values()) or conn.execute("SELECT count(*) FROM operational_fixture.batches").fetchone()[0]:
            raise ValueError("backtest control requires fresh disposable DB")
        for keys in (1,10):
            for days in (180,365,730):
                p=f"backtest-{keys}-{days}"; begin=time.monotonic()
                load_inventory(conn,inventory_manifest(p,keys,0))
                total=keys*days; end=START+timedelta(days=days)
                with conn.transaction():
                    copy_rows(conn,"planning_input","demand_batches",[(p+":demand","constant-control-v1",
                        "America/Los_Angeles",START,end,midnight(end),"complete",total+total//20+total//100,total)])
                    copy_rows(conn,"planning_input","day_observations",(
                        (f"{p}:day:{k}:{i}",p+":demand",*grain(p,k,1),START+timedelta(days=i),1,
                         midnight(START+timedelta(days=i+1)),midnight(START+timedelta(days=i+1)),"complete","available",1)
                        for k in range(keys) for i in range(days)))
                    def orders():
                        for k in range(keys):
                            for i in range(days):
                                accepted=midnight(START+timedelta(days=i))+timedelta(hours=12)
                                for rev in (1,2,3):
                                    index=k*days+i+1
                                    if rev==2 and index%20 or rev==3 and index%100: continue
                                    observed=midnight(end)+timedelta(days=1) if rev==3 else accepted+timedelta(hours=rev-1)
                                    yield (f"{p}:order:{k}:{i}:{rev}",p+":demand","control",f"{p}:{k}:{i}","1",rev,
                                        *grain(p,k,1),accepted,observed,observed,4000 if rev==3 else 4,"accepted")
                    copy_rows(conn,"planning_input","order_versions",orders())
                conn.execute("ANALYZE"); setup=time.monotonic()-begin
                before=source_digest(conn); saved=history(conn)
                path=output/(p+".json"); path.write_bytes(encoded(dict(prefix=p,days=days,code=code,
                    expected_origins=list(range(28,days-56+1,7)),expected_quantity=4,expected_method="naive"))+b"\n")
                begin=time.monotonic()
                with path.with_suffix(".log").open("w") as log:
                    child=subprocess.Popen([sys.executable,"-m","scripts.engineering_backtest","--worker",str(path)],cwd=ROOT,stdout=log,stderr=log)
                    try:
                        while child.poll() is None:
                            budget.sample(child.pid)
                            if time.monotonic()-begin>60: child.kill(); child.wait(); break
                            time.sleep(.2)
                    finally:
                        if child.poll() is None: child.kill(); child.wait()
                value=json.loads(path.with_suffix(".result.json").read_text()) if child.returncode==0 else dict(status="worker_error",returncode=child.returncode)
                after=source_digest(conn); assert before==after
                current=history(conn)
                delta=current["planning_runs"]-saved["planning_runs"]
                if delta not in (0,1): raise AssertionError("unexpected persisted history")
                if delta==1 and value["status"] not in ("completed","incorrect"):
                    value["status"]="committed_unverified"
                case=dict(case=p,keys=keys,days=days,day_rows=total,raw_order_revision_rows=total+total//20+total//100,
                    source_before=before,source_after=after,setup_seconds=setup,**value)
                cases.append(case); print(json.dumps({k:case[k] for k in ("case","status")}),flush=True)
    (output/"summary.json").write_bytes(encoded(dict(protocol=protocol,cases=cases,
        wall_seconds=time.monotonic()-budget.start,conservative_rss_upper_bound_bytes=budget.peak_upper_rss,
        sampled_cpu_seconds=budget.cpu))+b"\n")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker",type=Path); parser.add_argument("--output",type=Path)
    parser.add_argument("--pgdata",type=Path); parser.add_argument("--wall-seconds",type=int,default=7200)
    args=parser.parse_args()
    if args.worker: worker(args.worker)
    else:
        if not args.output or not args.pgdata or not 1<=args.wall_seconds<=7200:
            parser.error("provide new --output, isolated --pgdata and remaining wall cap")
        controller(args.output,args.pgdata,args.wall_seconds)


if __name__=="__main__": main()
