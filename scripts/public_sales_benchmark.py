"""Train-only UCI item selection and aggregate rolling observed-sales scores."""

import argparse
from collections import Counter, defaultdict
from datetime import date
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random

from inventory_intelligence import intermittent, public_sales as sales
from scripts.public_sales_adapter import prepare

VERSION = "uci-observed-sales-forecast-v1"
METHODS = ("naive", "mean", "seasonal_naive", "zero", "croston", "sba", "tsb")
HORIZONS = (7, 14, 28)
TRAIN_END = (date(2011, 9, 16) - sales.SOURCE_START).days
HOLDOUT_START = (date(2011, 11, 11) - sales.SOURCE_START).days
END = (sales.SOURCE_LAST_DAY - sales.SOURCE_START).days
SPLITS = dict(selection=(TRAIN_END, HOLDOUT_START), holdout=(HOLDOUT_START, END))


def canonical(value):
    """Keep exact large aggregate rationals without changing Python safety limits."""
    def exact(value):
        if isinstance(value, Fraction):
            return dict(numerator_hex=format(value.numerator, "x"),
                        denominator_hex=format(value.denominator, "x"))
        raise TypeError(f"unsupported JSON value: {type(value).__name__}")
    return json.dumps(value, default=exact, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def select_items(adapted, *, limit=32, seed=701):
    """Use training-seen identities and training-only sparsity/volume strata."""
    if adapted["audit"]["status"] != "assessable" or adapted["series"] is None:
        raise ValueError("complete attested extraction required")
    if type(limit) is not int or limit < 1 or type(seed) is not int:
        raise ValueError("invalid frozen subset arguments")
    features = {}
    for item, seen in adapted["source_seen_days"].items():
        if not any(day < "2011-09-16" for day in seen):
            continue
        values = adapted["series"][item]
        if len(values) != END + 1 or any(type(v) is not int or v < 0 for v in values):
            raise ValueError("invalid complete observed-sales calendar")
        train = values[:TRAIN_END]
        features[item] = dict(positive_day_rate=Fraction(sum(v > 0 for v in train), TRAIN_END),
                             training_units=sum(train))
    positive = sorted(f["training_units"] for f in features.values() if f["training_units"] > 0)
    median = Fraction(positive[(len(positive) - 1) // 2] + positive[len(positive) // 2], 2) if positive else Fraction(0)
    bins = defaultdict(list)
    for item, f in features.items():
        rate = f["positive_day_rate"]
        sparsity = "zero" if rate == 0 else "sparse" if rate <= Fraction(1, 10) else "medium" if rate <= Fraction(1, 2) else "dense"
        f["bin"] = sparsity if sparsity == "zero" else sparsity + (":low_volume" if f["training_units"] <= median else ":high_volume")
        bins[f["bin"]].append(item)
    rng = random.Random(seed)
    pools = {}
    for name in sorted(bins):
        pool = sorted(bins[name]); rng.shuffle(pool)
        pools[name] = pool[:1] if name == "zero" else pool
    chosen = []
    while len(chosen) < limit and any(pools.values()):
        for name in sorted(pools):
            if pools[name] and len(chosen) < limit:
                chosen.append(pools[name].pop())
    if not chosen:
        raise ValueError("no training-known item identities")
    return dict(seed=seed, limit=limit, selected=chosen, features={k: features[k] for k in chosen},
                training_known_items=len(features), training_volume_median=median,
                eligible_bin_counts={k: len(v) for k, v in sorted(bins.items())})


def scores(values, *, method, start, end, horizon):
    """Keep exact sufficient statistics; all targets end within the named split."""
    if not 7 <= start < end <= len(values) or type(horizon) is not int or horizon < 1:
        raise ValueError("invalid score boundaries")
    absolute = signed = cumulative = Fraction(0)
    units = origins = 0
    receipts = []
    for origin in range(start, end - horizon + 1, 7):
        prediction = intermittent.forecast(values[:origin], method=method, horizon=horizon)
        actual = values[origin:origin + horizon]
        errors = [p - a for p, a in zip(prediction, actual)]
        absolute += sum(abs(v) for v in errors); signed += sum(errors)
        cumulative += abs(sum(errors)); units += sum(actual); origins += 1
        receipts.append(dict(origin=origin, forecast_sha256=digest(prediction), actual_sha256=digest(actual)))
    return dict(origins=origins, points=origins * horizon, actual_units=units,
                absolute_error=absolute, signed_error=signed,
                cumulative_absolute_error=cumulative, origin_receipts=receipts)


def aggregate(results):
    n = sum(r["origins"] for r in results); p = sum(r["points"] for r in results)
    units = sum(r["actual_units"] for r in results)
    a = sum((r["absolute_error"] for r in results), Fraction(0))
    s = sum((r["signed_error"] for r in results), Fraction(0))
    c = sum((r["cumulative_absolute_error"] for r in results), Fraction(0))
    return dict(items=len(results), origins=n, points=p, actual_units=units,
                absolute_error=a, signed_error=s, cumulative_absolute_error=c,
                mae=a / p if p else None, bias=s / p if p else None, wape=a / units if units else None,
                cumulative_mae=c / n if n else None, cumulative_bias=s / n if n else None)


def evaluate(adapted):
    subset = select_items(adapted)
    items = {}
    for item in subset["selected"]:
        values = adapted["series"][item][:END]
        start, end = SPLITS["selection"]
        result = {"selection": {str(h): {m: scores(values, method=m, start=start, end=end, horizon=h)
            for m in METHODS} for h in HORIZONS}}
        chosen = min(METHODS, key=lambda m: result["selection"]["28"][m]["cumulative_absolute_error"]
                                           / result["selection"]["28"][m]["origins"])
        start, end = SPLITS["holdout"]
        result["holdout"] = {str(h): {m: scores(values, method=m, start=start, end=end, horizon=h)
            for m in METHODS} for h in HORIZONS}
        items[item] = dict(selected_method=chosen, bin=subset["features"][item]["bin"], scores=result)
    groups = ("overall", *sorted({r["bin"] for r in items.values()}))
    aggregates = {split: {str(h): {group: {m: aggregate([
        r["scores"][split][str(h)][r["selected_method"] if m == "selection_chosen" else m]
        for r in items.values() if group == "overall" or r["bin"] == group])
        for m in (*METHODS, "selection_chosen")} for group in groups}
        for h in HORIZONS} for split in SPLITS}
    public = dict(protocol_version=VERSION, observed_sales_only=True,
        rational_encoding="signed hexadecimal numerator/denominator strings; decode with int(value,16)",
        target="gross positive non-cancelled invoiced units", availability="unknown", unconstrained_demand="unknown",
        subset_sha256=digest(subset), selected_items=len(items), training_known_items=subset["training_known_items"],
        eligible_bin_counts=subset["eligible_bin_counts"], selected_bin_counts=dict(Counter(r["bin"] for r in items.values())),
        selected_method_counts=dict(Counter(r["selected_method"] for r in items.values())), methods=METHODS, horizons=HORIZONS,
        source_start="2010-12-01", selection_start="2011-09-16", holdout_start="2011-11-11", end_exclusive="2011-12-09",
        excluded_final_source_day=True, release_assumption="modeled end of source date", aggregate_scores=aggregates,
        limits=["Observed sales do not prove availability, unconstrained demand or historical stockouts.",
                "One retailer and dependent items/origins; no population confidence or operational promotion.",
                "Selection-chosen selection scores are optimistic; holdout evaluates the frozen choice.",
                "Forecast-only; synthetic-stock policy/safety grid is separate unfinished work.",
                "No price/customer/country features or advanced models."])
    return public, dict(subset=subset, item_results=items)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw/uci-online-retail"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt, adapted_path = prepare(args.raw_dir)
    public, local = evaluate(json.loads(adapted_path.read_text()))
    root = Path(__file__).resolve().parents[1]
    sources = ("docs/EVIDENCE.md", "scripts/public_sales_benchmark.py",
               "src/inventory_intelligence/intermittent.py", "src/inventory_intelligence/decision.py",
               "src/inventory_intelligence/forecasting.py")
    public.update(attribution=sales.ATTRIBUTION, source_url=sales.SOURCE_URL, license_url=sales.LICENSE_URL,
        archive_sha256=receipt["archive_sha256"], adapter_sha256=receipt["transform_sha256"],
        adapter_artifact_sha256=receipt["artifact_sha256"], extraction_counts=receipt["audit"]["counts"],
        source_sha256={name: sales.sha256_file(root / name) for name in sources},
        acquisition=json.loads((args.raw_dir / "source-manifest.json").read_text()))
    local_path = args.raw_dir / f"benchmark-{digest(public)[:12]}.json"
    if not local_path.exists():
        local_path.write_bytes(canonical(local) + b"\n")
    elif local_path.read_bytes() != canonical(local) + b"\n":
        raise ValueError("existing local benchmark evidence changed")
    public["local_item_results_sha256"] = sales.sha256_file(local_path)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(args.output.name + ".tmp")
    temporary.write_bytes(canonical(public) + b"\n"); temporary.replace(args.output)
    print(json.dumps(dict(selected_items=public["selected_items"], selected_bins=public["selected_bin_counts"],
                          selected_methods=public["selected_method_counts"]), sort_keys=True))


if __name__ == "__main__":
    main()
