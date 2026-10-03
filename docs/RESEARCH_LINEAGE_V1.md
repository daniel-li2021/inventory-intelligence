# Research integration lineage protocol — v1

This is a read-only reproducibility manifest for the combined research candidate,
not signed source attestation or a new benchmark. Preserve all published report
bytes. Old evidence stays bound to its original code; integration tests assess
the combined code separately. Never replace consumed source hashes with current
hashes, silently regenerate studies or import item-level public data into the Lab.

## Fixed delivery boundary

Record the exact already-published PR 14–23 heads and main `f6d3d16`. All ten heads
must be ancestors of the candidate. Eight explicit branch merges include stacked
PR 15/17 via PR 20; no commit is rewritten or main changed. The manifest names
retained reports/receipts, their bytes, source hashes, and explicit parent/freeze
references. Each report's source map must match one complete retained Git snapshot
from that package history. A changed shared file is reported as current drift,
not repaired or interpreted as a failed historical study.

Dependency nodes distinguish Git snapshots, versioned source files, full saved
artifacts, policy/config metadata, and declared external input fingerprints.
Public local inputs can be hashed when available; missing local inputs remain
explicitly unavailable. Their contents and item identities are never published.
A graph edge establishes byte/metadata dependence, not evidence authenticity,
causal identification, real demand, physical warehouse truth or model validity.

The core archived Lab evidence is also included. Its internal UUID/calculation
trace validation and the physical-count artifact's own DAG remain owned by their
existing semantic validators. The repository manifest binds those artifacts as
whole immutable bytes; it does not flatten or replace their internal semantics.

## Fail-closed audit

An independent audit rebuilds the expected manifest from pinned Git/file bytes
without model invocation, simulation, source acquisition, workbook parsing or
operational writes. Require exact report/receipt identity, one-snapshot source
coverage, parent bindings, canonical node identities, no missing edges/cycles,
exact denominator counts and declared current drift. A changed artifact, an
invented source hash, dropped dependency or rehashed invalid graph must fail.

Combine this with current-code regression and fresh disposable PostgreSQL
acceptance. Run saved semantic auditors in their complete original code snapshots
when their current-source guard correctly rejects a changed shared kernel.
Temporary source views are read-only inputs to audits, not a replacement for
combined-code regression. Use existing ignored local caches, not refits/replays.

## Release boundary

Passing this protocol proves a reviewable candidate and retained reproducibility
links. It does not prove main integration, remote CI, public hosting, calibrated
service, population independence or production readiness. No branch retirement
or main merge occurs until the integration-owner approval gate is satisfied.
