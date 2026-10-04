# Inventory Intelligence: trust the evidence before ordering stock

Inventory Intelligence is a Python/PostgreSQL portfolio system for finished
garments counted in whole pieces. It answers two connected questions: can the
inventory evidence be trusted, and what replenishment is defensible if it can?
It also tests whether a plausible forecast and ordering rule actually deliver
service when demand, starting state and supply timing change.

The operational core and local Decision Lab are implemented on main with
synthetic business data. Ten subsequent research/UX/readiness PRs are merged
through PR 24 at main `f132bf4` as of 2026-10-03, with a locally validated combined
acceptance and verified remote ancestry. PR 25 fixes full-history checkout;
the recorded `9d7c55f` CI run has [240 passing remote tests and green hygiene](https://github.com/daniel-li2021/inventory-intelligence/actions/runs/37164884160). Public
transaction research is a separate observed-sales boundary. There is no hosted
deployment, purchase execution, measured retailer saving or production claim.
[Current state and recorded acceptance](STATE.md), [exact claim receipt](review/portfolio-claims.json).

## Problem and architecture

A stock number is insufficient when movements are duplicated, snapshots refer
to different cutoffs, reservations are incomplete or inbound supply arrives
after an obligation. An accurate demand forecast can still lead to a bad order.
The system makes these evidence and timing dependencies explicit:

1. Reliability reconciles ledger and snapshot quantities at a common business
   cutoff, subject to what had arrived by the ingestion watermark. It records
   findings separately and preserves source identities and history.
2. Baseline forecasting uses only information available at the prediction
   origin. Planning requires trusted inventory and complete reservations/supply;
   missing or contradictory evidence yields `not_assessable` and null quantities.
3. The read-only Copilot explains persisted findings and calculations with
   evidence links. Deterministic code owns arithmetic and provenance; an optional
   language model routes bounded intent.
4. The local Decision Lab exposes synthetic scenarios and saved traces. A
   separate research simulator measures ordering decisions under declared
   demand/supply/cost protocols. Operational planning remains advisory.

[Core contract](CONTRACT_V1.md), [planning semantics](PLANNING.md),
[Lab walkthrough and commands](../README.md#try-the-decision-lab).

## Engineering decisions that make the conclusions reviewable

Exact integers and rational arithmetic preserve pieces, costs and denominators.
Business time and ingestion time prevent late evidence from becoming knowledge
at an earlier origin. Immutable run history, restricted database roles and
independent hand-calculated controls protect the operational boundary.

Research freezes inputs, candidate grids and evaluation rules before outcomes.
Starting inventory and every acquired piece are paid in the new costed studies;
warmup carries each policy's own stock, backlog and pipeline. Common settlement
ends keep unresolved obligations and residual stock visible. Repeated scenarios,
dependent origins and repriced trajectories are counted separately from distinct
paths. Viewed holdouts become consumed regression evidence.

Public-data engineering attests the official archive, extracted workbook,
adapter and subset. The complete 541,909-row UCI Online Retail extraction retains
531,285 positive non-cancelled rows, separately excludes 9,288 cancellation rows
and 1,336 other nonpositive rows, and diagnoses repeated invoice/item pairs
without silently deleting their quantities. Raw rows, reconstructable item
series and detailed item results stay in ignored local storage; Git contains
code, aggregate results, attribution and hashes.
[Adapter and source attribution](https://github.com/daniel-li2021/inventory-intelligence/blob/97d1f8a00a00cecdcd01368403bdfeab8b92d510/docs/PUBLIC_ADAPTER_V1.md).

## Failures discovered and measured outcomes

These are finite experiments with different protocols. Their costs and trial
counts must not be pooled into one performance score.

| Question | Measured evidence | Decision consequence |
|---|---|---|
| Does paying for a warm start solve weak service? | 360 paired comparisons / 720 arms over 18 distinct fresh synthetic demand paths: fill improves in 70, regresses in 35, is equal in 180 and undefined in 75; full cost is lower in only two. | Starting conditions explain some outcomes; warmup is not a general remedy. |
| Does shrinking stale safety solve declining demand? | 105 simulations / 17 distinct paths: recent-window and decay challengers each pass 0/21 descriptive cost/service gates. Safety reaches zero on cessation, but owned stock remains and pause-recovery service can regress. | A pause, seasonal low and permanent cessation need separate evaluation. |
| Is a nominal q95 target a 95% service guarantee? | Mean/q95, lead two, no extra delay: immediate fill 14,319/15,373 = 93.14%; cycle service 108/128 = 84.38%; target coverage 88/96 = 91.67%. | Calibration, availability and cycle service are distinct quantities. |
| Can supply timing dominate a calibrated demand target? | An extra synthetic three-day hidden delay lowers the same mean/q95 fill to 10,525/15,373 = 68.46%, while demand-target coverage remains 88/96. | Demand-only uncertainty does not correct an incorrectly modeled protection period. |
| Does higher service always lower cost? | SBA/q95 reaches 15,016/15,373 = 97.68% fill and 121/128 = 94.53% cycle service, but full synthetic cost increases from 788,483 to 866,644 versus safety off. | Service and acquisition/holding/backlog/setup economics require joint evaluation. |
| Does a selected forecast mix beat a simple fixed reference? | On the 32-item public subset at horizon 28, cumulative MAE is 247.8501 for fixed mean versus 443.6063 for the frozen selected mix; 32 origins / 896 points / 15,373 observed units. | This experiment does not justify adding an advanced model. |
| Can policy timing matter with identical forecasts? | 120 logical arms / 65 distinct physical trajectories. Prefix projection improves four cells representing one repeated late-inbound control; the periodic `(s,S)` rule regresses fill in 34/40 cells. | Counting late supply in aggregate inventory position can hide an early obligation gap. |

Sources: [fresh warmup](https://github.com/daniel-li2021/inventory-intelligence/blob/d2cb98ba1016f80bd2c2dd40159092f4f1b21395/docs/FRESH_WARMUP_RESULTS.md),
[retention](https://github.com/daniel-li2021/inventory-intelligence/blob/d2cb98ba1016f80bd2c2dd40159092f4f1b21395/docs/SAFETY_RETENTION_RESULTS.md),
[sales-proxy safety/service](https://github.com/daniel-li2021/inventory-intelligence/blob/706fa82c7520f5119ffd85b8c6a2a65f40fc2f10/docs/PUBLIC_SAFETY_RESULTS.md),
[observed-sales forecasts](https://github.com/daniel-li2021/inventory-intelligence/blob/97d1f8a00a00cecdcd01368403bdfeab8b92d510/docs/PUBLIC_SALES_RESULTS.md),
[policy timing](https://github.com/daniel-li2021/inventory-intelligence/blob/39bf64d7e70b9221afbe1d697fe49fd348fcdc04/docs/POLICY_COMPARISON_RESULTS.md).

The public safety study reuses **consumed** observations. Its 32 items, 56 paid
warmup days, 28 score days and 15 settlement days produce 768 continuous arms.
Suppliers, backlog obligations and costs are synthetic. Thirty items have
positive holdout sales; two have undefined fill. These are exploratory sales-
proxy decisions, not measured historical retailer stockouts or independent
evidence for promotion. The synthetic policy adapter exercises unchanged prefix
projection arithmetic; it does not execute the full operational planner gates.

## Demo accessibility and verification

A three-minute local walkthrough starts with the clean baseline, then changes
demand by 25%, introduces hidden supplier delay, and finally removes complete
supply evidence. The final scenario suppresses outputs while retaining the clean
baseline. Trace expansion and JSON export make the displayed numbers inspectable.

The separate accessibility package restores keyboard focus after Run, names
numeric inputs and scrollable tables, distinguishes chart series without color,
and keeps the blocked assessment within a 320px viewport. Actual browser checks
exercise validation, incomplete evidence, request failure and retry. It records
23 passing Lab/API tests and a JavaScript syntax check; no full WCAG or screen-
reader speech certification is claimed. Export reached its download announcement,
but downloaded bytes were not independently rechecked in that round.
[Targeted browser measurements and limits](RESULTS.md#browser-and-accessibility-results).

The merged readiness checkpoint records **134/134** local tests plus published-
path and browser checks. This is historical acceptance of the core, not a current
combined-suite result. PR 14–24 are now integrated; the separate main CI run
passes 240 tests. Neither test duration nor the retained small-fixture microtimings
is a controlled performance/scale benchmark. The case-study receipt is historical
and reconciles seven retained reports
against 50 pinned source-file hashes and selected exact denominators without
refitting models or rerunning simulations.
[Readiness evidence](EVIDENCE.md#acceptance-history), [claim receipt](review/portfolio-claims.json).

## Limits and the next evidence

Ledger/snapshot consistency does not establish physical warehouse truth. Hashes
prove consistency against recorded bytes, not an externally signed source.
Observed sales do not reveal unconstrained demand or inventory availability.
One retailer, small correlated subsets and synthetic economic assumptions cannot
establish population confidence, service guarantees or commercial savings.

Prospective disjoint-item calibration, a separate lost-sales protocol and an
additive synthetic physical-count layer are implemented and merged. The next
decision is review of the [engineering benchmark proposal](PLAN.md)
and [remaining readiness gaps](KB.md#engineering-gaps-and-hypotheses). Feature development,
including unfinished planner-loop execution, is paused. Complex models,
allocation/capacity optimization and hosting retain explicit evidence,
contract or ownership gates. The [22 retained research questions](KB.md#retained-research-questions-and-tentative-extensions)
preserve all options and the condition for moving each forward.

## Resume wording

These bullets describe merged implementation and retained local research evidence.
Main integration does not establish public hosting or production outcomes.

- Built a Python/PostgreSQL inventory reliability and advisory replenishment
  system with exact arithmetic, separate business/ingestion clocks, append-only
  evidence and fail-closed recommendations; validated the synthetic core with
  independent reconciliation controls and a recorded 134-test acceptance run.
- Implemented an attested public observed-sales adapter and train-only 32-item
  forecast benchmark on UCI Online Retail; evaluated daily and cumulative error
  while preserving cancellations, row identity and the sales-versus-demand boundary.
- Evaluated 768 fully costed sales-proxy simulation arms; showed that a nominal
  q95 target achieved 93.14% immediate fill but 84.38% cycle service in a defined
  mean/lead-two scenario, with independently audited timing, conservation and costs.
