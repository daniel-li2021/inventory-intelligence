# Knowledge and evidence index

Read [STATE](STATE.md) first, then select the relevant plan from the registry below.
[DECISIONS](DECISIONS.md) records why boundaries exist and when they are superseded;
[CONTRIBUTING](../CONTRIBUTING.md) owns the delivery workflow. This index is a
routing map, not another current-state ledger.

## Plans and work status

Multiple plans may cover different horizons or areas. This registry lists their
scope and status; each plan owns detailed progress, completed outcomes, remaining
gaps and next action. STATE identifies the immediate focus and mode. Work one
assigned task at a time; ongoing/proposed plans do not authorize execution.

| Plan | Horizon / scope | Status | Next action / remaining gap |
|---|---|---|---|
| [Engineering readiness](PLAN.md) | Near-term correctness, capacity and runtime evidence | Ongoing design; P0 completed, P1 awaiting review | Review workload/SLO, host/runtime and pilot budget before implementation. |
| [Research roadmap](RESEARCH_ROADMAP.md) | Long-term evidence and decision quality | Ongoing strategic plan; feature execution paused | Resolve engineering gate before choosing one justified follow-up. |
| [Hosted Lab](HOSTED_LAB_PLAN.md) | Serving architecture and release | Readiness package completed; release gaps remain | Linux/container/recovery evidence, then reviewed host/domain/cost and public release checks. Source-bound design stays unchanged. |

At completion, update the plan with completed work and evidence plus remaining
gaps (linked follow-up or explicit deferral), then update its registry status.
Completed does not mean all future extensions are done. Keep useful completed
plans accessible; mark obsolete plans superseded and link the replacement.
Archive only duplicates or obsolete detail with a pinned historical link.

## Durable implementation and operations

| Surface | Contract / knowledge | Operations / example |
|---|---|---|
| Inventory reliability | [CONTRACT_V1](CONTRACT_V1.md), [DATA](DATA.md), [ENGINE](ENGINE.md) | [Validation](VALIDATION.md), [combined example](examples/combined.md) |
| Demand, forecasts and advisory planning | [CONTRACT_PLANNING_V1](CONTRACT_PLANNING_V1.md) | [PLANNING](PLANNING.md), [example](examples/stage2.md) |
| Read-only evidence Copilot | [Copilot-1](CONTRACT_COPILOT_V1.md), [additive Copilot-2](CONTRACT_COPILOT_V2.md) | [Examples](examples/copilot.md), [routing evaluation](STAGE3_BENCHMARK.md), [stabilization](STAGE3_STABILIZATION.md) |
| Local synthetic Lab | [Architecture/API/UX](DECISION_LAB.md) | [Independent oracles](DECISION_LAB_VALIDATION.md), [accessibility review](LAB_ACCESSIBILITY_REVIEW.md) |
| Hosted serving design | [HOSTED_LAB_PLAN](HOSTED_LAB_PLAN.md) retains source-bound design and completed readiness work | [Deploy/rollback operations](../deploy/lab/README.md); remaining work is gated in PLAN |
| Engineering readiness | [Recorded investigation](ENGINEERING_READINESS.md) | [Active proposal](PLAN.md); no benchmark result exists |
| Source/tool research and portfolio | [Original reference investigation](RESEARCH.md), [pinned metadata](research/repositories.json) | [Case study and scoped claims](PORTFOLIO_CASE_STUDY.md) |

## Evidence and reproducibility

Retain frozen protocols, source snapshots, machine-readable reports/receipts,
independent oracles and curated examples at stable paths. `docs/review/` contains
historical evidence, not editable status. Historical reviews describe only their
recorded commit, environment and scope: [Stage 1](STAGE1_REVIEW.md),
[three-stage](THREE_STAGE_REVIEW.md), [core readiness](READINESS_CORE_REVIEW.md),
[Lab readiness](READINESS_LAB_REVIEW.md), [combined readiness](READINESS_REVIEW.md),
[research integration](RESEARCH_INTEGRATION.md). New state supersedes their status
claims without changing the captured outcomes. Exact integration/CI references
remain in the immutable [merge receipt](review/research-main-integration.json)
and [engineering inspection](review/engineering-readiness-baseline.json).

[RESEARCH_LINEAGE_V1](RESEARCH_LINEAGE_V1.md) and the
[original manifest](review/research-integration-lineage-v1.json) retain package
heads, complete source maps and parent/freeze bindings. Preserve full Git history
and original report bytes. Saved-manifest audit is an **exact snapshot check**:
later validator or documentation edits may make it reject current files. Run
historical audits in the complete original Git/source view, not after copying an
old kernel into current code. Current `tests.test_research_lineage` builds/audits
current bindings separately; a new manifest, if needed, uses a new path and
committed validator sources. Never overwrite the original manifest to clear drift.

Source-hashed protocols keep their exact pre-cleanup bytes. Three static redirects
(`NEXT_ROUND_RESEARCH`, `READINESS_NEXT_STEPS`, `ENGINEERING_BENCHMARK_PLAN`)
preserve inbound links to pinned originals. RESEARCH_ROADMAP now hosts the linked
long-term plan and retains a link to its original snapshot. New planning status
does not rewrite frozen protocols or authorize their historical assignments.
Original reports, source maps and the historical hosted-design drift stay intact;
no artifact hashes are rewritten and no studies are rerun. Negative outcomes,
consumed holdouts, undefined denominators, source-versus-authenticity and
local-versus-CI distinctions remain explicit. Reuse ignored raw/item caches;
do not publish or delete them.

## Retained research questions and tentative extensions

All 22 earlier directions remain discoverable below. Evidence columns refer to
bounded historical studies; the condition column is a future question, **not an
active assignment**. Feature expansion stays paused under D11. Progress belongs
in the relevant indexed plan; do not duplicate its detailed delivery checklist here.

| # / question | Durable evidence or rationale | Condition for further work |
|---|---|---|
| 1 Fresh demand/supply and paid warmup | [Protocol](RESEARCH_WARMUP_V1.md), [results](FRESH_WARMUP_RESULTS.md) | New frozen traces; paid owned carryover and common settlement. |
| 2 Feasibility versus policy misses | [Diagnostic](FEASIBILITY_DIAGNOSTIC.md), [results](FEASIBILITY_DIAGNOSTIC_RESULTS.md) | Signed interventions with explicit interactions; no invented additive attribution. |
| 3 Safety target versus achieved service | [Safety results](PUBLIC_SAFETY_RESULTS.md), [disjoint calibration](PUBLIC_CALIBRATION_RESULTS.md) | Fresh evidence beyond consumed same-retailer/calendar paths; no nominal guarantee. |
| 4 Retention during decline/recovery | [Protocol](SAFETY_RETENTION_V1.md), [negative results](SAFETY_RETENTION_RESULTS.md) | Justified revision tested on fresh recovery paths with owned stock/cost. |
| 5 Lead-time/supplier reliability | [Protocol](SUPPLY_SENSITIVITY_V1.md), [results](SUPPLY_SENSITIVITY_RESULTS.md) | Specific unmet supply question; actual supplier truth remains unavailable. |
| 6 Probabilistic protection demand | [Safety protocol](PUBLIC_SAFETY_V1.md), [calibration protocol](PUBLIC_CALIBRATION_V1.md) | Completed origin-known calibration labels, target coverage/pinball and achieved service. |
| 7 Policy comparison | [Protocol](POLICY_COMPARISON_V1.md), [negative/conditional results](POLICY_COMPARISON_RESULTS.md) | Fresh paid warm states and hidden-delay-compatible inputs. |
| 8 Public adapter/provenance | [Assigned protocol](PUBLIC_SALES_PROTOCOL_V1.md), [adapter](PUBLIC_ADAPTER_V1.md) | Preserve identity, source rights and immutable caches; no operational imports. |
| 9 Observed-sales realism | [Forecast protocol](PUBLIC_FORECAST_V1.md), [results](PUBLIC_SALES_RESULTS.md) | Broader/later frozen evidence; sales remain a proxy rather than unconstrained demand. |
| 10 Advanced models | [Intermittent protocol](CONTRACT_INTERMITTENT_V1.md), [results](INTERMITTENT_BENCHMARK.md) | Repeated sealed baseline weakness before ADIDA/IMAPA; feature/license/dependency protocol before global ML. |
| 11 Source provenance | [Lineage protocol](RESEARCH_LINEAGE_V1.md), [integration evidence](RESEARCH_INTEGRATION.md) | Demonstrated missing semantic link; hashes are not signed authenticity. |
| 12 Property/mutation QA | Existing independent controls in `tests/`, [readiness evidence](READINESS_REVIEW.md) | A concrete uncovered invariant; test counts are not a quality target. |
| 13 Backlog versus lost sales | [Contract](CONTRACT_LOST_SALES_V1.md), [paired results](LOST_SALES_RESULTS.md) | Keep permanent losses and owed backlog plus different cost units explicit. |
| 14 Actual planner closed loop | Paused `codex/planner-closed-loop` protocol/unfinished work; see STATE | Preserve action/receipt identity, repeated clocks and actual reliability/supply gates; resume only after scope approval. |
| 15 Physical inventory truth | [Contract](CONTRACT_PHYSICAL_COUNT_V1.md), [results](PHYSICAL_COUNT_RESULTS.md) | Authenticated count/business evidence needed for real truth; no automatic inventory write. |
| 16 Performance/scale | [Engineering investigation](ENGINEERING_READINESS.md), [PLAN](PLAN.md) | Program/host/budget review before a runner; report measured envelope and failures. |
| 17 Multi-location allocation | Existing contract grain is SKU/warehouse; original rationale in retired research | Demonstrated benefit from transfers, then transit/cost/constraints contract. |
| 18 Supplier capacity/calendar | Existing MOQ/pack boundaries; original rationale in retired research | Binding use case and timing contract before extending constraints. |
| 19 Guided demo | [Lab](DECISION_LAB.md), [three-minute case study](PORTFOLIO_CASE_STUDY.md) | Reuse clean/spike/delay/blocked walkthrough; add structure only for a demonstrated UX gap. |
| 20 Accessibility/cold start | [Targeted local review](LAB_ACCESSIBILITY_REVIEW.md) | Speech/zoom/forced colors/download bytes and human cold start remain scoped manual checks. |
| 21 Hosted read-only Lab | [Design evidence](HOSTED_LAB_PLAN.md), [operations](../deploy/lab/README.md) | Actual Linux/runtime/recovery plus reviewed host/domain/cost before public TLS/uptime claims. |
| 22 Portfolio wording | [Case study](PORTFOLIO_CASE_STUDY.md), [historical claim receipt](review/portfolio-claims.json) | Refresh from exact merged/deployed/measured evidence only. |

## Retired plans and checkpoints

The following original documents are retired instead of moving to a maintained
archive folder. Three compatibility paths contain static redirects; RESEARCH_ROADMAP
holds the current linked strategic plan. Other retired paths leave the working tree. Each link is pinned to main
`208d5b3e1a9f2beb78ea94258800dfe4407150c8`; all original bytes, decisions, rationale, commands, handoffs and
checkpoint evidence remain recoverable with `git show <commit>:<path>`.
Existing inbound links use pinned versions or the static redirects. These snapshots
have no current authority. Original frozen contracts/reports are kept in-tree.

| Retired document | Replacement / reason |
|---|---|
| [docs/AUTOMATION_PROGRESS.md](https://github.com/daniel-li2021/inventory-intelligence/blob/208d5b3e1a9f2beb78ea94258800dfe4407150c8/docs/AUTOMATION_PROGRESS.md) | Replaced by STATE; historical checkpoints retained in Git. |
| [docs/RESEARCH_STATUS.md](https://github.com/daniel-li2021/inventory-intelligence/blob/208d5b3e1a9f2beb78ea94258800dfe4407150c8/docs/RESEARCH_STATUS.md) | Delivery snapshots retained in Git; evidence and all 22 questions indexed here. |
| [docs/RESEARCH_ROADMAP.md](https://github.com/daniel-li2021/inventory-intelligence/blob/208d5b3e1a9f2beb78ea94258800dfe4407150c8/docs/RESEARCH_ROADMAP.md) | Original execution priorities retired; current long-term plan is linked in the registry. |
| [docs/READINESS_NEXT_STEPS.md](https://github.com/daniel-li2021/inventory-intelligence/blob/208d5b3e1a9f2beb78ea94258800dfe4407150c8/docs/READINESS_NEXT_STEPS.md) | Earlier priority assessment; decisions retained in DECISIONS. |
| [docs/NEXT_ROUND_RESEARCH.md](https://github.com/daniel-li2021/inventory-intelligence/blob/208d5b3e1a9f2beb78ea94258800dfe4407150c8/docs/NEXT_ROUND_RESEARCH.md) | Earlier investigation; rationale and tentative extensions retained in Git. |
| [docs/STAGE1_PLAN.md](https://github.com/daniel-li2021/inventory-intelligence/blob/208d5b3e1a9f2beb78ea94258800dfe4407150c8/docs/STAGE1_PLAN.md) | Delivered design; contract, data, engine and validation guides retained. |
| [docs/STAGE2_PLAN.md](https://github.com/daniel-li2021/inventory-intelligence/blob/208d5b3e1a9f2beb78ea94258800dfe4407150c8/docs/STAGE2_PLAN.md) | Delivered design; planning contract and operator guide retained. |
| [docs/STAGE3_PLAN.md](https://github.com/daniel-li2021/inventory-intelligence/blob/208d5b3e1a9f2beb78ea94258800dfe4407150c8/docs/STAGE3_PLAN.md) | Delivered design; Copilot contracts, examples and routing evidence retained. |
| [docs/STAGE2_CHECKPOINT.md](https://github.com/daniel-li2021/inventory-intelligence/blob/208d5b3e1a9f2beb78ea94258800dfe4407150c8/docs/STAGE2_CHECKPOINT.md) | Historical slice acceptance; superseded by combined acceptance. |
| [docs/PARALLEL_WORK.md](https://github.com/daniel-li2021/inventory-intelligence/blob/208d5b3e1a9f2beb78ea94258800dfe4407150c8/docs/PARALLEL_WORK.md) | Completed Stage 1 ownership map; no standing agent assignment. |
| [docs/agents/01_DATA.md](https://github.com/daniel-li2021/inventory-intelligence/blob/208d5b3e1a9f2beb78ea94258800dfe4407150c8/docs/agents/01_DATA.md) | Completed Stage 1 data handoff. |
| [docs/agents/02_ENGINE.md](https://github.com/daniel-li2021/inventory-intelligence/blob/208d5b3e1a9f2beb78ea94258800dfe4407150c8/docs/agents/02_ENGINE.md) | Completed Stage 1 engine handoff. |
| [docs/agents/03_VALIDATION.md](https://github.com/daniel-li2021/inventory-intelligence/blob/208d5b3e1a9f2beb78ea94258800dfe4407150c8/docs/agents/03_VALIDATION.md) | Completed Stage 1 validation handoff. |
| [docs/DECISION_LAB_PLAN.md](https://github.com/daniel-li2021/inventory-intelligence/blob/208d5b3e1a9f2beb78ea94258800dfe4407150c8/docs/DECISION_LAB_PLAN.md) | Delivered architecture; reusable API/UX semantics consolidated into DECISION_LAB. |
| [docs/DECISION_LAB_BACKEND.md](https://github.com/daniel-li2021/inventory-intelligence/blob/208d5b3e1a9f2beb78ea94258800dfe4407150c8/docs/DECISION_LAB_BACKEND.md) | Adapter operations consolidated into DECISION_LAB; original notes retained in Git. |
| [docs/DECISION_LAB_FRONTEND.md](https://github.com/daniel-li2021/inventory-intelligence/blob/208d5b3e1a9f2beb78ea94258800dfe4407150c8/docs/DECISION_LAB_FRONTEND.md) | UI behavior consolidated into DECISION_LAB; original notes retained in Git. |
| [docs/ENGINEERING_BENCHMARK_PLAN.md](https://github.com/daniel-li2021/inventory-intelligence/blob/208d5b3e1a9f2beb78ea94258800dfe4407150c8/docs/ENGINEERING_BENCHMARK_PLAN.md) | Promoted without changing proposed workloads/budgets into the single active PLAN. |

## Maintenance rules

- **STATE:** keep short (at most 80 lines), replace stale facts at each phase or
  material checkpoint. Include phase, integrated/measured boundary, preserved active
  work, blockers/next action and the single integration-mode setting. Link evidence
  rather than repeat long test/package histories. No self-referential commit SHA.
- **Plans:** allow distinct short-term, long-term and area files; use descriptive
  names rather than forcing everything into PLAN.md. Link each in the registry
  with scope/status. Each records completed work/evidence, remaining gaps, gates
  and next action. Keep useful completed plans; archive only obsolete/duplicates.
  Superseded plans link replacements. Preserve source-hashed design bytes; record
  evolving follow-up work in a separate linked plan rather than changing evidence.
- **DECISIONS:** add only durable choices and explicit supersession. Tentative
  ideas stay labelled as questions until assigned; old reasoning stays recoverable.
- **Guides/contracts/evidence:** update a guide when behavior changes; version a
  contract when its interface changes. Curate reproducible evidence rather than
  adding routine transcripts/screenshots or generated logs. Immutable artifacts
  never become a mutable progress record.
- **Index:** update plan links and lifecycle status when work starts, pauses,
  completes or is superseded; also track knowledge/evidence additions and retirement.
  Keep detailed progress in its plan; current focus/mode remain only in STATE.
- **Validation:** run `python3 scripts/check_docs.py` and whitespace/metadata checks;
  use focused behavior/provenance checks only when affected. CI hygiene checks local
  Markdown targets, heading fragments and the canonical mode/state size.
