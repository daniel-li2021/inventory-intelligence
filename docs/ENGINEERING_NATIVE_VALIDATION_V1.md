# Native HTTP and recovery pilot v1

This is part of the assigned existing-Mac exploratory pilot in [PLAN](PLAN.md).
Freeze each script hash and protocol receipt before its first request/fault. Run
after batch measurements, within the same two-hour / eight observed CPU-hour /
30 GiB / conservative 6 GiB guard budget. No reference-host, public hosting,
Linux enforcement, statistical percentile or RTO/RPO claim follows.

## B4 preliminary network

Serve unchanged HostedLab in one Uvicorn process, active4, burst20, 2 tokens/s,
worker1/limit16/backlog32. Separate external client process schedules arrivals
independently of responses; no retry. Start fresh server for each cell. Native
loopback, no proxy, existing Python environment; retain exact script/version
and packaged archive identity. Static readiness calls are separate from API load.

Three hosted campaigns each use 20 seconds at offered 1.5/s (30 planned requests)
for mixed, homogeneous scenario POST and homogeneous evidence GET. Mixed route
order repeats POST/POST/POST/Lab GET/evidence GET. The POST scenario rotation is
clean, 125% spike, hidden delay 3 days and incomplete supply, with deterministic
request-index allocation. Every admitted body must satisfy the hand quantities
and null controls from the hosted acceptance checker. One corresponding local
create_app campaign distinguishes HTTP/computation from admission wrapping.

Client concurrency is 16; retain planned, issued, succeeded, rejected, timed-out,
incorrect, dropped and backlogged counts, scheduling lag, both latency clocks,
bytes/digests, client CPU/RSS and sampled process-resource observations. Scheduling
lag above 100 ms invalidates the offered-load campaign. No quick 429/503 enters
successful throughput. Twenty-second campaigns and per-route samples are only
preliminary; every p95/p99 confirmation remains insufficient, even when all pass.

Separately offer bursts 20/40 with up to 40 client threads, retain all responses
and lag, then wait 10.2 seconds for token refill and verify the evidence endpoint.
Slow partial bodies (>5s), declared 4,097-byte bodies, valid chunked bodies and
client disconnection exercise 408/413/200 and subsequent recovery. These cells
do not cover the full 1/4/8/16-client or sustained-rate grid, proxy behavior,
enforced Linux limits, 30-minute stability or the 1,000-request route floor.

## V2 native synthetic faults

Use a fresh two-key `engineering_recovery` database in the explicitly named
disposable pilot cluster. Real run_checks persists two +1 snapshot discrepancies.
Hold an independent owner lock on reliability.findings; observe the restricted
writer waiting at its child insert, after its transaction has inserted parent and
checks. Other connections must see no uncommitted parent. Kill the client process,
release the lock, and require identical prior history and source/result hashes.

Repeat the lock boundary, then independently commit +1 to both snapshots and
advance snapshot/batch observation time by one second in this
separate fault fixture. This deliberate source-owner mutation is recorded, not a
repair of benchmark inputs. Release the writer: its retained repeatable-read
findings must still have delta +1; the next run evaluated at the new observation
time sees delta +2. Compare exact
quantities and identities rather than a count-only snapshot assertion.

Immediately stop only this disposable PostgreSQL cluster and restart it with its
saved configuration. Require identical committed source/result hashes and history
after WAL recovery. Dump the small synthetic recovery database in custom format,
restore to a new `engineering_restore` database, and require byte-stable canonical
source/result hashes and all saved run IDs, checks, findings and quantities.
Retain observed duration, dump bytes/hash and exact outcome per fault.

This verifies a small native synthetic recovery path. Application crash under
live load, full-history/large backup recovery, Linux faults, independent human
cold-start/speech/zoom/forced-color review and public release stay unmeasured.

## B2 supplemental backtest control

Measure full run_benchmark and its actual saved-report reader for 180/365/730
days, first with one key and then ten keys in the shared archive. Each call selects
one key. Use an independently specified constant quantity 4/day: all three methods
must predict exactly 4, every actual is 4, MAE/bias/WAPE are zero, and the declared
tie order selects naive. This is a constant-demand correctness/size control, not
the canonical 30%-zero demand grid or a ten-key serial throughput measurement.

Known revision 2 is added to every twentieth one-based global line; late revision
3 to every hundredth, both late clocks strictly after evaluation. Every complete
day is available, including the evaluation boundary. Freeze exact origin indices
28,35,... through history_days-56 before execution; final holdout starts at
history_days-28. Preserve all raw revisions, exact source hashes, independent
expected quantities/scores and explicit reader rejection. One fresh-process call
per cell is exploratory; no reported percentile or stable envelope follows.
