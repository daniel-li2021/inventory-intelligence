# Stage 1 completion review

Reviewed 2026-10-02. Acceptance means the bounded reconciliation milestone in
[contract v1](CONTRACT_V1.md), not certification of physical stock.

Current status: the later [three-stage review](THREE_STAGE_REVIEW.md) adds the
known-but-uncovered movement regression (23 Stage 1 tests), preserving v1
interfaces. Latest `main` at `ce8ab0d` passed all 79 combined tests
in the [pinned main CI](https://github.com/daniel-li2021/inventory-intelligence/actions/runs/37085401000).
The original 21/22-test results below remain historical acceptance evidence.

## Delivered

- Data foundation `f611554`: synthetic source/storage schemas, restricted runner
  role, pinned PostgreSQL Compose, deterministic fault scenarios and loader checks.
- Engine `0502c2f` plus corrections `a90d7a1`: five SQL rule families, aligned
  cutoff/watermark arithmetic, Repeatable Read, atomic append-only run results,
  exact evidence, stable reports, and CLI exit semantics.
- Independent validation `fa90d10`: integrated foundation/engine, manually
  calculated golden inputs, exact assertions, PostgreSQL CI, fresh-database
  quickstart and verified clean/corrupt examples.

The original 21-test suite passed again in this checkout on PostgreSQL 17.9 and
Python 3.12.12, including quantity boundaries, duplicate/reference/transfer faults,
manifest gaps, rollback, history, operational-write denial and CLI behavior.
The earlier [GitHub acceptance run](https://github.com/daniel-li2021/inventory-intelligence/actions/runs/36993288732)
was independently checked: both acceptance and hygiene succeeded.

## Review correction

Two complete, zero-row manifests with no coverage previously passed all five
rules. This proved no inventory was compared, so the result was unsupported.
The checker now emits an R005 `coverage_mismatch` for each empty declared coverage
set, with `empty_coverage` evidence, and blocks R001. The existing contract's
rule IDs/report shape remain unchanged. A regression checks exact batch evidence
and absence of manufactured quantity deltas. Explicit zero-stock controls remain
valid. Final acceptance includes this additional test (22 total).

## Boundaries for the next stage

Operational writers must retain source evidence; runtime permissions protect
against checker writes but do not stop an upstream owner from rewriting inputs.
V1 checks posted reversal quantities in arithmetic and validates referenced row
existence; richer reversal semantics, running-negative policies, transit and
reservations are future contracts. A passing run proves internal consistency at
its selected cutoff/coverage, not uncensored demand or current physical stock.
Forecasting must therefore use separate demand/completeness/availability inputs.
