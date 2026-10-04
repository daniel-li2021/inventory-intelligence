"""Native synthetic transaction interruption, snapshot isolation, crash and restore.

Requires a dedicated disposable pilot cluster, TEST_DATABASE_URL/DATABASE_URL
pointing at a fresh bootstrapped recovery DB, --pg-bin and --pgdata. Never run on
a demo/production cluster. The exact selected cluster is stopped immediately and
restarted; no other PostgreSQL process is touched.
"""
import argparse
from datetime import timedelta
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import psycopg
from psycopg import sql

from scripts.engineering_fixtures import (CUTOFF,encoded,inventory_manifest,load_inventory,source_digest)
from scripts.engineering_benchmark import connect,history
from inventory_intelligence.reliability import run_checks

ROOT=Path(__file__).resolve().parents[1]


def result_digest(conn):
    h=sha256()
    for table,key in (("runs","run_id"),("check_results","run_id,rule_id"),("findings","run_id,finding_id")):
        h.update(table.encode())
        with conn.cursor().copy(sql.SQL("COPY (SELECT row_to_json(t)::text FROM reliability.{} t ORDER BY {}) TO STDOUT")
                .format(sql.Identifier(table),sql.SQL(key))) as stream:
            for block in stream: h.update(block)
    return h.hexdigest()


def blocked_writer(owner,args,output,*,kill):
    before=history(owner)
    blocker=connect("TEST_DATABASE_URL")
    blocker.execute("BEGIN")
    blocker.execute("LOCK reliability.findings IN ACCESS EXCLUSIVE MODE")
    env=dict(os.environ,II_FAULT_ARGS=json.dumps(args))
    code="""import json,os,psycopg
from datetime import datetime
from inventory_intelligence.reliability import run_checks
args=json.loads(os.environ['II_FAULT_ARGS'])
for key in ('as_of','evaluated_at'): args[key]=datetime.fromisoformat(args[key])
with psycopg.connect(os.environ['DATABASE_URL'],autocommit=True,application_name='ii-pilot-fault-writer') as conn:
 conn.execute("SET statement_timeout='55s'")
 result=run_checks(conn,**args)
 print(json.dumps(result))
"""
    begin=time.monotonic()
    with (output/("interrupted.log" if kill else "concurrent.log")).open("w") as log:
        process=subprocess.Popen([sys.executable,"-c",code],cwd=ROOT,env=env,stdout=log,stderr=log)
        try:
            waiting=False
            for _ in range(60):
                waiting=owner.execute("SELECT EXISTS(SELECT FROM pg_stat_activity WHERE application_name='ii-pilot-fault-writer' AND wait_event_type='Lock' AND query LIKE '%%INSERT INTO reliability.findings%%')").fetchone()[0]
                if waiting: break
                if process.poll() is not None: break
                time.sleep(.05)
            if not waiting: raise AssertionError("writer did not reach the predeclared persistence fault boundary")
            visible=owner.execute("SELECT count(*) FROM reliability.runs").fetchone()[0]
            if visible!=before["reliability_runs"]: raise AssertionError("uncommitted parent became visible")
            if kill:
                process.kill(); process.wait(timeout=5)
            else:
                # Deliberate source-owner transaction in this separate fault fixture.
                # Retained writer must persist its already acquired repeatable-read snapshot.
                with owner.transaction():
                    owner.execute("UPDATE operational_fixture.snapshots SET on_hand_qty=on_hand_qty+1, observed_at=%s WHERE batch_id=%s",(CUTOFF+timedelta(seconds=1),args["snapshot_batch_id"]))
                    owner.execute("UPDATE operational_fixture.batches SET observed_at=%s WHERE batch_id=%s",(CUTOFF+timedelta(seconds=1),args["snapshot_batch_id"]))
            blocker.execute("ROLLBACK")
            if not kill:
                process.wait(timeout=10)
                if process.returncode: raise AssertionError("released writer failed")
        finally:
            if process.poll() is None: process.kill(); process.wait()
            blocker.close()
    for _ in range(40):
        if not owner.execute("SELECT EXISTS(SELECT FROM pg_stat_activity WHERE application_name='ii-pilot-fault-writer')").fetchone()[0]: break
        time.sleep(.05)
    after=history(owner)
    if kill and before!=after: raise AssertionError("interrupted writer left partial evidence")
    return dict(fault="client process killed at blocked child insert" if kill else "source owner committed while writer blocked",
        seconds=time.monotonic()-begin,history_before=before,history_after=after,
        waiting_boundary_observed=True,uncommitted_parent_invisible=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--pg-bin",type=Path,required=True)
    parser.add_argument("--pgdata",type=Path,required=True)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    pgdata=args.pgdata.resolve()
    owner=connect("TEST_DATABASE_URL")
    if Path(owner.execute("SHOW data_directory").fetchone()[0]).resolve()!=pgdata:
        raise ValueError("selected DB does not belong to explicit disposable cluster")
    if owner.execute("SELECT current_database()").fetchone()[0]!="engineering_recovery":
        raise ValueError("require isolated engineering_recovery DB")
    if any(history(owner).values()) or owner.execute("SELECT count(*) FROM operational_fixture.batches").fetchone()[0]:
        raise ValueError("recovery fixture requires fresh database")
    port=owner.execute("SHOW port").fetchone()[0]
    begin=time.monotonic(); cases=[]
    protocol=dict(version="engineering-recovery-v1",source_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        scope="fresh two-key synthetic fault DB on explicit disposable native cluster",
        faults=["kill writer while findings insert blocked","owner commit during repeatable-read writer",
            "immediate PostgreSQL stop/restart","pg_dump custom restore to second database"],
        reference_host=False,guaranteed_rto_rpo=False)
    (args.output/"protocol.json").write_bytes(encoded(protocol)+b"\n")
    m=inventory_manifest("v2",2,0,quantity_probe=True)
    load_inventory(owner,m)
    context=dict(ledger_batch_id="v2:ledger",snapshot_batch_id="v2:snapshot",as_of=CUTOFF,evaluated_at=CUTOFF,code_version=protocol["source_sha256"])
    with connect("DATABASE_URL") as runner: committed=run_checks(runner,**context)
    before_source=source_digest(owner); before_result=result_digest(owner)
    cases.append(blocked_writer(owner,{**context,"as_of":CUTOFF.isoformat(),"evaluated_at":CUTOFF.isoformat()},args.output,kill=True))
    assert before_source==source_digest(owner) and before_result==result_digest(owner)
    cases.append(blocked_writer(owner,{**context,"as_of":CUTOFF.isoformat(),"evaluated_at":CUTOFF.isoformat()},args.output,kill=False))
    old_deltas=owner.execute("SELECT delta_qty FROM reliability.findings WHERE run_id<>%s ORDER BY finding_id",(committed["run_id"],)).fetchall()
    assert old_deltas==[(1,),(1,)]
    with connect("DATABASE_URL") as runner:
        new=run_checks(runner,**(context|dict(evaluated_at=CUTOFF+timedelta(seconds=1))))
    assert [f["delta_qty"] for f in new["findings"]]==[2,2]
    cases[-1].update(saved_old_deltas=[1,1],next_run_deltas=[2,2],coherent_repeatable_read=True,
        source_owner_observed_at=(CUTOFF+timedelta(seconds=1)).isoformat(),
        subsequent_evaluated_at=(CUTOFF+timedelta(seconds=1)).isoformat())
    source=source_digest(owner); results=result_digest(owner); saved_history=history(owner)
    owner.close()
    restart=time.monotonic()
    subprocess.run([str(args.pg_bin/"pg_ctl"),"-D",str(pgdata),"-m","immediate","-w","-t","10","stop"],check=True)
    subprocess.run([str(args.pg_bin/"pg_ctl"),"-D",str(pgdata),"-l",str(pgdata/"server.log"),"-w","-t","10","start"],check=True)
    owner=connect("TEST_DATABASE_URL")
    assert source_digest(owner)==source and result_digest(owner)==results and history(owner)==saved_history
    cases.append(dict(fault="immediate DB stop/restart with WAL recovery",seconds=time.monotonic()-restart,
        committed_source_preserved=True,committed_result_identity_preserved=True,observed_lost_committed_runs=0))
    dump=args.output/"recovery.dump"
    backup=time.monotonic()
    subprocess.run([str(args.pg_bin/"pg_dump"),"--dbname",os.environ["TEST_DATABASE_URL"],"-Fc","-f",str(dump)],check=True)
    owner.execute("CREATE DATABASE engineering_restore")
    restore_args=dict(psycopg.conninfo.conninfo_to_dict(os.environ["TEST_DATABASE_URL"]),dbname="engineering_restore")
    restore_dsn=psycopg.conninfo.make_conninfo(**restore_args)
    subprocess.run([str(args.pg_bin/"pg_restore"),"--dbname",restore_dsn,"--exit-on-error",str(dump)],check=True)
    with psycopg.connect(restore_dsn,autocommit=True) as restored:
        restored.execute("SET TIME ZONE 'UTC'")
        assert source_digest(restored)==source and result_digest(restored)==results and history(restored)==saved_history
    cases.append(dict(fault="synthetic backup restore to second DB",seconds=time.monotonic()-backup,
        source_sha256=source,results_sha256=results,history=saved_history,
        backup_bytes=dump.stat().st_size,backup_sha256=sha256(dump.read_bytes()).hexdigest(),
        all_saved_identities_and_quantities_preserved=True))
    owner.close()
    (args.output/"summary.json").write_bytes(encoded(dict(protocol=protocol,cases=cases,
        wall_seconds=time.monotonic()-begin,deferred=["application/server crash under live load",
            "full archive backup/restore at scale","Linux/runtime faults","RTO/RPO guarantees"]))+b"\n")
    print(json.dumps(dict(cases=len(cases),status="passed")))


if __name__=="__main__": main()
