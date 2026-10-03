"""Frozen attribution of existing synthetic Lab controls; no policy selection."""

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path

from inventory_intelligence import lab
from inventory_intelligence.decision_diagnostics import common_window_costs, startup_feasibility
from inventory_intelligence.planning_runs import exact_json

VERSION = "lab-feasibility-diagnostic-v1"
COMMON_END_DAY = 36
CONTROLS = (("baseline", {}), ("delay3", {"supplier_delay_days": 3}),
            ("demand125", {"demand_percent": 125}), ("zero", {"demand_percent": 0}),
            ("incomplete_supply", {"evidence_case": "incomplete_supply"}))


def build_report(evidence=None):
    evidence = lab.load_evidence() if evidence is None else lab.validate_evidence(evidence)
    clean = evidence["plans"]["clean"]["result"]
    records = []
    metadata = None
    for name, overrides in CONTROLS:
        result = lab.evaluate(overrides, evidence=evidence)
        metadata = result["metadata"]
        side = result["scenario"]
        record = dict(name=name, status=side["status"], reasons=side["reasons"],
                      parameters=side["parameters"], calculation_id=side["run_id"],
                      inputs=None, feasibility=None, realized=None, accounting=None,
                      common_cost_delta_vs_baseline=None)
        if side["status"] == "assessable":
            params = side["parameters"]
            sim = side["simulation"]
            inputs = dict(demand=side["forecast"]["demand"], on_hand=metadata["on_hand"],
                lead_days=params["lead_days"], review_days=params["review_days"],
                supplier_delays=sim["assumptions"]["supplier_delays"],
                commitments=[dict(id=clean["supply"]["reservations"][0]["reservation_id"],
                                  due_day=0, quantity=params["reservation_qty"])]
                            if params["reservation_qty"] else [],
                inbound=[dict(id=row["inbound_id"], arrival_day=params["inbound_day"],
                              quantity=row["remaining_qty"])
                         for row in clean["supply"]["inbound"] if row["status"] == "confirmed"])
            bound = startup_feasibility(**inputs)
            before = [row for row in sim["days"] if row["scored"] and row["day"] < bound["startup_days"]]
            after = [row for row in sim["days"] if row["scored"] and row["day"] >= bound["startup_days"]]
            def misses(rows):
                return sum(row["new_demand"] - row["immediately_filled_units"] for row in rows)
            prior_before = sum(row["newly_unmet_units"] -
                               (row["new_demand"] - row["immediately_filled_units"]) for row in before)
            rate = sim["metrics"]["immediate_fill_rate"]
            rate = Fraction(rate) if rate is not None else None
            if (misses(before) != bound["inevitable_new_missed_units"]
                    or prior_before != bound["inevitable_prior_missed_units"]
                    or (rate is not None and rate > bound["immediate_fill_ceiling"])):
                raise ValueError("simulation violates independent startup bound")
            accounting = common_window_costs(sim, holding_cost=Fraction(side["costs"]["rates"]["holding"]),
                                             end_day=COMMON_END_DAY)
            record.update(inputs=inputs, feasibility=bound, accounting=accounting,
                realized=dict(startup_new_missed_units=misses(before), later_new_missed_units=misses(after),
                    startup_new_demand_units=sum(row["new_demand"] for row in before),
                    later_new_demand_units=sum(row["new_demand"] for row in after),
                    startup_prior_missed_units=prior_before,
                    immediate_fill_rate=rate, shortage_days=sim["metrics"]["shortage_days"],
                    proposed_prefix_order_qty=side["plan"]["proposed_order_qty"]))
            record["common_cost_delta_vs_baseline"] = (
                accounting["common_total_cost"] - records[0]["accounting"]["common_total_cost"]
                if records else Fraction(0))
        records.append(record)
    root = Path(__file__).resolve().parents[1]
    files = ("docs/FEASIBILITY_DIAGNOSTIC.md", "scripts/feasibility_diagnostic.py",
             "src/inventory_intelligence/decision_diagnostics.py", "src/inventory_intelligence/decision.py",
             "src/inventory_intelligence/lab.py", "src/inventory_intelligence/forecasting.py",
             "src/inventory_intelligence/lab_evidence.json")
    return exact_json(dict(protocol_version=VERSION, synthetic=True, common_end_day=COMMON_END_DAY,
        source_metadata=metadata, source_sha256={name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                                               for name in files}, controls=records,
        limits=["Existing single synthetic replay; consumed evidence, not fresh generalization.",
                "Evaluation diagnostics never inform ordering or select a model.",
                "Common window extends settled no-demand runoff; terminal stock has no salvage value.",
                "Later missed fill is not exclusively forecast error; no business-savings claim."]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_report()
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(f"Wrote {len(report['controls'])} synthetic controls to {args.output}")


if __name__ == "__main__":
    main()
