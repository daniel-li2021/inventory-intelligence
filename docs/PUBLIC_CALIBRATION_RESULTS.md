# Disjoint-item quantile/service replication

The [protocol](PUBLIC_CALIBRATION_V1.md), implementation and
[public subset/grid freeze](review/public-calibration-freeze-v1.json) were
committed at `6b76a2a4fad4b1e279582c69f2586df56ea7c6cb` before the first new-item
simulation. Seed 1709 selects 32 training-known items after excluding all 32
items from the parent seed-701 study; overlap is zero. Selection accesses only
the prefix before 2011-09-16. Raw source/workbook/extraction caches are reused.

This is **prospective disjoint-item evidence**, with a design informed by prior
results. It uses the same retailer/calendar and correlated products, not a new
retailer, later-time validation, statistical independence or external sealed
custody. These outcomes are now consumed; any outcome-driven revision needs a
new protocol and new evaluation evidence.

## Exact population and accounting

The remaining training-known pool contains 3,806 items. The selected bins are
7 dense/high-volume, 6 medium/high, 6 medium/low, 6 sparse/high, 6 sparse/low and
one zero-training item. Bin volume median is recomputed on this eligible pool.
No warmup/holdout volumes enter selection.

Mean/SBA × off/q90/q95 × lead 2/5 × extra delay 0/3 gives 768 continuous arms and
512 same-item safety-off contrasts. Each starts at zero, pays for 56 warmup
days, retains its own stock/backlog/pipeline, scores 28 days, then pays a common
15-day settlement. Acquisition, holding, backlog and setup rates are the same
synthetic 2/1/10/2 units as the parent protocol.

Every configuration scores 6,207 modeled new-demand units, 896 item-days,
128 complete cycles and 96 complete protection targets. There are 25 positive-
holdout items and seven undefined-fill items; the latter are retained, not
converted to 100% or dropped from cycle/coverage denominators. Only one is in
the zero-training bin. Origin 77's incomplete target remains excluded.
Public observations do not establish actual availability or unconstrained demand;
suppliers, costs and backlog obligations are synthetic.

## Nominal target does not guarantee service

| Forecast / safety | Lead / extra delay | Immediate fill | Cycle service | Target coverage | Paid full synthetic cost |
|---|---|---:|---:|---:|---:|
| mean / off | 2 / 0 | 42.66% | 57.03% | 65.62% | 598500 |
| mean / q90 | 2 / 0 | 78.20% | 80.47% | 85.42% | 498936 |
| mean / q95 | 2 / 0 | 92.12% | 85.94% | 92.71% | 583573 |
| mean / q95 | 2 / 3 | 76.74% | 83.59% | 92.71% | 680633 |
| SBA / off | 2 / 0 | 73.50% | 62.50% | 76.04% | 621626 |
| SBA / q90 | 2 / 0 | 88.48% | 86.72% | 92.71% | 641501 |
| SBA / q95 | 2 / 0 | 93.35% | 89.84% | 95.83% | 746784 |
| SBA / q95 | 2 / 3 | 84.21% | 85.94% | 95.83% | 806355 |

Mean/q95/L2/no extra delay has fill 5718/6207, cycle service 110/128 and target
coverage 89/96. Only 15/25 positive-demand items reach 95% fill; 22/32 reach
95% cycle service and 26/32 reach 95% coverage. Protection-target pinball loss
is 18641/1920.

SBA/q95/L2/no extra delay has fill 5794/6207, cycle service 115/128 and coverage
92/96. Its coverage exceeds 95% in aggregate, while actual fill and cycle service
do not. Only 18/25 positive-demand items meet the fill target, 23/32 cycle service
and 28/32 coverage. Pinball loss is 2021/192.

The parent consumed-item study's SBA/q95 fill was 97.68%, with cycle service
94.53%. Here those are 93.35% and 89.84%. This is descriptive evidence of
cross-item variation; different item mix/volume prevents a causal difference or
population confidence claim. It does not select a model or safety level.
[Parent results](PUBLIC_SAFETY_RESULTS.md).

Extra hidden delay leaves every paired forecast/calibration target unchanged
but reduces mean/q95 fill to 4763/6207 and SBA/q95 to 5227/6207. With lead five,
q95/no delay fill is 79.76% for mean and 89.46% for SBA; extra delay reduces
those to 60.71% and 76.48%. Demand-target coverage measures a declared modeled
protection period, not actual inventory availability under hidden delay.

## Service and paid stock stay coupled

Across 512 safety-on contrasts, fill improves in 310, equals the off reference
in 90 and is undefined in 112; none regress on this fixed grid. In 223 contrasts
full cost is lower without fill/cycle regression. Correlated finite cases do
not establish a universal monotonic rule or an adoptable optimal policy.

For SBA/L2/no extra delay, q95 improves service but raises full cost from 621626
to 746784 (+125158). Mean/q95 costs 583573 versus 598500 off, but mean/q90 costs
498936 with lower service. No policy is chosen from these outcomes, and the
different subsets' aggregate costs are not directly comparable.

Mean/q95/L2/no delay pays warmup 349265, holdout 163000 and settlement 71308,
totaling 583573. Its score-boundary state is stock 3289/backlog 452; terminal
paid stock is 4708. SBA/q95's corresponding costs are 435180/213132/98472,
totaling 746784, with boundary stock 4777/backlog 124 and terminal stock 6516.
Historical warmup obligations consume later supply through FIFO; they are not
added to the 6207 new-demand holdout denominator or cleared for free.

## Acceptance and reproducibility

29 focused tests pass on Python 3.12.14 / Psycopg 3.3.6. Five new training/grid/
metadata controls cover future-access rejection, disjoint identities, exact
training features, incomplete pools and semantic receipt fields. Inherited
independent timing/cost/FIFO/rank/null controls and six rehashed arm mutations
remain accepted. These package counts are not unique additional tests to sum
with earlier studies.

The natural cached audit verifies all new 768 arms / 512 pairs, observation/
subset/source identity, timed receipts, FIFO/conservation, complete calibration
labels/ranks, paid costs, target/service/null denominators and every public
aggregate with **zero forecast refits or simulation replays**. The original
768-arm parent cache also passes its unchanged auditor. Re-running the new
score command with simulation explicitly disabled proves a byte-identical cache
hit. [Acceptance receipt](review/public-calibration-acceptance.json).

The new local detailed cache is 58,220,312 bytes; the aggregate public report is
488,745 bytes. Item identities, series and trajectories remain ignored/local.
Exact fractions use signed hexadecimal numerator/denominator strings, decoded
with the parent `decode` helper. All outcomes are retained in the
[aggregate artifact](review/public-calibration-v1.json), including every bin,
configuration, paid cost period and null denominator.

```sh
PYTHONPATH=src python3.12 -m scripts.public_calibration_benchmark audit
PYTHONPATH=src python3.12 -m scripts.public_calibration_benchmark score
```

Scoring reuses the cache when pinned sources/protocol/subset match; changed
sources fail closed. No archive download, workbook parse, database, model API,
new dependency, operational promotion or deployment was needed. Main integration
remains pending owner approval. Next ready work is the separately versioned
lost-sales protocol and synthetic physical-count/provenance boundary; advanced
models still require independent forecast weakness, not these service results.
