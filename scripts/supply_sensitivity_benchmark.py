"""Expected-mean-controlled supply variability and signed service interventions."""

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random

from inventory_intelligence.research_warmup import paired_trial, summarize
from scripts.decision_benchmark import canonical, digest
from scripts.warmup_benchmark import observations, PARAMETERS

VERSION = "supply-sensitivity-v1"
SEEDS = (5301, 5709, 6027)
FAMILIES = ("constant", "lumpy", "declining")
PROFILES = {"low": (1, 1, 1, 1, 1, 1), "medium": (0, 0, 1, 1, 2, 2),
            "high": (0, 0, 0, 0, 2, 4)}
CONFIGS = {"mean:fixed0": dict(method="mean"),
           "tsb:fixed0": dict(method="tsb"),
           "tsb:q90": dict(method="tsb", safety_quantile=Fraction(9, 10))}
REFERENCE = "lead5:medium"


def intervention_grid():
    cells = {f"lead{lead}:{profile}": dict(lead_days=lead, delay_profile=profile)
             for lead in (2, 5, 10) for profile in PROFILES}
    cells.update({"initial0": dict(lead_days=5, delay_profile="medium", on_hand=0),
                  "initial40": dict(lead_days=5, delay_profile="medium", on_hand=40),
                  "review1": dict(lead_days=5, delay_profile="medium", review_days=1),
                  "pack1:moq1": dict(lead_days=5, delay_profile="medium", pack_size=1, moq=1)})
    return cells


def fresh_inputs(family, seed):
    values = observations(family, int(digest((VERSION, "demand", seed)), 16))
    rng = random.Random(int(digest((VERSION, "supplier", family, seed)), 16))
    return dict(family=family, seed=seed, history=values[:252],
                warmup_demand=values[252:308], score_demand=values[308:364],
                daily_shocks=[rng.randrange(6) for _ in range(133)])


def trial(physical, config, parameters):
    pair, simulations = paired_trial(**physical, **config, **parameters)
    for arm, sim in simulations.items():
        start = len(physical["warmup_demand"]) if arm == "warm" else 0
        common = summarize(sim, warmup_days=start, score_days=len(physical["score_demand"]),
            on_hand=parameters["on_hand"], unit_cost=parameters["unit_cost"],
            holding_cost=parameters["holding_cost"], common_end_day=start + len(physical["score_demand"]) + 21,
            review_days=parameters["review_days"], horizon=parameters["lead_days"] + parameters["review_days"],
            nominal_quantile=config.get("safety_quantile"))
        pair["arms"][arm]["accounting"] = common["accounting"]
        delays = pair["arms"][arm]["supplier_delays"]
        count = len(range(start, start + len(physical["score_demand"]), parameters["review_days"]))
        offset = start // parameters["review_days"]
        scored = delays[offset:offset + count]
        pair["arms"][arm]["score_supplier_slots"] = dict(count=count,
            mean_delay=Fraction(sum(scored), count), max_delay=max(scored))
    pair["warm_minus_cold"]["full_intervention_cost"] = (
        pair["arms"]["warm"]["accounting"]["full_intervention_cost"]
        - pair["arms"]["cold"]["accounting"]["full_intervention_cost"])
    pair["trajectory_sha256"] = {arm: digest(sim) for arm, sim in simulations.items()}
    return pair


def difference(candidate, reference):
    # These are paired intervention effects, not additive causal categories.
    result = {}
    for key in ("missed_units", "immediate_fill_rate", "cycle_service", "backlog_piece_days"):
        a, b = candidate["score"][key], reference["score"][key]
        result[key] = a - b if a is not None and b is not None else None
    result["full_intervention_cost"] = (candidate["accounting"]["full_intervention_cost"]
                                        - reference["accounting"]["full_intervention_cost"])
    return result


def run():
    root = Path(__file__).resolve().parents[1]
    sources = ("docs/SUPPLY_SENSITIVITY_V1.md", "scripts/supply_sensitivity_benchmark.py",
               "scripts/warmup_benchmark.py", "scripts/decision_benchmark.py",
               "src/inventory_intelligence/research_warmup.py", "src/inventory_intelligence/decision.py",
               "src/inventory_intelligence/decision_diagnostics.py", "src/inventory_intelligence/intermittent.py",
               "src/inventory_intelligence/forecasting.py")
    grid = intervention_grid()
    report = dict(protocol_version=VERSION, synthetic=True, configurations=CONFIGS,
        interventions=grid, delay_profiles=PROFILES, parameters=PARAMETERS,
        common_tail_days=21, source_sha256={name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                                          for name in sources}, paths=[],
        limits=["Synthetic finite-window interventions, not historical supplier or retailer evidence.",
                "Equal expected delay does not imply equal realized slot means.",
                "Review intervention also changes protection horizon and calibration labels.",
                "Signed one-factor effects interact; do not sum them into shortage attribution.",
                "Repeated controls and cost/forecast/start arms are not independent paths.",
                "No automatic selection, tuning or promotion."])
    cache = {}
    for family in FAMILIES:
        for seed in SEEDS:
            inputs = fresh_inputs(family, seed)
            row = dict(inputs=inputs, input_sha256=digest(inputs), cells={})
            for name, intervention in grid.items():
                params = dict(PARAMETERS, **{key: value for key, value in intervention.items() if key != "delay_profile"})
                physical = {key: inputs[key] for key in ("history", "warmup_demand", "score_demand")}
                physical["daily_delays"] = [PROFILES[intervention["delay_profile"]][shock]
                                            for shock in inputs["daily_shocks"]]
                row["cells"][name] = {}
                for model, config in CONFIGS.items():
                    key = digest(dict(physical=physical, config=config, parameters=params))
                    if key not in cache:
                        cache[key] = dict(**trial(physical, config, params), physical_input_sha256=key)
                    row["cells"][name][model] = cache[key]
            row["intervention_deltas_vs_reference"] = {
                name: {model: {arm: difference(pair["arms"][arm], row["cells"][REFERENCE][model]["arms"][arm])
                    for arm in ("cold", "warm")} for model, pair in row["cells"][name].items()}
                for name in grid if name != REFERENCE}
            row["forecast_vs_variability"] = {
                str(lead): {arm: dict(
                    lower_variability_vs_high=difference(row["cells"][f"lead{lead}:low"]["mean:fixed0"]["arms"][arm],
                                                        row["cells"][f"lead{lead}:high"]["mean:fixed0"]["arms"][arm]),
                    tsb_fixed0_vs_mean_at_medium=difference(row["cells"][f"lead{lead}:medium"]["tsb:fixed0"]["arms"][arm],
                                                           row["cells"][f"lead{lead}:medium"]["mean:fixed0"]["arms"][arm]))
                    for arm in ("cold", "warm")} for lead in (2, 5, 10)}
            report["paths"].append(row)
    comparisons = [pair for row in report["paths"] for models in row["cells"].values() for pair in models.values()]
    report["summary"] = dict(path_labels=len(report["paths"]),
        distinct_demand_paths=len({digest(row["inputs"]["history"] + row["inputs"]["warmup_demand"]
            + row["inputs"]["score_demand"]) for row in report["paths"]}),
        intervention_cells=len(grid), paired_comparisons=len(comparisons),
        logical_arm_simulations=2 * len(comparisons), unique_paired_simulations=len(cache))
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
