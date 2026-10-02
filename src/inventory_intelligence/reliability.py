"""Read/check/persist under one Repeatable Read snapshot; never mutate inputs."""

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sysconfig
from uuid import uuid4

from psycopg.pq import TransactionStatus
from psycopg.rows import tuple_row
from psycopg.types.json import Jsonb


def _utc(value):
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("timestamps must be aware UTC datetime objects")
    return value.astimezone(timezone.utc).isoformat()


def _sql():
    source = Path(__file__).resolve().parents[2] / "sql"
    installed = Path(sysconfig.get_path("data")) / "share" / "inventory_intelligence"
    directory = source if (source / "checks.sql").is_file() else installed
    return "\n".join((directory / name).read_text(encoding="utf-8") for name in ("views.sql", "checks.sql"))


def _finish_report(result):
    """Stable finding identities and order, independent of PostgreSQL collation."""
    for finding in result["findings"]:
        finding["source_row_ids"].sort()
        finding["severity"] = "error"
        identity = json.dumps(finding, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        finding["finding_id"] = hashlib.sha256(identity.encode()).hexdigest()
    result["checks"].sort(key=lambda check: check["rule_id"])
    result["findings"].sort(key=lambda f: (
        f["rule_id"], f["reason"], f["sku_id"] or "", f["warehouse_id"] or "",
        f["source_row_ids"], f["finding_id"],
    ))
    statuses = {check["status"] for check in result["checks"]}
    result["overall_status"] = "fail" if "fail" in statuses else (
        "not_assessable" if "not_assessable" in statuses else "pass"
    )
    return result


def run_checks(
    conn, *, ledger_batch_id: str, snapshot_batch_id: str,
    as_of, evaluated_at, code_version: str = "dev", max_snapshot_age_hours: int = 24,
) -> dict:
    """Check selected immutable batches and atomically append a reliability run.

    The caller supplies an idle autocommit Psycopg connection. Configuration and
    SQL/persistence errors raise and leave no partial run behind.
    """
    timestamps = {"as_of": _utc(as_of), "evaluated_at": _utc(evaluated_at)}
    for name, value in (("ledger_batch_id", ledger_batch_id), ("snapshot_batch_id", snapshot_batch_id),
                        ("code_version", code_version)):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a nonempty string")
    if type(max_snapshot_age_hours) is not int or not 0 <= max_snapshot_age_hours <= 2147483647:
        raise ValueError("max_snapshot_age_hours must be a nonnegative PostgreSQL integer")
    if not conn.autocommit or conn.info.transaction_status != TransactionStatus.IDLE:
        raise ValueError("connection must be idle with autocommit=True")
    params = dict(ledger_batch_id=ledger_batch_id, snapshot_batch_id=snapshot_batch_id,
                  as_of=as_of, evaluated_at=evaluated_at, max_snapshot_age_hours=max_snapshot_age_hours)
    query = _sql()
    with conn.transaction():
        with conn.cursor(row_factory=tuple_row) as cur:
            cur.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
            # Keep evidence timestamps stable even when the caller's session uses another timezone.
            cur.execute("SET LOCAL TIME ZONE 'UTC'")
            cur.execute(query, params)
            result = _finish_report(cur.fetchone()[0])
            result.update(run_id=str(uuid4()), contract_version="1", code_version=code_version,
                          ledger_batch_id=ledger_batch_id, snapshot_batch_id=snapshot_batch_id, **timestamps)
            cur.execute("""
                INSERT INTO reliability.runs
                (run_id, contract_version, code_version, ledger_batch_id, snapshot_batch_id,
                 as_of, evaluated_at, overall_status)
                VALUES (%(run_id)s, %(contract_version)s, %(code_version)s, %(ledger_batch_id)s,
                        %(snapshot_batch_id)s, %(as_of)s, %(evaluated_at)s, %(overall_status)s)
            """, result)
            cur.executemany("""
                INSERT INTO reliability.check_results (run_id, rule_id, status)
                VALUES (%s, %s, %s)
            """, [(result["run_id"], c["rule_id"], c["status"]) for c in result["checks"]])
            if result["findings"]:
                cur.executemany("""
                    INSERT INTO reliability.findings
                    (run_id, finding_id, rule_id, severity, reason, sku_id, warehouse_id,
                     source_row_ids, expected_qty, observed_qty, delta_qty, evidence)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [(
                    result["run_id"], f["finding_id"], f["rule_id"], f["severity"], f["reason"],
                    f["sku_id"], f["warehouse_id"], Jsonb(f["source_row_ids"]),
                    f["expected_qty"], f["observed_qty"], f["delta_qty"], Jsonb(f["evidence"]),
                ) for f in result["findings"]])
    return result
