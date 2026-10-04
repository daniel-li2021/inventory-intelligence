# Current project state

Updated: 2026-10-04 (America/Los_Angeles). Replace stale facts after each phase or
material checkpoint; link evidence instead of appending a progress diary.

Integration mode: AUTO

Phase: engineering readiness; local continuation complete as practical; reference/stability/release gates pending.
Features remain paused. The user assigned the remaining benchmark checks and one
evidence-led optimization on October 4, selecting available local runtimes only.
Native batch/scale checks, five fresh ARM64 Linux campaigns and timed JIT diagnosis
are complete. One full continuous HTTP window and verified app crash passed;
short/discontinuous/interrupted attempts remain excluded from stability confirmation.
Wall-clock discontinuities caused the three-hour target to overrun; measurements
stopped and clock guards/journaling were repaired. Paid deployment and planner
feature resumption require their own scope decision.

## Integrated and measured

- Core reliability, advisory planning, read-only Copilot, synthetic Lab and separate
  research packages are integrated (PRs 14–26; pre-cleanup baseline `208d5b3`).
- Retained remote correctness acceptance: 240 tests / OK plus hygiene at `9d7c55f`.
  [CI/source receipt](review/engineering-readiness-baseline.json),
  [separate local combined acceptance](EVIDENCE.md#acceptance-history).
- [Local engineering pilot](RESULTS.md#local-engineering-pilot): scoped batch/reader,
  planning/backtest, short native HTTP and small recovery evidence recorded.
  [Continuation](RESULTS.md#engineering-continuation): one identical-workload SQL
  optimization (~12x), 1M upper tier, serial100/backtest/defect grids, ARM64 Linux
  enforcement and scaled recovery. Sixty-three focused regressions plus six
  postcommit lineage checks passed ([receipt](review/engineering-continuation-v1/postcommit-validation.json)).
  Reference/stable capacity, public hosting and production benefit remain
  unverified; [gaps](KB.md#engineering-gaps-and-hypotheses).
- Current knowledge, choices, results and evidence are consolidated; completed
  plans/protocol narratives and compatibility stubs are removed. Historical source
  bytes remain in Git, and original result/receipt bytes remain unchanged.

## Active work and next action

- [Engineering plan](PLAN.md): remaining continuity-verified HTTP/rate/client,
  x86/two-date, dense-evidence, serial1000 and independent human checks.
  ARM64 one-date results do not complete the reference gate; Linux JIT tuning
  needs a separate comparison after the assigned single optimization.
  Other research possibilities remain conditional knowledge, not active plans.
  [Registry](README.md#plans-and-work-status).
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
