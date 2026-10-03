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
service claim. Results will be recorded after the frozen experiment runs.
