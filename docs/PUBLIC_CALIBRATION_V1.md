# Prospective disjoint-item calibration replication v1

Assigned 2026-10-03 under the continuing research goal. This package depends on
PR #17's validated sales-proxy kernel and attested PR #15 public-data adapter.
It preserves all historical sources and outcomes; it does not alter operational
accepted-order demand, planner gates or purchase execution.

## Question and evidence boundary

Do the nominal q90/q95 demand targets translate into achieved coverage, immediate
fill and cycle service on a prospectively frozen, previously unscored item block?
This is a cross-item replication within the same retailer/calendar, informed by
the prior 32-item results. Items are disjoint, but dates/products are correlated.
It is not statistical independence, a new retailer, a later calendar or external
custodian-sealed evidence. New viewed outcomes become consumed immediately.

Reusing an already attested source archive is permitted. The new selector reads
only dates and quantities before 2011-09-16, not the new item's warmup/holdout
quantities. It reconstructs the original seed-701 subset from training-only
features and verifies its digest against the published parent before excluding
all 32 identities. A new seed 1709 selects exactly 32 remaining training-known
items using the same training sparsity/volume round-robin rule. The volume median
is recomputed on the remaining eligible pool, and a zero-training bin contributes
at most one item. Report eligible/selected bins, exclusion and overlap counts.
Missing/incomplete source or fewer than 32 eligible items fails closed.

Freeze the protocol, implementation/source hashes, exact candidate grid and
public subset hash/denominators in Git before scoring. Item identities and
features stay in the ignored local freeze; the manifest attests its complete
bytes. Refuse changed freeze/source/grid/parent/cache receipts rather than
reselecting, overwriting consumed evidence or silently rerunning a study.

## Fixed experiment

Use existing mean and SBA forecasts, safety off/q90/q95, lead 2/5, extra hidden
supplier delay 0/3: 24 configurations × 32 items = 768 arms, 512 safety-off pairs.
No model, quantile, threshold or item selection is based on the new outcomes.
No advanced-model promotion follows from this inventory study.

Calendar and accounting are unchanged from PUBLIC_SAFETY_V1: training ends
2011-09-16; start with zero stock, run 56 paid warmup days to 2011-11-11, continue
policy-owned stock/backlog/pipeline for 28 score days, exclude partial 2011-12-09,
and pay a common 15-day closure. Review every seven days, pack two/MOQ four.
Every acquired piece costs two; daily holding one, backlog ten, order setup two.
No free initial stock, liquidation credit, state reset or cross-arm inventory.
Demand-target horizon is modeled lead plus review (9/12), with expanding completed
nonoverlapping residuals, minimum training 28 and eight samples. Hidden realized
delay is not available to the forecasting/calibration policy.

Each item's holdout has four complete cycles and three complete protection
origins (56,63,70); origin77's target is incomplete and excluded. Report all 32
items, exact holdout units/896 item-days/128 cycles/96 targets; positive-demand
and undefined-fill item denominators remain separate. Pinball, coverage, fill,
cycle, purchased inventory, terminal stock and full warmup/score/settlement costs
are different outcomes. Compare each safety arm with its same-item off reference.
Between-subset results are descriptive; different item volumes preclude a causal
aggregate-cost comparison or pooling them as independent replications.

## Acceptance and reproduction

Training-access guard tests must prove selection never accesses future quantities;
independent feature/identity controls cover exclusions, insufficient data, median,
zero cap and reproducibility. Inherit existing independent simulation/accounting
and rehashed-mutation oracles without changing their original source files.
The cached auditor checks every new arm's timed receipts, FIFO/conservation,
paid costs, completed calibration ranks, null/service/coverage denominators and
public aggregates without forecast refits or simulation replay. Detailed item
receipts remain ignored/local; publish aggregate outcomes only.

```sh
PYTHONPATH=src python3.12 -m unittest tests.test_public_calibration tests.test_sales_safety tests.test_public_sales_benchmark tests.test_intermittent -q
PYTHONPATH=src python3.12 -m scripts.public_calibration_benchmark freeze
# Commit protocol/code/tests/public freeze before the next command.
PYTHONPATH=src python3.12 -m scripts.public_calibration_benchmark score
PYTHONPATH=src python3.12 -m scripts.public_calibration_benchmark audit
```

Freeze/output defaults are docs/review/public-calibration-freeze-v1.json and
public-calibration-v1.json. Acquisition is disabled unless separately assigned;
existing accepted caches are required. Any positive or negative result remains
observed-sales proxy evidence with unknown availability/unconstrained demand and
synthetic supply/cost assumptions. No service guarantee, retailer savings or
production readiness is claimed.
