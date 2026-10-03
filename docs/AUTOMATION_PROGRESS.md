# Development checkpoint

Updated 2026-10-03. This is the current resumable status; detailed historical
acceptance remains in the linked stage/review documents.

## Current checkpoint — prospective disjoint calibration task branch

`codex/public-calibration-generalization` stacks on PR17's published sources;
main remains unchanged. [Protocol](PUBLIC_CALIBRATION_V1.md) and exact public
freeze were committed at `6b76a2a` before any new-item simulation. Training-only
seed1709 excludes all32 consumed parent items and selects32 new ones, overlap0.
[Results](PUBLIC_CALIBRATION_RESULTS.md) retain768 continuous paid arms/512pairs,
6207 holdout units,25 positive-item and7 null-fill denominators. Mean/q95/L2/no
extra delay has92.12% fill/85.94% cycle; SBA/q95 has93.35%/89.84% even though its
target coverage is95.83%. Same retailer/calendar and prior-informed design,
not statistical independence, later-time validation or a service guarantee.

29 focused tests pass. A separate cached audit validates all768 new arms with
zero refits/replays; unchanged parent768-arm audit passes. An explicitly disabled
simulation cache-hit check preserves exact public bytes. Raw source/extraction
caches are reused without download or workbook parse. All item evidence stays
ignored/local. No model/policy selection, main merge or hosted deployment.

Accessibility and portfolio work were independently published in
[PR18](https://github.com/daniel-li2021/inventory-intelligence/pull/18) and
[PR19](https://github.com/daniel-li2021/inventory-intelligence/pull/19).
The latter preserves [all22 statuses and the long-term sequence](https://github.com/daniel-li2021/inventory-intelligence/blob/758d5d317ff8470841cc376bba49b86909ebb69c/docs/RESEARCH_STATUS.md).
Integration still needs explicit owner approval after automatic review rejected
the PR14 main merge; do not retry it on a goal continuation. Next independent
package: separately versioned research-only lost sales, then physical-count/
provenance boundaries. Hosted resources still need a concrete target and budget.

## Prior checkpoint — sales-proxy safety task branch

The dependent `codex/public-safety-service` branch extends PR15's attested adapter
without changing its archived forecast results. [Protocol](PUBLIC_SAFETY_V1.md)
was committed before real-sales simulation; [results](PUBLIC_SAFETY_RESULTS.md)
retain768 arms/512 contrasts over the same32 training-selected items. These are
explicitly consumed public observations, not fresh holdout or actual stockouts.
All56 warmup days, purchases and common15-day settlement are charged. q95 does
not guarantee95% fill/cycle service.31 focused tests pass; a separate audit
reconciles every cached arm and public aggregate with zero refits/replays.

Published prior packages remain unmerged: [PR14](https://github.com/daniel-li2021/inventory-intelligence/pull/14)
(all22 useful directions, fresh warmup, safety retention, supply interventions),
[PR15](https://github.com/daniel-li2021/inventory-intelligence/pull/15) (public
adapter/forecast), [PR16](https://github.com/daniel-li2021/inventory-intelligence/pull/16)
(fixed-forecast policy comparison). PR14 integration was rejected by automatic
approval review; the required explicit integration-owner approval is still pending.
No main integration is retried, and independent ready work continues.

Next: local accessibility/UX audit, missing provenance/invariant checks and a
portfolio case study with the negative public/synthetic findings. Advanced models
remain conditional; bigger lost-sales/physical-count/allocation/hosting work keeps
its separate contract/target gates in PR14's complete roadmap.

## Prior checkpoint — public observed-sales task branch

The user assigned the long-term research directions on2026-10-03. Fresh costed
warmup, retention and supply-intervention work is published in PR14 and awaits
merge approval after automatic review rejected default-branch integration.
Remote main has not been advanced by that batch.

The independent `codex/public-observed-sales` branch implements the official UCI
adapter and first forecast-only benchmark. The541909-row extraction passes;
32 train-stratified items show fixed mean outperforming selection-chosen methods
on the28-day holdout.22 focused tests pass. Raw observations and item-level
results stay ignored/local. [Full evidence](PUBLIC_SALES_RESULTS.md).

Next ready work: explicit small policy comparison, sales-proxy safety evaluation,
cross-layer provenance/QA and demo accessibility. Advanced models remain gated;
public sales do not become accepted-order demand. The full22-direction roadmap
is retained on the research-roadmap branch/PR14, not silently narrowed here.

## Current checkpoint — policy comparison branch, integration pending

The continuing research goal includes a frozen three-rule comparison with
identical forecasts, known supply, prior commitments and review calendars.
[Protocol](POLICY_COMPARISON_V1.md) / [results](POLICY_COMPARISON_RESULTS.md):
120 logical arms / 65 distinct physical trajectories; prefix arithmetic improves
four repeated late-inbound cells, while periodic `(s,S)` regresses fill in 34/40.
All initial/inbound/ordered units and settlement costs are charged. This is a
research arithmetic adapter, not operational planner execution or source approval.
Focused acceptance: **61 tests pass** on Python 3.12.14 / Psycopg 3.3.6, including
Lab/API regressions and the archived default-kernel oracle. No database or API run.

Other independent packages are published but unmerged: PR #14 (22-direction
roadmap, fresh costed warmup, safety retention and supply interventions), PR #15
(attested UCI observed-sales adapter and train-only forecast benchmark). Their
branches retain their artifacts; this independent branch starts from current main.
The automatic approval reviewer rejected PR #14 integration because it requires
explicit integration-owner approval; the human approval question remains pending.
No merger is retried. Independent research continues toward public sales-proxy
safety/service evaluation, probabilistic calibration and demo accessibility.

## Current checkpoint — independent Lab accessibility branch

`codex/lab-accessibility` starts from current main `f6d3d1`. The
[targeted review](LAB_ACCESSIBILITY_REVIEW.md) fixes submit focus loss, repeated
control hints, keyboard table scrolling, 320px blocked-state overflow and faint
text/graph/input boundaries. Existing presets are sufficient; no new scenario
framework was added. Browser evidence and source hashes are retained.23 Lab/API
tests and JavaScript syntax pass. Backend/evidence/contracts are unchanged.

Previously published, unmerged research: PR14 (complete22-direction roadmap,
fresh paid warmup, retention and supply attribution), PR15 (public adapter/forecast),
PR16 (policy comparison), PR17 (paid public sales-proxy safety/service, dependent
on PR15). PR14 integration remains pending explicit owner approval after automatic
review rejected the merge. This branch does not retry shared-main integration.

Next independent work: portfolio case study using verified negative results,
remaining provenance/property gaps and separately frozen fresh calibration labels.
Large lost-sales/physical-count/hosting extensions keep their contract/target gates;
the full roadmap is preserved in PR14 rather than narrowed to completed work.

## Current checkpoint — independent lost-sales research branch

The continuing goal's separate lost-sales boundary is frozen in
[CONTRACT_LOST_SALES_V1](CONTRACT_LOST_SALES_V1.md) at7550cc4; isolated kernel,
generator/oracles/auditor commit54ded62 precedes fresh scoring. No accepted-order
backlog contract or planner/Lab file changes. Both semantics use synthetic
completed attempted-demand feedback, not inferred lost demand from sales.

[Results](LOST_SALES_RESULTS.md) retain288 matched pairs/576 logical arms,
480 exact-input computations/376 distinct native trajectories,12 distinct
demand paths and19 supplier paths. First orders all match; later purchased
quantities differ in199 pairs. Immediate fill improves89, regresses10, equals93
and is undefined96. Lost penalties10/40 yield171/25 lower-cost pairs, respectively;
different unit-day/once-per-unit business penalties are not interchangeable ROI.
All warmup, purchases and common100-day settlement accounting are paid.

24 focused tests and the separate480-arm saved-event audit pass; six rehashed
faults are detected. Cache reuse with evaluation disabled preserves exact bytes.
Full synthetic traces are compressed in Git alongside a readable exact summary.
No database/model API, dependency, source import, CI monitoring or main merge.

The independent public calibration replication is published in
[PR20](https://github.com/daniel-li2021/inventory-intelligence/pull/20), with its
disjoint32-item/frozen source evidence on that branch. The complete22-direction
status/case study is preserved in
[PR19](https://github.com/daniel-li2021/inventory-intelligence/pull/19).
Main integration remains pending explicit owner approval after automatic review
rejected PR14's merge. Next independent package: additive synthetic physical-count
truth/provenance, then a concrete hosted read-only target/ownership proposal.

## Prior checkpoint — bounded startup attribution implemented

Automation continuation began from fetched/pruned `origin/main` at `673dae8`.
Frozen [diagnostic protocol](FEASIBILITY_DIAGNOSTIC.md) commit `5e2ec8e` precedes
the five-control replay. New pure offline diagnostics attribute startup misses
without informing orders and extend settled terminal stock to a common 36-day
cost window. Existing simulator/Lab contracts and archived outcomes stay intact.

Delay3 has eight unavoidable startup misses and 60 later misses of 112 new units.
Common-window costs 387 versus 1171 preserve the delay disadvantage, with delta 784
instead of the unequal-window 844. Zero demand remains null-service and incomplete
supply remains blocked. [Results/reproduction](FEASIBILITY_DIAGNOSTIC_RESULTS.md),
[exact artifact](review/feasibility-diagnostic.json).

Focused acceptance passes **48/48**, including 15 new independent diagnostic/CLI
tests, on Python 3.12.14 / Psycopg 3.3.6. No new database/model API, benchmark refit,
external acquisition or deployment was needed. These controls reuse one consumed
synthetic path; fresh demand/supplier traces and costed warmup remain the next
evaluation milestone. Additional forecasts are still unjustified.

## Prior checkpoint — independent readiness review complete

Started from fetched `origin/main` at `429cc71`. Isolated engineering, Lab and
research reviews found and fixed persisted demand-evidence contradictions and
rehashed Lab archive inconsistencies. The Lab now distinguishes prefix shortages
from periodic backlog and discloses unequal runoff accounting windows. README
leads with the completed architecture and standalone Lab rather than Stage 1.
[Project assessment](READINESS_REVIEW.md), [core review](READINESS_CORE_REVIEW.md),
[Lab review](READINESS_LAB_REVIEW.md) and [ranked next steps](READINESS_NEXT_STEPS.md).

Fresh local acceptance passes **134/134**, with no failures/errors/skips, on
Python 3.12.14 / Psycopg 3.3.6 / fresh isolated PostgreSQL 17.6. Installed-wheel
HTTP and real-browser fail-closed/delay/zero-demand checks pass. Independent
audits of retained selections/promotions pass; all four prior benchmark/replay
artifacts are byte-for-byte unchanged. [Receipt](review/readiness-acceptance.json).
No new model/API evaluation, external data, benchmark generation, schema,
dependency or frozen contract change was introduced. Remote CI was not monitored.

Ready for a synthetic portfolio demo; production performance and source
attestation remain unmeasured. Freeze core contracts and current model/Lab scope.
Next useful deliverable is a separate feasibility/evaluation protocol with fresh
demand/supply paths and costed startup/warmup counterfactuals. Safety retention
under decline follows only if unexplained weaknesses remain. Public observed
sales and hosted access still need separate boundary decisions. No new direction
has been implemented by this review.

## Prior checkpoint — Decision Lab integrated

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
Integrated through [PR 12](https://github.com/daniel-li2021/inventory-intelligence/pull/12)
at `089d28f`, verified on remote main. All four task branches were ancestry-merged
and removed; the three clean task worktrees were retired. Existing active
branches/worktrees and the local app environment were preserved. The disposable
lab PostgreSQL service was stopped; its data and test logs remain local.
Remote CI was not monitored and is not represented by the local test count.
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
