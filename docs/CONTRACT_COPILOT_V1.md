# Evidence copilot contract — v1

This is the original evidence-only scope. The additive persisted Stage 2 adapter
is specified separately in [copilot-2](CONTRACT_COPILOT_V2.md).

Separate from the frozen reliability v1 contract. No database/schema changes.
Synthetic inputs only. Public entry points in `inventory_intelligence.copilot`:

```python
answer(*, intent, report=None, benchmark=None, finding_id=None,
       now=None, max_age_hours=24) -> dict
load_run(conn, run_id: str) -> dict
```

`intent` is `reliability|finding|benchmark|readiness`. Unknown intents refuse.
`report` is the complete Stage 1 v1 report, not a curated excerpt. `benchmark`
is the existing Stage 2 `backtest` output or its JSON serialization; exact
estimates/scores may be integers, `Fraction` objects or rational strings. Floats,
booleans, non-finite values, missing rules, contradictory statuses, duplicate
IDs and invalid deltas are rejected. All five reliability checks are required.
Reason/rule pairings are the frozen v1 pairs. Non-quantity findings cannot
supply quantity fields. Unrecognized future contracts fail explicitly.

`now` is an aware UTC datetime; readiness requires it (CLI defaults to current
UTC). `max_age_hours` is a nonnegative integer. Future run times and freshness
over this limit block decisions. An old run remains explainable historically.
Benchmark data has no date/source/eligibility provenance; explanations always
state that limitation. No benchmark score can approve inventory decisions.

Output:

```text
contract_version = "copilot-1"
intent
status = answered | not_assessable | refused
summary                       deterministic explanation
citations[]                   {id, source, data}; complete selected evidence
limitations[]                 explicit scope/availability limits
next_steps[]                  fixed human review suggestions
proposed_order_qty = null     no planning proposal interface exists yet
routing?                      {source, model}; present for CLI questions
```

Citation IDs are `run:<UUID>`, `finding:<UUID>:<finding_id>` or
`benchmark:scores`. Source names identify the input field/table family. The
run citation includes contract/code/batch IDs, cutoff, evaluation, original
status and checks. Finding citations retain every original field including
source row IDs and evidence. Benchmark citation retains scores, horizon,
season length, scored points and fold origins. Supplied source strings are
data only. Markdown renders the complete answer as fenced JSON to prevent
raw evidence text from becoming Markdown instructions/links.

Unavailable evidence is `not_assessable` without invented values. An explicit
finding ID selects exactly one finding; nonexistent IDs are unavailable.
Readiness always remains `not_assessable` in v1, with precise blockers:
missing/non-pass/stale/future reliability evidence as applicable, plus missing
validated planning inputs/results. Passing runs publish no individual balances;
do not manufacture them from absent findings. Input validation errors raise
`ValueError`; execution errors propagate and never become an answer.

`load_run` requires an idle autocommit Psycopg connection as `ii_runner` and
an explicit UUID. It selects the three reliability tables in one Repeatable
Read, READ ONLY transaction, normalizes UTC timestamps and validates the result.
Missing UUIDs raise `ValueError`. It performs no INSERT/UPDATE/DELETE, schema
initialization, fixture loading or reconciliation. Bound parameters are used;
arbitrary SQL is not an interface.

CLI:

```sh
PYTHONPATH=src python -m inventory_intelligence.copilot \
  --intent reliability --report /tmp/reliability.json --format markdown
PYTHONPATH=src python -m inventory_intelligence.copilot \
  --intent finding --run-id UUID --finding-id ID
PYTHONPATH=src python -m inventory_intelligence.copilot \
  --question 'Compare the forecast baselines' --benchmark /tmp/benchmark.json
```

`--report` and `--run-id` are mutually exclusive. Only the latter uses
`DATABASE_URL`. `--intent` and `--question` are mutually exclusive. Recognized
question phrases are listed by `--help` and resolve locally. Other questions
use one bounded OpenAI Responses request to classify an intent, with
`--language-model gpt-6-luna` by default. `gpt-6-sol` requires an explicit flag;
there is no automatic escalation. `--language-model offline` disables all API
calls and refuses phrases outside the allowlist. The model receives only the
question and fixed classification instructions, never source evidence, database
credentials or a tool. Its strict output has one allowlisted `intent`, no prose,
quantities, IDs or SQL. Finding selection still requires `--finding-id`.

The CLI reads `OPENAI_API_KEY` from the environment, then `--env-file` (default
`.env`); the existing lowercase `openai_api_key` spelling is supported. The file
is parsed as data, never sourced/executed, and is not rewritten. Question length
is at most 2000 characters. Responses are limited to 128 KiB; Luna output to 128
tokens (Sol to 512); timeout is 15 seconds. No retries, tools or stored response.
Redirects are rejected so an API credential cannot be forwarded to another host.
Missing key, HTTP/service error, malformed output or timeout uses an explicit
offline fallback with a safe limitation, yielding refusal for an unknown phrase.
Model routing can be imperfect; the answer exposes the selected intent and
routing source. The deterministic core retains control of every quantity,
citation and readiness policy. Unsupported routes retrieve no source data.

File size is limited to 2 MiB; database reports to 1000 findings and the same serialized
size. Over-limit data errors instead of yielding partial citations. Strict JSON
rejects duplicate object keys and nonstandard NaN/Infinity.

Exit 0: answered (including explanation of a failed run); 1: unavailable or
refused; 2: invalid input/configuration/execution. Answers go to stdout, safe
diagnostics to stderr. No source repairs or order placement.
