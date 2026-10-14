# Inventory Intelligence master implementation plan

Updated 2026-10-13 (America/Los_Angeles). This plan replaces the completed
Increments 0–4 plan and the stale October 12 opportunity ordering. The full user
assignment authorizes the remaining local synthetic product and engineering scope
under AUTO; no new prompt is required between increments. [STATE](STATE.md) owns
integration status. [PLAN](PLAN.md) retains the separate reference/stability
protocol. These are the only ongoing plans. Completed execution protocols and
commands remain in the [execution guide](PLANNER_EXECUTION.md); durable lessons
belong in [KB](KB.md), measured outcomes in [RESULTS](RESULTS.md), and immutable
receipts in [EVIDENCE](EVIDENCE.md).

The baseline is integrated main `3d25409`: a functioning React/TypeScript workbench,
100-key history, actual PostgreSQL planner execution, durable local commitments and
partial receipts, controlled immutable synthetic intake/replay, discovery V2 and
paid one-review contrasts. Extend these paths; do not rebuild completed capability.
The completion target is one usable journey: new evidence → prioritized insight →
inspect cause/evidence → compare feasible decisions → record synthetic execution →
replay later evidence. All business outcomes remain synthetic.

## O01–O25 implementation audit

Status describes the complete opportunity, not whether one useful slice exists.
**Full** means the bounded local product objective is implemented; external gates
are stated separately. **Partial** means existing code should be extended.
**Unimplemented** means no supported workflow exists. **Superseded** means the
original approach has no remaining value in this assignment. Audit evidence is
current source plus retained receipts, not historical plan checkmarks.

| ID | Status at baseline | Existing evidence / code | Remaining disposition |
|---|---|---|---|
| O01 Serving failure boundaries | Partial | `lab_hosted.py`; retained ARM64 crash/runtime controls; RESULTS engineering continuation | Preserve local failure states; proxy slow-body outcome and public continuity remain PLAN gates, not local-product blockers. |
| O02 Planning latency | Partial | `replenishment.run_plan` revalidates inventory; retained ~3s ARM64 selected plans and JIT profile | F: isolated transaction-local JIT comparison before any batch reuse; retain larger/dirty controls and losing result. |
| O03 Scalable evidence access | Partial | `product.py` interns sources and bounds catalogs; `planning_runs.py`/reliability readers retain size caps | F: complete evidence paging/index only for measured reader failures; never truncate or raise caps to conceal failures. |
| O04 Budgets/observability | Partial | Hosted admission/deadlines; engineering Budget/journals and saved recovery receipts | F: bounded new paths, timings/reasons and failed-publish recovery; public load cells remain separate. |
| O05 Lab clarity/navigation | Full locally | `frontend/src/main.tsx`, state controls and browser receipts | Cohesive UI pass; preserve blocked/stale/retry/export behavior. Human conformance remains open. |
| O06 Multi-item workbench | Full locally | Product catalog/API and 100-key × three-cutoff archive | Reuse views for independent intake, constraints and transfers; no new frontend framework. |
| O07 Delivery/developer experience | Partial | Wheel bundles React/assets/evidence; installed-wheel receipts; SQL bootstrap | F: additive reproducible upgrades needed by new schemas, PostgreSQL17 and latest regression checks. No global typing rewrite. |
| O08 Immutable input staging | Partial | `synthetic_replay.admit/replay`, `synthetic-intake-v1`, original text/source versions | A: independent datasets and failed admission/publication controls. No real/company adapter. |
| O09 Exception review | Unimplemented | Durable decision/receipt journal is not an exception-review queue | B: small local source-bound review/dismiss/reopen loop only if useful; never suppress evidence gates. |
| O10 Actual planner closed loop | Full locally | `planner_loop.py`, seven corrected controls + 12×3 stress cells, 129 actual reviews | E: fresh uncertainty/disruption study, retaining blocked and no-winner paths. Do not rerun consumed controls as fresh efficacy evidence. |
| O11 Supplier/purchase lifecycle | Partial | `workflow.Journal`: decisions, commitments, ETA and partial receipts; `publish_supply` | C: bind feasible supply terms/commitments and subsequent planner evidence. No ERP/real ordering/outbox claim. |
| O12 Supplier calendars/capacity | Unimplemented | `decision_contrast.py` checks nominal pack/MOQ/lead only | C: effective calendars, cutoff, capacity, truthful earliest promise and constrained alternatives. |
| O13 Multi-location transfers | Unimplemented | Immediate paired ledger transfers exist; no transit workflow | D: donor-safe deterministic transfer-before-purchase, durable dispatch/transit/partial receipts and transport economics. |
| O14 Count/quality workflow | Partial | `physical_count.evaluate` independent blind-count/review evidence | Preserve kernel/negative controls; operational count intake/quality disposition deferred beyond core scope. |
| O15 Forecast/service intelligence | Partial | Mean/naive/seasonal/intermittent, calibration, warmup/retention/supply studies | E: compare existing baselines' forecast error and actual decision quality on fresh splits before adding methods. |
| O16 Decision-quality evaluation | Partial | Actual loop + one-review contrasts and saved-only cost/conservation audits | E: fresh frozen scenario suite including constraint/transfer baselines and complete paid economics. |
| O17 Evidence Copilot | Full bounded explanation | Saved-evidence Copilot and selected-insight facts/hypotheses/unknowns | B/UI: contributing factors with exact citations; no model/arithmetic calls required. |
| O18 Apparel/lifecycle | Partial | Style/color/size matrix and complete-scope location imbalance | Keep useful matrix; aging, margin/markdown/size-curve economics need unavailable evidence and are deferred. |
| O19 Identity/tenant isolation | Unimplemented | Anonymous read-only package; explicit loopback synthetic journal | Excluded operational gate. No authenticated multi-user/company data claims or speculative auth service. |
| O20 Portfolio/bounded release | Partial | README case study/local demo and pinned receipts | Final local scenario walkthroughs + claim/evidence catalog. Public deployment excluded. |
| O21 Provenance/replay | Partial | Source digests/original text, clocks, immutable reports/journal | A/C/D/F: changing evidence and exact historical reconstruction; hashes do not prove upstream authenticity. |
| O22 Larger frontend redesign | Superseded as a rewrite | React/TypeScript/Vite already integrated and packaged | Adapt existing structure/tokens for cohesive design. Next.js/SSR/framework replacement has no measured value. |
| O23 Discovery/prioritization | Partial | `insights.discover`, I201–I206, exact 15/15 retained triggers | B: explainable stable ordering, contributing factors, gaps and useful next action; no invented probability. |
| O24 Decision comparison | Partial | `decision_contrast.compare` actual/no-action/quantity, common 33 paid days | C/D: feasible constrained alternatives and network baselines, with compatible cost/service windows. |
| O25 History/trends | Full bounded history | Three-cutoff V1 + immutable variable-cutoff V2 catalogs, compatible deltas | A/B/C/D: new dataset history, origin-known changes and execution consequences; missing scope stays unknown. |

The baseline measurements and their denominators are retained in
[dynamic results](RESULTS.md#dynamic-replay-and-insight-discovery-v2),
[actual execution](PLANNER_EXECUTION.md#measured-acceptance), and
[engineering results](RESULTS.md#engineering-continuation). A validation maximum
such as 50×2×12 is not measured full-scale execution support.

## Delivery sequence and acceptance gates

All increments freeze independent expected quantities/negative controls before
implementation, leave the existing interface working, update canonical guides,
and integrate only validated exact heads. Parallel work may own separate modules
and tests; shared contracts, schema migrations, API and frontend integration have
one owner. Do not parallelize competing edits or freeze studies after inspecting
outcomes. A failing meaningful invariant blocks its milestone; unsupported
external environments remain explicit limitations.

### Increment 5 — A/B: independent data and explainable intelligence

Extend existing intake/replay rather than creating an import service. Accept only
explicit synthetic local sources with exact quantities, complete expected scope,
unique natural identities, business/knowledge clocks and immutable version/digest.
Create new actual reliability/forecast/plan runs and insights for a fresh dataset.
The owner stages input; the restricted runner appends results; publication is a
separate atomic stage. Failure must retain the last published valid catalog.

Acceptance: at least two independent new dataset designs differ from the original
100-key archive in identities/dimensions and demand/supply patterns. Freeze exact
insight sets, quantities, clocks and source bindings; include demand/supply change,
persistent/worsening risk, imbalance and missing/contradictory evidence controls.
Replay one historical cutoff after newer knowledge arrives and reproduce its exact
semantic result without rewriting old reports. Duplicate/conflicting identity,
incomplete coverage, future knowledge and forced late transaction/publication
failures leave no partial source/run publication. Count applicable/blocked/unknown
keys explicitly. Prioritization exposes its deterministic factors and tie-break;
verified facts, hypotheses and unknown causes remain distinct. Optional exception
review binds an insight observation/source version and cannot waive a blocker.

### Increment 6 — C: feasible replenishment and feedback

Depends on A provenance and the existing journal. Add an explicit effective
supplier/calendar/cutoff/capacity contract around the actual saved proposal.
Feasible alternatives include no action and pack/MOQ quantities within known
capacity; calendar scheduling determines the earliest supported promise. Capacity
shortfall is shown explicitly, not filled by hypothetical supply. Delay/ETA and
partial receipt facts retain known-at time and outstanding quantities.

Acceptance: independent weekend/holiday/cutoff/boundary and zero/partial/full
capacity controls; exact feasible arrival and quantity; infeasible alternative
rejected or labeled unavailable with no executable promise. Compare purchase,
setup, holding and backlog over common paid windows, preserving null fill at zero
demand and a no-action cost winner. Admission binds source and constraint identity;
retry/reopen/concurrent overreceipt/rollback controls preserve one commitment and
exact receipts. New immutable supply evidence after ETA/partial receipt changes a
subsequent actual planner result; old decisions retain their original context.
Forecast/projected outcomes are separate from realized synthetic execution.

### Increment 7 — D: donor-safe transfers

Depends on C feasibility and A source versions. One bounded two-location SKU
workflow is sufficient initially; it must be a real durable workflow, not an
imbalance label. Compute donor surplus after its own origin-known obligations,
forecast protection/safety and existing reservations. Reserve stock once; dispatch
removes donor availability and creates in-transit quantity; destination stock
appears only on receipt. Support positive transit time, exact partial receipts and
transport per-piece/setup cost. Start with a deterministic transfer-before-purchase
heuristic, residual feasible purchase, purchase-only and no-action baselines.

Acceptance: independent daily network conservation including reservations/transit,
no pre-arrival selling, duplicate/concurrent dispatch/overreceipt rejection,
origin-known history and missing/contradictory legs fail closed. Compare both
locations' service and complete paid network economics on common windows. Protect
donor service under the declared donor forecast/reservation envelope and report
realized synthetic donor service separately; forecasts cannot guarantee service on
arbitrary future demand. Freeze beneficial transfer, transport-too-expensive,
late-arrival, donor-risk and missing-evidence cases. Preserve losing transfers.
Do not add global MILP unless fresh counterexamples demonstrate a valuable gap.

### Increment 8 — E: forecast and decision evidence

Depends on C/D execution contracts. Reuse existing methods and consumed evidence
for regression only. Predeclare fresh independent synthetic traces, study IDs,
selection/evaluation seeds or manifests, policies/costs, equal paid windows and
resource ceilings before outcomes. Include intermittent/zero demand, level shift,
supplier disruption/recovery and incompatible/missing evidence. Selection may use
only its earlier origin-known data; freeze chosen policy before evaluation.

Acceptance: independent error/bias and cumulative protection-demand metrics;
calibration only for methods providing a declared probabilistic target, otherwise
explicitly unavailable. Audit actual planner reviews, infeasibility, immediate/
eventual service, backlog, inventory exposure and every paid cost component.
Show when forecast ranking disagrees with decision ranking. Keep all evaluated
policies, losing cases, irrecoverable evidence gates and no-winner outcomes.
No tuning consumed holdouts, universal champion, sales-proxy demand guarantee or
commercial savings claim. A new model is optional only after a baseline weakness
and fresh promotion gate justify its added cost.

### Increment 9 — F: necessary engineering

Run alongside A/B and C/D where changes are independent; finish before final local
acceptance. Reuse retained scale/Linux/recovery evidence. Measure only identified
new-path bottlenecks and previously measured reader/selected-plan failures.
A transaction-local JIT comparison must keep semantics/source hashes identical,
counterbalance order and include clean/larger/dirty controls. Evidence paging must
retain full validated content and stable identities; UI pagination alone does not
repair an unreadable producer report. Introduce additive/idempotent migrations only
for required new schemas, checking fresh and populated upgrade paths plus failure
rollback. Observe structured operation identity, duration, outcome/reason and limits.

Acceptance: exact legacy/source/history compatibility, focused then latest-code
regressions, installed-wheel no-Node/no-key read-only and explicit-loopback demos,
bounded concurrent admissions/receipts/publication and failure recovery. Complete
available PostgreSQL17 reference checks with the actual version; native18 results
cannot satisfy that gate. Freeze/report runtime, sample counts, cache state,
latency/resource limits and failures. Bound each new local study to 15 minutes and
retain an explicit limited result at its ceiling; broader PLAN campaigns keep their
existing guards and require an available runtime. No paid services or public load.

### Increment 10 — product design, scenarios and portfolio acceptance

Keep UI integration in each earlier increment. After core contracts stabilize,
perform one cohesive design pass on the existing workbench. Adapt Meridian's
structured hierarchy and Folio's readable evidence inspection to inventory:
attention queue first, compact item/location/cutoff context, feasible comparison,
linked evidence, execution/history and responsive detail. Exact tables accompany
charts; no client business arithmetic or ungrounded confidence score. Freeze the
scope of screens/states before the pass; avoid new framework/dependency families.

Acceptance: existing journeys and new data/constraints/transfer flows work at each
milestone. Verify desktop/mobile, keyboard/focus, reload/shareable state, long
exact values, blocked/stale/loading/error/retry/export and preserved last-good
results. Browser developer controls do not establish independent human
comprehension or accessibility conformance. Provide reproducible local commands,
scenario artifacts, architecture and concise engineering case studies linking
problem → implementation → independent benchmark → user result → limitations.

Final scenarios must independently cover: new dataset admission/regeneration;
explainable demand/supply stockout risk; materially different feasible replenishment
outcomes; donor-safe transfer versus purchase/no-action; commitment/ETA/partial
receipt feedback into later actual plans; and unsafe evidence rejection with
unchanged history. Run the relevant independent auditor and retain receipt/denominator
for each. Final integration verifies remote main and returns primary checkout to
current main; retire only proven-integrated clean task branches/worktrees.

## Benchmarks and stopping conditions

The suite is a catalog of complementary evidence, not a single blended score:

- Exact correctness: independent source binding, identities/clocks, conservation,
  feasible dates/quantities, complete paid arithmetic, null/block and negative controls.
- Intelligence: expected rule set, factor values, deterministic ordering, unknown
  scope/causes and historical persistence; no precision claim without a declared set.
- Policy quality: fresh paired traces with each method's forecast metrics, actual
  reviews/service/cost/exposure/infeasibility and held-out selection boundary.
- Transfer: network and donor outcomes plus transport costs; beneficial and losing
  scenarios with a complete two-location denominator.
- Engineering: available exact-version regression, installed-wheel/browser smoke,
  operation latency/resources, concurrency and forced recovery; retain environment.

Stop a workstream when its scoped independent controls and integrated journey pass.
Do not expand tests/workloads repeatedly without a new failure or justified claim.
A measured no-benefit method is complete evidence, not a reason to add model families.
The full assignment completes only when A–F and the integrated scenarios are
implemented and locally accepted, or a genuine external gate is documented with
all feasible local work finished. Do not mark planning or A/B alone as completion.

## UI direction and reference comparison

The retained October 12 reference metadata in [repositories.json](research/repositories.json)
records public pattern/license inspections; it is historical context, not a current
upstream recommendation. Use task-oriented queues, explicit inventory states,
filtered drillthrough and readable calculation/source context. Study the current
local FinRAG Meridian implementation and an available Folio source/reference before
making new comparative claims. Borrow hierarchy/inspection patterns, not another
product's business data, assets or code. Inventory's distinguishing interaction is
known evidence → feasible action → later receipt/history with exact pieces.

## Excluded scope and future work

Public hosting/TLS, x86/reference hardware, independent human/accessibility
conformance, authenticated multi-tenant operation, source-owner authenticity and
real purchasing remain separate external gates. No company data, credentials,
real orders, paid services or public deployment are authorized by this roadmap.
Full ERP/accounting/BOM/lots/serials, richer quality/count intake, lifecycle margins,
real supplier adapters and advanced allocation remain conditional future work.
Queues, microservices, Kubernetes, a forecast model zoo, autonomous ordering and a
frontend rewrite have no supported value in this scope. Future additions require
specific unmet evidence/workflow needs and fresh acceptance, not mechanical O-ID
completion. The approved attributed UCI exception remains offline research only.
