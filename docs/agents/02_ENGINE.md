# Agent 2 — reliability engine

Implement only milestone 1's reliability engine in an isolated worktree. Read root `AGENTS.md`, `docs/CONTRACT_V1.md`, and `docs/PARALLEL_WORK.md`. Begin from `contract-v1` on `codex/stage1-engine`.

Own only `src/inventory_intelligence/**`, `pyproject.toml`, `sql/views.sql`, `sql/checks.sql`, and `docs/ENGINE.md`. Do not edit schema, generator/Compose, independent tests/CI, root README, or the contract.

Deliver `run_checks` and the CLI/report interfaces exactly as frozen. Implement R001–R005 using SQL and minimal Python/Psycopg orchestration. Use Repeatable Read, preserve input provenance and previous runs, suppress unsupported quantity conclusions, and retain explicit pass/fail/not-assessable outcomes. Runtime never initializes, reloads, or repairs source tables. Pin the selected Psycopg 3 dependency; do not introduce an ORM or quality framework.

Before the data branch is available, prepare against the documented table/API interface. Integrate the foundation to run real database validation when available; do not claim unrun integration succeeded. Put any small local engine self-check in your owned paths; Agent 3 independently verifies the complete behavior.

Document installation, CLI examples, error/exit behavior, and implementation limitations in `docs/ENGINE.md`. Commit focused changes on your branch and report the SHA and actual checks. Do not merge to main or privately alter rule IDs, report fields, or temporal semantics.
