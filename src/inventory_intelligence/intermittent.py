"""Exact intermittent-demand models and empirical safety for offline research."""

from fractions import Fraction
from functools import lru_cache
from math import ceil

from . import decision
from .forecasting import METHODS as BASELINE_METHODS, forecast as baseline_forecast

RESEARCH_VERSION = "intermittent-research-v1"
METHODS = (*BASELINE_METHODS, "zero", "croston", "sba", "tsb")
DEFAULT_ALPHA = DEFAULT_BETA = Fraction(1, 5)


def _probability(name, value):
    if type(value) not in (int, Fraction) or not 0 < value <= 1:
        raise ValueError(f"{name} must be an int or Fraction in (0, 1]")
    return Fraction(value)


def _inputs(history, method, horizon, alpha, beta):
    history = decision._observations("history", history)
    decision._integer("horizon", horizon, 1)
    if method not in METHODS:
        raise ValueError(f"unknown intermittent method: {method}")
    if method == "seasonal_naive" and len(history) < 7:
        raise ValueError("seasonal_naive needs seven history days")
    return history, _probability("alpha", alpha), _probability("beta", beta)


# ponytail: 8192 immutable fits/evidence entries; raise bound if larger experiments thrash.
@lru_cache(maxsize=8192)
def _forecast(history, method, horizon, alpha, beta):
    if method in BASELINE_METHODS:
        return tuple(baseline_forecast(history, method=method, horizon=horizon))
    if method == "zero":
        return (Fraction(0),) * horizon
    first = next((i for i, quantity in enumerate(history) if quantity), None)
    if first is None:
        return (Fraction(0),) * horizon
    size = Fraction(history[first])
    interval = Fraction(first + 1)
    probability = Fraction(1, first + 1)
    last = first
    for day in range(first + 1, len(history)):
        quantity = history[day]
        if quantity:
            size = alpha * quantity + (1 - alpha) * size
            if method != "tsb":
                interval = alpha * (day - last) + (1 - alpha) * interval
            last = day
        if method == "tsb":
            probability = beta * bool(quantity) + (1 - beta) * probability
    expected = size * probability if method == "tsb" else size / interval
    if method == "sba":
        expected *= 1 - alpha / 2
    return (expected,) * horizon


def forecast(history, *, method, horizon, alpha=DEFAULT_ALPHA, beta=DEFAULT_BETA):
    """Forecast exact daily expectations; return fresh lists, never cached mutables."""
    history, alpha, beta = _inputs(history, method, horizon, alpha, beta)
    return list(_forecast(history, method, horizon, alpha, beta))


@lru_cache(maxsize=8192)
def _errors(history, method, horizon, alpha, beta, min_train):
    origins = tuple(range(min_train, len(history) - horizon + 1, horizon))
    errors = tuple(Fraction(sum(history[origin:origin + horizon])) -
                   sum(_forecast(history[:origin], method, horizon, alpha, beta))
                   for origin in origins)
    return origins, errors


def calibrate(history, *, method, horizon, quantile, alpha=DEFAULT_ALPHA,
              beta=DEFAULT_BETA, min_train=28, min_samples=8):
    """Use completed, non-overlapping cumulative errors and nearest-rank quantiles."""
    history, alpha, beta = _inputs(history, method, horizon, alpha, beta)
    quantile = _probability("quantile", quantile)
    decision._integer("min_train", min_train, 1)
    decision._integer("min_samples", min_samples, 1)
    if method == "seasonal_naive" and min_train < 7:
        raise ValueError("seasonal_naive calibration needs seven training days")
    origins, errors = _errors(history, method, horizon, alpha, beta, min_train)
    if len(errors) < min_samples:
        raise ValueError(f"calibration needs at least {min_samples} complete samples")
    error_q = sorted(errors)[ceil(quantile * len(errors)) - 1]
    return dict(origins=list(origins), errors=list(errors), count=len(errors),
                quantile_error=error_q, safety_qty=max(0, ceil(error_q)))


def simulate(history, demand, *, method, alpha=DEFAULT_ALPHA, beta=DEFAULT_BETA,
             safety_quantile=None, **decision_inputs):
    """Research wrapper using the unchanged receipt/order/service event kernel."""
    history = decision._observations("history", history)
    demand = decision._observations("demand", demand)
    # Shared kernel validates horizon/L/R; model validation is independent of reviews.
    history, alpha, beta = _inputs(history, method, 1, alpha, beta)
    if safety_quantile is not None:
        safety_quantile = _probability("safety_quantile", safety_quantile)
        if decision_inputs.get("safety_qty", 0) != 0:
            raise ValueError("empirical safety requires safety_qty=0")
    parameters = dict(method=method, alpha=alpha, beta=beta,
                      safety_quantile=safety_quantile)

    def provider(completed, horizon):
        predictions = forecast(completed, method=method, horizon=horizon, alpha=alpha, beta=beta)
        calibration = (calibrate(completed, method=method, horizon=horizon,
                                 quantile=safety_quantile, alpha=alpha, beta=beta)
                       if safety_quantile is not None else None)
        safety = calibration["safety_qty"] if calibration is not None else decision_inputs.get("safety_qty", 0)
        return dict(forecast=predictions, safety_qty=safety, calibration=calibration,
                    parameters=dict(parameters), protection_target=ceil(sum(predictions) + safety))

    result = decision._simulate(history, demand, method=method,
                                _review_provider=provider, **decision_inputs)
    result["research_version"] = RESEARCH_VERSION
    result["parameters"] = parameters
    horizon = result["assumptions"]["horizon"]
    origins = [row for row in result["reviews"]
               if not row["runoff"] and row["day"] + horizon <= len(demand)]
    covered = 0
    loss = Fraction(0)
    for row in origins:
        actual = sum(demand[row["day"]:row["day"] + horizon])
        target = row["protection_target"]
        covered += actual <= target
        if safety_quantile is not None:
            error = actual - target
            loss += max(safety_quantile * error, (safety_quantile - 1) * error)
    result["metrics"].update(
        protection_target_origins=len(origins), protection_target_covered=covered,
        protection_target_coverage=Fraction(covered, len(origins)) if origins else None,
        protection_target_pinball_loss=loss / len(origins) if origins and safety_quantile is not None else None)
    return result
