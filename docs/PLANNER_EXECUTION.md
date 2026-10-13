# Actual planner execution and decision quality

Assigned 2026-10-13 by the integrated acceptance automation. The preserved
[original protocol](CONTRACT_PLANNER_LOOP_V1.md) and [seven manual controls](examples/planner-loop-manual-v1.json)
remain byte-identical to commits `55f4170` / `538d29d`.

## Fresh paired stress protocol

[Stress traces](examples/planner-quality-stress-v1.json) freeze 12 new nine-day paths
before implementation or outcomes. Each is replayed with actual proposals, Do Nothing
(decline all proposals), and fixed 18 pieces at an assessable review. All three run
the real restricted-runner planner; alternatives cannot waive missing/training/overdue
gates. Each policy observes its own previous physical execution but shares the exact
exogenous demand and first-order delay/notification rule. Initial stock is paid; no
free warmup, no closure orders, common 14-day paid window, no salvage. All admitted
orders arrive by closure. Costs 2/purchase piece, 1/ending stock/day, 10/backlog/day,
2/positive order. Exact immediate/eventual fill, ending stock/backlog, every cost
component and score/closure totals are audited independently from saved daily events.

This is a bounded synthetic stress comparison, not an unseen random efficacy study,
a universal policy winner or commercial value. No tuning on consumed controls.
The original seven cases establish execution correctness separately from this grid.

## Acceptance and implementation boundary

Owner inserts immutable new source archives; restricted runner appends reliability
and planning results. Reports are reloaded through the existing persisted validator.
Admission checks exact context, source digest and integer proposal before using the
stable scenario/date decision identity. Duplicate planning UUIDs cannot create another
order. Hidden future supplier dates and acceptances are absent from source archives.
A saved-only auditor uses events, integer conservation, FIFO and declared costs,
without calling the planner, forecast or periodic simulator. Reports/protocol/code
hashes bind committed source. Export refuses existing output files.

Implementation/results and next capability scope will be recorded here after the
frozen controls pass. Real intake, orders, deployment and public runtime remain gated.
