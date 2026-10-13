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

Implementation and validation are complete within this local synthetic scope.
Real intake, orders, deployment and public runtime remain gated.

The additive [one-review contrast](SYNTHETIC_REPLAY.md#one-review-decision-contrast-predeclared-arithmetic-controls)
compares a selected saved actual proposal, no action and a pack/MOQ alternative over
33 common paid days. It shares FIFO physical execution with this runner, includes
initial stock/confirmed inbound/purchase/holding/backlog/setup and preserves blocked
gates. It uses declared future synthetic demand and makes no later review/order;
it extends the user comparison journey, not this frozen repeated-policy study.
The original protocols, stress traces and archive bytes remain unchanged.

## Original control erratum

The first actual-run check rejected one of the seven original controls. For cold
shortage, zero opening stock and five forecasts of 3 yield balances
−3/−6/−9/−12/−15. Prefix safety 2 therefore needs 17 pieces, rounded to pack 6: 18,
not the original 12. No production kernel or frozen original was altered.
[Explicit erratum](examples/planner-loop-errata-v1.json) records the independently
recalculated outcome: stock 0/0/9/6/3/0/0/0/0, backlog 3/6/0/0/0/0/3/6/9;
12 immediate and 18 eventual pieces of 27; total cost 36 purchase + 18 holding +
720 backlog + 2 setup = 776. The original expectation must continue to reject.
The corrected control is a diagnostic arithmetic repair after first execution,
not fresh held-out decision-quality evidence. The 12 new stress traces remain frozen.

## Measured acceptance

[Saved actual archive](review/planner-loop-v1.json.gz) contains seven controls plus
36 paired policy cells: 129 real `run_checks`/`run_plan` reviews, each reloaded through
the persisted report validator. The committed source binding is retained at `c8322f7`;
current auditors add stricter source/key/UTC/gate controls without rewriting bytes.
Portable recovery snapshot `6fff524` retains the original protocol/control bytes;
the original paused commits remain local and unmerged.
All seven corrected trajectories/costs match a [second fresh database](review/planner-loop-confirmation.json).
The original control is six passes/one rejected oracle; the erratum is explicit.

Actual proposal costs versus Do Nothing versus fixed-18 across all 12 stress traces
sum to 3160 / 11350 / 6134 synthetic cost units. These sums describe the frozen grid,
not expected commercial economics. Actual is cheaper than fixed-18 on 12/12 and
Do Nothing on 11/12; quiet reverses the comparison (330 / 160 / 760). Eleven nonzero
actual cells have immediate fill 1; quiet fill is null. Seven manual controls retain
shortage/blocking counterexamples and must not be pooled into that service claim.

## Durable synthetic feedback contract

`Journal` atomically appends source-bound decisions and confirmed inbound, then ETA
and exact partial receipt events. Natural scenario/date identity prevents repeated
planner UUIDs from creating another order. Source case/input/context digests remain
inspectable. SQLite triggers reject update/delete; immediate transactions serialize
admission and receipt conservation. Snapshot reads use one coherent transaction.
Knowledge is at business-date grain; backdated events and new admissions reject globally across decisions. An identical event ID
and payload repeats harmlessly; conflicting identity or overreceipt rejects.
The local sandbox supports at most 256 events; pieces remain exact decimal strings
at the new API boundary. Positive receipts cannot precede the original feasible
promise; ETA notifications cannot precede their known date. Blocked/zero reviews
never create inbound. These are local synthetic constraints, not supplier calendars,
producer authentication or an operational exactly-once executor.

`publish_supply` is a separate synthetic-owner stage. It requires explicit current
reservation evidence and policy, filters journal commitments by SKU/location, and
inserts a fresh supply batch without changing source stock or earlier reports. Its
PostgreSQL write and the SQLite journal are separate boundaries; no cross-database
atomic production handoff is claimed. Independent feedback control: initial 12-piece
proposal becomes confirmed inbound; new actual plan is 0 with balances 7/4/13/10/7,
while the original saved proposal stays 12. Partial receipts 5 then 7 conserve 12;
reopen, concurrent overreceipt, transaction failure and historical views pass.

## Local demo and reproduction

With the existing `.[lab]` environment installed:

```sh
python scripts/run_local_demo.py --port 8020 --journal output/local-demo.sqlite
```

Open `http://127.0.0.1:8020/#/execution`. The demo binds loopback only and enables
synthetic journal writes explicitly. Exercise Admit 12 → Receive 5 → Notify ETA →
Receive 7, then choose March 8/9/11 history. Each event is durable/idempotent; no reset
or source repair is implicit. Use a new journal path for a new isolated experiment.
Default `inventory_intelligence.lab_hosted:app` remains read-only, including the
execution archive, and has no journal write routes. No database/Node/model runtime
is needed for either packaged view or local journal; a database is required only
for separately authorized synthetic owner staging/live research.

```sh
PYTHONPATH=src python scripts/export_planner_loop.py --audit --output docs/review/planner-loop-v1.json.gz
PYTHONPATH=src python -m unittest tests.test_planner_loop_saved tests.test_workflow tests.test_execution_api -v
```

Live `tests.test_planner_loop` requires fresh disposable owner/`ii_runner` connections
via `TEST_DATABASE_URL` and `DATABASE_URL`; bootstrap follows VALIDATION. Export binds
committed protocols/implementation, never overwrites an archive, and uses a separate
fresh database. Original studies/holdouts are reused, never tuned or rerun for a new
accuracy claim. [Final acceptance](review/increments-0-4-acceptance.json).
