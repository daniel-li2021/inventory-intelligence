"""Read-only explanations of existing results; no model calls or stock decisions."""

import argparse
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from fractions import Fraction
import json
import os
from pathlib import Path
import sys
from uuid import UUID

from .forecasting import METHODS

MAX_BYTES = 2 * 1024 * 1024
MAX_FINDINGS = 1000
STATUSES = {"pass", "fail", "not_assessable"}
REASONS = {
    "R001": {"quantity_mismatch"},
    "R002": {"duplicate_movement_key"},
    "R003": {"unknown_reference", "missing_opening_balance", "duplicate_opening_balance",
             "opening_cutoff_mismatch"},
    "R004": {"invalid_transfer"},
    "R005": {"missing_batch", "incomplete_batch", "count_mismatch", "metadata_mismatch",
             "stale_snapshot", "coverage_mismatch", "missing_snapshot", "duplicate_snapshot"},
}
QUESTIONS = {
    "what failed": "reliability",
    "summarize inventory reliability": "reliability",
    "explain this finding": "finding",
    "compare the forecast baselines": "benchmark",
    "can i make a replenishment decision": "readiness",
    "how much should i order": "readiness",
}


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _time(value):
    if not isinstance(value, (str, datetime)):
        raise ValueError("timestamps must be aware ISO 8601 or datetime values")
    try:
        result = datetime.fromisoformat(value) if isinstance(value, str) else value
        if result.tzinfo is None or result.utcoffset() != timedelta(0):
            raise ValueError
        return result.astimezone(timezone.utc)
    except ValueError:
        raise ValueError("timestamps must use aware UTC") from None


def _bounded(value, *, rationals=False, max_bytes=MAX_BYTES):
    def encode(obj):
        if rationals and isinstance(obj, Fraction):
            return str(obj)
        raise TypeError
    try:
        encoded = json.dumps(value, allow_nan=False, default=encode).encode("utf-8")
    except (TypeError, ValueError):
        raise ValueError("evidence must be JSON-compatible") from None
    if len(encoded) > max_bytes:
        raise ValueError("evidence exceeds the size limit")


def _validate_report(report):
    try:
        _bounded(report)
        if report["contract_version"] != "1":
            raise ValueError
        UUID(report["run_id"])
        if not all(_text(report[key]) for key in
                   ("code_version", "ledger_batch_id", "snapshot_batch_id")):
            raise ValueError
        # Future cutoffs are valid failed reports, with R005 metadata evidence.
        _time(report["evaluated_at"])
        _time(report["as_of"])
        checks = report["checks"]
        if not isinstance(checks, list) or len(checks) != 5:
            raise ValueError
        states = {check["rule_id"]: check["status"] for check in checks}
        if set(states) != set(REASONS) or not set(states.values()) <= STATUSES:
            raise ValueError
        overall = "fail" if "fail" in states.values() else (
            "not_assessable" if "not_assessable" in states.values() else "pass")
        if report["overall_status"] != overall:
            raise ValueError
        findings = report["findings"]
        if not isinstance(findings, list) or len(findings) > MAX_FINDINGS:
            raise ValueError
        ids = set()
        failed = set()
        for f in findings:
            rule = f["rule_id"]
            if (f["reason"] not in REASONS[rule] or f["severity"] != "error"
                    or not _text(f["finding_id"]) or f["finding_id"] in ids
                    or not isinstance(f["evidence"], dict)):
                raise ValueError
            ids.add(f["finding_id"])
            failed.add(rule)
            rows = f["source_row_ids"]
            if (not isinstance(rows, list) or not all(_text(row) for row in rows)
                    or len(rows) != len(set(rows))):
                raise ValueError
            for key in ("sku_id", "warehouse_id"):
                if f[key] is not None and not _text(f[key]):
                    raise ValueError
            quantities = [f[key] for key in ("expected_qty", "observed_qty", "delta_qty")]
            if rule == "R001":
                if (not all(type(q) is int for q in quantities)
                        or quantities[1] - quantities[0] != quantities[2]
                        or quantities[2] == 0 or not rows
                        or f["sku_id"] is None or f["warehouse_id"] is None):
                    raise ValueError
            elif any(q is not None for q in quantities):
                raise ValueError
        if failed != {rule for rule, state in states.items() if state == "fail"}:
            raise ValueError
        if (_time(report["evaluated_at"]) < _time(report["as_of"])
                and not any(f["rule_id"] == "R005" and f["reason"] == "metadata_mismatch"
                            for f in findings)):
            raise ValueError
    except (KeyError, TypeError, ValueError, AttributeError):
        raise ValueError("invalid or inconsistent contract-v1 reliability report") from None


def _rational(value):
    if type(value) is not int and not isinstance(value, (str, Fraction)):
        raise ValueError("benchmark numbers must be exact integers or rationals")
    return Fraction(value)


def _validate_benchmark(benchmark):
    """Check supplied fold/score consistency; never rerun a forecasting model."""
    try:
        _bounded(benchmark, rationals=True)
        for key in ("horizon", "season_length", "scored_points"):
            if type(benchmark[key]) is not int or benchmark[key] < 1:
                raise ValueError
        horizon = benchmark["horizon"]
        folds = benchmark["folds"]
        if not isinstance(folds, list) or not folds or benchmark["scored_points"] != len(folds) * horizon:
            raise ValueError
        absolute = dict.fromkeys(METHODS, Fraction(0))
        signed = dict.fromkeys(METHODS, Fraction(0))
        total = 0
        previous = 0
        for fold in folds:
            origin = fold["origin"]
            if type(origin) is not int or origin <= previous or origin < benchmark["season_length"]:
                raise ValueError
            previous = origin
            actual = fold["actual"]
            if (not isinstance(actual, list) or len(actual) != horizon
                    or any(type(a) is not int or a < 0 for a in actual)
                    or set(fold["predictions"]) != set(METHODS)):
                raise ValueError
            total += sum(actual)
            for method in METHODS:
                predicted = fold["predictions"][method]
                if not isinstance(predicted, list) or len(predicted) != horizon:
                    raise ValueError
                values = [_rational(p) for p in predicted]
                if any(p < 0 for p in values):
                    raise ValueError
                errors = [p - a for p, a in zip(values, actual)]
                absolute[method] += sum(abs(e) for e in errors)
                signed[method] += sum(errors)
        if set(benchmark["scores"]) != set(METHODS):
            raise ValueError
        scores = {}
        for method in METHODS:
            score = benchmark["scores"][method]
            expected = dict(mae=absolute[method] / benchmark["scored_points"],
                            bias=signed[method] / benchmark["scored_points"],
                            wape=absolute[method] / total if total else None)
            if set(score) != set(expected) or any(
                (score[k] is not None if v is None else _rational(score[k]) != v)
                for k, v in expected.items()
            ):
                raise ValueError
            scores[method] = {k: str(v) if v is not None else None for k, v in expected.items()}
        return dict(horizon=horizon, season_length=benchmark["season_length"],
                    scored_points=benchmark["scored_points"],
                    origins=[fold["origin"] for fold in folds], scores=scores)
    except (KeyError, TypeError, ValueError, ZeroDivisionError, AttributeError):
        raise ValueError("invalid or inconsistent baseline benchmark") from None


def answer(*, intent, report=None, benchmark=None, finding_id=None, now=None, max_age_hours=24):
    """Explain supplied evidence. Readiness never invents unfinished Stage 2 inputs."""
    result = dict(contract_version="copilot-1", intent=intent, status="not_assessable",
                  summary="Required evidence is unavailable.", citations=[], limitations=[],
                  next_steps=[], proposed_order_qty=None)
    if intent not in {"reliability", "finding", "benchmark", "readiness"}:
        result.update(status="refused", summary="Unsupported question or action.")
        result["limitations"] = ["Use an explicit supported read-only intent."]
        return result
    if intent == "benchmark":
        result["limitations"] = [
            "This mathematical benchmark has no dated source or demand-eligibility provenance.",
            "WAPE is a ratio; null means zero total actual demand.",
            "These scores do not select a production model or authorize an inventory decision."]
        if benchmark is not None:
            scores = _validate_benchmark(benchmark)
            result.update(status="answered", summary="Exact scores on shared rolling origins are shown in benchmark:scores.")
            result["citations"] = [dict(id="benchmark:scores", source="backtest.scores/folds", data=scores)]
        return result
    if type(max_age_hours) is not int or not 0 <= max_age_hours <= 2147483647:
        raise ValueError("max_age_hours must be a nonnegative PostgreSQL integer")
    if report is not None:
        _validate_report(report)
        report = deepcopy(report)
        run_ref = "run:" + report["run_id"]
        metadata = {k: report[k] for k in (
            "run_id", "contract_version", "code_version", "ledger_batch_id", "snapshot_batch_id",
            "as_of", "evaluated_at", "overall_status", "checks")}
        result["citations"].append(dict(id=run_ref, source="reliability.runs/check_results", data=metadata))
        result["limitations"].append("This run describes its original cutoff and coverage, not current stock or complete demand.")
    if intent == "readiness":
        decision_time = _time(now)
        if report is None:
            result["limitations"].append("No reliability run was supplied.")
        else:
            if report["overall_status"] != "pass":
                result["limitations"].append(f"The selected run is {report['overall_status']} [{run_ref}]; readiness is blocked globally.")
            if decision_time < _time(report["evaluated_at"]) or decision_time < _time(report["as_of"]):
                result["limitations"].append(f"The run is in the future relative to question time [{run_ref}].")
            elif decision_time - _time(report["as_of"]) > timedelta(hours=max_age_hours):
                result["limitations"].append(f"Inventory evidence exceeds the question-time freshness limit [{run_ref}].")
        result["limitations"].append("No validated Stage 2 proposal was supplied to this request. Use the planning intent to explain an explicit persisted planning run.")
        result.update(summary="A replenishment decision is not assessable; no order quantity is proposed.")
        result["next_steps"] = ["Supply an explicit persisted Stage 2 run for historical explanation; assess current inputs at a new planning cutoff before acting."]
        return result
    if report is None:
        return result
    if intent == "finding":
        findings = [f for f in report["findings"] if f["finding_id"] == finding_id]
        if not findings:
            result["limitations"].append("The selected finding ID is absent; no bucket outcome is inferred.")
            return result
    else:
        findings = report["findings"]
    result.update(status="answered", summary=f"The selected reliability run is {report['overall_status']} [{run_ref}].")
    for f in findings:
        ref = f"finding:{report['run_id']}:{f['finding_id']}"
        result["citations"].append(dict(id=ref, source="reliability.findings", data=f))
        if intent == "finding":
            if f["rule_id"] == "R001":
                result["summary"] = (f"Snapshot {f['observed_qty']} minus ledger expectation {f['expected_qty']} "
                                     f"equals {f['delta_qty']:+d} pieces [{ref}].")
            else:
                result["summary"] = f"The checker recorded {f['reason']} under {f['rule_id']} [{ref}]; see its original evidence."
        if f["rule_id"] == "R001":
            step = "Review the cited opening, movement and snapshot evidence before any correction."
        elif f["rule_id"] in {"R002", "R004"}:
            step = "Review the cited source identities or transfer conditions; do not deduplicate or repair stock automatically."
        else:
            step = "Review the cited references, coverage, manifests and timestamps before relying on quantities."
        if step not in result["next_steps"]:
            result["next_steps"].append(step)
    result["limitations"].append("Findings establish recorded defects; they do not establish business causation or a repair quantity.")
    return result


def load_run(conn, run_id):
    """Retrieve an explicit persisted run in a coherent, read-only transaction."""
    from psycopg.pq import TransactionStatus
    from psycopg.rows import dict_row

    try:
        run_id = str(UUID(run_id))
    except (ValueError, TypeError, AttributeError):
        raise ValueError("run_id must be a UUID") from None
    if not conn.autocommit or conn.info.transaction_status != TransactionStatus.IDLE:
        raise ValueError("connection must be idle with autocommit=True")
    with conn.transaction():
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            cur.execute("SET LOCAL TIME ZONE 'UTC'")
            cur.execute("SELECT current_user AS name")
            if cur.fetchone()["name"] != "ii_runner":
                raise ValueError("connection must use ii_runner")
            cur.execute("SELECT * FROM reliability.runs WHERE run_id = %s", (run_id,))
            report = cur.fetchone()
            if report is None:
                raise ValueError("selected reliability run does not exist")
            report["run_id"] = str(report["run_id"])
            for key in ("as_of", "evaluated_at"):
                report[key] = _time(report[key]).isoformat()
            cur.execute("SELECT rule_id, status FROM reliability.check_results WHERE run_id = %s ORDER BY rule_id", (run_id,))
            report["checks"] = cur.fetchall()
            cur.execute("""SELECT count(*) AS count,
                           coalesce(sum(octet_length(row_to_json(f)::text)), 0) AS bytes
                           FROM reliability.findings f WHERE run_id = %s""", (run_id,))
            size = cur.fetchone()
            if size["count"] > MAX_FINDINGS or size["bytes"] > MAX_BYTES:
                raise ValueError("selected run exceeds evidence limits")
            cur.execute("SELECT * FROM reliability.findings WHERE run_id = %s ORDER BY rule_id, finding_id", (run_id,))
            report["findings"] = cur.fetchall()
            for f in report["findings"]:
                del f["run_id"]
            # Match the checker's deterministic presentation, independent of DB collation.
            report["findings"].sort(key=lambda f: (f["rule_id"], f["reason"], f["sku_id"] or "",
                                                 f["warehouse_id"] or "", f["source_row_ids"], f["finding_id"]))
            _validate_report(report)
            return report


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def _read(path):
    with Path(path).open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("evidence file exceeds the 2 MiB limit")
    def invalid_constant(value):
        raise ValueError("nonstandard JSON number")
    return json.loads(raw, object_pairs_hook=_object, parse_constant=invalid_constant)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Explain existing inventory evidence without stock writes or orders")
    route = parser.add_mutually_exclusive_group(required=True)
    route.add_argument("--intent", choices=("reliability", "finding", "benchmark", "readiness", "planning"))
    route.add_argument("--question", help="Supported phrases: " + "; ".join(QUESTIONS))
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--report", help="Complete saved reliability JSON report")
    source.add_argument("--run-id", help="Explicit persisted UUID, read through DATABASE_URL")
    source.add_argument("--planning-run-id", help="Explicit persisted Stage 2 UUID; use --intent planning")
    parser.add_argument("--benchmark", help="Saved baseline benchmark JSON")
    parser.add_argument("--finding-id")
    parser.add_argument("--now", help="UTC question time; defaults to current UTC")
    parser.add_argument("--max-age-hours", type=int, default=24)
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--language-model", choices=("gpt-6-luna", "gpt-6-sol", "offline"),
                        default="gpt-6-luna", help="Question routing only; exact supported phrases stay offline")
    parser.add_argument("--env-file", default=".env", help="Ignored local API key file; never executed")
    parser.add_argument("--measure-usage", action="store_true", help="Expose measured routing API latency and provider token counters")
    args = parser.parse_args(argv)
    try:
        routing = None
        telemetry = {} if args.measure_usage else None
        intent = args.intent
        if args.question:
            from .copilot_language import route_question
            options = dict(model=args.language_model, env_file=args.env_file)
            if telemetry is not None:
                options["telemetry"] = telemetry
            routing = route_question(args.question, **options)
            intent = routing["intent"]
        # A refusal needs no source retrieval, credentials or evidence validation.
        supported = intent != "unsupported"
        if intent == "planning" or (args.planning_run_id and supported):
            from .copilot_planning import load_planning_run, answer_planning
            if intent != "planning" or not args.planning_run_id:
                raise ValueError("planning requires --intent planning and --planning-run-id")
            import psycopg
            dsn = os.environ.get("DATABASE_URL")
            if not dsn:
                raise ValueError("DATABASE_URL is required for --planning-run-id")
            with psycopg.connect(dsn, autocommit=True) as conn:
                result = answer_planning(load_planning_run(conn, args.planning_run_id))
        else:
            result = None
        report = _read(args.report) if args.report and supported else None
        if args.run_id and supported:
            import psycopg
            dsn = os.environ.get("DATABASE_URL")
            if not dsn:
                raise ValueError("DATABASE_URL is required for --run-id")
            with psycopg.connect(dsn, autocommit=True) as conn:
                report = load_run(conn, args.run_id)
        result = result if result is not None else answer(intent=intent, report=report,
                        benchmark=_read(args.benchmark) if args.benchmark and supported else None,
                        finding_id=args.finding_id,
                        now=_time(args.now) if args.now else datetime.now(timezone.utc),
                        max_age_hours=args.max_age_hours)
        if routing:
            result["routing"] = {k: routing[k] for k in ("source", "model")}
            if telemetry is not None:
                result["routing"]["telemetry"] = telemetry
            if routing["limitation"]:
                result["limitations"].append(routing["limitation"])
        if args.report:
            result["limitations"].append("Saved JSON is caller-supplied evidence; persisted provenance has not been verified.")
        output = json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2, allow_nan=False)
        if args.format == "markdown":
            output = "# Inventory Copilot\n\n```json\n" + output + "\n```"
        print(output)
        return 0 if result["status"] == "answered" else 1
    except Exception as exc:
        # Keep provider/driver/OS details and credentials out of diagnostics.
        diagnostic = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
        print(f"inventory-copilot: {diagnostic}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
