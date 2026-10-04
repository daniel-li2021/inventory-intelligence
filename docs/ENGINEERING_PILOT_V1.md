# Frozen local engineering pilot v1

Assigned 2026-10-03: implement and run an exploratory pilot on the existing Mac.
This supplements [PLAN](PLAN.md); it does not change its reference-host SLOs,
confirmation repetitions, two-date requirement or separate eight-hour gate.
No paid resources, models, public data, deployment or paused features are included.

## Workload and independent truth

Freeze this protocol and generated manifests before executing engines. Stable
case prefixes, source-code/SQL hashes, full source hashes, independent expected
quantities and exact duplicate row groups identify each cell. Sources are loaded
once and never repaired. Use a fresh isolated PostgreSQL database and ii_runner
for every measured production operation.

B1 uses 100 raw receipts/key, quantity +1 and opening 1,000. Clean tiers are
10/1k, 100/10k, 1k/100k and exploratory 10k/1M. At 1k/100k, skew assigns exactly
80k rows to the first 10 keys, then 20k to the remaining 990; divide by key count
and assign remainders to ascending key indices. Ten warehouses keep K fixed:
SKU index is floor(key/10), warehouse is key modulo 10. Transfer controls replace
the first 20 rows/key with quantity -3 on even warehouses and +3 on the adjacent
odd warehouse; each pair shares SKU, transfer, effective instant and sequence.
Expected balances are 1,000 + 80 - 60 / +60. Exclusion controls use disjoint first
5 pending, next 5 future-effective, next 5 above-watermark rows/key; 85 remain
eligible, snapshot 1,085. Raw manifests always retain 100/key.

Selected history controls keep 1k/100k fixed and append one, then eight additional
same-size unrelated batches. Repeat natural event/line/leg identities across
batches with distinct row IDs. Compare exact selected semantics and source hashes.

B3 duplicate cells label the first 100/1k/10k raw movements bad (0.1/1/10% of
100k). Consecutive pairs share natural identity, without deleting rows. Expected
R002 groups are 50/500/5k; blocked keys are 1/10/100 and R001 is not_assessable.
Other rules pass; non-R001 quantities remain null. An additional quantity probe
changes every snapshot by +1 in a separate fixture, requiring independently known
expected, observed and delta quantities for every key. These are producer cells.

Reader-only capacity fixtures are explicitly synthetic saved reports, separate
from engine-produced evidence. Compact valid R001 findings isolate 999/1,000/1,001
finding controls. ASCII padding isolates reliability 2 MiB and planning 16 MiB
at threshold -1/0/+1 using the loaders' actual PostgreSQL row_to_json accounting.
The subsequent JSON/semantic validator has its own accounting; record its result
too. Never infer an accepted reader envelope from DB bytes alone. Retain exact
run identities, fetch/validation time, size and history-preservation observations.

B2 archives have 10/100/1k grains and exactly 180 days/key. Each ten-day block
starts with three zero days followed by seven quantity-10 lines (54 zeros/126
positive lines per key). Add same-quantity revision 2 to every twentieth positive
line globally, and late quantity-1,000 revision 3 to every hundredth. Allocation
uses one-based positive-line indices; counts are floor(total/20) and floor(total/100).
Late revision source and observation clocks are origin +1 day and remain invisible.
Mean forecast is exactly 7/day at the winter Pacific midnight origin 2026-01-02
08:00 UTC. Planning has a separate K-key, zero-movement ledger, opening/snapshot
20, reservation 3 on day 0, confirmed inbound 5 on day 1, lead 2, review H-2,
safety 2, pack 6, MOQ 10. H=7/28/90 needs 29/176/610, rounded orders 30/180/612.
Complete and stockout-day/incomplete-supply controls preserve null blocked outputs.
Selected-key forecasts/plans and serial ten-key drivers are distinct measurements.
Full rolling backtest growth and larger serial grids remain separately identified.

## Boundaries and resources

At most two hours including fixture setup; at most eight observed CPU-hours,
30 GiB added disk, 6 GiB conservative sampled RSS upper bound. Native macOS lacks
cgroup/PSS accounting: a sum of process RSS double counts shared pages, so use it
only as a conservative abort guard, never as measured combined memory. Per-call
Python ru_maxrss is bytes on macOS and KiB on Linux; it includes setup/interpreter
and is a process high-water value, not a precisely isolated operation peak.
Disclose sampled peaks/CPU and unverified platform enforcement. Python/SQL call
deadlines are 60/55 seconds and benchmark lock waits five seconds. Connections
are disposed after cancellation; verify no partial persisted children afterwards.

Each exploratory batch cell uses a fresh worker process and three serial calls;
the first is retained as first-access, the other two as repeat-access. These are
neither confirmed warm samples nor DB/OS-cold observations. No percentile or SLA
claim follows. Operation intervals include read/check/serialize/persist/commit;
fixture COPY, ANALYZE, oracle checks, JSON-file writing, hashes and EXPLAIN are
outside them, with their costs reported separately. Raw failures stay in JSONL.
EXPLAIN ANALYZE runs only read-only SQL as a separate diagnostic, never timing
subtracted from the producer. An individual blocked cell does not cancel unrelated
small objectives; global budget exhaustion stops further measurements honestly.

The environment manifest records actual versions/dependencies, schema/index/SQL
hashes, DB settings and available host/storage facts. Native Mac results never
stand in for Linux x86-64, PostgreSQL 17.9, Python 3.12.12, container enforcement,
public TLS, crash/restore recovery, human accessibility or multi-date confirmation.
