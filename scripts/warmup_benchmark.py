"""Fresh paired traces, costed warmup and nominal/achieved-service diagnostics."""

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random

from scripts.decision_benchmark import canonical, digest
from inventory_intelligence.research_warmup import paired_trial

VERSION = "fresh-warmup-v1"
SEEDS = (1301, 1709, 2027)
FAMILIES = ("constant", "weekly", "zero", "lumpy", "pause", "seasonal_low", "declining", "obsolescence")
BLOCKS = (("selection", 252), ("holdout", 308), ("later_holdout", 364))
WARMUP_DAYS = SCORE_DAYS = 56
CONFIGS = {"mean:fixed0": dict(method="mean"),
           "seasonal_naive:fixed0": dict(method="seasonal_naive"),
           "tsb:fixed0": dict(method="tsb"),
           "tsb:q90": dict(method="tsb", safety_quantile=Fraction(9, 10)),
           "tsb:q95": dict(method="tsb", safety_quantile=Fraction(19, 20))}
PARAMETERS = dict(on_hand=10, lead_days=2, review_days=7, pack_size=2, moq=4,
                  holding_cost=1, backlog_cost=10, order_cost=2, unit_cost=2)


def rng_for(*identity):
    return random.Random(int(digest((VERSION, *identity)), 16))


def observations(family, seed):
    if family not in FAMILIES:
        raise ValueError("unknown fresh demand family")
    if family == "constant":
        return [3] * 420
    if family == "weekly":
        return [0, 1, 2, 3, 4, 5, 6] * 60
    if family == "zero":
        return [0] * 420
    rng = rng_for("demand", family, seed)
    result = []
    for day in range(420):
        probability = Fraction(1, 4)
        if family == "pause" and 252 <= day < 280:
            probability = Fraction(0)
        elif family == "seasonal_low" and day % 112 >= 84:
            probability = Fraction(1, 20)
        elif family == "declining":
            probability = max(Fraction(1, 50), Fraction(2, 5) - Fraction(max(0, day - 196), 560))
        elif family == "obsolescence" and day >= 280:
            probability = Fraction(0)
        draw = Fraction(rng.randrange(10000), 10000)
        result.append(rng.choice((2, 8, 20)) if draw < probability else 0)
    return result


def supplier_trace(family, seed, block):
    rng = rng_for("supplier", family, seed, block)
    return [rng.choice((0, 0, 1, 3)) for _ in range(WARMUP_DAYS + SCORE_DAYS + 12)]


def run():
    root = Path(__file__).resolve().parents[1]
    sources = ("docs/RESEARCH_WARMUP_V1.md", "scripts/warmup_benchmark.py",
               "src/inventory_intelligence/research_warmup.py", "src/inventory_intelligence/decision.py",
               "src/inventory_intelligence/decision_diagnostics.py", "src/inventory_intelligence/intermittent.py",
               "src/inventory_intelligence/forecasting.py", "scripts/decision_benchmark.py")
    report = dict(protocol_version=VERSION, synthetic=True, parameters=PARAMETERS,
        configurations=CONFIGS, source_sha256={name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                                             for name in sources},
        rational_encoding="exact numerator/denominator objects", paths=[], trials=[],
        limits=["Synthetic whole-piece accepted demand; no business savings or population confidence.",
                "Repeated controls and overlapping origins are not independent evidence.",
                "Each origin is a separate trial; warm state is continuous only within that trial.",
                "Full cost includes extra warmup operating time; cold is inactive before scoring.",
                "Forecast target quantile/coverage never guarantees actual inventory service.",
                "No selection, tuning or operational promotion; published paths are consumed."])
    cache = {}
    for family in FAMILIES:
        for seed in SEEDS:
            values = observations(family, seed)
            path_id = f"{family}:{seed}"
            report["paths"].append(dict(id=path_id, family=family, seed=seed, demand=values,
                                        demand_sha256=digest(values)))
            for block, origin in BLOCKS:
                inputs = dict(path_id=path_id, block=block, origin_day=origin,
                    history=values[:origin - WARMUP_DAYS],
                    warmup_demand=values[origin - WARMUP_DAYS:origin],
                    score_demand=values[origin:origin + SCORE_DAYS],
                    daily_delays=supplier_trace(family, seed, block))
                row = dict(inputs=inputs, input_sha256=digest(inputs), comparisons={})
                for name, config in CONFIGS.items():
                    physical = {key: value for key, value in inputs.items()
                                if key in ("history", "warmup_demand", "score_demand", "daily_delays")}
                    key = digest(dict(**physical, **config, **PARAMETERS))
                    if key not in cache:
                        summary, trajectories = paired_trial(**physical, **config, **PARAMETERS)
                        cache[key] = dict(**summary, physical_input_sha256=key,
                            trajectory_sha256={arm: digest(sim) for arm, sim in trajectories.items()})
                    row["comparisons"][name] = cache[key]
                report["trials"].append(row)
    pairs = [pair for row in report["trials"] for pair in row["comparisons"].values()]
    rates = [pair["warm_minus_cold"]["immediate_fill_rate"] for pair in pairs]
    report["summary"] = dict(demand_path_labels=len(report["paths"]),
        distinct_generated_demand_paths=len({path["demand_sha256"] for path in report["paths"]}),
        origin_trials=len(report["trials"]), paired_comparisons=len(pairs),
        unique_paired_simulations=len(cache), logical_arm_simulations=2 * len(pairs),
        supplier_paths=len({digest(row["inputs"]["daily_delays"]) for row in report["trials"]}),
        null_fill_pairs=sum(rate is None for rate in rates),
        warm_improved_fill_pairs=sum(rate is not None and rate > 0 for rate in rates),
        warm_regressed_fill_pairs=sum(rate is not None and rate < 0 for rate in rates),
        warm_equal_fill_pairs=sum(rate == 0 for rate in rates),
        warm_lower_full_cost_pairs=sum(pair["warm_minus_cold"]["full_intervention_cost"] < 0 for pair in pairs))
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
