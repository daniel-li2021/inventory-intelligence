# Operator guide

Use the [root quickstart](../README.md) for installation and a fresh demo. Use
[VALIDATION](VALIDATION.md) for tests and [CONTRACTS](CONTRACTS.md) for exact
interfaces. The [Lab guide](DECISION_LAB.md) and [hosting guide](../deploy/lab/README.md)
cover those entry points. Commands below use synthetic local credentials.


## Data fixtures

### Connection roles

`.env.example` contains synthetic, local-only credentials:

- Owner/loader: `ii_owner`, password `ii_owner_local`, via `FIXTURE_DATABASE_URL`.
- Checker: `ii_runner`, password `ii_runner_local`, via `DATABASE_URL`.

The owner creates schema and loads scenarios. `ii_runner` has schema USAGE and
SELECT on operational inputs, plus SELECT/INSERT on reliability results. It cannot
INSERT/UPDATE/DELETE/TRUNCATE operational tables, create tables in either schema,
or UPDATE/DELETE results. Runtime does not need schema-creation privileges.
Reliability child tables reference their run through foreign keys.
An existing cluster-wide `ii_runner` must be unprivileged and have no role
memberships; bootstrap refuses elevated roles and leaves existing passwords alone.
The Compose database gets the documented password when the role is first created.

Operational rows enforce primary-key row identity and required field types only.
They deliberately have no business-reference foreign keys, business-key uniqueness,
or enum checks that would reject raw defect evidence. Duplicate movement identities,
unknown references, duplicate opening/snapshot buckets, and broken manifests can
therefore be inspected by the checker. No source repair occurs in this layer.

### Load and reuse scenarios

```sh
python -m synthetic.generate clean
python -m synthetic.generate combined
# Or use --database-url with an explicit owner connection.
```

Each prints the two batch IDs and aware UTC cutoff/evaluation instants as JSON.
IDs for all catalogs, batches, coverage, opening, movement and snapshot rows are
prefixed `<scenario>:`. Namespaces coexist in the same database. A second load of
any existing namespace raises `ValueError` (CLI exit 2), without overwriting or
deleting inputs. The loader inserts all rows in one transaction and writes no
reliability results. Concurrent loads of the same namespace cannot overwrite data;
a primary-key conflict rolls back the losing load.

```python
import os
import psycopg
from synthetic.generate import load_scenario

with psycopg.connect(os.environ["FIXTURE_DATABASE_URL"], autocommit=True) as conn:
    context = load_scenario(conn, "quantity_mismatch")
# context: ledger_batch_id, snapshot_batch_id, as_of, evaluated_at
# Pass context to the engine separately using an ii_runner connection.
```

The connection must be idle with `autocommit=True`; the loader owns its transaction.
No table creation happens inside `load_scenario`.

| Scenario | Deliberate source change |
| --- | --- |
| `clean` | Complete controls, no corruption |
| `quantity_mismatch` | Jacket/harbor snapshot 26 instead of independently expected 25; delta +1 |
| `duplicate_movement` | Duplicate hoodie receipt natural key, separate raw row ID |
| `unknown_reference` | Extra posted row referring to `unknown-sku` |
| `invalid_transfer` | Tee inbound transfer +3 against outbound -4 |
| `stale_snapshot` | Evaluation is 24 hours and 1 second after snapshot cutoff |
| `missing_snapshot` | Zero-stock tee-L/harbor snapshot absent despite explicit coverage |
| `combined` | Duplicate hoodie receipt, broken tee transfer, jacket quantity mismatch on separate buckets |

All raw movement and snapshot counts match their manifests, including fault
scenarios; missing snapshot coverage is distinct from a raw count mismatch.
There are five declared buckets per batch and five opening balances per scenario.
Each scenario has 13 movements (14 for duplicate, unknown-reference and combined),
and five snapshot rows (four for missing-snapshot).

Independent clean snapshot observations at `2026-01-02T00:00:00+00:00` are:

| SKU / warehouse | Opening | Posted effects in comparison | Independent snapshot |
| --- | ---: | --- | ---: |
| tee-M / harbor | 20 | +10 receipt -3 shipment -4 transfer +1 cutoff return | 24 |
| tee-M / upland | 5 | +4 transfer | 9 |
| hoodie-L / harbor | 12 | +4 receipt -2 shipment +2 posted reversal | 16 |
| tee-L / harbor | 0 | No movement | 0 |
| jacket-M / harbor | 30 | -5 adjustment | 25 |

Baseline is `2026-01-01T00:00:00+00:00`, watermark 10. A baseline-time receipt,
pending receipt, after-cutoff receipt, and higher-sequence late observation remain
raw evidence but do not contribute. The immediate transfer shares one event and
sequence across distinct legs. The two receipt lines share one event/document.
The reversal links to the original shipment; both quantities remain in arithmetic.
Default evaluation is two hours after cutoff. Observation/recording instants are
preserved separately; manifest observation is 90 minutes after cutoff.


## Reliability

### CLI and library

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

### SQL and assessment

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
SKU, warehouse, SKU style, and non-null reversal row references. Freshness uses
the snapshot manifest cutoff; disagreeing row cutoffs/watermarks are metadata
defects and do not establish an additional freshness conclusion. Watermarks
are compared between manifests only when the ledger watermark is available.
Unknown movement references remain local R003 defects, allowing unrelated
covered buckets to retain their quantity comparisons.

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


## Planning

### Fresh-database demonstration

Use a NEW disposable database/Compose project, not a previous test/demo volume.
Existing Stage 1 databases can install the final additive planning schema once
as owner; never reset a populated schema to run a demo. Python and runtime pins
are in the README. No new dependency is needed.

```sh
export COMPOSE_PROJECT_NAME=ii_stage2_demo
export POSTGRES_PORT=55437
docker compose up -d --wait
export FIXTURE_DATABASE_URL=postgresql://ii_owner:ii_owner_local@localhost:55437/inventory_intelligence
export DATABASE_URL=postgresql://ii_runner:ii_runner_local@localhost:55437/inventory_intelligence
python -m synthetic.planning_demo --format json > /tmp/stage2-demo.json
```

The demo inserts source fixtures through the owner, checks inventory through the
restricted runner, then persists five benchmarks and two proposals. It refuses
reloads rather than overwriting inputs. `--format markdown` produces a compact
report instead (choose the format before loading; rerun on a fresh database).
Full evidence lives in `planning.runs.context/result`; the concise report includes
run IDs for retrieval. [Verified summary](examples/stage2.md).

Expected independent outcomes: constant/zero choose naive on ties; weekly and
intermittent choose seasonal naive with zero errors on these deterministic
patterns. Each clean group has 14 shared selection origins for 7/14/28-day scores,
plus the separate final 28-day holdout. The blocked control has no selected model.
The complete supply proposes 12 pieces; the incomplete supply is `not_assessable`
with null order. This proves wiring and arithmetic on synthetic controls, not
model performance in a real business. No advanced model is justified by this toy
benchmark.

### Library entry points

Use an idle Psycopg autocommit connection for every result-producing function.
`run_forecast`, `run_benchmark` and `run_plan` each own one Repeatable Read
transaction, set UTC serialization, read immutable inputs and append a new run.
They never load fixtures or modify inputs. `demand.read_series` is read-only and
runs under its caller's transaction.

```python
from inventory_intelligence.planning_runs import run_forecast, run_benchmark
from inventory_intelligence.replenishment import run_plan

# All dates are datetime.date, and evaluated_at is an aware datetime.
run_forecast(conn, batch_id=batch, sku_id=sku, warehouse_id=warehouse,
             start_day=start, origin_day=origin, method="mean", horizon=7,
             code_version="reviewed-commit")
run_benchmark(conn, batch_id=batch, sku_id=sku, warehouse_id=warehouse,
              group="weekly", start_day=start, end_day=end,
              evaluated_at=evaluation_cutoff, code_version="reviewed-commit")
run_plan(conn, batch_id=batch, sku_id=sku, warehouse_id=warehouse,
         start_day=start, origin_day=origin, method="mean",
         reliability_run_id=inventory_run, supply_batch_id=supply,
         code_version="reviewed-commit")
```

Demand zero requires complete daily coverage AND available stock evidence, with
matching order-line count. Both source recording and observation time gate each
revision. Cancellations preserve gross accepted quantity; corrections revise it
only from the time they become known. No shipments are used as demand. Origin
training excludes the current business day and never compresses unavailable days.

Reservations are remaining, unshipped commitments from before the origin. Forecasts
cover new acceptances, assumed to require stock on acceptance day. Confirmed inbound
arrives at day start; forecast and reservations consume at day end. The new order
arrives after L FULL calendar days; lead 1 starts at the origin, so order arrival
is zero-based index L. Need covers the maximum safety deficit from L through H-1,
where H=L+review. Earlier shortages are explicitly reported and remain unsolved by
that order. Policy bounds H to 366; no estimated lead time or calibrated safety
stock is invented. Pack/MOQ rounding never forces an order when raw need is zero.

A historical passing inventory run is insufficient: cutoff/evaluation must match
origin, records must be known then, the key must be covered, and current Stage 1
SQL revalidation must still pass. V1 source owners retain their preservation duty;
the planner also stores the evidence actually read. Missing/incomplete inputs
append `not_assessable` with no proposal. Invalid API arguments and database errors
raise and roll back, rather than becoming missing-data results.
