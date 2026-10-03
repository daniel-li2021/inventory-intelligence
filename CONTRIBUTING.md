# Development workflow

## Current phase

All three bounded synthetic stages, decision/intermittent research and the local
Decision Lab are integrated on `main`. See the
[current independent review and fresh acceptance](docs/READINESS_REVIEW.md).
Earlier 79/106/124-test results remain historical checkpoints. The
[frozen milestone 1 contract](docs/CONTRACT_V1.md) remains separate from planning
and copilot contracts. See [current status](docs/AUTOMATION_PROGRESS.md) and
[current next-step investigation](docs/READINESS_NEXT_STEPS.md). Research proposals are not
implementation handoffs; public real data requires an explicit separate boundary
decision before import under the current synthetic-only project instructions.

## GitHub bootstrap

The project has its own local Git repository, independent of its parent folder. The bootstrap commit goes on `main`. Subsequent parallel or nontrivial changes use short-lived `codex/<task>` branches or isolated worktrees. Task branches do **not** open pull requests by default; an integration owner combines validated work and decides whether the batch needs one integration PR or can be merged directly.

Destination: [daniel-li2021/inventory-intelligence](https://github.com/daniel-li2021/inventory-intelligence), public. Its initial README history is preserved when integrating the research bootstrap.

Bootstrap and subsequent configuration:

1. Verify the destination owner, repository, visibility, and existing history before adding `origin`.
2. For an empty destination, push local `main` with upstream tracking. For an initialized destination, fetch and integrate its initial files/history deliberately; never force-push over it.
3. Verify the remote commit. The repository CI workflow activates on GitHub after publication.
4. Protect `main` from force pushes and accidental deletion. Do not require a pull request for every solo-agent change; use CI and the integration-owner checks below as the default gate.
5. Use one integration PR when a batch changes shared contracts/schema, adds a dependency or public-data boundary, introduces a milestone-sized feature, or benefits from a pre-main GitHub review surface. Small validated fixes and documentation changes may be integrated directly.

The repository URL and connected GitHub access are verified. Branch protection/settings remain recommendations until explicitly verified on the remote; a workflow file alone does not configure them. Do not wait for CI after routine pushes.

## Each change

Confirm the repository root and inspect status. When a remote exists:

```sh
git fetch origin
git switch -c codex/<task> origin/main
```

If the checkout has unrelated modifications or another task is using it, leave that work intact and use a clean worktree. Keep each task commit focused. Sub-agents commit their isolated changes; the integration owner controls publication and PR creation. Do not mix generated report refreshes with unrelated refactors.

Before committing, inspect explicit staged paths and the staged diff:

```sh
git diff --cached --check
git diff --cached
python3 -m json.tool docs/research/repositories.json > /dev/null
```

Run checks appropriate to the change. Update README/operator instructions and the affected design documentation in the same task or integration batch. Document what changed, why, validation, and material limitations.

Fetch again before pushing and compare the branch with current `origin/main`. Integrate new main commits if needed, rerun affected checks, then push and verify the remote branch SHA. The integration owner reviews task commits/diffs, resolves straightforward conflicts, runs the relevant combined acceptance, and merges or cherry-picks coherent work into an integration branch or directly into `main` when safe. Do not let multiple sub-agents write `main` concurrently. Use one integration PR only when the change class above warrants it; otherwise direct integration is allowed under the owner's standing authorization. Before each task, fetch with pruning and inspect existing branches. After integration, verify remote `main`, then remove merged task branches/worktrees when safe. Preserve dirty/active work and needed environments. Keep commits focused without rewriting published history for cleanup.

## Integration policy

Use branches/worktrees for **isolation**, not as a requirement to create one PR per agent.

Default multi-agent flow:

1. Each sub-agent starts from current `origin/main`, works in its own `codex/<task>` branch/worktree, runs focused tests and commits.
2. Sub-agents do not open PRs by default and do not write directly to `main`.
3. One integration owner reviews all candidate commits, rebases/merges current `main` as needed, resolves conflicts, and runs combined acceptance.
4. If the batch is small and low risk, the integration owner may fast-forward/merge/cherry-pick the validated work to `main` directly, push and verify the remote ref. Monitor CI only when specifically required or a failure is evident.
5. Use a single integration PR before `main` for shared contract/schema changes, dependency/model changes, public-data/license boundary changes, major milestone batches, or whenever pre-main CI/review materially reduces risk.
6. If integration or CI exposes a defect, fix the defect in the integration branch, rerun the relevant acceptance, and only then update `main`.

Prefer a small number of meaningful integration boundaries over one PR per sub-agent. PR count is not a quality metric; reproducible acceptance evidence is.

## CI policy

The initial `Repository hygiene` job validates whitespace across the submitted change and parses the research JSON. It needs no secrets or package installation. Actions are pinned to commit SHAs and the workflow token has read-only repository access, following [GitHub's secure-use guidance](https://docs.github.com/en/actions/reference/security/secure-use).

The **first implementation PR** must introduce a PostgreSQL service, install reviewed/pinned Python dependencies, and run the same inventory tests locally and in CI. Use standard-library `unittest` initially. Tests must fail on missed faults, unexpected clean-data findings, wrong record IDs, and wrong quantity deltas. Intentionally dirty demo data is a successful test when the expected findings match; running the checker normally against dirty data should return a nonzero findings status.

No scheduled data pipeline, deployment pipeline, external business database, or paid/cloud service is needed for Stage 1. Do not add placeholders that pass without executing inventory tests.

## Scheduled development

Two daily Codex app schedules return to the project coordination chat, using Pacific time (`America/Los_Angeles`):

| Time | Automation | Work |
| --- | --- | --- |
| 3:30 AM | Inventory overnight build | Resume unfinished work, fix failures, integrate validated changes, and continue the next ready milestone with a durable goal. |
| 9:20 AM | Inventory morning review | Check overnight progress and publication, review correctness, finish remaining work, and investigate unresolved risks. |

The owner authorizes this coordination agent to commit, push, and merge validated project work into `main` without another approval. Preserve other agents' unfinished work and use isolated worktrees when paths overlap. This authorization does not permit force pushes, discarding work, or merging unrelated changes. Follow the existing Git and validation checks above.

Record resumable checkpoints in `docs/AUTOMATION_PROGRESS.md` as work proceeds: completed work, commit references, validation, blockers, and the next action. Continue an existing goal before creating another. Finish Stage 1 acceptance before starting Forecasting & Planning; preserve `contract-v1` and document subsequent contracts separately.

The requested five-hour work window is a preference for sustained useful work, not a supported goal timer or guaranteed runtime. Goals continue according to completion, usage limits, and tool availability. Local scheduled work requires the computer awake, the app running, and the repository available. Manage schedules in the app; they are not GitHub Actions or repository-hosted cron jobs.

## Data and dependencies

Keep synthetic fixtures small, deterministic, and versioned. Keep generated reports and local environments out of Git unless a small curated sample is intentionally added with its generation command. Fixtures must remain independent of checker output.

Add a dependency only for a demonstrated need; record its version, license, and purpose. Original MIT licensing does not change upstream licensing. Do not copy GPL/AGPL ERP implementations into the project as if they were original MIT code. Credentials belong in ignored local configuration or GitHub secrets, never fixtures or reports.
