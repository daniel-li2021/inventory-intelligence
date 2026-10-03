"""Research-only retention of completed residuals; no product retirement rules."""

from fractions import Fraction
from math import ceil

from . import decision, intermittent

VERSION = "safety-retention-v1"
RETENTIONS = ("expanding", "recent", "decay")


def retained_quantile(errors, *, quantile, retention, window=12,
                      decay=Fraction(4, 5), min_samples=8):
    """Compute an exact empirical/weighted quantile without inventing samples."""
    errors = tuple(errors)
    if any(type(value) not in (int, Fraction) for value in errors):
        raise ValueError("residuals must be exact signed quantities")
    q = intermittent._probability("quantile", quantile)
    decision._integer("window", window, 1)
    decision._integer("min_samples", min_samples, 1)
    decay = intermittent._probability("decay", decay)
    if retention not in RETENTIONS:
        raise ValueError("unknown retention policy")
    selected = errors[-window:] if retention == "recent" else errors
    if len(selected) < min_samples:
        raise ValueError("insufficient complete retained calibration samples")
    weights = ([decay ** age for age in reversed(range(len(selected)))]
               if retention == "decay" else [Fraction(1)] * len(selected))
    mass = sum(weights, Fraction(0))
    threshold = q * mass
    cumulative = Fraction(0)
    for error, weight in sorted(zip(selected, weights), key=lambda pair: pair[0]):
        cumulative += weight
        if cumulative >= threshold:
            error_q = Fraction(error)
            break
    return dict(errors=list(selected), count=len(selected), source_count=len(errors),
                quantile=q, quantile_error=error_q, safety_qty=max(0, ceil(error_q)),
                retention=retention, weights=weights, threshold_mass=threshold,
                effective_sample_count=mass * mass / sum(weight * weight for weight in weights),
                rank=ceil(q * len(selected)) if retention != "decay" else None)


def calibrate(history, *, method, horizon, quantile, retention,
              window=12, decay=Fraction(4, 5), min_train=28, min_samples=8):
    """Fit on full origin-known prefixes, retain only completed target errors."""
    original = intermittent.calibrate(history, method=method, horizon=horizon,
        quantile=quantile, min_train=min_train, min_samples=min_samples)
    result = retained_quantile(original["errors"], quantile=quantile,
                              retention=retention, window=window, decay=decay, min_samples=min_samples)
    result["origins"] = original["origins"][-result["count"]:]
    return result


def simulate(history, demand, *, method="tsb", retention=None,
             quantile=Fraction(9, 10), **decision_inputs):
    """Reuse event timing and point forecasts while changing residual retention."""
    history, _, _ = intermittent._inputs(history, method, 1,
                                         intermittent.DEFAULT_ALPHA, intermittent.DEFAULT_BETA)
    demand = decision._observations("demand", demand)
    if retention is not None:
        if retention not in RETENTIONS:
            raise ValueError("unknown retention policy")
        quantile = intermittent._probability("quantile", quantile)
    if decision_inputs.get("safety_qty", 0) != 0:
        raise ValueError("retention experiment requires safety_qty=0")

    def provider(completed, horizon):
        predictions = intermittent.forecast(completed, method=method, horizon=horizon)
        calibration = (calibrate(completed, method=method, horizon=horizon,
                                 quantile=quantile, retention=retention)
                       if retention is not None else None)
        safety = calibration["safety_qty"] if calibration else 0
        return dict(forecast=predictions, safety_qty=safety, calibration=calibration,
                    protection_target=ceil(sum(predictions) + safety))

    result = decision._simulate(history, demand, method=method,
                                _review_provider=provider, **decision_inputs)
    result["research_version"] = VERSION
    result["parameters"] = dict(method=method, retention=retention,
                                quantile=quantile if retention is not None else None)
    return result
