# Current interfaces and constraints

This is the canonical interface reference for accepted implementations. Consolidation
changes documentation paths, not contract identifiers, behavior or old decoding.
Historical experiment grids and source bytes are recoverable from Git via
[EVIDENCE](EVIDENCE.md); measured outcomes are in [RESULTS](RESULTS.md).
Shared versioned interfaces require an explicit amendment, never an implicit change.


- [Inventory v1](#inventory-v1)
- [Planning v1](#planning-v1)
- [Copilot v1](#copilot-v1)
- [Copilot v2](#copilot-v2)
- [Decision simulation v1](#decision-simulation-v1)
- [Intermittent methods v1](#intermittent-methods-v1)
- [Lost sales v1](#lost-sales-v1)
- [Physical count v1](#physical-count-v1)
- [Observed sales adapter](#observed-sales-adapter)

## Inventory v1

### Scope and invariants

- Python 3.12, PostgreSQL 17, Docker Compose, Psycopg 3; standard-library CLI/JSON/unittest. Pin reviewed dependency versions and image versions/digests during implementation.
- One fictional business, finished garments in integer pieces, `(sku_id, warehouse_id)` balance grain. Styles group color/size SKUs; they do not hold inventory.
- Synthetic data only. Checker reads operational inputs and writes reliability results only. No upload/form layer, ERP, ORM, scheduler, dashboard, forecasting, or LLM.
- Ledger and snapshot are independent observations. Missing data is never zero. Ambiguous input blocks quantity conclusions for affected buckets.
- Source batches/rows used by existing runs must remain available. Repeated checking creates a new run without rewriting previous findings.

### Database interface

Table/column names below are fixed. IDs/codes/statuses/references are `text`, quantities and source sequences are `bigint`, instants are `timestamptz`, counts are `integer`. `?` marks nullable columns; others are required. Fixture row IDs are primary keys. No business-reference foreign keys or business-key uniqueness constraints on movement/opening/snapshot rows: they must admit the seeded bad records.

```text
operational_fixture.styles
  style_id, style_code, name
operational_fixture.skus
  sku_id, style_id, sku_code, color, size, base_uom
operational_fixture.warehouses
  warehouse_id, warehouse_code, name
operational_fixture.batches
  batch_id, kind, status, baseline_at?, as_of, watermark?, observed_at,
  expected_row_count
operational_fixture.coverage
  row_id, batch_id, sku_id, warehouse_id
operational_fixture.opening_balances
  row_id, batch_id, sku_id, warehouse_id, quantity, as_of, baseline_ref
operational_fixture.movements
  row_id, batch_id, source_system, event_id, document_id, document_line_id,
  leg_id, sku_id, warehouse_id, quantity, movement_type, posting_status,
  effective_at, source_recorded_at, source_seq, observed_at,
  transfer_id?, reversal_of_row_id?, reason?
operational_fixture.snapshots
  row_id, batch_id, sku_id, warehouse_id, on_hand_qty, as_of, watermark?,
  observed_at
```

`base_uom=each`. Batch `kind=ledger|snapshot`, `status=complete|incomplete`; ledger baseline is required, snapshot baseline is null. Ledger expected row count counts all raw movement rows in that batch; snapshot count counts all raw snapshot rows. Opening balances/coverage are checked separately. Coverage explicitly lists expected SKU/warehouse keys, including zero stock; no sparse-zero convention in v1.

Movement `posting_status=posted|pending`; types are `receipt|shipment|return|adjustment|transfer|reversal`. Posted signed quantities supply the arithmetic. Posted reversal legs negate their original effects; never also remove the original from the sum. Multi-line documents and distinct transfer legs are legitimate, not duplicates.

Natural movement-leg key: `(source_system, event_id, document_line_id, leg_id)`, scoped to the selected ledger batch. `source_seq` is the upstream event sequence, not a local row ID or event-time timestamp; an immediate transfer's two legs share that sequence. Preserve recording/observation times separately from effective time.

The schema also includes these storage tables, using report field types below:

```text
reliability.runs
  run_id uuid PK, contract_version, code_version, ledger_batch_id,
  snapshot_batch_id, as_of, evaluated_at, overall_status
reliability.check_results
  run_id uuid, rule_id, status; PK(run_id, rule_id)
reliability.findings
  run_id uuid, finding_id, rule_id, severity, reason, sku_id?, warehouse_id?,
  source_row_ids jsonb, expected_qty?, observed_qty?, delta_qty?, evidence jsonb;
  PK(run_id, finding_id)
```

Use foreign keys from reliability child tables to runs. Bootstrap creates a local `ii_runner` role with SELECT/USAGE on operational tables/schema and SELECT/INSERT/USAGE on reliability tables/schema, without operational write privileges. Password/configuration is synthetic local configuration, documented in OPERATIONS; never use real credentials. Runtime must not require schema creation privileges.

### Cutoff and checks

Both selected batch manifests must be complete, cover the same declared keys, and agree with requested cutoff `T` and watermark `W`. Each snapshot row must agree with its manifest. Opening balances match ledger baseline `t0`. Freshness uses `evaluated_at - snapshot.as_of`; v1 default is 24 hours, and exactly 24 hours is fresh. A future snapshot cutoff is invalid metadata.

Eligible movements belong to the selected ledger batch, are posted, and satisfy `t0 < effective_at <= T` and `source_seq <= W`. Higher-sequence late arrivals, pending movements, and movements after `T` do not affect this comparison. Check identity/transfers for eligible movements. Read/check/persist in one Repeatable Read transaction; retain the selected batch IDs and cutoff in the run.

```text
expected_qty = opening.quantity + sum(eligible signed quantities)
delta_qty = snapshot.on_hand_qty - expected_qty
```

Fixed rule IDs and reasons:

- `R001` quantity: `quantity_mismatch`, one finding per assessable mismatched bucket, with exact expected/observed/delta quantities.
- `R002` identity: `duplicate_movement_key`, one finding per duplicate natural-key group with all offending row IDs. Conflicting and identical duplicates both block their affected buckets; do not silently deduplicate.
- `R003` references/baseline: `unknown_reference` per offending movement/opening/snapshot row (evidence names unknown fields); `missing_opening_balance`, `duplicate_opening_balance`, or `opening_cutoff_mismatch` per affected covered bucket.
- `R004` transfers: `invalid_transfer` per eligible transfer ID. Require two posted transfer legs, same SKU/effective time/source sequence, different warehouses, and equal-and-opposite nonzero quantities. Evidence names broken conditions. Incomplete ledger extraction cannot prove a missing transfer leg; mark this check not assessable when the ledger batch is incomplete/missing.
- `R005` coverage/freshness: `missing_batch`, `incomplete_batch`, `count_mismatch`, `metadata_mismatch`, `stale_snapshot`, `coverage_mismatch` per affected batch; `missing_snapshot` or `duplicate_snapshot` per covered bucket. Check both manifests and unexpected snapshot keys, not just snapshot rows that happen to exist.

All v1 findings have `severity=error`. Quantity fields are null outside R001. Global manifest/cutoff/freshness failures block R001 for all buckets; local source/reference/opening/transfer/snapshot defects block affected buckets. Continue checks that can still establish defects from available evidence. Never emit a manufactured quantity delta for blocked buckets.

Exactly five check-result entries appear per successful execution. A rule is `fail` if it emitted findings, otherwise `not_assessable` if required comparisons were blocked, otherwise `pass`. R001 with some comparable and some blocked buckets is not fully passed. Overall: `fail` if any rule fails, else `not_assessable` if any rule is not assessable, else `pass`. Execution errors roll back that transaction and are separately reported; they must not become passes.

### Python and CLI interfaces

All connection arguments are idle Psycopg connections opened with `autocommit=True`; each function owns its transaction. Datetime arguments/context values are aware UTC `datetime` objects.

```python
# Fixture loader: no dependency on the checker
synthetic.generate.load_scenario(conn, scenario_name: str) -> dict
# returns ledger_batch_id, snapshot_batch_id, as_of, evaluated_at

# Checker and separate persistence
inventory_intelligence.reliability.run_checks(
    conn, *, ledger_batch_id: str, snapshot_batch_id: str,
    as_of, evaluated_at, code_version: str = "dev",
    max_snapshot_age_hours: int = 24,
) -> dict
```

Fixture loading inserts deterministic, scenario-namespaced batches/rows in one transaction; refuse to overwrite an existing scenario. Tests load once and can check repeatedly. Source schemas are created beforehand with `sql/schema.sql`; the checker never initializes or reloads them.

Report dict fields: `run_id` (UUID string), `contract_version` (`"1"`), `code_version`, `ledger_batch_id`, `snapshot_batch_id`, `as_of`, `evaluated_at`, `overall_status`, `checks` (list of `{rule_id,status}`), and `findings` (list of storage fields above except `run_id`). Serialize timestamps as UTC ISO 8601. `finding_id` is a deterministic string; source row ID arrays are sorted, check entries sort by rule ID, findings sort by rule/reason/bucket/source IDs. Run IDs are the only required volatile report field.

CLI: `python -m inventory_intelligence --ledger-batch ID --snapshot-batch ID --as-of ISO --evaluated-at ISO --format json|markdown`, using `DATABASE_URL` for an `ii_runner` connection. Optional `--max-snapshot-age-hours` and `--code-version` match the library. Exit 0 pass, 1 fail/not-assessable, 2 execution/configuration error. Output goes to stdout; diagnostic errors to stderr. No automatic source repair or fixture loading in this command.


## Planning v1

### Demand and eligibility

Grain is existing `(sku_id, warehouse_id)` in whole `each` pieces. Calendar is
`America/Los_Angeles`; intervals are `[start_day, end_day)`. Origins are local
midnight instants converted to UTC; a day must have ended at the origin. Local
days can be 23/25 hours. Never group by UTC date or add 24 hours to local midnight.

Target is **gross recorded accepted customer order quantity**, allocated to its
original acceptance day and requested fulfillment warehouse. Shipments, transfers,
returns and adjustments are not demand. A cancellation is retained as a version
but does not erase previously accepted demand. Quantity corrections replace the
accepted quantity only as known; this is not outstanding order backlog or lost
sales. Accepted time/SKU/warehouse cannot change within an order-line identity.

Order identity is `(source_system, order_id, line_id)`; version is a positive
integer `revision`. Each row keeps its ingestion `row_id`, `accepted_at`,
`source_recorded_at`, `observed_at`, `accepted_qty` and `status=accepted|cancelled`.
For knowledge cutoff K, use the greatest revision with BOTH recording and
observation times <= K. Future-recorded or future-observed versions are invisible.
Duplicate identities at the same visible revision, identity changes, invalid
units/quantities/status/times block the series; never silently deduplicate.

Daily evidence has its own row ID, revision, business day, source recording and
observation times, `coverage=complete|incomplete`,
`availability=available|stockout|unknown`, and expected active order-line count.
Use the latest visible daily revision. Exactly one complete available record
with matching line count is required. No lines on such a day means **zero**.
Missing, incomplete, stockout-constrained, unknown, conflicting or count-mismatched
days have null demand and explicit reasons. No imputation/compression of gaps.
Even positive recorded orders on a constrained day remain in evidence but are
ineligible for the bounded uncensored baseline. The target does not measure
unrecorded demand; lost-sales estimation is deferred.

A demand batch is an immutable **replay archive**, with version, calendar range,
timezone, assembly time, status and exact raw order/day counts. Assembly time is
provenance, not the historical knowledge time of every record. Archive counts
are validated at evaluation; per-record knowledge gates drive historical replay.
Results retain selected records and batch metadata. Owner loaders refuse reloads.
Runtime has SELECT only on inputs; owners must keep archives used by runs intact.

### Forecasting and evaluation

Only wholly eligible contiguous daily training series feed the existing exact
`naive`, `mean`, `seasonal_naive` kernel. Version `baselines-v1`, 7-day season,
minimum training 28 days. Record cutoff, training range, batch/version,
timezone, method/version, horizon, code version and eligibility evidence.
Invalid API arguments are errors; unavailable source evidence is `not_assessable`
with null predictions/scores, never a fabricated zero forecast.

Benchmark horizons 7/14/28 use identical candidate origins (weekly spacing) and
require the maximum horizon to fit before selection end. Reconstruct each origin's
training using that origin's knowledge time. Selection truth uses the earlier of the explicit evaluation cutoff and holdout
start; revisions learned during/after holdout cannot influence model selection.
Holdout truth uses the explicit evaluation cutoff and must itself be eligible. Retain reasons for excluded folds.
Use only origins eligible for ALL horizons/models. Score every origin/lead pair;
MAE = sum absolute error / points, bias = sum(forecast-actual) / points,
WAPE = sum absolute error / sum(actual), null for zero actual volume.

Reserve the final 28 days as temporal holdout. Selection folds end on/before its
start. Select by lowest 28-day MAE, ties in kernel method order. Freeze that choice
before a single holdout origin; reconstruct its training as known then. Holdout
truth never selects the method. Report each SKU/warehouse/group separately.
No eligible selection folds means no chosen model, even if holdout is assessable.

`planning.runs`: append-only UUID, contract/code/model versions, kind,
created_at, input digest, status, context JSONB and result JSONB. Fractional values
serialize as exact rational strings, never floats. Repeated unchanged inputs
give stable semantic results excluding run identity/creation time; no upserts.
Read, compute and persist in one Repeatable Read transaction. Errors roll back.

### Inventory projection and replenishment

Use an explicit persisted Stage 1 run, contract 1, all FIVE stored checks passing,
no findings, overall pass, selected key covered and a single matching snapshot.
Run evaluated_at must equal T, and all selected inventory evidence must be observed by planning origin T;
the run cannot have been evaluated in the future. Require snapshot/run as_of = T,
with freshness recomputed at T, never the old evaluation time. A mismatched,
historical or failing run yields `not_assessable`. No per-bucket rescue from a
globally nonpassing run. Reuse Stage 1's read-only SQL at T to revalidate current
source evidence, so a source change after a saved pass cannot silently authorize
stock. Retain that current validation separately; never rewrite the saved run. Reject negative stock. Keep the run and batch identities.

A separate immutable supply batch for a single key/cutoff declares explicit
reservation AND inbound completeness, exact raw row counts, observation time and
effective cutoff T. Reservations are **remaining unshipped commitments at T**;
include only open entries due within the protection horizon, not posted shipments
again. Inbound includes remaining confirmed quantities with arrival dates in the
future horizon; pending/cancelled or out-of-horizon rows stay in evidence and
contribute zero. Duplicate natural IDs, negative quantities, invalid statuses,
overdue open reservations/confirmed receipts, future observations, missing policy
or incomplete manifests block recommendations. No implicit empty input is complete.

One explicit policy (H <= 366 days): positive integer lead days L, review days R, pack size P and
MOQ M; nonnegative integer safety pieces S. Protection horizon H=L+R. Daily demand
is the selected caller-declared baseline's H-day forecast (no automatic model
promotion). Reservations and forecast refer to disjoint targets: forecasts cover
**new acceptances after T**; reservations cover previously accepted unshipped
commitments. New acceptances are assumed to require stock on their acceptance day; customer
fulfillment-lag modeling is deferred. These assumptions are explicit; quantities
cannot be counted twice.
Confirmed inbound arrives at the START of the named local day; reservation and
forecast demand deplete at its END. Proposed stock arrives at local midnight T + L calendar days
(after L full days; the first forecast day starts at T). All dates are future business dates starting T's
local date. Supplier delays require a new supply batch, never mutate prior results.

Let B_d = on_hand + cumulative confirmed inbound - cumulative open reservations
- cumulative forecast through day d. Projection lists each exact B_d, and flags
negative balances before the new order could arrive; it does not imply the order
repairs earlier shortages. Target: keep B_d + order >= S for every zero-based day index d >= L.
Unrounded need = max(0, max(S-B_d for d=L..H-1)). Whole-piece need is its ceiling.
If need=0, order=0 (MOQ does not force buying). Otherwise order is
P * ceil(max(ceil(need), M) / P). This prefix rule prevents late inbound from
masking an earlier post-arrival shortage. Report end inventory position, daily
projection, raw need, integer ceiling, pack/MOQ effects, arrival day and shortages.
Safety pieces are a declared policy, not a calibrated service-level guarantee.

Required input gaps return `not_assessable`, null recommendation and reasons.
Execution/configuration errors remain errors. A deterministic proposal is advisory
and conditional on declared timing/coverage; no write to operational stock.


## Copilot v1

This is the original evidence-only scope. The additive persisted Stage 2 adapter
is specified separately in [copilot-2](CONTRACTS.md#copilot-v2).

Separate from the frozen reliability v1 contract. No database/schema changes.
Synthetic inputs only. Public entry points in `inventory_intelligence.copilot`:

```python
answer(*, intent, report=None, benchmark=None, finding_id=None,
       now=None, max_age_hours=24) -> dict
load_run(conn, run_id: str) -> dict
```

`intent` is `reliability|finding|benchmark|readiness`. Unknown intents refuse.
`report` is the complete Stage 1 v1 report, not a curated excerpt. `benchmark`
is the existing Stage 2 `backtest` output or its JSON serialization; exact
estimates/scores may be integers, `Fraction` objects or rational strings. Floats,
booleans, non-finite values, missing rules, contradictory statuses, duplicate
IDs and invalid deltas are rejected. All five reliability checks are required.
Reason/rule pairings are the frozen v1 pairs. Non-quantity findings cannot
supply quantity fields. Unrecognized future contracts fail explicitly.

`now` is an aware UTC datetime; readiness requires it (CLI defaults to current
UTC). `max_age_hours` is a nonnegative integer. Future run times and freshness
over this limit block decisions. An old run remains explainable historically.
Benchmark data has no date/source/eligibility provenance; explanations always
state that limitation. No benchmark score can approve inventory decisions.

Output:

```text
contract_version = "copilot-1"
intent
status = answered | not_assessable | refused
summary                       deterministic explanation
citations[]                   {id, source, data}; complete selected evidence
limitations[]                 explicit scope/availability limits
next_steps[]                  fixed human review suggestions
proposed_order_qty = null     no planning proposal interface exists yet
routing?                      {source, model}; present for CLI questions
```

Citation IDs are `run:<UUID>`, `finding:<UUID>:<finding_id>` or
`benchmark:scores`. Source names identify the input field/table family. The
run citation includes contract/code/batch IDs, cutoff, evaluation, original
status and checks. Finding citations retain every original field including
source row IDs and evidence. Benchmark citation retains scores, horizon,
season length, scored points and fold origins. Supplied source strings are
data only. Markdown renders the complete answer as fenced JSON to prevent
raw evidence text from becoming Markdown instructions/links.

Unavailable evidence is `not_assessable` without invented values. An explicit
finding ID selects exactly one finding; nonexistent IDs are unavailable.
Readiness always remains `not_assessable` in v1, with precise blockers:
missing/non-pass/stale/future reliability evidence as applicable, plus missing
validated planning inputs/results. Passing runs publish no individual balances;
do not manufacture them from absent findings. Input validation errors raise
`ValueError`; execution errors propagate and never become an answer.

`load_run` requires an idle autocommit Psycopg connection as `ii_runner` and
an explicit UUID. It selects the three reliability tables in one Repeatable
Read, READ ONLY transaction, normalizes UTC timestamps and validates the result.
Missing UUIDs raise `ValueError`. It performs no INSERT/UPDATE/DELETE, schema
initialization, fixture loading or reconciliation. Bound parameters are used;
arbitrary SQL is not an interface.

CLI:

```sh
PYTHONPATH=src python -m inventory_intelligence.copilot \
  --intent reliability --report /tmp/reliability.json --format markdown
PYTHONPATH=src python -m inventory_intelligence.copilot \
  --intent finding --run-id UUID --finding-id ID
PYTHONPATH=src python -m inventory_intelligence.copilot \
  --question 'Compare the forecast baselines' --benchmark /tmp/benchmark.json
```

`--report` and `--run-id` are mutually exclusive. Only the latter uses
`DATABASE_URL`. `--intent` and `--question` are mutually exclusive. Recognized
question phrases are listed by `--help` and resolve locally. Other questions
use one bounded OpenAI Responses request to classify an intent, with
`--language-model gpt-6-luna` by default. `gpt-6-sol` requires an explicit flag;
there is no automatic escalation. `--language-model offline` disables all API
calls and refuses phrases outside the allowlist. The model receives only the
question and fixed classification instructions, never source evidence, database
credentials or a tool. Its strict output has one allowlisted `intent`, no prose,
quantities, IDs or SQL. Finding selection still requires `--finding-id`.

The CLI reads `OPENAI_API_KEY` from the environment, then `--env-file` (default
`.env`); the existing lowercase `openai_api_key` spelling is supported. The file
is parsed as data, never sourced/executed, and is not rewritten. Question length
is at most 2000 characters. Responses are limited to 128 KiB; Luna output to 128
tokens (Sol to 512); timeout is 15 seconds. No retries, tools or stored response.
Redirects are rejected so an API credential cannot be forwarded to another host.
Missing key, HTTP/service error, malformed output or timeout uses an explicit
offline fallback with a safe limitation, yielding refusal for an unknown phrase.
Model routing can be imperfect; the answer exposes the selected intent and
routing source. The deterministic core retains control of every quantity,
citation and readiness policy. Unsupported routes retrieve no source data.

File size is limited to 2 MiB; database reports to 1000 findings and the same serialized
size. Over-limit data errors instead of yielding partial citations. Strict JSON
rejects duplicate object keys and nonstandard NaN/Infinity.

Exit 0: answered (including explanation of a failed run); 1: unavailable or
refused; 2: invalid input/configuration/execution. Answers go to stdout, safe
diagnostics to stderr. No source repairs or order placement.


## Copilot v2

This additive Stage 3 interface explains an explicit persisted `planning-v1` run.
The existing [copilot-1](CONTRACTS.md#copilot-v1) reliability, finding, baseline and
readiness interfaces retain their scope. No Stage 1 table or report changes.

```python
from inventory_intelligence.copilot_planning import load_planning_run, answer_planning
load_planning_run(conn, run_id: str) -> dict
answer_planning(report: dict) -> dict
```

Loading requires an idle autocommit `ii_runner` connection and an explicit UUID.
It reads one `planning.runs` record in Repeatable Read, READ ONLY, using bound
parameters. It performs no source queries, reconciliation, forecasting, INSERT,
UPDATE or DELETE. Missing, malformed, inconsistent or oversized evidence errors;
results are never silently truncated. Complete replay benchmarks can exceed the
legacy 2 MiB report limit, so this separate loader permits at most 16 MiB.

Only `planning-v1`, `baselines-v1`, and forecast/backtest/replenishment kinds are
recognized. Validate exact values, envelope/result statuses, baseline scores on
shared folds, model selection, and selection truth knowledge before holdout.
Proposal validation checks its supplied projection/rounding arithmetic using the
existing exact planner; this is consistency validation, not a new stock decision.
No float quantities or fabricated zeros. Unsupported future contracts error.

Output retains the copilot shape with `contract_version="copilot-2"`,
`intent="planning"`, `status="answered"`, and `proposed_order_qty=null`.
A citation `planning:<UUID>` names `planning.runs` and keeps run/version/digest,
context, source identities and result fields. Forecast/proposal citations retain
the complete record; backtest citations select exact selection/holdout scores,
chosen method and all candidate origin/status fields, explicitly excluding raw
replay rows from presentation after validating the complete record.

A blocked historical plan is successfully explainable: its original status,
reasons and null quantity remain in the citation. An assessable historical
proposal retains its original quantity **inside the citation only**. Neither
answer approves a current order. Source freshness/completeness must be established
again at a new planning cutoff before action. No source evidence enters an LLM.
The new intent is explicit; natural-language routing is unchanged.

```sh
PYTHONPATH=src python -m inventory_intelligence.copilot \
  --intent planning --planning-run-id UUID --language-model offline
```

`--planning-run-id`, `--run-id` and `--report` are mutually exclusive. Planning
requires `--intent planning` plus `--planning-run-id` and `DATABASE_URL`.
Exit 0 means the explanation succeeded, even for a stored blocked plan; exit 2
means invalid input/retrieval/evidence. The ordinary readiness intent still
blocks without current validated planning inputs. Source strings remain data;
Markdown uses the existing fenced JSON renderer.


## Decision simulation v1

### Inputs and public interface

`inventory_intelligence.decision.simulate(history, demand, *, method, on_hand,
lead_days, review_days, safety_qty=0, pack_size=1, moq=1, review_phase=0,
commitments=(), inbound=(), supplier_delays=(), holding_cost=1,
backlog_cost=10, order_cost=0)` returns a dict with `contract_version`, `days`,
`reviews`, `metrics`, `terminal`, and `assumptions`. Baselines are the unchanged
`forecasting.METHODS`; additionally `zero` is an explicit research diagnostic.
History is nonempty and covers seven days for seasonal naive. History and demand
are contiguous eligible nonnegative integers; gaps, floats, booleans and negative
pieces are errors, never zero. Forecasts use exactly history plus completed
simulation days before each origin. Demand is nonempty.

L/R/pack/MOQ are positive integers, safety/stock nonnegative integers,
`0 <= review_phase < review_days`. H=L+R must be <=366. Each commitment is
`{id, due_day, quantity}`, with unique nonempty id and a zero-based due day
inside the scored demand window. These are disjoint prior accepted commitments,
not new simulated demand. Each initial inbound is `{id, arrival_day, quantity}`,
unique nonempty id and nonnegative arrival day inside the scored window; it is
confirmed and known initially. Explicit empty tuples mean complete empty inputs.
Reject malformed rows. All quantities are positive whole pieces in these rows.
The complete hidden supplier trace has one nonnegative delay per possible review
day across scoring and runoff; empty means all zero. Index by absolute review
slot (including zero orders), not candidate order count. Positive orders placed
on t arrive at start of t+L+delay[t//R]. Policy sees all outstanding quantities,
never future delay values. Rational cost rates are nonnegative int/Fraction;
float/string/bool rates are rejected. Acquisition and lost-sales costs are omitted.

### Events and policy

All new accepted units are due on acceptance day, an explicit counterfactual.
Days are source-local calendar-day indices, independent of DST hour lengths.
For each day:

1. Receive scheduled inbound and previously placed orders.
2. Add today's prior commitments and fulfill due backlog from on-hand. Priority
   is ascending due/acceptance day, prior commitments before new demand on ties,
   then identity. Future commitments are not fulfilled early.
3. On t=phase+kR, forecast H days with only completed observations, then order.
4. Observe new daily demand at day end, fulfill immediately from remaining stock,
   and retain unmet units in backlog. Later fulfillment never repairs immediate
   fill or on-time commitment rates.
5. Charge h*ending_on_hand + b*ending_backlog + K*(positive order placed).

The named policy is **periodic inventory-position order-up-to**, deliberately
separate from planning-v1's prefix projection. At review, target = sum of H-day
forecast + safety + remaining *future* prior commitments due before t+H.
Inventory position = current on_hand + ALL outstanding order/inbound quantities
- current due backlog. Order need = max(0, target-position), whole need=ceil(need).
Positive order = pack*ceil(max(whole_need, MOQ)/pack); zero need places no order.
Outstanding quantities remain in position even if delayed, preventing duplicate
ordering. This policy can still suffer early shortages; it does not promise
prefix protection or calibrated service. No call to or change of `project`.

### Scoring and fixed runoff

Score days [0,N); initial stock, prior commitments, supplier trace, phase and
cost regime are paired identically for every candidate. There is no warmup after
the supplied history. Complete cycles are [phase+kR,phase+(k+1)R) wholly inside
[0,N); days before phase and incomplete final cycles do not enter cycle service.
All days inside [0,N) still enter unit/service/exposure metrics.

Append exactly L+max(declared supplier delays, default 0)+R runoff days, for ALL
candidates. No new demand in runoff. Continue reviews but order only to clear
due backlog: need=max(0,backlog-on_hand-outstanding), same packs/MOQ. Do not
forecast new demand or replenish safety in runoff. Charge holding, backlog and
setup costs through the fixed runoff. This settles scored obligations and late
orders without allowing them to disappear at N. Return separate scored, runoff
and total costs, final on-hand/backlog/outstanding orders. Any residual backlog or
pipeline is an error (invalid runoff completion), never a successful cheap run.
Residual stock has no salvage/acquisition valuation; reported finite-window
penalties are synthetic, not profit or business savings. No claim of infinite
horizon optimality.

Service/exposure metrics cover scoring days only:

- `new_demand_units`, `immediately_filled_units`, nullable `immediate_fill_rate`;
  `eventually_filled_units` / nullable `eventual_fill_rate` includes runoff
  completion of scored new demand and is reported separately.
- `prior_commitment_units`, `on_time_prior_units`, nullable
  `on_time_prior_fill_rate`; due-day shortages cannot be repaired retroactively.
- `complete_cycles`, `shortage_free_cycles`, nullable `cycle_service`.
  A shortage day has unmet new units OR an unfilled due commitment/backlog at
  day end; an empty shelf with no unmet units is not a shortage.
- `shortage_days`, `newly_unmet_units` (new demand plus newly due prior units
  still unfilled on their first due day), `backlog_piece_days`,
  `on_hand_piece_days`, `average_on_hand`, `end_on_hand`, `end_backlog`,
  `order_count`, plus `runoff_order_count` and explicit terminal pipeline.
- Forecast scores use only scored reviews whose entire H-day target ends by N.
  Report `forecast_origins`, `forecast_points`, actual-volume denominator,
  nullable daily MAE/bias/WAPE, nullable mean absolute cumulative H error and
  mean cumulative bias (forecast-actual). No complete targets means null scores.
  WAPE is null for zero actual volume. Retain origin forecasts for audit.

Every day records stock, backlog, new/prior demand, immediate new fulfillment,
newly unmet units, receipts, order quantity, outstanding quantities, shortage,
scored/runoff flag and each rational cost component. Physical stock and backlog
must remain nonnegative integers. Units conserve: initial stock + all receipts
= all fulfillment + final stock; accepted commitments/new demand = fulfilled
+ final backlog. Cost rational arithmetic is exact.


## Intermittent methods v1

### Algorithms and interfaces

`intermittent.forecast(history, *, method, horizon, alpha=Fraction(1,5),
beta=Fraction(1,5))` returns exact Fraction daily expectations for baseline
methods, zero, Croston, SBA and TSB. Reuse the baseline kernel; do not extend
its METHODS. Positive integer horizon; contiguous nonnegative whole-piece
observations; rational alpha/beta in (0,1], rejecting bool/float/string.
Initialize at the first positive observation i: size=q_i, interval=i+1,
occurrence probability=1/(i+1). All-zero history returns zero. These initial
conditions are declared project choices, not a uniquely mandated estimator.

At subsequent positive arrivals, size = alpha*q+(1-alpha)*size. Croston/SBA
update interval similarly using days since the last positive arrival; they do
not change on zero days. Croston forecast=size/interval; SBA multiplies this by
(1-alpha/2). TSB updates probability every subsequent day with
beta*indicator+(1-beta)*probability and forecasts=size*probability. The point
estimate repeats across the horizon. Exact smoothing arithmetic is a specified
algorithm; it does not imply the estimate is truth or a probability guarantee.
[SBA stock-control paper](https://doi.org/10.1016/j.ijpe.2005.04.004),
[TSB paper](https://doi.org/10.1016/j.ejor.2011.05.018).

`intermittent.calibrate(history, *, method, horizon, quantile, alpha=..., beta=...,
min_train=28, min_samples=8)` uses completed non-overlapping H-day targets with
origins 28,28+H,... and origin+H<=len(history). For each, forecast only the prefix
before the origin. Error=actual cumulative demand minus cumulative forecast.
Nearest-rank quantile is sorted_errors[ceil(q*n)-1], q rational in (0,1]. Return
origins, exact errors, count, quantile_error and safety_qty=max(0,ceil(error_q)).
Fewer than eight complete samples is an error, never zero safety. No summing
daily quantiles. Memoization of immutable prefix/model inputs may reuse valid
fits/calibration evidence inside the bounded experiment.

`intermittent.simulate(history,demand,*,method,alpha=...,beta=...,
safety_quantile=None,**decision_inputs)` reuses the decision event/cost kernel.
None uses caller-declared fixed safety; a quantile dynamically calibrates at
each scored review from completed observations only and requires safety_qty=0.
The decision module can expose a private shared `_simulate` accepting a private
review forecast/safety provider; public decision.simulate keeps its original
signature, method whitelist and identical semantic outputs. No duplicate event
loop. The research wrapper validates provider outputs and appends research
version/parameters and per-review calibration evidence. Runoff never forecasts
or recalibrates, and retains the same obligation-clearance rule.

Research metrics retain all decision-v1 outcomes plus protection_target_origins,
protection_target_covered and nullable protection_target_coverage, scored only
for complete H-day new-demand targets. For empirical policies add nullable
mean pinball loss against the integer policy target ceil(sum(forecast)+safety),
before pack/MOQ; the existing rational decision target remains unchanged;
loss=max(q*(actual-target),(q-1)*(actual-target)). This evaluates the rounded
rounded policy target, not an unrounded distribution claim. Report target
coverage separately from achieved inventory service. Supplier delay uncertainty
stays paired/hidden; H remains nominal L+R and is not claimed delay-adjusted.


## Lost sales v1

### Meaning and observation boundary

A new demand value is an attempted purchase due today. In lost sales, stock not
available that day permanently loses the remaining attempted units. Later
receipts cannot repair the immediate or eventual fill of those units. There is
no backlog. Prior accepted commitments are unsupported and must be rejected;
turning an accepted obligation into a lost sale would change its contract.

The matched study deliberately assumes completed **attempted demand** is captured
in synthetic feedback, including unfilled attempts. Both kernels use identical
history plus attempts strictly before each review origin. This isolates demand
fulfillment semantics and preserves identical forecasts. It is not a model of
ordinary censored sales feedback; real lost demand is usually unavailable from
sales alone. Censored feedback needs a separately frozen experiment, not an
unannounced method change. No public observed-sales data enters this study.

### Inputs and lost-sales interface

`inventory_intelligence.lost_sales.simulate(history, demand, *, method, on_hand,
lead_days, review_days, safety_qty=0, pack_size=1, moq=1, review_phase=0,
commitments=(), inbound=(), supplier_delays=(), holding_cost=1,
lost_cost=10, order_cost=0)` returns version, days, reviews, metrics, terminal
and assumptions. Use unchanged baseline forecast arithmetic plus zero diagnostic.
Nonempty contiguous history/attempts are nonnegative whole integers; missing,
negative, float and boolean quantities are errors. Seasonal history needs seven
days. Stock/safety are nonnegative, lead/review/pack/MOQ positive, phase in [0,R),
horizon H=L+R <=366. Nonempty commitments are rejected.

Initial inbound has unique `{id,arrival_day,quantity}` rows with positive pieces
and day inside [0,N), known initially. All outstanding quantities contribute to
position even when their receipt is later than a protection target. The complete
hidden delay trace has one nonnegative value per possible review across scored
and runoff dates; empty means no delay. Index by absolute calendar review slot,
including slots with no order. Cost rates accept nonnegative int/Fraction only.
The kernel excludes acquisition; the study separately pays every owned piece.

### Daily timing and conservation

1. Receive due initial inbound and previously placed orders at day start.
2. On t=phase+kR before today's attempts, forecast H from completed attempts only.
   Target = sum(forecast)+safety. Position = on_hand+all outstanding quantities.
   Need=max(0,target-position); positive order=pack*ceil(max(ceil(need),MOQ)/pack).
   Order arrives at t+L+hidden_delay[t//R]; policy cannot see hidden realized delays.
3. Observe today's attempts; fill min(on_hand,attempts), permanently lose the rest,
   then append today's attempts to completed history. No same-day receipt from
   a new order (lead >=1), no later fulfillment of lost units.
4. Charge h*ending stock + p*new lost units + K*positive order.

Append exactly L+max(declared delay)+R runoff days. No new attempts, forecasts,
safety replenishment or orders during runoff; receive the outstanding pipeline
and charge holding. Fail on residual pipeline. End backlog is explicitly zero.
Conserve initial stock+receipts=served+ending stock; attempts=served+lost. Keep
whole-piece daily state, lost events, receipts, orders and exact cost components.
Zero-demand fill is undefined; empty shelves without attempted misses are not
shortages. Complete-cycle service counts cycles with no newly lost units.


## Physical count v1

### What the comparison can establish

Ledger/snapshot consistency is not physical warehouse truth. Compare a declared
assessable synthetic system-stock observation with separately identified physical
counts at one `(sku_id,warehouse_id)`/business cutoff. This layer validates the
provided evidence and a strict corroboration policy; it does not independently
run Stage1 SQL, authenticate source signers, prove observer independence or verify
that the actual warehouse was frozen. Those assertions remain source attestations.

Whole pieces only (`uom=each`). Missing, incomplete, ambiguous, future or conflicting
evidence must not become zero, a match or an approved adjustment. A first count,
even when it equals the book quantity, is unconfirmed. At least two distinct
source-declared blind observers and agreement of **all** valid count quantities
are required; same-observer recounts do not establish independent corroboration.
A third conflicting count cannot be hidden by majority voting or last-row wins.

### Inputs and clocks

`inventory_intelligence.physical_count.evaluate(system,manifest,counts,
*,evaluated_at,adjustment_reviews=())` consumes JSON-shaped observations and
returns a new report; it never mutates inputs. `evaluated_at` is an aware ISO8601
instant (invalid request clock raises ValueError). Source clocks must also be
aware; malformed source payload produces `not_assessable`/null conclusions.

System fields are exactly: `source_system,record_id,sku_id,warehouse_id,as_of,
observed_at,status,uom,quantity`. Status must be `pass`; quantity is a nonnegative
integer. This status is a declared synthetic upstream result, not newly verified
ledger reliability. Preserve source identity and both business/observation time.

Manifest fields are exactly: `source_system,session_id,sku_id,warehouse_id,as_of,
freeze_start,freeze_end,observed_at,uom,coverage_complete,frozen,expected_rows`.
Flags must be boolean True; expected raw rows a nonnegative integer equal to
len(counts). Freeze covers the requested cutoff and every actual count timestamp.
Manifest observation occurs after freeze end and all included row observations;
manifest/system must already be available by evaluated_at. A future complete
batch cannot become known at an earlier historical evaluation.

Each count has exactly `source_system,count_id,session_id,observer_id,blind_count,
sku_id,warehouse_id,as_of,counted_at,observed_at,quantity,uom`. Strings are nonempty,
quantities exact nonnegative integers, blind flag boolean True. Natural identity
is `(source_system,count_id)`; identical and contradictory duplicate identities
both block, never silently deduplicate. All rows belong to the same declared
session/grain/cutoff/uom. Business count time is in the frozen interval and not
before as_of; observed_at >= counted_at and <= manifest.observed_at. Unexpected
scope, incomplete coverage or a bad row blocks the entire single-key comparison.
This contract does not normalize moving stock between count timestamps.

### Report and evidence confidence

Report quantities `system_quantity,physical_quantity,variance_quantity` are
conclusions, not raw-data replacements. A blocked comparison leaves all three
null. Valid but uncorroborated evidence retains system quantity only; physical
quantity and variance remain null. Raw count quantities remain in evidence rows.

- `not_assessable`: invalid/incomplete/missing source context; confidence `none`.
- `recount_required`: fewer than two distinct observers (`none`/`single_observer`)
  or disagreeing quantities (`conflicting`). No physical conclusion.
- `confirmed_match`: at least two source-declared blind observers agree,
  physical-system=0; confidence `corroborated`.
- `confirmed_variance`: same corroboration, nonzero physical-system; confidence
  `corroborated`. Signed variance preserves shortage/surplus without classifying
  its cause as shrinkage, damage, theft or receiving error.

These are categorical evidence levels, not measured probabilities or warehouse
truth guarantees. Return sorted findings/reasons and source references, exact raw
count evidence, evaluated clock, canonical complete-input SHA256 and deterministic
run ID. Keep source file byte hashes separately in the experiment provenance.

### Adjustment evidence without execution

Only confirmed nonzero variance creates a read-only candidate proposal. Proposal
ID is SHA256 of canonical JSON `{system,manifest,counts}` with counts sorted by
natural identity. Full source facts/clocks are bound, not only the delta. Exclude
evaluation time and approval rows so the same facts can be reviewed later without
changing identity. Reordering count input does not change the proposal; a source
version, quantity, scope or clock change does.

A candidate records before/count quantities and signed delta, never changes book
stock. Adjustment status is `no_proposal`, `review_required`, `approved_evidence`,
`rejected` or `not_assessable`. `approved_adjustment_quantity` is null unless one
valid explicitly approved review binds exactly to the proposal. Even then this
field is advisory evidence, not an executed write or verified warehouse outcome.

Each review has exactly `source_system,review_id,proposal_id,reviewer_id,decision,
reason_code,reviewed_at,observed_at`. Decision approve/reject; reason_code one of
`shrinkage,damage,count_correction,receiving_error,unexplained_variance`. A reason
is source-declared classification, never inferred from the sign. Reviewer differs
from every count observer. Reviewed time >= all evidence observation times,
observed_at >= reviewed_at, both <= evaluated_at. Natural review identities are
unique; more than one selected review is ambiguous and requires reassessment.
Do not select the latest or silently ignore contradictory/late/unbound reviews.
An invalid review blocks approval while retaining independently confirmed count
conclusions. Reviews without a current proposal cannot authorize a quantity.


## Observed sales adapter

Official source: Chen, D. (2015), Online Retail, DOI10.24432/C5BW33,
[UCI source](https://archive.ics.uci.edu/dataset/352/online%2Bretail),
CC BY4.0. Official archive URL:
`https://archive.ics.uci.edu/static/public/352/online%2Bretail.zip`.
The source/license was rechecked on 2026-10-03. Preserve attribution and the
[license](https://creativecommons.org/licenses/by/4.0/).

Acquire only that archive, at most64MiB, atomically into ignored
`data/raw/uci-online-retail/`. Record real UTC acquisition time, response URL,
archive size/hash, member size/hash, source page/version/license, sheet names,
exact header and row counts. Reuse a valid accepted archive/manifest; reject
hash/schema/count changes without overwriting the acceptance record. No mirror,
automatic license inference or raw-data publication.

Read the official `Online Retail.xlsx` using optional research-only
openpyxl3.1.5 in read-only mode. Do not modify the workbook. Expect541909 data
rows, eight columns in this exact order: InvoiceNo, StockCode, Description,
Quantity, InvoiceDate, UnitPrice, CustomerID, Country. Validate required identity,
date and quantity independently of UCI metadata. Required formulas, blank keys,
booleans, fractional/noninteger quantities, ambiguous date strings and aware
timestamps block adaptation. Preserve recorded naive calendar labels rather
than inventing a source timezone or recording/ingestion clock.

Source row identity is(dataset, archive SHA-256, sheet, original row number),
not(invoice, stock code). Repeated source identities block. Repeated invoice/
stock pairs are counted and retained without silent deduplication because they
do not prove duplicate source rows. Cancellation-coded invoices are excluded
first, then nonpositive non-cancelled quantities. Never subtract returns as
negative demand. Invalid rows block the whole extraction; audit and raw evidence
remain local, while derived series become unavailable rather than a partial pass.

Target: gross positive non-cancelled invoiced units per StockCode/source date,
across the dataset retailer. Country is customer residence, not a warehouse.
StockCode mapping preserves string codes and maps numeric cells to their decimal
identifier; source-row identity remains authoritative. The scope identifier
`dataset-retailer` is an aggregation label, not physical location evidence.
Descriptions/customer IDs/prices/countries are not forecast features.

Only verified complete archive extraction permits observed-sales zeros in the
declared archive calendar. That does not prove availability, latent demand,
lost sales or business completeness outside this archive. The final potentially
partial2011-12-09 is excluded from benchmark dates; raw audit still includes it.
Raw archives, all row/invalid/exclusion evidence, reconstructable series and item
selection manifests stay ignored/local. Git may contain only adapter/benchmark
code, synthetic tests, protocols and attributed aggregate metrics.
