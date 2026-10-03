"""Pure, exact offline decision-benchmark-v1 simulation; no purchase execution."""

from fractions import Fraction
from math import ceil

from .forecasting import METHODS, forecast

CONTRACT_VERSION = "decision-benchmark-v1"


def _integer(name, value, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return value


def _observations(name, values):
    try:
        values = tuple(values)
    except TypeError as error:
        raise ValueError(f"{name} must be a nonempty sequence") from error
    if not values:
        raise ValueError(f"{name} must be nonempty")
    for value in values:
        _integer(name, value)
    return values


def _rows(name, values, day_key, window):
    try:
        values = tuple(values)
    except TypeError as error:
        raise ValueError(f"{name} must be a sequence of rows") from error
    ids = set()
    result = []
    for row in values:
        if not isinstance(row, dict) or set(row) != {"id", day_key, "quantity"}:
            raise ValueError(f"malformed {name} row")
        identity = row["id"]
        if not isinstance(identity, str) or not identity.strip() or identity in ids:
            raise ValueError(f"{name} ids must be unique nonempty strings")
        day = _integer(day_key, row[day_key])
        if day >= window:
            raise ValueError(f"{day_key} must be inside the scored window")
        quantity = _integer("quantity", row["quantity"], 1)
        ids.add(identity)
        result.append(dict(id=identity, **{day_key: day}, quantity=quantity))
    return result


def _rate(name, value):
    if type(value) not in (int, Fraction) or value < 0:
        raise ValueError(f"{name} must be a nonnegative int or Fraction")
    return Fraction(value)


def simulate(history, demand, *, method, on_hand, lead_days, review_days,
             safety_qty=0, pack_size=1, moq=1, review_phase=0,
             commitments=(), inbound=(), supplier_delays=(), holding_cost=1,
             backlog_cost=10, order_cost=0):
    """Return auditable whole-piece trajectories and exact Fraction metrics.

    Day on_hand/backlog are ending quantities; receipts/order_qty/outstanding_qty
    are whole pieces. Review forecasts are retained even for incomplete targets.
    Forecast scores and all service/exposure metrics cover scored days only;
    eventually_filled_units also counts fulfillment during the fixed runoff.
    """
    return _simulate(history, demand, method=method, on_hand=on_hand,
                     lead_days=lead_days, review_days=review_days,
                     safety_qty=safety_qty, pack_size=pack_size, moq=moq,
                     review_phase=review_phase, commitments=commitments,
                     inbound=inbound, supplier_delays=supplier_delays,
                     holding_cost=holding_cost, backlog_cost=backlog_cost,
                     order_cost=order_cost)


def _simulate(history, demand, *, method, on_hand, lead_days, review_days,
              safety_qty=0, pack_size=1, moq=1, review_phase=0,
              commitments=(), inbound=(), supplier_delays=(), holding_cost=1,
              backlog_cost=10, order_cost=0, _review_provider=None):
    """Shared event kernel; the private provider sees completed observations only."""
    history = _observations("history", history)
    demand = _observations("demand", demand)
    if _review_provider is None and method not in (*METHODS, "zero"):
        raise ValueError(f"unknown decision method: {method}")
    if method == "seasonal_naive" and len(history) < 7:
        raise ValueError("seasonal_naive needs seven history days")
    on_hand = _integer("on_hand", on_hand)
    lead_days = _integer("lead_days", lead_days, 1)
    review_days = _integer("review_days", review_days, 1)
    safety_qty = _integer("safety_qty", safety_qty)
    pack_size = _integer("pack_size", pack_size, 1)
    moq = _integer("moq", moq, 1)
    review_phase = _integer("review_phase", review_phase)
    if review_phase >= review_days:
        raise ValueError("review_phase must be less than review_days")
    horizon = lead_days + review_days
    if horizon > 366:
        raise ValueError("lead_days + review_days must be <= 366")
    n = len(demand)
    commitments = _rows("commitments", commitments, "due_day", n)
    inbound = _rows("inbound", inbound, "arrival_day", n)
    try:
        delays = tuple(supplier_delays)
    except TypeError as error:
        raise ValueError("supplier_delays must be a sequence") from error
    for delay in delays:
        _integer("supplier delay", delay)
    runoff_days = lead_days + max(delays, default=0) + review_days
    stop = n + runoff_days
    slots = len(range(review_phase, stop, review_days))
    if delays and len(delays) != slots:
        raise ValueError(f"supplier_delays must contain exactly {slots} review slots")
    if not delays:
        delays = (0,) * slots
    h = _rate("holding_cost", holding_cost)
    b = _rate("backlog_cost", backlog_cost)
    k = _rate("order_cost", order_cost)

    stock = on_hand
    pending = [dict(row, kind="inbound") for row in inbound]
    queue = []
    days, reviews = [], []
    completed = list(history)
    eventual_new = on_time_prior = 0
    scored_cost = runoff_cost = Fraction(0)

    def fulfill(day, records):
        nonlocal stock, eventual_new, on_time_prior
        queue.sort(key=lambda row: (row["due_day"], row["kind"] != "prior", row["id"]))
        for row in queue:
            quantity = min(stock, row["quantity"])
            if quantity:
                stock -= quantity
                row["quantity"] -= quantity
                records.append(dict(id=row["id"], kind=row["kind"],
                                    due_day=row["due_day"], quantity=quantity))
                if row["kind"] == "new":
                    eventual_new += quantity
                elif row["due_day"] == day:
                    on_time_prior += quantity
        queue[:] = [row for row in queue if row["quantity"]]

    for day in range(stop):
        scored = day < n
        arrived = [row for row in pending if row["arrival_day"] == day]
        receipts = sum(row["quantity"] for row in arrived)
        stock += receipts
        pending[:] = [row for row in pending if row["arrival_day"] != day]
        due = [dict(row, kind="prior") for row in commitments if row["due_day"] == day]
        prior_demand = sum(row["quantity"] for row in due)
        queue.extend(due)
        fulfillments = []
        fulfill(day, fulfillments)
        due_unmet = sum(row["quantity"] for row in queue
                        if row["kind"] == "prior" and row["due_day"] == day)
        outstanding = sum(row["quantity"] for row in pending)
        backlog = sum(row["quantity"] for row in queue)
        order_qty = 0
        if day >= review_phase and (day - review_phase) % review_days == 0:
            evidence = {}
            review_safety = safety_qty
            if scored and _review_provider is not None:
                evidence = _review_provider(tuple(completed), horizon)
                if not isinstance(evidence, dict):
                    raise ValueError("review provider must return forecast/safety evidence")
                predictions = evidence.get("forecast")
                review_safety = _integer("provider safety_qty", evidence.get("safety_qty"))
                if (not isinstance(predictions, (list, tuple)) or len(predictions) != horizon
                        or any(type(value) is not Fraction or value < 0 for value in predictions)):
                    raise ValueError("provider forecasts must be H nonnegative Fractions")
            else:
                predictions = ([Fraction(0)] * horizon if method == "zero" else
                               forecast(completed, method=method, horizon=horizon)) if scored else []
            future_prior = sum(row["quantity"] for row in commitments
                               if day < row["due_day"] < day + horizon)
            target = sum(predictions, Fraction(0)) + review_safety + future_prior if scored else Fraction(0)
            position = stock + outstanding - backlog
            need = max(Fraction(0), target - position)
            if need:
                whole_need = max(ceil(need), moq)
                order_qty = pack_size * ((whole_need + pack_size - 1) // pack_size)
                pending.append(dict(id=f"order:{day}", kind="order", quantity=order_qty,
                                    arrival_day=day + lead_days + delays[day // review_days]))
                outstanding += order_qty
            reviews.append(dict(day=day, runoff=not scored, forecast=predictions,
                                target=target, inventory_position=position, order_qty=order_qty, **{
                                    key: value for key, value in evidence.items() if key != "forecast"}))
        new_demand = demand[day] if scored else 0
        immediate = min(stock, new_demand)
        if new_demand:
            queue.append(dict(id=f"new:{day}", kind="new", due_day=day, quantity=new_demand))
            fulfill(day, fulfillments)
        backlog = sum(row["quantity"] for row in queue)
        newly_unmet = due_unmet + new_demand - immediate
        holding = h * stock
        backlog_charge = b * backlog
        setup = k if order_qty else Fraction(0)
        cost = holding + backlog_charge + setup
        if scored:
            scored_cost += cost
            completed.append(new_demand)
        else:
            runoff_cost += cost
        days.append(dict(day=day, scored=scored, on_hand=stock, backlog=backlog,
                         new_demand=new_demand, prior_demand=prior_demand,
                         immediately_filled_units=immediate,
                         fulfilled_units=sum(row["quantity"] for row in fulfillments),
                         fulfillments=fulfillments, newly_unmet_units=newly_unmet,
                         receipts=receipts, order_qty=order_qty, outstanding_qty=outstanding,
                         shortage=bool(backlog), holding_cost=holding,
                         backlog_cost=backlog_charge, order_cost=setup, total_cost=cost))
    if queue or pending:
        raise ValueError("invalid runoff completion: residual backlog or pipeline")
    # Conservation covers both scored obligations and all receipts through runoff.
    fulfilled = sum(row["fulfilled_units"] for row in days)
    prior_units = sum(row["quantity"] for row in commitments)
    new_units = sum(demand)
    assert on_hand + sum(row["receipts"] for row in days) == fulfilled + stock
    assert new_units + prior_units == fulfilled

    scored_days = days[:n]
    immediate_units = sum(row["immediately_filled_units"] for row in scored_days)
    cycle_starts = list(range(review_phase, n - review_days + 1, review_days))
    shortage_free = sum(not any(row["shortage"] for row in days[start:start + review_days])
                        for start in cycle_starts)
    origins = [row for row in reviews if not row["runoff"] and row["day"] + horizon <= n]
    absolute = signed = cumulative_absolute = Fraction(0)
    actual_units = 0
    for row in origins:
        actual = demand[row["day"]:row["day"] + horizon]
        errors = [predicted - observed for predicted, observed in zip(row["forecast"], actual)]
        absolute += sum(abs(error) for error in errors)
        signed += sum(errors)
        cumulative_absolute += abs(sum(errors))
        actual_units += sum(actual)
    points = len(origins) * horizon
    piece_days = sum(row["on_hand"] for row in scored_days)
    metrics = dict(new_demand_units=new_units, immediately_filled_units=immediate_units,
                   immediate_fill_rate=Fraction(immediate_units, new_units) if new_units else None,
                   eventually_filled_units=eventual_new,
                   eventual_fill_rate=Fraction(eventual_new, new_units) if new_units else None,
                   prior_commitment_units=prior_units, on_time_prior_units=on_time_prior,
                   on_time_prior_fill_rate=Fraction(on_time_prior, prior_units) if prior_units else None,
                   complete_cycles=len(cycle_starts), shortage_free_cycles=shortage_free,
                   cycle_service=Fraction(shortage_free, len(cycle_starts)) if cycle_starts else None,
                   shortage_days=sum(row["shortage"] for row in scored_days),
                   newly_unmet_units=sum(row["newly_unmet_units"] for row in scored_days),
                   backlog_piece_days=sum(row["backlog"] for row in scored_days),
                   on_hand_piece_days=piece_days, average_on_hand=Fraction(piece_days, n),
                   end_on_hand=scored_days[-1]["on_hand"], end_backlog=scored_days[-1]["backlog"],
                   order_count=sum(row["order_qty"] > 0 for row in reviews if not row["runoff"]),
                   runoff_order_count=sum(row["order_qty"] > 0 for row in reviews if row["runoff"]),
                   forecast_origins=len(origins), forecast_points=points,
                   forecast_actual_units=actual_units,
                   forecast_mae=absolute / points if points else None,
                   forecast_bias=signed / points if points else None,
                   forecast_wape=absolute / actual_units if actual_units else None,
                   forecast_cumulative_mae=cumulative_absolute / len(origins) if origins else None,
                   forecast_cumulative_bias=signed / len(origins) if origins else None,
                   scored_cost=scored_cost, runoff_cost=runoff_cost,
                   total_cost=scored_cost + runoff_cost)
    return dict(contract_version=CONTRACT_VERSION, days=days, reviews=reviews,
                metrics=metrics, terminal=dict(on_hand=stock, backlog=0, outstanding_qty=0, orders=[]),
                assumptions=dict(policy="periodic inventory-position order-up-to",
                                 demand_due="acceptance day", scored_days=n,
                                 runoff_days=runoff_days, horizon=horizon,
                                 residual_stock_value=0, costs="synthetic finite-window penalties"))


if __name__ == "__main__":
    result = simulate([2], [2, 2], method="naive", on_hand=0,
                      lead_days=1, review_days=1)
    assert [day["receipts"] for day in result["days"][:2]] == [0, 4]
    assert result["metrics"]["immediate_fill_rate"] == Fraction(1, 2)
    assert result["metrics"]["eventual_fill_rate"] == 1
    assert result["metrics"]["newly_unmet_units"] == 2
    assert result["terminal"]["backlog"] == result["terminal"]["outstanding_qty"] == 0
    print("decision smoke checks passed")
