# Research delivery status and continuation

Snapshot: 2026-10-03. This consolidates the user's 22 directions and supersedes
the older roadmap checkpoint for delivery status. The original
[full rationale and execution rules](https://github.com/daniel-li2021/inventory-intelligence/blob/d2cb98ba1016f80bd2c2dd40159092f4f1b21395/docs/RESEARCH_ROADMAP.md)
remain preserved. Finish reviewable packages, retain negative outcomes and
consumed evidence, then move to the next independent task when a gate blocks one.

## Combined candidate versus integrated main

Main remains `f6d3d16034af038eda4c8687ea4f1ed6d2445ef6`. The operational core,
historical research and synthetic local Lab are merged. PR 14–23 are retained
by ancestry in the `codex/research-integration` candidate; this is **not main
integration**, remote CI or public hosting. All original saved reports/receipts
retain their published bytes. The original
[portfolio claim receipt](review/portfolio-claims.json) remains a historical
snapshot; use the [combined acceptance](RESEARCH_INTEGRATION.md) for current status.

| PR | Package | Exact retained head |
|---|---|---|
| 14 | Fresh paid warmup / retention / supply interventions | `d2cb98ba1016f80bd2c2dd40159092f4f1b21395` |
| 15 | Attested public adapter / observed-sales forecast | `97d1f8a00a00cecdcd01368403bdfeab8b92d510` |
| 16 | Fixed-forecast policy comparison | `39bf64d7e70b9221afbe1d697fe49fd348fcdc04` |
| 17 | Exploratory public safety/service | `706fa82c7520f5119ffd85b8c6a2a65f40fc2f10` |
| 18 | Lab keyboard/mobile accessibility | `3d66b4309cc465d39ed830b4db59ef0860807c25` |
| 19 | Case study / all-direction status | `758d5d317ff8470841cc376bba49b86909ebb69c` |
| 20 | Prospective disjoint-item calibration | `e7473a595d4ef6deca33c283ea6b27e23ad83bc4` |
| 21 | Separate lost-sales protocol / paired study | `d06badeb2a61b2f76da5ebb4afbd9ff6ffc38023` |
| 22 | Physical-count / adjustment evidence | `c916c046b3af06503574aaea208a0197e0615a3e` |
| 23 | Bounded hosted serving / deployment readiness | `c337a5616dda27398b0f82e9b9e011aba9fe9c6f` |

The candidate resolves shared documentation and preserves source semantics.
Historical code drift is declared rather than rehashed away. The automatic
approval review previously rejected the attempted PR 14 main merge, requiring
explicit owner approval for default-branch mutation and downstream workflows.
That gate remains pending; do not infer approval from automatic continuations.
After approval, integrate the reviewable candidate, verify remote main ancestry,
then retire only proven-merged clean branches. No published history is rewritten.

## All 22 directions

“Measured” below refers to retained package evidence, not production performance.
No direction is dropped merely because it is gated.

| # | Direction | Current evidence/state | Next step or gate |
|---:|---|---|---|
| 1 | Fresh demand/supply and paid warmup | #14 measured: 360 pairs, 18 distinct demand paths, paid carryover/settlement. | Use new traces for any revised policy; old paths are consumed. |
| 2 | Service feasibility attribution | Main startup bound; #14 signed stock/lead/delay/review/pack interventions. | Keep interactions/residuals explicit; no additive causal partition without identification. |
| 3 | Safety calibration versus achieved service | #14/#17 plus #20 prospectively frozen disjoint 32-item/768-arm replication. Mean/SBA q95 fill 92.12%/93.35% at L2/no extra delay. | Same retailer/calendar; future policy revisions need fresh frozen evidence. No service guarantee. |
| 4 | Safety retention under decline | #14 pause/seasonal/decline/cessation study; recent and decay gates both 0/21. | Test a justified revision on fresh paths with recovery service and owned stock. |
| 5 | Lead-time/supplier reliability | #14 leads 2/5/10, equal-mean variable delay, matched forecast controls. | Extend only to a specific unmet supply question; actual supplier data remains unavailable. |
| 6 | Probabilistic forecasting | #17 completed residual quantiles, target coverage and exact pinball measured. | Disjoint-item replication completed in #20; no nominal-to-service guarantee. |
| 7 | Small decision-policy comparison | #16 order-up-to, periodic `(s,S)`, prefix arithmetic; negative trigger result retained. | Fresh costed warm states and hidden-delay-compatible inputs before broader conclusions. |
| 8 | Public-data adapter/provenance | #15 official UCI extraction, hashes, identity/exclusion/schema/subset receipts. | Preserve immutable caches and attribution; operational imports remain excluded. |
| 9 | Public observed-sales realism | #15 seven methods on frozen train-only subset; #17 proxy inventory outcomes. | Disjoint block completed in #20 (overlap zero); one-retailer/calendar limitation remains. |
| 10 | Advanced-model gate | No independent promotion evidence; fixed mean beats frozen mix in H28 aggregate. | Repeated sealed baseline weakness before ADIDA/IMAPA; feature/dependency protocol before global model. |
| 11 | Stronger source provenance | Combined 24-artifact / 119-node manifest binds 17 source maps to complete historical snapshots and five parent/freeze links; #22 retains its internal DAG. | Declared external fingerprints and source assertions are not signed authenticity. Global semantic coverage remains bounded by individual validators. |
| 12 | Property/mutation QA | Package conservation/clock/FIFO oracles; #17 six rehashed mutations detected. | Combined source/parent/drift/candidate/graph controls added; continue only for a demonstrated invariant gap. |
| 13 | Backlog versus lost sales | #21 separate contract and 288 fresh matched pairs; 480 saved-arm audits, paid warmup and common closure. | Unit-day backlog versus once-per-unit lost penalties are distinct economics; accepted orders keep backlog semantics. |
| 14 | Operational planner closed loop | #16 runs projection arithmetic only; complete operational source gates not executed. | Define advisory-action/receipt identity and repeated knowledge clocks; synthetic execution adapter protocol first. |
| 15 | Physical inventory truth | #22 additive count/recount/variance/review contract; 40 controls; stock 100/count 96 yields advisory −4. | Source-declared freeze/blind/observer IDs are not real authenticated warehouse truth; zero inventory writes. |
| 16 | Performance/scale | Optional; no demonstrated current latency failure or published scale result. | Workload/environment budget before 10k SKU or 100k/1M movements. |
| 17 | Multi-location allocation | Deferred evidence/scope gate; existing grain is SKU/warehouse. | Demonstrate a single-location decision improved by transfers, then specify transit/cost constraints. |
| 18 | Supplier capacity/calendar | MOQ/pack exists; capacity/blackouts/calendar extension not implemented. | Document a binding use case and timing contract before adding constraints. |
| 19 | Guided demo | Existing clean/reset plus demand/delay/incomplete presets suffice; #18 keyboard paths checked. | Reuse the three-minute case-study walkthrough; no extra preset framework. |
| 20 | Accessibility/UX | #18 targeted keyboard/contrast/320px/failure/retry acceptance. | Screen-reader speech, browser zoom/forced colors and downloaded bytes remain explicitly unverified. |
| 21 | Hosted read-only Lab | #23 plan, bounded anonymous wrapper, pinned templates and 13 private-CA HTTPS checks; combined candidate contains #18. | Docker/container/Linux limits and public host/domain/cost/TLS/uptime remain unverified; no paid resource created. |
| 22 | Resume/case study | [Case study and scoped resume wording](PORTFOLIO_CASE_STUDY.md) prepared in this package. | Refresh claims only from independently verified artifacts and merged/deployed status. |

## Long-term sequence

1. **Integration and provenance:** the combined candidate and saved-source audits
   now make approval concrete. Preserve all original artifacts; approve/integrate
   the candidate before claiming main delivery. Keep local versus CI evidence
   explicit and do not sum overlapping package test counts.
2. **Closed-loop planning boundary:** next independent design work should define
   synthetic advisory-action/receipt identities and repeated as-known clocks,
   then run the actual planner with its reliability/supply gates. The prefix
   arithmetic comparison alone does not execute an operational planning workflow.
3. **Access:** use the concrete hosted readiness package after a host/domain/cost
   is reviewed and Docker is available. Confirm combined accessibility/CSP on the
   final packaged app, Linux enforcement/restart, public trusted TLS and actual
   uptime before claiming a deployed service. Keep the local demo available.
4. **Decision research:** all published demand/public-sales paths are consumed.
   Any safety-retention or calibration revision needs newly frozen evidence and
   paid owned-state/recovery-service gates. Retain the negative findings and
   do not call repeated scenarios or a second item block independent markets.
5. **Conditional extensions:** larger allocation/capacity/scale/model work stays
   recorded. Specify a binding use case and workload/contract before adding it.
   Advanced models still lack independent promotion evidence. A negative gate
   decision is a completed bounded research outcome, not a reason to delete
   the direction or claim a production result.

If integration or hosting is blocked, continue the next independent design or
evidence gap. Do not silently redefine the long-term objective around the work
already completed. Protocol/source authenticity, current physical stock and
production economics remain outside the measured synthetic/sales-proxy evidence.
