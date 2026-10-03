# Combined research candidate acceptance

Status: **locally validated integration candidate**, not merged main, remote CI,
public deployment or production evidence. Main remains `f6d3d16`. Exact PR 14–23
heads and all 22 directions are recorded in [the delivery ledger](RESEARCH_STATUS.md).
The candidate preserves all ten heads by ancestry through eight explicit merges;
stacked PR 15/17 are included through PR 20. Published histories are not rewritten.

## Combined behavior and conflict resolution

Shared README, public-sales protocol and development checkpoint conflicts were
resolved by retaining assignment/operational boundaries and completed package
results. No source-code merge conflict occurred. The public-sales adapter remains
separate from accepted-order demand and the synthetic Lab. Lost sales and physical
counts retain separate additive contracts. The hosted wrapper now contains the
accessibility frontend on this candidate; the default local app remains available.

One combined acceptance failure identified an old intermittent-report hash check
that compared consumed evidence to the newly extended simulator. It now checks
`decision-v1-source.py.txt`, using the same strict original-hash boundary as the
existing decision-report test. Report bytes/hashes were not replaced. Existing
policy oracles independently compare the extended default simulator against the
original kernel. This separates historical provenance from current regression.

## Measured acceptance

- **240/240 tests**, no failures/errors/skips, in a single full discovery run on a
  fresh isolated PostgreSQL **17.6** cluster, Python **3.12.14**, Psycopg **3.3.6**.
  Owner/restricted-runner roles and existing reconciliation/planning persistence
  oracles remain exercised. This includes four new lineage tests and their seven
  graph/identity/binding faults; package counts are not summed.
- The saved count audit validates **40 controls / 86 internal nodes** without
  reassessment. The repository lineage audit validates **24 artifacts / 119 nodes**,
  **17 source maps** each matching a complete historical snapshot, and **five**
  explicit parent/freeze bindings. All published artifact bytes are unchanged.
- Saved semantic audits in complete original source views validate **768** parent
  public-safety arms, **768** disjoint calibration arms and **480** unique lost-sales
  saved trajectories. Existing ignored source/extraction/item caches are reused;
  acquisition/parsing/forecast/simulation entry points are disabled. There are
  **zero model refits or simulation replays**.
- A fresh installed wheel served outside the checkout passes **13 live localhost
  HTTPS response checks** through Caddy 2.10.2 and an explicitly trusted private CA;
  no certificate is installed in the system trust store. Baseline 12/cost 327,
  spike 18/cost 351, delay fill 11/28/cost 1171, blocked nulls, zero-demand null fill,
  evidence identity and proxy-generated 413 headers remain correct.
- The same installed wheel under actual hosted CSP also passes a real-browser
  loopback HTTP smoke: Enter runs the spike, returns focus to Run, and renders the
  18-piece/351-cost outcome against baseline 12/327. Four SVG chart surfaces render
  and no console errors/warnings are observed. At **320 × 740**, incomplete supply
  blocks the scenario, retains baseline and has document width **320**. This is a
  bounded combined smoke, not full WCAG, speech/forced-colors or download-byte QA.

[Exact combined receipt](review/research-integration-acceptance.json),
[saved-source audit results](review/research-integration-saved-audits.json),
[local HTTPS responses](review/research-integration-local-http.json),
[browser observations](review/research-integration-browser.json).
Temporary database, app, proxy and browser tab were stopped/closed; viewport
settings were restored. Local environments/caches and active branches are retained.

## Reproducibility versus authenticity

[Protocol](RESEARCH_LINEAGE_V1.md) and
[immutable manifest](review/research-integration-lineage-v1.json) bind Git snapshots,
versioned source bytes, whole artifacts, declared configuration and external input
fingerprints. Twelve historical simulator source bindings differ from the current
private-hook kernel; one hosted-receipt pyproject binding differs because the public
research extra was combined. These **13** differences remain explicit. They do not
change the reported historical outcomes and must not be silently rehashed away.

The manifest verifies complete historical source maps and source/parent/graph
identities. It does not independently authenticate suppliers, freeze/blind-count
assertions or source authors. Declared external fingerprints alone do not verify
local contents; the separate saved-source semantic audits perform that bounded
cache verification. Internal Lab UUID/calculation validation and physical-count
DAG semantics remain owned by their existing validators. This is stronger
repository reproducibility, not universal cryptographic or business attestation.

From the repository root in the existing environment:

```sh
PYTHONPATH=src python -m scripts.research_lineage --audit
PYTHONPATH=src python -m scripts.physical_count_benchmark --audit
```

Current-source guards on consumed public/lost-sales studies correctly reject the
changed kernel. For historical audits, materialize the exact heads recorded in
`review/research-integration-saved-audits.json` into disposable source views with
`git archive`; run their unchanged audit entry points against the existing
absolute ignored raw-cache directory. Do not copy an old kernel over current code,
replace accepted source hashes, delete caches, download again or regenerate a
report merely to pass a guard. Combined-code regression is a separate check.

## Remaining gates and next work

Automatic approval review rejected an earlier main merge, requiring explicit
integration-owner approval for default-branch mutation/downstream workflows.
This candidate makes that approval concrete; no main merge is retried on an
automatic goal continuation. Before an approved merge, fetch current main,
reconcile any upstream change, verify candidate ancestry and rerun only checks
justified by new changes. After integration, verify remote main contains the exact
candidate and retire only proven-merged clean task branches. CI is not monitored
or claimed by this local acceptance.

Docker/Compose runtime, Linux resource/read-only identity enforcement, crash
recovery, public DNS/ACME TLS/redirect and actual uptime remain unverified. No host,
domain, paid subscription or public service has been created. The
[hosted plan](HOSTED_LAB_PLAN.md) and [readiness operations](../deploy/lab/README.md)
remain the release gates. Local private-CA HTTPS is not public trusted TLS.

Next independent design work: a planner execution adapter with synthetic action/
receipt identities, actual reliability/planner gates, repeated knowledge clocks,
paid carryover/settlement and independent conservation oracles. The existing
prefix arithmetic comparison is not that closed loop. Advanced-model, multi-
location, capacity/calendar and scale expansions keep their evidence/contract
budgets in the all-direction ledger; no direction was discarded to declare this
candidate complete.
