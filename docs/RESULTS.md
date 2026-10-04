# Core and interface results

Measured outcomes consolidated from completed reviews. Original reports remain
immutable; [EVIDENCE](EVIDENCE.md) binds commits/environments. These are bounded
synthetic/local studies, not commercial savings, production readiness or fresh
results from documentation cleanup. Research studies have separate indexed
[research results below](#research-results).

## Forecast selection and advisory planning

Seven synthetic groups, 180 days, three stdlib methods, 7/14/28-day horizons and
14 shared selection origins per eligible group: 98/196/392 selection points and
separate holdouts of 7/14/28 points within the final 28-day block. The blocked group
has 0 included / 14 excluded selection origins and null scores. Selection uses
28-day MAE and frozen origin/tie rules. Below is 28-day holdout MAE in pieces;
decimal displays are rounded to three places.

| Group | Selected | Holdout MAE: naive / mean / seasonal-naive |
|---|---|---|
| Constant | naive | 0 / 0 / 0 |
| Weekly | seasonal-naive | 1.857 / 1.719 / 0 |
| Intermittent | seasonal-naive | 1 / 1.691 / 0 |
| Zero | naive | 0 / 0 / 0; WAPE undefined |
| Blocked | none | null / null / null |
| Drifting | naive | 19/14 / 3417/532 / 19/14 |
| Irregular | mean | 3 / 827/266 / 9/2 |

The selected irregular mean loses to naive on this holdout; do not retune on it.
Exact forecasts/scores/repeats: [baseline](review/baseline.json),
[round 1](review/final-round1.json), [round 2](review/final-round2.json),
[validation](review/validation.json). Semantic repeats exclude fresh run IDs and
creation timestamps. Source hashes stayed unchanged; Stage 3 appended no history,
whereas Stage 1/2 intentionally appended saved runs.

## Decision metric counterexamples

Derived from saved irregular 28-day bias using exact `Fraction` arithmetic:
absolute cumulative error `abs(bias * 28)` is naive 36, mean 278/19, seasonal-naive
16. Mean improves horizon-total accuracy while naive wins daily MAE. This is a
derivation from [round 2](review/final-round2.json), not measured inventory cost.

Independent one-period oracle: equally weighted demand `[0, 0, 0, 10]`, stock equal
to forecast, holding penalty 1/leftover piece and lost-sales penalty 10/unmet piece.
Stock 0 gives MAE 5/2 and mean cost 25; stock 3 gives MAE 4 and cost 79/4;
stock 10 gives MAE 15/2 and cost 15/2. The MAE winner is the cost loser under these
declared synthetic penalties. Neither establishes real financial benefit.

## Historical timings

Each column is a median of three local calls, in milliseconds. Two final rounds
give six samples per case; the separate baseline supplies three more. Small
uncontrolled samples do not establish load capacity or reliable tail latency.
Setup, fixture generation and source hashing are excluded; actual DB/read/check/
persist work is included. The rounds share one environment, not six independent hosts.

| Case | Final round 1 / round 2 (ms) |
|---|---:|
| Clean reconciliation | 4.137 / 4.824 |
| Complete plan | 26.083 / 26.657 |
| Constant 180-day backtest | 195.471 / 202.819 |
| Weekly benchmark | 217.040 / 201.640 |
| Irregular benchmark | 131.900 / 134.890 |
| Clean Stage 3 explanation | 0.360 / 0.400 |
| Persisted benchmark explanation | 118.770 / 111.340 |
| Persisted proposal explanation | 18.270 / 18.060 |

The persisted benchmark validates roughly 4 MiB of evidence; additive reader bound
16 MiB, without truncation. Original reliability reader limits remain intact.
Historical timing reproduction on an already-populated synthetic demo:
`PYTHONPATH=src python -m scripts.review_benchmark --repeats 3 --output /tmp/review.json`.
Do not reload fixtures or call this a controlled scale campaign.

## Lab arithmetic and service

Independent planner oracle: on-hand 10, prior reservations 3, confirmed inbound 5
on day 1, demand 4/day, lead 2, review 3, safety 2, pack 6, MOQ 10. Without the
proposal the position is `[3, 4, 0, -4, -8]`; raw deficit 10 rounds to 12, giving
`[3, 4, 12, 8, 4]`. Incomplete supply yields null proposals.

Separate periodic baseline: 112 new-demand pieces and 3 prior-reserved pieces
fulfilled, ten orders of 12. Holding 219 + setup 20 = scored cost 239; runoff 88
gives total 327. Average stock 219/28, terminal stock 20; all nine completed cycles
are shortage-free. [API and operating semantics](DECISION_LAB.md).

| Scenario | Planner proposal | Periodic outcome |
|---|---:|---|
| Baseline | 12 | Total cost 327; 28 scored + 5 runoff days |
| Demand 125% | 18 | Total cost 351 |
| Demand 150% | 24 | Demand 6/day |
| Demand 50% | 0 | Demand 2/day |
| Demand 101% | 18 | Upward-rounded demand 5/day |
| Hidden delay 3 | 12, first review unchanged | 17 shortage days, 100 backlog piece-days, immediate fill 11/28; scored cost 1,027 + runoff 144 = 1,171; 28 + 8 days |
| Zero demand | Case-specific | WAPE, fill and service-target denominators stay null |
| Incomplete supply / contradictory archive | null | Scenario quantities and outcome metrics suppressed |

Delay/baseline totals have unequal runoff exposures. Conservation controls cover
extreme valid scenarios and holding/backlog/setup rates 1/10/2. Invalid booleans,
floats, strings, nulls, unknown fields and out-of-bound knobs return 422; archive
contradictions return 503. Tests inject copies, preserving originals. Source demand
stays 4/day regardless of scenario scaling.

## Browser and accessibility results

[Receipt](review/lab-accessibility-browser.json): 1280×900 and 320×740 keyboard
paths cover presets/Run, spike/delay, invalid inputs, disclosures, evidence-table
arrow scrolling and skip-to-main. Prefix ArrowRight scrolls 80 px; blocked document
width improved from 339 to 320 px. Ten inputs have short distinct names and hints.
Completion restores Run focus only when focus fell to the body; another selected
element retains focus. Failure exposes a focusable alert/retry and retains the
last successful result when available.

Measured contrast: helper text on paper 5.44:1, green surface 5.24:1, blocked state
5.58:1, input boundary 3.46:1. Baseline stock/backlog improved from 2.83/2.20 to
4.82/4.42, with dotted/short-dash/solid distinctions and inset disclosure focus.
[Desktop](review/lab-accessibility-desktop.jpg),
[mobile](review/lab-accessibility-mobile.jpg), [blocked](review/lab-accessibility-blocked.jpg).

Original installed-wheel acceptance parsed downloaded comparison JSON and checked
baseline/null blocked outputs. The later accessibility download capture timed out;
it did not reconfirm export bytes. Its owned-server stop/restart checked error focus
and retry. Combined integration separately checked CSP, Enter-to-run, spike focus,
four SVG charts and 320px blocked reflow ([receipt](review/research-integration-browser.json)).
Cached assets once masked fixes: verify served bytes at a fresh origin. Actual
VoiceOver/NVDA, zoom, forced colors, other engines and full WCAG remain unmeasured.

## Copilot routing and fidelity

Original 2026-10-02 run: 45 cases, including five post-hoc explicit-selector controls
added using saved 40-case measurements, without new model calls. Groups: 5 reliability,
11 finding, 4 baseline, 7 readiness, 6 unsupported, 6 persisted planning, 6 invalid.
Exactly 22 sequential Luna calls; no fallback/escalation.

| Dimension | Original evaluation | Fresh frozen stabilization set |
|---|---:|---:|
| All expected outcomes | 40/45 | 32/32 |
| Natural-language routing | 23/28 (includes 6 local phrases) | 32/32 |
| Live model intent | 17/22 | 32/32 |
| End-to-end evidence / numeric / citations | 34/39 each | 32/32 each |
| Conditional on correct routing | 34/34 each | 32/32 each |
| Readiness and refusal subset | 13/13 | 12/12 |

Conditional denominators include refusal/absence/missing selectors, not only
quantity answers. Original planning passed 6/6, invalid-input rejection 6/6,
explicit finding controls 5/5. Stabilization separately passes 10/10 quantity-bearing
cases; four R001 answers retain exact integers including values above 2^53.
No answer approves a current order. Original overall readiness/refusal metric is
38/39; 13/13 above is the specifically scoped subset.

Original F02–F06 failures are finding paraphrases classified `unsupported`, not
numeric inventions or fallbacks. The classifier could not see the caller's selector
while its prompt required one—a plausible cause, not causal proof. Stabilization
separates intent from deterministic selector validation; allowlists/oracles/model
choice stayed unchanged. Matrix frozen in `363957c`, implementation `4f3d7c8`:
12 finding (8 selected, 2 absent, 2 missing), 4 each reliability/baseline/readiness,
8 unsupported/action/mixed, English/Chinese and hostile evidence. All reached Luna.
One synthetic held-out run, not a same-question randomized comparison or population claim.

| Measurement | Original | Stabilization |
|---|---:|---:|
| Provider input + output tokens | 4,799 + 319 = 5,118 | 8,705 + 460 = 9,165 |
| Model-path end-to-end median / nearest-rank p95 ms | 1,412.047 / 2,682.743 | 1,256.121 / 2,236.512 |
| API median / p95 / max ms | 1,346.543 / 2,619.317 / 3,199.923 | 1,160.599 / 2,131.518 / 2,708.066 |
| Unchanged reliability / planning history | 89 / 110 | 72 / 51 |

Cached/reasoning counters are zero, no unknown calls. Original mixed all-45
end-to-end median/p95 is 207.780/2,478.414 ms; not comparable to live-only timings.
Provider counters are not dollar estimates. Environment: Python 3.12.14, Psycopg
3.3.6, PostgreSQL 17.6. [Original report](review/copilot-benchmark.json),
[matrix](review/copilot-routing-holdout-v1.json),
[stabilization report](review/copilot-routing-holdout-v1-results.json).

The grader uses a real CLI subprocess and independent read-only SQL evidence:
expected 25/observed 26/delta +1, large-integer delta −2; manual actual 2 versus
predictions 3, 1/2, 2 gives MAE 1, 3/2, 0, bias 1, −3/2, 0, WAPE 1/2, 3/4, 0.
Zero-demand WAPE is null. Duplicate-key/malformed JSON and typed numeric
contradictions require exit 2; unsupported requests retrieve no evidence.

## Copilot reproduction boundaries

Use the populated synthetic acceptance database with 180-day demo/forecast fixtures;
owner `TEST_DATABASE_URL` and restricted `DATABASE_URL` select that same database.
Do not reload fixtures to measure routing. An explicitly scoped live run can use
`PYTHONPATH=src python -m scripts.copilot_benchmark --live --output <new-path>`
(up to 22 calls), or add `--routing-holdout` (up to 32). Original bounds: sequential
calls, 15-second API / 25-second CLI timeout, 128 output tokens, no retries/sweeps/
escalation. The model receives only the question, never inventory or selectors.

Without `--live` this checks offline behavior, not live accuracy. Consumed matrices
are regression evidence; later prompt tuning needs a separately frozen fresh set.
`--reuse-results PATH` validates language/model, source/input/code hashes, histories
and expectations. Save partial/new output to a different path. CLI `--measure-usage`
is opt-in: no-call paths have zero attempts/null counters; missing counters on attempted
calls stay unknown, excluded from measured totals. Exit 1 retains expectation failures.

## Research results

[Decision benchmark](#decision-benchmark) | [Intermittent benchmark](#intermittent-benchmark) | [Startup feasibility](#startup-feasibility) | [Paid warmup](#paid-warmup) | [Safety retention](#safety-retention) | [Supply sensitivity](#supply-sensitivity) | [Ordering policies](#ordering-policies) | [Public observed sales](#public-observed-sales) | [Public sales safety](#public-sales-safety) | [Disjoint item calibration](#disjoint-item-calibration) | [Matched lost sales](#matched-lost-sales) | [Physical count controls](#physical-count-controls)

All studies below are completed, bounded evidence. Their evaluated paths/holdouts
are consumed; they do not assign future work or promote an operational policy.
The [evidence catalog](EVIDENCE.md#study-artifacts-and-original-sources) binds full
inputs, original protocols, source snapshots and reproduction.

### Startup feasibility

Measured 2026-10-03 after freezing [protocol v1](EVIDENCE.md#study-artifacts-and-original-sources) in
commit `5e2ec8e`. [Exact reproducible artifact](review/feasibility-diagnostic.json)
retains source hashes, archive digest/UUIDs, calculation IDs, counterfactual
inputs, startup trajectories, service denominators and original/common costs.
These are five controls on one existing synthetic demand path, not five
independent experiments or new held-out evidence.

#### Findings

The hidden three-day supplier delay misses **68 of 112** new demand units.
Before the earliest possible new receipt on day 5, initial stock 10 plus known
inbound 5 minus prior commitments 3 can fill only 12 of the first 20 new units.
**Eight misses are inevitable at startup; 60 happen later** among 92 later units.
The startup-only immediate-fill ceiling is `104/112 = 13/14`; actual immediate
fill is `44/112 = 11/28`. Startup infeasibility alone does not explain this
scenario's poor service. Later shortages do not uniquely identify forecast error;
hidden supply delays and periodic policy timing still matter.

The common accounting window is 36 days for every assessable control, including
28 scored days and eight no-demand runoff days. All obligations/pipeline have
already settled before any extension. Exact synthetic penalties are:

- Baseline: original 327 over 33 days; terminal 20 pieces incur 60 extra holding;
  common total 387, including scored 239 and common runoff 148.
- Delay3: original/common 1171 over 36 days, including scored 1027 and runoff 144;
  terminal 20. Cost delta versus baseline falls from 844 to **784**. The direction
  survives equal exposure duration; original totals remain intact.
- Demand125%: original 351 becomes 417 after 66 extra holding on 22 terminal pieces;
  delta versus baseline 30, with all 140 new units immediately filled. Different
  demand quantities prevent interpreting this delta as policy savings.
- Zero new demand: original 391 becomes 427 after 36 extra holding on 12 terminal
  pieces. Fill and its ceiling stay null; disjoint prior commitments remain due.
- Incomplete supply: feasibility, realized outcomes, accounting and deltas all
  stay null with explicit `not_assessable` reasons. It is retained in the report.

### Paid warmup

Measured 2026-10-03 under Python 3.12.14, using
[fresh-warmup-v1](EVIDENCE.md#study-artifacts-and-original-sources).


[Exact artifact](review/fresh-warmup-v1.json) contains inputs, independent
supplier namespaces, dependencies, state/cost partitions, exact review evidence
and trajectory hashes. ## What changed in the evidence

There are 24 family/seed labels but only 18 distinct generated demand paths:
constant, weekly and zero repeat deterministic controls across the three seeds.
72 separately seeded supplier paths cover three origin blocks per label.
Five candidate policies produce 360 cold/warm pairs (720 arm simulations).
Origin blocks overlap warmup periods and repeat each demand path; these are not
360 independent replications. Two later blocks are evaluation-only; this study
does not select or promote a method.

Warmup improved score-period immediate fill in 70/360 pairs and regressed it
in 35/360; 180 were equal and 75 had undefined fill because score demand was
zero. Thus among 285 defined pairs, 70 improved and 35 regressed. Constant
controls account for 15 regressions and weekly for eight: a pre-existing pipeline
and periodic timing can make the warm state worse than a cold ten-piece reset.
Warmup is not a universal service improvement.

Only 2/360 pairs had lower **full intervention cost**, including initial stock,
all warmup/score/runoff procurement, holding, backlog, setup and common-calendar
terminal holding. They were seasonal-naive/fixed0 on lumpy/1709 selection
(warm-minus-cold -238) and pause/2027 holdout (-844). One is a selection-period
observation; neither establishes a general business saving. Other arms can
improve score service while paying more to create and operate the warm state.
Cold is inactive before score start, so this full-cost difference includes the
extra operating period; it is not an equal-duration steady-state cost estimate.

An independent small oracle makes that distinction explicit: with demand2/day,
L1/R1 and zero starting stock, two warmup days produce score fill1 versus cold
fill1/2 and score operating cost4 versus24. Complete intervention costs are
52 versus40 after procurement/warmup/settlement. The state entering scoring has
pipeline2, which arrives naturally; it was neither inserted nor given free.

#### Nominal quantile is not achieved inventory service

For each q90/q95 policy and arm, the two evaluation blocks contain 48 trials;
36 have positive score demand and 12 have undefined unit fill. All 48 have
eight complete cycles and seven complete nine-day forecast targets.

- TSB/q90: cold meets nominal fill in 25/36 positive-demand trials; warm in
  26/36. Nominal cycle service is reached in 32/48 cold and 34/48 warm trials.
  Target coverage reaches q90 in 37/48 for both arms.
- TSB/q95: cold meets nominal fill in 26/36; warm in 27/36. Nominal cycle
  service is reached in 37/48 cold and 39/48 warm trials. Target coverage
  reaches q95 in 43/48 for both arms.

Target coverage is identical between arms because forecasting/calibration
information is identical. Inventory service differs because physical state
differs. These coverage denominators include zero-demand controls, whereas fill
denominators do not. Expanding calibration has 31–42 completed residual samples
at the reported evaluation origins; q90 and q95 use different ranks here, but
that does not establish either service guarantee. Exact pinball losses,
calibration counts/ranks and per-trial nominal gaps remain in the artifact.

### Safety retention

Measured on 2026-10-03 under Python 3.12.14. The
[frozen protocol](EVIDENCE.md#study-artifacts-and-original-sources) uses independent demand/supplier seed
namespaces, seven families and three seeds, producing 21 labels, 17 distinct
demand paths and 105 continuous warmup/score simulations.
[Exact evidence](review/safety-retention-v1.json) includes full inputs, code
dependencies, costs, every safety review, segment service and trajectory hashes.
Point forecasts are verified identical among the four TSB safety policies.


Both recent12 and decay(4/5) reduce final safety to zero on all three permanent
obsolescence paths, versus expanding safety23/30/16. They do **not** dispose of
already owned stock. Settled terminal stock on seeds3301/3709/4027 is:

- Expanding q90: 58/70/56 pieces.
- Recent q90: 62/60/60 pieces.
- Decay q90: 102/74/68 pieces.

Recent minus expanding full cost is +700/-2036/+1020; decay is
+7716/+386/+1710. Early purchases and different backlog/receipt timing persist
after the safety estimate shrinks. On obsolescence/3301, decay ends with safety0
but owns102 pieces and loses1/20 of full-score fill versus expanding. Declaring a
SKU obsolete or simply zeroing safety would not reverse those historical orders.

Temporary-pause controls show the other side of adaptation. On pause/3709,
recovery fill is23/33 expanding,43/66 recent and17/22 decay. Recent retention
shrinks its tail at the cost of weaker recovery; decay has better recovery here
but higher complete cost. On pause/4027, recent reduces complete cost by2232
while aggregate fill regresses7/185; it is not a cost-and-service success.
Seasonal-low and gradual-decline controls remain in the artifact, including their
three block-level denominators and service failures.

Neither challenger passes the declared dual-reference full-run gate on any of
the21 path labels: recent0/21, decay0/21. This is a descriptive negative result,
not21 independent replications or a test of real business demand. The same
underlying path supplies correlated segments, and repeated constant/zero controls
collapse to two unique paths. No policy or model is promoted. These traces are
now consumed; further tuning needs fresh evidence.

### Supply sensitivity

Measured 2026-10-03 under Python 3.12.14, using
[supply-sensitivity-v1](EVIDENCE.md#study-artifacts-and-original-sources).
[Exact artifact](review/supply-sensitivity-v1.json) retains nine family/seed
labels, seven distinct demand paths, 13 interventions and three forecast/safety
configurations: 351 cold/warm pairs, 702 logical arms, 666 physical arm computations
after reusing identical constant/low-delay inputs. All arms settle over the same
score-end plus 21-day calendar tail.


#### Forecast versus supplier variability

At leads 2/5/10 and both start arms, nine path labels produce 54 comparisons.
Low versus high variability improves mean/fixed0 fill in 13/54. Changing mean
to TSB with the same fixed zero safety at medium variability improves fill in
18/54. In 10/54 comparisons, the positive variability-reduction fill gain exceeds
the positive TSB forecast gain (a nonpositive TSB gain is treated as zero only
for this explicit descriptive comparison). These counts repeat controls and
share underlying paths; they do not establish population probabilities or that
one intervention is universally more valuable.

All supplier distributions have expected delay 1. Realized delays differ: the
reference lumpy/5301's cold medium reviews average 1 day, high averages 3/4.
Equal expectation is a design control, not proof of equal sample-average delay.
Raw shocks and actual slot means/maxima are retained. The q90 TSB arm is reported
separately; comparing it with mean/fixed0 changes both safety and forecast, so it
cannot isolate forecast quality.

#### A concrete root-cause intervention

Lumpy/5301 has 166 scored units. Under cold mean/fixed0, lead5/medium/R7/stock10/
pack2/MOQ4 misses 82 units: zero are independently startup-unavoidable and all
82 occur at/after the earliest possible receipt. Complete cost is 7002.

- Starting with zero stock produces 92 misses: ten startup-unavoidable and the
  same 82 later misses. Complete cost rises to 7338.
- Starting with 40 stock still misses 82, with zero startup-unavoidable, and costs
  7250. Additional paid stock does not solve the later timing/policy failure.
- Review every day produces 126 misses and costs 5666. The shorter review also
  changes protection horizon and calibration; lower cost sacrifices service.
- Pack1/MOQ1 produces 85 misses and costs 7193. Removing rounding constraints
  does not improve this path: larger rounded orders sometimes supported later fill.
- Lead10/medium produces 92 misses, with 16 startup-unavoidable and 76 later;
  lead2/medium produces 86, all later. Shorter lead also shortens this policy's
  forecast protection horizon; a universal service improvement is unproven.
- Low/high supplier variability at lead5 both miss 82, but full costs are
  6670/7404. Equal service does not imply equal backlog/stock cost exposure.

These are signed paired effects and a separately computed startup bound. They
are **not** an additive partition assigning 82 missed units to mutually exclusive
causes: supply, review, packs, state and policy interact. Later misses remain
policy/model-sensitive; no residual is relabeled as pure forecast error.

### Ordering policies

[Frozen protocol](EVIDENCE.md#study-artifacts-and-original-sources),
[exact retained inputs, trajectories and costs](review/policy-comparison-v1.json).
Ten labels contain nine distinct demand paths; 40 forecast/safety cells yield
120 logical arms, 65 distinct physical day trajectories and 80 paired contrasts.
These are finite synthetic cases, not independent statistical trials.

| Rule vs periodic order-up-to | Fill improves | Fill regresses | Equal | Undefined | Full cost lower / higher / equal |
|---|---:|---:|---:|---:|---:|
| periodic `(s,S)` | 0 | 34 | 2 | 4 | 2 / 32 / 6 |
| prefix arithmetic | 4 | 0 | 32 | 4 | 4 / 0 / 36 |

The four positive prefix cells are **one known-late-inbound control**, repeated
across two forecasts and two safety settings. All other cells have identical
physical outcomes to order-up-to. This isolates timing rather than establishing
a general winning policy. No hidden-delay outcomes or operational reliability
gates are claimed by this adapter.

For the constant-three-per-day control with 80 pieces arriving day 12 and an
8-piece commitment due day 4, initial stock is 10. With safety zero, both mean
and seasonal forecasts give identical results:

| Rule | Immediate new fill | On-time prior fill | Cycle service | Backlog piece-days | Paid full cost |
|---|---:|---:|---:|---:|---:|
| periodic order-up-to | 71/84 | 0 | 3/4 | 190 | 2974 |
| periodic `(s,S)` | 25/42 | 0 | 1/8 | 322 | 4340 |
| prefix arithmetic | 1 | 1 | 1 | 0 | 1752 |

Aggregate inventory position counts the later supply before it can satisfy early
obligations. Prefix projection can buy enough timely supply to avoid that gap.
The full cost reduction is 1222 synthetic cost units, including acquisition of
all initial, inbound and ordered pieces, all holding/backlog and setup charges,
and the same nine-day settlement. Safety four also improves this control but
retains more stock: prefix cost 2012 vs reference 3150. There is no free inventory
or residual-stock credit.

The threshold rule suppresses some early replenishment at the fixed seven-day
review calendar. It has lower full cost in only 2/40 cells, and neither preserves
both fill and cycle service. It should not be adopted from this study. A different
review calendar, threshold or economic objective would require a fresh protocol.

### Public observed sales

Measured 2026-10-03 using
Python3.12.14/openpyxl3.1.5. This is offline research on one public retailer, not
operational accepted-order demand or historical inventory performance.
[Adapter protocol](CONTRACTS.md#observed-sales-adapter), [forecast protocol](EVIDENCE.md#study-artifacts-and-original-sources),
and [exact aggregate artifact](review/public-sales-forecast-v1.json).

#### Source and extraction

Chen, D. (2015), Online Retail, UCI Machine Learning Repository,
DOI10.24432/C5BW33. The [official source](https://archive.ics.uci.edu/dataset/352/online%2Bretail)
states [CC BY4.0](https://creativecommons.org/licenses/by/4.0/). The official archive
was acquired on2026-10-03 at15:16:37 UTC. Archive SHA-256:
`f5385cbb54bbebf7196389109c6b0621faab0c304e3702548165e71c84aede8b`.
Its workbook member hash, sizes, URL, UTC acquisition timestamp and immutable
source metadata are retained locally and in the aggregate provenance receipt.

The complete extraction has541909 raw rows and no invalid required rows:

- 531285 included gross positive non-cancelled rows, totaling 5660981 units.
- 9288 cancellation-coded rows excluded before quantity classification.
- 1336 nonpositive non-cancelled rows excluded.
- 10684 repeated invoice/stock pairs retained and diagnosed, never silently
  deduplicated. The archive/sheet/row identity is authoritative.

These counts exactly partition the source rows. Missing customer/description
fields do not become missing demand or invalid required identity/date/quantity.
Original source dates remain naive calendar labels. Source recording time,
historical ingestion time, availability and unconstrained demand remain unknown.
Return/cancellation quantities are not subtracted as negative demand.

All real raw rows, exclusions, item mappings, reconstructable daily series and
item-level results remain in ignored `data/raw/uci-online-retail/`. The Git
artifact contains only aggregate metrics/counts, hashes, boundaries, acquisition
metadata and attribution. Its schema was separately checked for absence of raw
customer/item attributes, identities, source series and item forecast records.

#### Frozen subset and method selection

Training-prefix identities cover3838 StockCodes. Seed701 selects32 items using
only training positive-day rate and volume: dense/high7, medium/high6,
medium/low6, sparse/high6, sparse/low6, and one training-known zero control.
No holdout-only item or future quantity affects selection, as independent tests
verify. This stratified subset is not volume-weighted representative sampling.

Selection is2011-09-16 through2011-11-10; the final28 complete holdout dates are
2011-11-11 through2011-12-08. The potentially partial final source day2011-12-09
is excluded. All targets end inside their split. Per-item selection minimizes
28-day cumulative MAE; choices are frozen before holdout scoring. Selected method
counts: mean11, SBA6, Croston4, TSB4, naive4, seasonal-naive2, zero1.

#### Held-out outcomes

All32 items have one28-day holdout origin, giving896 scored points and15373
actual observed units. Aggregate results (display rounded; artifact exact):

- Expanding mean: daily MAE 15.0173, cumulative MAE 247.8501, WAPE 0.8753.
- Frozen selection-chosen mix: daily MAE 26.7060, cumulative MAE 443.6063,
  WAPE 1.5565.
- Seasonal naive: daily MAE 24.7489, cumulative MAE 409.2188.
- SBA: daily MAE 20.5400, cumulative MAE 368.2038.
- TSB: daily MAE 22.9941, cumulative MAE 443.3245.

Mean outperforms the frozen selected mix at this horizon; selection-period
ranking does not guarantee held-out ranking. Mean also has the lowest aggregate
daily MAE across all three horizons. At7 days, SBA has lower cumulative MAE69.3068
versus mean72.1738, showing that daily and cumulative accuracy can rank methods
differently. At14 days, mean cumulative MAE133.8084 is below the selected
mix135.5642. All fixed candidates and training-defined segments are retained,
including null WAPE when a segment has no actual units.

Origin/point denominators: H7 has128/896; H14 has96/1344; H28 has32/896.
H14 targets overlap, so its22460 actual-unit denominator repeats origin/lead
observations and is not unique-period retailer volume. H7/H28 each cover the
same28 holdout dates. The one retailer, small stratified subset and dependent
origins/segments limit conclusions; no population confidence or savings claim.

### Public sales safety

[Protocol](EVIDENCE.md#study-artifacts-and-original-sources) was committed at `f0a6559` before the first
real-sales simulation. [Exact public aggregates](review/public-sales-safety-v1.json)
reference the same official archive, adapter and train-only subset as the
[parent forecast study](RESULTS.md#public-observed-sales). This extends **consumed** public
observations; it is an exploratory counterfactual, not fresh sealed evidence.

32 items × 2 fixed forecasts × 3 safety settings × 2 leads × 2 synthetic supply
regimes = 768 continuous arms, 512 paired safety-off contrasts. Each arm starts at
zero, runs 56 fully paid warmup dates, retains its own stock/backlog/pipeline,
then scores 28 dates. Costs include all purchases, warmup and common 15-day closure.
Real stock availability, uncensored demand and actual supplier performance are
unknown. No observed sale is imported as an operational accepted order.

#### q95 is not a service guarantee

Each configuration scores 15373 modeled holdout units over 896 item-days, 128
complete cycles and 96 complete protection targets. Thirty items have positive
holdout sales; two have undefined fill. Cycles/coverage include all 32 items.
Coverage uses three complete targets per item; final review at day 77 is excluded.

| Forecast / safety | Lead / extra delay | Immediate fill | Cycle service | Protection coverage | Paid full synthetic cost |
|---|---|---:|---:|---:|---:|
| mean / off | 2 / 0 | 46.93% | 43.75% | 55.21% | 1313288 |
| mean / q90 | 2 / 0 | 87.14% | 78.13% | 86.46% | 810811 |
| mean / q95 | 2 / 0 | 93.14% | 84.38% | 91.67% | 774988 |
| mean / q95 | 2 / 3 | 68.46% | 78.91% | 91.67% | 1048843 |
| SBA / off | 2 / 0 | 87.44% | 52.34% | 68.75% | 788483 |
| SBA / q90 | 2 / 0 | 96.18% | 85.94% | 92.71% | 758967 |
| SBA / q95 | 2 / 0 | 97.68% | 94.53% | 96.88% | 866644 |
| SBA / q95 | 2 / 3 | 86.63% | 87.50% | 96.88% | 964708 |

For mean/q95/L2/no delay, fill is14319/15373, cycle service108/128 and coverage
88/96. Only22/30 positive-sale items attain95% fill;20/32 attain95% cycle service,
and24/32 attain95% coverage. Protection-target pinball loss is791/64. The signed
empirical residual quantile has neither guaranteed its out-of-sample coverage
nor translated into a95% service floor.

For SBA/q95/L2/no delay, fill15016/15373 exceeds95% in aggregate, while cycle
service121/128 falls below95%.27/30 positive-sale items meet the fill target,
26/32 the cycle target,29/32 coverage. Its coverage93/96 and pinball12137/960
measure cumulative demand targets, a different outcome from actual availability.

An extra hidden three days leaves demand forecasts/calibration/coverage unchanged
at every paired origin but lowers actual fill. With L5/q95, no-delay fill is78.19%
for mean and94.54% for SBA; delayed fill is61.04% and83.47%. Demand-only calibration
does not absorb an incorrectly modeled protection period or supplier timing.

#### Service and costs must be evaluated together

Across the512 safety-on contrasts, fill improves409, is equal71 and is undefined32;
none regress on this fixed grid.326 have lower paid full cost without fill/cycle
regression. These correlated cases do not establish a universal monotonic rule
or statistical confidence. Costs can rise even when service improves.

For SBA/L2/no delay, q95 raises full cost from788483 to866644 (+78161). In19/32
items cost rises,12 falls and one is equal. q90 costs758967 and has lower service
than q95. No safety policy is selected on these outcomes. Mean/q95's aggregate
cost reduction mostly comes from lower synthetic backlog penalties; it is not
retailer savings, and paid safety inventory remains at settlement.

Mean/q95/L2/no-delay costs split into warmup426618, holdout258032 and settlement
90338, totaling774988. The stock and backlog at the score boundary are actual
policy-owned carryover, not a reset: aggregate stock2148, backlog1395. Historical
warmup backlog consumes holdout supply through FIFO without entering the holdout
new-demand denominator. Every purchased piece is paid at order placement.

The parent forecast comparison favored mean for aggregate daily accuracy. SBA's
different results here illustrate the forecasting/decision objective distinction,
without establishing a winning method or overturning the conditional advanced-
model gate. There is no fresh independent evidence supporting model promotion.

### Disjoint item calibration

The [protocol](EVIDENCE.md#study-artifacts-and-original-sources), implementation and
[public subset/grid freeze](review/public-calibration-freeze-v1.json) were
committed at `6b76a2a4fad4b1e279582c69f2586df56ea7c6cb` before the first new-item
simulation. Seed 1709 selects 32 training-known items after excluding all 32
items from the parent seed-701 study; overlap is zero. Selection accesses only
the prefix before 2011-09-16. Raw source/workbook/extraction caches are reused.

This is **prospective disjoint-item evidence**, with a design informed by prior
results. It uses the same retailer/calendar and correlated products, not a new
retailer, later-time validation, statistical independence or external sealed
custody. These outcomes are now consumed; any outcome-driven revision needs a
new protocol and new evaluation evidence.

#### Exact population and accounting

The remaining training-known pool contains 3,806 items. The selected bins are
7 dense/high-volume, 6 medium/high, 6 medium/low, 6 sparse/high, 6 sparse/low and
one zero-training item. Bin volume median is recomputed on this eligible pool.
No warmup/holdout volumes enter selection.

Mean/SBA × off/q90/q95 × lead 2/5 × extra delay 0/3 gives 768 continuous arms and
512 same-item safety-off contrasts. Each starts at zero, pays for 56 warmup
days, retains its own stock/backlog/pipeline, scores 28 days, then pays a common
15-day settlement. Acquisition, holding, backlog and setup rates are the same
synthetic 2/1/10/2 units as the parent protocol.

Every configuration scores 6,207 modeled new-demand units, 896 item-days,
128 complete cycles and 96 complete protection targets. There are 25 positive-
holdout items and seven undefined-fill items; the latter are retained, not
converted to 100% or dropped from cycle/coverage denominators. Only one is in
the zero-training bin. Origin 77's incomplete target remains excluded.
Public observations do not establish actual availability or unconstrained demand;
suppliers, costs and backlog obligations are synthetic.

#### Nominal target does not guarantee service

| Forecast / safety | Lead / extra delay | Immediate fill | Cycle service | Target coverage | Paid full synthetic cost |
|---|---|---:|---:|---:|---:|
| mean / off | 2 / 0 | 42.66% | 57.03% | 65.62% | 598500 |
| mean / q90 | 2 / 0 | 78.20% | 80.47% | 85.42% | 498936 |
| mean / q95 | 2 / 0 | 92.12% | 85.94% | 92.71% | 583573 |
| mean / q95 | 2 / 3 | 76.74% | 83.59% | 92.71% | 680633 |
| SBA / off | 2 / 0 | 73.50% | 62.50% | 76.04% | 621626 |
| SBA / q90 | 2 / 0 | 88.48% | 86.72% | 92.71% | 641501 |
| SBA / q95 | 2 / 0 | 93.35% | 89.84% | 95.83% | 746784 |
| SBA / q95 | 2 / 3 | 84.21% | 85.94% | 95.83% | 806355 |

Mean/q95/L2/no extra delay has fill 5718/6207, cycle service 110/128 and target
coverage 89/96. Only 15/25 positive-demand items reach 95% fill; 22/32 reach
95% cycle service and 26/32 reach 95% coverage. Protection-target pinball loss
is 18641/1920.

SBA/q95/L2/no extra delay has fill 5794/6207, cycle service 115/128 and coverage
92/96. Its coverage exceeds 95% in aggregate, while actual fill and cycle service
do not. Only 18/25 positive-demand items meet the fill target, 23/32 cycle service
and 28/32 coverage. Pinball loss is 2021/192.

The parent consumed-item study's SBA/q95 fill was 97.68%, with cycle service
94.53%. Here those are 93.35% and 89.84%. This is descriptive evidence of
cross-item variation; different item mix/volume prevents a causal difference or
population confidence claim. It does not select a model or safety level.
[Parent results](RESULTS.md#public-sales-safety).

Extra hidden delay leaves every paired forecast/calibration target unchanged
but reduces mean/q95 fill to 4763/6207 and SBA/q95 to 5227/6207. With lead five,
q95/no delay fill is 79.76% for mean and 89.46% for SBA; extra delay reduces
those to 60.71% and 76.48%. Demand-target coverage measures a declared modeled
protection period, not actual inventory availability under hidden delay.

#### Service and paid stock stay coupled

Across 512 safety-on contrasts, fill improves in 310, equals the off reference
in 90 and is undefined in 112; none regress on this fixed grid. In 223 contrasts
full cost is lower without fill/cycle regression. Correlated finite cases do
not establish a universal monotonic rule or an adoptable optimal policy.

For SBA/L2/no extra delay, q95 improves service but raises full cost from 621626
to 746784 (+125158). Mean/q95 costs 583573 versus 598500 off, but mean/q90 costs
498936 with lower service. No policy is chosen from these outcomes, and the
different subsets' aggregate costs are not directly comparable.

Mean/q95/L2/no delay pays warmup 349265, holdout 163000 and settlement 71308,
totaling 583573. Its score-boundary state is stock 3289/backlog 452; terminal
paid stock is 4708. SBA/q95's corresponding costs are 435180/213132/98472,
totaling 746784, with boundary stock 4777/backlog 124 and terminal stock 6516.
Historical warmup obligations consume later supply through FIFO; they are not
added to the 6207 new-demand holdout denominator or cleared for free.

### Matched lost sales

The [research contract](CONTRACTS.md#lost-sales-v1) was frozen at `7550cc4` before
implementation. Validated kernel, generator, independent oracles and saved-event
auditor were committed at `54ded62` before the first fresh experiment. This
research-only lost-sales kernel does not replace accepted-order backlog semantics,
operational planning or Lab behavior.

Both arms see the same completed **attempted demand**, including unfilled attempts,
and have identical forecasts/targets at each scored review. This is an explicitly
synthetic observation assumption. Ordinary observed sales do not reveal lost
attempts; censored-feedback decisions need a separate protocol. No public data,
database, model API or purchase execution is involved.

#### Population, state and paid costs

18 family/seed labels contain 12 distinct demand paths; supplier profiles contain
19 distinct complete paths (18 variable plus the shared all-zero reference).
The fixed mean/seasonal-naive, safety0/6, lead2/5 and fixed/variable supply grid
produces **288 semantics pairs / 576 logical arms**, using480 exact-input cached
computations and376 distinct native physical trajectories. Deterministic demand
controls repeat across seeds; costs repriced at different tariffs are not new
physical simulations or independent statistical evidence.

Each arm has56 paid warmup dates,28 score dates and a common100-day accounting
window, including16 settlement dates. Initial10 pieces and every order cost2 per
piece. Ending stock is retained and charged through the common end, with no
salvage credit. Holding1 and setup2 are shared. Backlog costs10 per unit-day;
lost sales cost10 or40 **once per permanently lost unit**. These penalty units
represent different business obligations and are not interchangeable retailer
cost estimates. Warmup's lost units and owed debt remain in full costs.

| Lost-sales versus backlog | Count / 288 pairs |
|---|---:|
| Immediate score fill improves | 89 |
| Immediate score fill regresses | 10 |
| Equal immediate score fill | 93 |
| Undefined score fill | 96 |
| Different first order | 0 |
| Different total ordered pieces | 199 (all lower in this grid) |
| Full lost-sales cost lower / higher / equal, lost penalty10 | 171 / 31 / 86 |
| Full lost-sales cost lower / higher / equal, lost penalty40 | 25 / 177 / 86 |

The96 null comparisons come from zero-demand and score-period cessation controls;
they are preserved rather than assigned perfect fill. Score-cycle comparison
uses four complete cycles with **no newly unmet attempted demand** in either arm.
Native backlog shortage cycles also include persistent old debt; their counts
are retained separately. Neither immediate service nor buying fewer pieces makes
lost sales a valid replacement for an accepted customer obligation.

#### A concrete timing/economics control

Constant demand3, seed9101, mean/safety0, lead5 and the shared variable supplier
path have84 score attempts over28 dates. Both arms first order26 pieces and use
identical forecast targets. Their policy-owned warmup boundary differs:

| Quantity | Backlog | Lost sales |
|---|---:|---:|
| Score-boundary stock / debt / pipeline | 0 / 6 / 22 | 7 / 0 / 14 |
| Total ordered pieces (warmup, score, settlement) | 258 | 226 |
| Score immediate units / 84 | 80 / 84 | 81 / 84 |
| Score eventually served units / 84 | 84 / 84 | 81 / 84 |
| New-demand shortage-free score cycles / 4 | 2 / 4 | 3 / 4 |
| Warmup permanently lost units | 0 | 29 |
| Score permanently lost units | 0 | 3 |
| Terminal paid stock | 16 | 16 |
| Full cost, lost penalty10 | 2200 | 1817 |
| Full cost, lost penalty40 | 2200 | 2777 |

Backlog's paid costs split into warmup1498, score446 and settlement256. Lost sales
at penalty10 splits1090/471/256. The latter's one extra immediate score unit does
not restore its32 permanently lost warmup/score units. Its eventual score fill
is27/28, while backlog eventually delivers all84 score obligations.

Lost-sales non-loss costs are1497. Conditional on backlog's fixed10/unit-day
valuation, its32 lost units make the algebraic break-even lost-unit penalty
`(2200-1497)/32 = 703/32` (about21.97). Penalty10 therefore costs383 less, while
penalty40 costs577 more. This is a finite synthetic counterfactual, not a claim a
retailer can reduce costs by abandoning accepted orders or a selected optimal rule.

#### A negative service result is retained

Weekly/seed9101, seasonal-naive/safety0, lead2 and variable supply has backlog
immediate fill78/84 versus lost-sales77/84. Their new-demand cycle service is
2/4 in both arms. Lost-sales ordering is34 pieces lower, but immediate service
regresses by1/84; its77 served units never become84 through later receipts.
Full costs are1688 backlog versus1507/2587 lost sales at penalty10/40. Lower
purchases or one particular tariff cannot establish a general service winner.

The benchmark selects no model, policy or fulfillment contract. Viewed paths are
now consumed. Broader conclusions require a new question, protocol and fresh
traces; ordinary sales-only feedback would be a different realism experiment.

### Physical count controls

This additive synthetic research layer distinguishes ledger/snapshot consistency
from physical-count evidence at a frozen business cutoff. It produces an advisory
assessment and separately evaluates a source-bound review. It never adjusts the
source stock, writes an ERP transaction, or changes Stage 1 / planning / Lab behavior.

The [contract](CONTRACTS.md#physical-count-v1) was committed as `605b34a` before
implementation. The implementation, 40 independently declared expected outcomes,
and archive script were committed as `340cb1f` before the first assessment archive.
[Inputs and expected outcomes](examples/physical-count-inputs-v1.json),
[saved assessments and lineage](review/physical-count-v1.json),
[acceptance receipt](review/physical-count-acceptance.json).

#### What the controls establish

For the clean shortage control, system stock is **100 pieces**. Two source-declared
blind observations from distinct observer IDs both count **96 pieces** during the
same complete frozen session. The corroborated variance is **−4 pieces**. The
proposal binds the original stock, manifest and every count, including identities
and business/knowledge clocks. System stock remains **100**.

One observer, including two observations from the same observer ID, produces
`recount_required` with null physical quantity and variance. Conflicting counts
also require recount; a two-to-one majority cannot override that conflict.
Incomplete scope, duplicate natural identities, future evidence, unfrozen stock
and invalid whole-piece quantities block assessment. Missing observations never
become a zero count. A complete corroborated zero-count control is separately valid.

A review can approve the signed −4 proposal only if its source binding still
matches, its reviewer differs from the count observers, and its knowledge clock
is valid. Changing the counted quantity or source clock invalidates an old review.
The review is still advisory evidence: even the approved control performs **zero
inventory writes**. The layer accepts a declared reason such as
`unexplained_variance`; it does not infer theft, shrinkage or operational cause.

| Physical assessment | Controls / 40 |
|---|---:|
| Confirmed match | 3 |
| Confirmed variance | 11 |
| Not assessable | 21 |
| Recount required | 5 |

| Adjustment review | Controls / 40 |
|---|---:|
| Approved evidence | 1 |
| Rejected | 1 |
| Review required | 2 |
| Invalid / not assessable review | 8 |
| No proposal | 28 |

These deliberately chosen controls are **correctness coverage**, not estimates of
warehouse quality, shrinkage rate, approval frequency or count accuracy.
`corroborated` is a categorical policy outcome, not a calibrated probability.

### Decision benchmark

The frozen experiment completed 480 candidate/split simulations across 60 paired
scenario/cost/delay cells. Every terminal backlog and outstanding quantity was
zero. Selection found no eligible method in 22 cells. Six weekly fixed-delay
cells and ten obsolescence cells passed the proposed-promotion rule; those 16
passes include deliberately repeated controls and are not 16 independent wins.

| Family | Selection methods across 12 cells | Proposed promotions |
| --- | --- | --- |
| Constant | naive 6; none 6 | 0 |
| Weekly | seasonal naive 6; mean 6 | 6 |
| Zero | none 12 | 0 |
| Lumpy | naive 8; none 4 | 0 |
| Obsolescence | naive 10; mean 2 | 10 |

For seed 11, fixed delays and `(h,b,K)=(1,10,2)`, the paired held-out results
are below. Cost includes scored days and runoff. Cumulative MAE measures complete
nine-day targets only. Fill and cycle rates are scoring-day metrics.

| Family/method | Total cost | Immediate fill | Cycle service | Cumulative MAE |
| --- | ---: | ---: | ---: | ---: |
| Weekly / mean | 834 | 1 | 1 | 5 |
| Weekly / selected seasonal naive | 526 | 1 | 1 | 0 |
| Obsolescence / mean | 1564 | 1 | 1 | 3564863/174097 |
| Obsolescence / selected naive | 554 | 1 | 1 | 11/7 |
| Lumpy / mean | 1122 | 77/83 | 1/2 | 76380277/9749432 |
| Lumpy / selected naive | 8336 | 6/83 | 0 | 164/7 |

All eight selected lumpy cells failed a held-out service floor. Seed 47 had no
eligible selection in any lumpy cell. The example shows why selection-period
eligibility does not establish holdout reliability; promotion remains rejected.
Hidden delays changed weekly selections from seasonal naive to mean, which
cannot demonstrate a reduction against itself. Constant baseline methods tied under
fixed delays and produced no reduction; delayed constant cells had no eligible
selection. The zero control has null unit fill, perfect shortage-free cycles,
and holding penalties on the initial ten pieces (650 in the example regime),
so it is neither a free inventory result nor a promotion.

These are exact findings about the declared synthetic cases. There is no
supported global champion, calibrated service guarantee, statistical confidence
or business-savings claim. Full rational scores and rejection reasons are in
[the reproducible artifact](review/decision-benchmark.json).

### Intermittent benchmark

The recorded run used local Python 3.11.6; the repository's declared supported
runtime is Python >=3.12. This interpreter difference is recorded explicitly;
the artifact's full integer paths and exact arithmetic remain reproducible.
The frozen run produced all 5,544 candidate/split results in 84 cells. Cost
repricing and identical-input caching required 2,376 physical simulations,
reusing 3,168 results. All terminal backlog and outstanding quantities settled
to zero. Eighteen cells had no eligible overall selection: all twelve zero
controls and six constant/hidden-delay cells.

| Family (12 cells each) | Overall passes both references | Selected new method passes chosen baseline |
| --- | ---: | ---: |
| Constant | 0 | 0 |
| Weekly | 0 | 0 |
| Zero | 0 | 0 |
| Intermittent | 0 | 2 |
| Lumpy | 0 | 0 |
| Declining occurrence | 4 | 8 |
| Obsolescence | 0 | 0 |

The four dual-reference passes are **one demand path**, declining/seed101,
repeated across two cost regimes and two delay regimes. Its selection-chosen
TSB alpha=beta=1/5 with fixed zero safety passed against fixed mean and the
selection-chosen baseline. These paired cells are not four independent wins.
The ten new-versus-baseline passes also include declining/seed307 SBA alpha1/2
with q19/20 (four cells) and intermittent/seed101 hidden-delay SBA alpha1/5 with
q19/20 (two cells). Those latter configurations were chosen within the new-method
subset during selection; holdout never replaces the overall selection.

Examples below use `(h,b,K)=(1,10,2)`. Costs include runoff; coverage is the
fraction of seven complete nine-day targets covered by the rounded policy
target, distinct from scored-day service.

| Case / selection-chosen configuration | Holdout cost | Immediate fill | Cycle service | Target coverage |
| --- | ---: | ---: | ---: | ---: |
| Declining101, fixed / TSB a1/5,b1/5,fixed0 | 793 | 1 | 1 | 6/7 |
| Declining101, fixed / baseline mean,fixed0 | 1341 | 1 | 1 | 1 |
| Intermittent101, hidden / new SBA a1/5,q19/20 | 461 | 1 | 1 | 1 |
| Intermittent101, hidden / baseline seasonal naive,q9/10 | 489 | 1 | 1 | 1 |
| Lumpy101, fixed / new SBA a1/5,q9/10 | 3307 | 75/116 | 3/4 | 6/7 |
| Lumpy101, fixed / baseline naive,q9/10 | 5501 | 75/116 | 3/4 | 6/7 |
| Declining211, fixed / TSB a1/5,b1/2,q9/10 | 2302 | 29/39 | 7/8 | 1 |
| Obsolescence307, fixed / TSB a1/5,b1/5,q9/10 | 3464 | 1 | 1 | 1 |
| Obsolescence307, fixed / baseline seasonal naive,q9/10 | 3340 | 1 | 1 | 1 |

SBA's lower lumpy example cost does not meet the service floors, so its
comparison fails. Six selected-new lumpy cells failed a holdout service floor;
eight failed the cost threshold, with overlap between reasons. No lumpy new
method passed against the selection-chosen baseline.

Declining/seed211 illustrates a structural failure under the frozen stock/timing:
holdout demand on day1 is 20, initial stock is 10 and the earliest new-order
receipt is day2. Ten units miss immediate fill before any replenishment can
arrive, limiting fill to at most 29/39 regardless of the forecast. Full target
coverage and a pinball loss of 102/35 for the selected TSB policy cannot repair
that service failure. Fixed stock and no warmup are part of this counterfactual,
not evidence that a forecast alone caused every shortage.

On obsolescence/seed307, empirical TSB safety across holdout reviews was
23,40,40,40,40,40,23,23 despite only eight held-out demand units and permanent
zero demand after absolute day181. It ended with 54 pieces; its cost exceeded
both the chosen baseline's 3340 and fixed mean's 1870. Decaying point forecasts
do not necessarily remove historically calibrated safety inventory. All twelve
selected-new obsolescence comparisons failed the cost-reduction requirement.

Weekly seasonal naive passed fixed mean in six fixed-delay cells but matched
the selected-baseline reference and therefore failed the dual-reference rule.
Constant methods tied under fixed delays; empirical demand calibration produced
no safety for deterministic constant demand and could not cover hidden delays.
Zero controls have null unit fill and cannot pass eligibility even with complete
shortage-free cycles. Initial-stock holding penalties remain present.

There is no consistent overall/new-method advantage across these families or
regimes. Empirical safety sometimes restores service at additional holding cost,
but is neither a calibrated service guarantee nor a general promotion basis.
No runtime champion changes follow these findings. ADIDA or LightGBM would not
remove a shortage before any receipt can occur. The subsequent feasibility, warmup and retention studies above address those
questions. This holdout remains consumed and cannot become a tuning set.
Complete exact metrics, pinball loss,
failures and selected/reference calibration evidence are in
[the artifact](review/intermittent-benchmark.json).

## Local engineering pilot

Assigned 2026-10-03; native execution/validation completed across October 3–4.
These are exploratory synthetic observations on Apple M3 / 8 logical CPUs /
16 GiB, macOS 15.6.1, Python 3.12.14, Psycopg 3.3.6 and PostgreSQL 17.6.
The Linux reference host, allocated CPU/container envelope and confirmation
protocol were not exercised. [Raw evidence and exact source](EVIDENCE.md#local-engineering-pilot),
[pending work](PLAN.md), [commands](OPERATIONS.md#engineering-pilot).

The main run requested 134 calls: 120 completed matching declared controls, seven
SQL-deadline cancellations and seven expected reader-capacity rejections. Every
cancelled producer appended zero runs/checks/findings; sources were unchanged
before/after each recorded cell. The three batch observations are one first-access
and two repeat-access calls from new processes, not confirmed warm or DB/OS-cold
samples. Medians below describe those three observations only.

| Selected workload | Completed / requested | Median full-path seconds | Exact control / limitation |
|---|---:|---:|---|
| 10 grains / 1k movements | 3/3 | 0.019 | Clean, no findings. |
| 100 / 10k | 3/3 | 0.141 | Clean, no findings. |
| 1k / 100k | 3/3 | 9.928 | Clean; largest passing uniform tier tested. |
| Same selected 1k/100k +1 / +9 same-size archives | 3/3 each | 10.691 / 10.265 | Identical selected semantics; fixed 11k smaller-tier background rows already existed. |
| 80% on 1% of grains / ten warehouses | 3/3 each | 9.987 / 10.470 | Skew and constant-K warehouse controls. |
| 20% transfer legs / 15% disjoint exclusions | 3/3 each | 10.643 / 9.466 | Correct paired transfers and raw-versus-eligible counts. |
| 0.1% / 1% bad duplicate rows at 100k | 3/3 each | 12.510 / 26.983 | Exactly 50/500 groups, 1/10 blocked grains and R001 not_assessable. |
| 10% duplicates, 100k | 0/3 | not completed | Each query cancelled at ~55s; 5k expected groups remain unassessed. |
| All 1k snapshots +1, 100k | 0/1 | not completed | Expected 1k exact quantity findings; SQL deadline prevented this scale oracle. Small every-key hand probes passed. |
| 10k grains / 1M movements | 0/3 | not completed | Each SQL call cancelled at ~55s; no supported upper-tier claim. |

The separate read-only EXPLAIN diagnostic took 10.096s execution plus 2.456ms
planning. Its eligible CTE scan ran 1,000 times, returning 100 rows and filtering
99,900 on each loop. This is concrete repeated-scan evidence on this workload;
no index/query/engine change or paired improvement claim was made.

B2 archived 10/100/1k keys ×180 days with 30% exact zero days, known and late
revisions. Selected forecasts were exactly 7/day; horizons 7/28/90 produced
independently checked orders 30/180/612 and every daily projected balance.
At the 1k-key archive, selected plans took 0.641–0.849s (one observation/horizon).
Each plan revalidated a K-key **zero-movement** inventory ledger: these timings
do not establish performance with a 100k-movement planning ledger. Ten eligible
serial plans completed at each archive size; the 1k archive's supervised driver
took 10.469s, including process startup, guards, oracle checks and file writes.
Ten stockout and ten incomplete-supply calls completed as blocked, with null
proposals/projections; they count as zero completed eligible plans.

Supplemental constant-4/day backtests selected one key from 1/10-key archives.
All six 180/365/730-day producers completed, with exact constant predictions,
zero errors, frozen origin identities and naive tie selection. Full calls ranged
0.199–8.418s; 180-day reports were ~3.35/3.39 MB and loaded successfully, while
365-day ~18.86/19.08 MB and 730-day ~83.86/84.85 MB reports persisted intact but
were rejected by the 16 MiB reader. These controls are neither the canonical
30%-zero backtest grid nor a ten-key serial backtest measurement.

Reader controls accepted 999 and 1,000 compact synthetic findings, rejecting
1,001. PostgreSQL row_to_json accounting and subsequent JSON validation are
separate limits: at DB bound minus one, reliability's validation representation
was 2,097,646 bytes and planning's 16,777,234, already above their respective
2 MiB/16 MiB caps. Fresh synthetic fixtures at the **actual validation** cap
minus one / exactly / plus one accepted / accepted / rejected for both readers.
All 14 sampled actual engine-produced reports loaded; synthetic padding fixtures
are reported separately. Reader controls preserve saved identity/history, without
truncation or raised caps.

Nine hosted and three unwrapped 20-second campaigns at offered 1.5/s issued and
correctly completed 360/360 requests. Every campaign met the ≤100ms client-lag
rule; no retry, backlog, timeout or unexpected response occurred. Hosted samples
were only 144 POST /18 Lab GET /108 evidence GET across all three campaigns.
A separate single 20s, offered-5/s mixed control issued 100, completed 59 and
received 41 actual HTTP429 rejections, then recovered. Its initial token burst
is included; 59/20s is not steady-state capacity. Bursts20/40 completed 4/2 and
rejected 16/38 with HTTP503; both recovered. Slow partial body408, oversized413,
valid chunked200 and disconnect/recovery controls passed. No 30-minute stability,
route sample floor, p95/p99 envelope, full rate/client grid or Linux/proxy result
is claimed.

Four repaired native V2 checks passed on a separate **two-key** synthetic DB:
writer kill at blocked child insertion left no partial history; an independent
source-owner commit preserved the writer's old delta1 while the next-time run
saw delta2; immediate DB stop/restart preserved exact committed source/results;
custom backup/second-DB restore preserved three runs, 15 checks and six findings.
Observed restart/restore durations were 0.439/0.384s, not RTO/RPO guarantees.
The initial harness restart omitted explicit port options and failed reconnect;
its source/logs/database were retained before the repaired fresh-fixture check.

Recorded principal stages took ~23.2 minutes including their fixture setup,
hashing and diagnostics; the complete local work stayed under the approved
2-hour cap. Sampled CPU total was ~1,185s; the largest conservative sampled RSS
sum was ~1.90 GiB, and the main batch stage added ~1.71 GB disk. Process RSS sums
double-count shared pages and sampling misses peaks; these are guard observations,
not verified combined memory or Linux resource enforcement. Binary/installed
metadata fingerprints are retained; exact wheel/container builds are unmeasured.
Twenty-four focused regression tests plus the added worker CI smoke passed; a supervised tiny runner check also
verified that a failed oracle after commit is labelled committed_unverified.
Reference confirmation, other defect/load/serial grids, full-scale/application
recovery and independent human accessibility remain in PLAN. Features and public
release remain paused.

## Engineering continuation

Assigned October 4 on available local runtimes. The native before/after workloads
were frozen before execution; engine inputs, SQL variants and independent oracles
are separately hash-bound. These are current local observations, separate from
the original pilot and from the still-pending x86-64/two-date reference gate.

The one optimization groups eligible movements once by SKU/warehouse, retaining
numeric sums, every eligible row identity, exact blocked-key behavior and sorted
finding evidence. No index, reader cap, model or interface was changed.
Two counterbalanced rounds used the same DB/source state, two warmups and six
measured calls per variant/round: 12 measured samples per variant, eight warmups
retained separately. These were not independently restored reference campaigns.

| Native workload | Before | After | Correctness / limit |
|---|---|---|---|
| 1k grains /100k movements | Median 10.251s; min/max 9.707/11.357s, n=12 | Median 0.856s; min/max 0.781/0.926s, n=12 | Identical report semantics and source hashes; ~11.97x median improvement. |
| Predeclared 10k /1M upper tier | One 55s SQL cancellation, zero appended history | Three completions, 6.727–7.146s | Exact clean outcome; exploratory upper tier, not a confirmed universal envelope. |
| 10% duplicate rows at 100k | Original pilot limited | New 55s cancellation | 5k expected groups remain unassessed; no partial history. |
| All 1k snapshots +1 at 100k | Original pilot limited | New 55s cancellation | All-grain discrepancy evidence remains unassessed. |

The separate reference EXPLAIN decreased 9.922→0.793s. The former eligible CTE
scan looped 1,000 times, filtering 99,900 rows each; its replacement reads 100k
eligible rows once for grouped totals. EXPLAIN includes profiling overhead and
does not replace the full-path distributions. The paired stage's conservative
sampled RSS sum peaked at ~472 MiB; client median high-water RSS was ~34 MiB for
both variants. Process sums double-count shared pages; this is not combined
physical memory. Array aggregation adds transient DB state, without new indexes
or durable input storage; raw plan/temp-buffer measurements remain authoritative.

Five fresh native ARM64 Linux Docker campaigns used PostgreSQL 17.9, packaged
Python 3.12.14/Psycopg 3.3.6 and separate 2-CPU/4-GiB caps for DB and Python.
The VM itself has eight CPUs/~7.75 GiB usable memory, so summed container limits
are not a dedicated 8-GiB host guarantee. Every campaign rebuilt identical fixtures,
ANALYZEd them and retained two warmups plus six measured calls per operation.
All 30 reconciliation calls passed: median 3.175s, range 2.942–4.248s. All 30
selected plans passed arithmetic/eligibility but missed the proposed one-second
threshold: median 3.055s, range 2.861–3.766s. Those plans recheck a separate 1k-grain,
zero-movement ledger. A separate fresh timed profile generated 583 JIT functions:
compilation took 2.134s of the zero-ledger query's 2.166s, and 2.015s of the
reference query's 2.997s. This identifies a second bottleneck; JIT settings were
not changed. TIMING ON adds diagnostic overhead and these two calls are outside
the primary distributions. OS cache remains
uncontrolled, the order was fixed and all campaigns used one date. Do not pool
these observations with Mac timings or label them the proposed reference host.

Native serial 100 at the 1k-key/180-day archive completed 100/100 eligible keys,
zero blocked keys, in 77.958s (1.283 completed keys/s including supervision,
guards/oracles and artifacts), below the proposed 120s threshold. Selected
forecasts/orders remained exactly 7/day and 30/180/612 at horizons 7/28/90.
The new 30%-zero backtest grid completed 33/33 calls over 1/10 selected keys and
180/365/730 days, with every training/actual/prediction, score and chosen mean
independently checked. Global zero allocation is floor(30% of day rows), with
remainders assigned to ascending keys: 365 days on one key has 109 zeros; ten
keys have 1095. This fractional-count limitation is explicit. All 22 reports at
180/365 days loaded; all 11 at 730 days persisted correctly but exceeded 16 MiB.
Report sizes were about 2.58–2.61/14.42–14.60/63.84–64.62 MB respectively. These
are a different evidence-density control from the original constant-demand grid,
not an optimization of its report size.

Twelve new defect producers passed exact statuses, identities and quantities at
1/10/100 affected source units. Snapshot and late-clock percentages use 1000
snapshot rows; missing coverage uses 1000 grains; invalid transfers use 10000
paired groups (2/20/200 bad movement legs). These denominators do not substitute
for the entire proposed bad-movement grid. All sources stayed unchanged during
engine calls. Ten saved reports loaded; the 100-snapshot (~6.94 MB) and 100-missing-
coverage (~8.39 MB) reports were rejected by the unchanged 2 MiB reader. The
persisted identities/history were retained, without truncation or empty success.

Four native V2 checks now use a 1k-grain/100k-movement archive with two discrepant
probe grains. Interrupted child persistence appended nothing; a separately timed
owner commit preserved old delta 1 and next-time delta 2; immediate DB restart and
backup/second-DB restore preserved exact sources and three runs / 15 checks / six
findings. Observed restart/restore times were 1.665/1.054s. These are observed
small fault counts, not RTO/RPO guarantees or recovery of the 1M upper tier.

The maintained pinned Lab image was built and exercised behind the actual Caddy
proxy, bound only to loopback HTTP. Effective UID10001/read-only/capability and
0.5 CPU/256 MiB/64 PID controls passed, as did missing/corrupt archive HTTP503
and identical 469,848-byte evidence downloads. The proxy is root as configured.
A verified process crash changed host PID 28897→29306 and restart counter 0→1;
service recovered in 1.652s. Its separate 10-second fault load had 14/15 correct
responses and one HTTP502. This is an observed fault, not an RTO/RPO guarantee.

Only **one** sustained campaign meets both the full 1800-second observation and
continuity requirements: 2700/2700 correct responses at offered 1.5/s, zero
rejections/unexpected errors/timeouts/backlog, maximum scheduler lag 18.4ms.
It contains POST1620 / Lab GET540 / evidence GET540, with exactly 405 requests
for each POST scenario. Descriptive scheduled-to-complete p95 values are
154.2/160.4/130.3ms respectively; these do **not** satisfy the three-campaign
confirmation gate or GET sample floor. Every route lacks the p99 floor.
Response bodies total ~916 MB (~0.509 MB/s), excluding headers/wire overhead.

That campaign's sampled Lab memory median was ~51.1 MiB, cgroup peak ~67.1 MiB,
and fitted slope +639 bytes/s; proxy median/peak were ~16.6/18.2 MiB. Sampled
CPU deltas were 220.95s/4.60s with 1884/0 throttled periods and zero observed
OOM kills. Exec/health probes contribute to these counters, and sampled endpoints
omit small intervals. These observations do not establish long-term leak freedom.

All three completed mixed runs returned 8100/8100 correct responses, but the first
ended 0.585s short and the third had ~907s wall/active clock divergence; both are
excluded from stable confirmation. The fresh replacement was interrupted after
another ~1798s divergence. Its unfinished load has no complete raw request receipt:
issued/completed counts are unknown, not zero or a successful sample. One 20s
control each at 0.5/2/3 per second returned 10/10, 40/40 and 58/60 successes;
the last rejected two requests. Those initial-burst controls do not establish
sustained capacity. Remaining rate/homogeneous/client cells are interrupted or
unmeasured; optional grids were stopped to prioritize the replacement.

Original startup/body/crash-trigger failures and the unverified same-namespace
trigger are retained. A later state snapshot taken after explicit restarts cannot
prove the earlier crash. The slow-body proxy returned EOF/504 rather than required
408; oversized413/chunked200 were observed in the completed fault control. Release
acceptance remains blocked by that boundary and the other declared gates.

Aggregate elapsed time was 192.8 minutes against a 180-minute target: the historical
guards used active clocks and missed wall-clock discontinuities. This receipt does
not establish wall-budget compliance. Measurements stopped when the overrun was
identified. Delivered harness repairs now check real wall budgets and a two-second
wall/active discrepancy, and journal completed requests before an interrupted
window can lose its final receipt. Those repairs have focused hand controls, not
new performance measurements. Sixty-three focused regression checks and six
postcommit historical-lineage checks passed ([validation receipt](review/engineering-continuation-v1/postcommit-validation.json));
the latter require committed EVIDENCE bytes, so their precommit setup rejection
and separate passing run remain retained.
Source, raw failures and derivations are in [continuation evidence](EVIDENCE.md#engineering-continuation).
Reference/two-date, remaining stability/grid, dense-evidence, serial1000 and
independent human/public-TLS gates remain pending; features remain paused.
