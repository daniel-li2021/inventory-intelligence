# Milestone 1 reliability engine

The engine implements the frozen [v1 contract](CONTRACT_V1.md). It reads existing
operational batches and appends reliability runs, check results, and findings.
It never creates schemas, loads fixtures, repairs inputs, or replaces previous
results. Source batches and rows referenced by runs must remain available.

## Installation and inputs

Use Python 3.12 and PostgreSQL 17. Install from the engine checkout:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install .
```

Psycopg and its binary extra are pinned to `3.3.6`; the build backend is pinned
to setuptools `80.9.0`. No ORM or quality framework is used. SQL files are
included in the wheel. An editable install (`pip install -e .`) also works.

Provision `sql/schema.sql`, the `ii_runner` role, and synthetic inputs using the
data foundation before running the checker. See `docs/DATA.md` when that branch
is integrated. Set `DATABASE_URL` to that runtime role's connection string.
The CLI verifies `current_user = 'ii_runner'`. Database grants enforce SELECT
on operational inputs and SELECT/INSERT on reliability outputs; no runtime DDL
or operational write privileges are required. The library accepts any idle
Psycopg connection with `autocommit=True`, including a custom row factory.

## CLI and library

```sh
export DATABASE_URL='postgresql://ii_runner:LOCAL_SYNTHETIC_PASSWORD@localhost:5432/inventory'
.venv/bin/python -m inventory_intelligence \
  --ledger-batch clean-ledger --snapshot-batch clean-snapshot \
  --as-of 2026-10-01T00:00:00Z --evaluated-at 2026-10-02T00:00:00Z \
  --format json --code-version "$(git rev-parse HEAD)"

# Substitute the actual batch IDs/cutoffs returned by the fixture loader.
# Use --format markdown for a readable report with full finding evidence.
```

Required flags are `--ledger-batch`, `--snapshot-batch`, `--as-of`, and
`--evaluated-at`. Format defaults to JSON. `--max-snapshot-age-hours` defaults
to 24 and accepts a nonnegative integer; `--code-version` defaults to `dev`.
CLI timestamps require an explicit timezone and are normalized to UTC. Exactly
24 hours is fresh; a future snapshot cutoff is a metadata failure.

```python
import psycopg
from inventory_intelligence.reliability import run_checks

with psycopg.connect(database_url, autocommit=True) as conn:
    report = run_checks(
        conn,
        ledger_batch_id=context["ledger_batch_id"],
        snapshot_batch_id=context["snapshot_batch_id"],
        as_of=context["as_of"],
        evaluated_at=context["evaluated_at"],
        code_version="dev",
    )
```

Library datetime arguments must be aware UTC `datetime` values. Invalid
arguments and non-idle/non-autocommit connections raise `ValueError`; database
and SQL-resource errors propagate to the caller. The connection remains the
caller's responsibility. Each successful call returns the exact v1 report
shape with five sorted rule results, sorted source IDs/findings, UTC ISO 8601
timestamps, deterministic SHA-256 finding IDs, and a new UUID run ID.

CLI exit codes:

| Exit | Meaning |
| --- | --- |
| 0 | Successful execution; all checks pass |
| 1 | Successful execution; fail or not assessable |
| 2 | Configuration, connection, query, or persistence error |

Reports go to stdout and errors to stderr. Driver errors report their class
and SQLSTATE when available, avoiding connection-string/credential output.
An execution error rolls back the complete run, including any inserted results;
it does not generate a passing report. A successful fail/not-assessable run is
persisted, just like a passing run.

## SQL and assessment

`sql/views.sql` supplies read-only CTE projections; `sql/checks.sql` supplies
the checks and assessment gates. They form one parameterized query. No installed
views or schema-creation privileges are needed. Reading, checking, and inserting
results happen in one Repeatable Read transaction. The transaction sets its
local timezone to UTC so evidence is stable across caller session timezones.

| Rule | Implemented comparison |
| --- | --- |
| R001 | Exact opening plus eligible signed movements against independent snapshot |
| R002 | Duplicate selected-ledger natural leg keys; identical and conflicting duplicates both block |
| R003 | Movement/opening/snapshot references and covered opening existence, uniqueness, cutoff |
| R004 | Eligible transfer pairs: two legs, one SKU/time/sequence, different warehouses, nonzero opposite quantities |
| R005 | Both manifests, raw counts, cutoff/watermark metadata, freshness, explicit coverage, snapshot existence/uniqueness |

Eligibility is posted, `baseline_at < effective_at <= as_of`, and
`source_seq <= ledger.watermark`. Pending rows, later effective times, and
higher-sequence arrivals are excluded from arithmetic, identity, and transfer
checks. Posted reversals are summed as signed legs; their originals remain in
the sum. Reference validation examines all selected source rows, including
ineligible movements, and preserves their evidence. Unknown references include
SKU, warehouse, SKU style, and non-null reversal row references. Freshness is
checked on the manifest and available snapshot rows; row cutoff/watermark
disagreement is also a metadata defect.

Manifest, count, metadata, freshness, and coverage defects suppress every
quantity comparison. Opening, reference, duplicate-leg, transfer, and snapshot
defects suppress their affected buckets while other buckets can still produce
quantity findings. A conflicting identity group blocks every bucket represented
by its rows. Missing data never supplies a zero or a manufactured delta.

An incomplete/missing ledger, unusable eligibility metadata, or raw-count
mismatch cannot prove transfer pairing: R004 is not assessable and emits no
missing-leg conclusion. Available identity/reference defects can still fail
their rules. Any emitted finding makes its rule fail; otherwise a blocked
required comparison is not assessable. Overall status follows fail, then not
assessable, then pass. All findings have error severity; quantities are null
outside R001. Evidence retains raw source records, manifests, business times,
source sequence, recording/observation times, and baseline/transfer references.

## Validation and current limits

The small maintained orchestration check is:

```sh
.venv/bin/python -m inventory_intelligence.selfcheck
```

It checks stable sorting/IDs, status precedence, exact JSON quantities, UTC
parsing, report rendering, and availability of packaged SQL. It does **not**
replace independent database acceptance tests.

With a preloaded clean fixture, enable its database smoke check by supplying the
loader's context as JSON (no fixture loading or source writes occur):

```sh
export ENGINE_CLEAN_CONTEXT='{"ledger_batch_id":"clean-ledger","snapshot_batch_id":"clean-snapshot","as_of":"2026-10-01T00:00:00Z","evaluated_at":"2026-10-02T00:00:00Z"}'
.venv/bin/python -m inventory_intelligence.selfcheck
```

Substitute actual loader values and set `DATABASE_URL` as above. This asserts
all five clean outcomes, repeated semantic stability, and persisted check
results. Without this context the database check is explicitly skipped.

Engine-local validation used Python 3.12.14, Psycopg 3.3.6, and a temporary
PostgreSQL 17.6 database with a hand-built contract-shaped synthetic fixture.
Assertions covered clean multi-line/zero-stock/transfer/reversal controls,
cutoff/watermark/pending boundaries, exact quantities above `2**53`, individual
rules, faults on separate buckets, missing/duplicate openings and snapshots,
manifest/coverage/freshness failures, repeated semantic reports and persisted
history, runtime source-write denial, full rollback after denied finding
inserts, custom connection row factories, and CLI JSON/Markdown/exit behavior.
The installed wheel also passed all three maintained self-checks, including
the database smoke check, when run outside the source checkout.

The foundation branch did not yet supply `sql/schema.sql`, Compose, or
`synthetic.generate` at implementation time. Validation against that actual
bootstrap/loader and Agent 3's independent oracle remains pending. No Docker
integration or complete milestone acceptance is claimed here.

Quantities use PostgreSQL exact numeric arithmetic and are checked when
converted to the contract's bigint output fields. A total or delta outside
bigint range is an execution error with rollback. This implementation assumes
the frozen input column types/nullability and source-retention contract; it
does not validate arbitrary schemas or enforce retention for upstream writers.
