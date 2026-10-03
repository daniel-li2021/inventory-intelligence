# Fixed forecasts, different ordering rules

[Frozen protocol](POLICY_COMPARISON_V1.md),
[exact retained inputs, trajectories and costs](review/policy-comparison-v1.json).
Ten labels contain nine distinct demand paths; 40 forecast/safety cells yield
120 logical arms, 65 distinct physical day trajectories and 80 paired contrasts.
These are finite synthetic cases, not independent statistical trials.

| Rule vs periodic order-up-to | Fill improves | Fill regresses | Equal | Undefined | Full cost lower / higher / equal |
|---|---:|---:|---:|---:|---:|
| periodic `(s,S)` | 0 | 34 | 2 | 4 | 2 / 32 / 6 |
| prefix arithmetic | 4 | 0 | 32 | 4 | 4 / 0 / 36 |

The four positive prefix cells are **one known-late-inbound control**, repeated
across two forecasts and two safety settings. All other cells have identical
physical outcomes to order-up-to. This isolates timing rather than establishing
a general winning policy. No hidden-delay outcomes or operational reliability
gates are claimed by this adapter.

For the constant-three-per-day control with 80 pieces arriving day 12 and an
8-piece commitment due day 4, initial stock is 10. With safety zero, both mean
and seasonal forecasts give identical results:

| Rule | Immediate new fill | On-time prior fill | Cycle service | Backlog piece-days | Paid full cost |
|---|---:|---:|---:|---:|---:|
| periodic order-up-to | 71/84 | 0 | 3/4 | 190 | 2974 |
| periodic `(s,S)` | 25/42 | 0 | 1/8 | 322 | 4340 |
| prefix arithmetic | 1 | 1 | 1 | 0 | 1752 |

Aggregate inventory position counts the later supply before it can satisfy early
obligations. Prefix projection can buy enough timely supply to avoid that gap.
The full cost reduction is 1222 synthetic cost units, including acquisition of
all initial, inbound and ordered pieces, all holding/backlog and setup charges,
and the same nine-day settlement. Safety four also improves this control but
retains more stock: prefix cost 2012 vs reference 3150. There is no free inventory
or residual-stock credit.

The threshold rule suppresses some early replenishment at the fixed seven-day
review calendar. It has lower full cost in only 2/40 cells, and neither preserves
both fill and cycle service. It should not be adopted from this study. A different
review calendar, threshold or economic objective would require a fresh protocol.

## Verification and reproduction

Focused acceptance: **61 tests pass** on Python 3.12.14 / Psycopg 3.3.6. No
database, network, model API or operational pipeline was run for this study.

```sh
PYTHONPATH=src python3 scripts/policy_benchmark.py --output /tmp/policy-comparison-v1.json
PYTHONPATH=src python3 -m unittest tests.test_policy_comparison tests.test_decision tests.test_decision_benchmark tests.test_decision_diagnostics tests.test_lab tests.test_lab_api -q
```

Validation uses independent hand-calculated first orders, early fill, carryover
identity/due dates, pack/MOQ rounding, paid stock and settlement. The saved audit
reconciles source/input/trajectory hashes, forecast equality across policies,
piece conservation, every arm's costs and paired cost differences. Complete
default simulator outputs are compared with the attested original kernel, also
covering hidden delay, exact costs and prior FIFO. Historical benchmark results
retain their original source bytes and are not regenerated for a private hook.

Remaining work: independent costed warm states, hidden-delay-compatible planning
inputs, actual operational planner execution gates, and public observed-sales
inventory proxies. Each has a different evidence boundary; this result promotes
no production model or policy and establishes no service guarantee.
