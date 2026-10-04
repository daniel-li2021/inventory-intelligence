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

[Lineage protocol](EVIDENCE.md#historical-provenance-and-independent-audits) and
[original manifest](review/research-integration-lineage-v1.json) bind 24 artifacts,
119 nodes, 17 complete historical source maps and five parent/freeze bindings.
All ten delivery heads must be ancestors; stacked PR 15/17 enter via PR 20. The
original manifest captures 13 drift bindings (12 extended decision-kernel bindings
and one packaging binding). Later hosted-document drift is declared by current
regression, not written into the old manifest. This is byte/metadata reproducibility,
not signed authenticity or universal business validation.

The original decision kernel is retained in [decision-v1-source.py.txt](review/decision-v1-source.py.txt).
Historical artifact guards verify the complete pinned original Git source, including
protocols and scripts, rather than requiring retired documents in the working tree.
Separate current-code policy oracles compare default behavior to the archived kernel. Independent
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

## Documentation lifecycle

Completed plans, reviews, investigations and compatibility stubs are removed from
current documentation. Current interfaces are consolidated in CONTRACTS, operator
commands in OPERATIONS, outcomes in RESULTS, lessons/constraints in KB and enduring
choices in DECISIONS. Only PLAN has pending execution. Prior narrative bytes remain
in Git; `git show 886e893:<path>` recovers the previous documentation surface.
Original historical protocols are evidence inputs in their pinned Git views, not
maintained files or separate planning authority. Missing current documents are
explicit drift with `current_sha256: null`; immutable historical hashes stay exact.

## Study artifacts and original sources

Every original source map is retained in its immutable report and checked against
one complete Git snapshot by the lineage audit. Use `git show <snapshot>:<path>`
for protocol/code bytes or a detached worktree for executing the original auditor.
Do not run a consumed study merely because its old runner exists. Future studies
need newly assigned scope and a fresh protocol/output; no report hash is updated.

| Evidence | Immutable report / source view |
|---|---|
| Decision / intermittent | [Decision](review/decision-benchmark.json), [intermittent](review/intermittent-benchmark.json); original complete source `f6d3d16034af038eda4c8687ea4f1ed6d2445ef6`. |
| Feasibility | [Five exact controls](review/feasibility-diagnostic.json); its complete source map is in the saved lineage manifest. |
| Warmup / retention / supply | [Warmup](review/fresh-warmup-v1.json), [retention](review/safety-retention-v1.json), [supply](review/supply-sensitivity-v1.json); PR 14 head `d2cb98ba1016f80bd2c2dd40159092f4f1b21395`. |
| Policies | [Paired policies](review/policy-comparison-v1.json); PR 16 head `39bf64d7e70b9221afbe1d697fe49fd348fcdc04`. |
| Public forecast / safety | [Forecast](review/public-sales-forecast-v1.json), [safety](review/public-sales-safety-v1.json); complete source maps and parent bindings are in the lineage manifest. |
| Disjoint calibration | [Frozen subset](review/public-calibration-freeze-v1.json), [outcomes](review/public-calibration-v1.json), [acceptance](review/public-calibration-acceptance.json); `e7473a595d4ef6deca33c283ea6b27e23ad83bc4`. |
| Lost sales | [Trajectory archive](review/lost-sales-v1.json.gz), [summary](review/lost-sales-v1-summary.json), [acceptance](review/lost-sales-acceptance.json); `d06badeb2a61b2f76da5ebb4afbd9ff6ffc38023`. |
| Physical counts | [40 controls / 86 nodes](review/physical-count-v1.json), [acceptance](review/physical-count-acceptance.json); `c916c046b3af06503574aaea208a0197e0615a3e`. |
| Hosted / portfolio | [Image pins](review/hosted-lab-image-manifests.json), [hosted acceptance](review/hosted-lab-acceptance.json), [claim audit](review/portfolio-claims.json); source views in the lineage manifest. |

The public adapter's exact cross-item rational sums use signed hexadecimal
numerator/denominator strings; decode with the original study's `decode` helper.
A 5,000-digit round-trip oracle checks this format. No process conversion limit
was weakened. Original public/physical auditors deliberately guard their complete
sources; documentation relocation makes current-source reuse reject, so audit
those historical caches at the recorded source snapshot. Current kernel tests
remain separate from historical provenance, including independent mutation controls.

## Local engineering pilot

[Measured outcomes](RESULTS.md#local-engineering-pilot) and [pending confirmation](PLAN.md)
refer to the explicitly approved existing-Mac exploratory pilot. The frozen source
snapshot is `970ab16` (full commit in [source binding](review/engineering-pilot-v1/source-binding.json));
its core source/SQL/fixture/protocol bytes reproduce the recorded combined hash.
Base at launch was `886e893`. Concurrent documentation consolidation through
`650ae05`/`4b112ad` is preserved and did not change measured engine/SQL inputs.
Completed protocol narratives were extracted into PLAN/OPERATIONS and removed
from the maintained surface; original bytes stay in that frozen Git source view.

- [Environment](review/engineering-pilot-v1/batch-environment.json),
  [binary/installed metadata diagnostics](review/engineering-pilot-v1/runtime-diagnostics.json),
  [raw batch calls](review/engineering-pilot-v1/batch-samples.jsonl),
  [raw summary](review/engineering-pilot-v1/batch-summary.json),
  [derived corrected summary](review/engineering-pilot-v1/batch-derived-summary.json),
  [read-only SQL plan](review/engineering-pilot-v1/batch-selected-sql-plan.json).
- [Actual producer reads/accounting diagnostic](review/engineering-pilot-v1/batch-reader-diagnostics.json),
  [exact validation-byte controls](review/engineering-pilot-v1/batch-reader-json-boundaries.json),
  [supplemental control source](review/engineering-pilot-v1/batch-reader-boundary-controls.py).
  Diagnostic wrappers call the original validator; they do not bypass it. Primary
  capacity timing is separate from that instrumentation.
- [HTTP summary](review/engineering-pilot-v1/network-summary.json) and raw per-campaign
  JSONL/resource files in the same directory; [5/s allowance control](review/engineering-pilot-v1/allowance-summary.json)
  has a separate offered-load denominator and recovery receipt.
- [Backtest control](review/engineering-pilot-v1/backtest-summary.json),
  [repaired native recovery](review/engineering-pilot-v1/recovery-summary.json),
  [initial failed harness attempt](review/engineering-pilot-v1/initial-recovery-initial-failure.json).
  Original failed source/logs and `engineering_recovery_initial` DB remain retained;
  the corrected attempt used a fresh fixture, not an overwritten failed result.
- [Final runner natural/fault smoke](review/engineering-pilot-v1/runner-smoke-samples.jsonl)
  records three valid calls and a deliberately failed oracle after a complete
  append, retained as committed_unverified. The [final two-key quantity probe](review/engineering-pilot-v1/runner-probe-verified.json)
  validates corrected expected-finding metadata without retired protocol files. Twenty-four focused tests plus the added worker CI smoke passed;
  this does not replace the separate retained full correctness/remote-CI baseline.

Two reporting defects in the historical summary are corrected only in the derived
view/current runner: the all-key quantity probe expects 1,000 findings (its frozen
manifest was correct, raw summary label was 0); serial completed counts were API
calls, including blocked calls, rather than completed eligible plans. The derived
view explicitly separates both denominators and retains supervisor overhead.
The current runner also removes its retired Markdown-protocol dependency and
honestly classifies missing post-commit receipts. No baseline measurements were
replayed for these reporting changes; no production engine/SQL was optimized.

[Artifact manifest](review/engineering-pilot-v1/artifact-manifest.json) retains exact
original sizes/hashes. Large synthetic producer reports and fixture manifests
remain ignored under `artifacts/engineering-*-v1`; the disposable cluster is
retained stopped at `/private/tmp/ii-engineering-pilot-pg`. The original JSONL and
receipts are not reformatted/rehashed in place. Published-file integrity is in
[published hashes](review/engineering-pilot-v1/published-hashes.json).
No public/customer operational data, model calls, paid provisioning or deployment
is part of this receipt. Wheel/image hashes, enforced Linux resources, long/stable
campaigns, broader recovery and independent human checks remain unverified.
