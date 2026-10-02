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


def manual_demand(conn, prefix, values=(0, 2, 4, 6, 8, 10, 12)):
    context = load_golden(conn, prefix)
    batch = prefix + ":demand"
    with conn.transaction():
        put(conn, "demand_batches", batch_id=batch, version_id="manual-v1",
            business_timezone="America/Los_Angeles", start_day=START, end_day=START + timedelta(days=len(values)),
            assembled_at=ORIGIN + timedelta(days=len(values)+3), status="complete", expected_orders=sum(q > 0 for q in values), expected_days=len(values))
        # Truth = [0,2,4,6,8,10,12]. Hand-entered independently of production functions.
        for i, quantity in enumerate(values):
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
                         start_day=START, end_day=START + timedelta(days=len(values)), known_at=ORIGIN + timedelta(days=len(values)-7))


def manual_plan(conn, runner, prefix):
    """Inventory 10; 5-day forecast 4/day; reservation 3 and confirmed receipt 5.

    Balances [3,4,0,-4,-8], safety 2 => raw need 10; pack 6/MOQ 10 => 12.
    These independent amounts do not come from the planner or scenario generator.
    """
    from inventory_intelligence.reliability import run_checks
    context, demand = manual_demand(conn, prefix, values=[4]*28)
    origin_day = START + timedelta(days=28)
    origin = datetime(2026, 1, 25, 8, tzinfo=timezone.utc)
    with conn.transaction():
        conn.execute("UPDATE operational_fixture.batches SET as_of=%s, observed_at=%s WHERE batch_id IN (%s,%s)",
                     (origin,origin,context["ledger_batch_id"],context["snapshot_batch_id"]))
        conn.execute("UPDATE operational_fixture.snapshots SET as_of=%s, observed_at=%s WHERE batch_id=%s", (origin,origin,context["snapshot_batch_id"]))
        # The original oracle's explicitly future movement stays outside comparison.
        conn.execute("UPDATE operational_fixture.movements SET posting_status='pending' WHERE row_id=%s", (prefix+":after-cutoff",))
        conn.execute("UPDATE operational_fixture.opening_balances SET quantity=1 WHERE row_id=%s", (prefix+":opening:shirt:a",))
        conn.execute("UPDATE operational_fixture.snapshots SET on_hand_qty=10 WHERE row_id=%s", (prefix+":snapshot:shirt:a",))
        supply = prefix+":supply"
        put(conn, "supply_batches", batch_id=supply, version_id="manual-supply-v1",
            sku_id=prefix+":shirt", warehouse_id=prefix+":a", as_of=origin, observed_at=origin,
            status="complete", reservations_complete=True, inbound_complete=True,
            expected_reservations=3, expected_inbound=4)
        put(conn, "policies", row_id=prefix+":policy", batch_id=supply, lead_days=2,
            review_days=3, safety_qty=2, pack_size=6, moq=10, source_recorded_at=origin, observed_at=origin)
        put(conn, "reservations", row_id=prefix+":reservation", batch_id=supply,
            source_system="manual", reservation_id="unshipped-1", remaining_qty=3,
            due_day=origin_day, status="open", source_recorded_at=origin, observed_at=origin)
        for label, due, status in (("fulfilled",0,"fulfilled"),("outside",5,"open")):
            put(conn, "reservations", row_id=prefix+":reservation:"+label, batch_id=supply,
                source_system="manual", reservation_id=label, remaining_qty=100,
                due_day=origin_day+timedelta(days=due), status=status,
                source_recorded_at=origin, observed_at=origin)
        for name, qty, arrival, status in (("confirmed",5,1,"confirmed"),
             ("pending",100,0,"pending"), ("outside",100,5,"confirmed"), ("cancelled",100,0,"cancelled")):
            put(conn, "inbound", row_id=prefix+":"+name, batch_id=supply, source_system="manual",
                inbound_id=name, remaining_qty=qty, arrival_day=origin_day+timedelta(days=arrival),
                status=status, source_recorded_at=origin, observed_at=origin)
    checked = run_checks(runner, **(context | dict(as_of=origin, evaluated_at=origin)))
    if checked["overall_status"] != "pass":
        raise AssertionError("manual Stage 1 control must pass")
    return dict(batch_id=demand["batch_id"], sku_id=demand["sku_id"], warehouse_id=demand["warehouse_id"],
                start_day=START, origin_day=origin_day, method="mean", reliability_run_id=checked["run_id"],
                supply_batch_id=supply)
