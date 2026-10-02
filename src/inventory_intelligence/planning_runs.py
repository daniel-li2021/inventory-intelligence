"""Append exact, versioned forecast/backtest results under one database snapshot."""

from datetime import date, datetime, timedelta, timezone
from fractions import Fraction
import hashlib
import json
from uuid import uuid4

from psycopg.pq import TransactionStatus
from psycopg.types.json import Jsonb

from inventory_intelligence.demand import instant, midnight, read_series, BUSINESS_TIMEZONE
from inventory_intelligence.forecasting import METHODS, forecast, _positive

MODEL_VERSION = "baselines-v1"
HORIZONS = (7, 14, 28)
MIN_TRAIN = 28


def _json_value(value):
    if isinstance(value, Fraction):
        return str(value)
    if isinstance(value, datetime):
        return instant(value).isoformat()
    if type(value) is date:
        return value.isoformat()
    raise TypeError(f"unsupported result type: {type(value).__name__}")


def exact_json(value):
    return json.loads(json.dumps(value, default=_json_value, sort_keys=True))


def _idle(conn, code_version):
    if not conn.autocommit or conn.info.transaction_status != TransactionStatus.IDLE:
        raise ValueError("connection must be idle with autocommit=True")
    if not isinstance(code_version, str) or not code_version.strip():
        raise ValueError("code_version must be nonempty")


def persist(conn, *, kind, context, inputs, result, code_version):
    """Caller owns transaction. JSONB keeps evidence/estimates without float coercion."""
    payload = exact_json(dict(context=context, inputs=inputs))
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    report = exact_json(dict(run_id=str(uuid4()), created_at=datetime.now(timezone.utc),
        contract_version="planning-v1", code_version=code_version, model_version=MODEL_VERSION,
        kind=kind, input_digest=digest, status=result["status"], context=context, result=result))
    conn.execute("""INSERT INTO planning.runs
        (run_id, contract_version, code_version, model_version, kind, created_at,
         input_digest, status, context, result) VALUES
        (%(run_id)s, %(contract_version)s, %(code_version)s, %(model_version)s,
         %(kind)s, %(created_at)s, %(input_digest)s, %(status)s, %(context)s, %(result)s)""",
        report | dict(context=Jsonb(report["context"]), result=Jsonb(report["result"])))
    return report


def prediction(series, *, method, horizon):
    if series["status"] != "eligible" or len(series["days"]) < MIN_TRAIN:
        return dict(status="not_assessable", predictions=None, training=series,
                    reasons=["ineligible_or_insufficient_training"])
    return dict(status="assessable", reasons=[], training=series,
                predictions=forecast([d["quantity"] for d in series["days"]],
                                     method=method, horizon=horizon))


def run_forecast(conn, *, batch_id, sku_id, warehouse_id, start_day, origin_day,
                 method, horizon, code_version="dev"):
    _idle(conn, code_version)
    _positive("horizon", horizon)
    if method not in METHODS:
        raise ValueError("unknown baseline method")
    origin = midnight(origin_day)
    with conn.transaction():
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
        series = read_series(conn, batch_id=batch_id, sku_id=sku_id, warehouse_id=warehouse_id,
                             start_day=start_day, end_day=origin_day, known_at=origin)
        result = prediction(series, method=method, horizon=horizon)
        context = dict(batch_id=batch_id, sku_id=sku_id, warehouse_id=warehouse_id,
                       start_day=start_day, origin=origin, origin_day=origin_day,
                       method=method, horizon=horizon, business_timezone=BUSINESS_TIMEZONE)
        return persist(conn, kind="forecast", context=context, inputs=series,
                       result=result, code_version=code_version)


def _scores(folds, horizon):
    points = len(folds) * horizon
    if not points:
        return dict(scored_points=0, scores=None)
    actual_total = sum(sum(f["actual"][:horizon]) for f in folds)
    scores = {}
    for method in METHODS:
        errors = [p-a for f in folds for p, a in
                  zip(f["predictions"][method][:horizon], f["actual"][:horizon])]
        absolute = sum(abs(e) for e in errors)
        scores[method] = dict(mae=Fraction(absolute, points), bias=Fraction(sum(errors), points),
                             wape=Fraction(absolute, actual_total) if actual_total else None)
    return dict(scored_points=points, scores=scores)


def run_benchmark(conn, *, batch_id, sku_id, warehouse_id, group, start_day,
                  end_day, evaluated_at, code_version="dev"):
    """Shared 7/14/28-day origins; choice frozen before the final 28-day holdout."""
    _idle(conn, code_version)
    evaluated_at = instant(evaluated_at)
    if type(start_day) is not date or type(end_day) is not date or start_day >= end_day:
        raise ValueError("a nonempty date interval is required")
    if not isinstance(group, str) or not group.strip():
        raise ValueError("group label must be nonempty")
    holdout_day = end_day - timedelta(days=28)
    with conn.transaction():
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
        def fold(day):
            training = read_series(conn, batch_id=batch_id, sku_id=sku_id, warehouse_id=warehouse_id,
                start_day=start_day, end_day=day, known_at=midnight(day))
            truth = read_series(conn, batch_id=batch_id, sku_id=sku_id, warehouse_id=warehouse_id,
                start_day=day, end_day=day+timedelta(days=28), known_at=evaluated_at)
            allowed = (training["status"] == truth["status"] == "eligible"
                       and len(training["days"]) >= MIN_TRAIN)
            return dict(origin_day=day, origin=midnight(day), training=training, truth=truth,
                status="assessable" if allowed else "not_assessable",
                actual=[d["quantity"] for d in truth["days"]] if allowed else None,
                predictions={m: forecast([d["quantity"] for d in training["days"]], method=m,
                                         horizon=28) for m in METHODS} if allowed else None)
        candidates = [fold(start_day+timedelta(days=i)) for i in
                      range(MIN_TRAIN, (holdout_day-start_day).days-28+1, 7)]
        included = [f for f in candidates if f["status"] == "assessable"]
        selection = {str(h): _scores(included, h) for h in HORIZONS}
        chosen = min(METHODS, key=lambda m: selection["28"]["scores"][m]["mae"]) if included else None
        # No holdout evidence or scores participate in selecting chosen.
        holdout = fold(holdout_day) if (holdout_day-start_day).days >= MIN_TRAIN else None
        holdout_scores = {str(h): _scores([holdout] if holdout and
                          holdout["status"] == "assessable" else [], h) for h in HORIZONS}
        result = dict(status="assessable" if chosen and holdout and holdout["status"] == "assessable"
                      else "not_assessable", chosen_method=chosen, selection=selection,
                      candidates=candidates, holdout=holdout, holdout_scores=holdout_scores)
        context = dict(batch_id=batch_id, sku_id=sku_id, warehouse_id=warehouse_id, group=group,
            start_day=start_day, end_day=end_day, evaluated_at=evaluated_at, horizons=HORIZONS,
            min_train=MIN_TRAIN, season_length=7, step=7, holdout_day=holdout_day,
            business_timezone=BUSINESS_TIMEZONE)
        return persist(conn, kind="backtest", context=context, inputs=dict(candidates=candidates,
                       holdout=holdout), result=result, code_version=code_version)
