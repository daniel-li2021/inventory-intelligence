# Project documentation

[STATE](STATE.md) is the short current phase, integration mode and next action.

| Home | Purpose |
|---|---|
| [Project overview](../README.md) | What the project does and how to try it. |
| [KB](KB.md) | What we know: constraints, lessons, open questions and data rights. |
| [DECISIONS](DECISIONS.md) | Why choices were made, including explicit supersession. |
| [RESULTS](RESULTS.md) | Measured outcomes, independent examples and limitations. |
| [EVIDENCE](EVIDENCE.md) | Immutable reports, original Git source views and audit reproduction. |
| [CONTRACTS](CONTRACTS.md) | Current interfaces/version identifiers; inventory, planning, Copilot and research kernels. |
| [OPERATIONS](OPERATIONS.md) | Current fixture, reliability and planning commands. |
| [Product / Lab](DECISION_LAB.md) / [hosting](../deploy/lab/README.md) | API/UX, packaged evidence, serving and rollback. |
| [Synthetic replay / insights V2](SYNTHETIC_REPLAY.md) | Controlled local intake, immutable versions, discovery rules, one-review comparisons and walkthrough. |
| [Actual planner execution / feedback](PLANNER_EXECUTION.md) | Completed frozen protocols, arithmetic erratum, measured actual execution and durable-journal reproduction guide. |
| [Engineering pilot](RESULTS.md#local-engineering-pilot) / [reproduction](EVIDENCE.md#local-engineering-pilot) | Local exploratory measurements, limits and pending confirmation. |
| [Engineering continuation](RESULTS.md#engineering-continuation) / [receipts](EVIDENCE.md#engineering-continuation) | Paired SQL improvement, scale/ARM64/runtime/recovery evidence and explicit remaining gates. |
| [VALIDATION](VALIDATION.md) | Independent checks and disposable-database acceptance. |
| [CONTRIBUTING](../CONTRIBUTING.md) | Concise delivery workflow and AUTO/REVIEW. |

## Plans and work status

| Active plan | Scope / status | Next action |
|---|---|---|
| [Master product and engineering plan](ROADMAP.md) | Full local synthetic A–F assignment; O01–O25 audited against implementation/evidence | Independent datasets/insights, feasible suppliers, donor-safe transfers, fresh policy evidence and cohesive product acceptance. |
| [Engineering reference protocol](PLAN.md) | Retained uncompleted reference/stability cells; measured local evidence unchanged | Available PostgreSQL17/current regression and necessary engineering under ROADMAP; x86/two-date/human/public gates stay explicit. |

Only these two documents own pending execution. PLANNER_EXECUTION is a durable
completed guide, not an ongoing plan. Keep another plan only when concrete future
execution needs it; extract completed facts into KB, guides, RESULTS and EVIDENCE.
The full user assignment supersedes the earlier two-increment/paused feature scope;
AUTO integrates validated assigned work. Public/paid deployment and real operational
intake remain excluded. Preserve original unmerged planner controls as STATE directs.

## Maintenance rules

Update STATE after each phase/material checkpoint. Update affected guides, decisions,
results and evidence where they belong. When a plan/review/investigation completes
or becomes superseded, extract useful facts and delete it; Git retains original
history. No archives, compatibility stubs or completed-plan exceptions in the
maintained surface. Preserve original artifact bytes and source ancestry, not
redundant documents. Historical audits use original Git snapshots; current checks
stay separate. Run `python3 scripts/check_docs.py` after navigation changes.
