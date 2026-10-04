"""Five fresh local ARM64 Linux campaigns, never x86/two-date confirmation.

Run after building inventory-lab:engineering-v1. Uses the pinned PostgreSQL 17.9
image and isolated containers; does not touch any existing database/container.
"""
import argparse
from datetime import datetime
from hashlib import sha256
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import resource
import subprocess
import time

import psycopg
from psycopg import sql
from scripts.engineering_benchmark import ROOT, write
from scripts.engineering_fixtures import CUTOFF, inventory_manifest, load_inventory, source_digest, verify_inventory, digest
from inventory_intelligence.reliability import run_checks, _sql
from inventory_intelligence.replenishment import run_plan
from scripts.engineering_fixtures import START, ORIGIN_DAY, ORIGIN, load_demand, load_supply


def worker(campaign,diagnostic_only=False):
    output=Path("/output"); samples=[]
    owner=psycopg.connect(os.environ["TEST_DATABASE_URL"],autocommit=True)
    runner=psycopg.connect(os.environ["DATABASE_URL"],autocommit=True)
    assert runner.execute("SELECT current_user").fetchone()[0]=="ii_runner"
    runner.execute("SET statement_timeout='55s'"); runner.execute("SET lock_timeout='5s'")
    runner.execute("SET TIME ZONE 'UTC'"); owner.execute("SET TIME ZONE 'UTC'")
    for name in ("server_version","shared_buffers","work_mem","synchronous_commit","checkpoint_timeout","max_wal_size","max_connections",
            "jit","jit_above_cost","jit_inline_above_cost","jit_optimize_above_cost"):
        samples.append(dict(setting=name,value=owner.execute(sql.SQL("SHOW {}").format(sql.Identifier(name))).fetchone()[0]))
    write(output/f"campaign-{campaign}-environment.json",dict(platform=platform.platform(),machine=platform.machine(),
        python=platform.python_version(),dependencies={d.metadata["Name"]:d.version for d in importlib.metadata.distributions()},
        settings=samples,query_sha256=sha256(_sql().encode()).hexdigest(),os_cache="uncontrolled VM cache; fresh PostgreSQL per campaign",
        reference_host=False,confirmation=False))
    samples=[]; setup=time.monotonic()
    manifest=inventory_manifest("linux-reference",1000,100000)
    load_inventory(owner,manifest)
    planning=inventory_manifest("linux-planning",1000,0,opening=20,cutoff=ORIGIN)
    load_inventory(owner,planning); load_demand(owner,"linux-planning",1000); load_supply(owner,"linux-planning",1000,7)
    owner.execute("ANALYZE"); setup=time.monotonic()-setup
    before=source_digest(owner)
    checked=run_checks(runner,ledger_batch_id="linux-planning:ledger",snapshot_batch_id="linux-planning:snapshot",
        as_of=ORIGIN,evaluated_at=ORIGIN,code_version="linux-controlled-v1")
    for operation in ("run_checks","run_plan"):
        for i in range(0 if diagnostic_only else 8):
            wal=owner.execute("SELECT pg_current_wal_lsn(),pg_database_size(current_database())").fetchone()
            begin=time.perf_counter_ns(); cpu=time.process_time_ns()
            if operation=="run_checks":
                r=run_checks(runner,ledger_batch_id="linux-reference:ledger",snapshot_batch_id="linux-reference:snapshot",
                    as_of=CUTOFF,evaluated_at=CUTOFF,code_version="linux-controlled-v1")
            else:
                r=run_plan(runner,batch_id="linux-planning:demand",sku_id="linux-planning:sku:0",warehouse_id="linux-planning:wh:0",
                    start_day=START,origin_day=ORIGIN_DAY,method="mean",reliability_run_id=checked["run_id"],
                    supply_batch_id="linux-planning:supply:7:0",code_version="linux-controlled-v1")
            elapsed=time.perf_counter_ns()-begin; cpu=time.process_time_ns()-cpu
            if operation=="run_checks": verify_inventory(r,manifest)
            else:
                assert r["status"]=="assessable" and r["result"]["proposed_order_qty"]==30
                assert r["result"]["unrounded_need"]=="29"
                assert [d["balance_without_order"] for d in r["result"]["projection"]]==["10","8","1","-6","-13","-20","-27"]
            sample=dict(campaign=campaign,phase="warmup" if i<2 else "measured",operation=operation,
                status="completed",oracle="pass",elapsed_ns=elapsed,cpu_ns=cpu,run_id=r["run_id"],
                semantic_sha256=digest({k:v for k,v in r.items() if k not in ("run_id","created_at")}),
                worker_high_water_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                wal_bytes=int(owner.execute("SELECT pg_wal_lsn_diff(pg_current_wal_lsn(),%s)",(wal[0],)).fetchone()[0]),
                database_bytes_before=wal[1],database_bytes_after=owner.execute("SELECT pg_database_size(current_database())").fetchone()[0])
            samples.append(sample); print(json.dumps(sample),flush=True)
    if campaign==5 or diagnostic_only:
        for label,prefix,cutoff in (("reference","linux-reference",CUTOFF),("planning-ledger","linux-planning",ORIGIN)):
            params=dict(ledger_batch_id=prefix+":ledger",snapshot_batch_id=prefix+":snapshot",
                as_of=cutoff,evaluated_at=cutoff,max_snapshot_age_hours=24)
            # Primary diagnostics use TIMING OFF; this explicit supplementary
            # pass enables timers to expose JIT generation/optimization costs.
            timing="ON" if diagnostic_only else "OFF"
            plan=owner.execute(f"EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON,TIMING {timing}) "+_sql(),params).fetchone()[0]
            write(output/(label+"-plan.json"),plan)
    after=source_digest(owner); assert before==after
    write(output/f"campaign-{campaign}.json",dict(samples=samples,setup_seconds=setup,source_before=before,source_after=after,
        worker_cgroup_memory_peak_bytes=int(Path('/sys/fs/cgroup/memory.peak').read_text()),
        worker_cgroup_cpu_stat=Path('/sys/fs/cgroup/cpu.stat').read_text(),
        history=dict(reliability_runs=owner.execute("SELECT count(*) FROM reliability.runs").fetchone()[0],
        checks=owner.execute("SELECT count(*) FROM reliability.check_results").fetchone()[0],
        findings=owner.execute("SELECT count(*) FROM reliability.findings").fetchone()[0],
        planning_runs=owner.execute("SELECT count(*) FROM planning.runs").fetchone()[0])))
    owner.close(); runner.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker",type=int); parser.add_argument("--docker",type=Path)
    parser.add_argument("--output",type=Path)
    parser.add_argument("--campaigns",type=int,default=5,choices=range(1,6))
    parser.add_argument("--diagnostic-only",action="store_true")
    args=parser.parse_args()
    if args.worker: worker(args.worker,args.diagnostic_only); return
    if not args.docker or not args.output: parser.error("provide docker/new output")
    args.output.mkdir(parents=True,exist_ok=False); output=args.output.resolve()
    output.chmod(0o777)  # Dedicated synthetic receipt directory for UID10001.
    launch_source=Path(__file__).read_bytes()
    (output/"executed-controller.py").write_bytes(launch_source)
    env=dict(os.environ,PATH=str(args.docker.parent)+os.pathsep+os.environ.get("PATH",""))
    def docker(*parts,timeout=90):
        return subprocess.check_output([str(args.docker),*parts],env=env,text=True,stderr=subprocess.STDOUT,timeout=timeout)
    network="ii-engineering-reference-"+str(os.getpid())
    docker("network","create","--internal",network)
    start=time.monotonic(); campaigns=[]
    write(output/"protocol.json",dict(campaigns=args.campaigns,dates=1,code_sha256=sha256(launch_source).hexdigest(),warmups=0 if args.diagnostic_only else 2,
        measured=0 if args.diagnostic_only else 6,diagnostic_only=args.diagnostic_only,reference_confirmation=False,
        architecture="native ARM64 Linux VM on existing Mac",allocated_cpu_total=4,memory_caps_total_bytes=8*1024**3,
        python="packaged 3.12.14, differs from proposed 3.12.12",db="pinned 17.9",
        workloads=["1000 grains/100k movements","selected plan in 1000-key/180-day demand; zero movement inventory"],
        phase_order="same order in all campaigns; no full reference counterbalance claim"))
    try:
        for campaign in range(1,args.campaigns+1):
            db=network+f"-db{campaign}"; client=network+f"-client{campaign}"
            try:
                docker("run","-d","--name",db,"--network",network,"--network-alias","db","--cpus","2","--memory","4g","--memory-swap","4g",
                    "-e","POSTGRES_DB=engineering","-e","POSTGRES_USER=ii_owner","-e","POSTGRES_PASSWORD=ii_owner_local",
                    "--mount",f"type=bind,src={ROOT}/sql/schema.sql,dst=/docker-entrypoint-initdb.d/01-schema.sql,readonly",
                    "--mount",f"type=bind,src={ROOT}/sql/planning_schema.sql,dst=/docker-entrypoint-initdb.d/02-planning.sql,readonly",
                    "postgres:17.9@sha256:2a0d0fe14825b0939f78a8cad5cd4e6aa68bf94d0e5dd96e24b6d23af4315545")
                for _ in range(90):
                    try:
                        docker("exec","-e","PGPASSWORD=ii_owner_local",db,"psql","-h","127.0.0.1","-U","ii_owner","-d","engineering","-tAc","SELECT count(*) FROM planning.runs")
                        break
                    except subprocess.CalledProcessError: time.sleep(.2)
                command=["run","--name",client,"--network",network,"--cpus","2","--memory","4g","--memory-swap","4g",
                    "--cap-drop","ALL","--security-opt","no-new-privileges:true","--workdir","/bench",
                    "-e","TEST_DATABASE_URL=postgresql://ii_owner:ii_owner_local@db:5432/engineering",
                    "-e","DATABASE_URL=postgresql://ii_runner:ii_runner_local@db:5432/engineering",
                    "--mount",f"type=bind,src={ROOT}/scripts,dst=/bench/scripts,readonly",
                    "--mount",f"type=bind,src={output},dst=/output",
                    "inventory-lab:engineering-v1","python","-m","scripts.engineering_linux","--worker",str(campaign)]
                if args.diagnostic_only: command.append("--diagnostic-only")
                log=docker(*command,timeout=120); (output/f"campaign-{campaign}.log").write_text(log)
                for label,cid in (("db",db),("client",client)):
                    write(output/f"campaign-{campaign}-{label}-inspect.json",json.loads(docker("inspect",cid)))
                stats=docker("exec",db,"sh","-c","cat /sys/fs/cgroup/memory.peak /sys/fs/cgroup/cpu.stat /sys/fs/cgroup/memory.events")
                (output/f"campaign-{campaign}-db-cgroup.txt").write_text(stats)
                campaigns.append(json.loads((output/f"campaign-{campaign}.json").read_text()))
                print(json.dumps(dict(campaign=campaign,status="completed",calls=len(campaigns[-1]["samples"]))),flush=True)
            finally:
                for cid in (client,db):
                    try: docker("rm","-f","-v",cid)
                    except subprocess.CalledProcessError: pass
    finally:
        docker("network","rm",network)
        write(output/"summary.json",dict(campaigns=campaigns,wall_seconds=time.monotonic()-start,
            reference_confirmation=False,remaining=["x86-64 host","two dates","Python3.12.12","OS cache control","all reference cells"]))


if __name__=="__main__": main()
