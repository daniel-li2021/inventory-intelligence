"""Fresh retention controls with full costs and pause-recovery service."""

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random

from inventory_intelligence import safety_retention
from inventory_intelligence.research_warmup import summarize, supplier_slots, window_metrics
from scripts.decision_benchmark import canonical, digest
from scripts.warmup_benchmark import observations, PARAMETERS

VERSION = safety_retention.VERSION
SEEDS = (3301, 3709, 4027)
FAMILIES = ("constant", "zero", "lumpy", "pause", "seasonal_low", "declining", "obsolescence")
CONFIGS = {"mean:fixed0": dict(method="mean"), "tsb:fixed0": dict(method="tsb"),
           "tsb:expanding90": dict(method="tsb", retention="expanding"),
           "tsb:recent90": dict(method="tsb", retention="recent"),
           "tsb:decay90": dict(method="tsb", retention="decay")}


def fresh_inputs(family, seed):
    # Reuse lifecycle shapes, with a distinct nested demand RNG namespace.
    demand_seed = int(digest((VERSION, "demand", seed)), 16)
    values = observations(family, demand_seed)
    rng = random.Random(int(digest((VERSION, "supplier", family, seed)), 16))
    daily = [rng.choice((0, 0, 1, 3)) for _ in range(236)]
    return dict(family=family, seed=seed, demand_seed=demand_seed,
                history=values[:196], warmup_demand=values[196:252],
                score_demand=values[252:420], daily_delays=daily)


def gate(candidate, references):
    failures = []
    c = candidate["score"]
    if c["immediate_fill_rate"] is None or c["immediate_fill_rate"] < Fraction(9, 10):
        failures.append("fill_floor")
    if c["cycle_service"] is None or c["cycle_service"] < Fraction(4, 5):
        failures.append("cycle_floor")
    for name, ref in references.items():
        if candidate["accounting"]["full_intervention_cost"] > ref["accounting"]["full_intervention_cost"] * Fraction(19, 20):
            failures.append(f"{name}:cost_gain_below_5_percent")
        for metric in ("immediate_fill_rate", "cycle_service"):
            if c[metric] is None or ref["score"][metric] is None or c[metric] < ref["score"][metric]:
                failures.append(f"{name}:{metric}_regression_or_undefined")
    return dict(passed=not failures, failures=failures)


def run():
    root = Path(__file__).resolve().parents[1]
    sources = ("docs/SAFETY_RETENTION_V1.md", "scripts/safety_retention_benchmark.py",
        "src/inventory_intelligence/safety_retention.py", "src/inventory_intelligence/research_warmup.py",
        "scripts/warmup_benchmark.py", "scripts/decision_benchmark.py",
        "src/inventory_intelligence/decision.py", "src/inventory_intelligence/decision_diagnostics.py",
        "src/inventory_intelligence/intermittent.py", "src/inventory_intelligence/forecasting.py")
    report = dict(protocol_version=VERSION, synthetic=True, configurations=CONFIGS,
        parameters=PARAMETERS, source_sha256={name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                                            for name in sources}, paths=[],
        limits=["Fresh synthetic controls, not observed business demand or population confidence.",
                "Same forecast across TSB arms; changed residual retention only.",
                "Low safety does not liquidate stock already owned.",
                "Dependent origins and deterministic repeated controls are not independent successes.",
                "Descriptive gates do not select, tune or promote an operational policy."])
    for family in FAMILIES:
        for seed in SEEDS:
            inputs = fresh_inputs(family, seed)
            demand = inputs["warmup_demand"] + inputs["score_demand"]
            delays = supplier_slots(inputs["daily_delays"], start_day=0, demand_days=224,
                                    lead_days=2, review_days=7)
            row = dict(inputs=inputs, input_sha256=digest(inputs), candidates={})
            forecasts = None
            for name, config in CONFIGS.items():
                nominal = Fraction(9, 10) if config.get("retention") else None
                sim = safety_retention.simulate(inputs["history"], demand, **config,
                    **{key: value for key, value in PARAMETERS.items() if key != "unit_cost"}, supplier_delays=delays)
                result = summarize(sim, warmup_days=56, score_days=168,
                    **{key: PARAMETERS[key] for key in ("on_hand", "unit_cost", "holding_cost", "review_days")},
                    common_end_day=236, horizon=9, nominal_quantile=nominal)
                result["blocks"] = {label: window_metrics(sim, start_day=56 + index * 56,
                    end_day=112 + index * 56, review_days=7, horizon=9, nominal_quantile=nominal)
                    for index, label in enumerate(("selection_period", "holdout", "later_holdout"))}
                if family == "pause":
                    result["pause_recovery"] = window_metrics(sim, start_day=84, end_day=112,
                        review_days=7, horizon=9, nominal_quantile=nominal)
                result["safety_reviews"] = [dict(day=review["day"], safety_qty=review["safety_qty"],
                    count=review["calibration"]["count"] if review["calibration"] else None,
                    source_count=review["calibration"]["source_count"] if review["calibration"] else None,
                    effective_sample_count=review["calibration"]["effective_sample_count"] if review["calibration"] else None,
                    quantile_error=review["calibration"]["quantile_error"] if review["calibration"] else None)
                    for review in sim["reviews"] if not review["runoff"]]
                if config["method"] == "tsb":
                    current = [review["forecast"] for review in sim["reviews"] if not review["runoff"]]
                    if forecasts is not None and forecasts != current:
                        raise ValueError("retention changed point forecasts")
                    forecasts = current
                result["physical_input_sha256"] = digest(dict(inputs=inputs, config=config, parameters=PARAMETERS))
                result["trajectory_sha256"] = digest(sim)
                row["candidates"][name] = result
            refs = {name: row["candidates"][name] for name in ("mean:fixed0", "tsb:expanding90")}
            row["gates"] = {name: gate(row["candidates"][name], refs)
                            for name in ("tsb:recent90", "tsb:decay90")}
            report["paths"].append(row)
    report["summary"] = dict(path_labels=len(report["paths"]), simulations=len(report["paths"]) * len(CONFIGS),
        distinct_demand_paths=len({digest(row["inputs"]["history"] + row["inputs"]["warmup_demand"]
            + row["inputs"]["score_demand"]) for row in report["paths"]}),
        passed_gates={name: sum(row["gates"][name]["passed"] for row in report["paths"])
                      for name in ("tsb:recent90", "tsb:decay90")})
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(args.output.name + ".tmp")
    temporary.write_bytes(canonical(report) + b"\n")
    temporary.replace(args.output)
    print(json.dumps(report["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
