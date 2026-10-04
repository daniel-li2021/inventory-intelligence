# Engineering readiness plan

Status: **local exploratory pilot authorized; execution complete**. Current phase/mode
and scope gates live in [STATE](STATE.md). The user approved implementation and a
pilot on the existing Mac on 2026-10-03. Proposed reference workload/SLOs below
remain unchanged; Linux/reference confirmation and the separate eight-hour program
are deferred. No feature resumption, paid host or public deployment is authorized.

## Phase handoff and checkpoints

- [x] P0: inspect green correctness baseline, preserve paused planner work and
  publish [engineering readiness evidence](KB.md#engineering-gaps-and-hypotheses).
- [x] Local decision gate: retain proposed workload/SLOs; actual Mac runtime and
  two-hour exploratory pilot approved. Frozen recipes and outcomes: [results](RESULTS.md#local-engineering-pilot),
  [source/evidence](EVIDENCE.md#local-engineering-pilot), [commands](OPERATIONS.md#engineering-pilot).
- [x] P1 local implementation: minimal deterministic runner and independent controls;
  B1/B3 and small-to-medium B2 executed. Limited cells are retained, not retried as successes.
- [ ] P1 reference confirmation: reviewed Linux host/runtime and five campaigns over
  two dates. Local samples do not satisfy this gate.
- [x] P2 local subset: preliminary native HTTP, supplemental backtest growth and
  interrupted-writer/snapshot/crash/restore controls completed. Initial restart
  harness failure is retained alongside the repaired check.
- [ ] P2 remaining: Linux/container enforcement, other defect/serial/load grids,
  full HTTP confirmation and independent human checks. These remain unmeasured.
- [ ] P3: only after confirmed evidence, one targeted change plus paired confirmation;
  otherwise preserve the baseline. No engine optimization made during this pilot.

Record resumable task status, blockers and the next action here; update STATE at
material checkpoints. This near-term plan owns pending engineering execution;
other research possibilities remain conditional knowledge in KB. At completion,
extract durable knowledge, results and evidence, then retire this task file.

Completed locally: B1 tiers/shapes/history; B3 duplicates and both reader boundaries;
B2 forecasts/plans/blocked controls and constant-demand backtest growth; preliminary
B4 network/admission/body recovery; four small native V2 fault/recovery checks.
[Exact results and limitations](RESULTS.md#local-engineering-pilot) replace a progress diary.

Remaining: Linux reference host/container controls; multi-date confirmation and
HTTP sample/duration floors; other B3 defect classes, full B2 serial/30%-zero
backtest grids and B4 rates/client counts; full-scale/app recovery; independent
human accessibility/cold start. The measured SQL deadlines and consumer-size
limits remain explicit gaps. No public deployment or engine optimization occurred.

Next action: review a disposable Linux reference host/runtime and confirmation
scope/budget, then confirm the reference batch and limited evidence paths. Retain
this plan for those pending decisions/execution; broader features remain paused.

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

Artifacts proposed for the later implementation: frozen benchmark contract,
synthetic workload manifest/independent oracles, environment+schema manifest,
raw per-call/request JSONL, per-campaign resource/DB-plan logs, exact case statuses,
compact JSON summary, capacity/result report and independently verifiable hashes.
Samples include case/seed/campaign, size, cache/phase, operation, status, elapsed,
CPU/RSS, output bytes, counts, timeouts and oracle outcome. Sampling can miss RSS
peaks; include OS/cgroup high-water values and state platform units. Preserve raw
failures and censored ≥deadline timings. Never replace a timeout with the deadline
as a successful sample or compute completed-only latency without its denominator.

## Improvements allowed only after evidence

- **Batch/grain indexes or query reuse:** question: is selected-work latency
  dominated by unrelated scans or repeated reads? Claim: measured before/after
  reduction with index storage/load/write cost disclosed and exact duplicate/
  clock behavior preserved. No unique business-key constraint that hides defects.
- **Archive validation/cache reuse:** question: does repeated immutable validation
  dominate Lab CPU? Claim: a measured CPU/latency reduction only if rehashed invalid
  archive, missing-file and changed-source behavior remains fail closed. No
  process-wide “trust forever” cache or skipped validation to pass throughput.
- **Reader/producer boundary or timeout handling:** question: are evidence caps
  and cancellation honest/contained at scale? Claim: predictable rejection and
  complete history; a schema/contract change needs its own review. Never increase
  caps or invent partial evidence to call a failed scale supported.
- **Concurrency/worker changes:** question: is one worker a measured bottleneck
  after lower-cost remedies? Claim: measured throughput only with global admission,
  clock/evidence and resource semantics preserved. Multiworker per-process buckets
  change total allowance, so are not an interchangeable tuning flag.

Same frozen baseline workloads precede every targeted change; counterbalanced
before/after campaigns and a new predeclared confirmation workload follow it.
Publish regressions, extra memory/storage and cells that stop passing. If the
baseline meets the proposed practical envelope, **do not optimize it**.

## Additional readiness validation and phase gates

- **V1 / P2:** fresh Linux installation and actual container build/config/run,
  non-root/read-only/network/resource enforcement, missing/corrupt archive assets,
  clean shutdown/restart. Record exact pass/fail checks. Answers reproducible
  packaging and resource-control questions; supports only that runtime/topology.
- **V2 / P2:** interrupted calculation/persistence, client cancellation, restricted
  concurrent readers and independently timed source-owner transactions, DB/app
  crash/restart, synthetic backup restore to a second DB. Require no partial result,
  no lost committed evidence/source identity, coherent repeatable-read boundaries
  and bounded return to service. Record observed recovery time and loss per fault;
  do not advertise an RTO/RPO guarantee from a few local interruptions.
- **V3 / P2:** manual cold-start walkthrough, screen-reader speech, zoom/forced
  colors, mobile, error/retry and downloaded JSON-byte identity. Answers whether
  the portfolio demo is understandable and operable without author assistance.

P0 is this design/status review. P1 builds only the approved runner and publishes
B1/B3 plus pilot B2. P2 completes growth/load/runtime/recovery/manual evidence.
P3 targets one demonstrated bottleneck, or stops with the baseline frozen.
Unmet host/Docker/budget gates are explicit not-measured results, not permission
to resume models or closed-loop feature work. Full-grid execution is not a CI
requirement; a tiny runner correctness smoke belongs in CI after implementation.

## Frozen local workload recipes for follow-up

Original pilot source/protocol bytes are in Git `970ab16`; current executable
recipes are in `scripts/engineering_fixtures.py`. This records current reusable
measurement boundaries; historical receipts remain unchanged in EVIDENCE.

- B1 uniform receipts are +1, opening 1,000, 100 raw rows/key. Skew assigns 80k
  rows to the first 10/1,000 keys and 20k to the remaining 990; divide exactly and
  allocate remainders to ascending key indices. Ten warehouses keep K fixed,
  SKU=floor(key/10), warehouse=key modulo 10. Transfer controls replace the first
  20 rows/key with paired -3/+3 legs on adjacent warehouses: balances 1,020/1,140.
  Separate first 5 pending/next 5 future-effective/next 5 above-watermark rows
  leave 85 eligible rows/key and balance 1,085. Raw manifests keep every row.
- History appends 1 then 9 total same-size unrelated archives, repeating upstream
  natural identities with distinct row IDs. Selected semantics must remain equal.
- B3 labels first 100/1k/10k rows of 100k bad, pairs consecutive duplicate identities:
  50/500/5k exact groups, 1/10/100 blocked grains, R002 fail and R001 not_assessable.
  A separate all-key +1 snapshot probe requires exact expected/observed/delta.
  Other defect cells in the program remain pending.
- B2's 180-day pattern repeats three zero days then seven quantity-10 days:
  54 zeros/126 positive lines per key. Every twentieth one-based global positive
  line gets a same-quantity known revision; every hundredth gets a quantity-1,000
  late revision, both clocks origin +1 day. Counts use floor(total/20,/100).
  Origin is 2026-01-02 08:00 UTC; mean is exactly 7. The separate inventory ledger
  has K grains/zero movements/opening 20; reservation 3 day0, inbound 5 day1,
  L=2, R=H-2, safety2/pack6/MOQ10. H=7/28/90 needs 29/176/610, orders 30/180/612.
- Supplemental backtests are constant 4/day, histories 180/365/730 and archive
  keys 1/10, one selected key. All predictions/actuals are 4, errors zero, tie chooses
  naive. Freeze origins 28,35,... through days-56 and the days-28 holdout. These
  controls do not substitute for the 30%-zero grid or serial multi-key backtests.
- Readers have separate PostgreSQL row_to_json byte and JSON-validation accounting.
  Compact synthetic reports isolate 999/1k/1,001 findings and exact -1/0/+1 byte
  points for both layers. Padding is inert; no engine-produced evidence is truncated.
  Synthetic reader-only fixtures and actual producer reads are distinguished.
- Native HTTP uses unchanged hosted admission, one Uvicorn worker/limit16/backlog32,
  independent external schedules at 1.5/s for 20s, three hosted campaigns and one
  unwrapped local campaign, each mixed/POST/evidence. Mixed order is three POSTs,
  Lab GET, evidence GET; POSTs rotate clean/spike/delay/incomplete truth. Lag >100ms
  invalidates offered-load claims; no retries. Bursts20/40 use up to40 client threads;
  10.2s refill precedes recovery. Slow/oversized/chunked/disconnected bodies are
  separate faults. A separate offered-5/s, 20s mixed control freezes 100 arrivals
  and verifies token-exhaustion HTTP429 plus recovery. No p95/p99 confirmation
  follows from these short campaigns.
- Native V2 uses a separate two-key fault DB: block findings insertion, kill writer,
  require no partial history; repeat with an owner +1/observation-clock +1s commit,
  require old snapshot delta1 and next-time delta2. Immediate DB stop/restart and
  small custom backup/second-DB restore preserve exact committed source/results.

The local budget is two hours including fixture setup, eight observed CPU-hours,
30 GiB added disk and a conservative sampled 6 GiB RSS guard; native shared-memory
sums are not true combined memory or OS enforcement. Fresh worker calls have a
60s supervisor and 55s SQL/5s lock limit. Report missing receipts after complete
commits as unverified, not partial/zero/success. Calls include production commit;
fixture loads, hashes, oracle checks, file writes and EXPLAIN are outside timing.
Three exploratory process-restarted batch calls are first/repeat access, not
confirmed warm or DB/OS-cold. Serial driver timing includes supervision and
verification; blocked calls never count as completed eligible plans. The reference
confirmation protocol above remains unchanged.
