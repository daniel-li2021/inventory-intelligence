# Three parallel implementation paths

The owner requested prepared handoffs, not agent launches. No implementation agents have been started. All three begin from the same frozen `contract-v1` Git tag and read [CONTRACT_V1.md](CONTRACT_V1.md) first.

1. **Data foundation** — branch `codex/stage1-data`; [handoff](agents/01_DATA.md). Owns `sql/schema.sql`, `compose.yaml`, `synthetic/**`, `.env.example`, and `docs/DATA.md`.
2. **Reliability engine** — branch `codex/stage1-engine`; [handoff](agents/02_ENGINE.md). Owns `src/inventory_intelligence/**`, `pyproject.toml`, `sql/views.sql`, `sql/checks.sql`, and `docs/ENGINE.md`.
3. **Independent validation and delivery** — branch `codex/stage1-validation`; [handoff](agents/03_VALIDATION.md). Owns `tests/**`, `.github/workflows/ci.yml`, `README.md`, `docs/examples/**`, and `docs/VALIDATION.md`.

Use separate worktrees/checkouts for the three agents. Do not run them in one shared mutable checkout. Worktree parent locations are an operator choice; create them when the agents are actually started. Use unique Compose project names/database instances so resets and test data cannot collide.

## Coordination

- Prepare on the frozen interfaces concurrently: Agent 1 supplies inputs/schema, Agent 2 supplies the runner/report, Agent 3 writes its independent oracle/tests and CI. Agent 3 must not derive expected findings from Agent 2's output.
- No agent edits another agent's owned paths or the frozen contract. Each updates its own documentation. Root/shared documentation is integrated by the validation owner or coordinator.
- Agent 2 can validate SQL shape/logic locally before the foundation lands; Agent 3 can prepare fixture arithmetic, exact assertions, and CI before the modules are available. They must disclose that integration is pending, not mark skipped tests as proof of completion.
- Final database integration has dependencies: merge/reconcile the data and engine branches into the validation checkout, then run the actual PostgreSQL suite. Parallel authoring does not make this final validation independent.
- Each agent commits focused changes on its assigned branch, reports validation and limitations, and opens a draft PR when requested. No independent merge to main, force push, or contract edits.
- The coordinator combines reviewed branches, resolves only genuine integration issues, verifies the fresh-database demo and exact failure suite, then publishes the milestone through a PR.

The three working branch names are reserved for these handoffs. The `contract-v1` tag is the immutable interface baseline; do not move it. Future compatible internal changes use normal commits; interface changes get an explicit new contract revision.
