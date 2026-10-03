# Development checkpoint

Updated 2026-10-03. This is the current resumable status; detailed historical
acceptance remains in the linked stage/review documents.

## Current checkpoint — Decision Lab accepted locally

The user assigned the synthetic portfolio-facing Inventory Decision Lab. Its
[compact plan and isolated handoffs](DECISION_LAB_PLAN.md) precede implementation.
The integration owner combined focused backend, frontend and independent-test
branches; no agent pushed to main or opened a separate PR. The optional local
FastAPI app reuses all existing core modules unchanged, with bundled evidence
generated through real reliability/forecast/planning runs.

Combined acceptance passes **124/124** local tests (18 new lab/API tests) on fresh
isolated PostgreSQL 17.6 / Python 3.12.14. Installed-wheel and real-browser checks
pass; zero-demand and incomplete-evidence outputs stay fail closed. Scenario
derivations cite calculation hashes separately from saved source UUIDs.
[Operations, exact results and synthetic screenshot](DECISION_LAB.md).
Publication uses one integration PR because this adds dependencies and a
portfolio capability. Remote CI is not represented by these local results.
The lab remains a historical synthetic replay, with no operational execution,
new models, live data, scheduled jobs or cloud infrastructure.

## Prior checkpoint — stabilization complete

Started from fetched/pruned `origin/main` at `43a952d`, containing decision PR 10
(`33ced64`), intermittent PR 11 (`429f0f9`) and updated integration-owner workflow.
Focused commits freeze the routing holdout (`363957c`) before implementing the
classification/selector boundary (`4f3d7c8`). Small validated fixes integrate
directly under the standing authorization; no per-agent PRs are needed.

Published batch `722873e` is verified on remote `main`.
[Integration CI 37104968788](https://github.com/daniel-li2021/inventory-intelligence/actions/runs/37104968788)
passed Repository hygiene and PostgreSQL acceptance. The workflow pins PostgreSQL
17.9 / Python 3.12.12; archived logs returned HTTP 403, so the remote test count
is unverified. The **106/106** count below is verified local acceptance.
This task's merged branch was
removed locally/remotely; other branches, worktrees and environments were preserved.
This final checkpoint update changes documentation only.

Fresh combined acceptance passed **104/104** on that untouched main, then
**106/106** on locally integrated main at `4f3d7c8`: Stage 1 23, Stage 2 24,
Stage 3 34, offline decision/intermittent 25. Python 3.12.14 / Psycopg 3.3.6 /
PostgreSQL 17.6, separate new databases, no failures/errors/skips, unchanged
independent oracles. [Exact revisions, hashes and test outcomes](review/stabilization-acceptance.json).
The existing 480 decision and 5,544 intermittent results remain unchanged and
were verified through current provenance/input/arithmetic/settlement tests.

**Complete within the synthetic boundary:** Stage 1 reconciliation, planning-v1,
copilot-1/2 deterministic explanations, both offline research harnesses, and this
focused Stage 3 stabilization. Intent classification is independent of selector
availability; deterministic code alone selects findings. Fresh live routing
passed **32/32**, evidence fidelity **32/32**, numeric fidelity **32/32**, including
**10/10** cases with quantities/scores. [Protocol and limitations](STAGE3_STABILIZATION.md).
The original failed benchmark and all research artifacts remain historical evidence.

**Still experimental:** optional natural-language routing (one synthetic live
holdout, no production/population guarantee), intermittent methods and empirical
safety (offline research only), and cell-wise decision promotion findings.
No runtime champion, current-order authorization or real-data claim follows.
Public-sales acquisition remains gated by the synthetic-only boundary. No new
forecasting models or large features were added in this stabilization wave.

### Consumed evaluation sets — regression only

| Set | Consumed boundary; do not use for tuning |
| --- | --- |
| Original Stage 2 / three-stage review | Seven 180-day synthetic groups and their final holdouts; repeated results are correlated regression evidence. |
| Original Stage 3 benchmark | All 45 cases, including five observed misroutes and five later explicit controls. Preserve the original 40/45 artifact. |
| Fresh routing holdout v1 | All 32 new English/Chinese cases; frozen in `363957c`, evaluated once at `4f3d7c8`. Now consumed. |
| Decision benchmark v1 | Seeds 11/29/47; all 60 paired cells, 480 candidate/split results and final 56-day holdouts. |
| Intermittent research v1 | Seeds 101/211/307; all 84 cells, 5,544 results and final 56-day holdouts. |

Known questions, holdouts and observed service/cost failures must not tune prompts,
allowlists, models, smoothing/safety parameters, initial stock or policy and then
be relabeled fresh validation. Keep frozen selection rules; any new iteration
needs a separately declared counterfactual/protocol and fresh evaluation set
before outcomes are inspected. Existing fixtures remain independent regression
oracles. Next work requires a focused handoff; speculative expansion is deferred.

The sections below preserve prior milestones and investigation chronology.

## Integrated milestone — intermittent/safety research

The user authorized integration of PRs 10 and 11 on 2026-10-02. PR 10 merged at
`33ced649a7a1271e1272d0138e6b7ffc9b112f67`, verified on remote main after resolving
README, checkpoint and research-note conflicts with PR 9. The continuation in
[PR 11](https://github.com/daniel-li2021/inventory-intelligence/pull/11) merged at
`429f0f9`, incorporating that ancestry. It freezes
[CONTRACT_INTERMITTENT_V1.md](CONTRACT_INTERMITTENT_V1.md), adds exact offline
Croston/SBA/TSB with cumulative-error empirical safety, and evaluates fresh
seeds 101/211/307. [Protocol/results](INTERMITTENT_BENCHMARK.md) retain all 5,544
candidate/split results across 84 cells and 33 configurations; 2,376 unique
physical simulations reuse the rest. All terminal obligations settle.

Selected new methods pass ten cell-wise comparisons against the selection-chosen
baseline; only four overall selections pass both reference comparisons. These
are synthetic, correlated comparisons, not a global promotion. No lumpy or
obsolescence cell supports new-method promotion. Complete target coverage can
coexist with failed fill because initial stock cannot meet demand before receipt.
The old v1 artifact's semantic scenarios reproduce exactly after sharing the
event kernel; only current source provenance is refreshed.
Integrated Python 3.12.14 validation passed all 31 focused tests, including
current-interpreter demand reproduction, artifact provenance and completed-only
calibration checks. The valid intermittent outputs were reused.

The [public-sales protocol](PUBLIC_SALES_PROTOCOL_V1.md) is prepared with verified
official UCI license attribution and a separate observed-sales target. It awaits
the explicit boundary choice required by synthetic-only AGENTS.md. No real data
has been acquired. M5 terms were unreadable; no rights are inferred. ADIDA/IMAPA,
LightGBM and registry/drift/scheduling infrastructure remain conditional on new
evidence and a separately frozen handoff, not automatic expansions.

## Integrated milestone — offline decision-benchmark-v1

The user assigned the next milestone from
[NEXT_ROUND_RESEARCH.md](NEXT_ROUND_RESEARCH.md). Work began on
`codex/decision-benchmark-v1` from fetched remote main `ce8ab0d`; the previous
research branch is preserved. The separate
[decision contract](CONTRACT_DECISION_V1.md) fixes backlog semantics, local-day
event timing, inventory-position policy, exact costs, service denominators,
paired synthetic scenarios, selection/holdout boundaries and fixed runoff.
Simulator, independent oracle and evaluation authoring used isolated worktrees.
Integrated offline validation passed 19 focused tests on Python 3.12.14 and
completed 480 candidate/split simulations across 60 paired cells. All terminal
obligations settled; 22 cells lacked eligible selection and all eight selected
lumpy cells failed held-out service. Six weekly and ten obsolescence cells passed
the declared promotion rule, including repeated controls; no champion is changed.
Results, exact provenance and validation are recorded in
[DECISION_BENCHMARK.md](DECISION_BENCHMARK.md). Implementation is published through [PR 10](https://github.com/daniel-li2021/inventory-intelligence/pull/10).
The user authorized conflict resolution and integration on 2026-10-02; the
upstream PR 9 documentation is preserved alongside these results.

Main already contains all three bounded synthetic stages through PRs 7/8.
The prior baseline and investigation below retain their original chronology
and are not current blockers. This milestone adds no public data, model dependency, database
schema, runtime order execution or change to planning-v1/Copilot contracts.
The original later SBA/TSB and safety-calibration steps are delivered by the
continuation above; public-sales evidence remains gated by its separate protocol.

## Prior verified integration — PRs 1–8

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
At that earlier checkpoint, inventory-cost/service outcomes had not yet been measured.

The later [Copilot benchmark](STAGE3_BENCHMARK.md) is merged and retains
observed live routing failures: five finding questions were classified as
unsupported. This is separate from deterministic evidence/test acceptance.
That historical research made no new API calls. The completed stabilization at
the top of this checkpoint uses fresh held-out paraphrases and deterministic
selector validation; it preserves the original failures as recorded evidence.

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

## Original investigation sequence — superseded by assigned milestones

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

The original investigation was documentation-only. No new runtime contract, source import,
model dependency, simulator, scheduler or automatic model promotion was added.
Existing planning-v1 and historical copilot decoding remain unchanged. Public
real-data import is gated by the current synthetic-only instructions and a
separate approved research protocol. M5 redistribution rights remain unverified.
