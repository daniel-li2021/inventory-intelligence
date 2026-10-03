# Fresh warmup and achieved-service results

Measured 2026-10-03 under Python 3.12.14, using
[fresh-warmup-v1](RESEARCH_WARMUP_V1.md). Reproduce from the repository root:

```sh
PYTHONPATH=src python3.12 -m scripts.warmup_benchmark --output output/fresh-warmup-v1.json
PYTHONPATH=src python3.12 -m unittest tests.test_research_warmup tests.test_decision tests.test_intermittent tests.test_decision_diagnostics -q
```

[Exact artifact](review/fresh-warmup-v1.json) contains inputs, independent
supplier namespaces, dependencies, state/cost partitions, exact review evidence
and trajectory hashes. The 44 focused tests passed using the existing Python
3.12.14 / Psycopg 3.3.6 validation environment. No database, external API or
production input was used. A separate archive acceptance checked all dependency
hashes, all 360 cost partitions and settled terminal states, and equality of
cold/warm forecasts and safety at every paired scored review.

## What changed in the evidence

There are 24 family/seed labels but only 18 distinct generated demand paths:
constant, weekly and zero repeat deterministic controls across the three seeds.
72 separately seeded supplier paths cover three origin blocks per label.
Five candidate policies produce 360 cold/warm pairs (720 arm simulations).
Origin blocks overlap warmup periods and repeat each demand path; these are not
360 independent replications. Two later blocks are evaluation-only; this study
does not select or promote a method.

Warmup improved score-period immediate fill in 70/360 pairs and regressed it
in 35/360; 180 were equal and 75 had undefined fill because score demand was
zero. Thus among 285 defined pairs, 70 improved and 35 regressed. Constant
controls account for 15 regressions and weekly for eight: a pre-existing pipeline
and periodic timing can make the warm state worse than a cold ten-piece reset.
Warmup is not a universal service improvement.

Only 2/360 pairs had lower **full intervention cost**, including initial stock,
all warmup/score/runoff procurement, holding, backlog, setup and common-calendar
terminal holding. They were seasonal-naive/fixed0 on lumpy/1709 selection
(warm-minus-cold -238) and pause/2027 holdout (-844). One is a selection-period
observation; neither establishes a general business saving. Other arms can
improve score service while paying more to create and operate the warm state.
Cold is inactive before score start, so this full-cost difference includes the
extra operating period; it is not an equal-duration steady-state cost estimate.

An independent small oracle makes that distinction explicit: with demand2/day,
L1/R1 and zero starting stock, two warmup days produce score fill1 versus cold
fill1/2 and score operating cost4 versus24. Complete intervention costs are
52 versus40 after procurement/warmup/settlement. The state entering scoring has
pipeline2, which arrives naturally; it was neither inserted nor given free.

## Nominal quantile is not achieved inventory service

For each q90/q95 policy and arm, the two evaluation blocks contain 48 trials;
36 have positive score demand and 12 have undefined unit fill. All 48 have
eight complete cycles and seven complete nine-day forecast targets.

- TSB/q90: cold meets nominal fill in 25/36 positive-demand trials; warm in
  26/36. Nominal cycle service is reached in 32/48 cold and 34/48 warm trials.
  Target coverage reaches q90 in 37/48 for both arms.
- TSB/q95: cold meets nominal fill in 26/36; warm in 27/36. Nominal cycle
  service is reached in 37/48 cold and 39/48 warm trials. Target coverage
  reaches q95 in 43/48 for both arms.

Target coverage is identical between arms because forecasting/calibration
information is identical. Inventory service differs because physical state
differs. These coverage denominators include zero-demand controls, whereas fill
denominators do not. Expanding calibration has 31–42 completed residual samples
at the reported evaluation origins; q90 and q95 use different ranks here, but
that does not establish either service guarantee. Exact pinball losses,
calibration counts/ranks and per-trial nominal gaps remain in the artifact.

## Next decision

The result supports continuing retention and supply-timing research, not adding
new forecasting models. Fresh independent traces and costed carryover now exist;
the remaining question is how a safety policy should adapt to permanent decline
while preserving recovery after a pause or seasonal low. Freeze those challengers
and new seed namespaces before evaluating them. These published traces are
consumed evidence, retained for regressions only.
