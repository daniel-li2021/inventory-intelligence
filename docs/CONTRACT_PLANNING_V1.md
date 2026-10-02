# Planning contract — v1

Frozen for this Stage 2 implementation handoff on 2026-10-02. This contract adds
separate `planning_input` and `planning` schemas. It does not amend Stage 1 v1.
All data is synthetic. Runtime reads inputs and appends results; no orders are
placed and no operational rows are repaired. The handoff covers the demand
adapter, synthetic replay archive, versioned benchmark, projection and proposals.

## Demand and eligibility

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

## Forecasting and evaluation

Only wholly eligible contiguous daily training series feed the existing exact
`naive`, `mean`, `seasonal_naive` kernel. Version `baselines-v1`, 7-day season,
minimum training 28 days. Record cutoff, training range, batch/version,
timezone, method/version, horizon, code version and eligibility evidence.
Invalid API arguments are errors; unavailable source evidence is `not_assessable`
with null predictions/scores, never a fabricated zero forecast.

Benchmark horizons 7/14/28 use identical candidate origins (weekly spacing) and
require the maximum horizon to fit before selection end. Reconstruct each origin's
training using that origin's knowledge time. Truth uses a separate explicit
evaluation cutoff and must itself be eligible. Retain reasons for excluded folds.
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

## Inventory projection and replenishment

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

## Acceptance and boundaries

Independent manually supplied small inputs assert exact forecasts/scores,
zero versus gaps, cancellations/corrections and late observation replay, daylight
saving, projections, delayed inbound, reservations, pack/MOQ and history. Real
PostgreSQL enforces runtime permissions and atomic persistence in CI. Synthetic
180-day groups (constant, weekly, intermittent, zero plus blocked controls) are
separate from the manual oracle. Stage 2 requires these integrated pieces and
their CI evidence; a baseline kernel or a PR title alone cannot complete it.
No LLM, agent, UI, scheduler, cloud or advanced forecasting model in this handoff.
