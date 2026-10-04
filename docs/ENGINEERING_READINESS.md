# Engineering readiness investigation — 2026-10-03

> Historical assessment for the recorded source/environment. Use [STATE](STATE.md)
> for current phase, scope, integration mode and acceptance references.

Reviewed integrated main **9d7c55f8e30c9b885e14c450632de18efe413693**, after
PR 14–24 integration and PR 25's CI-history correction. This is an evidence
review and proposed execution plan. **No new feature, performance experiment,
model fit, data acquisition, cloud service or deployment was implemented.**
Feature development, including the unpublished planner-loop branch, is paused.
The branch's protocol commits and unfinished files are preserved and excluded
from this assessment; they are not merged implementation or readiness evidence.

## Readiness claim that is supported now

The project supports a **bounded synthetic technical portfolio demonstration**:
exact reconciliation, evidence-gated advisory planning, persisted read-only
explanations, independent correctness controls and a locally exercised Lab.
It has substantially stronger research/reproducibility evidence after PR 14–24.
It does **not** yet support a measured operating-capacity envelope, production
readiness, deployed-demo reliability or real-business benefit.

### Current green baseline

- [Main CI run](https://github.com/daniel-li2021/inventory-intelligence/actions/runs/37164884160):
  PostgreSQL acceptance and repository hygiene both completed successfully.
  Its [acceptance log](https://github.com/daniel-li2021/inventory-intelligence/actions/runs/37164884160/job/111325671795)
  records **240 tests / OK / 19.495 seconds**, Python 3.12.12, PostgreSQL 17.9,
  Psycopg 3.3.6, Ubuntu runner and full Git history. Test duration is not service
  latency or throughput. One green run establishes this commit's acceptance,
  not CI reliability across repeated runs or performance across machines.
- PR 24 preserves the ten original research delivery heads and their published
  artifact bytes. PR 25 corrects shallow checkout; it does not weaken lineage
  tests. The older PR 16 original-kernel hash assertion is already corrected.
  Documentation conflicts were resolved before integration; no unresolved merge
  conflict is present in this baseline.
- [Local combined acceptance](review/research-integration-acceptance.json) is a
  separate 240-test PostgreSQL 17.6 / Python 3.12.14 receipt. Its pre-merge
  main_changed=false and remote_ci_verified=false remain historically correct;
  they must not be overwritten to imply a CI run existed at capture time.
- [Inspection receipt](review/engineering-readiness-baseline.json) binds the
  reviewed source snapshot, selected saved artifacts and remote observations.

## What is measured, and what the measurements cannot establish

1. **Correctness and fail-closed behavior:** actual PostgreSQL oracles cover
   reconciliation quantities, clocks, duplicate identities, source coverage,
   transaction rollback and runtime role restrictions. Demand/planning tests
   exercise revision visibility, forecast eligibility, exact orders and persisted
   contradictions. Lab tests challenge coherently rehashed corrupt evidence.
   These validate scoped semantics; they do not measure resource exhaustion,
   concurrent writers, crash recovery or growing retained history.
2. **Decision/research outcomes:** fresh paid warmup, retention, lead/supply,
   fixed-forecast policy, public-sales calibration and lost-sales studies retain
   independent controls, explicit costs, null denominators and negative results.
   Thousands of decision arms are not thousands of engineering load requests.
   UCI's 541,909 extracted rows establish an observed-sales adapter/evaluation
   boundary, not ingestion throughput, operational availability or demand truth.
3. **Repository reproducibility:** the combined manifest retains 24 artifacts,
   119 dependency nodes, 17 complete historical source maps, five parent/freeze
   bindings and 13 disclosed historical/current file differences. Saved semantic
   audits cover 768 parent safety arms, 768 new-item arms and 480 unique lost-sales
   arms. Counts establish bounded coverage, not signed authenticity or a universal
   semantic verifier. No need to regenerate these consumed studies.
4. **Packaging and UI:** an installed combined wheel outside the checkout passed
   13 localhost private-CA HTTPS checks and a real-browser hosted-CSP/keyboard/
   320px smoke. Baseline 12/cost327 and spike18/cost351 remain exact. This does not
   prove a clean Linux/Docker cold start, container resource enforcement, complete
   accessibility, public DNS/ACME, restart, uptime or sustained HTTP capacity.
5. **Historical engineering microtimings exist:** final-round1/final-round2 each
   record three samples per operation on small fixed synthetic fixtures. Median
   Stage 1 clean is **4.137 / 4.824 ms**, complete planning **26.083 / 26.657 ms**,
   constant-series 180-day backtest **195.471 / 202.819 ms**, respectively.
   They include live DB/read/check/persist paths. They are historical, serial,
   same-environment observations without a declared scale ladder, cache protocol,
   resource envelope or independently restarted campaigns. Do not pool six samples
   as six independent environments or extrapolate them to 1M movements.
6. **Copilot latency is a separate historical observation:** the saved routing
   study has 22 live API calls, API median **1346.543 ms**, nearest-rank p95
   **2619.317 ms**. Its 45-case end-to-end distribution mixes routed/offline/reused
   paths. It supports bounded historical call accounting; it does not establish
   deterministic-backend capacity, current provider latency or a service SLO.

Sources: [round1](review/final-round1.json), [round2](review/final-round2.json),
[measurement boundary](../scripts/review_benchmark.py),
[Copilot receipt](review/copilot-benchmark.json),
[combined acceptance](RESEARCH_INTEGRATION.md). This review reuses saved evidence;
it performs no new timings. **There is no published controlled engineering
performance/scale benchmark of the integrated system.**

## 1. Strong enough to freeze

- **Core contracts and permissions:** integer-piece arithmetic, separate business/
  knowledge clocks, explicit completeness, append-only result history, natural
  identity and the restricted runner. Freeze the current accepted-order and
  advisory boundaries. Claim: independently tested evidence-safe computation.
- **Existing simple methods and bounded policy boundaries:** retain deterministic
  baselines, prefix planning versus periodic simulation, distinct lost-sales and
  physical-count protocols. Freeze method grids and consumed research artifacts.
  Claim: disciplined evaluation with negative results, not model superiority.
- **Read-only explanations and provenance:** preserve explicit UUID citations,
  bounded report readers, original-source hashes and immutable saved reports.
  Claim: reproducible, auditable synthetic decisions; not source authenticity.
- **Lab's current scope and controls:** clean/delay/spike/incomplete presets already
  support the story. Freeze this demo's evidence and behavior while measuring it.
  Claim: locally demonstrated assumptions and failure states.

Freezing behavior is not forbidding a measured implementation optimization.
Any change must preserve exact outcomes, clocks, duplicate handling and history.

## 2. Validation needed before stronger engineering readiness claims

Priorities reference the proposed [benchmark program](PLAN.md).

- **B1/B2 — scale and retained-history behavior:** how do real reconciliation and
  gated planning paths behave as selected rows, keys and unrelated archived batches
  grow? Supports a precise batch/interactive capacity envelope on one pinned host.
- **B3 — high-finding/report capacity:** can defect-heavy evidence be computed,
  persisted and read within declared consumer limits, with honest rejection above
  them? Supports fail-closed behavior at a measured size; not unlimited evidence.
- **B4 — real HTTP load/admission:** what work is actually completed below the
  hosted allowance, and how do 429/503/timeout/recovery behave under overload?
  Supports measured demo capacity and bounded rejection, not configured RPS as
  throughput or internet DoS protection.
- **V1 — fresh packaging/runtime:** does a clean Linux environment and actual
  Compose runtime install/start, enforce non-root/read-only/resource controls and
  serve the exact wheel/assets? Supports reproducible deployment readiness.
  It still does not establish public TLS or uptime.
- **V2 — transaction failure, restart and restore:** do cancellations/process or
  DB termination leave complete committed evidence or no partial run, and can a
  synthetic backup be restored coherently? Supports tested failure recovery on
  the declared fixture/runtime, not an unmeasured commercial RTO/RPO.
- **V3 — accessibility and cold-start usability:** can a human complete the clean,
  blocked and delayed narrative with keyboard/screen-reader speech, 200% zoom,
  forced colors, mobile error/retry and verified downloaded evidence bytes?
  Supports bounded accessible portfolio usability; not full WCAG certification.

## 3. Incomplete or weak evidence today

- No scale ladder, raw engineering samples, per-operation CPU/RSS/DB buffers,
  payload/storage growth, queue behavior or published maximum sustainable load.
- No declared engineering SLO or target hardware. Existing 4-active/2-per-second
  hosted admission and Docker limits are configuration, not measured capacity.
- Schema inspection finds primary-key indexes but no dedicated batch/grain
  filtering indexes. Demand reads visible order identities across a whole batch;
  backtest folds repeat this and retain nested evidence. These are **hypotheses**
  for B1/B2, not measured bottlenecks or authorization to weaken identity checks.
  Actual run_plan also rechecks the inventory source batch for each selected key;
  B2 measures this repeated gate instead of bypassing it.
- Report producers and consumers have different envelopes: reliability explainer
  readers cap 1,000 findings/2 MiB; planning reader caps 16 MiB. Large SQL JSON
  reports or archived per-origin evidence may hit reader limits before quantity
  arithmetic fails. There is no measured capacity or truncation policy.
- Existing acceptance proves deliberate DB errors roll back; it does not prove
  cancellation, multi-process contention, crash/restart, backup/restore or retention
  storage budgets. No statement/lock timeout policy is set in runtime code.
- Docker build/Compose/Linux enforcement remains unverified, although hosted
  wrapper tests and native localhost proxy behavior have been exercised.
- Real availability, supplier truth, physical counts, commercial economics and
  external business-semantic review remain outside synthetic/public-sales evidence.
- Closed-loop planner execution is not on main. Unpublished feature work is paused
  and has no accepted result; its draft files are not part of this green baseline.
- Repository branch/ruleset enforcement has not been independently verified in
  this investigation. Successful merges and CI do not prove mandatory protection.

## 4. Valuable, but can wait

- **Closed-loop research:** later answers how actual evidence gates affect repeat
  execution. Supports a synthetic execution claim only after its own controls pass.
  Keep paused until the engineering envelope is understood.
- **Hosted public demo:** answers whether a recruiter can inspect the demo
  without setup. Supports public demo accessibility only after V1/V2/B4 and a
  host/domain/budget decision; public TLS/uptime need a separate release check.
- **Fresh safety/retention/calibration studies:** answer whether a justified
  policy revision resolves a specific service/owned-stock weakness on new frozen
  paths. Support that bounded decision-quality result, not engineering readiness.
  Existing negative outcomes stay published; more arms do not close capacity gaps.
- **Public-adapter throughput:** later measure parsing/transform/cache reuse only
  if batch acquisition time or archive memory matters to the target use. It can
  support ETL throughput, never uncensored-demand or inventory-service claims.
- **Larger fault/security audits or semantic lineage coverage:** add cases where
  an identified boundary lacks an oracle. Support that exact boundary, not a
  growing test-count headline or generic production certification.

## 5. Explicitly do not build now

- More forecast models/global ML, network allocation, supplier calendars/capacity
  or new inventory domains without independent evidence that existing decisions
  need them. They support new product claims, not current engineering capacity.
- Redis, queues, parallel workers, sharding, Kubernetes, microservices, ORM or a
  scheduler merely to claim scale. Measure the current native stack first.
- Speculative caches/indexes/bulk-query refactors. Only optimize a measured
  bottleneck; nonunique indexes must preserve bad-record admission and identity
  semantics. Do not filter away cross-key identity contradictions to get faster.
- A new load-test platform or observability service before the small benchmark
  runner's requirements exceed standard tools. No paid host is needed for design.
- Raising evidence caps, dropping findings, sampling bad data or excluding
  timeouts to improve a chart. Consumer rejection and capacity limits are results.
- Re-running consumed decision studies to turn negative results positive or
  presenting test-suite runtime, configured rate limits or row counts as throughput.

## Recommended phased decision

**P0 now:** freeze green main, preserve paused feature work, correct stale status,
and review the proposed workload/SLO/environment/budget. This document completes
the investigation; it does not authorize automatic benchmark implementation.

**P1 after program approval:** implement only the fixture/oracle/measurement
runner, then B1/B3 and the selected B2 small-to-medium cells. Publish raw samples,
query diagnostics and even failed/unfinished upper scales. The gate is reproducible
correctness plus an honestly stated envelope, not “1M must pass.”

**P2 after P1 evidence:** complete B2 growth and B4 network campaigns, plus V1/V2
runtime/failure checks and V3 manual demo review. If Docker or a reference host is
unavailable, record exactly which checks remain unmeasured and proceed with local
DB investigation rather than pretend to validate hosted controls.

**P3 only if a gap is measured:** one minimal targeted improvement (batch index,
query reuse, report boundary, timeout/recovery behavior or inaccessible interaction),
same-fixture before/after campaigns, and a separately frozen confirmation workload.
Supports a quantified improvement with resource/correctness tradeoffs. If the
baseline meets the envelope, freeze it and stop optimizing.

No engineering phase is a backdoor to resume feature development. Revisit the
feature roadmap only after reporting capacity, remaining gaps and the next explicit
decision. All 22 earlier directions remain recorded, with this investigation
superseding their previous execution priority.
