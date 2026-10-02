# Development checkpoint

Updated 2026-10-02.

## Stage 1

All three implementation handoffs are integrated. Completion review reused the
validated baseline, reran its 21 acceptance tests and checked the earlier remote
CI result. A newly reproduced empty-coverage false pass was corrected without
changing contract v1 interfaces. Final fresh PostgreSQL 17.9 acceptance: 22 tests
passed with Python 3.12.12, zero failures/errors/skips.

Merged all three handoffs and the review correction through
[PR 1](https://github.com/daniel-li2021/inventory-intelligence/pull/1), main
`83e84578013bce2e5b82cbdc689ae2e5357938ab`, verified locally and remotely. Deleted
the four merged Stage 1 task refs locally/remotely and the two older merged
documentation branch refs locally. Preserved the `contract-v1` tag. Temporary
implementation worktrees are retired after final checks. Cleanup policy now
lives in AGENTS.md. The final Stage 1 correction also passed
[remote CI run 36994543696](https://github.com/daniel-li2021/inventory-intelligence/actions/runs/36994543696)
on PR head `a83e730a08484a13a3004662e402c62b884ab2d4`.

## Next work

Stage 2 means Forecasting & Planning; [STAGE2_PLAN.md](STAGE2_PLAN.md) now defines
the sequence and acceptance boundaries separately from v1. Initial kernel:
naive, historical mean, seasonal naive and fair rolling-origin evaluation with
exact rational arithmetic. Five independent model tests pass; the installed
package's synthetic demo also matches the manually expected scores. No new
dependency or external model call. This is a benchmark, not the complete
forecasting stage.

Independent checkpoint of current main: all 27 original tests passed on fresh
PostgreSQL 17.6 (Python 3.12.14), with no Stage 1 change or material defect; see
[STAGE2_CHECKPOINT.md](STAGE2_CHECKPOINT.md). Planning contract and deterministic
demand replay/eligibility now have their own slice and manual database checks.
[Eligibility PR 3](https://github.com/daniel-li2021/inventory-intelligence/pull/3)
passed both jobs in [CI run 36997926902](https://github.com/daniel-li2021/inventory-intelligence/actions/runs/36997926902).
Origin-aware forecasts/benchmarks now append versioned PostgreSQL evidence with
independent knowledge-time/holdout oracles.
[Benchmark PR 4](https://github.com/daniel-li2021/inventory-intelligence/pull/4)
passed [CI run 36998446346](https://github.com/daniel-li2021/inventory-intelligence/actions/runs/36998446346).
The final slice adds inventory revalidation, complete supply gates, exact daily
projection, prefix-aware replenishment and a deterministic PostgreSQL demo.
Fresh local full acceptance: 45 tests, no failures/errors/skips. See
[PLANNING.md](PLANNING.md) and [verified demo](examples/stage2.md). This stack
requires contract/integration review, CI and an authorized merge; Stage 2 is not
complete on main. Stage 3's working checkout remains untouched.
