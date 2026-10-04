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
| Scale and repeated work | Grouping eligible movements once removes the confirmed 1,000 scans ×99,900 filtered rows. The local paired median fell 10.251→0.856s; the 1M-movement cell now completes. `run_plan` still revalidates its whole batch per key. ARM64 Linux selected planning takes ~3s; a separate zero-ledger profile spent 2.134/2.166s compiling 583 JIT functions. | Keep native/Linux distributions separate; complete x86/two-date confirmation. Any JIT tuning needs a separate comparison; the assigned single optimization is complete. |
| Report growth | Reliability readers cap 1,000 findings / 2 MiB; planning readers cap 16 MiB. Local producer growth and both reader accounting boundaries are now measured; larger defect cells hit the SQL deadline. | B3 failure-envelope measurements. Never truncate findings or raise limits merely to improve a chart. |
| Contention and cancellation | Only benchmark connections have 55s/5s deadlines. Native interruption/snapshot/crash/restore covers a 1k-grain/100k-movement archive with two discrepant probe grains. A verified Lab process crash recovered in 1.652s, with one fault-window 502. Dense duplicate and all-grain discrepancy calls still cancel with no appended history. | Remaining sustained B4/grid cells; do not generalize these faults into RTO/RPO guarantees. |
| Runtime | Actual ARM64 Linux Lab controls verify UID10001, read-only/no-new-privileges/capability restrictions and 0.5 CPU /256 MiB /64 PID limits. One continuous 30-minute campaign completed 2700/2700; short/discontinuous/interrupted windows are excluded. Active clocks missed a wall-budget overrun; delivered guards and journals address that integrity gap. The proxy slow-body path closes or returns 504 rather than 408. | Three-campaign stability/sample gates, proxy timeout semantics and x86/two-date reference remain open. Harness repairs have correctness controls, not new performance confirmation. |
| Release and human use | Private-CA HTTPS and bounded keyboard/mobile paths passed. Public uptime, speech/zoom/forced colors and cold-start acceptance remain unmeasured. Branch protection was not verified by green CI. | V3 human checks plus reviewed host/domain/cost/public release. |

Workloads, SLOs, cache/timing definitions, environment and budget remain in PLAN.
The original existing-Mac pilot is complete. The October 4 assignment authorizes
remaining checks on available local runtimes and one focused optimization; that
optimization is now measured. Keep further engine changes separate from diagnosis.
Speculative queues,
Redis, Kubernetes, sharding, ORMs, indexes or advanced models do not follow from this.

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
| 14 Actual planner closed loop | Paused `codex/planner-closed-loop` protocol/unfinished work; see STATE | Preserve action/receipt identity, repeated clocks and actual reliability/supply gates; resume only after scope approval. |
| 15 Physical inventory truth | [Contract](CONTRACTS.md#physical-count-v1), [results](RESULTS.md#physical-count-controls) | Authenticated count/business evidence needed for real truth; no automatic inventory write. |
| 16 Performance/scale | [Engineering investigation](KB.md#engineering-gaps-and-hypotheses), [PLAN](PLAN.md) | Program/host/budget review before a runner; report measured envelope and failures. |
| 17 Multi-location allocation | SKU/warehouse grain and paired transfer legs do not define transit availability, transport costs or optimal allocation. | Demonstrated transfer benefit, then a transit/cost/capacity contract and independent service oracle. |
| 18 Supplier capacity/calendar | MOQ/pack rounding is not supplier capacity or a working-day calendar. ERP reordering features do not establish optimization of this project's objective. | A binding use case and receipt/approval/timing contract before extending constraints. |
| 19 Guided demo | [Lab](DECISION_LAB.md), [three-minute case study](../README.md) | Reuse clean/spike/delay/blocked walkthrough; add structure only for a demonstrated UX gap. |
| 20 Accessibility/cold start | [Targeted local review](RESULTS.md#browser-and-accessibility-results) | Speech/zoom/forced colors/download bytes and human cold start remain scoped manual checks. |
| 21 Hosted read-only Lab | [Design evidence](../deploy/lab/README.md#serving-architecture-and-limits), [operations](../deploy/lab/README.md) | Actual Linux/runtime/recovery plus reviewed host/domain/cost before public TLS/uptime claims. |
| 22 Portfolio wording | [Case study](../README.md), [historical claim receipt](review/portfolio-claims.json) | Refresh from exact merged/deployed/measured evidence only. |
