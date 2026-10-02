"""Deterministic 180-day synthetic archive, separate from manual test oracles."""

from datetime import date, timedelta
from psycopg import sql
from psycopg.pq import TransactionStatus
from inventory_intelligence.demand import midnight, BUSINESS_TIMEZONE

START = date(2025, 7, 6)
END = START + timedelta(days=180)


def load_demand(conn, *, batch_id="demand-v1", source_prefix="clean"):
    if not conn.autocommit or conn.info.transaction_status != TransactionStatus.IDLE:
        raise ValueError("loader requires idle autocommit connection")
    specs = (("constant", "tee-m", "harbor"), ("weekly", "hoodie-l", "harbor"),
             ("intermittent", "jacket-m", "harbor"), ("zero", "tee-l", "harbor"),
             ("blocked", "tee-m", "upland"))
    orders, days = [], []
    for group, sku, warehouse in specs:
        for i in range(180):
            day = START + timedelta(days=i)
            quantity = {"constant": 4, "weekly": (1, 2, 3, 4, 5, 6, 7)[i % 7],
                        "intermittent": 7 if i % 7 == 6 else 0,
                        "zero": 0, "blocked": 2}[group]
            recorded = midnight(day + timedelta(days=1))
            if group == "blocked" and i == 30:
                continue  # A missing day, never zero.
            days.append(dict(row_id=f"{batch_id}:{group}:day:{i}", batch_id=batch_id,
                sku_id=f"{source_prefix}:{sku}", warehouse_id=f"{source_prefix}:{warehouse}",
                business_day=day, revision=1, source_recorded_at=recorded, observed_at=recorded,
                coverage="complete", availability="stockout" if group == "blocked" and i == 40
                else "available", expected_lines=int(quantity > 0)))
            if quantity:
                order = dict(row_id=f"{batch_id}:{group}:order:{i}", batch_id=batch_id,
                    source_system="synthetic-orders", order_id=f"{batch_id}:{group}:{i}",
                    line_id="1", revision=1, sku_id=f"{source_prefix}:{sku}",
                    warehouse_id=f"{source_prefix}:{warehouse}", accepted_qty=quantity,
                    accepted_at=midnight(day) + timedelta(hours=12),
                    source_recorded_at=recorded, observed_at=recorded, status="accepted")
                if group == "blocked" and i == 50:
                    order["observed_at"] = recorded + timedelta(days=10)
                orders.append(order)
                if group == "blocked" and i == 60:
                    orders.append(order | dict(row_id=order["row_id"] + ":duplicate"))
                if group == "blocked" and i == 70:
                    orders.append(order | dict(row_id=order["row_id"] + ":revision", revision=2,
                        accepted_qty=3, source_recorded_at=recorded + timedelta(days=5),
                        observed_at=recorded + timedelta(days=5)))
    batch = dict(batch_id=batch_id, version_id="synthetic-demand-v1",
                 business_timezone=BUSINESS_TIMEZONE, start_day=START, end_day=END,
                 assembled_at=midnight(END) + timedelta(days=10), status="complete",
                 expected_orders=len(orders), expected_days=len(days))
    with conn.transaction():
        # Missing source keys are an error for the loader, not invented references.
        for _, sku, warehouse in specs:
            if not conn.execute("""SELECT 1 FROM operational_fixture.skus s,
                operational_fixture.warehouses w WHERE s.sku_id=%s AND w.warehouse_id=%s""",
                (f"{source_prefix}:{sku}", f"{source_prefix}:{warehouse}")).fetchone():
                raise ValueError("load the matching Stage 1 synthetic scenario first")
        for table, rows in (("demand_batches", [batch]), ("order_versions", orders),
                            ("day_observations", days)):
            columns = list(rows[0])
            query = sql.SQL("INSERT INTO planning_input.{} ({}) VALUES ({})").format(
                sql.Identifier(table), sql.SQL(",").join(map(sql.Identifier, columns)),
                sql.SQL(",").join(sql.Placeholder() for _ in columns))
            with conn.cursor() as cur:
                cur.executemany(query, [tuple(r[c] for c in columns) for r in rows])
    return dict(batch_id=batch_id, start_day=START, end_day=END,
                groups=[dict(group=g, sku_id=f"{source_prefix}:{s}",
                             warehouse_id=f"{source_prefix}:{w}") for g, s, w in specs])
