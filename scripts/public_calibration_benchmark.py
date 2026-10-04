"""Prospective disjoint-item calibration replication using attested UCI caches."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path

from inventory_intelligence import public_sales as sales, sales_safety as study
from scripts.public_sales_adapter import prepare
from scripts.public_sales_benchmark import END, TRAIN_END, canonical, digest, select_items
from scripts.public_safety_benchmark import aggregate, compact, decode, key, paired
from scripts.public_safety_audit import audit_arm, require

VERSION = "uci-disjoint-calibration-v1"
LIMIT = 32
SEED = 1709
ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/review/public-calibration-freeze-v1.json"
REPORT = ROOT / "docs/review/public-calibration-v1.json"
SOURCES = ("docs/EVIDENCE.md", "scripts/public_calibration_benchmark.py",
           "scripts/public_sales_benchmark.py", "scripts/public_safety_benchmark.py",
           "scripts/public_safety_audit.py", "src/inventory_intelligence/sales_safety.py",
           "src/inventory_intelligence/intermittent.py", "src/inventory_intelligence/decision.py",
           "src/inventory_intelligence/decision_diagnostics.py", "src/inventory_intelligence/forecasting.py")


def training_view(adapted):
    """Selection can access training quantities only; future dates do not qualify."""
    require(adapted["audit"]["status"] == "assessable" and adapted["series"] is not None,
            "complete attested extraction required")
    seen = {item: [day for day in dates if day < "2011-09-16"]
            for item, dates in adapted["source_seen_days"].items()
            if any(day < "2011-09-16" for day in dates)}
    series = {}
    for item in seen:
        prefix = adapted["series"][item][:TRAIN_END]
        require(len(prefix) == TRAIN_END, "incomplete training calendar")
        series[item] = prefix + [0] * (END + 1 - TRAIN_END)
    return dict(audit=adapted["audit"], source_seen_days=seen, series=series)


def select_disjoint(view, excluded, *, limit=LIMIT, seed=SEED):
    require(bool(excluded) and len(set(excluded)) == len(excluded), "invalid consumed identities")
    require(set(excluded) <= set(view["series"]), "consumed identity is not training-known")
    remaining = {name: {item: value for item, value in view[name].items() if item not in set(excluded)}
                 for name in ("series", "source_seen_days")}
    subset = select_items(dict(audit=view["audit"], **remaining), limit=limit, seed=seed)
    require(len(subset["selected"]) == limit, "insufficient disjoint training-known items")
    return subset


def grid():
    return {key(m, q, lead, delay): dict(method=m, quantile=q, lead_days=lead, delay=delay)
            for m in study.METHODS for q in study.QUANTILES for lead in study.LEADS for delay in study.DELAYS}


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(canonical(value) + b"\n"); temporary.replace(path)


def inputs(raw_dir):
    receipt, path = prepare(raw_dir)
    adapted = json.loads(path.read_text())
    parent_path = ROOT / "docs/review/public-sales-forecast-v1.json"
    parent = decode(parent_path.read_text())
    require(all(parent[name] == receipt[field] for name, field in
                (("archive_sha256", "archive_sha256"), ("adapter_sha256", "transform_sha256"),
                 ("adapter_artifact_sha256", "artifact_sha256"))), "parent source attestation differs")
    view = training_view(adapted)
    excluded = select_items(view)
    require(digest(excluded) == parent["subset_sha256"], "consumed subset differs from parent")
    subset = select_disjoint(view, excluded["selected"])
    attestation = dict(archive_sha256=receipt["archive_sha256"], adapter_sha256=receipt["transform_sha256"],
        adapter_artifact_sha256=receipt["artifact_sha256"], parent_forecast_sha256=sales.sha256_file(parent_path),
        parent_safety_sha256=sales.sha256_file(ROOT / "docs/review/public-sales-safety-v1.json"),
        source_sha256={name: sales.sha256_file(ROOT / name) for name in SOURCES})
    return adapted, subset, excluded, attestation


def freeze(raw_dir):
    _, subset, excluded, attestation = inputs(raw_dir)
    local = dict(subset=subset, excluded_subset=excluded)
    path = raw_dir / f"calibration-subset-{digest(local)[:12]}.json"
    if path.exists():
        require(decode(path.read_text()) == local, "frozen local subset changed")
    else:
        write(path, local)
    manifest = dict(protocol_version=VERSION, frozen_at_utc=datetime.now(timezone.utc).isoformat(),
        **attestation, subset_sha256=digest(subset), excluded_subset_sha256=digest(excluded),
        local_subset_sha256=sales.sha256_file(path), local_subset_name=path.name,
        selected_items=len(subset["selected"]), excluded_items=len(excluded["selected"]), overlap_items=0,
        selected_bin_counts=dict(Counter(f["bin"] for f in subset["features"].values())),
        eligible_bin_counts=subset["eligible_bin_counts"], eligible_items=subset["training_known_items"],
        selection_seed=SEED, configurations=grid(), score_rule="all fixed arms; no selection/promotion",
        dates=dict(training_end="2011-09-16", warmup_days=56, holdout_start="2011-11-11",
                   holdout_days=28, end_exclusive="2011-12-09", common_settlement_days=15))
    if MANIFEST.exists():
        existing = decode(MANIFEST.read_text())
        manifest["frozen_at_utc"] = existing["frozen_at_utc"]
        require(existing == manifest, "published freeze changed; do not replace consumed evidence")
    else:
        write(MANIFEST, manifest)
    return dict(items=len(subset["selected"]), excluded=len(excluded["selected"]), overlap=0,
                training_bins=manifest["selected_bin_counts"], manifest_sha256=sales.sha256_file(MANIFEST))


def frozen_inputs(raw_dir):
    require(MANIFEST.is_file(), "commit the subset/protocol freeze before scoring")
    manifest = decode(MANIFEST.read_text())
    adapted, subset, excluded, attestation = inputs(raw_dir)
    require(all(manifest[name] == value for name, value in attestation.items()), "frozen source bytes changed")
    local_path = raw_dir / manifest["local_subset_name"]
    require(sales.sha256_file(local_path) == manifest["local_subset_sha256"], "frozen subset bytes changed")
    require(decode(local_path.read_text()) == dict(subset=subset, excluded_subset=excluded), "frozen selection changed")
    require(manifest["subset_sha256"] == digest(subset) and manifest["excluded_subset_sha256"] == digest(excluded),
            "subset lineage changed")
    require(manifest["configurations"] == grid() and manifest["selected_items"] == LIMIT
            and manifest["excluded_items"] == LIMIT and manifest["overlap_items"] == 0
            and not set(subset["selected"]) & set(excluded["selected"]), "frozen grid/identity boundary changed")
    return adapted, subset, manifest


def aggregates(local, configs):
    groups = ("overall", *sorted({r["bin"] for r in local["items"].values()}))
    scores, pairs = {}, {}
    for name, config in configs.items():
        scores[name], pairs[name] = {}, {}
        for group in groups:
            records = [r for r in local["items"].values() if group == "overall" or r["bin"] == group]
            current = [r["arms"][name] for r in records]
            scores[name][group] = aggregate(current, config["quantile"])
            if config["quantile"] is not None:
                baseline = key(config["method"], None, config["lead_days"], config["delay"])
                pairs[name][group] = paired(current, [r["arms"][baseline] for r in records])
    return scores, pairs


def verify_public(public, manifest):
    """Hashes alone do not establish semantic metadata or experiment boundaries."""
    expected = dict(protocol_version=VERSION, freeze_sha256=sales.sha256_file(MANIFEST),
        source_sha256=manifest["source_sha256"], subset_sha256=manifest["subset_sha256"],
        excluded_subset_sha256=manifest["excluded_subset_sha256"], selected_items=LIMIT,
        excluded_items=LIMIT, overlap_items=0, selected_bin_counts=manifest["selected_bin_counts"],
        dates=manifest["dates"], configurations=grid(), arms=768, paired_contrasts=512,
        observed_sales_only=True, availability="unknown", unconstrained_demand="unknown",
        attribution=sales.ATTRIBUTION, source_url=sales.SOURCE_URL, license_url=sales.LICENSE_URL)
    require(all(public.get(k) == v for k, v in expected.items()), "public semantic boundary changed")


def score(raw_dir):
    adapted, subset, manifest = frozen_inputs(raw_dir)
    # The freeze must already exist unchanged in HEAD, rather than only on disk.
    import subprocess
    committed = subprocess.check_output(["git", "show", "HEAD:docs/review/public-calibration-freeze-v1.json"], cwd=ROOT)
    require(committed == MANIFEST.read_bytes(), "freeze is not committed unchanged")
    attestation = dict(freeze_sha256=sales.sha256_file(MANIFEST), source_sha256=manifest["source_sha256"])
    cache_path = raw_dir / f"calibration-{digest(attestation)[:12]}.json"
    if cache_path.exists():
        cached = decode(cache_path.read_text())
        require(cached["attestation"] == attestation and digest(cached["payload"]) == cached["payload_sha256"], "cached calibration changed")
        if REPORT.exists():
            require(decode(REPORT.read_text())["local_evidence_sha256"] == sales.sha256_file(cache_path), "published local bytes changed")
        public = cached["payload"]["public"]
    else:
        local = dict(subset=subset, items={}, residuals={})
        for number, item in enumerate(subset["selected"], 1):
            values = adapted["series"][item]
            record = dict(history=values[:TRAIN_END], demand=values[TRAIN_END:END],
                          bin=subset["features"][item]["bin"], arms={})
            receipts = {}
            for name, config in manifest["configurations"].items():
                simulation, summary = study.simulate_arm(record["history"], record["demand"], **config)
                origins = [{k: r[k] for k in ("day", "forecast", "safety_qty", "calibration")}
                           for r in simulation["reviews"] if not r["runoff"]]
                identity = key(config["method"], config["quantile"], config["lead_days"], 0)
                require(identity not in receipts or receipts[identity] == digest(origins), "supply changed demand calibration")
                receipts[identity] = digest(origins)
                compact(simulation, local["residuals"])
                record["arms"][name] = dict(simulation=simulation, summary=summary,
                    trajectory_sha256=digest(simulation),
                    input_sha256=digest(dict(history=record["history"], demand=record["demand"], config=config)))
            local["items"][item] = record
            print(f"items {number}/{LIMIT}", flush=True)
        totals, pairs = aggregates(local, manifest["configurations"])
        public = dict(protocol_version=VERSION, **attestation, subset_sha256=manifest["subset_sha256"],
            excluded_subset_sha256=manifest["excluded_subset_sha256"], selected_items=LIMIT, excluded_items=LIMIT,
            overlap_items=0, selected_bin_counts=manifest["selected_bin_counts"], dates=manifest["dates"],
            arms=LIMIT * len(grid()), paired_contrasts=LIMIT * 16, configurations=grid(),
            aggregate_scores=totals, paired_safety_off=pairs, observed_sales_only=True,
            availability="unknown", unconstrained_demand="unknown", attribution=sales.ATTRIBUTION,
            source_url=sales.SOURCE_URL, license_url=sales.LICENSE_URL,
            evaluation_novelty="Prospectively frozen disjoint item outcomes; same source/calendar and prior-informed design, not statistical independence or later-time validation.",
            limits=["No model or policy selection/promotion; newly viewed outcomes become consumed.",
                    "Synthetic suppliers/backlog/costs; not historical retailer inventory or savings.",
                    "One retailer, correlated items/calendar and only three complete protection targets per item.",
                    "Nominal quantiles do not guarantee achieved fill, cycle service or target coverage."])
        payload = dict(public=public, local=local)
        write(cache_path, dict(attestation=attestation, payload=payload, payload_sha256=digest(payload)))
    verify_public(public, manifest)
    public = dict(public, local_evidence_sha256=sales.sha256_file(cache_path))
    write(REPORT, public)
    return dict(items=LIMIT, arms=public["arms"], pairs=public["paired_contrasts"], cache_bytes=cache_path.stat().st_size)


def audit(raw_dir):
    adapted, subset, manifest = frozen_inputs(raw_dir)
    public = decode(REPORT.read_text())
    verify_public(public, manifest)
    attestation = dict(freeze_sha256=sales.sha256_file(MANIFEST), source_sha256=manifest["source_sha256"])
    require(all(public[k] == v for k, v in attestation.items()), "report freeze attestation changed")
    cache_path = raw_dir / f"calibration-{digest(attestation)[:12]}.json"
    require(public["local_evidence_sha256"] == sales.sha256_file(cache_path), "local evidence bytes changed")
    cached = decode(cache_path.read_text()); payload = cached["payload"]
    require(cached["attestation"] == attestation and digest(payload) == cached["payload_sha256"], "cache receipt changed")
    require(payload["public"] == {k: v for k, v in public.items() if k != "local_evidence_sha256"}, "public receipt changed")
    local = payload["local"]
    require(local["subset"] == subset and set(local["items"]) == set(subset["selected"]), "scored item boundary changed")
    for item, record in local["items"].items():
        require(record["history"] == adapted["series"][item][:TRAIN_END]
                and record["demand"] == adapted["series"][item][TRAIN_END:END], "observations changed")
        require(record["bin"] == subset["features"][item]["bin"]
                and set(record["arms"]) == set(grid()), "segment/arm boundary changed")
        for name, config in grid().items():
            audit_arm(record, record["arms"][name], config, local["residuals"])
    totals, pairs = aggregates(local, grid())
    require(totals == public["aggregate_scores"] and pairs == public["paired_safety_off"], "aggregate outcomes changed")
    require(public["arms"] == 768 and public["paired_contrasts"] == 512 and public["overlap_items"] == 0, "denominator changed")
    return dict(arms=768, pairs=512, overlap_items=0, model_refits=0, simulation_replays=0,
                public_bytes=REPORT.stat().st_size, local_bytes=cache_path.stat().st_size)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("freeze", "score", "audit"))
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw/uci-online-retail"))
    args = parser.parse_args()
    print(json.dumps({"freeze": freeze, "score": score, "audit": audit}[args.action](args.raw_dir), sort_keys=True))
