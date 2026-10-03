# Offline decision benchmark — v1

Frozen for the user-assigned next milestone on 2026-10-02, following
[the investigation](NEXT_ROUND_RESEARCH.md). Identifier `decision-benchmark-v1`.
This separate research contract leaves planning-v1, its methods, projections,
database schemas and historical Copilot decoding unchanged. Synthetic single-key
whole-piece demand only; no database, model API, real data or purchase execution.

## Inputs and public interface

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

## Events and policy

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

## Scoring and fixed runoff

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

## Bounded comparison and acceptance

`scripts/decision_benchmark.py` is a deterministic offline CLI with `--output`.
It compares the three existing baselines and zero diagnostic on constant, weekly,
all-zero, irregular/lumpy and obsolescence synthetic controls (declared seeds
11/29/47). Fixed 56-day training, 56-day selection, fresh 56-day holdout; R=7,
L=2, phase=0, stock=10, safety=0, pack=2, MOQ=4. Compare fixed lead and a shared
hidden 0/1/2-day delay trace under exact rates (h,b,K)=(1,10,2) and (3,2,5).
Data generation, parameters, costs and promotion rule are frozen before scores.
Histories in selection/holdout contain only earlier data; candidate stock resets
identically at each split. Holdout forecasts may update on completed holdout
days; method selection cannot. This is a new synthetic experiment, not new
real-world evidence. Store protocol/code version, full reproducible scenario
inputs and SHA-256, scores/terminal state for each candidate, and paired results.

Select candidate by lowest selection total cost among methods with immediate
fill >=9/10 and cycle service >=4/5, tie in METHODS order (zero last). If none,
return no selection. A proposed promotion requires held-out total cost at least
5% below the fixed mean reference AND those service floors AND no service-rate
regression versus mean. Report eligibility, differences and failures per
scenario/regime; no automatic champion change. Zero-demand null service does
not pass these floors; clean zero is reported as a control, not a promotion.
No confidence/population claim from correlated cycles or three synthetic seeds.

Independent hand-calculated tests cover clean/zero, early shortage, lead-time
timing, hidden delays, FIFO prior commitments, duplicate-order prevention,
pack/MOQ, rational costs, terminal obligations, cycle/service denominators,
cumulative forecast errors, invalid inputs and future-data leakage. Expected
values must not be obtained from simulator output.

## Parallel handoff for this milestone

Coordinator owns this contract, README, checkpoint, research status and review.
Simulator agent owns `src/inventory_intelligence/decision.py`; independent oracle
agent owns `tests/test_decision.py`; evaluation agent owns
`scripts/decision_benchmark.py`, `docs/DECISION_BENCHMARK.md` and
`docs/review/decision-benchmark.json`. Agents use separate temporary worktrees
from the contract commit and return focused commits for coordinator integration.
No shared contracts or existing runtime interfaces are edited by agents.
