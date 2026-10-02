# Agent 3 — independent validation and delivery

Implement milestone 1's independent acceptance suite and delivery workflow in an isolated worktree. Read root `AGENTS.md`, `docs/CONTRACT_V1.md`, and `docs/PARALLEL_WORK.md`. Begin from `contract-v1` on `codex/stage1-validation`.

Own only `tests/**`, `.github/workflows/ci.yml`, `README.md`, `docs/examples/**`, and `docs/VALIDATION.md`. Do not edit source schema/generator, engine/package/SQL, or the contract. Report defects to the owning path rather than patching another agent's files.

Write a manually calculated golden case and exact expected findings independently of checker output. Test clean controls and each known fault, null/suppressed deltas for unassessable inventory, inclusive/exclusive cutoff edges, missing/incomplete batches, conflicting duplicates, repeat-run semantic stability/history, and operational read-only role enforcement. Use standard-library unittest against actual PostgreSQL, not SQLite or mocks for SQL semantics.

Prepare tests/oracles/CI against the frozen APIs concurrently. Final execution requires the data and engine commits; integrate those reviewed branches into this checkout before reporting acceptance. Do not convert absent modules/database or skipped tests into green milestone evidence.

Extend the existing hygiene workflow with a real PostgreSQL integration job and reproducible dependency installation. Demonstrate intentional dirty-data detection as passing assertions, retain CLI exit 1 for bad/unassessable data, and update the quickstart plus a small verified example report. No deployment/scheduled jobs or new dashboard.

Commit focused changes on your branch and report exact commands/results, upstream commits integrated, and remaining limitations. Do not independently merge/push integration to main; report the merge-ready milestone to the coordinator.
