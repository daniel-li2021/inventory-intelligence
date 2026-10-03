"""Offline warmup accounting and paired trials; never an operational planner."""

from fractions import Fraction
from itertools import groupby
from math import ceil

from . import decision, intermittent
from .decision_diagnostics import common_window_costs, startup_feasibility


def supplier_slots(daily_delays, *, start_day, demand_days, lead_days, review_days):
    """Map shared calendar shocks to all review slots, including fixed runoff."""
    trace = decision._observations("daily supplier delays", daily_delays)
    start = decision._integer("start_day", start_day)
    n = decision._integer("demand_days", demand_days, 1)
    lead = decision._integer("lead_days", lead_days, 1)
    review = decision._integer("review_days", review_days, 1)
    bound = max(trace)
    stop = n + lead + bound + review
    if start + stop > len(trace):
        raise ValueError("daily supplier trace does not cover settlement")
    # The kernel sizes runoff from the maximum supplied slot, not a declared
    # daily bound. Removing unused tail slots can only decrease that maximum.
    while True:
        delays = tuple(trace[start + day] for day in range(0, stop, review))
        actual_stop = n + lead + max(delays) + review
        if actual_stop == stop:
            return delays
        stop = actual_stop


def window_metrics(simulation, *, start_day, end_day, review_days, horizon,
                   review_phase=0, unit_cost=2, nominal_quantile=None):
    """Score a contiguous operating window, retaining carried backlog in service."""
    start = decision._integer("start_day", start_day)
    end = decision._integer("end_day", end_day, 1)
    review = decision._integer("review_days", review_days, 1)
    horizon = decision._integer("horizon", horizon, 1)
    phase = decision._integer("review_phase", review_phase)
    price = decision._rate("unit_cost", unit_cost)
    if phase >= review or not start < end <= simulation["assumptions"]["scored_days"]:
        raise ValueError("invalid scoring window or review phase")
    if nominal_quantile is not None:
        nominal_quantile = intermittent._probability("nominal_quantile", nominal_quantile)
    rows = simulation["days"][start:end]
    units = sum(row["new_demand"] for row in rows)
    filled = sum(row["immediately_filled_units"] for row in rows)
    cycle_starts = [day for day in range(phase, end - review + 1, review) if day >= start]
    clean = sum(not any(row["shortage"] for row in simulation["days"][day:day + review])
                for day in cycle_starts)
    origins = [row for row in simulation["reviews"]
               if start <= row["day"] and row["day"] + horizon <= end and not row["runoff"]]
    covered = 0
    pinball = cumulative_absolute = cumulative_signed = daily_absolute = Fraction(0)
    actual_units = 0
    for row in origins:
        actual = [day["new_demand"] for day in simulation["days"][row["day"]:row["day"] + horizon]]
        errors = [forecast - observed for forecast, observed in zip(row["forecast"], actual)]
        observed = sum(actual)
        target = row["protection_target"]
        covered += observed <= target
        cumulative_absolute += abs(sum(errors))
        cumulative_signed += sum(errors)
        daily_absolute += sum(abs(error) for error in errors)
        actual_units += observed
        if nominal_quantile is not None:
            error = observed - target
            pinball += max(nominal_quantile * error, (nominal_quantile - 1) * error)
    counts = [row["calibration"]["count"] for row in origins if row.get("calibration") is not None]
    rates = dict(immediate_fill_rate=Fraction(filled, units) if units else None,
                 cycle_service=Fraction(clean, len(cycle_starts)) if cycle_starts else None,
                 target_coverage=Fraction(covered, len(origins)) if origins else None)
    result = dict(days=end - start, new_demand_units=units, immediately_filled_units=filled,
                  missed_units=units - filled, shortage_days=sum(row["shortage"] for row in rows),
                  on_hand_piece_days=sum(row["on_hand"] for row in rows),
                  backlog_piece_days=sum(row["backlog"] for row in rows),
                  complete_cycles=len(cycle_starts), shortage_free_cycles=clean,
                  purchased_units=sum(row["order_qty"] for row in rows),
                  operating_cost=sum((row["total_cost"] for row in rows), Fraction(0)),
                  acquisition_cost=price * sum(row["order_qty"] for row in rows),
                  end_on_hand=rows[-1]["on_hand"], end_backlog=rows[-1]["backlog"],
                  end_pipeline=rows[-1]["outstanding_qty"],
                  forecast_origins=len(origins), forecast_points=len(origins) * horizon,
                  forecast_actual_units=actual_units,
                  forecast_mae=daily_absolute / (len(origins) * horizon) if origins else None,
                  forecast_wape=daily_absolute / actual_units if actual_units else None,
                  cumulative_mae=cumulative_absolute / len(origins) if origins else None,
                  cumulative_bias=cumulative_signed / len(origins) if origins else None,
                  target_covered=covered,
                  target_pinball_loss=pinball / len(origins) if origins and nominal_quantile else None,
                  calibration_min_count=min(counts) if counts else None,
                  calibration_max_count=max(counts) if counts else None, **rates)
    result["nominal_quantile"] = nominal_quantile
    result["nominal_gaps"] = {key: value - nominal_quantile if value is not None else None
                               for key, value in rates.items()} if nominal_quantile else None
    return result


def summarize(simulation, *, warmup_days, score_days, on_hand, unit_cost,
              holding_cost, common_end_day, review_days, horizon, nominal_quantile):
    """Include owned initial pieces and every order in complete-window costs."""
    price = decision._rate("unit_cost", unit_cost)
    warmup = decision._integer("warmup_days", warmup_days)
    score = window_metrics(simulation, start_day=warmup, end_day=warmup + score_days,
                           review_days=review_days, horizon=horizon,
                           unit_cost=price, nominal_quantile=nominal_quantile)
    before = (window_metrics(simulation, start_day=0, end_day=warmup, review_days=review_days,
                            horizon=horizon, unit_cost=price, nominal_quantile=nominal_quantile)
              if warmup else None)
    accounting = common_window_costs(simulation, holding_cost=holding_cost, end_day=common_end_day)
    purchase = price * sum(row["order_qty"] for row in simulation["days"])
    initial = price * decision._integer("on_hand", on_hand)
    carry = (dict(on_hand=simulation["days"][warmup - 1]["on_hand"],
                  backlog=simulation["days"][warmup - 1]["backlog"],
                  pipeline=simulation["days"][warmup - 1]["outstanding_qty"])
             if warmup else dict(on_hand=on_hand, backlog=0, pipeline=0))
    # Assert conservation independently from scored service partitioning.
    days = simulation["days"]
    if (on_hand + sum(row["receipts"] for row in days)
            != sum(row["fulfilled_units"] for row in days) + simulation["terminal"]["on_hand"]
            or sum(row["new_demand"] + row["prior_demand"] for row in days)
            != sum(row["fulfilled_units"] for row in days)):
        raise ValueError("trial violates physical or obligation conservation")
    return dict(warmup=before, score=score, score_start_state=carry,
                accounting=dict(**accounting, initial_acquisition_cost=initial,
                    all_order_acquisition_cost=purchase,
                    warmup_operating_cost=before["operating_cost"] if before else Fraction(0),
                    warmup_order_acquisition_cost=before["acquisition_cost"] if before else Fraction(0),
                    score_operating_cost=score["operating_cost"],
                    score_order_acquisition_cost=score["acquisition_cost"],
                    common_runoff_order_acquisition_cost=purchase - score["acquisition_cost"]
                        - (before["acquisition_cost"] if before else Fraction(0)),
                    full_intervention_cost=accounting["common_total_cost"] + initial + purchase),
                terminal=simulation["terminal"])


def paired_trial(history, warmup_demand, score_demand, daily_delays, *, method,
                 safety_quantile=None, on_hand=10, lead_days=2, review_days=7,
                 pack_size=2, moq=4, holding_cost=1, backlog_cost=10,
                 order_cost=2, unit_cost=2):
    """Run seamless warmup and history-matched cold start on the same future."""
    history = decision._observations("history", history)
    warmup = decision._observations("warmup_demand", warmup_demand)
    score = decision._observations("score_demand", score_demand)
    lead = decision._integer("lead_days", lead_days, 1)
    review = decision._integer("review_days", review_days, 1)
    if len(warmup) % review:
        raise ValueError("warmup must align the paired review calendars")
    max_delay = max(decision._observations("daily_delays", daily_delays))
    common_tail = lead + max_delay + review
    params = dict(method=method, safety_quantile=safety_quantile, on_hand=on_hand,
                  lead_days=lead, review_days=review, pack_size=pack_size, moq=moq,
                  holding_cost=holding_cost, backlog_cost=backlog_cost, order_cost=order_cost)
    results = {}
    trajectories = {}
    for arm, prefix, demand, offset in (
            ("cold", history + warmup, score, len(warmup)),
            ("warm", history, warmup + score, 0)):
        delays = supplier_slots(daily_delays, start_day=offset, demand_days=len(demand),
                                lead_days=lead, review_days=review)
        sim = intermittent.simulate(prefix, demand, supplier_delays=delays, **params)
        start = len(warmup) if arm == "warm" else 0
        summary = summarize(sim, warmup_days=start, score_days=len(score), on_hand=on_hand,
            unit_cost=unit_cost, holding_cost=holding_cost, common_end_day=len(demand) + common_tail,
            review_days=review, horizon=lead + review, nominal_quantile=safety_quantile)
        summary["supplier_delays"] = delays
        # Compact review evidence still identifies the full prefix-calibration
        # ranks; exact residuals/trajectories reproduce from hashed inputs.
        summary["score_reviews"] = [dict(day=row["day"] - start,
            forecast_runs=[dict(value=value, days=len(list(group)))
                           for value, group in groupby(row["forecast"])],
            safety_qty=row["safety_qty"], target=row["protection_target"],
            order_qty=row["order_qty"], calibration_count=row["calibration"]["count"]
                if row["calibration"] else None,
            calibration_rank=ceil(safety_quantile * row["calibration"]["count"])
                if row["calibration"] else None)
            for row in sim["reviews"] if start <= row["day"] < start + len(score)]
        results[arm] = summary
        trajectories[arm] = sim
    feasibility = startup_feasibility(score, on_hand=on_hand, lead_days=lead,
                                      review_days=review, supplier_delays=results["cold"]["supplier_delays"])
    cutoff = feasibility["startup_days"]
    for arm, sim in trajectories.items():
        start = len(warmup) if arm == "warm" else 0
        rows = sim["days"][start:start + len(score)]
        misses = sum(row["new_demand"] - row["immediately_filled_units"] for row in rows[:cutoff])
        results[arm]["timing"] = dict(before_cold_earliest_receipt_missed_units=misses,
            at_or_after_cold_earliest_receipt_missed_units=results[arm]["score"]["missed_units"] - misses)
    if (results["cold"]["timing"]["before_cold_earliest_receipt_missed_units"]
            != feasibility["inevitable_new_missed_units"]):
        raise ValueError("cold trial violates independent startup feasibility")
    results["cold"]["feasibility"] = feasibility
    deltas = {key: (results["warm"]["score"][key] - results["cold"]["score"][key]
                    if results["warm"]["score"][key] is not None
                    and results["cold"]["score"][key] is not None else None)
              for key in ("missed_units", "immediate_fill_rate", "cycle_service", "operating_cost",
                          "on_hand_piece_days", "backlog_piece_days")}
    deltas["full_intervention_cost"] = (results["warm"]["accounting"]["full_intervention_cost"]
                                        - results["cold"]["accounting"]["full_intervention_cost"])
    return dict(arms=results, warm_minus_cold=deltas), trajectories
