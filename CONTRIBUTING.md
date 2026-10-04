# Development workflow

Start with [STATE](docs/STATE.md) for the current phase, gates and integration
mode, then the relevant plan in [the registry](docs/README.md#plans-and-work-status).
[The knowledge index](docs/README.md) routes to
contracts and evidence; [DECISIONS](docs/DECISIONS.md) records durable choices and
supersession. Read only the surfaces needed for the assigned task.

## Integration modes

The single persisted setting is `Integration mode: AUTO` or
`Integration mode: REVIEW` in STATE. A simple “Switch to AUTO/REVIEW” instruction
changes that line; it applies to later tasks until switched again. An explicit
instruction to merge a particular change can authorize that merge without changing
the persistent mode. Neither mode expands implementation scope or clears a
contract, data-license, benchmark-program or paid-deployment approval gate.

| Mode | After scoped validation and diff review |
|---|---|
| AUTO | The integration owner integrates authorized work into current main, pushes and verifies the remote ref without another merge confirmation. |
| REVIEW | Prepare a clean validated commit and reviewable diff/task branch (PR if useful), report checks and limitations, and stop before merging into main. |

Branches/worktrees provide isolation. PRs provide an optional review surface;
change size/type does not create a third merge mode. One integration owner controls
main if multiple agents were explicitly assigned; sub-agents do not merge or push
main. Old handoffs never launch or authorize additional agents.

## Each change

1. Verify `git rev-parse --show-toplevel`, status, branch and remote. Fetch with
   pruning and inspect branches before nontrivial work. Start `codex/<task>` from
   current `origin/main`; use a clean worktree if active or dirty work needs isolation.
2. Trace the relevant contract/callers. Prepare a compact proposal before a new
   capability and implement only an assigned handoff. Preserve frozen semantics,
   source permissions, original evidence, active branches and required environments.
3. Run focused checks and a meaningful operator/published-path check when behavior
   changes. For PostgreSQL acceptance use a fresh disposable database; never reset
   a populated demo or another task's database. Existing README/VALIDATION commands
   are authoritative; do not regenerate consumed studies to make an audit pass.
4. Update STATE and the affected plan after material progress; record completed
   work, remaining gaps and next action. Keep each short-term, long-term or area
   plan linked in the index with scope/status. Complete one assigned task at a time.
   On completion retain useful plans with results and open gaps; superseded plans
   link their replacements. Archive only obsolete/duplicate material. Update
   affected durable guides; add a decision only for an enduring choice. Stage explicit
   files, inspect `git diff --cached`, and run `git diff --cached --check`.
5. Fetch again before publication; compare with current `origin/main`, reconcile
   upstream work without overwriting it, and rerun checks affected by that reconciliation.
   Re-read the mode in current main and the candidate STATE before merging. If another
   task changed the mode/gate, honor the latest user instruction rather than silently
   restoring a stale value. A discrepancy without a clear instruction requires review.
6. In AUTO, integrate coherently and push without rewriting published history;
   a direct fast-forward is sufficient for small validated changes. Use an integration
   PR when a shared review surface is useful. In REVIEW, stop with the validated
   result before main integration. Verify any pushed ref with `git ls-remote`.
7. After every merge, verify remote main contains the work, then switch the primary
   checkout to current main, remove the completed clean disposable worktree, and
   delete the completed local task branch with `git branch -d`. Finish this cleanup
   in the same task. Preserve active/dirty/unmerged work and required environments
   in their own checkout. For cherry-picked integrations, verify every unique patch
   exists in main and preserve the original tip with a local archive tag before
   retiring the branch; never discard unique commits. Do not monitor CI after routine
   pushes unless CI/deployment verification was requested or there is evidence of failure.

Documentation-only validation uses the standard library and needs no service:

```sh
python3 scripts/check_docs.py
python3 -m json.tool docs/research/repositories.json > /dev/null
git diff --check
```

CI hygiene runs the doc check and JSON parsing. PostgreSQL CI runs real independent
oracles with full Git history; mocks, local acceptance and exact remote CI runs are
separate evidence. Do not sum overlapping package test counts or imply the suite's
elapsed time is measured service capacity. [Validation guide](docs/VALIDATION.md).

## Evidence, data and dependencies

Keep small deterministic synthetic inputs versioned, independent of the checker.
Keep local environments, raw public observations and reconstructable item series
ignored. Preserve consumed report/receipt bytes, source snapshots and Git history.
Documentation navigation edits may change current source fingerprints; declare
that drift rather than rehashing an old artifact or calling it a new experiment.
A historical audit uses its complete original source view; current regression is
separate. See [reproducibility boundaries](docs/README.md#evidence-and-reproducibility).

Add dependencies only for a demonstrated need; record version, license and purpose.
Original MIT licensing does not override upstream licenses. Never copy GPL/AGPL ERP
code as original MIT material. Credentials stay in ignored config/secrets.

## Scheduled work

Manage Codex schedules in the app, not repository cron. Earlier overnight/morning
schedule descriptions are historical configuration snapshots, not verified current
schedules. A continuation reads STATE's current focus/mode, then the relevant
indexed plan's authorization gates; AUTO permits merging assigned work, not
resuming paused features. Keep resumable work in that plan and STATE instead of
another automation progress file. Local
schedules require an awake computer, running app and available repository.
