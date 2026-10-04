# Development workflow

Read [STATE](docs/STATE.md), then the relevant indexed [plan or guide](docs/README.md).
Historical evidence and proposals do not assign implementation work.

## Integration modes

STATE holds the single setting `Integration mode: AUTO` or `Integration mode: REVIEW`.
“Switch to AUTO/REVIEW” updates that line and persists across tasks.

| Mode | After validation and diff review |
|---|---|
| AUTO | Merge authorized work into current main, push and verify the remote ref. |
| REVIEW | Prepare a validated commit and reviewable branch/diff; stop before merge. |

PRs are optional review surfaces. An explicit task-specific merge instruction may
authorize that merge. Neither mode expands scope or clears data, benchmark or
paid-deployment gates.

## Deliver a change

1. Verify repository, status, branch and remote; fetch with pruning. Start nontrivial
   work on `codex/<task>` from current `origin/main`. Isolate only when needed.
2. Implement the assigned scope, preserve contracts and unrelated work, and run
   focused checks. Use [VALIDATION](docs/VALIDATION.md) for fresh PostgreSQL acceptance;
   reuse original study bytes and caches rather than rerunning consumed experiments.
3. Update STATE, the affected plan and guides. Index ongoing plans with scope/status;
   record outcomes and remaining gaps, then extract durable material and remove stale
   task documents. Record enduring choices and supersession in [DECISIONS](docs/DECISIONS.md).
4. Stage explicit files and inspect the staged diff. Fetch again, reconcile upstream
   changes and re-read the mode in current main before integration. Verify pushed refs
   with `git ls-remote`; never rewrite published history. After a merge, return the
   primary checkout to current main, delete the completed local branch with
   `git branch -d`, and retire its clean disposable worktree. Preserve active, dirty
   or unmerged work and required environments. No routine CI polling after push.

For documentation-only changes:

```sh
python3 scripts/check_docs.py
python3 -m json.tool docs/research/repositories.json > /dev/null
git diff --check
```

Preserve frozen contracts, source snapshots and reports; declare drift instead of
rehashing historical evidence. [EVIDENCE](docs/EVIDENCE.md) explains source-view audits.
Keep raw public/item data, environments and credentials ignored. Add dependencies
only for a demonstrated need, with version/license/purpose; project MIT licensing
does not override upstream licenses, including GPL/AGPL ERP code.
