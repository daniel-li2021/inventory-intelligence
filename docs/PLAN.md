# Engineering readiness plan

Status: **reference/stability confirmation pending**. [STATE](STATE.md) owns
integration mode; [ROADMAP](ROADMAP.md) owns independent product acceptance.
The local pilot, continuation and single SQL optimization are complete. Their
outcomes, failures and exact denominators live in [RESULTS](RESULTS.md#engineering-continuation)
and [EVIDENCE](EVIDENCE.md#engineering-continuation); reusable recipes live in
[OPERATIONS](OPERATIONS.md#frozen-local-workload-recipes-for-follow-up).

## Remaining execution

| Gate | Available evidence / remaining work | Next action |
|---|---|---|
| Reference batch/planning | Five ARM64 Linux campaigns retain 30 reconciliation and 30 selected-plan outcomes; planning misses the one-second threshold. PG17.9/ARM64/Python3.12.14 correctness is checked. Exact x86-64/Python3.12.12/two-date timing remains open. | Obtain an available authorized reference host; reuse frozen inputs and run only missing confirmation cells. |
| Sustained HTTP | One continuous 30-minute campaign passes 2700/2700. Short, discontinuous and interrupted windows do not qualify. | Run two further continuity-verified campaigns plus missing sparse rate/client cells, subject to the route sample floor and declared budget. |
| Producer/reader envelope | Serial100, the 1/10-key 30%-zero backtest grid, both original reader limits and 100k-movement recovery are measured. Bounded page inspection is separate from complete semantic acceptance. | Measure serial1000, remaining archive-growth/defect cells and dense-producer/whole semantic-reader acceptance only within the declared ceiling. |
| Runtime and human use | The October 15 public smoke verifies trusted TLS/readiness and a brief developer journey. Sustained public serving, cold start, independent comprehension and assistive-technology checks remain open; proxy slow bodies close or return 504 instead of 408. | Keep public smoke separate from runtime capacity; use ROADMAP for human acceptance and retain proxy timeout behavior as an unresolved gap. |

Next action: obtain an available authorized runtime for missing continuous HTTP/
rate/client cells, then the exact reference cells. This cleanup assigns no new
benchmark campaign, paid host, real/company intake or engine optimization.
Retain failures, clock discontinuities and limited cells. The original continuation
exceeded its 180-minute target (192.8 minutes); guard repairs do not erase that result.
No new planning/JIT benefit follows from reusing consumed studies.

Update this table and STATE after material progress. Retire this plan only after
its remaining work is completed or explicitly superseded; extract durable outcomes
into KB/RESULTS/EVIDENCE first. Conditional improvements belong in
[KB](KB.md#engineering-gaps-and-hypotheses).

## Questions and supported claims

### B1 — real reconciliation size, skew and historical batch growth

**Question:** what limits reconciliation: selected movement/key count, unrelated
history scans, skew, defect evidence or persistence? **Claim if measured:** exact
reconciliation over K declared SKU/warehouse keys and M movements in X median/
maximum seconds at Y peak memory on the recorded host; largest passing and first
limited cells disclosed. No claim about other hosts, retailer schemas or live SLAs.

- Clean ladder: (K,M) = (10,1,000), (100,10,000), (1,000,100,000),
  (10,000,1,000,000), exactly 100 raw movements/key on the uniform controls.
  K is inventory grain count, **not** interchangeable with SKU or warehouse count.
  All raw and eligible rows, source snapshots, output findings and bytes reported.
- At K=1,000/M=100,000: uniform versus 80% of movements assigned to 1% of keys;
  one warehouse versus ten at constant K; 20% of eligible movement rows as paired
  valid transfer legs. These shapes exercise existing contracts, not allocation.
  Specify integer allocation/tie rules and paired transfer quantities in the freeze.
- Hold selected 100,000 movements constant; add 0/1/9 unrelated same-size archived
  batches. Selected totals and findings must stay identical. Natural keys repeated
  in other batches remain legitimate; this explicitly tests extraction-scope safety.
- Separate 5% pending, 5% future-effective and 5% above-watermark exclusions with
  disjoint row IDs; do not silently change raw manifest counts. Put the detailed
  inclusion map and exact expected balances into each immutable fixture manifest.

Measure the actual run_checks read/check/JSON/persist/commit path with ii_runner.
Time its read-only SQL separately for diagnosis, not as a substitute for end-to-end.
Record insertion/load/ANALYZE durations separately outside the operation interval.

### B2 — gated forecasting/planning and retained research history

**Question:** does per-SKU demand access or repeated fold evidence dominate time/
memory as a shared archive grows? **Claim:** measured serial forecast/plan and
backtest throughput under current evidence semantics, not a new bulk API.

- Shared demand archives with 10/100/1,000 keys × 180 complete days; report day
  rows AND raw order/revision rows (one possible positive line/day, 30% zero days,
  5% additional known revisions, plus separately identified late revisions).
  Generate these rates with frozen exact allocation, not random achieved ratios.
- Planning horizon 7/28/90, valid L/R decomposition frozen before results; safety,
  MOQ, pack, commitments and confirmed inbound fixed across comparisons. Mean is
  the operational baseline. Do not change models to manufacture a timing gain.
- First measure one selected key while the archive grows; then a **serial driver**
  over 10/100/1,000 keys. Publish requested, eligible, blocked and completed keys
  and elapsed seconds; keys/second uses actual completed keys, not input cardinality.
- Separate actual run_plan, run_forecast, and full run_benchmark. run_plan
  reruns inventory reliability on the selected source batch; record that ledger
  size as well as demand size so repeated whole-batch checks are visible. Backtests use
  180/365/730-day histories on 1/10 keys with existing origins/holdout boundaries.
  Pilot smaller cells first; large nested reports may legitimately exceed 16 MiB.
- Complete demand versus a known constrained/missing-day control; complete versus
  incomplete supply; an unrelated-history control. Preserve blocks and source
  clock visibility. Exact immutable-input checks are outside the timed interval.

### B3 — finding density, report size and consumer limits

**Question:** can the evidence path remain correct and fail closed when defects or
retained per-origin evidence grow? **Claim:** a measured producer/reader envelope
with explicit capacity limits, rather than universal evidence-size support.

- Clean plus 0.1%/1%/10% independently labelled bad raw rows at the 100k tier:
  snapshot discrepancies, duplicate natural identities, invalid transfer pairs,
  missing coverage and late clocks are separate cells. A defect row is not a
  finding: publish expected affected buckets/groups, findings and blocked buckets.
- Measure full producer persistence, raw/serialized bytes, DB relation/WAL growth,
  reader DB fetch and semantic validation separately. Exercise reliability
  Copilot limits at 999/1,000/1,001 findings and actual encoded bytes on either
  side of 2 MiB; planning reader just below/at/above its 16 MiB bound. Byte thresholds
  must use each loader's actual accounting representation, not assumed file size.
- Expected over-limit rejection is a capacity result, not an unexpected runtime
  fault. Report its latency/resources and preserved DB result identity. Do not
  truncate, raise caps or convert rejected evidence to empty/pass/zero.

### B4 — actual network Lab capacity, admission and recovery

**Question:** what is completed under a real Uvicorn process and optional Caddy
proxy, and what happens to clients and resources under overload? **Claim:** bounded
demo throughput and rejection/recovery on the recorded topology, not public uptime.

- Separate local create_app computation/HTTP from **unchanged** HostedLab with its
  2 tokens/second, burst20, active4; single Uvicorn worker/limit16/backlog32. A
  configured allowance of 2/s is not proof of sustained successful 2 requests/s.
- Fixed route workload: scenario POST 60%, Lab GET 20%, evidence GET 20%; freeze
  clean/spike/delay/incomplete proportions and response truth by route. Also run
  homogeneous POST and evidence GET diagnostics so the mixed workload cannot hide
  the expensive route. Static assets and health are accounted separately.
- Hosted sustained offered rates 0.5/1.5/2/3/5 requests/s; independent schedules
  and seeds, at least three campaigns. Preliminary bounded runs are allowed but
  not sufficient to claim a stable percentile envelope. Full confirmation cells
  require at least 1,000 completed admitted requests per relevant route across
  campaigns; publish per-campaign counts and latency, not just pooled percentiles.
- Separate instantaneous bursts 20/40 requests and clients 1/4/8/16; slow/chunked
  bodies, >4 KiB requests, disconnects and recovery after overload. These faults
  must preserve 408/413/429/503 behavior and valid response evidence. No retries
  inside the timed measurement; if retry behavior is studied, count it separately.
- Use an external load-generator process with scheduled arrival timestamps:
  planned/actually issued/admitted/succeeded/rejected/timed-out/dropped/backlogged
  are distinct denominators. Log scheduler lag and client CPU; reject a campaign
  where the client cannot generate its predeclared offered load. A wait-for-response
  loop alone can hide queueing as the server slows (coordinated omission).
- Record scheduled-to-complete, issued-to-complete and rejected-request latency
  separately, actual success/s and 429/503/5xx/timeout rates, response bytes,
  process/thread counts, sampled RSS/CPU and RSS slope. Use 30-minute sustained
  checks as a minimum per confirmation campaign, extending duration/campaign
  count to reach the route sample floor. Low-rate and heavily rejected cells may
  remain descriptive under the budget; this is not multi-day uptime evidence.
- Test the actual Linux Compose 0.5 CPU/256 MiB Lab and 0.25 CPU/128 MiB proxy
  envelope separately from the unconstrained reference host. If Docker is absent,
  publish that test as **not measured**; native macOS proxy checks are no substitute.

The open-versus-closed load distinction follows
[Grafana's primary explanation](https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/open-vs-closed/).
This is a methodology reference, not a requirement to add k6 or a new service.

## Common measurement protocol

### Reference environment and bounded execution

Propose one disposable local/dedicated Linux x86-64 host: **4 allocated vCPUs,
8 GiB RAM, SSD**, Python3.12.12/Psycopg3.3.6/PostgreSQL17.9 matching CI pins.
Record actual CPU model, virtualization, kernel/OS, RAM/limits, storage/fs,
database settings (shared_buffers, work_mem, synchronous_commit, checkpoint/WAL,
max_connections), exact dependency/image hashes, schema/index definitions,
wheel/code/fixture commits and byte hashes. Snapshot dependency resolution;
current general CI does not freeze all transitive Lab dependencies. Existing
hosted requirements provide a bounded pinned runtime reference. Never combine
macOS and Linux timings into a single distribution or use variable CI machines
as the reference performance host. CI remains a correctness/runner smoke gate.

Proposed initial pilot limit: **2 hours wall time, 8 allocated CPU-hours,
30 GiB added disk, max 6 GiB combined DB/runner RSS**, including fixture setup and
diagnostics. Memory accounting uses cgroup totals or proportional shared-memory
accounting, not a naive sum of PostgreSQL processes that double-counts shared
buffers; disclose the method. Per individual batch call deadline 60s; DB statement deadline 55s and lock wait
5s only in benchmark connections, with cancelled work/rollback recorded.
Bound full confirmation to a separately reviewed **8-hour wall/32 CPU-hour**
program budget before launch. These budgets are caps, not duration estimates or
permission to purchase a host. Predeclare cell priority: first confirm the
1,000-key/100k reference batch, selected-key planning at the 1,000-key archive,
reader-limit controls and hosted 1.5/s; then confirm the largest passing and first
limited exploratory cells if budget remains. Every claimed envelope point needs
its stated confirmation repetitions. Pilot-only cells stay labelled exploratory;
the complete factorial grid is not required within one budget. Large or slow cells may remain unmeasured under
the budget; publish the exact stopping point rather than shrink the claim silently.

### Repetitions, order and cache states

- Use perf_counter_ns for monotonic client elapsed intervals, and separate CPU
  clocks/counters. [Python's timing documentation](https://docs.python.org/3.12/library/time.html#time.perf_counter_ns)
  specifies the clock boundary. Record timer and sampling overhead separately.
- Batch confirmation: **five independently restarted campaigns**, over at least
  two dates on the same reference host. After fixture restore/load and ANALYZE,
  retain two warmup observations separately, then six measured serial calls per
  cell/campaign: **30 warm-state samples/cell**. Fresh identical DB initial state
  per campaign; instrument results-table/WAL growth within each campaign.
- Counterbalance cell order with a recorded seed; vary physical load order in a
  separate fixture-layout sensitivity cell, not invisibly between baseline runs.
  No concurrent pipeline, model calls, ingestion or host-intensive job during
  measurements. Record resource contention; do not selectively discard slow runs.
- “Process cold” means a new Python process; “DB cold” means restarted PostgreSQL
  with empty shared buffers. A DB restart **does not clear OS page cache**. Capture
  first-access latency separately and disclose OS cache as uncontrolled unless a
  disposable host/cache reset makes it known. Never reset system caches casually
  on the user's workstation. Warm-state requires fixed warmup and buffer evidence.
- Median/IQR/min/max and per-campaign medians for batch calls; raw n always shown.
  With n=30, tail percentiles are exploratory. HTTP nearest-rank p95 requires the
  predeclared sample floor above; p99 needs at least 10,000 relevant completed
  requests or is labelled insufficient. These are proposed reporting rules, not
  proof that those sample sizes establish statistical population confidence.
- Bootstrap, if reported, resamples independent campaigns/fixture blocks rather
  than dependent requests as independent trials. Five campaigns provide limited
  inference; show variability and descriptive intervals without a universal SLA.

### Correctness accompanies every performance point

The independent expected outcome must not call the checker/planner it judges.
Use explicit hand controls plus independently derived integer balances, defect
labels, cutoff inclusions and controlled constant/seasonal forecasting outcomes.
Freeze expected quantities/statuses/identities/digests before engine execution.
Reconcile every affected key and exact findings, not only counts. Check retained
source hashes before/after and result transaction completeness. The performance
run cannot modify input permissions, filter away bad data, use future evidence or
disable semantic validation. No operational/public-source writes are included.

Keep fixture generation, loading, stats collection, oracle comparison and evidence
hashing outside the primary operation interval, but report their wall/resource
costs separately. SQL-only profiling excludes Python serialization/persistence;
full-path timing includes them and DB commit. Do not subtract noisy diagnostic
durations to invent a precise component cost.

Use EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON, TIMING OFF) on the existing read-only
SQL as a separately marked diagnostic pass. ANALYZE executes the statement and
adds measurement overhead; its plans are not the primary timing distribution.
Record estimate/actual rows, scan/filter work, buffer hits/reads, temp spills and
planning/execution time. Costs are planner units, not milliseconds.
[PostgreSQL17 reference](https://www.postgresql.org/docs/17/using-explain.html).
No pg_stat_statements dependency is required for the first runner.

### Proposed envelope, limits and result format

Reference batch question: can **1,000 keys / 100k movements** complete correctly
with median ≤10s and every call ≤60s within the declared memory cap? Test 10k/1M
as an exploratory upper tier even if it fails. Planning question: selected-key
forecast/plan median ≤1s at the 1,000-key/180-day archive and a 100-key serial
planning batch ≤120s, with exact eligibility. These are proposed investigative
thresholds; smaller explicit envelopes remain valuable results.

Hosted question: at offered **1.5/s**, do valid admitted responses have p95 ≤1s,
zero unexpected 5xx/timeouts, and stable resources across three campaigns, within
the actual wrapper and Linux limits? Rejection behavior is a separate capacity
boundary. Do not count quick 429 responses as successful throughput. State maximum
tested offered rate meeting the **entire** declared envelope; do not interpolate
capacity between sparse rates. Any correctness violation prevents a readiness
claim irrespective of speed; every timeout/OOM/block/rejection remains in output.

Required artifacts for a fresh confirmation: frozen benchmark contract,
synthetic workload manifest/independent oracles, environment+schema manifest,
raw per-call/request JSONL, per-campaign resource/DB-plan logs, exact case statuses,
compact JSON summary, capacity/result report and independently verifiable hashes.
Samples include case/seed/campaign, size, cache/phase, operation, status, elapsed,
CPU/RSS, output bytes, counts, timeouts and oracle outcome. Sampling can miss RSS
peaks; include OS/cgroup high-water values and state platform units. Preserve raw
failures and censored ≥deadline timings. Never replace a timeout with the deadline
as a successful sample or compute completed-only latency without its denominator.
