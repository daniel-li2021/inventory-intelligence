# Stage 3 bounded end-to-end benchmark

On 2026-10-02, **40 of 45 cases passed**. Five finding paraphrases were
classified as `unsupported` instead of `finding`. The separate explicit finding
controls passed, localizing the observed failures to natural-language routing.
No forecasting models, routing prompts, source records or database history were
changed. [Full per-case answers, checks, timing and measured usage](review/copilot-benchmark.json).

## Design and bounds

The fixed matrix contains 5 reliability questions, 11 finding questions
(including 5 explicit controls), 4 baseline comparisons, 7 readiness questions,
6 unsupported/action requests, 6 persisted planning explanations and 6 invalid
input/retrieval cases. English and Chinese paraphrases, mixed requests, claimed
system instructions, hostile source strings, clean controls and failed runs
are included. IDs and expected intents are fixed before routing.

Every executed case invokes the real `python -m inventory_intelligence.copilot`
CLI in a subprocess. Supported database cases use explicit persisted UUIDs
through the restricted `ii_runner` connection. Planning remains an explicit
intent; the classifier does not support natural-language planning selection.
Caller-supplied JSON is used only for hand-calculated numeric and malformed
input cases. Refusal cases point at deliberately invalid evidence to verify
that unsupported requests avoid retrieval and validation.

Bounds: **45 cases, at most 22 API calls**, one sequential call per question,
15-second API timeout, 25-second CLI timeout, 128 output tokens per Luna call,
no retries, model escalation, parameter sweeps or new forecasting. Sol is
available only through an explicit `--model` flag and was not run.

The initial 40 cases made all 22 live calls. Five explicit finding controls were
added afterward without more model requests. The final artifact preserves the
40 measurements and records `reused_cases=40`, `new_cases=5`; it is one bounded
evaluation, not two independent benchmark rounds. Controls deliberately reach
the core paths that the five misroutes prevented from being exercised.

## Independent checks

The evidence oracle reads existing tables directly in a read-only Repeatable
Read transaction; it does not call Copilot loaders or answer functions. Clean
and combined reliability outcomes are independently fixed: pass/no findings
versus R001 quantity mismatch, R002 duplicate movement and R004 invalid transfer.
The mismatch must retain **25 expected, 26 observed, +1 delta** and every source
identity and evidence field.

The existing manual baseline fixture has actual 2, with predictions naive 3,
mean 1/2 and seasonal naive 2. Its independently calculated MAEs are 1, 3/2 and
0, biases 1, -3/2 and 0, and WAPEs 1/2, 3/4 and 0. The zero-demand control keeps
WAPE null. An explicit finding verifies exact integers above 2^53 and a -2
delta, including the quantity sentence. Float quantities are rejected.

Persisted weekly selection and holdout scores are checked against separate
manual rational expectations, then citations against selected database fields.
Historical proposals retain **12 pieces** for complete supply and **null** for
incomplete supply, inside citations only. Backtest citations retain exact
scores/origins and omit raw replay rows only after full report validation.
No forecast/backtest/planning execution is triggered by this harness.

The grader compares complete citation content and typed numeric leaves, not
counts alone. It checks selected IDs/source families, status/exit codes,
quantity statements, readiness blockers and safe Markdown. Independent negative
controls prove that wrong routes, dropped or fabricated citations, float
substitutions, wrong quantity sentences and order approvals fail grading.

Readiness covers missing, failed, unavailable, future and stale evidence,
including the exact 24-hour freshness boundary and one second beyond it.
Unsupported requests must refuse. Invalid checks, float pieces, wrong deltas,
duplicate JSON keys, inconsistent scores and missing UUIDs must exit 2 without
an answer. Missing data never becomes a zero, pass or current order quantity.

## Measured results

- Overall case pass: **40/45 (88.9%)**. A case passes only if every applicable
  check passes; six expected validation errors count as successful controls.
- Natural-language routing: **23/28 (82.1%)**, including six local allowlist
  phrases. Live model routing alone: **17/22 (77.3%)**.
- End-to-end evidence selection, numeric fidelity and citations: each
  **34/39 (87.2%)**. The five misroutes fail all three dimensions because they
  provide no requested evidence; they are not numeric hallucinations.
- Conditional on correct routing: each fidelity dimension is **34/34**.
  This includes valid absence/refusal responses; it is not 34 numeric answers.
- Readiness/refusal outcomes: **13/13**; persisted planning explanations:
  **6/6**; expected invalid-input/retrieval errors: **6/6**; explicit finding
  controls: **5/5**. No response proposes a current order.
- Model-path end-to-end latency: median **1,412.047 ms**, nearest-rank p95
  **2,682.743 ms**, maximum **3,329.103 ms** (22 samples).
- API latency: median **1,346.543 ms**, p95 **2,619.317 ms**, maximum
  **3,199.923 ms** (22 samples). This measures the HTTP request/read interval;
  end-to-end includes process startup, routing, retrieval, validation and output.
- All-case end-to-end latency: median **207.780 ms**, p95 **2,478.414 ms**
  (45 samples). The mixed local/model workload makes model-path latency more
  useful for interpreting interactive performance.
- Returned model: **gpt-6-luna** for all 22 calls. Provider-reported usage:
  **4,799 input + 319 output = 5,118 total tokens**, cached 0, reasoning 0.
  Every call returned all recorded counters; no estimated usage or dollar cost.
- Operational/planning-input source digests remained identical. Run history
  stayed **89 reliability runs / 110 planning runs**. No evidence was regenerated.

These are single measurements on synthetic inputs using Python 3.12.14,
Psycopg 3.3.6 and local PostgreSQL 17.6, not production accuracy, a model comparison,
or a repeated load test. The benchmark requests never send inventory evidence
to the model. Tokens follow the provider's [Responses API usage fields](https://developers.openai.com/api/reference/cli/resources/responses/methods/create).

## Observed gap and next work

Failures are **F02–F06**: selected duplicate evidence, a selected large-integer
mismatch, selected source rows, an absent selected finding and a Chinese finding
explanation. All five returned a completed model classification of `unsupported`,
not a service fallback. All other live questions routed correctly.

The classifier instructions say a finding ID must be supplied by the caller,
but the model receives only the question and cannot see the CLI's finding-ID
argument. This is a plausible cause of excessive refusal, not a proven causal
result. A future routing change should separate intent classification from
deterministic selector validation and be evaluated on fresh held-out paraphrases.
This benchmark preserves the observed failures rather than tuning the router
against its own evaluation questions. New forecasting models are outside scope.

## Reproduce

Use an existing populated synthetic acceptance database with the 180-day
planning demo and forecast tests already run. Do not rerun the full suite or
reload fixtures merely to measure Copilot. Set `TEST_DATABASE_URL` to the owner
and `DATABASE_URL` to `ii_runner` for that same database.

```sh
PYTHONPATH=src python -m unittest tests.test_copilot_benchmark tests.test_copilot_language tests.test_copilot -q
PYTHONPATH=src python -m scripts.copilot_benchmark --live --output /tmp/copilot-benchmark.json
```

`--live` uses the configured key (environment, then `--env-file`, default `.env`)
and authorizes up to 22 requests. No key is printed, stored in results or copied
to a worktree. Omitting `--live` evaluates offline behavior: non-allowlisted
questions refuse, so it does not establish live routing accuracy. Exit 1 means
one or more expected outcomes failed, including observed routing defects; it
does not erase measurements or turn them into a pass.

`--reuse-results PATH` can reuse completed measured cases only when language
mode/model, selected input hashes, source digest, history counts, Copilot code
hashes and case expectations match. It executes only newly added controls; use
a different output path to preserve the cache during interrupted execution.
Partial measurements are saved after each new case. Result metadata records
reused/new case counts and the earlier measurement window.

The CLI's opt-in `--measure-usage` adds `routing.telemetry` with attempted calls,
HTTP latency, returned response/model IDs, status and provider token counters.
Default output is unchanged. No-call paths have attempted calls 0 and null
provider counters; missing counters on attempted calls remain unknown. Summary
totals include only measured counters and separately report unknown calls.
