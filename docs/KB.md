# Project knowledge

Durable findings and tentative questions extracted from completed investigations.
Use [STATE](STATE.md) for scope, [DECISIONS](DECISIONS.md) for choices and
[RESULTS](RESULTS.md) for outcomes. Hypotheses below are not assignments.

## Correctness and trust boundaries

- Reconciliation requires the same SKU/warehouse grain, cutoff, watermark and
  complete manifests. Empty coverage and known movements outside declared coverage
  are R005 `coverage_mismatch`, blocking R001; unknown references retain local R003
  handling. Internally consistent records are not proof of physical stock.
- Demand training is contiguous, complete integer data for the selected batch/key,
  with eligible business and knowledge clocks. Natural order identities must be
  unique across selected days. Null/stockout/unknown demand is not eligible zero.
- Freeze model selection at the earlier of evaluation and holdout start; replay
  eligibility at each origin. Day-41 quantity 7 revised to 700 but learned on day 60
  must not alter the earlier selector or quantity 7. Fold truth, selected revisions,
  scores and planner training/horizon must agree.
- Copilot validates saved evidence/context; it neither reforecasts nor queries latest
  raw sources to authenticate them. Historical blocked runs may be explained;
  contradictory evidence cannot produce replacement quantities or approved orders.
  Hashes identify bytes/lineage, not trustworthy upstream ownership.
- The Lab's packaged zero-movement fixture validator checks all retained inventory
  keys, counts/coverage/clocks, unique identities, supply receipts and report links.
  Rehashed contradictions, null receipt dates and malformed demand fail closed
  (offline suppression; HTTP 503). It is not a general SQL reliability checker.
- Reversal checks cover arithmetic and referenced rows, not every business reversal.
  Running-negative stock, richer transit/reservation semantics and stronger source
  authentication require separately defined contracts.
- Prefix planning protects the largest pre-arrival safety deficit. Periodic backlog
  simulation owns orders, receipts, costs and runoff separately. Hidden delays must
  not leak into planning; different runoff lengths are different cost exposures.
- SQL permissions prevent runtime source writes, not upstream-owner rewrites.
  Atomic rollback of known errors does not establish crash recovery.

Accepted interfaces remain in [inventory](CONTRACTS.md#inventory-v1),
[planning](CONTRACTS.md#planning-v1), [Copilot](CONTRACTS.md#copilot-v2) and
[simulation](CONTRACTS.md#decision-simulation-v1) contracts. Independent oracles are in
[VALIDATION](VALIDATION.md) and [RESULTS](RESULTS.md#lab-arithmetic-and-service).

## Decision-evaluation lessons

On the same scored observations, MAE and WAPE rank methods identically: the error
numerator is shared and the denominators do not depend on the method. Neither
expresses asymmetric shortage/holding costs. MAE targets a median; frequent zero
demand can favor zero forecasts despite positive expected demand. Preserve daily
error/bias alongside cumulative protection-period error for `H = lead + review`,
paid inventory outcomes and paired cost/service comparisons. An accurate final
total can still conceal an early shortage. [Concrete oracles](RESULTS.md#decision-metric-counterexamples).

Squared/scaled metrics need a nonzero training-only scale or remain null. If using
probabilistic forecasts, assess pinball loss and coverage for the actual cumulative
target; summing daily quantiles does not produce a cumulative quantile. Calibration
labels must be completed and origin-known. Collapse repriced costs/repeated controls
when counting independent paths; four passes on one seed are not four successes.

Keep startup infeasibility in the denominator. Compute unfillable units before the
first possible receipt independently, preserving prior-commitment priority; the
policy must not see future demand used by this diagnostic. Warmup carries each
policy's paid stock/backlog/pipeline into scoring, with costs and starting state
reported. Fresh demand and supplier paths across selection/holdout answer a stronger
question than reusing one hidden delay trace. A short zero run is not retirement;
lower safety targets cannot liquidate already owned stock. These lessons now have
[feasibility](RESULTS.md#startup-feasibility), [warmup](RESULTS.md#paid-warmup)
and [retention](RESULTS.md#safety-retention) results rather than old task plans.

## Engineering gaps and hypotheses

The initial assessment inspected main `9d7c55f` and reused saved results. The
subsequent authorized [native pilot](RESULTS.md#local-engineering-pilot) measured
exploratory synthetic behavior; reference/production capacity remains unconfirmed.
[Baseline receipt](review/engineering-readiness-baseline.json).
Correctness CI, research arm counts, suite elapsed time and the UCI 541,909-row
extraction are not measured throughput or service capacity.

| Gap | Finding / hypothesis | Evidence needed |
|---|---|---|
| Scale and repeated work | Grouping eligible movements once removes the confirmed 1,000 scans ×99,900 filtered rows. The local paired median fell 10.251→0.856s; the 1M-movement cell now completes. `run_plan` still revalidates its whole batch per key. ARM64 Linux selected planning takes ~3s; a separate zero-ledger profile spent 2.134/2.166s compiling 583 JIT functions. | Keep native/Linux distributions separate; complete x86/two-date confirmation. The [separate JIT comparison](ENGINEERING_SUPPORT.md#planning-latency-retained-negative-finding) fails its 20% adoption gate (4.02% benefit); no kernel change. Further tuning needs a fresh justified comparison; the single SQL optimization is complete. |
| Report growth | Reliability readers cap 1,000 findings / 2 MiB; planning readers cap 16 MiB. Local producer growth and both reader accounting boundaries are now measured; larger defect cells hit the SQL deadline. | B3 failure-envelope measurements. Never truncate findings or raise limits merely to improve a chart. |
| Contention and cancellation | Only benchmark connections have 55s/5s deadlines. Native interruption/snapshot/crash/restore covers a 1k-grain/100k-movement archive with two discrepant probe grains. A verified Lab process crash recovered in 1.652s, with one fault-window 502. Dense duplicate and all-grain discrepancy calls still cancel with no appended history. | Remaining sustained B4/grid cells; do not generalize these faults into RTO/RPO guarantees. |
| Runtime | Actual ARM64 Linux Lab controls verify UID10001, read-only/no-new-privileges/capability restrictions and 0.5 CPU /256 MiB /64 PID limits. One continuous 30-minute campaign completed 2700/2700; short/discontinuous/interrupted windows are excluded. Active clocks missed a wall-budget overrun; delivered guards and journals address that integrity gap. The proxy slow-body path closes or returns 504 rather than 408. | Three-campaign stability/sample gates, proxy timeout semantics and x86/two-date reference remain open. Harness repairs have correctness controls, not new performance confirmation. |
| Release and human use | The October 15 public smoke verifies trusted TLS, readiness and a brief developer journey. Sustained public serving, speech/zoom/forced colors and human cold-start acceptance remain unmeasured. Branch protection was not verified by green CI. | V3 human checks and sustained runtime evidence; brief public smoke is not capacity acceptance. |

Workloads, SLOs, cache/timing definitions, environment and budget remain in PLAN.
The original existing-Mac pilot is complete. The October 4 assignment authorizes
remaining checks on available local runtimes and one focused optimization; that
optimization is now measured. Keep further engine changes separate from diagnosis.
Conditional improvements require a demonstrated bottleneck and a fresh assigned
comparison: batch/grain query reuse or indexes must preserve duplicate/clock evidence
and disclose storage/write cost; archive caches must reject changed/rehashed invalid
inputs; reader/timeout changes must retain complete history and honest rejection;
worker changes must preserve global admission and resource semantics. Compare the
same frozen workloads before/after, retain regressions and stop if the baseline
meets its declared envelope. These are hypotheses, not pending implementation.
Speculative queues, Redis, Kubernetes, sharding, ORMs or advanced models do not
follow from this.

## Next-phase investigation

The [October 12 receipt](review/next-phase-investigation.json) records historical
inspection of `b5b8d5a`; its fixed-SKU UI and paused-feature gaps are superseded by
Increments 0–4 and controlled replay/discovery V2. [ROADMAP](ROADMAP.md) owns the
remaining independent acceptance after the completed local implementation. Keep
the original receipt unchanged.

Durable lessons from the completed product/execution work:

- The actual prefix planner, periodic simulator and one-review contrast have
  different action/review semantics. Label them before comparing outcomes; retain
  complete common paid windows, source identities and compatible metric denominators.
- Actual execution rejected one original cold-shortage oracle: a 17-piece need
  rounds to 18, not 12. The original expectation and explicit erratum remain;
  correcting an oracle after seeing execution is not fresh held-out quality evidence.
- On the frozen 12-trace grid, actual proposals beat fixed-18 on 12/12 and no-action
  on 11/12; quiet demand favors no action. Training stockouts and overdue commitments
  still block. Neither attractive sums nor a journal waive source/training gates.
  [Exact measurements](PLANNER_EXECUTION.md#measured-acceptance).
- Durable decisions and receipt events need source-bound natural identity and
  coherent transactions. Promise/ETA changes are knowledge, not physical receipt;
  partial receipts conserve outstanding pieces. SQLite journal and PostgreSQL
  owner publication are separate boundaries, not a production atomic handoff.
- Variable synthetic datasets already use immutable source versions/original text,
  actual restricted-runner reports and automatic discovery. A source digest proves
  byte identity, not real stock truth or trusted ownership. Reusing a new cutoff
  must not leak later knowledge into historical runs.
- Discovery verifies observable demand/supply/projection changes, not external
  causation. Explain measured facts, model hypotheses and absent evidence separately.
  Source completeness, freshness, applicability, uncertainty and feasible action
  remain different states; no composite AI-confidence percentage is supported.
- Location imbalance is not executable surplus. A transfer needs donor protection,
  reservations, dispatch/transit/receipt conservation, feasible timing and network
  economics. Nominal pack/MOQ/lead is not a supplier calendar/capacity contract.
- Readable context/evidence belongs beside the selected insight and decision.
  Existing React routes, matrix and exact inspector meet the bounded journey; another
  framework rewrite has no measured value. Independent human accessibility and
  comprehension remain separate from developer browser checks.
- Whole-batch revalidation/archive-wide reads remain visible; retained JIT profiles
  justify isolated measurement before caches/indexes. Large unreadable reports need
  complete versioned evidence access, not truncated findings or raised caps.

## Source and tool lessons

This consolidates the **2026-10-02 inspection**, not current upstream advice.
[Pinned metadata](research/repositories.json) retain inspected revisions, hashes,
license metadata and capture dates. Verify component licenses/versions before
adoption; popularity is not correctness.

| Reference | Useful lesson | Adoption boundary |
|---|---|---|
| ERPNext | Stock Ledger versus Bin separates events from balances; retain event/line identity, signed quantities, clocks and reversals. Backdating can use controlled reposting. | Do not copy GPL-3 ERP valuation/FIFO/accounting code or assume all backdating is forbidden. |
| Odoo 19 | `stock.move` versus `stock.quant`; variants, locations and units; on-hand/reserved/available differ. Counts create events rather than overwrite history. | Review component LGPL licensing and business semantics. |
| InvenTree | Actor/delta tracking; deleting stock can retain nullable history links, but deleting a part can erase history. | Not strict immutability; no Django/admin dependency is needed here. |
| SQLMesh | Versioned SQL audits, restatements and environments can help many derived models. | Downstream blocking audits may follow model writes, not roll them back. Incremental audits cover processed intervals. |
| Great Expectations | Named expectations and complete unexpected-row retrieval can help multiple backends. | Samples are not full coverage; setup does not supply inventory semantics. |
| Elementary | Monitoring through dbt artifacts. | Distinguish OSS and hosted capabilities; adding dbt just for this is unjustified. |
| dlt | Cursor choice matters for late/backdated records: update/ingestion knowledge clocks may be needed. | Event-time cursors can miss updates; the framework cannot align ledger/snapshot clocks or prove completeness. |
| dbt | Version/adapter/distribution matters, including inspected Python-v1 and Rust-v2 differences. | Verify licenses and Elementary compatibility; do not add both dbt and SQLMesh without need. |
| OpenLineage | Job/run/dataset vocabulary. | Dataset graphs do not identify the record causing a finding. Add a backend only for a demonstrated cross-system need. |
| Bruin / Carbon | README-level orchestration/manufacturing awareness. | No implementation audit. Carbon's inspected AGPL/enterprise exceptions and `NOASSERTION` do not establish permissive reuse. |
| Soda Core / data-diff | Ordinary SQL meets current validation needs. | Inspected Soda Core used Elastic License 2.0, not the older Apache assumption. Datafold data-diff was archived May 2024. |
| StatsForecast | Potential statistical/intermittent challengers. | Demonstrate a sealed baseline weakness; freeze method/version/license/evaluation before adding it. |

PostgreSQL, SQL, Psycopg, the standard library and Compose meet the present need.
Vocabulary can be adopted without importing upstream implementations.

## Public data boundary

Use the investigation's UCI fallback, **Online Retail**, Chen (2015), DOI
[10.24432/C5BW33](https://doi.org/10.24432/C5BW33). The
[official dataset page](https://archive.ics.uci.edu/dataset/352/online%2Bretail)
was checked 2026-10-02 and explicitly identifies CC BY 4.0. Its linked archive
contains `Online Retail.xlsx` (approximately 22.6 MB); metadata records 541,909
transactions from 2010-12-01 through 2011-12-09. Retain attribution, the
[license](https://creativecommons.org/licenses/by/4.0/) and retrieval provenance.
M5's [rules](https://www.kaggle.com/competitions/m5-forecasting-accuracy/rules)
and [data page](https://www.kaggle.com/competitions/m5-forecasting-accuracy/data)
returned no readable terms in this check. M5 acquisition/publication remains
unapproved; do not substitute an unofficial mirror or infer rights from MIT.

Acquire only the official UCI archive into ignored `data/raw/uci-online-retail/`.
Record real UTC retrieval time, exact URLs, license/version, archive/file SHA-256,
file sizes, workbook sheet names, schema and row counts. Preserve source row
identity `(dataset, archive_sha256, sheet, row_number)`; invoice/product pairs
are not proven unique line identities. Raw rows and reconstructable derived
series, customer identifiers and descriptions stay outside Git. Publish only
code, synthetic adapter tests, protocol and aggregate research metrics with
dataset attribution. No public-data screenshots or operational import.

### Target and completeness

Target is **gross positive non-cancelled invoiced unit sales per StockCode and
source date**, across the dataset's retailer. Customer Country is not a store
or fulfillment warehouse. Use recorded InvoiceDate calendar labels; no invented
timezone, acceptance time, recording time or historical ingestion clock.
Acquisition time is separate from a modeled end-of-day release assumption.

Cancellation-coded invoices and nonpositive quantities are excluded from gross
positive sales, with exact exclusion counts/reasons retained. Do not subtract
returns as negative demand, reconstruct hidden demand, silently drop duplicates
or infer product availability from first positive sale. Invalid required
quantity/date/identity rows block adaptation and are reported. Preserve original
row evidence outside Git, including excluded rows. Dates missing for a selected
item have observed sales zero only within a verified complete extraction of the
declared archive range; this never proves zero unconstrained demand or availability.
No prices, promotions or customer attributes enter forecasting features.

## Retained research questions and tentative extensions

All 22 earlier directions remain here with evidence/gates. These are future questions;
STATE and the active plan own prioritization and progress; these are not assignments.

| # / question | Durable evidence or rationale | Condition for further work |
|---|---|---|
| 1 Fresh demand/supply and paid warmup | [Protocol](EVIDENCE.md#study-artifacts-and-original-sources), [results](RESULTS.md#paid-warmup) | New frozen traces; paid owned carryover and common settlement. |
| 2 Feasibility versus policy misses | [Diagnostic](EVIDENCE.md#study-artifacts-and-original-sources), [results](RESULTS.md#startup-feasibility) | Signed interventions with explicit interactions; no invented additive attribution. |
| 3 Safety target versus achieved service | [Safety results](RESULTS.md#public-sales-safety), [disjoint calibration](RESULTS.md#disjoint-item-calibration) | Fresh evidence beyond consumed same-retailer/calendar paths; no nominal guarantee. |
| 4 Retention during decline/recovery | [Protocol](EVIDENCE.md#study-artifacts-and-original-sources), [negative results](RESULTS.md#safety-retention) | Justified revision tested on fresh recovery paths with owned stock/cost. |
| 5 Lead-time/supplier reliability | [Protocol](EVIDENCE.md#study-artifacts-and-original-sources), [results](RESULTS.md#supply-sensitivity) | Specific unmet supply question; actual supplier truth remains unavailable. |
| 6 Probabilistic protection demand | [Safety protocol](EVIDENCE.md#study-artifacts-and-original-sources), [calibration protocol](EVIDENCE.md#study-artifacts-and-original-sources) | Completed origin-known calibration labels, target coverage/pinball and achieved service. |
| 7 Policy comparison | [Protocol](EVIDENCE.md#study-artifacts-and-original-sources), [negative/conditional results](RESULTS.md#ordering-policies) | Fresh paid warm states and hidden-delay-compatible inputs. |
| 8 Public adapter/provenance | [Assigned protocol](KB.md#public-data-boundary), [adapter](CONTRACTS.md#observed-sales-adapter) | Preserve identity, source rights and immutable caches; no operational imports. |
| 9 Observed-sales realism | [Forecast protocol](EVIDENCE.md#study-artifacts-and-original-sources), [results](RESULTS.md#public-observed-sales) | Broader/later frozen evidence; sales remain a proxy rather than unconstrained demand. |
| 10 Advanced models | [Intermittent protocol](CONTRACTS.md#intermittent-methods-v1), [results](RESULTS.md#intermittent-benchmark) | Repeated sealed baseline weakness before ADIDA/IMAPA; feature/license/dependency protocol before global ML. |
| 11 Source provenance | [Lineage protocol](EVIDENCE.md#historical-provenance-and-independent-audits), [integration evidence](EVIDENCE.md#historical-provenance-and-independent-audits) | Demonstrated missing semantic link; hashes are not signed authenticity. |
| 12 Property/mutation QA | Existing independent controls in `tests/`, [readiness evidence](EVIDENCE.md#acceptance-history) | A concrete uncovered invariant; test counts are not a quality target. |
| 13 Backlog versus lost sales | [Contract](CONTRACTS.md#lost-sales-v1), [paired results](RESULTS.md#matched-lost-sales) | Keep permanent losses and owed backlog plus different cost units explicit. |
| 14 Actual planner closed loop | [Completed local execution guide](PLANNER_EXECUTION.md); original controls preserved by archive tag | Fresh assigned studies keep action/receipt identity, repeated clocks and actual reliability/supply gates; no consumed-holdout tuning. |
| 15 Physical inventory truth | [Contract](CONTRACTS.md#physical-count-v1), [results](RESULTS.md#physical-count-controls) | Authenticated count/business evidence needed for real truth; no automatic inventory write. |
| 16 Performance/scale | [Engineering investigation](KB.md#engineering-gaps-and-hypotheses), [PLAN](PLAN.md) | Reuse the delivered runner and completed cells; review host/budget before a new confirmation program and report failures. |
| 17 Multi-location allocation | SKU/warehouse grain and immediate paired legs do not define transit stock or donor-safe allocation. | [Bounded durable transfers](TRANSFERS.md) are implemented; repeated execution needs donor-basis reconciliation, and advanced optimization needs measured heuristic counterexamples. |
| 18 Supplier capacity/calendar | MOQ/pack rounding is not supplier capacity or a working-day calendar. | [Declared constraints and durable admission](SUPPLIER_FEASIBILITY.md) are implemented; new work needs a concrete unmet calendar/capacity need and independent cutoff/receipt controls. |
| 19 Guided demo | [Lab](DECISION_LAB.md), [three-minute case study](../README.md) | Reuse clean/spike/delay/blocked walkthrough; add structure only for a demonstrated UX gap. |
| 20 Accessibility/cold start | [Targeted local review](RESULTS.md#browser-and-accessibility-results) | Speech/zoom/forced colors/download bytes and human cold start remain scoped manual checks. |
| 21 Hosted read-only Lab | [Design evidence](../deploy/lab/README.md#serving-architecture-and-limits), [operations](../deploy/lab/README.md) | [Public smoke](review/render-public-smoke-v1.json) verifies trusted TLS and a brief journey; sustained runtime/cold-start/human acceptance remains open, with no uptime guarantee. |
| 22 Portfolio wording | [Case study](../README.md), [historical claim receipt](review/portfolio-claims.json) | Refresh from exact merged/deployed/measured evidence only. |


## Full product roadmap outcome and opportunity audit

The October13–14 full local synthetic assignment superseded the old limited
increment pauses. One master plan was frozen at commit73a2271; its completed
execution narrative is retained in Git. Current capabilities/reproduction belong
in [platform case studies](PLATFORM_GUIDE.md), not another completed-plan library.

| Opportunity | Current disposition | Evidence / remaining value |
|---|---|---|
| O01 serving boundaries | Partial | Local request/body/rate/concurrency/recovery guards; sustained/public gates remain PLAN. |
| O02 planning latency | Partial; JIT candidate not adopted |64 real calls,4.02% large-clean reduction below 20% gate; retain old/runtime differences. |
| O03 scalable evidence | Partial | Bounded source-bound inspection above old caps; full large-report semantic/producer acceptance remains open. |
| O04 budgets/observability | Partial | Local study guards, durations/reasons, immutable exports and recovery; public load/security separate. |
| O05 clarity/navigation | Full locally | Compact light workbench with progressive evidence inspection and tested states. |
| O06 multi-item workbench | Full locally | Original100 keys plus independent changed six-key datasets; no new framework. |
| O07 delivery/developer experience | Full local packaging; external reference partial | Current wheel/offline controls, additive journal upgrade, real PG17 regressions; exact hardware/runtime gates explicit. |
| O08 immutable staging | Full controlled synthetic scope | Version registry, source identity/clocks, real reports/replay, atomic last-good publication. |
| O09 exception review | Full local synthetic scope | Immutable source-bound acknowledgment/investigation/resolution; facts/gates never suppressed. |
| O10 actual planner closed loop | Full bounded scope | Original controls/stress traces and fresh48 loops/144 reviews; blocking/losers retained. |
| O11 purchase lifecycle | Full local synthetic scope | Feasible commitments, revised ETA, partial receipts and separate owner feedback; no ERP/real orders. |
| O12 supplier feasibility | Full declared synthetic scope | Weekday/cutoff/daily capacity, exact promises and compound negative controls. |
| O13 transfers | Full bounded two-location scope | Donor-safe reservations/dispatch/transit/partial receipts/ETA, conservation, paid comparison and actual feedback. |
| O14 count/quality | Partial | Existing blind-count/corroboration/review kernel; operational count intake beyond this scope. |
| O15 forecast/service intelligence | Partial | Existing intermittent/calibration research plus fresh point-baseline/decision evaluation; no intervals or new methods promoted. |
| O16 decision evaluation | Full bounded synthetic scope | Fresh selection/evaluation split, independent arithmetic, complete paid outcomes, ties/no-winner and blocks. |
| O17 evidence explanation | Full bounded scope | Cited saved facts, contributing factors, hypotheses/unknowns and exact backend arithmetic. |
| O18 apparel/lifecycle | Partial | Existing style/color/size matrix and location patterns; aging/margin/markdown lack inputs. |
| O19 identity/tenancy | Unimplemented operational gate | Real authenticated multi-user/private intake explicitly excluded. |
| O20 portfolio | Full local portfolio scope | Six connected reproducible case studies, working demo and explicit external gates. |
| O21 provenance/replay | Full local synthetic scope | Immutable sources/reports/versions/clocks/journals; authenticated upstream provenance remains separate. |
| O22 larger rewrite | No longer valuable | Existing React/Vite supports the cohesive journey; no Next.js/SSR/frontend replacement justified. |
| O23 discovery/prioritization | Full bounded rule scope | Expected triggers, exact factor values and explainable ordering; no detection/population accuracy claim. |
| O24 comparison | Full local bounded scope | Saved actual/no-action/feasible quantities, supplier constraints and network/transport economics. |
| O25 history | Full bounded scope | Compatible cutoff/source/knowledge history, origin-known ETA/partial effects and preserved missing scope. |

Lessons: short-prefix imbalance is not donor-safe surplus; full declared-demand
protection correctly blocks the original 80-stock/112-demand donor. Transfer goods
are paid once, not purchased again. Expensive transport can reverse the choice.
Accuracy-selected forecasts need not minimize paid costs; only 2/8 fresh choices pass
the downstream gate. Later arrival can reduce holding cost without lowering service.
A transfer reservation does not admit a residual purchase. Contradictory shared
supplier/day capacity cannot expand allocations; transport versions are immutable.
A new stock count and source basis require explicit owner evidence/reconciliation.
Pages are inspection, not complete semantic acceptance. Local/diagnostic/developer
checks never become unseen efficacy, independent human review or production evidence.

Valuable future work is conditional: independent human/accessibility acceptance,
exact runtime/hardware/sustained-serving confirmation, explicit donor-basis
reconciliation and fresh multi-review network studies, operational producer/tenant
identity and supplier/transport adapters, or lifecycle economics after required
inputs exist. New models/optimizers/services require a measured unmet need.
