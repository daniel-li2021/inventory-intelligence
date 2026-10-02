"""Standard-library CLI; DATABASE_URL must select the provisioned runtime role."""

import argparse
from datetime import datetime, timezone
import json
import os
import sys

import psycopg

from .reliability import run_checks


def _timestamp(value):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError
        return parsed.astimezone(timezone.utc)
    except ValueError:
        raise argparse.ArgumentTypeError("use an ISO 8601 timestamp with timezone") from None


def _cell(value):
    return str(value).replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def markdown(report):
    lines = [f"# Inventory reliability: {report['overall_status']}", "",
             f"Run: `{report['run_id']}`", "",
             f"Ledger: {_cell(report['ledger_batch_id'])}; snapshot: {_cell(report['snapshot_batch_id'])}",
             f"Cutoff: {report['as_of']}; evaluated: {report['evaluated_at']}", "",
             "| Rule | Status |", "| --- | --- |"]
    lines.extend(f"| {c['rule_id']} | {c['status']} |" for c in report["checks"])
    for finding in report["findings"]:
        lines.extend(["", f"## {finding['rule_id']}: {finding['reason']}", "", "```json",
                      json.dumps(finding, sort_keys=True, ensure_ascii=False, indent=2), "```"])
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check existing inventory batches without modifying them")
    parser.add_argument("--ledger-batch", required=True)
    parser.add_argument("--snapshot-batch", required=True)
    parser.add_argument("--as-of", required=True, type=_timestamp)
    parser.add_argument("--evaluated-at", required=True, type=_timestamp)
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--max-snapshot-age-hours", type=int, default=24)
    parser.add_argument("--code-version", default="dev")
    args = parser.parse_args(argv)
    try:
        dsn = os.environ.get("DATABASE_URL")
        if not dsn:
            raise ValueError("DATABASE_URL is required")
        with psycopg.connect(dsn, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT current_user")
                if cur.fetchone()[0] != "ii_runner":
                    raise ValueError("DATABASE_URL must connect as ii_runner")
            report = run_checks(
                conn, ledger_batch_id=args.ledger_batch, snapshot_batch_id=args.snapshot_batch,
                as_of=args.as_of, evaluated_at=args.evaluated_at, code_version=args.code_version,
                max_snapshot_age_hours=args.max_snapshot_age_hours,
            )
        output = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n" if args.format == "json" else markdown(report)
        sys.stdout.write(output)
        return 0 if report["overall_status"] == "pass" else 1
    except (ValueError, OSError, psycopg.Error) as exc:
        # Driver messages can include credentials/connection strings; never echo them.
        diagnostic = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
        if isinstance(exc, psycopg.Error) and exc.sqlstate:
            diagnostic += f" (SQLSTATE {exc.sqlstate})"
        print(f"inventory-intelligence: {diagnostic}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
