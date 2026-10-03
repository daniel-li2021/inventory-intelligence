"""Verify cached real-sales arms without refitting models or rerunning simulation."""

import argparse
from fractions import Fraction
from math import ceil
from pathlib import Path
import json

from inventory_intelligence import public_sales as sales
from scripts.public_sales_adapter import prepare
from scripts.public_sales_benchmark import END, TRAIN_END, digest, select_items
from scripts.public_safety_benchmark import aggregate, decode, key, paired


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit_arm(record, arm, config, residuals):
    simulation, summary = arm["simulation"], arm["summary"]
    demand, history = record["demand"], record["history"]
    require(digest(simulation) == arm["trajectory_sha256"], "trajectory bytes changed")
    require(digest(dict(history=history, demand=demand, config=config)) == arm["input_sha256"], "input changed")
    stock = outstanding = 0
    queue, arriving = {}, {}
    days = simulation["days"]
    require([row["day"] for row in days] == list(range(len(days))), "day calendar changed")
    require(len(days) == 84 + config["lead_days"] + config["delay"] + 7, "native closure changed")
    for row in days:
        day = row["day"]
        require(all(type(row[name]) is int and row[name] >= 0 for name in
                    ("order_qty", "receipts", "on_hand", "backlog", "outstanding_qty", "fulfilled_units")), "invalid quantities")
        require(row["receipts"] == arriving.get(day, 0), "receipt timing changed")
        stock += row["receipts"]
        outstanding -= row["receipts"]
        new = demand[day] if day < 84 else 0
        require(row["new_demand"] == new and row["prior_demand"] == 0, "sales/obligation mapping changed")
        if new:
            queue[day] = new
        filled = immediate = 0
        for fulfillment in row["fulfillments"]:
            due, quantity = fulfillment["due_day"], fulfillment["quantity"]
            require(bool(queue) and due == min(queue), "FIFO changed")
            require(fulfillment["kind"] == "new" and fulfillment["id"] == f"new:{due}", "obligation identity changed")
            require(quantity == min(stock, queue[due]) and quantity > 0, "fulfillment changed")
            stock -= quantity; queue[due] -= quantity; filled += quantity
            immediate += quantity if due == day else 0
            if not queue[due]:
                del queue[due]
        require(stock == row["on_hand"] and sum(queue.values()) == row["backlog"], "inventory/backlog conservation failed")
        require(not (stock and queue), "available stock left with due backlog")
        require(filled == row["fulfilled_units"] and immediate == row["immediately_filled_units"], "service receipts changed")
        require(row["newly_unmet_units"] == new - immediate and row["shortage"] == bool(queue), "shortage receipts changed")
        order = row["order_qty"]
        if order:
            require(order >= 4 and order % 2 == 0, "pack/MOQ changed")
            arrival = day + config["lead_days"] + config["delay"]
            arriving[arrival] = arriving.get(arrival, 0) + order
            outstanding += order
        require(outstanding == row["outstanding_qty"], "pipeline conservation failed")
        require(row["holding_cost"] == stock and row["backlog_cost"] == 10 * sum(queue.values())
                and row["order_cost"] == 2 * bool(order), "rate evidence changed")
    require(not queue and not outstanding, "unsettled obligations/pipeline")
    require(summary["accounting_days"] == 99 and summary["native_days"] == len(days), "common closure changed")
    require(summary["terminal_stock"] == stock, "terminal stock changed")
    require(summary["boundary_state"] == {name: days[55][name] for name in
            ("on_hand", "backlog", "outstanding_qty")}, "warm state changed")
    full = 0
    for period, start, end in (("warmup", 0, 56), ("holdout", 56, 84), ("settlement", 84, len(days))):
        window = days[start:end]
        holding = sum(row["on_hand"] for row in window) + ((99 - len(days)) * stock if period == "settlement" else 0)
        cost = dict(acquisition=2 * sum(row["order_qty"] for row in window), holding=holding,
                    backlog=10 * sum(row["backlog"] for row in window), setup=2 * sum(bool(row["order_qty"]) for row in window))
        cost["total"] = sum(cost.values()); full += cost["total"]
        require(summary["costs"][period] == cost, "paid period cost changed")
        if period == "settlement":
            continue
        result = summary[period]
        require(result["days"] == end - start, "period length changed")
        units = sum(demand[start:end]); immediate = sum(row["immediately_filled_units"] for row in window)
        require(result["demand_units"] == units and result["immediate_units"] == immediate
                and result["eventual_units"] == units, "period service denominator changed")
        require(result["immediate_fill"] == (Fraction(immediate, units) if units else None), "period fill changed")
        require(result["eventual_fill"] == (Fraction(1) if units else None), "eventual fill changed")
        cycle_starts = list(range(start, end - 6, 7))
        clear = sum(not any(row["backlog"] for row in days[day:day + 7]) for day in cycle_starts)
        require(result["cycles"] == len(cycle_starts) and result["shortage_free_cycles"] == clear
                and result["cycle_service"] == Fraction(clear, len(cycle_starts)), "period cycle denominator changed")
        require(result["new_unmet_units"] == units - immediate
                and result["backlog_piece_days"] == sum(row["backlog"] for row in window)
                and result["on_hand_piece_days"] == sum(row["on_hand"] for row in window), "period exposure changed")
        horizon = config["lead_days"] + 7
        origins = [row for row in simulation["reviews"] if start <= row["day"] <= end - horizon]
        covered = 0; pinball = Fraction(0)
        for origin in origins:
            target = ceil(sum(origin["forecast"]) + origin["safety_qty"])
            require(target == origin["protection_target"], "target changed")
            actual = sum(demand[origin["day"]:origin["day"] + horizon])
            covered += actual <= target
            if config["quantile"] is not None:
                error = actual - target; q = config["quantile"]
                pinball += q * error if error >= 0 else (q - 1) * error
        require(result["protection_origins"] == len(origins) and result["protection_covered"] == covered
                and result["protection_coverage"] == Fraction(covered, len(origins)), "coverage denominator changed")
        expected_loss = pinball / len(origins) if config["quantile"] is not None else None
        require(result["pinball_loss"] == expected_loss
                and result["pinball_sum"] == (pinball if config["quantile"] is not None else None), "pinball changed")
        reviews = [row for row in simulation["reviews"] if start <= row["day"] < end]
        require(result["review_count"] == len(reviews)
                and result["safety_sum"] == sum(row["safety_qty"] for row in reviews)
                and result["average_safety"] == Fraction(result["safety_sum"], len(reviews)), "safety denominator changed")
    require(summary["full_cost"] == full, "full cost changed")
    for review in simulation["reviews"]:
        if review["runoff"]:
            require(not review["forecast"] and review["target"] == 0, "runoff policy changed")
            continue
        calibrated = review["calibration"]
        if config["quantile"] is None:
            require(calibrated is None and review["safety_qty"] == 0, "safety-off changed")
        else:
            bundle = residuals[calibrated["residuals_sha256"]]
            require(digest(bundle) == calibrated["residuals_sha256"], "residual receipt changed")
            horizon = config["lead_days"] + 7
            require(bundle["origins"] == list(range(28, len(history) + review["day"] - horizon + 1, horizon)), "incomplete/future calibration labels")
            errors = bundle["errors"]; q = config["quantile"]
            require(len(errors) == calibrated["count"] and len(errors) >= 8, "calibration denominator changed")
            error_q = sorted(errors)[ceil(q * len(errors)) - 1]
            require(calibrated["quantile_error"] == error_q and review["safety_qty"] == max(0, ceil(error_q)), "quantile rank changed")


def audit(report_path, raw_dir):
    public = decode(report_path.read_text())
    receipt, adapted_path = prepare(raw_dir)
    attestation = {name: public[name] for name in ("archive_sha256", "adapter_sha256", "adapter_artifact_sha256", "parent_forecast_sha256", "source_sha256")}
    cache_path = raw_dir / f"safety-{digest(attestation)[:12]}.json"
    require(sales.sha256_file(cache_path) == public["local_evidence_sha256"], "local bytes changed")
    cached = decode(cache_path.read_text()); payload = cached["payload"]
    require(cached["attestation"] == attestation and digest(payload) == cached["payload_sha256"], "cache attestation changed")
    require(payload["public"] == {k: v for k, v in public.items() if k != "local_evidence_sha256"}, "public receipt changed")
    root = Path(__file__).resolve().parents[1]
    require(sales.sha256_file(root / "docs/review/public-sales-forecast-v1.json") == public["parent_forecast_sha256"], "parent report changed")
    require(all(sales.sha256_file(root / name) == value for name, value in public["source_sha256"].items()), "current code differs from pinned study sources")
    adapted = json.loads(adapted_path.read_text())
    local = payload["local"]
    require(digest(select_items(adapted)) == public["subset_sha256"] == digest(local["subset"]), "training subset changed")
    require(receipt["artifact_sha256"] == public["adapter_artifact_sha256"], "extraction changed")
    require(receipt["archive_sha256"] == public["archive_sha256"]
            and receipt["transform_sha256"] == public["adapter_sha256"], "source lineage changed")
    require(json.loads((raw_dir / "source-manifest.json").read_text()) == public["acquisition"], "acquisition receipt changed")
    require(set(local["items"]) == set(local["subset"]["selected"]), "selected item identities changed")
    arms = 0
    for item, record in local["items"].items():
        require(record["history"] == adapted["series"][item][:TRAIN_END]
                and record["demand"] == adapted["series"][item][TRAIN_END:END], "local observations changed")
        require(record["bin"] == local["subset"]["features"][item]["bin"], "training segment changed")
        for name, config in public["configurations"].items():
            audit_arm(record, record["arms"][name], config, local["residuals"]); arms += 1
    for name, config in public["configurations"].items():
        for group, expected in public["aggregate_scores"][name].items():
            records = [record for record in local["items"].values() if group == "overall" or record["bin"] == group]
            current = [record["arms"][name] for record in records]
            require(aggregate(current, config["quantile"]) == expected, "public aggregate differs from validated arms")
            if config["quantile"] is not None:
                baseline = key(config["method"], None, config["lead_days"], config["delay"])
                require(paired(current, [record["arms"][baseline] for record in records]) == public["paired_safety_off"][name][group], "paired summary changed")
    require(arms == public["arms"] == 768 and public["paired_contrasts"] == 512, "arm denominator changed")
    return dict(arms=arms, pairs=512, public_bytes=report_path.stat().st_size,
                local_bytes=cache_path.stat().st_size, model_refits=0, simulation_replays=0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=Path("docs/review/public-sales-safety-v1.json"))
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw/uci-online-retail"))
    args = parser.parse_args()
    print(json.dumps(audit(args.report, args.raw_dir), sort_keys=True))
