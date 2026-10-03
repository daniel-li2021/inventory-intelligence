"""Frozen synthetic decision experiment; no database, API or production selection."""

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random

from inventory_intelligence.forecasting import METHODS


VERSION = "decision-benchmark-v1"
CANDIDATES = (*METHODS, "zero")
SEEDS = (11, 29, 47)
FAMILIES = ("constant", "weekly", "zero", "lumpy", "obsolescence")
PARAMETERS = dict(on_hand=10, lead_days=2, review_days=7, safety_qty=0,
                  pack_size=2, moq=4, review_phase=0, commitments=[], inbound=[])
COSTS = ((1, 10, 2), (3, 2, 5))


def exact(value):
    if isinstance(value, Fraction):
        return dict(numerator=value.numerator, denominator=value.denominator)
    raise TypeError(f"unsupported JSON value: {type(value).__name__}")


def canonical(value):
    return json.dumps(value, default=exact, sort_keys=True,
                      separators=(",", ":")).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def observations(family, seed):
    rng = random.Random(seed)
    if family == "constant":
        return [3] * 168
    if family == "weekly":
        return [0, 1, 2, 3, 4, 5, 6] * 24
    if family == "zero":
        return [0] * 168
    if family == "lumpy":
        return [rng.choice((0, 0, 0, 0, 0, 2, 8, 16)) for _ in range(168)]
    if family == "obsolescence":
        return [4] * 56 + [2] * 28 + [1] * 35 + [0] * 49
    raise ValueError(f"unknown family: {family}")


def eligible(metrics):
    return (metrics["immediate_fill_rate"] is not None
            and metrics["cycle_service"] is not None
            and metrics["immediate_fill_rate"] >= Fraction(9, 10)
            and metrics["cycle_service"] >= Fraction(4, 5))


def select(selection):
    candidates = [method for method in CANDIDATES if eligible(selection[method])]
    return min(candidates, key=lambda method: selection[method]["total_cost"]) if candidates else None


def promotion(method, holdout):
    if method is None:
        return dict(passed=False, failures=["no_selection_eligible_method"])
    candidate, reference = holdout[method], holdout["mean"]
    failures = []
    reference_cost = reference["total_cost"]
    if reference_cost == 0 or candidate["total_cost"] > reference_cost * Fraction(19, 20):
        failures.append("cost_reduction_below_5_percent_or_zero_reference")
    if not eligible(candidate):
        failures.append("holdout_service_floor")
    differences = dict(total_cost=candidate["total_cost"] - reference_cost)
    for key in ("immediate_fill_rate", "cycle_service"):
        left, right = candidate[key], reference[key]
        differences[key] = left - right if left is not None and right is not None else None
        if differences[key] is None or differences[key] < 0:
            failures.append(f"{key}_regression_or_unavailable")
    return dict(passed=not failures, failures=failures, reference="mean",
                differences=differences,
                relative_cost_reduction=(reference_cost - candidate["total_cost"]) / reference_cost
                if reference_cost else None)


def self_check():
    """Independent expected choices; no simulator-derived expected outcomes."""
    assert digest({"b": 2, "a": 1}) == digest({"a": 1, "b": 2})
    assert digest([1, 2]) != digest([2, 1])
    scores = {method: dict(total_cost=100, immediate_fill_rate=Fraction(9, 10),
                          cycle_service=Fraction(4, 5)) for method in CANDIDATES}
    assert select(scores) == "naive"  # Frozen method order breaks exact ties.
    scores["naive"]["immediate_fill_rate"] = Fraction(89, 100)
    assert select(scores) == "mean"
    scores["seasonal_naive"]["total_cost"] = 95
    chosen = select(scores)
    assert chosen == "seasonal_naive"
    assert promotion(chosen, scores)["passed"]  # Exactly five percent passes.
    scores[chosen]["cycle_service"] = Fraction(79, 100)
    assert not promotion(chosen, scores)["passed"]
    assert chosen == "seasonal_naive"  # Holdout failure cannot reselect a method.
    zero = {method: dict(total_cost=0, immediate_fill_rate=None, cycle_service=1)
            for method in CANDIDATES}
    assert select(zero) is None
    assert not promotion("mean", zero)["passed"]
    for family in FAMILIES:
        assert len(observations(family, 11)) == 168
    data = observations("obsolescence", 11)
    assert data[:56] == [4] * 56 and data[119:] == [0] * 49


def run():
    # Deferred import lets the protocol/self-check be reviewed before simulator exists.
    from inventory_intelligence.decision import simulate

    root = Path(__file__).resolve().parents[1]
    sources = ("scripts/decision_benchmark.py", "src/inventory_intelligence/decision.py",
               "src/inventory_intelligence/forecasting.py", "docs/CONTRACT_DECISION_V1.md")
    report = dict(protocol_version=VERSION,
                  source_sha256={name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                                 for name in sources},
                  rational_encoding="exact numerator/denominator objects",
                  limitations=["synthetic finite-window penalties, not profit or business savings",
                               "correlated cycles and repeated controls, no population confidence",
                               "fixed policy and parameters, no production champion change",
                               "selection and holdout reset identical initial stock"], scenarios=[])
    for family in FAMILIES:
        for seed in SEEDS:
            data = observations(family, seed)
            rng = random.Random(seed + 1000)
            hidden = [rng.choice((0, 1, 2)) for _ in range(10)]
            for delay_name, delays in (("fixed", [0] * 10), ("hidden", hidden)):
                runoff = 2 + max(delays) + 7
                assert len(delays) == len(range(0, 56 + runoff, 7))
                for holding, backlog, setup in COSTS:
                    inputs = dict(family=family, seed=seed, generator=VERSION,
                                  train=data[:56], selection=data[56:112], holdout=data[112:],
                                  selection_history=data[:56], holdout_history=data[:112],
                                  parameters=PARAMETERS, delay_regime=delay_name,
                                  supplier_delays=delays,
                                  costs=dict(holding_cost=holding, backlog_cost=backlog,
                                             order_cost=setup))
                    result = dict(inputs=inputs, input_sha256=digest(inputs), selection={}, holdout={})
                    for split in ("selection", "holdout"):
                        for method in CANDIDATES:
                            simulation = simulate(inputs[f"{split}_history"], inputs[split],
                                                  method=method, **PARAMETERS,
                                                  supplier_delays=delays, **inputs["costs"])
                            if simulation["terminal"]["backlog"] or simulation["terminal"]["outstanding_qty"]:
                                raise ValueError("simulator did not settle terminal obligations")
                            result[split][method] = dict(metrics=simulation["metrics"],
                                                         terminal=simulation["terminal"],
                                                         reviews=simulation["reviews"],
                                                         assumptions=simulation["assumptions"],
                                                         service_eligible=eligible(simulation["metrics"]))
                    chosen = select({method: value["metrics"] for method, value in result["selection"].items()})
                    result["selected_method"] = chosen
                    result["promotion"] = promotion(chosen, {method: value["metrics"]
                                                             for method, value in result["holdout"].items()})
                    report["scenarios"].append(result)
    report["summary"] = dict(comparisons=len(report["scenarios"]),
                              candidate_split_runs=len(report["scenarios"]) * len(CANDIDATES) * 2,
                              no_selection=sum(row["selected_method"] is None for row in report["scenarios"]),
                              proposed_promotions=sum(row["promotion"]["passed"] for row in report["scenarios"]))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    self_check()
    report = run()
    encoded = json.dumps(report, default=exact, sort_keys=True, indent=2) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Build/serialize first; a failed experiment never truncates a previous artifact.
    temporary = args.output.with_name(args.output.name + ".tmp")
    temporary.write_text(encoded)
    temporary.replace(args.output)
    print(json.dumps(report["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
