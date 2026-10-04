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
| [Lab](DECISION_LAB.md) / [hosting](../deploy/lab/README.md) | API/UX, packaged evidence, serving and rollback. |
| [VALIDATION](VALIDATION.md) | Independent checks and disposable-database acceptance. |
| [CONTRIBUTING](../CONTRIBUTING.md) | Concise delivery workflow and AUTO/REVIEW. |

## Plans and work status

| Active plan | Scope / status | Next action |
|---|---|---|
| [Engineering readiness](PLAN.md) | Pending execution; P0 complete, P1 awaits program review | Review workload/SLO, environment and pilot budget. |

Keep another plan only when concrete future execution needs it; index its scope,
status, gaps and next action here. Ideas and deferred possibilities belong in KB.
The paused unmerged planner checkout is identified in STATE, not an accepted plan.

## Maintenance rules

Update STATE after each phase/material checkpoint. Update affected guides, decisions,
results and evidence where they belong. When a plan/review/investigation completes
or becomes superseded, extract useful facts and delete it; Git retains original
history. No archives, compatibility stubs or completed-plan exceptions in the
maintained surface. Preserve original artifact bytes and source ancestry, not
redundant documents. Historical audits use original Git snapshots; current checks
stay separate. Run `python3 scripts/check_docs.py` after navigation changes.
