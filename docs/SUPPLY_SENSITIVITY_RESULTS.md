# Supply/review sensitivity and signed shortage attribution

Measured 2026-10-03 under Python 3.12.14, using
[supply-sensitivity-v1](SUPPLY_SENSITIVITY_V1.md).
[Exact artifact](review/supply-sensitivity-v1.json) retains nine family/seed
labels, seven distinct demand paths, 13 interventions and three forecast/safety
configurations: 351 cold/warm pairs, 702 logical arms, 666 physical arm computations
after reusing identical constant/low-delay inputs. All arms settle over the same
score-end plus 21-day calendar tail.

```sh
PYTHONPATH=src python3.12 -m scripts.supply_sensitivity_benchmark --output output/supply-sensitivity-v1.json
PYTHONPATH=src python3.12 -m unittest tests.test_research_warmup tests.test_safety_retention tests.test_supply_sensitivity tests.test_decision tests.test_intermittent tests.test_decision_diagnostics -q
```

The combined 57 focused tests pass. Archive acceptance separately verifies
dependency hashes, all 702 full-cost partitions, terminal obligations and the
common settlement tail. Five new independent supply oracles check equal expected
delay, variability, exact paid-stock/common-window costs, one-factor controls,
signed/null effects and fresh namespaces.

## Forecast versus supplier variability

At leads 2/5/10 and both start arms, nine path labels produce 54 comparisons.
Low versus high variability improves mean/fixed0 fill in 13/54. Changing mean
to TSB with the same fixed zero safety at medium variability improves fill in
18/54. In 10/54 comparisons, the positive variability-reduction fill gain exceeds
the positive TSB forecast gain (a nonpositive TSB gain is treated as zero only
for this explicit descriptive comparison). These counts repeat controls and
share underlying paths; they do not establish population probabilities or that
one intervention is universally more valuable.

All supplier distributions have expected delay 1. Realized delays differ: the
reference lumpy/5301's cold medium reviews average 1 day, high averages 3/4.
Equal expectation is a design control, not proof of equal sample-average delay.
Raw shocks and actual slot means/maxima are retained. The q90 TSB arm is reported
separately; comparing it with mean/fixed0 changes both safety and forecast, so it
cannot isolate forecast quality.

## A concrete root-cause intervention

Lumpy/5301 has 166 scored units. Under cold mean/fixed0, lead5/medium/R7/stock10/
pack2/MOQ4 misses 82 units: zero are independently startup-unavoidable and all
82 occur at/after the earliest possible receipt. Complete cost is 7002.

- Starting with zero stock produces 92 misses: ten startup-unavoidable and the
  same 82 later misses. Complete cost rises to 7338.
- Starting with 40 stock still misses 82, with zero startup-unavoidable, and costs
  7250. Additional paid stock does not solve the later timing/policy failure.
- Review every day produces 126 misses and costs 5666. The shorter review also
  changes protection horizon and calibration; lower cost sacrifices service.
- Pack1/MOQ1 produces 85 misses and costs 7193. Removing rounding constraints
  does not improve this path: larger rounded orders sometimes supported later fill.
- Lead10/medium produces 92 misses, with 16 startup-unavoidable and 76 later;
  lead2/medium produces 86, all later. Shorter lead also shortens this policy's
  forecast protection horizon; a universal service improvement is unproven.
- Low/high supplier variability at lead5 both miss 82, but full costs are
  6670/7404. Equal service does not imply equal backlog/stock cost exposure.

These are signed paired effects and a separately computed startup bound. They
are **not** an additive partition assigning 82 missed units to mutually exclusive
causes: supply, review, packs, state and policy interact. Later misses remain
policy/model-sensitive; no residual is relabeled as pure forecast error.

## Decision and continuation

Supply and policy timing materially change service/cost, but neither faster
reviews nor more stock guarantees better outcomes under this periodic policy.
Next prioritize the public observed-sales adapter/benchmark and a small explicit
policy comparison. No advanced forecast or operational policy is promoted.
These traces are now consumed evaluation/regression evidence.
