# Intermittent decision research — v1

Assigned 2026-10-02 as the next part of the investigation. Frozen identifier
`intermittent-research-v1`. Synthetic offline research only. Planning-v1's
`METHODS`, PostgreSQL interfaces and Copilot decoding remain unchanged. No
automatic champion, public-data import or execution of orders.

## Algorithms and interfaces

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
mean pinball loss against the integer policy target sum(forecast)+safety;
loss=max(q*(actual-target),(q-1)*(actual-target)). This evaluates the actual
rounded policy target, not an unrounded distribution claim. Report target
coverage separately from achieved inventory service. Supplier delay uncertainty
stays paired/hidden; H remains nominal L+R and is not claimed delay-adjusted.

## Predeclared new experiment

Old decision-v1 holdouts are regression evidence only. New seeds 101/211/307,
224 days (112 train,56 selection,56 holdout). Fixed stock10,L2,R7,phase0,
pack2,MOQ4 and no prior commitments/inbound. Frozen families:

- constant: daily 3; weekly: repeat [0,1,2,3,4,5,6]; zero: all zero.
- intermittent: each day a fresh uniform draw; positive iff draw<3/20, then
  independently choose size from [1,2,3].
- lumpy: positive iff draw<1/5, size from [3,8,20].
- declining occurrence: p=max(1/20,2/5-i/640), size from [3,8,20].
- obsolescence: p=2/5 for i<112, 1/5 for 112<=i<182, then zero; same sizes.

Use Random(seed) for demand, with draw `randrange(10000)/10000` compared as an
exact Fraction and a size draw only on positives. No holdout-based exclusions.
Controls repeat across seeds and are not independent replications. Hidden
delay trace uses Random(seed+2000), draws from [0,1,2] by absolute review slot;
fixed delay is zero. Each split has ten scored-plus-runoff slots for these
parameters. Cost regimes remain (h,b,K)=(1,10,2)/(3,2,5).

Model grid in tie order: naive,mean,seasonal_naive,zero; Croston alpha1/5;
SBA alpha1/5 then1/2; TSB (alpha,beta)=(1/5,1/5),(1/5,1/2),(1/2,1/5),(1/2,1/2).
Each pairs safety in order fixed0, empirical9/10, empirical19/20: 33 candidates.
84 scenario/cost/delay cells; 5,544 candidate/split runs maximum. Parameters
are selected only by selection outcomes, not tuned on holdout. Histories and
stock reset at splits as in decision-v1; completed holdout observations may
update current estimates/calibration but cannot change the chosen configuration.

Select lowest total cost among candidates meeting immediate fill>=9/10 and
cycle service>=4/5; tie in the frozen order. No eligible candidate means no
selection. Report held-out promotion against both fixed mean/zero safety and
the selection-chosen existing baseline (same safety grid), requiring >=5% lower
cost, service floors and no fill/cycle regression. Also report a selected new
method only versus the selection-chosen baseline, without automatic promotion.
Report family/regime cells and clean/zero controls; no pooled/global champion
claim and no confidence claim from these three synthetic seeds.

Artifact stores complete inputs/digests, protocol/source versions/hashes, every
candidate's metrics/terminal and selected configs/comparisons. Per-review full
forecasts/calibration evidence need only be retained for selected and reference
configs; all others are reproducible from frozen inputs. Reuse forecast fits,
calibration results and fixed-policy simulations across identical input keys;
do not repeat identical work merely to relabel a control.

## Acceptance and handoff

Independent manual oracles: leading/all-zero, first positive and inter-arrival
updates, trailing-zero Croston/SBA versus TSB decay, rational/large quantities,
parameter validation, known cumulative quantile ranks/sign/ceiling, insufficient
calibration, no future observations/labels, rounded target coverage/pinball and
research wrapper conservation/timing. Reuse existing decision tests. Compare
the original v1 artifact's semantic scenarios against a current-kernel run;
only source provenance hashes may change. No broad database suite is required.

Runtime agent owns intermittent.py and the minimal private decision-kernel
extension. Oracle agent owns tests/test_intermittent.py. Evaluation agent owns
scripts/intermittent_benchmark.py, docs/INTERMITTENT_BENCHMARK.md and its result
artifact. Coordinator owns this contract, cross-harness tests, legacy evidence
compatibility and root/checkpoint/research documentation. Use isolated worktrees
from the frozen-contract commit; agents do not edit existing frozen contracts.
