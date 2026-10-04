# Stage 3 routing stabilization

> Historical assessment for the recorded source/environment. Use [STATE](STATE.md)
> for current phase, scope, integration mode and acceptance references.

## Frozen evaluation protocol

Frozen before changing routing, from integrated main `43a952d` (2026-10-02).
[Fresh held-out matrix](review/copilot-routing-holdout-v1.json): 32 new questions,
12 finding explanations (8 selected, 2 absent IDs, 2 missing IDs), 4 reliability,
4 baseline comparisons, 4 readiness and 8 unsupported/action/mixed requests.
English and Chinese, large exact integers and hostile source evidence are covered.
Questions and expectations are fixed before any evaluation. No question from the
original benchmark is used to choose prompt examples or add allowlist phrases.

One sequential Luna call per question, at most 32 requests, no retries, prompt
sweeps or model escalation. Use the existing independently checked database
evidence and unchanged citation/numeric grader. Evaluate routing separately from
end-to-end evidence and typed numeric fidelity, and report conditional fidelity
only with its denominator. Missing/absent selectors must remain not assessable;
the model receives only the question, never selectors or inventory evidence.
Explicit selector tests and existing malformed-input controls run without API
calls. No orders, source repairs, forecasts or new models are executed.

The original [45-case benchmark](STAGE3_BENCHMARK.md) and its artifact remain
historical evidence. This matrix becomes consumed evaluation evidence after its
first run and must not be reused to tune routing. A failure remains recorded;
any later prompt iteration needs a separately frozen fresh evaluation set.

## Measured result — 2026-10-02

Protocol frozen in `363957c`; implementation evaluated at `4f3d7c8`, descended
from latest integrated main `43a952d`. The fix removes the classifier's caller-ID
requirement and leaves evidence availability and selector validation to
deterministic code. No allowlist phrases, oracle expectations, model choice,
forecasting methods or contracts changed.

[Complete per-case answers and measurements](review/copilot-routing-holdout-v1-results.json):

| Dimension | Passed / evaluated |
| --- | ---: |
| Live intent classification | 32/32 |
| Finding intent (including missing/absent selectors) | 12/12 |
| Reliability / benchmark / readiness classification | 4/4 each |
| Unsupported, mixed and action requests | 8/8 |
| End-to-end evidence selection | 32/32 |
| Exact typed numeric fidelity | 32/32 |
| Complete citation fidelity | 32/32 |
| Readiness/refusal status and policy | 12/12 |

Conditional on correct routing, evidence/numeric/citation fidelity is also
32/32. Those denominators include refusals, missing selectors and valid absence,
not 32 quantity answers. The ten cases containing finding quantities or baseline
scores (H01,H04,H05,H06,H14,H16,H17–H20) separately pass numeric fidelity **10/10**;
four R001 finding answers retain exact quantities, including integers above 2^53.
Missing and absent selectors remain not assessable; question text never selects
a finding. No response approves a current order.

All 32 questions reached Luna, with no allowlist hits or service fallbacks.
Provider-reported usage: 8,705 input + 460 output = 9,165 tokens; cached and
reasoning tokens zero, no unknown counters. End-to-end median 1,256.121 ms,
nearest-rank p95 2,236.512 ms. Source digests stayed identical; history remained
72 reliability / 51 planning runs. Python 3.12.14, Psycopg 3.3.6, PostgreSQL 17.6.
This is one synthetic held-out measurement, without a same-question randomized
before/after comparison; it supports the corrected boundary without proving
population accuracy or isolating a causal effect. The historical 40/45 result
is preserved byte-for-byte and must not be presented as rerun or superseded data.

## Combined acceptance and reproduction

[Fresh acceptance evidence](review/stabilization-acceptance.json) records 104/104
tests on unmodified latest main `43a952d`, then 106/106 on locally integrated
`main` at `4f3d7c8`, each using a different fresh disposable PostgreSQL database.
Final counts: Stage 1 23, Stage 2 24, Stage 3 34, offline decision/intermittent 25;
zero failures, errors or skips. No real regression was found and no independent
oracle or citation/numeric grader was weakened. Source/test hashes and every
test outcome are retained. Later commits refresh documentation/evidence only.

The 480 decision and 5,544 intermittent results were reused, with current tests
checking provenance, exact inputs, completed-only calibration, costs and settled
terminal obligations. No new forecast fit, simulator experiment or dataset import.
Local PostgreSQL 17.6 acceptance is separate from pinned PostgreSQL 17.9 CI.

With fixture-owner `TEST_DATABASE_URL` and restricted `DATABASE_URL` pointing to
the same new disposable database:

```sh
PYTHONPATH=src python -m tests.bootstrap
PYTHONPATH=src python -m unittest discover -s tests -v
```

Reuse the populated acceptance database for the opt-in routing command:

```sh
PYTHONPATH=src python -m scripts.copilot_benchmark --routing-holdout --live \
  --output /tmp/copilot-routing-holdout-v1-replay.json
```

That command spends up to 32 requests. Replays are regression checks on a
consumed set, never fresh held-out evidence. Preserve the committed first-run
artifact; use another output path. Future routing evaluation requires a new
frozen matrix before inspecting outcomes.
