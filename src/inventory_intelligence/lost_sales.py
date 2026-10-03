"""Research-only lost sales; attempted-demand feedback and no accepted backlog."""

from fractions import Fraction
from math import ceil

from .decision import _integer, _observations, _rate, _rows
from .forecasting import METHODS, forecast

CONTRACT_VERSION = "lost-sales-research-v1"


def simulate(history, demand, *, method, on_hand, lead_days, review_days,
             safety_qty=0, pack_size=1, moq=1, review_phase=0, commitments=(),
             inbound=(), supplier_delays=(), holding_cost=1, lost_cost=10, order_cost=0):
    history = _observations("history", history)
    demand = _observations("attempted demand", demand)
    if method not in (*METHODS, "zero"):
        raise ValueError(f"unknown lost-sales method: {method}")
    if method == "seasonal_naive" and len(history) < 7:
        raise ValueError("seasonal_naive needs seven history days")
    try:
        commitments = tuple(commitments)
        delays = tuple(supplier_delays)
    except TypeError as error:
        raise ValueError("commitments and supplier delays must be sequences") from error
    if commitments:
        raise ValueError("accepted commitments cannot become lost sales")
    on_hand = _integer("on_hand", on_hand)
    lead_days = _integer("lead_days", lead_days, 1)
    review_days = _integer("review_days", review_days, 1)
    safety_qty = _integer("safety_qty", safety_qty)
    pack_size = _integer("pack_size", pack_size, 1)
    moq = _integer("moq", moq, 1)
    review_phase = _integer("review_phase", review_phase)
    if review_phase >= review_days or lead_days + review_days > 366:
        raise ValueError("invalid review phase or protection horizon")
    n = len(demand)
    inbound = _rows("inbound", inbound, "arrival_day", n)
    for delay in delays:
        _integer("supplier delay", delay)
    runoff = lead_days + max(delays, default=0) + review_days
    stop = n + runoff
    slots = len(range(review_phase, stop, review_days))
    if delays and len(delays) != slots:
        raise ValueError(f"supplier_delays must contain exactly {slots} review slots")
    delays = delays or (0,) * slots
    h, p, k = (_rate(name, value) for name, value in
               (("holding_cost", holding_cost), ("lost_cost", lost_cost), ("order_cost", order_cost)))
    stock = on_hand
    pending = [dict(row, kind="inbound") for row in inbound]
    completed = list(history)
    horizon = lead_days + review_days
    days, reviews = [], []
    scored_cost = runoff_cost = Fraction(0)
    for day in range(stop):
        scored = day < n
        receipts = sum(row["quantity"] for row in pending if row["arrival_day"] == day)
        stock += receipts
        pending[:] = [row for row in pending if row["arrival_day"] != day]
        outstanding = sum(row["quantity"] for row in pending)
        order_qty = 0
        if day >= review_phase and (day - review_phase) % review_days == 0:
            predictions = ([Fraction(0)] * horizon if method == "zero" else
                           forecast(completed, method=method, horizon=horizon)) if scored else []
            target = sum(predictions, Fraction(0)) + safety_qty if scored else Fraction(0)
            position = stock + outstanding
            need = max(Fraction(0), target - position)
            if need:
                whole = max(ceil(need), moq)
                order_qty = pack_size * ((whole + pack_size - 1) // pack_size)
                pending.append(dict(id=f"order:{day}", kind="order", quantity=order_qty,
                                    arrival_day=day + lead_days + delays[day // review_days]))
                outstanding += order_qty
            reviews.append(dict(day=day, runoff=not scored, forecast=predictions,
                                target=target, inventory_position=position, order_qty=order_qty))
        attempted = demand[day] if scored else 0
        served = min(stock, attempted)
        lost = attempted - served
        stock -= served
        holding, penalty, setup = h * stock, p * lost, k if order_qty else Fraction(0)
        cost = holding + penalty + setup
        if scored:
            scored_cost += cost
            completed.append(attempted)
        else:
            runoff_cost += cost
        days.append(dict(day=day, scored=scored, new_demand=attempted, prior_demand=0,
            receipts=receipts, order_qty=order_qty, outstanding_qty=outstanding, on_hand=stock, backlog=0,
            immediately_filled_units=served, fulfilled_units=served, lost_units=lost, newly_unmet_units=lost,
            fulfillments=[dict(id=f"new:{day}",kind="new",due_day=day,quantity=served)] if served else [],
            shortage=bool(lost), holding_cost=holding, lost_cost=penalty, order_cost=setup, total_cost=cost))
    if pending:
        raise ValueError("invalid runoff completion: residual pipeline")
    served = sum(row["fulfilled_units"] for row in days)
    lost = sum(row["lost_units"] for row in days)
    if on_hand + sum(row["receipts"] for row in days) != served + stock or sum(demand) != served + lost:
        raise ValueError("lost-sales piece conservation failed")
    starts = range(review_phase, n - review_days + 1, review_days)
    clear = sum(not any(row["shortage"] for row in days[start:start + review_days]) for start in starts)
    metrics = dict(new_demand_units=sum(demand), immediately_filled_units=served,
        immediate_fill_rate=Fraction(served, sum(demand)) if sum(demand) else None,
        eventually_filled_units=served, eventual_fill_rate=Fraction(served, sum(demand)) if sum(demand) else None,
        lost_units=lost, complete_cycles=len(starts), shortage_free_cycles=clear,
        cycle_service=Fraction(clear,len(starts)) if starts else None,
        shortage_days=sum(row["shortage"] for row in days[:n]),
        order_count=sum(row["order_qty"] > 0 for row in days[:n]), runoff_order_count=0,
        scored_cost=scored_cost, runoff_cost=runoff_cost, total_cost=scored_cost+runoff_cost)
    return dict(contract_version=CONTRACT_VERSION, days=days, reviews=reviews, metrics=metrics,
        terminal=dict(on_hand=stock,backlog=0,outstanding_qty=0,orders=[]),
        assumptions=dict(policy="periodic inventory-position order-up-to", observation="completed attempted demand",
                         scored_days=n,runoff_days=runoff,horizon=horizon,residual_stock_value=0,
                         costs="synthetic holding/lost-unit/setup penalties; acquisition excluded"))
