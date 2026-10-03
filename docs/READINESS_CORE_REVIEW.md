# Core engineering review — 2026-10-03

Review baseline: `429cc71` (current `main` at review start). Scope was the
Reliability → Demand/Forecast → Replenishment → persisted Copilot explanation
path. This is local synthetic evidence, not production validation.

## Meaningful finding and fix

The persisted planning explainer validated scores and projection arithmetic but
could accept contradictory source evidence. For example, a forecast with seven
positive predictions and `training.status=eligible` could cite a null daily
quantity, stockout evidence, another SKU, or knowledge learned after the origin.
Similarly, mutually consistent backtest scores/actuals could contradict their
cited daily truth. The existing correct-engine happy paths did not challenge
these report boundaries.

The explainer now checks eligible daily evidence against its declared batch/key,
calendar interval, knowledge time, complete/available day record, exact selected
order quantities and source clocks. Archive metadata must cover the interval;
selected records require valid row/revision identities and exact membership in
the retained visible raw evidence. Selected natural order identities must be
nonempty and unique across included days, even if a duplicate's daily quantity,
count and raw day evidence have been coherently rewritten. It requires contiguous complete training,
checks the shared weekly selection origins and holdout timing, and compares fold
actuals against the retained eligible truth. Replenishment training must agree
with its forecast training and declared policy horizon. Invalid evidence raises
an error; it never supplies a replacement number. Blocked historical runs remain
explainable. The WAPE limitation now includes the unavailable-scoring case.

The changes add no source queries, replay, forecasting, external calls or writes
to the explainer. They preserve the frozen public interfaces and the historical,
advisory-only output with `proposed_order_qty=null`.

## Reviewed surfaces and retained strengths

- Stage 1: `CONTRACT_V1.md`, `reliability.py`, and the complete read-only SQL
  projections/checks. Explicit coverage, independently observed snapshots,
  localized versus global blocks, numeric intermediate sums, deterministic
  findings, and atomic append-only persistence remain appropriate boundaries.
- Demand: `CONTRACT_PLANNING_V1.md`, `demand.py`, schema and manual PostgreSQL
  oracles. Dual knowledge clocks, immutable gross acceptance identity, revision
  visibility, local-day/DST boundaries, availability censoring and counted zero
  days are explicit. Cancellation does not erase accepted demand.
- Forecasting/persistence: `forecasting.py`, `planning_runs.py` and their callers.
  Shared-origin selection, holdout knowledge freeze, exact rational estimates,
  null WAPE for zero truth, and stable semantic history remain sound within the
  wholly eligible synthetic series reviewed.
- Replenishment: `replenishment.py` and its independent hand-calculated oracle.
  Current Stage 1 revalidation, strict cutoff/observation gates, explicit supply
  manifests, disjoint new acceptances/reservations, start-of-day arrivals,
  prefix safety need and exact pack/MOQ rounding are retained.
- Copilot: `copilot.py`, `copilot_planning.py`, both contracts and database/CLI
  callers. Explicit run selection, bounded complete retrieval, read-only
  Repeatable Read and refusal to authorize a current order remain intact.

No additional engine defect was established in these inspected boundaries.
This scoped finding does not imply an exhaustive formal audit.

## Validation actually run

Python 3.12.14, Psycopg 3.3.6 and a newly bootstrapped disposable PostgreSQL 17.6
database supplied by the integration owner. All commands used `PYTHONPATH=src`.

- The three new adversarial regression methods were executed against the
  unmodified `429cc71` explainer: all three failed because contradictory evidence
  was accepted. Their forecast/proposal/fold outputs remained otherwise valid.
- The focused `test_copilot_planning`, `test_planning_runs`, `test_demand`,
  `test_replenishment` and `test_forecasting` modules passed: **31 tests**.
  These include exact independent manual values, late revisions, holdout
  isolation, source mutation after a saved pass, blocked/null results, role
  permissions, unchanged prior history and the offline CLI.
- The final Copilot-only recheck passed all **7 tests** after the last guard
  adjustments. Repeating the entire focused run in the same database hit the
  existing demo loader's intentional duplicate-namespace refusal; source data was
  preserved. Use a fresh database for combined acceptance.
- A final duplicate-selection regression also failed before its uniqueness
  guard: duplicating the same selected order while adjusting the retained count
  and daily quantity was accepted. The final Copilot-only 7-test recheck passed
  after this narrow follow-up.
- `git diff --check` passed. Fresh combined integration acceptance is owned by
  the integration owner and is recorded separately after integration.

## Remaining boundaries and next evidence

The frozen Copilot contract deliberately forbids forecasting/replay during
explanation. It checks retained evidence consistency and score/proposal arithmetic;
it does not independently regenerate baseline predictions, select latest raw
revisions again, recompute the input digest, or prove that source owners kept the
archive unchanged. A coherently rewritten report can therefore remain coherent
to the explainer. Treat this as evidence explanation, not an independent engine
audit or cryptographic attestation. A future deterministic provenance verifier
would need an explicit coordinated contract decision before implementation.

Inventory conservation and arithmetic are strong enough to freeze within the
declared contract. Real demand adapters, actual reservation/forecast disjointness,
supplier timing and calibrated safety levels still require business-specific
evidence. Safety pieces are an input policy, never a service-level guarantee.
Observed sales without availability evidence cannot establish unconstrained
demand. Independent observed-data evaluation and inventory-feasibility/calibration
experiments would add more evidence than merely introducing a more complex
forecasting model.
