# Stage 3 routing stabilization

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
