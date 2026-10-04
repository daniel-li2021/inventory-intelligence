# Current project state

Updated: 2026-10-03 (America/Los_Angeles). Update this file after each phase or
material checkpoint; replace stale facts rather than append a progress diary.

Integration mode: AUTO

Phase: engineering readiness design (P0 complete; P1 awaiting program review).
Feature development is paused. Documentation/workflow cleanup is authorized;
it does not approve benchmark execution, resume planner features or deploy a host.

## Integrated and measured

- Baseline: main `208d5b3` (PRs 14–26 integrated before this documentation change).
  Core reliability, advisory planning, read-only Copilot, local synthetic Lab,
  separate decision/public-sales/lost-sales/physical-count research are integrated.
- Recorded remote correctness acceptance: **240 tests / OK**, hygiene success on
  `9d7c55f`; [exact CI observation](review/engineering-readiness-baseline.json).
  This is retained evidence for that commit, not a fresh run on this change.
  [Local combined acceptance](RESEARCH_INTEGRATION.md) remains separate.
- Engineering assessment and proposed workload/budget are complete; no controlled
  capacity benchmark or production/business benefit is measured. Public hosting,
  Linux container enforcement and recovery remain unverified.

## Active work and next action

- [PLAN](PLAN.md): review workload, SLO, environment and pilot budget before P1
  implementation. Missing runtime gates stay explicit; no automatic feature resume.
- Preserve paused `codex/planner-closed-loop` protocol commits `55f4170` / `538d29d`
  and its unfinished scripts, adapter, fixture and tests. They are unmerged and
  excluded from accepted main evidence; never delete or absorb them during cleanup.
- Documentation cleanup validated: 17 snapshots retired to pinned Git links;
  local navigation/mode controls, 6 lineage regressions and retained-report hash
  checks pass. All 13 source-hashed protocols and 116 tracked
  reports/receipts/metadata/core/fixtures/oracles remain byte-identical. No database
  suite, model call or study replay was needed.

## Boundaries and navigation

Operational demo inputs are synthetic. Approved UCI observed-sales research is a
separate offline boundary with ignored raw/derived data and aggregate publication;
it is not accepted-order demand, verified stock or operational-import permission.
No source repair, order execution or paid deployment is authorized by AUTO.

Read [workflow](../CONTRIBUTING.md), [decisions](DECISIONS.md), and
[knowledge/evidence index](README.md) only as needed after this file and PLAN.
To switch persistently, say **“Switch to REVIEW”** or **“Switch to AUTO”**; change
only the mode line here. REVIEW prepares validated work and stops before merge.
