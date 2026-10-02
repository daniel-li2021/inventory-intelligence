# Project instructions

Optimize for correctness and token efficiency.

- Start with the smallest relevant surface. Inspect the responsible file/function before exploring broadly.
- Read each file once when practical; use targeted searches and narrow ranges afterward.
- Trace actual callers and data flow before changing shared behavior. Fix root causes.
- Keep scope tight. Do not inspect or modify unrelated pipelines, workflows, tests, configuration, or architecture.
- Reuse valid outputs, caches, scores, and prior results. Avoid unnecessary recomputation.
- Avoid expensive crawlers, full pipelines, full test suites, builds, and external API/LLM calls unless necessary for correctness.
- Prefer focused edits and targeted validation. Use existing helpers, SQL, the standard library, and native database features before new dependencies or abstractions.
- Once behavior is implemented and sufficiently validated, stop. Do not add unrelated refactors or cleanup.
- Keep narration minimal and final summaries concise.
- Update relevant documentation after completing a task.

## Project boundaries

- Milestone 1 follows `docs/CONTRACT_V1.md`. Use the path ownership and interfaces in `docs/PARALLEL_WORK.md`; do not change shared contracts independently. Begin implementation only when assigned an implementation handoff.
- Public portfolio: synthetic business data only. Never import company code, data, screenshots, credentials, or confidential schema.
- Read operational inputs; write reliability results separately. Do not silently repair source inventory.
- Preserve source identity, evidence, business timestamps, and ingestion timestamps. Missing or incomplete data must not become zero or a pass.
- Test reconciliation against independent expected outcomes, including clean controls. A count-only assertion is insufficient.
- Keep inventory quantities exact. Stage 1 starts with finished garments measured in whole pieces.

## Git workflow

- Verify `git rev-parse --show-toplevel`, status, branch, and remote before editing. Work only in this project's repository.
- When `origin` exists, fetch it and start work on `codex/<task>` from current `origin/main`.
- Preserve unrelated dirty work. Use a clean worktree when isolation is needed; do not create one by default.
- Stage explicit project files, inspect the staged diff, run focused checks, and commit a clear problem-oriented change.
- Before pushing, fetch again and compare against current `origin/main`; reconcile upstream changes without overwriting others' work.
- Verify the pushed remote ref. Do not wait for or continuously monitor CI after a push unless CI/deployment validation is requested or a failure is evident.
- Before work, prune stale remote refs and inspect existing branches. Keep commits focused; do not rewrite published history merely for tidiness.
- After an authorized merge, verify that remote `main` contains the work, then remove merged task branches locally and remotely and retire clean temporary worktrees. Preserve active branches, dirty work, and required local environments; never force-delete unmerged work.
- Do not force-push, delete work, or merge a PR without authorization covering that action.
- Keep these shared instructions in this file; avoid duplicating them in editor-specific always-on rules.
