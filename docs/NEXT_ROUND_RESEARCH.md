# Next investigation: forecast value and inventory decisions

Current priority assessment: [READINESS_NEXT_STEPS.md](READINESS_NEXT_STEPS.md)
reviews the completed Decision Lab and retained research on 2026-10-03. The
sequence below records earlier proposals and subsequent assignments; it is
historical context rather than the next implementation handoff.

Investigated 2026-10-02 against fetched `origin/main` at `dcada27`. Three read-only
agents investigated decision evaluation, models/lifecycle and public datasets.
Publication refresh: main advanced to `ce8ab0d` with PR 8; existing
[latest CI](https://github.com/daniel-li2021/inventory-intelligence/actions/runs/37085401000)
passed 79 tests. Its [Copilot benchmark](STAGE3_BENCHMARK.md) documents observed
routing failures as a separate follow-up.
The user subsequently assigned the smallest next milestone on 2026-10-02.
Its separate [frozen decision contract](CONTRACT_DECISION_V1.md) and
[implementation/evaluation](DECISION_BENCHMARK.md) supersede the proposed
synthetic simulator handoff below. Public-data acquisition, advanced models and
changes to existing frozen contracts remain outside that assignment.
The subsequent request to continue the plan assigns the separate
[intermittent/safety contract](CONTRACT_INTERMITTENT_V1.md) and
[fresh held-out evaluation](INTERMITTENT_BENCHMARK.md). The
[public observed-sales protocol](PUBLIC_SALES_PROTOCOL_V1.md) is concrete and
awaits the public-data boundary choice; no real observations have been imported.
The user authorized integration of these milestones through PRs 10/11 on
2026-10-02. Both PRs 10/11 are merged with the refreshed PR 9 documentation.
The [stabilization wave](STAGE3_STABILIZATION.md) then verifies combined acceptance
and the classification/selector fix on a fresh routing holdout. Those evaluation
sets are now consumed; [checkpoint boundaries](AUTOMATION_PROGRESS.md) govern
future tuning. This authorization does not import real observations.
For the original research, existing benchmark JSON and acceptance evidence were reused; no data
download, new forecast fit, database pipeline or model API request occurred.

Recommendation: **prove inventory decision quality with existing models first;
then test SBA/TSB on unpredictable demand; add a separately governed public-sales
benchmark; reserve LightGBM and lifecycle infrastructure for demonstrated needs.**

## Current system and the material gaps

All three bounded synthetic stages are merged through
[PR 7](https://github.com/daniel-li2021/inventory-intelligence/pull/7).
[Main CI](https://github.com/daniel-li2021/inventory-intelligence/actions/runs/37044676872)
passed 76 tests. See [checkpoint](AUTOMATION_PROGRESS.md) and
[three-stage review](THREE_STAGE_REVIEW.md) for exact prior evidence.

The current planner already handles source identity, completeness, two knowledge
clocks, trusted inventory, reservations, dated inbound, lead/review periods,
declared safety pieces, packs/MOQ and exact prefix projections. `run_plan` calls
`replenishment.project`; `copilot_planning` also recomputes its arithmetic to
validate saved proposals. Preserve both and their historical interfaces.

The remaining gaps are business outcome validation, calibrated uncertainty and
realistic external demand evidence. `project` carries signed cumulative deficits;
it does not model fulfilled quantities, physical lost-sales inventory, backlog
clearance, repeated ordering or realized cost/service. A safety quantity is a
declared input, not an achieved service guarantee. Saved runs already provide
useful lifecycle provenance; automated deployment is not the immediate gap.

For an operational comparison, Odoo documents time-aware replenishment,
manual/automatic purchasing routes and lead buffers; ERPNext describes projected
stock and reorder levels using declared safety and consumption. Our advisory
calculation covers some of the same planning inputs. Supplier calendars/capacity,
execution/approval feedback, multi-location allocation, lifecycle and cost/service
calibration remain outside its contract. The immediate portfolio improvement is
outcome evidence, not building an ERP. These docs do not establish that either ERP
optimizes this project's stochastic objective.
[Odoo reordering](https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/inventory/warehouses_storage/replenishment/reordering_rules.html),
[Odoo lead times](https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/inventory/warehouses_storage/replenishment/lead_times.html),
[ERPNext item policy](https://docs.frappe.io/erpnext/item).

## Why MAE/WAPE are not sufficient

Keep daily MAE, signed bias and nullable WAPE for compatibility. On the same
scored observations, MAE and WAPE rank methods identically: the absolute-error
numerator is shared and each denominator is independent of the method. Neither
expresses asymmetric shortage/holding consequences. MAE targets a median; when
zero demand has probability above one half, a zero prediction can minimize daily
absolute loss despite positive expected demand.
[FPP3 accuracy](https://otexts.com/fpp3/accuracy.html).

Existing [round B](review/final-round2.json) already shows different rankings on
the irregular 28-day holdout. Naive daily MAE is 3, mean is 827/266 and seasonal
naive is 9/2. Absolute cumulative error, computed as `abs(stored_bias * 28)`,
is respectively 36, 278/19 and 16. Mean is better on the horizon total while
naive is better on daily MAE. This derivation was checked with stdlib `Fraction`;
it is not a measured inventory-cost result. Daily timing still matters because
an accurate final total can conceal an earlier shortage.

A separate hand-calculated one-period counterexample has four equally weighted
independent demand scenarios `[0,0,0,10]`, stock equal to the forecast, holding
penalty 1 per leftover piece and lost-sales penalty 10 per unmet piece. Stock
0 gives MAE 5/2 and mean cost 25; stock 3 gives MAE 4 and cost 79/4; stock 10
gives MAE 15/2 and cost 15/2. The MAE winner is the cost loser under these declared
synthetic penalties. This is an oracle, not a real financial estimate.

Add cumulative protection-period error/bias for `H=L+R`, inventory outcomes and
paired cost/service comparisons. RMSSE or squared loss can diagnose mean accuracy;
scaled metrics need a nonzero training-only scale, otherwise null. If probabilistic
forecasts are introduced, add pinball loss and empirical coverage for the actual
cumulative target. Do not sum daily quantiles and call the result a cumulative
quantile. Keep all-zero controls and explicit metric denominators.
[FPP3 distribution evaluation](https://otexts.com/fpp3/distaccuracy.html).

## Smallest next milestone: decision-benchmark-v1

First freeze a separate offline research contract; leave planning-v1 unchanged.
The proposed first implementation is one synthetic, single-key **backlog**
simulator using existing forecasts. Accepted units remain committed when unfilled.
All units being due on acceptance day is an explicit counterfactual assumption.
A later **lost-sales** profile discards newly unmet offered-demand units; it needs
a separately named demand target. Do not silently reinterpret accepted orders or
signed projected deficits as lost sales.

Proposed day sequence, to be fixed in the handoff:

1. Receive prior scheduled inbound at start of the source-local day.
2. Fulfill old backlog and due prior commitments with a declared priority rule.
3. On review days, order using only information available before new daily
   demand; order arrival is start of day `t+L` after L full calendar days.
4. Observe and attempt to fulfill new daily demand at day end.
5. Record ending on-hand, unmet new units, backlog and costs.

Initial reservations are pre-existing commitments and cannot reappear as new
demand. Inventory position must retain outstanding orders so repeated reviews
do not order the same need twice. Supplier realized future delays stay hidden
from the policy. A receipt on day 2 cannot repair day 0/1 immediate fill rates.
Simulator libraries use varying event sequences; copying their equations without
translating lead conventions risks off-by-one outcomes.
[Stockpyl event sequence](https://stockpyl.readthedocs.io/en/latest/tutorial/tutorial_sim.html).

Independent timing oracle: start with 1 piece; demand 2 on day 0; receive 2 at
start of day 1; demand 1 on day 1. Backlog mode ends `(inventory, backlog)` at
`(0,1)` then `(0,0)`. Lost-sales mode loses 1 on day 0 and ends inventory at
0 then 1. A later receipt must not erase the first day's shortage.

Cost definitions are proposed project choices, with exact rational synthetic
rates and integer physical quantities:

- Holding: `h * ending_on_hand`, h in currency/piece/day.
- Backlog: `b * ending_backlog`, b in currency/piece/day while waiting.
- Lost sales: `p * newly_unfulfilled_units`, p in currency/piece, charged once.
- Ordering: `K * (order_qty > 0)`, K in currency/order placed, not receipt row.
- Acquisition, if included: `c * ordered_units`; declare terminal valuation of
  stock and pending orders. Do not claim actual profit or business savings.

Do not charge both backlog and lost-sales penalties for one unit. Initially
omit acquisition cost and explicitly score holding, waiting/shortage and setup
penalties; report terminal inventory/backlog/pipeline and use a declared runoff
or terminal treatment so pushing obligations past the boundary cannot win.
Freeze initial stock, review phase, warmup, terminal cycles and scoring window.

Service measures must stay distinct:

- Immediate unit fill rate: immediately filled new units / all new demand units;
  zero demand gives null. Eventual backlog completion is a separate measure.
- Cycle service: shortage-free complete review cycles / all complete review
  cycles; no complete cycles gives null. Define cycle boundaries explicitly.
- On-time prior-commitment fill: pieces fulfilled by their due day / pieces of
  prior commitments due in the scored window; null if none. Report separately
  from new-demand fill. Shortage days/cycle failures include overdue commitments.
- Also report shortage days/units, backlog piece-days, on-hand piece-days,
  average/end stock, order count and outstanding terminal orders.

Cycle service measures frequency; fill rate measures units. An empty shelf with
no unmet demand is not automatically a shortage day.
[MIT stochastic inventory lecture](https://ocw.mit.edu/courses/15-772j-d-lab-supply-chains-fall-2014/0d50c5c77382852102ee30b98f1d4657_MIT15_772JF14_Lec14.pdf).

Compare **forecast plus policy**, under identical demand, initial inventory,
supplier scenarios, reservation assumptions, packs/MOQ and cost regimes. Tune
only in selection data. Include independent clean/zero, early-shortage, delayed
receipt, duplicate-order prevention, rounding and terminal-obligation oracles.
Implement after a handoff; this investigation adds no simulator or new tests.

## Uncertainty, safety stock and service targets

After deterministic outcomes are independently verified, compare declared fixed
safety with empirical quantiles of cumulative protection-period forecast errors
from completed pre-origin calibration windows. A target `S = forecast(D_H) +
quantile(error_H)` is a candidate policy; validate its achieved service, not just
its nominal quantile. Define `error_H = actual(D_H) - forecast(D_H)`; existing
reported bias has the opposite sign. Preserve integer target/order rounding and
prior commitments.

Start with fixed L; then evaluate a small declared synthetic delay distribution,
using the same hidden future supplier trace for all candidates. Under IID daily
demand independent of lead time and fixed R, the derived protection-demand
variance is
`E[L+R] * Var(daily_demand) + Var(L) * E[daily_demand]^2`.
This diagnostic excludes serial correlation and demand/supply dependence; joint
scenario paths are more appropriate when those assumptions fail. A normal
`mean + z * stddev` policy can be a reference, not an intermittent service guarantee.

The newsvendor critical fractile `underage / (underage + overage)` belongs to a
defined one-period loss with comparable cost units. A shortage cost per unit and
holding cost per unit/day cannot be combined without a time horizon. The fractile
does not prove optimality for repeated review with fixed order cost, positive
lead time, packs/MOQ and lost sales.
[Stockpyl newsvendor equations](https://stockpyl.readthedocs.io/en/latest/api/seio/newsvendor.html).

## Models: test the weakness before increasing complexity

The seven 180-day groups establish arithmetic and replay. Periodic intermittent
demand is deliberately seasonal-naive-perfect; irregular demand uses one seed.
Repeating that archive is not new statistical evidence. Add unpredictable
intermittent/lumpy, declining occurrence/obsolescence and multiple declared seeds
before claiming an intermittent method improves decisions.

Suggested challenger order after the decision benchmark is frozen:

1. Retain all current baselines and an explicit zero diagnostic. A recent-window
   mean or SES belongs to a demonstrated drift weakness, not automatically every
   intermittent benchmark.
2. Use Croston as a reference; test **SBA and TSB** first. Croston updates positive
   size/inter-arrival estimates at arrivals, is biased and does not decay during
   zero runs. SBA approximately corrects bias; TSB updates occurrence probability
   each period and addresses obsolescence. None is a universal winner.
   [Original TSB research](https://pure.rug.nl/ws/portalfiles/portal/145394864/Intermittent_demand_Linking_forecasting_to_inventory_obsolescence.pdf).
3. Test **ADIDA** if cumulative-demand weakness persists; add **IMAPA** only if
   sensitivity to aggregation levels warrants combining them. Disaggregation can
   lose daily timing, so cumulative improvements must survive shortage testing.
   [ADIDA research](https://researchportal.bath.ac.uk/en/publications/an-aggregate-disaggregate-intermittent-demand-approach-adida-to-f/).
4. One bounded global **LightGBM** challenger becomes useful with enough public
   item/store histories and frozen features. Objective choice matters: L1 targets
   a median; L2 and quantile serve different targets. Capability is not evidence
   of lower inventory cost. [Official objectives](https://lightgbm.readthedocs.io/en/latest/Parameters.html).

Advanced models touch shared `METHODS` in forecasting, planning runs, replenishment
and copilot validation. Copilot-2 recognizes `planning-v1`/`baselines-v1`, exact
rational evidence and MAE selection. A future handoff must version new methods,
metrics and approximate estimate precision while preserving historical decoding.
Do not turn ML floats into `Fraction(float)` and imply exact model arithmetic.
Physical pieces, source quantities and final orders remain integer-exact.

Freeze smoothing alpha/beta, initialization, windows, aggregation/disaggregation,
quantile calibration and policy parameter grids/budgets using selection data only.
Per-origin re-estimation uses earlier information exclusively. Training labels
must be fully observed/known before their split boundary; exclude labels whose
target window crosses validation/holdout. Early stopping cannot use holdout.

## M5: conditional yes, separate observed-sales protocol

**Yes for a new observed-sales research benchmark with synthetic inventory policy;
no as a direct planning-v1 accepted-order/uncensored-demand adapter.** Current
AGENTS.md and planning-v1 permit synthetic business inputs only. Before import,
authorize a separate public-data boundary and named protocol; do not edit or
weaken frozen v1 contracts to make rows pass eligibility.

M5 provides daily item/store unit sales, calendar and weekly prices for 30,490
bottom-level series. These are realized sales, not accepted order versions or
measured lost demand. It supplies neither daily stock-availability manifests nor
historical source-recording/ingestion clocks. Weekly prices average across seven
days and cannot automatically be treated as origin-known inputs. Preserve source
date labels; stores are research locations, not proven fulfillment warehouses.
Observed sales zeros do not prove zero unconstrained demand. Missing price is
not evidence of inventory availability.
[Official data](https://www.kaggle.com/c/m5-forecasting-accuracy/data),
[organizers' guide](https://storage.googleapis.com/kaggle-forum-message-attachments/772349/15032/M5-Competitors-Guide-Final-10-March-2020.pdf).

Kaggle labels the data license “Subject to Competition Rules.” Redistribution
rights were **not verified** because the rules page was unreadable in this
investigation. Check/retain applicable terms before acquisition or publication;
do not infer data rights from a code repository's MIT license or an unofficial
mirror. Keep raw and reconstructable data outside Git until rights are established.
No acquisition was performed.

Proposed bounded design, not executed:

- Freeze roughly 256 CA item/store keys, sampled with a declared seed using
  only a fixed training prefix. Stratify by department, sparsity and volume
  without looking at holdout. Retain all-zero controls and exclusions.
- Retain archive SHA-256, source URL/version/terms, real retrieval timestamp,
  file/schema/row counts, selected-key manifest, adapter/code/protocol versions
  and source identities `(dataset, item_id, store_id, day)`. Validation/evaluation
  filename suffixes must not change canonical item identity.
- Store actual acquisition time separately from modeled historical release
  latency. Static archives cannot prove historical as-known ingestion; simulated
  knowledge gates are assumptions. Keep synthetic revision/DST/availability
  oracles as the independent proof of the operational contract.
- Freeze final labeled 28 days as a predeclared internal holdout withheld from
  fitting/tuning, with multiple earlier weekly origins/windows for 7/14/28-day
  comparison. Current synthetic holdout
  has informed this research; keep it as regression evidence. New challenger
  claims need new evaluation data withheld from fitting/tuning.
- Start with past sales and deterministic calendar. Lags, scaling, segmentation
  and metric denominators use each origin's training prefix only. Global models
  cannot train on other items' future dates. Multi-step features cannot use future
  actual demand. Future prices/promotions/SNAP/events need knowledge evidence or
  an explicit competition-known covariate scenario, separately reported.
- Preserve observed sales zeros; never compress missing days or infer product
  launch/availability from first positive sale. Compare observed-sales accuracy
  separately from conditional policy simulation on a declared proxy demand trace.
  Synthetic stockouts and penalties are not Walmart historical shortages/profit.

M5's full hierarchical WRMSSE leaderboard is not our inventory decision score.
The organizers report strong LightGBM-based accuracy, while a robustness study
shows sensitivity across test periods. These support a fair challenger and
multiple windows, not a predetermined classical-model winner.
[M5 accuracy paper](https://doi.org/10.1016/j.ijforecast.2021.11.013),
[M5 robustness study](https://eprints.lancs.ac.uk/id/eprint/159736/).

Fallback: [UCI Online Retail](https://archive.ics.uci.edu/dataset/352/online%2Bretail)
has explicitly documented CC BY 4.0, invoice/product quantities/timestamps and
cancellation-coded invoices. It gives clearer sharing terms and transaction
evidence, but lacks accepted-order revisions, observation clocks, availability
and warehouses. Invoice time is not proven acceptance time; customer country
is not fulfillment location. It still requires a separate research target.

## Supplied repository references: useful questions, unverified gains

[Tanishqarya17/intermittent-demand-forecasting](https://github.com/Tanishqarya17/intermittent-demand-forecasting)
reports a 5,000-series internal RMSSE experiment and synthetic quantile stocking
costs. Its sample score is not official full-hierarchy WRMSSE. Reported compute
and savings numbers were not reproduced here and do not establish improvement
in this project. Daily q95 coverage does not establish protection-period service;
cost dimensions and policy arithmetic need independent verification.

[dhanysaputra/demandforecast](https://github.com/dhanysaputra/demandforecast)
advertises demand reconstruction, inventory simulation, MLflow and drift gating.
It is a feature reference, not proof of business improvement. Linked code could
not be inspected in this investigation; implementation claims remain unverified.
Imputed “true demand” cannot enter our pipeline as verified source evidence.

## Promotion evidence and minimal lifecycle

Predeclare improvement thresholds, required service and compute budgets in the
handoff before evaluating challengers. Promote only for lower paired held-out
cost at required/comparable service, or higher service at a fixed budget, with
no material clean/zero or important-segment regression. Report cost regimes,
segments, windows and uncertainty; overlapping weekly folds are correlated,
not hundreds of independent experiments. If results are unstable or disappear
under reasonable penalty/lead assumptions, keep the simpler approved baseline.

Existing append-only run UUIDs, model/code versions and input digests are the
foundation. Add parameters, data/feature/evaluation versions and artifact hash
only when needed. A reviewed champion reference and previous reference can
support rollback without a registry server. MLflow is a later scale option,
not the prerequisite for this experiment.
[MLflow registry concepts](https://mlflow.org/docs/latest/ml/model-registry/).

A failed challenger leaves the approved model unchanged. Data failure blocks
assessment; an old run is not current inventory evidence. Any fallback must use
current eligible inputs. For cheap statistical methods, updating current estimates
is distinct from champion promotion. Drift in zero rate, positive-size distribution
or cost/service can trigger investigation after enough observations, not automatic
promotion. Schedule evaluation only after value and cadence are established.

Next assignment should freeze the synthetic decision contract and independent
oracles, then implement/evaluate the current baselines. Public-data permission,
acquisition rights and protocol review are later prerequisites for the M5 slice.
