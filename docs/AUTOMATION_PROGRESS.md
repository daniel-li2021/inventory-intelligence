# Development checkpoint

Updated 2026-10-02. This is the current resumable status; detailed historical
acceptance remains in the linked stage/review documents.

## Verified integration

Fetched/pruned origin and verified remote `main` at
`ce8ab0dd23680a93ce2de4d2bda2b5c3e9f8fde7`. GitHub confirms PRs 1–8 are merged,
including Stage 2 eligibility/benchmark/replenishment (3/4/5), original Stage 3
(6), the combined review fixes (7) and measured Copilot benchmark (8).
Remaining local task branches are not evidence of unfinished implementation.

- **Stage 1 complete within contract-v1:** exact read-only reconciliation,
  completeness/coverage gates and append-only evidence. The later uncovered-key
  fix brings its independent acceptance to 23 tests; frozen interfaces remain.
- **Stage 2 complete within planning-v1:** origin-known demand/revision replay,
  nullable gaps versus eligible zero, exact baseline forecasts, shared
  7/14/28-day selection with separate holdout, inventory revalidation and
  prefix-aware advisory orders. 24 tests cover this bounded synthetic milestone.
- **Stage 3 complete within copilot-1/2:** read-only evidence explanations and
  explicit persisted planning UUID retrieval. Historical proposals remain
  citations, not current order approval. 32 tests; optional Luna routing is
  bounded and mocked tests are separate from older live smoke evidence.

[Main CI run 37085401000](https://github.com/daniel-li2021/inventory-intelligence/actions/runs/37085401000)
on `ce8ab0d` completed both jobs successfully. The PostgreSQL acceptance log
records **79 tests / OK**, using Python 3.12.12 and pinned PostgreSQL 17.9.
Prior local combined acceptance used Python 3.12.14 / Psycopg 3.3.6 / PostgreSQL
17.6 and passed twice, plus a final merge round. [Validation](VALIDATION.md).
No new database suite or model API calls were needed for this documentation pass.

## Existing results to reuse

[Three-stage review](THREE_STAGE_REVIEW.md) and immutable
[final round A](review/final-round1.json) / [B](review/final-round2.json)
retain seven 180-day synthetic groups and exact scores/proposals. Complete supply
proposes 12 pieces; incomplete supply stays `not_assessable` with null order.
Source hashes are unchanged across repetitions. Repetition proves reproducibility,
not independent statistical evidence or real-world forecasting performance.

The irregular holdout already illustrates an objective mismatch: naive has
daily MAE 3 versus mean 827/266, but mean has smaller absolute cumulative 28-day
error (278/19 versus 36), derived from stored bias without rerunning forecasts.
No inventory-cost/service improvement has yet been measured.

The later [Copilot benchmark](STAGE3_BENCHMARK.md) is merged and retains
observed live routing failures: five finding questions were classified as
unsupported. This is separate from deterministic evidence/test acceptance.
A focused routing follow-up should use fresh held-out paraphrases and keep
selector validation deterministic; this research made no new API calls.

## Authorized publication cleanup

The user authorized commit/push and branch cleanup. Deleted the remaining remote
`codex/stage2-eligibility` stack branch after preserving its exact tip `b0163bf`
in local tag `archive/stage2-stack-2026-10-02`. Deleted the ancestry-merged local
eligibility branch and removed the clean temporary `/private/tmp/ii-stage2-work`
checkout, which held only tracked files and disposable Python caches. Preserved
the local benchmark/replenishment branches: their original commit histories are
not ancestors of current main, although the reviewed implementations are integrated.
The separate Stage 3 worktree/environment was retained. No force deletion or
published-history rewrite occurred.

## Next action — proposed, not an implementation handoff

Read [next-round investigation](NEXT_ROUND_RESEARCH.md). Recommended order:

1. Freeze a separate offline decision-evaluation contract, including backlog
   versus lost sales, event timing, exact cost units, service denominators and
   terminal conditions. Then evaluate existing forecasts/policies on synthetic
   demand with independent manual outcomes.
2. Add unpredictable intermittent/lumpy and obsolescence controls, then bounded
   SBA/TSB challengers if the baseline decision weaknesses are reproducible.
3. Authorize a separate public observed-sales benchmark boundary and verify
   dataset rights before acquiring M5 or an alternative. Do not import public
   sales as accepted orders or fabricate availability/knowledge clocks.
4. Evaluate aggregation and a bounded LightGBM challenger only when justified;
   defer registry/drift/scheduling infrastructure until decision value is shown.

Current research is documentation-only. No new runtime contract, source import,
model dependency, simulator, scheduler or automatic model promotion was added.
Existing planning-v1 and historical copilot decoding remain unchanged. Public
real-data import is gated by the current synthetic-only instructions and a
separate approved research protocol. M5 redistribution rights remain unverified.
