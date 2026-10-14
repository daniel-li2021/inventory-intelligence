# Engineering support for the decision platform

## Planning latency: retained negative finding

The [predeclared JIT protocol](examples/planning-jit-v1.json) compared default JIT
with transaction-local `jit=off` on PostgreSQL17.9 ARM64: 1/1000 keys, clean and
contradictory current stock,180-day demand, two warmups and six counterbalanced
measurements per arm/cell. All64 actual persisted planner outcomes were identical;
source hashes and session settings remained unchanged. [Raw reports/timings](review/planning-jit-v1.json.gz)
retain the complete campaign, which took51.7 seconds within its180second cap.

The large clean median was0.7686→0.7377 seconds, a4.02% reduction below the frozen20%
adoption gate. Small clean was0.03229→0.03132 seconds; contradictory large was
1.02183→1.02215 seconds. **No planning optimization was adopted.** The earlier
~3second ARM64/JIT profile remains historical evidence for a different runtime/
workload; it was not reproduced here. No x86 or one-second production SLO claim.

```sh
python -m unittest tests.test_planning_jit_saved -v
```

## Scalable inspection without relaxing decision gates

`persisted-evidence-page-v1` reads PostgreSQL reliability children or whitelisted
planning JSONB subsections without transferring the full report into Python.
Pages are1–100 records, at most256 KiB including metadata. Metadata itself is limited
to64 KiB before transfer. A single oversized record blocks; it is never truncated.
Supported planning sections are projection, training days, one explicitly indexed
candidate's training days, and holdout training days. Missing arrays are unknown,
not empty successful evidence. Reliability records have stable C-collated identity
order; planning records retain zero-based original ordinals.

Each read uses an idle restricted `ii_runner`, Repeatable Read/read-only transaction,
five-second SQL deadline, complete run/content SHA256 binding, exact totals and
next-page information. Pass the returned binding for later pages; changed content
or selection rejects. Hashing still scans the complete server-side content, so this
is a bounded client-memory/readability repair, not a dense-producer latency result.
Pages are **inspection-only**: they do not claim whole-report semantic validation,
waive the original 2 MiB/16 MiB readers, or feed decisions/Copilot as authoritative runs.
Existing product catalog interning and validated read caching remain separate.

Independent PostgreSQL controls retain100 reliability records above 2 MiB and an
18,000-day training array above 16 MiB. The original readers continue to reject them;
small pages expose exact original quantities/ordinals, stable bindings, first/last
pages and source identity. Oversized pages/records, invalid bounds, wrong roles,
missing sections and wrong bindings reject. No full-scale producer guarantee follows.

```sh
python -m inventory_intelligence.evidence_pages --kind planning --run-id SAVED_UUID --section candidate_training --candidate 0 --page-size 10
python -m inventory_intelligence.evidence_pages --kind planning --run-id SAVED_UUID --section candidate_training --candidate 0 --page-size 10 --page 2 --binding FIRST_PAGE_BINDING
python -m unittest tests.test_evidence_pages -v
```

## Upgrade, recovery and observability boundaries

No PostgreSQL schema migration is required for these additions: existing immutable
source/result schemas already support saved runs and new supply batches. Fresh
bootstrap refuses populated operational schemas. SQLite adds transfer/review tables
and immutable triggers idempotently beside the original decisions/events; reopening
an existing journal retains old identities/history. No destructive reset, automatic
source repair, schema replacement or compatibility shim was added.

New paths keep the hosted4096byte body limit, admission rate/concurrency limits,
loopback/same-origin write boundary, explicit unavailable/retry/stale states and
source-bound exports. Synthetic studies retain operation/runtime/source identity,
exact counts, durations, resource bounds, failure/recovery and losing outcomes.
Tests cover concurrent reservation/receipt, transaction failure, version-conflict/
late-admission rollback and last-good archive publication. These checks complement
retained crash/restart evidence; they do not replace sustained HTTP/public security
campaigns. [PLAN](PLAN.md) owns remaining hardware/continuity/human/public gates.
