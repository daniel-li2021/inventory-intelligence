"""Independent hand-supplied inputs; never uses the demand scenario generator."""

from datetime import date, datetime, timedelta, timezone
from psycopg import sql
from tests.golden import load_golden

START = date(2025, 12, 28)
# Midnight Pacific in winter, explicitly supplied rather than using adapter calendar.
ORIGIN = datetime(2026, 1, 4, 8, tzinfo=timezone.utc)


def put(conn, table, **row):
    conn.execute(sql.SQL("INSERT INTO planning_input.{} ({}) VALUES ({})").format(
        sql.Identifier(table), sql.SQL(",").join(map(sql.Identifier, row)),
        sql.SQL(",").join(sql.Placeholder() for _ in row)), tuple(row.values()))


def manual_demand(conn, prefix):
    context = load_golden(conn, prefix)
    batch = prefix + ":demand"
    with conn.transaction():
        put(conn, "demand_batches", batch_id=batch, version_id="manual-v1",
            business_timezone="America/Los_Angeles", start_day=START, end_day=START + timedelta(days=7),
            assembled_at=ORIGIN + timedelta(days=10), status="complete", expected_orders=6, expected_days=7)
        # Truth = [0,2,4,6,8,10,12]. Hand-entered independently of production functions.
        for i, quantity in enumerate((0, 2, 4, 6, 8, 10, 12)):
            accepted = datetime(2025, 12, 28, 20, tzinfo=timezone.utc) + timedelta(days=i)
            observed = datetime(2025, 12, 29, 8, tzinfo=timezone.utc) + timedelta(days=i)
            put(conn, "day_observations", row_id=f"{prefix}:day:{i}", batch_id=batch,
                sku_id=prefix + ":shirt", warehouse_id=prefix + ":a", business_day=START + timedelta(days=i),
                revision=1, source_recorded_at=observed, observed_at=observed,
                coverage="complete", availability="available", expected_lines=int(quantity > 0))
            if quantity:
                put(conn, "order_versions", row_id=f"{prefix}:order:{i}", batch_id=batch,
                    source_system="manual", order_id=f"{prefix}:{i}", line_id="1", revision=1,
                    sku_id=prefix + ":shirt", warehouse_id=prefix + ":a", accepted_at=accepted,
                    source_recorded_at=accepted, observed_at=accepted, accepted_qty=quantity, status="accepted")
    return context, dict(batch_id=batch, sku_id=prefix + ":shirt", warehouse_id=prefix + ":a",
                         start_day=START, end_day=START + timedelta(days=7), known_at=ORIGIN)
