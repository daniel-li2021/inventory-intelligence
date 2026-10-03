# Stage 2: Forecasting & Planning

Status: the bounded synthetic milestone is complete on `main` at `dcada27`
through [PR 7](https://github.com/daniel-li2021/inventory-intelligence/pull/7),
with 76-test combined main acceptance. Started 2026-10-02 after Stage 1
contract-v1 integration. This plan records the delivered sequence;
[next-round research](NEXT_ROUND_RESEARCH.md) proposes later evaluation work.
V1 remains frozen; new database/report interfaces require a separate planning
contract before their implementation. The mathematical baseline kernel below
has no database interface and does not change v1.

## Outcome and scope

Produce a reproducible synthetic demand benchmark, then a read-only replenishment
proposal explaining its demand forecast, inventory position, lead time and input
limitations. Keep SKU/warehouse identity and original evidence. Never place orders
or modify operational stock. Forecasting estimates can be fractional; physical
pieces and final proposed orders remain exact integers.

Shipments are an observed fulfillment outcome, not automatically customer demand.
Stage 1's tiny movement fixture is not a forecasting dataset. A reconciliation
pass is evidence about its covered inventory at one cutoff, not proof of complete
sales history or absence of stockouts.

## Implementation sequence

### 1. Baseline benchmark — implemented first slice

`src/inventory_intelligence/forecasting.py` provides last-observation, historical
mean and seasonal-naive point forecasts. Weekly seasonality is explicit and
configurable for mathematical tests. These are standard benchmark methods; see
[Forecasting: Principles and Practice, simple methods](https://otexts.com/fpp3/simple-methods.html).
No new model dependency is needed for these arithmetic baselines.

`backtest` evaluates identical rolling origins for every model, using only the
observations before each origin. This follows
[time-series cross-validation](https://otexts.com/fpp3/tscv.html).
It scores full multi-day horizons, retains actual/predicted values per origin,
and reports MAE, signed bias (`forecast - actual`) and WAPE. WAPE is null when
actual demand sums to zero; no invented zero percentage or MAPE denominator.
Overlapping folds count each origin/lead pair explicitly. No model is promoted
to production based on the hand-authored weekly demonstration.

Forecasts and scores use stdlib `Fraction`, preserving exact pieces and rational
means. The demo serializes these estimates/scores as rational strings (for
example `12/7`); WAPE is a ratio, not a percentage. There is no automatic rounding.

```sh
PYTHONPATH=src python -m inventory_intelligence.forecasting
PYTHONPATH=src python -m unittest tests.test_forecasting -v
```

Acceptance: five independent tests cover hand-calculated forecasts/scores,
multiple future seasons, quantities above float precision, leakage controls,
zero/intermittent observations, and invalid/insufficient history. This kernel
accepts **already validated daily demand values**. It does not validate dates,
source coverage, availability, stockouts or reliability runs; it cannot be used
as a complete operational forecasting workflow by itself.

### 2. Synthetic demand and eligibility contract — implemented slice

The separately frozen [CONTRACT_PLANNING_V1.md](CONTRACT_PLANNING_V1.md) now governs
`demand.read_series`, `sql/planning_schema.sql` and `synthetic.demand.load_demand`.
Five independent PostgreSQL tests cover zero/gaps, revisions, identity, knowledge
time, DST and deterministic 180-day groups. See the independent
[checkpoint](STAGE2_CHECKPOINT.md). Specify stable
SKU/warehouse references, daily business calendar (`America/Los_Angeles`), source
order-line/version identity, business time, observation time, coverage manifests,
and the forecast origin. Include daylight-saving boundaries in calendar tests.

Use independent synthetic accepted customer order quantities as the first
demand target, defined by acceptance day and requested fulfillment warehouse.
Do not count shipments, transfers, returns or inventory adjustments as new
orders. Keep cancellations/revisions separately identifiable and define their
as-known-at-origin treatment before aggregation; never substitute today's order
status into an older benchmark. This target is recorded accepted demand, not a
claim that lost/unrecorded customer demand has been measured.

Supply approximately 180 daily observations for a few existing synthetic SKU /
warehouse keys, covering constant, weekly, intermittent and zero demand, plus
gaps, duplicate identities, late observations and availability constraints.
Separate training inputs from a manually calculated small oracle. Require an
explicit complete daily coverage record before an absent order day can become
zero. An unknown or stockout-constrained observation is unavailable for baseline
eligibility, not an imputed zero. Stockout recovery/lost-sales estimation is
deferred until its assumptions can be evaluated.

### 3. Versioned forecast runs and evaluation — implemented slice

`planning_runs.run_forecast` and `run_benchmark` now use existing Psycopg and
stdlib, replay origin-known training and persist exact JSONB evidence/results
under Repeatable Read. Five independent database tests assert manual weekly
scores, common exclusions, late revisions, held-out truth isolation, zero WAPE,
immutable history and rollback. Model selection uses 28-day selection MAE; the
other horizons remain explicit comparisons. The final 28 days never choose the
method. This is per-key evaluation, not a claim of model general superiority. Persist
planning results separately from source inputs and reliability findings. Store
input batch/version IDs, training interval, business timezone, cutoff, model
version, horizon, eligibility outcome, forecasts and rolling-origin scores.
Backtests must honor both event time and observation time; chronological slicing
of a revised present-day history alone does not prove absence of leakage.

Compare 7/14/28-day horizons on shared eligible origins; retain a final temporal
holdout separate from selection. Compare stable/seasonal/intermittent groups
separately rather than hiding them in one average. Add more sophisticated models
only when baseline comparisons expose a concrete weakness. Predictions must not
overwrite earlier runs; unchanged inputs produce stable semantic results.

### 4. Deterministic replenishment proposals — implemented slice

`replenishment.run_plan` now reads trusted inventory, explicit supply manifests,
reservations/confirmed inbound and lead/review/safety/pack/MOQ policy. It persists
projections and proposals, or `not_assessable` with no recommendation. The policy
uses the maximum daily safety deficit after supplier arrival; final inventory
position alone can hide earlier shortages. Current source SQL is revalidated at
decision time, reusing Stage 1 code without modifying its frozen interfaces.

Require a current passing Stage 1 run at the planning cutoff, covering the
selected keys, plus independently complete reservations/commitments, confirmed
inbound quantities/arrival dates and declared supplier lead times. Initially
fail closed on a non-pass run; do not invent per-bucket readiness from a report
that does not provide it. Historical reconciliation passes must satisfy the
decision-time freshness policy rather than retaining their old evaluation time.

Define inventory position, horizon, review period, safety-stock policy and
whole-piece rounding explicitly in the planning contract. Count inbound stock
only when its arrival falls within the relevant horizon. Never subtract physical
shipments a second time as reservations. Compute the minimum nonnegative order
needed to cover the declared target, then round to declared pack/MOQ constraints.
Show the unrounded estimate, rounding and each supporting input. Missing lead
time, inbound/reservation completeness, or an unassessable stock bucket yields
`not_assessable` with no order recommendation. Default safety stock must not
masquerade as a calibrated service-level guarantee.

### 5. Portfolio acceptance — local and remote CI evidence

[PLANNING.md](PLANNING.md) documents fresh-database generation, baseline
evaluation, APIs and clean/blocked planning demos. [Verified summary](examples/stage2.md)
records the deterministic downstream outcomes. The expanded suite has 45 tests:
22 frozen Stage 1, six kernel and 17 demand/forecast/planning checks. All passed
on a fresh local PostgreSQL database and in the pinned PostgreSQL 17.9 CI job.
[Final code CI](https://github.com/daniel-li2021/inventory-intelligence/actions/runs/36999887817)
ran all 45 tests successfully; hygiene also passed. Exact proposals are checked
against manual arithmetic, including zero demand, stockout gaps, late corrections,
pending/delayed inbound, duplicate orders, unit/pack boundaries and immutable history.
The existing CI command includes the full downstream demo; JSON/Markdown output
and a verified concise summary are available. Compatible contracts remain a
prerequisite for integration, now satisfied by the combined review and merge.

No scheduler, ERP, web UI, LLM, cloud service or business-data import is needed
for this stage. Its completion requires the demand/eligibility adapter, persisted
evaluation and proven planning arithmetic; the baseline kernel alone is a start.

## Integration handoff

The three dependent slices cover eligibility/contract, versioned benchmarks,
and inventory projection/proposals. The combined three-stage review integrates
all three with the existing main and corrects holdout selection truth timing.
[Review evidence and final benchmarks](THREE_STAGE_REVIEW.md) record the later
76-test acceptance and exact downstream results. The user authorized merging
the remaining fixes on 2026-10-02; this integration preserves the frozen Stage 1
interfaces and adds the separately versioned planning explanation contract.
No web UI, scheduler, cloud service or advanced forecasting model was added.

Verified integration: PRs 3/4/5 and PR 7 are merged. Remote `main` at `dcada27`
contains all slices; [CI run 37044676872](https://github.com/daniel-li2021/inventory-intelligence/actions/runs/37044676872)
passed both jobs and all 76 combined tests. The earlier 45-test slice results
above are retained as historical evidence. No new model or policy is selected
by the next-round investigation.
