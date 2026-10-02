"""Exact baseline arithmetic for already validated, daily demand observations.

This kernel does not infer demand from inventory movements or approve source data.
Run this module to print a small synthetic benchmark, without database writes.
"""

from fractions import Fraction
import json

METHODS = ("naive", "mean", "seasonal_naive")


def _positive(name, value):
    if type(value) is not int or value < 1:
        raise ValueError(f"{name} must be a positive integer")


def _pieces(values):
    values = tuple(values)
    if not values or any(type(value) is not int or value < 0 for value in values):
        raise ValueError("observations must be nonempty, nonnegative integer pieces")
    return values


def forecast(history, *, method, horizon, season_length=7):
    """Return exact point estimates; fractional expected demand is not physical stock."""
    history = _pieces(history)
    _positive("horizon", horizon)
    _positive("season_length", season_length)
    if method == "naive":
        return [Fraction(history[-1])] * horizon
    if method == "mean":
        return [Fraction(sum(history), len(history))] * horizon
    if method == "seasonal_naive":
        if len(history) < season_length:
            raise ValueError("seasonal_naive needs at least one complete season")
        season = history[-season_length:]
        return [Fraction(season[i % season_length]) for i in range(horizon)]
    raise ValueError(f"unknown baseline method: {method}")


def backtest(observations, *, min_train=14, horizon=7, step=7, season_length=7):
    """Compare all baselines at identical rolling origins using only earlier values.

    Origins are training lengths (exclusive slice ends). Each fold scores all
    horizon points. Overlapping folds, when requested, score each origin/lead pair.
    Fraction scores preserve exact arithmetic; WAPE is unavailable on all-zero truth.
    """
    observations = _pieces(observations)
    for name, value in (("min_train", min_train), ("horizon", horizon),
                        ("step", step), ("season_length", season_length)):
        _positive(name, value)
    if min_train < season_length:
        raise ValueError("min_train must cover a complete season for fair comparison")
    if len(observations) < min_train + horizon:
        raise ValueError("not enough history for one complete evaluation fold")
    folds = []
    absolute = dict.fromkeys(METHODS, 0)
    signed = dict.fromkeys(METHODS, 0)
    actual_total = 0
    for origin in range(min_train, len(observations) - horizon + 1, step):
        actual = observations[origin:origin + horizon]
        predictions = {method: forecast(observations[:origin], method=method,
                                       horizon=horizon, season_length=season_length)
                       for method in METHODS}
        for method, predicted in predictions.items():
            errors = [p - a for p, a in zip(predicted, actual)]
            absolute[method] += sum(abs(error) for error in errors)
            signed[method] += sum(errors)
        actual_total += sum(actual)
        folds.append(dict(origin=origin, actual=list(actual), predictions=predictions))
    count = len(folds) * horizon
    return dict(horizon=horizon, season_length=season_length, folds=folds,
                scored_points=count, scores={method: dict(
                    mae=Fraction(absolute[method], count),
                    bias=Fraction(signed[method], count),
                    wape=Fraction(absolute[method], actual_total) if actual_total else None,
                ) for method in METHODS})


if __name__ == "__main__":
    # Hand-specified weekly demand; this is a mathematical demo, not a data adapter.
    report = backtest([1, 2, 3, 4, 5, 6, 7] * 5)
    print(json.dumps(report, default=str, indent=2, sort_keys=True))
