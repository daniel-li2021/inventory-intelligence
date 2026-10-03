"""Frozen forecast-controlled policy comparison, exact synthetic evidence."""

import argparse
from datetime import date
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random

from inventory_intelligence.policy_comparison import POLICIES, VERSION, simulate_policy

SEEDS = (7301, 7709, 8027)
METHODS = ("mean", "seasonal_naive")
SAFETIES = (0, 4)


def exact(value):
    if isinstance(value, Fraction):
        return dict(numerator=value.numerator, denominator=value.denominator)
    if isinstance(value, date):
        return value.isoformat()
    raise TypeError(type(value).__name__)


def canonical(value):
    return json.dumps(value, default=exact, sort_keys=True, separators=(",", ":")).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def scenarios():
    for family in ("constant", "weekly", "zero", "lumpy", "pause", "late_inbound"):
        for seed in (SEEDS if family in ("lumpy", "pause") else SEEDS[:1]):
            rng = random.Random(seed)
            if family in ("constant", "late_inbound"):
                data = [3] * 140
            elif family == "weekly":
                data = [0, 1, 2, 3, 4, 5, 6] * 20
            elif family == "zero":
                data = [0] * 140
            else:
                data = [rng.choice((0, 0, 0, 0, 1, 2, 8, 16)) for _ in range(140)]
                if family == "pause":
                    data[98:119] = [0] * 21
            yield dict(family=family, seed=seed, history=data[:84], demand=data[84:],
                       parameters=dict(on_hand=10, lead_days=2, review_days=7,
                                       pack_size=2, moq=4, review_phase=0,
                                       commitments=([dict(id="prior", due_day=4, quantity=8)]
                                                    if family == "late_inbound" else []),
                                       inbound=([dict(id="known", arrival_day=12, quantity=80)]
                                                if family == "late_inbound" else []),
                                       holding_cost=1, backlog_cost=10, order_cost=2))


def full_cost(inputs, simulation):
    """All pieces are charged, including stock and inbound purchased before scoring."""
    days = simulation["days"]
    starting = inputs["parameters"]["on_hand"]
    inbound = sum(row["quantity"] for row in inputs["parameters"]["inbound"])
    purchased = sum(row["order_qty"] for row in days)
    holding = sum(row["holding_cost"] for row in days)
    backlog = sum(row["backlog_cost"] for row in days)
    setup = sum(row["order_cost"] for row in days)
    acquisition = 2 * (starting + inbound + purchased)
    if holding + backlog + setup != simulation["metrics"]["total_cost"]:
        raise ValueError("exposure/setup cost mismatch")
    if starting + inbound + purchased != (simulation["metrics"]["new_demand_units"]
            + simulation["metrics"]["prior_commitment_units"] + simulation["terminal"]["on_hand"]):
        raise ValueError("piece conservation mismatch")
    return dict(starting_units=starting, confirmed_inbound_units=inbound,
                purchased_units=purchased, unit_cost=2, acquisition_cost=acquisition,
                holding_cost=holding, backlog_cost=backlog, setup_cost=setup,
                full_cost=acquisition + holding + backlog + setup)


def run():
    root = Path(__file__).resolve().parents[1]
    sources = ("scripts/policy_benchmark.py", "src/inventory_intelligence/policy_comparison.py",
               "src/inventory_intelligence/decision.py", "src/inventory_intelligence/replenishment.py",
               "src/inventory_intelligence/forecasting.py", "docs/POLICY_COMPARISON_V1.md")
    report = dict(protocol_version=VERSION,
                  source_sha256={name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                                 for name in sources}, scenarios=[], pairs=[])
    for scenario in scenarios():
        for method in METHODS:
            for safety in SAFETIES:
                inputs = dict(scenario, method=method, safety_qty=safety)
                arms = {}
                forecasts = None
                for policy in POLICIES:
                    simulation = simulate_policy(inputs["history"], inputs["demand"],
                        policy=policy, method=method, safety_qty=safety, **inputs["parameters"])
                    receipts = [(row["day"], row["forecast"]) for row in simulation["reviews"]]
                    if forecasts is not None and receipts != forecasts:
                        raise ValueError("policy changed forecast or review calendar")
                    forecasts = receipts
                    arms[policy] = dict(simulation=simulation, trajectory_sha256=digest(simulation),
                                        cost=full_cost(inputs, simulation))
                cell = dict(inputs=inputs, input_sha256=digest(inputs), arms=arms)
                report["scenarios"].append(cell)
                reference = arms[POLICIES[0]]
                for policy in POLICIES[1:]:
                    candidate = arms[policy]
                    differences = {}
                    for key in ("immediate_fill_rate", "on_time_prior_fill_rate", "cycle_service",
                                "backlog_piece_days", "newly_unmet_units"):
                        left, right = (arm["simulation"]["metrics"][key]
                                       for arm in (candidate, reference))
                        differences[key] = left - right if left is not None and right is not None else None
                    differences["full_cost"] = candidate["cost"]["full_cost"] - reference["cost"]["full_cost"]
                    report["pairs"].append(dict(input_sha256=cell["input_sha256"],
                                                policy=policy, differences=differences))
    summary = dict(scenario_labels=10,
                   distinct_demand_paths=len({digest(row["inputs"]["history"] + row["inputs"]["demand"])
                                             for row in report["scenarios"]}),
                   forecast_safety_cells=len(report["scenarios"]),
                   arms=len(report["scenarios"]) * len(POLICIES), pairs=len(report["pairs"]),
                   distinct_physical_trajectories=len({digest(arm["simulation"]["days"])
                        for row in report["scenarios"] for arm in row["arms"].values()}),
                   policies={})
    for policy in POLICIES[1:]:
        pairs = [row["differences"] for row in report["pairs"] if row["policy"] == policy]
        summary["policies"][policy] = dict(
            paired_cells=len(pairs),
            fill_improved=sum(row["immediate_fill_rate"] is not None and row["immediate_fill_rate"] > 0 for row in pairs),
            fill_regressed=sum(row["immediate_fill_rate"] is not None and row["immediate_fill_rate"] < 0 for row in pairs),
            fill_equal=sum(row["immediate_fill_rate"] == 0 for row in pairs),
            fill_undefined=sum(row["immediate_fill_rate"] is None for row in pairs),
            cost_lower=sum(row["full_cost"] < 0 for row in pairs),
            cost_higher=sum(row["full_cost"] > 0 for row in pairs),
            cost_equal=sum(row["full_cost"] == 0 for row in pairs),
            lower_cost_without_fill_or_cycle_regression=sum(
                row["full_cost"] < 0 and row["immediate_fill_rate"] is not None
                and row["immediate_fill_rate"] >= 0 and row["cycle_service"] is not None
                and row["cycle_service"] >= 0 for row in pairs))
    report["summary"] = summary
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run()
    encoded = canonical(report) + b"\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(args.output.name + ".tmp")
    temporary.write_bytes(encoded)
    temporary.replace(args.output)
    print(json.dumps(report["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
