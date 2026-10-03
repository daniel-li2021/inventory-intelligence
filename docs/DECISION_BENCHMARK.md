# Offline decision benchmark

Frozen protocol `decision-benchmark-v1`, under
[CONTRACT_DECISION_V1.md](CONTRACT_DECISION_V1.md). The choices below are recorded
before executing simulations or inspecting scores. This experiment does not
change planning-v1 or select a production champion.

## Reproducible inputs

Each of seeds 11, 29 and 47 produces one 168-day series for each family. The
first 56 days train, the next 56 select and the final 56 score holdout. Constant,
weekly and zero controls intentionally repeat across seeds; these are controls,
not independent replications. Use Python's standard-library `random.Random` and
record every generated integer in the artifact so reproduction is independent
of future random-library changes.

- Constant: three pieces every day.
- Weekly: repeat `[0, 1, 2, 3, 4, 5, 6]`, starting with zero.
- Zero: zero pieces every day.
- Lumpy: independent daily draws from `[0, 0, 0, 0, 0, 2, 8, 16]` using the
  scenario seed. No smoothing, filtering or fitted parameters.
- Obsolescence: 56 days of four pieces, 28 days of two, 28 days of one, seven
  days of one, then 49 days of zero. This is one permanent demand decline;
  each seed repeats this deterministic control.

Selection history is exactly training; holdout history is exactly training plus
selection. Each simulated origin can observe only preceding history and
completed split days. Each candidate and split resets to stock 10, empty prior
commitments and inbound, L=2, R=7, phase=0, safety=0, pack=2 and MOQ=4.
Candidates follow `forecasting.METHODS` order, then the zero diagnostic.

Each scenario pairs both exact cost regimes `(h,b,K)=(1,10,2)` and `(3,2,5)`
with fixed zero delays and hidden delays drawn from `[0,1,2]` using a fresh
`Random(seed + 1000)`. Selection and holdout use the same declared delay trace;
it is shared across candidates, including zero-order slots. Each trace contains
exactly the simulator's scored-plus-runoff review slots. The fixed trace has ten
zeros (nine-day runoff). The hidden trace has enough slots for its declared
maximum (eleven-day runoff when the maximum is two). No policy reads the trace.

## Frozen selection and promotion

Eligible selection methods require immediate fill at least 9/10 and complete
cycle service at least 4/5. Null service fails eligibility. Select the lowest
selection **total** cost, including fixed runoff, breaking ties by candidate
order. No eligible candidate means no selection; holdout does not replace it.

The selected method is proposed for promotion only when its held-out total
cost is at most 95% of the unchanged mean reference, both service floors pass,
and neither service rate regresses against mean. A zero-cost reference cannot
demonstrate a 5% relative reduction and fails the cost test. All candidate
holdout results are stored for audit but never influence method selection.
No automatic champion change follows a pass.

## Run and audit

```sh
PYTHONPATH=src python3 scripts/decision_benchmark.py --output docs/review/decision-benchmark.json
```

The CLI uses no database, network, model API or new dependency. It runs small
assert-based checks for hashing, frozen selection, promotion and null controls
before simulating. Errors abort without replacing an existing report. JSON
rationals are exact numerator/denominator objects. The artifact stores protocol
and source hashes, complete scenario inputs and their SHA-256, selection and
holdout metrics/review forecasts/terminal state for every method, explicit
eligibility and paired holdout differences, and every failed promotion condition.

Historical source attestation is retained after the private ordering extension:
[original kernel bytes](review/decision-v1-source.py.txt), from main commit
`f6d3d16034af038eda4c8687ea4f1ed6d2445ef6`, match this report's recorded kernel
SHA-256. Other recorded sources are unchanged. The archive is source evidence,
not the runtime implementation. A regression oracle compares complete default
outputs against that original kernel, including hidden-delay/FIFO cases. Old
results were not regenerated to make their hashes match a newer implementation.

Synthetic penalties omit acquisition, salvage and lost-sales value. They are
finite-window costs, not profit or demonstrated business savings. Correlated
cycles, repeated controls and three lumpy seeds support no population confidence
or optimality claim.

## Recorded findings

The frozen experiment completed 480 candidate/split simulations across 60 paired
scenario/cost/delay cells. Every terminal backlog and outstanding quantity was
zero. Selection found no eligible method in 22 cells. Six weekly fixed-delay
cells and ten obsolescence cells passed the proposed-promotion rule; those 16
passes include deliberately repeated controls and are not 16 independent wins.

| Family | Selection methods across 12 cells | Proposed promotions |
| --- | --- | --- |
| Constant | naive 6; none 6 | 0 |
| Weekly | seasonal naive 6; mean 6 | 6 |
| Zero | none 12 | 0 |
| Lumpy | naive 8; none 4 | 0 |
| Obsolescence | naive 10; mean 2 | 10 |

For seed 11, fixed delays and `(h,b,K)=(1,10,2)`, the paired held-out results
are below. Cost includes scored days and runoff. Cumulative MAE measures complete
nine-day targets only. Fill and cycle rates are scoring-day metrics.

| Family/method | Total cost | Immediate fill | Cycle service | Cumulative MAE |
| --- | ---: | ---: | ---: | ---: |
| Weekly / mean | 834 | 1 | 1 | 5 |
| Weekly / selected seasonal naive | 526 | 1 | 1 | 0 |
| Obsolescence / mean | 1564 | 1 | 1 | 3564863/174097 |
| Obsolescence / selected naive | 554 | 1 | 1 | 11/7 |
| Lumpy / mean | 1122 | 77/83 | 1/2 | 76380277/9749432 |
| Lumpy / selected naive | 8336 | 6/83 | 0 | 164/7 |

All eight selected lumpy cells failed a held-out service floor. Seed 47 had no
eligible selection in any lumpy cell. The example shows why selection-period
eligibility does not establish holdout reliability; promotion remains rejected.
Hidden delays changed weekly selections from seasonal naive to mean, which
cannot demonstrate a reduction against itself. Constant baseline methods tied under
fixed delays and produced no reduction; delayed constant cells had no eligible
selection. The zero control has null unit fill, perfect shortage-free cycles,
and holding penalties on the initial ten pieces (650 in the example regime),
so it is neither a free inventory result nor a promotion.

These are exact findings about the declared synthetic cases. There is no
supported global champion, calibrated service guarantee, statistical confidence
or business-savings claim. Full rational scores and rejection reasons are in
[the reproducible artifact](review/decision-benchmark.json).

## Validation and next boundary

Integrated validation on Python 3.12.14 passed all 19 focused tests: ten
independent hand-calculated simulator oracles, three selection/promotion and
retained-evidence checks, and the six unchanged forecast tests. The final CLI
completed all 480 simulations; every source/input hash and terminal obligation
was checked. Run the same checks without a database:

```sh
PYTHONPATH=src python -m unittest tests.test_decision tests.test_decision_benchmark tests.test_forecasting -v
```

The lumpy selection/holdout failures justify a later bounded intermittent-method
experiment; they do not establish which challenger will help. This milestone
delivers the deterministic benchmark only. SBA/TSB, calibrated uncertainty,
lost-sales semantics and public-sales acquisition require their separate next
handoffs. Existing operational planning and historical decoding are unchanged;
their PostgreSQL acceptance was not rerun for these isolated offline additions.
