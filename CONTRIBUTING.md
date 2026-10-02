# Development workflow

## Current phase

The [frozen milestone 1 contract](docs/CONTRACT_V1.md) is implemented and independently validated. See the [completion review](docs/STAGE1_REVIEW.md). The three handoffs are integrated; they no longer describe separate pending implementations.

## GitHub bootstrap

The project has its own local Git repository, independent of its parent folder. The bootstrap commit goes on `main`; subsequent changes use short-lived `codex/<task>` branches and pull requests.

Destination: [daniel-li2021/inventory-intelligence](https://github.com/daniel-li2021/inventory-intelligence), public. Its initial README history is preserved when integrating the research bootstrap.

Bootstrap and subsequent configuration:

1. Verify the destination owner, repository, visibility, and existing history before adding `origin`.
2. For an empty destination, push local `main` with upstream tracking. For an initialized destination, fetch and integrate its initial files/history deliberately; never force-push over it.
3. Verify the remote commit. The repository CI workflow activates on GitHub after publication.
4. Configure a `main` ruleset requiring pull requests and the `Repository hygiene` status check, blocking force pushes and branch deletion. For solo work, require zero external approvals so self-authored PRs are usable. Register the check after its first GitHub run.
5. Prefer squash merging and automatic deletion of merged branches. Add the PostgreSQL integration check to required checks when milestone 1 introduces it.

The repository URL and connected GitHub access are verified. Branch protection/settings remain recommendations until explicitly verified on the remote; a workflow file alone does not configure them. Do not wait for CI after routine pushes.

## Each change

Confirm the repository root and inspect status. When a remote exists:

```sh
git fetch origin
git switch -c codex/<task> origin/main
```

If the checkout has unrelated modifications or another task is using it, leave that work intact and use a clean worktree. Keep each PR to one reviewable behavior; do not mix generated report refreshes with unrelated refactors.

Before committing, inspect explicit staged paths and the staged diff:

```sh
git diff --cached --check
git diff --cached
python3 -m json.tool docs/research/repositories.json > /dev/null
```

Run checks appropriate to the change. Update README/operator instructions and the affected design documentation in the same PR. Document what changed, why, validation, and material limitations.

Fetch again before pushing and compare the branch with current `origin/main`. Integrate new main commits if needed, rerun affected checks, then push. Verify the remote branch SHA; do not routinely wait for CI. Merging or publishing a deployment requires authorization covering that action. Before each task, fetch with pruning and inspect existing branches. After an authorized merge, verify the remote main commit and ancestry, remove merged task branches locally/remotely, and retire clean temporary worktrees. Preserve dirty/active work and needed environments. Keep commits focused without rewriting published history for cleanup.

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
