"""Replay gross recorded accepted demand; missing evidence never becomes zero."""

from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from psycopg.rows import dict_row

BUSINESS_TIMEZONE = "America/Los_Angeles"
CALENDAR = ZoneInfo(BUSINESS_TIMEZONE)


def midnight(day):
    if type(day) is not date:
        raise ValueError("business day must be a date")
    return datetime.combine(day, time(), CALENDAR).astimezone(timezone.utc)


def instant(value):
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("knowledge time must be an aware datetime")
    return value.astimezone(timezone.utc)


def _latest(rows, identity):
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row[field] for field in identity)].append(row)
    selected, reasons = [], []
    for group in groups.values():
        revisions = [r["revision"] for r in group]
        if any(r < 1 for r in revisions) or len(revisions) != len(set(revisions)):
            reasons.append("duplicate_or_invalid_revision")
        selected.append(max(group, key=lambda r: r["revision"]))
    return selected, reasons


def read_series(conn, *, batch_id, sku_id, warehouse_id, start_day, end_day, known_at):
    """Read under caller's transaction; return daily values, reasons and raw evidence.

    Replay archives may be assembled after historical origins. Each row's BOTH
    source recording and ingestion timestamps determine historical visibility.
    """
    known_at = instant(known_at)
    if type(start_day) is not date or type(end_day) is not date or start_day >= end_day:
        raise ValueError("a nonempty date interval is required")
    if any(not isinstance(x, str) or not x.strip() for x in (batch_id, sku_id, warehouse_id)):
        raise ValueError("batch and key identities must be nonempty strings")
    with conn.cursor(row_factory=dict_row) as cur:
        batch = cur.execute("SELECT * FROM planning_input.demand_batches WHERE batch_id=%s",
                            (batch_id,)).fetchone()
        counts = cur.execute("""SELECT
            (SELECT count(*) FROM planning_input.order_versions WHERE batch_id=%s) AS orders,
            (SELECT count(*) FROM planning_input.day_observations WHERE batch_id=%s) AS days
            """, (batch_id, batch_id)).fetchone()
        refs = cur.execute("""SELECT s.base_uom FROM operational_fixture.skus s
            JOIN operational_fixture.styles st USING (style_id)
            CROSS JOIN operational_fixture.warehouses w
            WHERE s.sku_id=%s AND w.warehouse_id=%s""", (sku_id, warehouse_id)).fetchone()
        # Fetch all visible identities in this archive: changed SKU/day/warehouse
        # must be detected before filtering to the requested key or interval.
        orders = cur.execute("""SELECT * FROM planning_input.order_versions
            WHERE batch_id=%s AND source_recorded_at <= %s AND observed_at <= %s
            ORDER BY source_system, order_id, line_id, revision, row_id""",
            (batch_id, known_at, known_at)).fetchall()
        days = cur.execute("""SELECT * FROM planning_input.day_observations
            WHERE batch_id=%s AND sku_id=%s AND warehouse_id=%s
            AND business_day >= %s AND business_day < %s
            AND source_recorded_at <= %s AND observed_at <= %s
            ORDER BY business_day, revision, row_id""",
            (batch_id, sku_id, warehouse_id, start_day, end_day, known_at, known_at)).fetchall()
    reasons = []
    if batch is None:
        reasons.append("missing_batch")
    elif (batch["status"] != "complete" or batch["business_timezone"] != BUSINESS_TIMEZONE
          or batch["start_day"] > start_day or batch["end_day"] < end_day
          or batch["expected_orders"] != counts["orders"] or batch["expected_days"] != counts["days"]):
        reasons.append("invalid_or_incomplete_batch")
    if refs is None or refs["base_uom"] != "each":
        reasons.append("unknown_reference_or_unit")
    related = {(r["source_system"], r["order_id"], r["line_id"]) for r in orders
               if (r["sku_id"], r["warehouse_id"]) == (sku_id, warehouse_id)}
    orders = [r for r in orders if (r["source_system"], r["order_id"], r["line_id"]) in related]
    selected, faults = _latest(orders, ("source_system", "order_id", "line_id"))
    reasons.extend(faults)
    identities = defaultdict(set)
    for row in orders:
        identities[row["source_system"], row["order_id"], row["line_id"]].add(
            (row["sku_id"], row["warehouse_id"], row["accepted_at"]))
        if (row["accepted_qty"] < 0 or row["status"] not in ("accepted", "cancelled")
                or row["source_recorded_at"] < row["accepted_at"]
                or row["observed_at"] < row["source_recorded_at"]):
            reasons.append("invalid_order")
    if any(len(keys) != 1 for keys in identities.values()):
        reasons.append("changed_order_identity")
    latest_days, faults = _latest(days, ("business_day",))
    reasons.extend(faults)
    by_day = {r["business_day"]: r for r in latest_days}
    accepted = defaultdict(list)
    for row in selected:
        if (row["sku_id"], row["warehouse_id"]) == (sku_id, warehouse_id):
            accepted[row["accepted_at"].astimezone(CALENDAR).date()].append(row)
    daily = []
    for i in range((end_day - start_day).days):
        day = start_day + timedelta(days=i)
        evidence, lines = by_day.get(day), accepted[day]
        issues = []
        if midnight(day + timedelta(days=1)) > known_at:
            issues.append("unfinished_day")
        if evidence is None:
            issues.append("missing_day_evidence")
        else:
            if evidence["coverage"] != "complete":
                issues.append("incomplete_day")
            if evidence["availability"] != "available":
                issues.append("constrained_or_unknown_availability")
            if evidence["expected_lines"] != len(lines):
                issues.append("line_count_mismatch")
            if (evidence["source_recorded_at"] < midnight(day + timedelta(days=1))
                    or evidence["observed_at"] < evidence["source_recorded_at"]):
                issues.append("invalid_day_time")
        daily.append(dict(day=day, quantity=None if issues or reasons else
                          sum(r["accepted_qty"] for r in lines), reasons=sorted(set(issues)),
                          day_record=evidence, order_records=lines))
    return dict(batch=batch, sku_id=sku_id, warehouse_id=warehouse_id,
                start_day=start_day, end_day=end_day, known_at=known_at,
                business_timezone=BUSINESS_TIMEZONE, reasons=sorted(set(reasons)),
                status="eligible" if not reasons and all(d["quantity"] is not None for d in daily)
                else "not_assessable", days=daily, order_versions=orders, day_versions=days)
