# Public sales-proxy safety and achieved service — v1

Protocol `uci-sales-proxy-safety-v1`, authored before its first simulation.
Dependency: the attested adapter/subset of `uci-observed-sales-forecast-v1`.
These public sales windows have already been scored in forecast research. This
is exploratory reuse of consumed observations, not fresh sealed holdout evidence.
No stock availability, uncensored demand, historical supplier or profit is known.

## Frozen experiment

Reuse the exact 32 training-stratified item identities, seed701, source archive
and dates. No re-selection or changed bin boundaries. Fixed mean and SBA (alpha1/5),
with safety off, empirical cumulative residual q90 and q95. These are predeclared
comparisons; no method/safety optimization or promotion is performed. Two lead
times L=2/5, review R=7, pack2/MOQ4. Synthetic supply is either no delay or an
extra three days on every policy-order review slot, hidden from forecasts. Demand
calibration does not incorporate that supply variability.

Training ends2011-09-16. Start each arm with zero stock/backlog/pipeline. Run
56 selection dates as warmup, then28 holdout dates continuously with no reset,
transfer or inventory gift. Known prior commitments/inbound are empty by design;
public sales are modeled new obligations under the research backlog semantics.
No order is actually executed. Completed source dates are the only observations
seen at reviews. Forecast and safety both update from completed history.

Use existing nearest-rank calibration of **signed** L+R cumulative errors at
non-overlapping completed training origins, min_train28/min_samples8. Quantile
error is clipped below at zero and ceiled to whole-piece safety. The protection
target is ceil(sum of origin forecasts + safety). q90/q95 name empirical target
quantiles, not contractual fill/cycle-service guarantees.

32 items × 2 methods × 3 safety settings × 2 leads × 2 supply regimes =768
continuous logical arms;512 paired contrasts compare q90/q95 to safety off in
the same item/method/lead/supply cell. No selection gates or holdout tuning.
Calibration/forecasts are equal across supply regimes for identical origins.

## Accounting and score boundaries

All arms close after84 warmup+holdout days and a common15-day settlement. The
unchanged kernel clears due backlog during runoff without forecast/safety/new
sales. Shorter native runoff is extended with paid terminal holding, never
truncated. Charge all orders at2 per piece, holding1 per end-stock piece-day,
backlog10 per end-backlog piece-day, setup2 per positive order. Include warmup,
holdout and settlement charges separately and together. Zero residual-stock
credit. Costs are synthetic penalties, not retailer savings or profit.

Primary service uses only days[56,84): immediate units / modeled new units,
complete four seven-day cycles, carryover-inclusive backlog and new unmet units.
Old warmup backlog consumes actual holdout supply through the original FIFO,
but never becomes holdout demand in the fill denominator. Eventual holdout fill
counts only fulfilled obligations originally due in[56,84), through settlement.
Report warmup service separately; it cannot inflate achieved holdout service.

For complete holdout protection targets (origins56,63,70), report coverage and
q90/q95 pinball loss. Exclude origin77 since L+R ends outside the holdout. Coverage
is actual cumulative sales <= origin protection target; it is distinct from
immediate fill and cycle service. Report micro and macro item fill, units/origin/
cycle denominators, null zero-demand items, nominal-target item pass counts and
paired safety-off effects. Four cycles per item make cycle estimates coarse.

## Evidence boundary

Source archive/adapter/subset/parent-report/config/code hashes accompany public
aggregates by the already frozen training segment and overall. Raw/item series,
calibration residuals, review forecasts and trajectories remain local/ignored.
The local receipt retains all input/trajectory hashes, exact state at holdout
boundary, service receipts and acquisition/exposure/settlement breakdowns. Never
publish reconstructable real item traces or import them into operational schemas.

Independent tests must verify quantile ranks, clipped safety, exact pinball,
warmup carryover, holdout FIFO denominator, full paid costs/common closure,
training-only subset identity and future-observation isolation. Archive audits
reconcile local arms into public aggregates. No model/policy is promoted here.
