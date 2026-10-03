# Fresh traces and costed warmup — v1

Frozen before generating results on 2026-10-03. Identifier
`fresh-warmup-v1`. Separate offline synthetic research using the unchanged
decision/intermittent event kernel; operational contracts and old artifacts stay
frozen. This is the first implementation handoff in [the roadmap](RESEARCH_ROADMAP.md).

## Frozen experiment

Demand seeds 1301/1709/2027, versioned with family name. Families: constant,
weekly, zero, lumpy, temporary pause/recovery, seasonal low, gradual decline and
permanent obsolescence. Generate 420 days once per family/seed. Train prefix is
196 days; origin blocks begin on 252, 308 and 364 and each score 56 days. The
first block is descriptive selection-period evidence; two later blocks remain
evaluation-only. No automatic method selection or tuning in this study. Controls
are repeated deterministic paths, not three independent observations.

Each origin is an independent initial-state trial. Warm arm starts 56 days before
scoring with ten pieces, no backlog or pipeline and runs its own policy through
warmup and scoring without reset/runoff at the boundary. Cold arm starts at
scoring with the same ten pieces and empty backlog/pipeline, using exactly the
same prior demand history as the warm arm. Thus this intervention changes state,
not forecasting information. Repeated origins are correlated; do not count
warmup/score overlaps as independent demand paths.

Compare mean/fixed0, seasonal-naive/fixed0, TSB/fixed0, TSB/empirical90 and
TSB/empirical95. TSB alpha/beta remain 1/5. Existing calibration uses completed,
non-overlapping H-day residuals with min_train28/min_samples8; no grid refit.
Parameters: L2/R7/phase0, pack2/MOQ4, no prior commitments or initial inbound.
Supplier paths use a separate SHA-256-derived RNG namespace per family, demand
seed and origin block; draw daily hidden delays from [0,0,1,3]. Warm/cold see the
same absolute-calendar review-slot realizations during scoring. Origins have
independently seeded supplier traces. Zero-order reviews consume their slot.
Neither future demand nor hidden delays reaches a policy provider.

## Costs and states

Record warmup costs, scoring costs, runoff costs, warmup ending state (stock,
backlog, pipeline), scoring ending state and settled terminal stock. Charge
initial ten pieces at synthetic unit cost2 in both arms, and every purchased
piece at cost2 when the order is placed, including warmup and runoff orders.
Daily h1/b10/setup2 follows existing exact kernel semantics. No salvage value.
Purchased pipeline cannot vanish from accounting at the scoring boundary.
Previously supplied training history is data only, not free physical inventory.

All arms share the calendar settlement end: score end + L2 + maximum declared
delay3 + R7 = twelve days. Use each arm's unchanged fixed runoff, then charge
terminal stock holding through that common date; never truncate an unsettled
arm. Full intervention cost includes acquisition + warmup + scoring + common
runoff. Cold is inactive before score start, so has no simulated pre-start
operating obligations/cost. Full-cost and score-period comparisons answer
different questions; report both, not a misleading steady-state savings claim.

## Metrics and evidence

Exact score-only new-demand fill, complete-cycle service, backlog/stock exposure,
cost and denominators. Warmup misses remain reported, even though excluded from
score service. Score cycle service includes carried warmup backlog. Full-run
eventual fill must conserve accepted units and settle backlog/pipeline.
Report nominal q90/q95 against achieved fill/cycle, cumulative rounded target
coverage, pinball loss and completed calibration counts/ranks; coverage is not
inventory service. Include only review targets wholly inside the scored block.
Forecast errors and target loss retain exact Fractions.

For the cold arm, independently derive earliest possible policy receipt and
startup-unfillable units, and compare actual startup misses to that bound. For
the warm arm, separate misses before/after the same calendar cutoff as a paired
timing diagnostic; the cold feasibility ceiling does not bound warm carryover.

Save full generated demand and daily supplier paths, per-arm input hashes,
candidate parameters, trajectory hashes, state snapshots, review/calibration
evidence (equal daily forecasts use exact run-length encoding), summary metrics
and code/protocol dependency SHA-256. Cache identical
physical inputs; repricing or controls cannot manufacture independent evidence.
Artifact publication makes these traces consumed. Future challengers need a
new version or genuinely unviewed evaluation evidence.

Independent acceptance covers hand-calculated warm boundary backlog/pipeline,
acquisition costs and common-window holding, denominator/null behavior, aligned
supplier slots, invalid inputs, full conservation and prefix invariance when
only future demand/delays change. No population confidence, calibrated service
guarantee, retailer profit or operational champion change is claimed.
