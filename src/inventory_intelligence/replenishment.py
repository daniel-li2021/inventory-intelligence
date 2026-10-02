"""Read-only inventory projection and exact whole-piece advisory orders."""

from collections import Counter
from datetime import timedelta
from fractions import Fraction
from math import ceil
from uuid import UUID

from psycopg import sql
from psycopg.rows import dict_row

from inventory_intelligence.demand import midnight, read_series, BUSINESS_TIMEZONE
from inventory_intelligence.forecasting import METHODS
from inventory_intelligence.planning_runs import _idle, persist, prediction
from inventory_intelligence.reliability import _sql


def _inventory(conn, run_id, sku_id, warehouse_id, origin):
    reasons = []
    with conn.cursor(row_factory=dict_row) as cur:
        run = cur.execute("SELECT * FROM reliability.runs WHERE run_id=%s", (run_id,)).fetchone()
        checks = cur.execute("SELECT rule_id, status FROM reliability.check_results WHERE run_id=%s ORDER BY rule_id", (run_id,)).fetchall()
        findings = cur.execute("SELECT * FROM reliability.findings WHERE run_id=%s ORDER BY finding_id", (run_id,)).fetchall()
        if (run is None or run["overall_status"] != "pass" or run["contract_version"] != "1"
            or checks != [dict(rule_id=f"R00{i}", status="pass") for i in range(1,6)] or findings):
            return dict(run=run, checks=checks, findings=findings, reasons=["nonpassing_or_missing_inventory_run"], on_hand=None)
        if run["as_of"] != origin or run["evaluated_at"] != origin:
            reasons.append("inventory_cutoff_or_decision_time_mismatch")
        ledger, snapshot = run["ledger_batch_id"], run["snapshot_batch_id"]
        evidence = {}
        for table in ("batches", "coverage", "opening_balances", "movements", "snapshots"):
            evidence[table] = cur.execute(sql.SQL("SELECT * FROM operational_fixture.{} WHERE batch_id IN (%s,%s) ORDER BY {}")
                .format(sql.Identifier(table), sql.Identifier("batch_id" if table == "batches" else "row_id")), (ledger,snapshot)).fetchall()
        for rows in evidence.values():
            for row in rows:
                if any(row.get(clock) is not None and row[clock] > origin
                       for clock in ("observed_at", "source_recorded_at")):
                    reasons.append("inventory_not_known_at_origin")
        # V1 source owners can write inputs. Reuse its read-only SQL to prevent a
        # changed source quantity being treated as trusted merely from an old pass.
        validation = cur.execute(_sql(), dict(ledger_batch_id=ledger, snapshot_batch_id=snapshot,
            as_of=origin, evaluated_at=origin, max_snapshot_age_hours=24)).fetchone()
        validation = next(iter(validation.values()))
        if validation["findings"] or any(c["status"] != "pass" for c in validation["checks"]):
            reasons.append("current_inventory_revalidation_failed")
        selected = [r for r in evidence["snapshots"] if r["batch_id"] == snapshot and
                    (r["sku_id"], r["warehouse_id"]) == (sku_id,warehouse_id)]
        covered = all(any(r["batch_id"] == b and (r["sku_id"],r["warehouse_id"]) == (sku_id,warehouse_id)
                         for r in evidence["coverage"]) for b in (ledger,snapshot))
        if not covered or len(selected) != 1 or selected[0]["on_hand_qty"] < 0:
            reasons.append("uncovered_or_invalid_stock")
        return dict(run=run, checks=checks, findings=findings, source=evidence,
                    current_validation=validation, reasons=sorted(set(reasons)),
                    on_hand=selected[0]["on_hand_qty"] if not reasons else None)


def _supply(conn, batch_id, sku_id, warehouse_id, origin, origin_day):
    with conn.cursor(row_factory=dict_row) as cur:
        batch = cur.execute("SELECT * FROM planning_input.supply_batches WHERE batch_id=%s", (batch_id,)).fetchone()
        rows = {t: cur.execute(sql.SQL("SELECT * FROM planning_input.{} WHERE batch_id=%s ORDER BY row_id")
                .format(sql.Identifier(t)), (batch_id,)).fetchall() for t in ("reservations", "inbound", "policies")}
    reasons = []
    if batch is None:
        reasons.append("missing_supply_batch")
    elif (batch["status"] != "complete" or batch["as_of"] != origin or batch["observed_at"] > origin
          or (batch["sku_id"],batch["warehouse_id"]) != (sku_id,warehouse_id)
          or not batch["reservations_complete"] or not batch["inbound_complete"]
          or batch["expected_reservations"] != len(rows["reservations"])
          or batch["expected_inbound"] != len(rows["inbound"])):
        reasons.append("incomplete_or_mismatched_supply")
    for table, identity, statuses, day_field, active in (
        ("reservations", "reservation_id", ("open","fulfilled","cancelled"), "due_day", "open"),
        ("inbound", "inbound_id", ("confirmed","pending","cancelled"), "arrival_day", "confirmed")):
        if any(n > 1 for n in Counter((r["source_system"],r[identity]) for r in rows[table]).values()):
            reasons.append("duplicate_"+table)
        for r in rows[table]:
            if r["remaining_qty"] < 0 or r["status"] not in statuses:
                reasons.append("invalid_"+table)
            if r["status"] == active and r[day_field] < origin_day:
                reasons.append("overdue_"+table)
    for records in rows.values():
        if any(r["source_recorded_at"] > origin or r["observed_at"] > origin
               or r["observed_at"] < r["source_recorded_at"] for r in records):
            reasons.append("supply_not_known_at_origin")
    policy = rows["policies"][0] if len(rows["policies"]) == 1 else None
    if (policy is None or any(policy[k] < 1 for k in ("lead_days","review_days","pack_size","moq"))
        or policy["safety_qty"] < 0 or policy["lead_days"]+policy["review_days"] > 366):
        reasons.append("missing_or_invalid_policy")
    return dict(batch=batch, **rows, policy=policy, reasons=sorted(set(reasons)))


def project(*, on_hand, forecasts, reservations, inbound, origin_day, policy):
    """Validated inputs only; incoming orders arrive after L full calendar days."""
    balance = Fraction(on_hand)
    days = []
    for i, quantity in enumerate(forecasts):
        day = origin_day + timedelta(days=i)
        arriving = sum(r["remaining_qty"] for r in inbound if r["status"] == "confirmed" and r["arrival_day"] == day)
        reserved = sum(r["remaining_qty"] for r in reservations if r["status"] == "open" and r["due_day"] == day)
        balance += arriving - reserved - quantity
        days.append(dict(day=day, lead=i+1, forecast=quantity, inbound=arriving,
                         reservations=reserved, balance_without_order=balance))
    lead, pack, moq, safety = (policy[k] for k in ("lead_days","pack_size","moq","safety_qty"))
    need = max([Fraction(0)] + [safety-d["balance_without_order"] for d in days[lead:]])
    whole = ceil(need)
    order = ((max(whole,moq)+pack-1)//pack)*pack if whole else 0
    for i, day in enumerate(days):
        day["balance_with_order"] = day["balance_without_order"] + (order if i >= lead else 0)
    return dict(status="assessable", reasons=[], proposed_order_qty=order,
                unrounded_need=need, whole_piece_need=whole, rounding_extra=order-whole,
                order_arrival_day=origin_day+timedelta(days=lead),
                pre_arrival_shortage_days=[d["day"] for d in days[:lead] if d["balance_without_order"] < 0],
                inventory_position=on_hand+sum(d["inbound"]-d["reservations"] for d in days),
                end_projected_balance=days[-1]["balance_without_order"], projection=days)


def run_plan(conn, *, batch_id, sku_id, warehouse_id, start_day, origin_day,
             method, reliability_run_id, supply_batch_id, code_version="dev"):
    _idle(conn, code_version)
    if method not in METHODS:
        raise ValueError("unknown baseline method")
    reliability_run_id = str(UUID(str(reliability_run_id)))
    if not isinstance(supply_batch_id, str) or not supply_batch_id.strip():
        raise ValueError("supply batch identity must be nonempty")
    origin = midnight(origin_day)
    with conn.transaction():
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
        conn.execute("SET LOCAL TIME ZONE 'UTC'")
        inventory = _inventory(conn, reliability_run_id, sku_id, warehouse_id, origin)
        supply = _supply(conn, supply_batch_id, sku_id, warehouse_id, origin, origin_day)
        training = read_series(conn, batch_id=batch_id, sku_id=sku_id, warehouse_id=warehouse_id,
                               start_day=start_day, end_day=origin_day, known_at=origin)
        policy = supply["policy"]
        horizon = policy["lead_days"]+policy["review_days"] if not supply["reasons"] else None
        forecast_result = prediction(training, method=method, horizon=horizon) if horizon else None
        reasons = inventory["reasons"] + supply["reasons"]
        if forecast_result is None or forecast_result["status"] != "assessable":
            reasons.append("ineligible_or_unavailable_forecast")
        if reasons:
            result = dict(status="not_assessable", reasons=sorted(set(reasons)),
                          proposed_order_qty=None, projection=None)
        else:
            result = project(on_hand=inventory["on_hand"], forecasts=forecast_result["predictions"],
                reservations=supply["reservations"], inbound=supply["inbound"], origin_day=origin_day, policy=policy)
        result.update(inventory=inventory, supply=supply, forecast=forecast_result, training=training)
        context = dict(batch_id=batch_id, sku_id=sku_id, warehouse_id=warehouse_id, start_day=start_day,
            origin_day=origin_day, origin=origin, method=method, horizon=horizon,
            reliability_run_id=reliability_run_id, supply_batch_id=supply_batch_id,
            business_timezone=BUSINESS_TIMEZONE, policy_version="prefix-stock-v1")
        return persist(conn, kind="replenishment", context=context,
            inputs=dict(inventory=inventory, supply=supply, training=training), result=result, code_version=code_version)
