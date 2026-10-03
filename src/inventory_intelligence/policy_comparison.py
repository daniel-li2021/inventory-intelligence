"""Research ordering rules; unchanged operational arithmetic, known supply only."""

from datetime import date, timedelta
from fractions import Fraction

from .decision import _integer, _simulate
from .replenishment import project

VERSION = "policy-comparison-v1"
POLICIES = ("periodic_up_to", "periodic_sS", "prefix_projection")
EPOCH = date(2000, 1, 1)


def ordering(policy, state):
    """Return raw need; the event kernel applies common whole-piece rounding."""
    day, lead = state["day"], state["lead_days"]
    target, position = state["target"], state["inventory_position"]
    if policy == "periodic_sS":
        trigger = sum(state["forecast"][:lead], Fraction(0)) + state["safety_qty"]
        trigger += sum(row["quantity"] for row in state["commitments"]
                       if row["due_day"] < day + lead)
        return dict(policy=policy, trigger=trigger, triggered=position <= trigger,
                    need=max(Fraction(0), target - position) if position <= trigger else Fraction(0))
    if policy != "prefix_projection":
        raise ValueError("unknown research ordering policy")
    origin = EPOCH + timedelta(days=day)
    reservations = [dict(status="open", remaining_qty=row["quantity"],
                         due_day=EPOCH + timedelta(days=row["due_day"]))
                    for row in state["commitments"]]
    reservations += [dict(status="open", remaining_qty=row["quantity"], due_day=origin)
                     for row in state["backlog"]]
    inbound = [dict(status="confirmed", remaining_qty=row["quantity"],
                    arrival_day=EPOCH + timedelta(days=row["arrival_day"]))
               for row in state["inbound"]]
    result = project(on_hand=state["on_hand"], forecasts=state["forecast"],
                     reservations=reservations, inbound=inbound, origin_day=origin,
                     policy={key: state[key] for key in
                             ("lead_days", "review_days", "pack_size", "moq", "safety_qty")})
    return dict(policy=policy, need=result["unrounded_need"], projection=result,
                carryover=[dict(row) for row in state["backlog"]])


def simulate_policy(history, demand, *, policy, **parameters):
    if policy not in POLICIES:
        raise ValueError("unknown research ordering policy")
    delays = tuple(parameters.get("supplier_delays", ()))
    for delay in delays:
        _integer("supplier delay", delay)
        if delay:
            raise ValueError("policy comparison requires known supply; hidden delays unsupported")
    parameters["supplier_delays"] = delays
    result = _simulate(history, demand, **parameters,
                       _order_provider=(None if policy == "periodic_up_to" else
                                        lambda state: ordering(policy, state)))
    result["research_protocol"] = VERSION
    result["assumptions"]["policy"] = policy
    result["assumptions"]["prefix_adapter"] = "arithmetic only; no operational source gates"
    return result
