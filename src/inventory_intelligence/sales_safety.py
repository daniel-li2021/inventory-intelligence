"""Exact sales-proxy accounting after paid policy-owned warmup; research only."""

from fractions import Fraction

from . import intermittent
from .decision import _integer, _observations
from .decision_diagnostics import common_window_costs

VERSION = "uci-sales-proxy-safety-v1"
METHODS = ("mean", "sba")
QUANTILES = (None, Fraction(9, 10), Fraction(19, 20))
LEADS = (2, 5)
DELAYS = (0, 3)
WARMUP_DAYS = 56
SCORED_DAYS = 28
REVIEW_DAYS = 7
SETTLEMENT_DAYS = 15


def summarize(simulation, demand, *, warmup_days, review_days, quantile, common_end):
    """Separate warmup obligations/costs from holdout, retaining actual carryover."""
    demand = _observations("demand", demand)
    warmup_days = _integer("warmup_days", warmup_days, 1)
    review_days = _integer("review_days", review_days, 1)
    if quantile is not None:
        quantile = intermittent._probability("quantile", quantile)
    n = len(demand)
    if warmup_days >= n or warmup_days % review_days:
        raise ValueError("warmup must end on a review boundary inside demand")
    if simulation["assumptions"]["scored_days"] != n:
        raise ValueError("demand and simulation windows disagree")
    if simulation["metrics"]["prior_commitment_units"]:
        raise ValueError("sales-proxy accounting excludes prior commitments")
    days = simulation["days"]
    if any(row["holding_cost"] != row["on_hand"] or row["backlog_cost"] != 10 * row["backlog"]
           or row["order_cost"] != 2 * bool(row["order_qty"]) for row in days):
        raise ValueError("sales-proxy accounting requires the declared 1/10/2 costs")
    closure = common_window_costs(simulation, holding_cost=1, end_day=common_end)
    purchased = sum(row["order_qty"] for row in days)
    if sum(row["receipts"] for row in days) != purchased:
        raise ValueError("sales-proxy accounting excludes initial inbound")
    if purchased != sum(demand) + simulation["terminal"]["on_hand"]:
        raise ValueError("sales-proxy accounting requires paid zero initial stock")
    horizon = simulation["assumptions"]["horizon"]
    result = {}
    for name, start, end in (("warmup", 0, warmup_days), ("holdout", warmup_days, n)):
        window = days[start:end]
        units = sum(demand[start:end])
        immediate = sum(row["immediately_filled_units"] for row in window)
        eventual = sum(fulfillment["quantity"] for row in days
                       for fulfillment in row["fulfillments"]
                       if fulfillment["kind"] == "new" and start <= fulfillment["due_day"] < end)
        starts = range(start, end - review_days + 1, review_days)
        cycles = len(starts)
        clear = sum(not any(row["shortage"] for row in days[day:day + review_days]) for day in starts)
        reviews = [row for row in simulation["reviews"] if start <= row["day"] < end]
        origins = [row for row in reviews if row["day"] + horizon <= end]
        covered = 0
        loss = Fraction(0)
        for origin in origins:
            actual = sum(demand[origin["day"]:origin["day"] + horizon])
            target = origin["protection_target"]
            covered += actual <= target
            error = actual - target
            if quantile is not None:
                loss += max(quantile * error, (quantile - 1) * error)
        result[name] = dict(days=end - start, demand_units=units, immediate_units=immediate,
            immediate_fill=Fraction(immediate, units) if units else None,
            eventual_units=eventual, eventual_fill=Fraction(eventual, units) if units else None,
            cycles=cycles, shortage_free_cycles=clear, cycle_service=Fraction(clear, cycles) if cycles else None,
            new_unmet_units=sum(row["newly_unmet_units"] for row in window),
            backlog_piece_days=sum(row["backlog"] for row in window),
            on_hand_piece_days=sum(row["on_hand"] for row in window),
            protection_origins=len(origins), protection_covered=covered,
            protection_coverage=Fraction(covered, len(origins)) if origins else None,
            pinball_sum=loss if quantile is not None else None,
            pinball_loss=loss / len(origins) if quantile is not None and origins else None,
            review_count=len(reviews), safety_sum=sum(row["safety_qty"] for row in reviews),
            average_safety=Fraction(sum(row["safety_qty"] for row in reviews), len(reviews)) if reviews else None)
    costs = {}
    for name, start, end in (("warmup", 0, warmup_days), ("holdout", warmup_days, n),
                             ("settlement", n, len(days))):
        window = days[start:end]
        purchase = 2 * sum(row["order_qty"] for row in window)
        holding = sum(row["holding_cost"] for row in window)
        if name == "settlement":
            holding += closure["extension_holding_cost"]
        backlog = sum(row["backlog_cost"] for row in window)
        setup = sum(row["order_cost"] for row in window)
        costs[name] = dict(acquisition=purchase, holding=holding, backlog=backlog, setup=setup,
                           total=purchase + holding + backlog + setup)
    full_cost = sum(row["total"] for row in costs.values())
    if full_cost != 2 * purchased + closure["common_total_cost"]:
        raise ValueError("paid full cost does not reconcile")
    result.update(costs=costs, full_cost=full_cost, accounting_days=common_end,
                  native_days=len(days), terminal_stock=simulation["terminal"]["on_hand"],
                  boundary_state={key: days[warmup_days - 1][key]
                                  for key in ("on_hand", "backlog", "outstanding_qty")})
    return result


def simulate_arm(history, demand, *, method, quantile, lead_days, delay):
    if method not in METHODS or quantile not in QUANTILES or lead_days not in LEADS or delay not in DELAYS:
        raise ValueError("arm outside the frozen sales-proxy grid")
    demand = _observations("demand", demand)
    if len(demand) != WARMUP_DAYS + SCORED_DAYS:
        raise ValueError("sales-proxy grid needs 56 warmup + 28 holdout days")
    stop = len(demand) + lead_days + delay + REVIEW_DAYS
    supplier = [delay] * len(range(0, stop, REVIEW_DAYS))
    simulation = intermittent.simulate(history, demand, method=method, safety_quantile=quantile,
        on_hand=0, lead_days=lead_days, review_days=REVIEW_DAYS, pack_size=2, moq=4,
        supplier_delays=supplier, holding_cost=1, backlog_cost=10, order_cost=2)
    summary = summarize(simulation, demand, warmup_days=WARMUP_DAYS, review_days=REVIEW_DAYS,
        quantile=quantile, common_end=len(demand) + SETTLEMENT_DAYS)
    return simulation, summary
