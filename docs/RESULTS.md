# Core and interface results

Measured outcomes consolidated from completed reviews. Original reports remain
immutable; [EVIDENCE](EVIDENCE.md) binds commits/environments. These are bounded
synthetic/local studies, not commercial savings, production readiness or fresh
results from documentation cleanup. Research studies have separate indexed
[result reports](README.md#research-results).

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
