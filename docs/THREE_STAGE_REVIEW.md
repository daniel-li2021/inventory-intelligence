# Three-stage review and comparative benchmarks

Review date: 2026-10-02. Review branch: `codex/three-stage-review`.
The user authorized merging the remaining fixes on 2026-10-02. The integration
incorporates the original Stage 3 main merge and all three Stage 2 slices.

Integration checkpoint: [PR 7](https://github.com/daniel-li2021/inventory-intelligence/pull/7)
is merged; fetched remote `main` at `dcada27` contains the reviewed integration.
[Main CI run 37044676872](https://github.com/daniel-li2021/inventory-intelligence/actions/runs/37044676872)
passed both jobs and all 76 tests on pinned PostgreSQL 17.9 / Python 3.12.12.
The executions and pre-merge limitations below are retained as historical evidence.
[Next investigation](NEXT_ROUND_RESEARCH.md) reuses the stored scores without
claiming new model or inventory-performance results.

## Evidence and live-data boundary

These are actual executions on PostgreSQL 17.6, Python 3.12.14 and Psycopg 3.3.6,
using the restricted `ii_runner` role. All business inputs are synthetic, as
required by AGENTS.md. They are not production apparel data or evidence of
commercial accuracy. No company data, credentials or confidential schema was
imported. Existing local runtime/binaries were reused; a separate temporary
cluster and fresh databases preserved other agents' databases.

The configured OpenAI key was detected without exposing it. Live Luna tests
remain pending an explicit reuse choice required by the API-key skill; this
review made **zero API requests**. Eight existing mocked language tests pass.
The older Stage 3 three-question live smoke result remains prior evidence,
not a new benchmark or a broad language-accuracy claim.

## What Stage 3 looked like

The original saved answers faithfully cited combined R001/R002/R004 findings,
including jacket expectation 25, observed 26, delta +1. The clean historical
run still blocked current replenishment because its cutoff was stale and no
proposal had been supplied. The mathematical benchmark showed seasonal naive
MAE 0 on a repeating weekly pattern, versus mean 12/7 and naive 3.

The limitation was integration: Stage 3 could not consume persisted Stage 2
benchmarks or proposals. At that checkpoint, main contained only Stage 2's forecast kernel; fuller
Stage 2 demand, evaluation and replenishment were on separate task branches.
The review branch combines their committed outputs with Stage 3 before testing.

## Thorough stage review and corrections

**Stage 1:** traced the CLI, `run_checks`, SQL projections/checks and persistence.
The independent oracle covers balances 109/25/15/0, posted reversals, transfer
legs, cutoff/watermark boundaries, missing inputs, partial local blocking,
large exact integers, rollback, immutability and role permissions. A valid
movement on a known but uncovered key produced a false pass. It now emits R005
`coverage_mismatch` with the exact source row and `unexpected_movement_key`;
R001 becomes not assessable. The first fix also blocked unrelated controls on
unknown references; the full suite caught that regression. The final fix keeps
unknown-reference handling local under R003. Frozen v1 interfaces are preserved.

**Stage 2:** traced daily coverage, both knowledge clocks, revision identities,
Pacific calendar/DST, exact baselines, common 7/14/28-day folds, holdout selection,
append-only runs, inventory revalidation and supply/proposal arithmetic. A late
revision of a selection-period order learned during holdout could change model
selection scores. Selection truth is now frozen at the earlier of evaluation
cutoff and holdout start; historical training is still replayed at each origin.
The independent regression adds quantity 700 to day 41, learned at day 60:
selection truth remains 7 and the chosen model/scores stay unchanged.

The planner's prefix arithmetic, reservation separation, delayed inbound and
pack/MOQ rules passed independent checks. A declared policy is not a calibrated
service guarantee; no extra forecasting model was justified by these small
synthetic experiments. The useful improvement is honest temporal isolation and
a broader benchmark, not a claim of production forecasting superiority.

**Stage 3:** traced evidence validation, explicit UUID retrieval, routing, size
bounds, freshness and CLI exits. A future-cutoff pass without metadata failure
was accepted by the old validator; it is now rejected. Valid failed future-cutoff
reports remain explainable. The additive copilot-2 adapter retrieves explicit
persisted forecasts, benchmarks and proposals in Repeatable Read, READ ONLY.
It validates exact scores, selection knowledge and projection/rounding evidence.
Historical proposal quantities stay inside citations; current order quantity
remains null. Missing, contradictory, float or oversized evidence errors.
Complete replay reports are about 4 MiB, so the separate planning loader allows
16 MiB while retaining the original reliability/file bounds. No truncation.

## Repeated validation

| Round | Tests | Result | Elapsed seconds |
| --- | ---: | --- | ---: |
| Original combined baseline | 69 | pass | 2.330 |
| Expanded regressions | 76 | 2 failures, corrected | 2.807 |
| Final fresh database A | 76 | pass | 2.842 |
| Final fresh database B | 76 | pass | 2.829 |

Final coverage: Stage 1 23 tests; Stage 2 24 tests; Stage 3 29 tests. No skipped
checks. A final four-test adapter followup also passed, including forecast
explanation and invalid UUID/nested-float handling. Reproduced latent defects
were failing independent assertions before correction, not weakened oracles.

Each benchmark round repeats every case three times. There is one baseline
round and two final rounds: nine repetitions per shared case, six with the final
adapter. All six final score/proposal results agree; unchanged inputs give stable
semantic results excluding run UUID/creation time. Source digests match before
and after each benchmark. Stage 3 retrieval/answer tests append no history;
Stage 1/2 intentionally append separate runs.

## Demand comparison and final data

Seven synthetic groups, 180 days each, three methods, 7/14/28-day horizons.
Each eligible group has 14 shared selection origins (98/196/392 scored points
by horizon) and a separate final 28-day holdout (7/14/28 points). Blocked demand
has 14 excluded origins, null scores and no model. The drifting series is
`2 + day_index // 14`; irregular demand uses seed 42 and `[0,0,0,2,5,9]` draws.
All groups retain source and cutoff identities. The exact JSON includes fold
training quantities, actuals, predictions, knowledge cutoffs and day issues.

Holdout **MAE in pieces**, decimal display rounded to three places; exact
rational MAE/bias/WAPE and all horizons are in the linked JSON. Selection uses
only 28-day selection MAE, never holdout performance.

| Group | Selected model | Naive MAE | Mean MAE | Seasonal naive MAE | Included/excluded origins |
| --- | --- | ---: | ---: | ---: | ---: |
| constant | naive | 0.000 | 0.000 | 0.000 | 14/0 |
| weekly | seasonal_naive | 1.857 | 1.719 | 0.000 | 14/0 |
| intermittent | seasonal_naive | 1.000 | 1.691 | 0.000 | 14/0 |
| zero | naive | 0.000 | 0.000 | 0.000 | 14/0 |
| blocked | — | — | — | — | 0/14 |
| drifting | naive | 1.357 | 6.423 | 1.357 | 14/0 |
| irregular | mean | 3.000 | 3.109 | 4.500 | 14/0 |

Seasonal naive wins the deliberately repeating weekly/intermittent controls.
For drifting demand, naive holdout MAE is 19/14 versus mean 3417/532. For irregular
demand, selection picks mean, but its holdout MAE 827/266 is slightly worse than
naive 3. This is a real comparative outcome of the experiment; switching the
model after seeing holdout would contaminate evaluation. Zero-demand WAPE is
null, including when its MAE is zero. No cross-group production winner is claimed.

The complete-supply proposal remains exactly **12 pieces**: on hand 10,
forecast 4/day for five days, reservation 3, confirmed inbound 5, safety 2,
lead 2 days, pack 6 and MOQ 10. Without-order balances are `[3,4,0,-4,-8]`;
raw need 10 is rounded to 12, giving `[3,4,12,8,4]`. Incomplete supply returns
`not_assessable` and null quantity. Stage 3 cites both outcomes without issuing
an order or presenting January inventory as current October stock.

## Execution-cost comparison

Wall-clock **median milliseconds** of three executions per round, on this
local machine; setup, fixture generation and source hashing excluded. No speedup
claim or statistical significance is inferred from these small samples. Stages
do different work, so their durations are not interchangeable efficiency scores.
Persisted Stage 3 benchmark retrieval includes decoding/validating a ~4 MiB run;
its legacy baseline explanation processes a tiny mathematical experiment.

| Operation | Baseline median ms | Final A median ms | Final B median ms |
| --- | ---: | ---: | ---: |
| stage1_clean | 4.00 | 4.14 | 4.82 |
| stage1_combined | 4.79 | 4.92 | 4.88 |
| stage2_benchmark_weekly | 203.89 | 217.04 | 201.64 |
| stage2_benchmark_irregular | 137.19 | 131.90 | 134.89 |
| stage2_plan_complete | 25.50 | 26.08 | 26.66 |
| stage3_clean | 0.34 | 0.36 | 0.40 |
| stage3_combined | 0.63 | 0.57 | 0.62 |
| stage3_persisted_benchmark | unavailable | 118.77 | 111.34 |
| stage3_persisted_proposal | unavailable | 18.27 | 18.06 |

## Reproduce and inspect

Use the existing fresh-database setup in [VALIDATION.md](VALIDATION.md), then:

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m scripts.review_benchmark --repeats 3 --output /tmp/review.json
PYTHONPATH=src python -m inventory_intelligence.copilot \
  --intent planning --planning-run-id UUID --language-model offline
```

Run the full suite only once per fresh database: named fixture loaders refuse
reloads. The benchmark can be repeated in that database and reuses its own
immutable archive. It does not modify existing source rows. Later model API
benchmarking should use the pending approved key, bounded synthetic questions,
explicit expected routes and separately reported latency/routing accuracy.

- [Baseline measurements](review/baseline.json)
- [Final round A: exact data, forecasts and scores](review/final-round1.json)
- [Final round B: exact data, forecasts and scores](review/final-round2.json)
- [Validation environment, rounds and findings](review/validation.json)
- [Persisted planning explanation contract](CONTRACT_COPILOT_V2.md)

Production-data integration, live language accuracy, PostgreSQL 17.9 CI on this
combined branch are not established by these local results. Git merge status is
verified separately from acceptance and benchmark evidence.

## Authorized merge validation — 2026-10-02

After incorporating main's original Stage 3 merge, all **76 tests passed**
with zero failures, errors or skips on fresh database `review_merge_final`
(PostgreSQL 17.6, Python 3.12.14, Psycopg 3.3.6). The reviewed implementation
and stored comparative benchmark data are unchanged by conflict resolution.
This additional integration round made no model API requests.
