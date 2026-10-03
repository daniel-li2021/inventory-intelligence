# Intermittent decision research

Protocol `intermittent-research-v1` is frozen before scoring, following
[CONTRACT_INTERMITTENT_V1.md](CONTRACT_INTERMITTENT_V1.md). This is a new synthetic
experiment; old holdouts supply regression evidence only. No production method
or database contract changes.

## Frozen recipe

For seeds 101, 211 and 307, use a fresh `Random(seed)` per family. Generate 224
whole-piece observations: 112 training, 56 selection, 56 fresh holdout.
Constant is daily 3; weekly repeats `[0,1,2,3,4,5,6]`; zero is all zero.
For each stochastic family/day, draw `Fraction(rng.randrange(10000),10000)`;
draw a size independently only when that draw is below the day's probability.
Intermittent uses p=3/20 and sizes `[1,2,3]`; lumpy uses p=1/5 and
`[3,8,20]`; declining uses `max(1/20,2/5-i/640)` with those larger sizes;
obsolescence uses p=2/5 before day112, p=1/5 for days112..181 and zero thereafter.
No cases are excluded using observed outcomes. Deterministic controls repeat
across seeds; these are not independent replications.

At each split all candidates reset to stock10,L2,R7,phase0,pack2,MOQ4, empty
prior commitments and inbound. Selection observes only the 112 training days;
holdout starts with training plus selection history. Within each split, reviews
may observe only completed days. Ten absolute review-slot delays are either all
zero or drawn from `[0,1,2]` using a fresh `Random(seed+2000)`. The same hidden
trace is paired across candidates and splits. Cost regimes are exactly
`(h,b,K)=(1,10,2)` and `(3,2,5)`.

Model tie order is naive,mean,seasonal naive,zero,Croston alpha1/5,SBA alpha1/5,
SBA alpha1/2,TSB (alpha,beta)=(1/5,1/5),(1/5,1/2),(1/2,1/5),(1/2,1/2).
For each model, safety tie order is fixed0,empirical9/10,empirical19/20.
The 33 configurations cover 84 paired family/seed/cost/delay cells and at most
5,544 candidate/split results. Empirical safety requires at least eight complete
non-overlapping nine-day calibration targets starting at origin28, then37,...;
quantiles, initialization and exact update equations are the frozen contract's
choices, not fitted on these holdouts.

Simulation trajectories do not depend on cost labels: the fixed policy does not
optimize or read costs. Run each unique history/demand/delay/configuration once
at unit h/b/K, then calculate both cost regimes from scored/runoff piece-day and
positive-order exposures. Cache keys contain all actual physical/model inputs,
not family or seed labels. Repeated controls reuse identical simulations. The
runtime memoizes exact prefix forecasts and calibration evidence across safety
and cost comparisons. No cached results cross an input or code-version change.

## Selection, references and rejection

All choices use selection costs only among methods with immediate fill>=9/10
and cycle service>=4/5. Null service fails. Break cost ties in the declared grid
order. Record the eligible overall winner, existing-baseline winner (including
zero and the same three safety choices), and new-method winner separately;
none means no eligible selection in that subset. Holdout cannot reselect any.

Compare the overall selection against fixed mean/fixed0 and against the
selection-chosen existing baseline. Also compare the selection-chosen new
method against that baseline. A comparison passes only with at least 5% lower
held-out total cost, both service floors and no immediate-fill/cycle regression
against that reference. A missing selection/reference or null service fails.
A zero-cost reference cannot prove a relative reduction. Report failures per
cell/family/regime; there is no pooled/global champion decision.

Coverage of rounded protection targets and empirical pinball loss are reported
separately from achieved fill/cycle service. Nominal H=9 does not incorporate
supplier delay uncertainty. Calibration's empirical quantiles are not guarantees.

## Run and artifact

```sh
PYTHONPATH=src python3 scripts/intermittent_benchmark.py --output docs/review/intermittent-benchmark.json
```

The deterministic CLI uses no database, network, LLM, public dataset or new
dependency. It runs small independent assert checks first. On failure it retains
the prior artifact. Compact JSON stores exact numerator/denominator rationals,
source hashes, every complete input and digest, all configuration metrics and
terminal states, and frozen selection/comparison results. Full review forecasts
and calibration evidence are retained only for selected configurations and
references; other reviews can be reproduced from the complete inputs. No
per-day archive is stored. Counts distinguish logical evaluations from unique
physical simulations and cache hits.

Synthetic finite-window penalties omit acquisition, salvage and lost-sales value
and cannot establish profit or business savings. Three random seeds, repeated
controls and correlated cycles support no population confidence or calibrated
service claim.

## Recorded findings

The recorded run used local Python 3.11.6; the repository's declared supported
runtime is Python >=3.12. This interpreter difference is recorded explicitly;
the artifact's full integer paths and exact arithmetic remain reproducible.
The frozen run produced all 5,544 candidate/split results in 84 cells. Cost
repricing and identical-input caching required 2,376 physical simulations,
reusing 3,168 results. All terminal backlog and outstanding quantities settled
to zero. Eighteen cells had no eligible overall selection: all twelve zero
controls and six constant/hidden-delay cells.

| Family (12 cells each) | Overall passes both references | Selected new method passes chosen baseline |
| --- | ---: | ---: |
| Constant | 0 | 0 |
| Weekly | 0 | 0 |
| Zero | 0 | 0 |
| Intermittent | 0 | 2 |
| Lumpy | 0 | 0 |
| Declining occurrence | 4 | 8 |
| Obsolescence | 0 | 0 |

The four dual-reference passes are **one demand path**, declining/seed101,
repeated across two cost regimes and two delay regimes. Its selection-chosen
TSB alpha=beta=1/5 with fixed zero safety passed against fixed mean and the
selection-chosen baseline. These paired cells are not four independent wins.
The ten new-versus-baseline passes also include declining/seed307 SBA alpha1/2
with q19/20 (four cells) and intermittent/seed101 hidden-delay SBA alpha1/5 with
q19/20 (two cells). Those latter configurations were chosen within the new-method
subset during selection; holdout never replaces the overall selection.

Examples below use `(h,b,K)=(1,10,2)`. Costs include runoff; coverage is the
fraction of seven complete nine-day targets covered by the rounded policy
target, distinct from scored-day service.

| Case / selection-chosen configuration | Holdout cost | Immediate fill | Cycle service | Target coverage |
| --- | ---: | ---: | ---: | ---: |
| Declining101, fixed / TSB a1/5,b1/5,fixed0 | 793 | 1 | 1 | 6/7 |
| Declining101, fixed / baseline mean,fixed0 | 1341 | 1 | 1 | 1 |
| Intermittent101, hidden / new SBA a1/5,q19/20 | 461 | 1 | 1 | 1 |
| Intermittent101, hidden / baseline seasonal naive,q9/10 | 489 | 1 | 1 | 1 |
| Lumpy101, fixed / new SBA a1/5,q9/10 | 3307 | 75/116 | 3/4 | 6/7 |
| Lumpy101, fixed / baseline naive,q9/10 | 5501 | 75/116 | 3/4 | 6/7 |
| Declining211, fixed / TSB a1/5,b1/2,q9/10 | 2302 | 29/39 | 7/8 | 1 |
| Obsolescence307, fixed / TSB a1/5,b1/5,q9/10 | 3464 | 1 | 1 | 1 |
| Obsolescence307, fixed / baseline seasonal naive,q9/10 | 3340 | 1 | 1 | 1 |

SBA's lower lumpy example cost does not meet the service floors, so its
comparison fails. Six selected-new lumpy cells failed a holdout service floor;
eight failed the cost threshold, with overlap between reasons. No lumpy new
method passed against the selection-chosen baseline.

Declining/seed211 illustrates a structural failure under the frozen stock/timing:
holdout demand on day1 is 20, initial stock is 10 and the earliest new-order
receipt is day2. Ten units miss immediate fill before any replenishment can
arrive, limiting fill to at most 29/39 regardless of the forecast. Full target
coverage and a pinball loss of 102/35 for the selected TSB policy cannot repair
that service failure. Fixed stock and no warmup are part of this counterfactual,
not evidence that a forecast alone caused every shortage.

On obsolescence/seed307, empirical TSB safety across holdout reviews was
23,40,40,40,40,40,23,23 despite only eight held-out demand units and permanent
zero demand after absolute day181. It ended with 54 pieces; its cost exceeded
both the chosen baseline's 3340 and fixed mean's 1870. Decaying point forecasts
do not necessarily remove historically calibrated safety inventory. All twelve
selected-new obsolescence comparisons failed the cost-reduction requirement.

Weekly seasonal naive passed fixed mean in six fixed-delay cells but matched
the selected-baseline reference and therefore failed the dual-reference rule.
Constant methods tied under fixed delays; empirical demand calibration produced
no safety for deterministic constant demand and could not cover hidden delays.
Zero controls have null unit fill and cannot pass eligibility even with complete
shortage-free cycles. Initial-stock holding penalties remain present.

There is no consistent overall/new-method advantage across these families or
regimes. Empirical safety sometimes restores service at additional holding cost,
but is neither a calibrated service guarantee nor a general promotion basis.
No runtime champion changes follow these findings. ADIDA or LightGBM would not
remove a shortage before any receipt can occur. This run supports examining
initial-stock/lead-time feasibility and safety retention under demand decline
before expanding the model grid. Such changes need a new frozen counterfactual;
this holdout must not become a tuning set. Complete exact metrics, pinball loss,
failures and selected/reference calibration evidence are in
[the artifact](review/intermittent-benchmark.json).

## Integrated validation

Python 3.12.14 passed all 31 focused decision, forecast, intermittent and harness
tests. These include independent exact initialization/smoothing/calibration and
event/cost oracles, repricing and selection boundaries, source/input provenance,
completed-only calibration windows and terminal settlement. The retained demand
generation matches Python 3.12.14 for every seed/family. The 5,544 valid results
were reused rather than rerunning the experiment. A required compatibility run
confirmed every original decision-v1 scenario and result unchanged apart from
current source hashes after sharing the event kernel. No PostgreSQL or API run
was needed; existing operational methods and historical contracts are preserved.

```sh
PYTHONPATH=src python -m unittest tests.test_decision tests.test_decision_benchmark tests.test_forecasting tests.test_intermittent tests.test_intermittent_benchmark -v
```
