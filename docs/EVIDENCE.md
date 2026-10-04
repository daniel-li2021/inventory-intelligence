# Evidence and reproduction

This catalog consolidates acceptance/provenance from retired reviews. Reports in
`review/` are immutable observations for their recorded source/environment, not
mutable current status. [STATE](STATE.md) owns present scope; [RESULTS](RESULTS.md)
owns measured core outcomes; [KB](KB.md) owns constraints and unresolved questions.

## Acceptance history

Counts below are separate runs, never additive. Local results do not imply CI
results; suite duration does not establish performance capacity.

| Boundary | Source / environment | Retained outcome / evidence |
|---|---|---|
| Stage 1 foundation | `f611554` data, `0502c2f` engine, `a90d7a1` corrections, `fa90d10` validation; Python 3.12.12 / PostgreSQL 17.9 | Original 21 independent tests. Empty complete coverage regression added R005 blocking (22 tests), followed by uncovered-key control. [Original CI](https://github.com/daniel-li2021/inventory-intelligence/actions/runs/36993288732); [golden oracles](VALIDATION.md). |
| Three-stage review | PR 7, main `dcada27`; local Python 3.12.14 / PostgreSQL 17.6 / Psycopg 3.3.6 | Expanded 76 tests (23/24/29), two fresh local rounds 2.842/2.829 s after two defects were corrected. [Validation](review/validation.json), [CI](https://github.com/daniel-li2021/inventory-intelligence/actions/runs/37044676872). Later [CI checkpoint](https://github.com/daniel-li2021/inventory-intelligence/actions/runs/37085401000) records 79 tests. |
| Copilot stabilization | Baseline `43a952d`, integrated `4f3d7c8`; fresh local Python 3.12.14 / PostgreSQL 17.6 / Psycopg 3.3.6 | 104 baseline / 106 integrated tests on separate databases; final 23/24/34 + 25 offline. [Acceptance](review/stabilization-acceptance.json), [live results](RESULTS.md#copilot-routing-and-fidelity). |
| Original Lab | PR 12, main `089d28f`; fresh local Python 3.12.14 / PostgreSQL 17.6 | 18 Lab/API and 124 combined tests; installed wheel outside checkout, five root/asset/evidence routes, downloaded JSON parsed, rounding/calculation references checked. [Screenshot](review/decision-lab.jpg); [independent arithmetic](RESULTS.md#lab-arithmetic-and-service). |
| Adversarial readiness | Base `429cc71`; fresh local Python 3.12.14 / PostgreSQL 17.6 / Psycopg 3.3.6 | Three coherently wrong persisted-training regressions failed before correction; focused core 31 tests, final Copilot 7. Lab/API 23 tests include 29 independently rehashed malformed cases and null receipt HTTP failure. Combined 134/134, zero errors/failures/skips; wheel/browser checks recorded separately. [Exact receipt](review/readiness-acceptance.json). |
| Accessibility / hosted boundary | Local keyboard/mobile review and installed wheel, Caddy 2.10.2 private CA | Accessibility 23 Lab/API tests; hosted 34 focused tests (11 + 23), 13 live HTTPS checks. No system trust-store change. [Browser receipt](review/lab-accessibility-browser.json), [hosted receipt](review/hosted-lab-acceptance.json), [HTTP results](review/hosted-lab-local-http.json). |
| Combined research | PRs 14–24, merge `f132bf4`, tree equal to candidate `f7d17e5`; local Python 3.12.14 / PostgreSQL 17.6 / Psycopg 3.3.6 | One fresh 240/240 run, no errors/failures/skips; four lineage tests/seven corruption controls; wheel, 13 private-CA HTTPS checks and browser CSP/mobile validation. [Acceptance](review/research-integration-acceptance.json), [integration identity](review/research-main-integration.json), [HTTP](review/research-integration-local-http.json), [browser](review/research-integration-browser.json). |
| Corrected remote baseline | Main `9d7c55f`; Python 3.12.12 / PostgreSQL 17.9 / Psycopg 3.3.6, full Git history | 240 tests / OK / 19.495 s plus hygiene. [Exact CI](https://github.com/daniel-li2021/inventory-intelligence/actions/runs/37164884160), [inspection receipt](review/engineering-readiness-baseline.json). This is retained evidence, not a new run. |

Baseline three-stage acceptance was 69 tests; the expanded run exposed uncovered
movement coverage and late-revision selector leakage. Fixes preserved local R003
handling and froze holdout selection instead of weakening independent oracles.
Core readiness then added contiguous/eligible saved training, unique selected order
identities and score/truth consistency. Lab readiness added all-key reconciliation,
temporal/count/source validation and fail-closed archive handling. See [KB](KB.md).

## Historical provenance and independent audits

[Lineage protocol](RESEARCH_LINEAGE_V1.md) and
[original manifest](review/research-integration-lineage-v1.json) bind 24 artifacts,
119 nodes, 17 complete historical source maps and five parent/freeze bindings.
All ten delivery heads must be ancestors; stacked PR 15/17 enter via PR 20. The
original manifest captures 13 drift bindings (12 extended decision-kernel bindings
and one packaging binding). Later hosted-document drift is declared by current
regression, not written into the old manifest. This is byte/metadata reproducibility,
not signed authenticity or universal business validation.

The original decision kernel is retained in [decision-v1-source.py.txt](review/decision-v1-source.py.txt).
Decision/intermittent artifact guards use it instead of the extended current kernel;
separate current-code oracles compare default behavior to that original. Independent
readiness audit derived all 480 decision and 5,544 intermittent selection/promotion
outcomes from saved scores, tie rules, floors, nulls and zero-cost cases without
calling the harness selector or refitting; all agreed. Count evidence has 40 controls
and 86 internal nodes with its own semantic DAG.

[Saved semantic audit receipt](review/research-integration-saved-audits.json):
768 parent safety arms / 512 pairs and 768 disjoint arms / 512 pairs, with zero item
overlap; lost-sales 576 logical arms / 288 pairs, 480 unique saved trajectories.
Source snapshots are `e7473a595d4ef6deca33c283ea6b27e23ad83bc4` (public) and
`d06badeb2a61b2f76da5ebb4afbd9ff6ffc38023` (lost sales). Reuse existing ignored
source/extraction/item caches, with zero acquisition, workbook parsing, model fits,
simulation replays or operational writes. Preserve caches; never publish them.
Temporary paths in the old receipts describe that run and are not required to exist.

## Reproduce without rewriting evidence

Use a complete retained Git/source view for a historical audit. Copying one old
kernel into current code, or using a source export without ancestry, is insufficient
for repository lineage. An exact saved-manifest audit can reject evolved current
validators/docs; that does not invalidate its historical study. Current regression
builds/audits current bindings separately.

The following original-view audit was checked during consolidation (substitute an
unused temporary checkout and the absolute manifest path in your primary repository):

```sh
git worktree add --detach /tmp/ii-original-lineage 87caa748560285ec6330e22fa3156791f6e17720
cd /tmp/ii-original-lineage
PYTHONPATH=src python -m scripts.research_lineage --audit --output /absolute/path/to/Inventory_Intelligence/docs/review/research-integration-lineage-v1.json
```

It returns the original 24 artifacts / 119 nodes / 17 maps / five parents / 13 drift
bindings, with zero refits/replays/writes. Remove only your clean temporary worktree
afterward. Semantic public/lost-sales audits likewise use their complete source
snapshots and ignored caches; the receipt preserves the calls/input bindings.
New manifests, if needed, use a new path and committed validator/protocol/oracles.
Do not rehash artifacts, suppress drift or rerun consumed studies to clear guards.
[Current validation commands](VALIDATION.md).

## CI lessons

- PR 24 / main shallow-checkout failure: `fatal: Not a valid commit name f6d3d160...`,
  then `ValueError: base not retained`. 236 tests ran without assertion failures;
  one setup error prevented four lineage tests. [Failure](https://github.com/daniel-li2021/inventory-intelligence/actions/runs/37160187852/job/111311855286).
  PR 25 fixed acceptance checkout with `fetch-depth: 0`; retain full history, never
  skip ancestry checks. The corrected remote baseline is recorded above.
- PR 26 [run](https://github.com/daniel-li2021/inventory-intelligence/actions/runs/37166377305):
  240 tests, one failure because an oracle fixed drift count at 13 when hosted docs
  legitimately added a 14th binding. The correction enumerates exact artifact/source
  identities, old/current hashes, missing paths and the denominator. Omitting a real
  drift row still fails even if its reduced count matches. Never substitute a new
  fixed count or rewrite evidence. Earlier PR 16's kernel guard was corrected using
  the retained original source, as described above.

## Retired plans and checkpoints

Extraction replaces maintenance of completed task narratives. The following files
are deleted after their durable information moves to these homes:

| Retired document(s) | Long-term home |
|---|---|
| `STAGE1_REVIEW`, `THREE_STAGE_REVIEW` | Golden controls in VALIDATION; acceptance above; forecasts, planner oracle and timings in RESULTS; clock/coverage lessons in KB. |
| `READINESS_CORE_REVIEW`, `READINESS_LAB_REVIEW`, `READINESS_REVIEW` | Trust/semantic boundaries in KB; numerical/service outcomes in RESULTS; source/environment, adversarial and combined acceptance above. |
| `STAGE3_BENCHMARK`, `STAGE3_STABILIZATION` | RESULTS retains failures, exact denominators, consumed matrix, usage/latency and reproduction; original reports/matrix remain in review. |
| `DECISION_LAB_VALIDATION`, `LAB_ACCESSIBILITY_REVIEW` | Independent arithmetic, browser measurements/limitations in RESULTS; operational/API behavior in DECISION_LAB; immutable receipts/screenshots retained. |
| `RESEARCH_INTEGRATION`, `CI_RESEARCH_HISTORY` | This catalog retains merge identity, combined acceptance, source views, audit counts/commands and CI incidents; original receipts unchanged. |
| `ENGINEERING_READINESS`, `RESEARCH` | KB retains engineering hypotheses/gaps and pinned-source/tool lessons; PLAN retains the active complete benchmark specification. |

Earlier stage/handoff/automation progress files were already retired: current status
is STATE, ongoing work is in indexed plans, interfaces/operations in contracts/guides,
and enduring choices in DECISIONS. All 22 investigation questions are extracted to
KB. Original narratives remain recoverable via `git show f3dc4a9:<path>`; earlier
retirements via `git show 208d5b3:<path>`. Git history is recovery, not the only home
for useful knowledge.

Four legacy links are symlinks only: `NEXT_ROUND_RESEARCH` and `READINESS_NEXT_STEPS`
point to KB, `ENGINEERING_READINESS` to KB, `ENGINEERING_BENCHMARK_PLAN` to PLAN.
These preserve links embedded in source-hashed protocols/design without retaining
old narratives or another status file. Frozen contracts, HOSTED_LAB_PLAN, original
reports and source-bound study protocols keep their bytes. Hosted release gaps
evolve in PLAN, KB and the deploy guide rather than the frozen design document.
