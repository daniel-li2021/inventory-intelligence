# Knowledge and evidence index

Read [STATE](STATE.md) for current focus/mode. This index routes knowledge;
[DECISIONS](DECISIONS.md) preserves reasoning/supersession and
[CONTRIBUTING](../CONTRIBUTING.md) describes delivery.

## Plans and work status

Multiple plans can cover different areas or horizons; each owns completed outcomes,
remaining gaps and next action. Work one assigned task at a time.

| Plan | Scope / status | Next action |
|---|---|---|
| [Engineering readiness](PLAN.md) | Near-term; P0 complete, P1 awaiting program review | Review workload/SLO, environment and pilot budget before runner implementation. |
| [Research roadmap](RESEARCH_ROADMAP.md) | Long-term; ongoing, feature execution paused | Resolve engineering gate, then select one evidence-backed follow-up. |

[Hosted Lab design](HOSTED_LAB_PLAN.md) is completed source-bound evidence, not a
second progress ledger. Its open runtime/recovery/release gaps are in PLAN and
[deployment operations](../deploy/lab/README.md).

## Durable knowledge and operations

| Home | Content |
|---|---|
| [KB](KB.md) | Correctness/trust boundaries, engineering gaps/hypotheses, tool lessons, all 22 tentative research questions. |
| [RESULTS](RESULTS.md) | Core forecasts, planner/simulator oracles, historical timings, Copilot routing/fidelity, browser/accessibility measurements. |
| [EVIDENCE](EVIDENCE.md) | Acceptance history, original source/audit reproduction, CI incidents and extraction map. |
| Inventory | [Contract](CONTRACT_V1.md), [data](DATA.md), [engine](ENGINE.md), [validation](VALIDATION.md), [example](examples/combined.md). |
| Planning | [Contract](CONTRACT_PLANNING_V1.md), [operations](PLANNING.md), [example](examples/stage2.md). |
| Copilot | [Original contract](CONTRACT_COPILOT_V1.md), [additive contract](CONTRACT_COPILOT_V2.md), [examples](examples/copilot.md). |
| Lab / hosting | [Architecture/API/UX](DECISION_LAB.md), [source-bound design](HOSTED_LAB_PLAN.md), [deployment/rollback](../deploy/lab/README.md). |
| Portfolio | [Case study and scoped wording](PORTFOLIO_CASE_STUDY.md), [pinned source metadata](research/repositories.json). |

## Research results

These are durable study reports and frozen protocols, not ongoing plans. Keep
negative/conditional outcomes, consumed holdouts and undefined denominators explicit.

| Study | Protocol / result |
|---|---|
| Decisions | [Contract](CONTRACT_DECISION_V1.md), [benchmark](DECISION_BENCHMARK.md). |
| Intermittent demand | [Contract](CONTRACT_INTERMITTENT_V1.md), [benchmark](INTERMITTENT_BENCHMARK.md). |
| Warmup / feasibility | [Warmup](RESEARCH_WARMUP_V1.md), [result](FRESH_WARMUP_RESULTS.md); [diagnostic](FEASIBILITY_DIAGNOSTIC.md), [result](FEASIBILITY_DIAGNOSTIC_RESULTS.md). |
| Retention | [Protocol](SAFETY_RETENTION_V1.md), [negative result](SAFETY_RETENTION_RESULTS.md). |
| Supply / policy | [Supply](SUPPLY_SENSITIVITY_V1.md), [result](SUPPLY_SENSITIVITY_RESULTS.md); [policy](POLICY_COMPARISON_V1.md), [result](POLICY_COMPARISON_RESULTS.md). |
| Public observed sales | [Source rights/boundary](PUBLIC_SALES_PROTOCOL_V1.md), [adapter](PUBLIC_ADAPTER_V1.md), [forecast protocol](PUBLIC_FORECAST_V1.md), [result](PUBLIC_SALES_RESULTS.md). |
| Public safety / calibration | [Safety](PUBLIC_SAFETY_V1.md), [result](PUBLIC_SAFETY_RESULTS.md); [disjoint calibration](PUBLIC_CALIBRATION_V1.md), [result](PUBLIC_CALIBRATION_RESULTS.md). |
| Lost sales | [Contract](CONTRACT_LOST_SALES_V1.md), [paired result](LOST_SALES_RESULTS.md). |
| Physical counts | [Contract](CONTRACT_PHYSICAL_COUNT_V1.md), [result](PHYSICAL_COUNT_RESULTS.md), [input example](examples/physical-count-inputs-v1.json). |
| Repository lineage | [Protocol](RESEARCH_LINEAGE_V1.md), [saved manifest](review/research-integration-lineage-v1.json), [reproduction](EVIDENCE.md#reproduce-without-rewriting-evidence). |

## Evidence and reproducibility

Keep original reports/receipts/source snapshots, independent oracles, frozen protocols
and required ignored caches. `review/` contains immutable observations. Current drift
is declared, not rehashed away. Run historical audits in their complete original Git
view; current regression is separate. [Details](EVIDENCE.md).

## Retired plans and checkpoints

Completed reviews/investigations are extracted into KB, RESULTS and EVIDENCE, then
removed. [Extraction map and source-bound link exceptions](EVIDENCE.md#retired-plans-and-checkpoints).
Old narratives remain recoverable in Git; useful knowledge is available here.

## Maintenance rules

- Keep STATE under 80 lines; replace stale phase/focus/gates at material checkpoints.
- Index each ongoing plan with scope/status. Record completed outcomes, remaining gaps
  and next action. On completion migrate durable information and remove the task file;
  keep a plan only for active work or genuine source-bound reproducibility.
- Update affected guides/results; record enduring choices with explicit supersession
  in DECISIONS. Do not add duplicate progress diaries or per-agent handoff documents.
- Preserve immutable artifact bytes and accepted contract versions. Evolving follow-up
  work belongs in an indexed plan, never a rewritten historical protocol.
- Check documentation links/mode/state size with `python3 scripts/check_docs.py`.
