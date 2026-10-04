# Current project state

Updated: 2026-10-03 (America/Los_Angeles). Replace stale facts after each phase or
material checkpoint; link evidence instead of appending a progress diary.

Integration mode: AUTO

Phase: engineering readiness design; P0 complete, P1 awaiting program review.
Features are paused. Documentation cleanup is authorized; benchmark execution,
planner feature resumption and paid deployment require their own scope decision.

## Integrated and measured

- Core reliability, advisory planning, read-only Copilot, synthetic Lab and separate
  research packages are integrated (PRs 14–26; pre-cleanup baseline `208d5b3`).
- Retained remote correctness acceptance: 240 tests / OK plus hygiene at `9d7c55f`.
  [CI/source receipt](review/engineering-readiness-baseline.json),
  [separate local combined acceptance](EVIDENCE.md#acceptance-history).
- No controlled capacity or production/business benefit is measured. Public hosting,
  Linux enforcement and recovery remain unverified; [gaps](KB.md#engineering-gaps-and-hypotheses).
- Current knowledge, choices, results and evidence are consolidated; completed
  plans/protocol narratives and compatibility stubs are removed. Historical source
  bytes remain in Git, and original result/receipt bytes remain unchanged.

## Active work and next action

- [Engineering plan](PLAN.md): review workload/SLO, environment and pilot budget
  before P1 runner implementation. Other [research possibilities](KB.md#retained-research-questions-and-tentative-extensions)
  remain conditional knowledge, not active plans. [Registry](README.md#plans-and-work-status).
- Preserve unmerged planner protocol commits `55f4170` / `538d29d` and unfinished
  scripts/adapter/fixture/tests in `/private/tmp/ii-planner-closed-loop` on
  `codex/planner-closed-loop`. They are excluded from accepted main evidence.
- After each merge, verify remote main, return the primary checkout to current main
  and retire the completed local task branch/clean worktree. Integrated original tips
  from earlier branch cleanup remain in local `archive/integrated/*` tags.

## Boundaries and navigation

Operational inputs are synthetic. The UCI exception is offline observed-sales
research with ignored raw/reconstructable data and aggregate attribution, not
accepted-order demand, verified stock or operational-import permission.

Read [workflow](../CONTRIBUTING.md), [index](README.md), [decisions](DECISIONS.md).
Say “Switch to REVIEW” or “Switch to AUTO” to persistently update the mode line.
