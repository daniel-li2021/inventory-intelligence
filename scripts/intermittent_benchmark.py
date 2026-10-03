"""Frozen intermittent decision experiment with exact, input-keyed reuse."""

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random

from decision_benchmark import canonical, digest, eligible, exact, promotion


VERSION = "intermittent-research-v1"
SEEDS = (101, 211, 307)
FAMILIES = ("constant", "weekly", "zero", "intermittent", "lumpy", "declining", "obsolescence")
BASELINES = ("naive", "mean", "seasonal_naive", "zero")
PARAMETERS = dict(on_hand=10, lead_days=2, review_days=7, safety_qty=0,
                  pack_size=2, moq=4, review_phase=0, commitments=[], inbound=[])
COSTS = ((1, 10, 2), (3, 2, 5))


def config_grid():
    models = [(name, Fraction(1, 5), Fraction(1, 5)) for name in BASELINES]
    models += [("croston", Fraction(1, 5), Fraction(1, 5)),
               ("sba", Fraction(1, 5), Fraction(1, 5)),
               ("sba", Fraction(1, 2), Fraction(1, 5))]
    models += [("tsb", alpha, beta) for alpha in (Fraction(1, 5), Fraction(1, 2))
               for beta in (Fraction(1, 5), Fraction(1, 2))]
    configs = {}
    for method, alpha, beta in models:
        model_id = method if method in BASELINES else f"{method}:a{alpha}"
        if method == "tsb":
            model_id += f":b{beta}"
        for quantile in (None, Fraction(9, 10), Fraction(19, 20)):
            config_id = model_id + (":fixed0" if quantile is None else f":q{quantile}")
            configs[config_id] = dict(method=method, alpha=alpha, beta=beta,
                                      safety_quantile=quantile)
    return configs


def observations(family, seed):
    if family == "constant":
        return [3] * 224
    if family == "weekly":
        return [0, 1, 2, 3, 4, 5, 6] * 32
    if family == "zero":
        return [0] * 224
    if family not in FAMILIES:
        raise ValueError(f"unknown family: {family}")
    rng = random.Random(seed)
    result = []
    for day in range(224):
        if family == "intermittent":
            probability, sizes = Fraction(3, 20), (1, 2, 3)
        elif family == "lumpy":
            probability, sizes = Fraction(1, 5), (3, 8, 20)
        elif family == "declining":
            probability = max(Fraction(1, 20), Fraction(2, 5) - Fraction(day, 640))
            sizes = (3, 8, 20)
        else:
            probability = Fraction(2, 5) if day < 112 else Fraction(1, 5) if day < 182 else Fraction(0)
            sizes = (3, 8, 20)
        draw = Fraction(rng.randrange(10000), 10000)
        result.append(rng.choice(sizes) if draw < probability else 0)
    return result


def select(scores, configs):
    candidates = [key for key in configs if eligible(scores[key])]
    return min(candidates, key=lambda key: scores[key]["total_cost"]) if candidates else None


def compare(candidate, reference, holdout):
    if reference is None:
        return dict(passed=False, failures=["no_selection_eligible_baseline"], reference=None)
    if candidate is None:
        result = promotion(None, {})
    else:
        result = promotion("candidate", {"candidate": holdout[candidate], "mean": holdout[reference]})
    result["reference"] = reference
    return result


def summarize(simulation):
    if simulation["terminal"]["backlog"] or simulation["terminal"]["outstanding_qty"]:
        raise ValueError("simulator did not settle terminal obligations")
    exposures = {}
    for split, scored in (("scored", True), ("runoff", False)):
        days = [day for day in simulation["days"] if day["scored"] == scored]
        exposures[split] = dict(on_hand=sum(day["on_hand"] for day in days),
                               backlog=sum(day["backlog"] for day in days),
                               orders=sum(day["order_qty"] > 0 for day in days))
    return dict(metrics=simulation["metrics"], terminal=simulation["terminal"],
                reviews=simulation["reviews"], exposures=exposures)


def reprice(summary, costs):
    metrics = dict(summary["metrics"])
    for split, exposure in summary["exposures"].items():
        metrics[f"{split}_cost"] = Fraction(exposure["on_hand"] * costs["holding_cost"]
                                            + exposure["backlog"] * costs["backlog_cost"]
                                            + exposure["orders"] * costs["order_cost"])
    metrics["total_cost"] = metrics["scored_cost"] + metrics["runoff_cost"]
    return metrics


def self_check():
    configs = config_grid()
    assert len(configs) == 33 and list(configs)[:3] == ["naive:fixed0", "naive:q9/10", "naive:q19/20"]
    scores = {key: dict(total_cost=100, immediate_fill_rate=Fraction(9, 10),
                        cycle_service=Fraction(4, 5)) for key in configs}
    assert select(scores, configs) == "naive:fixed0"
    scores["naive:q9/10"]["total_cost"] = 95
    chosen = select(scores, configs)
    assert chosen == "naive:q9/10" and compare(chosen, "mean:fixed0", scores)["passed"]
    assert compare(chosen, "mean:fixed0", scores)["relative_cost_reduction"] == Fraction(1, 20)
    assert not compare(chosen, None, scores)["passed"]
    scores[chosen]["cycle_service"] = Fraction(79, 100)
    assert not compare(chosen, "mean:fixed0", scores)["passed"]
    assert chosen == "naive:q9/10"  # Holdout outcomes cannot replace selection.
    summary = dict(metrics={"scored_cost": 999}, exposures={
        "scored": dict(on_hand=3, backlog=2, orders=1),
        "runoff": dict(on_hand=1, backlog=0, orders=0)})
    priced = reprice(summary, dict(holding_cost=3, backlog_cost=2, order_cost=5))
    assert priced["scored_cost"] == 18 and priced["total_cost"] == 21
    assert summary["metrics"]["scored_cost"] == 999  # Cache remains immutable.
    for family in FAMILIES:
        values = observations(family, 101)
        assert len(values) == 224 and all(type(value) is int and value >= 0 for value in values)
        assert values == observations(family, 101)
    assert observations("obsolescence", 101)[182:] == [0] * 42


def run(simulator=None):
    if simulator is None:
        from inventory_intelligence.intermittent import simulate
        simulator = simulate
    root = Path(__file__).resolve().parents[1]
    sources = ("scripts/intermittent_benchmark.py", "scripts/decision_benchmark.py",
               "src/inventory_intelligence/decision.py", "src/inventory_intelligence/intermittent.py",
               "src/inventory_intelligence/forecasting.py", "docs/CONTRACT_INTERMITTENT_V1.md")
    configs = config_grid()
    baseline_configs = [key for key, value in configs.items() if value["method"] in BASELINES]
    new_configs = [key for key, value in configs.items() if value["method"] not in BASELINES]
    cache = {}
    logical_runs = 0
    report = dict(protocol_version=VERSION, configurations=configs, configuration_order=list(configs),
                  source_sha256={name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                                 for name in sources},
                  rational_encoding="exact numerator/denominator objects",
                  limitations=["synthetic finite-window penalties, no business-savings claim",
                               "three seeds, correlated cycles and repeated controls; no population confidence",
                               "empirical target coverage is separate from actual inventory service",
                               "nominal horizon does not adjust calibration for hidden supplier delays",
                               "no pooled/global champion decision"], scenarios=[])
    for family in FAMILIES:
        for seed in SEEDS:
            values = observations(family, seed)
            rng = random.Random(seed + 2000)
            hidden = [rng.choice((0, 1, 2)) for _ in range(10)]
            for delay_name, delays in (("fixed", [0] * 10), ("hidden", hidden)):
                split_results = {}
                cached_evidence = {}
                for split, history, demand in (("selection", values[:112], values[112:168]),
                                               ("holdout", values[:168], values[168:])):
                    split_results[split] = {}
                    cached_evidence[split] = {}
                    for key, config in configs.items():
                        physical_inputs = dict(history=history, demand=demand, parameters=PARAMETERS,
                                               supplier_delays=delays, configuration=config)
                        input_hash = digest(physical_inputs)
                        if input_hash not in cache:
                            cache[input_hash] = summarize(simulator(history, demand, **PARAMETERS,
                                                                   **config, supplier_delays=delays,
                                                                   holding_cost=1, backlog_cost=1, order_cost=1))
                        cached_evidence[split][key] = cache[input_hash]
                        split_results[split][key] = dict(physical_input_sha256=input_hash)
                for holding, backlog, setup in COSTS:
                    costs = dict(holding_cost=holding, backlog_cost=backlog, order_cost=setup)
                    inputs = dict(family=family, seed=seed, generator=VERSION,
                                  train=values[:112], selection=values[112:168], holdout=values[168:],
                                  selection_history=values[:112], holdout_history=values[:168],
                                  parameters=PARAMETERS, delay_regime=delay_name, supplier_delays=delays,
                                  costs=costs, configuration_order=list(configs))
                    row = dict(inputs=inputs, input_sha256=digest(inputs), selection={}, holdout={})
                    for split in ("selection", "holdout"):
                        for key, cached in cached_evidence[split].items():
                            metrics = reprice(cached, costs)
                            row[split][key] = dict(metrics=metrics, terminal=cached["terminal"],
                                                   service_eligible=eligible(metrics),
                                                   **split_results[split][key])
                            logical_runs += 1
                    selection = {key: value["metrics"] for key, value in row["selection"].items()}
                    holdout = {key: value["metrics"] for key, value in row["holdout"].items()}
                    chosen = select(selection, configs)
                    baseline = select(selection, baseline_configs)
                    new = select(selection, new_configs)
                    row["selected"] = dict(overall=chosen, baseline=baseline, new_method=new)
                    row["comparisons"] = dict(overall_vs_fixed_mean=compare(chosen, "mean:fixed0", holdout),
                                              overall_vs_selected_baseline=compare(chosen, baseline, holdout),
                                              new_vs_selected_baseline=compare(new, baseline, holdout))
                    selected_ids = [key for key in configs if key in (chosen, baseline, new, "mean:fixed0")]
                    row["review_evidence"] = {
                        split: {key: cached_evidence[split][key]["reviews"] for key in selected_ids}
                        for split in ("selection", "holdout")}
                    report["scenarios"].append(row)
    report["summary"] = dict(cells=len(report["scenarios"]), configurations=len(configs),
                              candidate_split_results=logical_runs, unique_simulations=len(cache),
                              simulation_cache_hits=logical_runs - len(cache),
                              no_overall_selection=sum(row["selected"]["overall"] is None
                                                       for row in report["scenarios"]),
                              both_reference_passes=sum(
                                  row["comparisons"]["overall_vs_fixed_mean"]["passed"]
                                  and row["comparisons"]["overall_vs_selected_baseline"]["passed"]
                                  for row in report["scenarios"]),
                              new_vs_baseline_passes=sum(row["comparisons"]["new_vs_selected_baseline"]["passed"]
                                                         for row in report["scenarios"]))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    self_check()
    report = run()
    encoded = canonical(report).decode() + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(args.output.name + ".tmp")
    temporary.write_text(encoded)
    temporary.replace(args.output)
    print(json.dumps(report["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
