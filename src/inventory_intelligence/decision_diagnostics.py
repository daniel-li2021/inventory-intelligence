"""Offline evaluation diagnostics; never inputs to an ordering policy."""

from fractions import Fraction

from .decision import _integer, _observations, _rate, _rows


def startup_feasibility(demand, *, on_hand, lead_days, review_days,
                        review_phase=0, commitments=(), inbound=(), supplier_delays=()):
    """Bound immediate fill before any new order could arrive, with FIFO priority.

    Hidden delays and future demand are used for evaluation only. Every scored
    review is considered, including reviews at which the actual policy orders zero.
    """
    demand = _observations("demand", demand)
    n = len(demand)
    stock = _integer("on_hand", on_hand)
    lead = _integer("lead_days", lead_days, 1)
    review = _integer("review_days", review_days, 1)
    phase = _integer("review_phase", review_phase)
    if phase >= review or lead + review > 366:
        raise ValueError("invalid review phase or lead/review horizon")
    commitments = _rows("commitments", commitments, "due_day", n)
    inbound = _rows("inbound", inbound, "arrival_day", n)
    try:
        delays = tuple(supplier_delays)
    except TypeError as error:
        raise ValueError("supplier_delays must be a sequence") from error
    for delay in delays:
        _integer("supplier delay", delay)
    stop = n + lead + max(delays, default=0) + review
    if delays and len(delays) != len(range(phase, stop, review)):
        raise ValueError("supplier_delays must cover all scored and runoff review slots")
    earliest = min((day + lead + (delays[day // review] if delays else 0)
                    for day in range(phase, n, review)), default=None)
    startup_days = min(n, earliest) if earliest is not None else n
    backlog = new_misses = prior_misses = 0
    days = []
    for day in range(startup_days):
        stock += sum(row["quantity"] for row in inbound if row["arrival_day"] == day)
        # Every old due unit outranks today's commitments and new demand.
        filled = min(stock, backlog)
        stock -= filled
        backlog -= filled
        prior = sum(row["quantity"] for row in commitments if row["due_day"] == day)
        prior_unmet = max(0, prior - stock)
        stock = max(0, stock - prior)
        immediate = min(stock, demand[day])
        stock -= immediate
        new_unmet = demand[day] - immediate
        backlog += prior_unmet + new_unmet
        prior_misses += prior_unmet
        new_misses += new_unmet
        days.append(dict(day=day, on_hand=stock, backlog=backlog,
                         new_missed_units=new_unmet, prior_missed_units=prior_unmet))
    total = sum(demand)
    return dict(earliest_possible_order_receipt_day=earliest, startup_days=startup_days,
                new_demand_units=total, inevitable_new_missed_units=new_misses,
                inevitable_prior_missed_units=prior_misses,
                immediate_fill_ceiling=Fraction(total - new_misses, total) if total else None,
                days=days)


def common_window_costs(simulation, *, holding_cost, end_day):
    """Extend a settled simulator result to [0,end_day), charging terminal stock.

    Accepts native exact simulator results or their rational-string JSON form.
    This assumes the unchanged no-new-demand runoff policy, not continuing sales.
    """
    end_day = _integer("end_day", end_day, 1)
    rate = _rate("holding_cost", holding_cost)
    days = simulation["days"]
    terminal = simulation["terminal"]
    if not days or [row["day"] for row in days] != list(range(len(days))):
        raise ValueError("simulation must have contiguous accounting days")
    if end_day < len(days):
        raise ValueError("common window cannot truncate original runoff")
    stock = _integer("terminal stock", terminal["on_hand"])
    if (terminal["backlog"] != 0 or terminal["outstanding_qty"] != 0 or terminal["orders"]
            or days[-1]["backlog"] != 0 or days[-1]["outstanding_qty"] != 0
            or days[-1]["on_hand"] != stock):
        raise ValueError("common window requires a settled terminal state")
    def charge(value):
        if type(value) not in (int, Fraction, str):
            raise ValueError("cost must be an exact nonnegative rational")
        result = Fraction(value)
        if result < 0:
            raise ValueError("cost must be nonnegative")
        return result
    scored = sum((charge(row["total_cost"]) for row in days if row["scored"]), Fraction(0))
    runoff = sum((charge(row["total_cost"]) for row in days if not row["scored"]), Fraction(0))
    extension = (end_day - len(days)) * stock * rate
    return dict(scored_days=sum(row["scored"] for row in days), original_days=len(days),
                common_days=end_day, extension_days=end_day - len(days), terminal_on_hand=stock,
                scored_cost=scored, original_runoff_cost=runoff, original_total_cost=scored + runoff,
                extension_holding_cost=extension, common_runoff_cost=runoff + extension,
                common_total_cost=scored + runoff + extension)
