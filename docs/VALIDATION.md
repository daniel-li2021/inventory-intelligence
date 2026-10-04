# Independent validation

Use focused checks for the affected behavior; retained historical outcomes and
CI environments are in [EVIDENCE](EVIDENCE.md#acceptance-history). Database acceptance
uses real PostgreSQL, not SQLite/mocks. Missing modules, URLs, schemas or database
are errors, never skipped tests.

## Independent arithmetic and evidence

`tests/golden.py` inserts its own fixture without the generator or checker SQL.

| SKU / warehouse | Opening | Eligible signed movements | Expected |
|---|---:|---|---:|
| shirt / a | 100 | +10 −7 −5 +7 +4 | 109 |
| shirt / b | 20 | +5 | 25 |
| coat / a | 10 | +2 +3 | 15 |
| zero / a | 0 | no movements | 0 |

Shipment −7 and posted reversal +7 both remain; coat receipts have distinct lines
and occur at the inclusive cutoff. Transfer legs share the upstream sequence.
Pending, opening-instant, after-cutoff and above-watermark rows are excluded;
a higher-sequence late observation is excluded even if effective before cutoff.
Snapshot age exactly 24 hours passes; one microsecond older fails.

Mutating each snapshot by +1 proves all four keys are assessed. Assert exact rule,
reason, source identity, bucket, quantity/delta and null semantics; counts alone
are insufficient. Generator cases have separate expected findings, including jacket
expected 25 / observed 26 / delta +1. Duplicate evidence may span buckets.

Controls cover references, transfer legs, openings/snapshots, manifest counts/coverage,
clocks, clean/blocked cases and integers above float precision. Repeats compare
semantics excluding run IDs and require distinct persisted runs, exact saved children
and unchanged source rows. Forced child failure requires full transaction rollback;
runtime-role writes/DDL require permission denial. CLI: 0 clean, 1 dirty, 2 execution
or configuration error. [Planner/Lab/Copilot oracles](RESULTS.md).

## PostgreSQL acceptance

Use the pinned environment and a **fresh disposable** Compose project from
[README](../README.md#independent-acceptance). Owner `TEST_DATABASE_URL` and restricted
`DATABASE_URL` select the same database. Compose initializes schemas. Run once:

```sh
python -m unittest discover -s tests -v
```

Without Compose initialization, first run `python -m tests.bootstrap`; it reads
`sql/schema.sql` and refuses an existing operational schema. Loaders retain source
inputs/history and refuse overwritten namespaces. Another full suite needs another
fresh database; individual golden tests use unique namespaces. Never reset a demo.

## Documentation and retained provenance

```sh
python3 scripts/check_docs.py
python3 -m json.tool docs/research/repositories.json > /dev/null
git diff --check
PYTHONPATH=src python -m unittest tests.test_research_lineage tests.test_decision_benchmark.DecisionBenchmarkTests.test_retained_artifact_inputs_hashes_and_settled_obligations -v
```

The last command checks current lineage/corruption controls and retained exact-input,
source-hash/settlement evidence without a database/model call or study replay. Use it
when documentation affects source bindings. Historical source-view audits are
[separate](EVIDENCE.md#reproduce-without-rewriting-evidence); never overwrite a manifest.

CI separates hygiene from real PostgreSQL acceptance, with pinned Python 3.12.12,
PostgreSQL 17.9, Psycopg 3.3.6 and full Git history for lineage. No business secrets,
external operational data or deployment is involved. Green CI does not prove branch
protection, current deployment or service capacity.
