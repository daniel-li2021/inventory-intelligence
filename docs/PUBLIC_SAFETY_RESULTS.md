# Nominal quantiles versus achieved sales-proxy service

[Protocol](PUBLIC_SAFETY_V1.md) was committed at `f0a6559` before the first
real-sales simulation. [Exact public aggregates](review/public-sales-safety-v1.json)
reference the same official archive, adapter and train-only subset as the
[parent forecast study](PUBLIC_SALES_RESULTS.md). This extends **consumed** public
observations; it is an exploratory counterfactual, not fresh sealed evidence.

32 items × 2 fixed forecasts × 3 safety settings × 2 leads × 2 synthetic supply
regimes = 768 continuous arms, 512 paired safety-off contrasts. Each arm starts at
zero, runs 56 fully paid warmup dates, retains its own stock/backlog/pipeline,
then scores 28 dates. Costs include all purchases, warmup and common 15-day closure.
Real stock availability, uncensored demand and actual supplier performance are
unknown. No observed sale is imported as an operational accepted order.

## q95 is not a service guarantee

Each configuration scores 15373 modeled holdout units over 896 item-days, 128
complete cycles and 96 complete protection targets. Thirty items have positive
holdout sales; two have undefined fill. Cycles/coverage include all 32 items.
Coverage uses three complete targets per item; final review at day 77 is excluded.

| Forecast / safety | Lead / extra delay | Immediate fill | Cycle service | Protection coverage | Paid full synthetic cost |
|---|---|---:|---:|---:|---:|
| mean / off | 2 / 0 | 46.93% | 43.75% | 55.21% | 1313288 |
| mean / q90 | 2 / 0 | 87.14% | 78.13% | 86.46% | 810811 |
| mean / q95 | 2 / 0 | 93.14% | 84.38% | 91.67% | 774988 |
| mean / q95 | 2 / 3 | 68.46% | 78.91% | 91.67% | 1048843 |
| SBA / off | 2 / 0 | 87.44% | 52.34% | 68.75% | 788483 |
| SBA / q90 | 2 / 0 | 96.18% | 85.94% | 92.71% | 758967 |
| SBA / q95 | 2 / 0 | 97.68% | 94.53% | 96.88% | 866644 |
| SBA / q95 | 2 / 3 | 86.63% | 87.50% | 96.88% | 964708 |

For mean/q95/L2/no delay, fill is14319/15373, cycle service108/128 and coverage
88/96. Only22/30 positive-sale items attain95% fill;20/32 attain95% cycle service,
and24/32 attain95% coverage. Protection-target pinball loss is791/64. The signed
empirical residual quantile has neither guaranteed its out-of-sample coverage
nor translated into a95% service floor.

For SBA/q95/L2/no delay, fill15016/15373 exceeds95% in aggregate, while cycle
service121/128 falls below95%.27/30 positive-sale items meet the fill target,
26/32 the cycle target,29/32 coverage. Its coverage93/96 and pinball12137/960
measure cumulative demand targets, a different outcome from actual availability.

An extra hidden three days leaves demand forecasts/calibration/coverage unchanged
at every paired origin but lowers actual fill. With L5/q95, no-delay fill is78.19%
for mean and94.54% for SBA; delayed fill is61.04% and83.47%. Demand-only calibration
does not absorb an incorrectly modeled protection period or supplier timing.

## Service and costs must be evaluated together

Across the512 safety-on contrasts, fill improves409, is equal71 and is undefined32;
none regress on this fixed grid.326 have lower paid full cost without fill/cycle
regression. These correlated cases do not establish a universal monotonic rule
or statistical confidence. Costs can rise even when service improves.

For SBA/L2/no delay, q95 raises full cost from788483 to866644 (+78161). In19/32
items cost rises,12 falls and one is equal. q90 costs758967 and has lower service
than q95. No safety policy is selected on these outcomes. Mean/q95's aggregate
cost reduction mostly comes from lower synthetic backlog penalties; it is not
retailer savings, and paid safety inventory remains at settlement.

Mean/q95/L2/no-delay costs split into warmup426618, holdout258032 and settlement
90338, totaling774988. The stock and backlog at the score boundary are actual
policy-owned carryover, not a reset: aggregate stock2148, backlog1395. Historical
warmup backlog consumes holdout supply through FIFO without entering the holdout
new-demand denominator. Every purchased piece is paid at order placement.

The parent forecast comparison favored mean for aggregate daily accuracy. SBA's
different results here illustrate the forecasting/decision objective distinction,
without establishing a winning method or overturning the conditional advanced-
model gate. There is no fresh independent evidence supporting model promotion.

## Validation and reproduction

31 focused tests pass on Python 3.12.14 / Psycopg 3.3.6. Independent cached acceptance
audits all 768 arms / 512 pairs without any model refit or simulation replay: raw
subset identity, source/input/trajectory hashes, timed receipts, FIFO identities,
piece/pipeline conservation, paid costs and closure, rank/safety, completed
calibration labels, score denominators, pinball and every public aggregate.
Six purposeful mutations with recomputed hashes are detected, including shifted
receipt, altered service/cost/coverage, wrong quantile rank and future labels.

```sh
PYTHONPATH=src python3.12 -m unittest tests.test_sales_safety tests.test_public_sales tests.test_public_sales_benchmark tests.test_intermittent -q
PYTHONPATH=src python3.12 -m scripts.public_safety_benchmark --output docs/review/public-sales-safety-v1.json
PYTHONPATH=src python3.12 -m scripts.public_safety_audit
```

The benchmark reuses a verified cache when its pinned code/protocol/input hashes
match. The auditor deliberately rejects changed current sources rather than
calling historical reports current. New code needs its own evidence receipt.
59MB local detailed evidence stays ignored; the492832-byte public artifact has
aggregate outcomes only, source attribution and the original acquisition receipt.
No raw download, workbook parse, operational pipeline, database or API was run
for this extension. No model or policy is promoted.

Next ready work: independent future/public labels for calibration generalization,
cross-layer evidence QA and local demo accessibility. Hosting requires its own
concrete deployment target and cost/ownership decision. Public sales remain an
external-realism proxy, while synthetic tests remain the stockout-semantic oracle.
