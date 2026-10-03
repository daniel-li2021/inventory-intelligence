"""Public sales-proxy service/calibration study; reuse attested local extraction."""

import argparse
from collections import Counter
from fractions import Fraction
import json
from pathlib import Path

from inventory_intelligence import public_sales as sales, sales_safety as study
from scripts.public_sales_adapter import prepare
from scripts.public_sales_benchmark import (END, TRAIN_END, canonical, digest, select_items)


def decode(text):
    def exact(value):
        if set(value) == {"numerator_hex", "denominator_hex"}:
            return Fraction(int(value["numerator_hex"], 16), int(value["denominator_hex"], 16))
        return value
    return json.loads(text, object_hook=exact)


def key(method, quantile, lead, delay):
    return f"{method}:q{int(100 * quantile) if quantile is not None else 'off'}:L{lead}:delay{delay}"


def compact(simulation, residuals):
    """Deduplicate repeated residual receipts without losing origin-level evidence."""
    for review in simulation["reviews"]:
        calibration = review.get("calibration")
        if calibration is not None:
            bundle = {name: calibration[name] for name in ("origins", "errors")}
            identity = digest(bundle)
            if identity in residuals and residuals[identity] != bundle:
                raise ValueError("calibration receipt identity collision")
            residuals[identity] = bundle
            review["calibration"] = {name: value for name, value in calibration.items()
                                     if name not in ("origins", "errors")}
            review["calibration"]["residuals_sha256"] = identity
    return simulation


def aggregate(arms, quantile):
    summaries = [arm["summary"] for arm in arms]
    result = dict(items=len(arms), periods={})
    for period in ("warmup", "holdout"):
        rows = [summary[period] for summary in summaries]
        totals = {name: sum(row[name] for row in rows) for name in
                  ("days", "demand_units", "immediate_units", "eventual_units", "cycles",
                   "shortage_free_cycles", "new_unmet_units", "backlog_piece_days",
                   "on_hand_piece_days", "protection_origins", "protection_covered",
                   "review_count", "safety_sum")}
        positive = [row for row in rows if row["immediate_fill"] is not None]
        totals.update(defined_fill_items=len(positive), undefined_fill_items=len(rows) - len(positive),
            immediate_fill=Fraction(totals["immediate_units"], totals["demand_units"]) if totals["demand_units"] else None,
            macro_immediate_fill=sum((row["immediate_fill"] for row in positive), Fraction(0)) / len(positive) if positive else None,
            eventual_fill=Fraction(totals["eventual_units"], totals["demand_units"]) if totals["demand_units"] else None,
            cycle_service=Fraction(totals["shortage_free_cycles"], totals["cycles"]) if totals["cycles"] else None,
            protection_coverage=Fraction(totals["protection_covered"], totals["protection_origins"]) if totals["protection_origins"] else None,
            pinball_loss=(sum(row["pinball_sum"] for row in rows) / totals["protection_origins"]
                          if quantile is not None and totals["protection_origins"] else None),
            average_safety=Fraction(totals["safety_sum"], totals["review_count"]) if totals["review_count"] else None,
            nominal_fill_pass_items=sum(row["immediate_fill"] >= quantile for row in positive) if quantile is not None else None,
            nominal_cycle_pass_items=sum(row["cycle_service"] >= quantile for row in rows if row["cycle_service"] is not None) if quantile is not None else None,
            nominal_coverage_pass_items=sum(row["protection_coverage"] >= quantile for row in rows if row["protection_coverage"] is not None) if quantile is not None else None)
        result["periods"][period] = totals
    result["costs"] = {period: {name: sum(summary["costs"][period][name] for summary in summaries)
                               for name in ("acquisition", "holding", "backlog", "setup", "total")}
                       for period in ("warmup", "holdout", "settlement")}
    result.update(full_cost=sum(summary["full_cost"] for summary in summaries),
                  mean_full_cost=sum(summary["full_cost"] for summary in summaries) / len(summaries),
                  terminal_stock=sum(summary["terminal_stock"] for summary in summaries),
                  carryover={name: sum(summary["boundary_state"][name] for summary in summaries)
                             for name in ("on_hand", "backlog", "outstanding_qty")})
    return result


def paired(arms, references):
    if len(arms) != len(references):
        raise ValueError("paired arms must have equal item denominators")
    pairs = []
    for arm, reference in zip(arms, references):
        left, right = arm["summary"], reference["summary"]
        a, b = left["holdout"], right["holdout"]
        pairs.append(dict(cost=left["full_cost"] - right["full_cost"],
            fill=a["immediate_fill"] - b["immediate_fill"] if a["immediate_fill"] is not None and b["immediate_fill"] is not None else None,
            cycle=a["cycle_service"] - b["cycle_service"]))
    return dict(pairs=len(pairs), fill_improved=sum(row["fill"] is not None and row["fill"] > 0 for row in pairs),
        fill_regressed=sum(row["fill"] is not None and row["fill"] < 0 for row in pairs),
        fill_equal=sum(row["fill"] == 0 for row in pairs), fill_undefined=sum(row["fill"] is None for row in pairs),
        cost_lower=sum(row["cost"] < 0 for row in pairs), cost_higher=sum(row["cost"] > 0 for row in pairs),
        cost_equal=sum(row["cost"] == 0 for row in pairs), full_cost_difference=sum(row["cost"] for row in pairs),
        lower_cost_without_fill_or_cycle_regression=sum(row["cost"] < 0 and row["fill"] is not None
            and row["fill"] >= 0 and row["cycle"] >= 0 for row in pairs))


def evaluate(adapted, *, progress=None):
    subset = select_items(adapted)
    local = dict(subset=subset, items={}, residuals={})
    configs = {}
    for method in study.METHODS:
        for quantile in study.QUANTILES:
            for lead in study.LEADS:
                for delay in study.DELAYS:
                    configs[key(method, quantile, lead, delay)] = dict(method=method, quantile=quantile,
                                                                     lead_days=lead, delay=delay)
    for number, item in enumerate(subset["selected"], 1):
        values = adapted["series"][item]
        history, demand = values[:TRAIN_END], values[TRAIN_END:END]
        record = dict(history=history, demand=demand, bin=subset["features"][item]["bin"], arms={})
        receipts = {}
        for name, config in configs.items():
            simulation, summary = study.simulate_arm(history, demand, **config)
            origin_receipts = [{k: review[k] for k in ("day", "forecast", "safety_qty", "calibration")}
                               for review in simulation["reviews"] if not review["runoff"]]
            identity = key(config["method"], config["quantile"], config["lead_days"], 0)
            if identity in receipts and digest(receipts[identity]) != digest(origin_receipts):
                raise ValueError("supply regime changed demand calibration/forecast")
            receipts[identity] = origin_receipts
            simulation = compact(simulation, local["residuals"])
            record["arms"][name] = dict(summary=summary, simulation=simulation,
                trajectory_sha256=digest(simulation),
                input_sha256=digest(dict(history=history, demand=demand, config=config)))
        local["items"][item] = record
        if progress is not None:
            progress(number, len(subset["selected"]))
    groups = ("overall", *sorted({record["bin"] for record in local["items"].values()}))
    aggregates = {}
    pairs = {}
    for name, config in configs.items():
        aggregates[name], pairs[name] = {}, {}
        for group in groups:
            records = [record for record in local["items"].values() if group == "overall" or record["bin"] == group]
            arms = [record["arms"][name] for record in records]
            aggregates[name][group] = aggregate(arms, config["quantile"])
            if config["quantile"] is not None:
                baseline = key(config["method"], None, config["lead_days"], config["delay"])
                pairs[name][group] = paired(arms, [record["arms"][baseline] for record in records])
    public = dict(protocol_version=study.VERSION, exploratory_consumed_sales=True,
        observed_sales_only=True, availability="unknown", unconstrained_demand="unknown",
        target="gross positive non-cancelled invoiced units used as modeled backlog obligations",
        subset_sha256=digest(subset), selected_items=len(local["items"]),
        selected_bin_counts=dict(Counter(record["bin"] for record in local["items"].values())),
        configurations=configs, aggregate_scores=aggregates, paired_safety_off=pairs,
        arms=len(local["items"]) * len(configs), paired_contrasts=len(local["items"]) * 16,
        dates=dict(training_end="2011-09-16", warmup_days=56, holdout_start="2011-11-11",
                   holdout_days=28, end_exclusive="2011-12-09", common_settlement_days=15),
        rational_encoding="signed hexadecimal numerator/denominator strings",
        limits=["Consumed public observations; exploratory reuse, not fresh sealed evaluation.",
                "Synthetic supply, stock, backlog and penalties; no historical stockouts/profit.",
                "Nominal empirical demand quantile does not guarantee fill or cycle service.",
                "One retailer, correlated products/dates and four cycles per item; no population confidence.",
                "No model or policy selection/promotion; raw and item traces remain local."])
    return public, local


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw/uci-online-retail"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt, adapted_path = prepare(args.raw_dir)
    root = Path(__file__).resolve().parents[1]
    sources = ("docs/PUBLIC_SAFETY_V1.md", "scripts/public_safety_benchmark.py",
               "src/inventory_intelligence/sales_safety.py", "src/inventory_intelligence/intermittent.py",
               "src/inventory_intelligence/decision.py", "src/inventory_intelligence/decision_diagnostics.py",
               "src/inventory_intelligence/forecasting.py", "scripts/public_sales_benchmark.py")
    parent_path = root / "docs/review/public-sales-forecast-v1.json"
    parent = decode(parent_path.read_text())
    attestation = dict(archive_sha256=receipt["archive_sha256"], adapter_sha256=receipt["transform_sha256"],
        adapter_artifact_sha256=receipt["artifact_sha256"], parent_forecast_sha256=sales.sha256_file(parent_path),
        source_sha256={name: sales.sha256_file(root / name) for name in sources})
    if any(parent[name] != attestation[name] for name in ("archive_sha256", "adapter_sha256", "adapter_artifact_sha256")):
        raise ValueError("parent forecast and safety input attestation disagree")
    adapted = json.loads(adapted_path.read_text())
    subset = select_items(adapted)
    if digest(subset) != parent["subset_sha256"]:
        raise ValueError("parent forecast and safety subset disagree")
    cache_path = args.raw_dir / f"safety-{digest(attestation)[:12]}.json"
    if cache_path.exists():
        if args.output.exists():
            accepted = decode(args.output.read_text())
            if (accepted.get("source_sha256") == attestation["source_sha256"]
                    and accepted.get("local_evidence_sha256") != sales.sha256_file(cache_path)):
                raise ValueError("local safety bytes disagree with published receipt")
        cached = decode(cache_path.read_text())
        if cached["attestation"] != attestation or digest(cached["payload"]) != cached["payload_sha256"]:
            raise ValueError("accepted local safety evidence changed")
        public, local = cached["payload"]["public"], cached["payload"]["local"]
    else:
        public, local = evaluate(adapted, progress=lambda done, total: print(f"items {done}/{total}", flush=True))
        public.update(attestation, attribution=sales.ATTRIBUTION, source_url=sales.SOURCE_URL,
                      license_url=sales.LICENSE_URL,
                      acquisition=json.loads((args.raw_dir / "source-manifest.json").read_text()))
        payload = dict(public=public, local=local)
        cached = dict(attestation=attestation, payload=payload, payload_sha256=digest(payload))
        temporary = cache_path.with_name(cache_path.name + ".tmp")
        temporary.write_bytes(canonical(cached) + b"\n"); temporary.replace(cache_path)
    public["local_evidence_sha256"] = sales.sha256_file(cache_path)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(args.output.name + ".tmp")
    temporary.write_bytes(canonical(public) + b"\n"); temporary.replace(args.output)
    print(json.dumps(dict(items=public["selected_items"], arms=public["arms"], pairs=public["paired_contrasts"])))


if __name__ == "__main__":
    main()
