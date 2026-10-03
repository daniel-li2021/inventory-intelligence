# Research delivery status and continuation

Snapshot: 2026-10-03. This consolidates the user's 22 directions and supersedes
the older roadmap checkpoint for delivery status. The original
[full rationale and execution rules](https://github.com/daniel-li2021/inventory-intelligence/blob/d2cb98ba1016f80bd2c2dd40159092f4f1b21395/docs/RESEARCH_ROADMAP.md)
remain preserved. Finish reviewable packages, retain negative outcomes and
consumed evidence, then move to the next independent task when a gate blocks one.

## Delivered versus integrated

Main was verified at `f6d3d16034af038eda4c8687ea4f1ed6d2445ef6`.
The operational core, historical research and local synthetic Lab are merged.
The following PR states and exact heads were read from GitHub on this date;
all five are **open and unmerged**. Local validation is not merged acceptance,
remote CI or hosted deployment. [Pinned evidence/claim receipt](review/portfolio-claims.json).

| Package | PR | Verified head | Dependency |
|---|---|---|---|
| Fresh warmup, retention, supply interventions, original roadmap | [#14](https://github.com/daniel-li2021/inventory-intelligence/pull/14) | `d2cb98ba1016f80bd2c2dd40159092f4f1b21395` | main |
| Public adapter and observed-sales forecast benchmark | [#15](https://github.com/daniel-li2021/inventory-intelligence/pull/15) | `97d1f8a00a00cecdcd01368403bdfeab8b92d510` | main; optional research dependency/license review |
| Fixed-forecast ordering-policy comparison | [#16](https://github.com/daniel-li2021/inventory-intelligence/pull/16) | `39bf64d7e70b9221afbe1d697fe49fd348fcdc04` | main; private simulator hook |
| Public sales-proxy safety/service | [#17](https://github.com/daniel-li2021/inventory-intelligence/pull/17) | `706fa82c7520f5119ffd85b8c6a2a65f40fc2f10` | stacked on #15's branch |
| Local Lab keyboard/mobile accessibility | [#18](https://github.com/daniel-li2021/inventory-intelligence/pull/18) | `3d66b4309cc465d39ed830b4db59ef0860807c25` | main |

Integration is blocked by the automatic approval review's rejection of the
attempted #14 main merge: it required explicit owner approval for the shared
default-branch mutation and possible downstream workflows. That approval remains
pending. Continue independent research/docs; do not infer approval from automatic
goal continuations. Once approved, resolve shared README/protocol edits, integrate
#15 before #17, validate affected combined boundaries, verify remote main, then
retire only merged clean branches. Do not combine package test counts as unique tests.

## All 22 directions

“Measured” below refers to retained package evidence, not production performance.
No direction is dropped merely because it is gated.

| # | Direction | Current evidence/state | Next step or gate |
|---:|---|---|---|
| 1 | Fresh demand/supply and paid warmup | #14 measured: 360 pairs, 18 distinct demand paths, paid carryover/settlement. | Use new traces for any revised policy; old paths are consumed. |
| 2 | Service feasibility attribution | Main startup bound; #14 signed stock/lead/delay/review/pack interventions. | Keep interactions/residuals explicit; no additive causal partition without identification. |
| 3 | Safety calibration versus achieved service | #14 synthetic and #17 exploratory public-proxy fill/cycle/coverage/pinball. | Freeze independent labels and quantile calibration comparison before scoring. |
| 4 | Safety retention under decline | #14 pause/seasonal/decline/cessation study; recent and decay gates both 0/21. | Test a justified revision on fresh paths with recovery service and owned stock. |
| 5 | Lead-time/supplier reliability | #14 leads 2/5/10, equal-mean variable delay, matched forecast controls. | Extend only to a specific unmet supply question; actual supplier data remains unavailable. |
| 6 | Probabilistic forecasting | #17 completed residual quantiles, target coverage and exact pinball measured. | Independent calibration generalization; no nominal-to-service guarantee. |
| 7 | Small decision-policy comparison | #16 order-up-to, periodic `(s,S)`, prefix arithmetic; negative trigger result retained. | Fresh costed warm states and hidden-delay-compatible inputs before broader conclusions. |
| 8 | Public-data adapter/provenance | #15 official UCI extraction, hashes, identity/exclusion/schema/subset receipts. | Preserve immutable caches and attribution; operational imports remain excluded. |
| 9 | Public observed-sales realism | #15 seven methods on frozen train-only subset; #17 proxy inventory outcomes. | Independent train-selected item block excluding consumed items; one-retailer limitation remains. |
| 10 | Advanced-model gate | No independent promotion evidence; fixed mean beats frozen mix in H28 aggregate. | Repeated sealed baseline weakness before ADIDA/IMAPA; feature/dependency protocol before global model. |
| 11 | Stronger source provenance | Run history and package source/input/artifact hashes implemented. | Dependency/lineage manifest gap audit; distinguish reproducibility from signed attestation. |
| 12 | Property/mutation QA | Package conservation/clock/FIFO oracles; #17 six rehashed mutations detected. | Target unresolved cross-layer JSON/export/source dependency gaps; no count-driven suite expansion. |
| 13 | Backlog versus lost sales | Separate protocol required; current accepted orders preserve backlog. | Freeze research-only event timing, lost-sales denominator, inventory rule and penalty; independent oracle before fresh comparison. |
| 14 | Operational planner closed loop | #16 runs projection arithmetic only; complete operational source gates not executed. | Define advisory-action/receipt identity and repeated knowledge clocks; synthetic execution adapter protocol first. |
| 15 | Physical inventory truth | Ledger consistency is implemented; physical counts are not. | Additive synthetic count/recount/variance/confidence contract; no silent source adjustment. |
| 16 | Performance/scale | Optional; no demonstrated current latency failure or published scale result. | Workload/environment budget before 10k SKU or 100k/1M movements. |
| 17 | Multi-location allocation | Deferred evidence/scope gate; existing grain is SKU/warehouse. | Demonstrate a single-location decision improved by transfers, then specify transit/cost constraints. |
| 18 | Supplier capacity/calendar | MOQ/pack exists; capacity/blackouts/calendar extension not implemented. | Document a binding use case and timing contract before adding constraints. |
| 19 | Guided demo | Existing clean/reset plus demand/delay/incomplete presets suffice; #18 keyboard paths checked. | Reuse the three-minute case-study walkthrough; no extra preset framework. |
| 20 | Accessibility/UX | #18 targeted keyboard/contrast/320px/failure/retry acceptance. | Screen-reader speech, browser zoom/forced colors and downloaded bytes remain explicitly unverified. |
| 21 | Hosted read-only Lab | Local demo works; no hosted resource or deployment target configured. | Concrete HTTPS/restart/resource/abuse/cost/ownership proposal, then target authorization; continue local accessibility/docs meanwhile. |
| 22 | Resume/case study | [Case study and scoped resume wording](PORTFOLIO_CASE_STUDY.md) prepared in this package. | Refresh claims only from independently verified artifacts and merged/deployed status. |

## Long-term sequence

1. **Next evaluation package:** freeze a disjoint training-selected public item
   block and a bounded calibration study, excluding the consumed 32-item subset.
   Reuse the attested source archive. Inspect selection inputs only until the
   manifest/protocol is committed; score once, preserve every null/failure and
   never call the old window an untouched holdout. New items test cross-item
   generalization, not a later calendar or a second retailer. If source/cache
   provenance is unavailable, switch to the separate semantics package below.
2. **Next semantics package:** specify and implement research-only lost sales
   with explicit demand event timing, immediate fill, permanent lost units,
   inventory conservation, penalty accounting and settlement. Compare under
   matched fresh traces without changing accepted-order backlog semantics.
   If the economic/contract boundary cannot be made defensible, proceed to the
   physical-count/provenance design instead.
3. **Evidence/domain package:** make the missing provenance links and physical-
   count confidence/recount boundary concrete. Add only the narrow independently
   testable gap; proposed adjustments never silently mutate inventory sources.
4. **Access and integration:** prepare a minimal hosting proposal while owner
   approval is pending. After a target and budget are set, validate read-only
   synthetic public deployment; until then use the functioning local demo.
   Integrate approved branches with focused combined acceptance and direct remote
   verification. No continuous CI polling by default.
5. **Conditional expansion:** reconsider advanced models, large scale, multi-
   location and supplier capacity only when the preceding measured results show
   the specific need. A negative gate decision is a completed research outcome.

Each continuation should name the next ready package, its frozen evidence
boundary and its acceptance criterion. Do not silently turn blocked integration,
missing deployment ownership or optional large scope into a reason to stop all
authorized independent work.
