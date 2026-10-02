# Stage 3: Inventory Copilot

Implementation handoff: the user assigned Stage 3 on 2026-10-02 while a separate
agent reviews Stage 1 and completes Stage 2. This plan owns `copilot*.py`, `test_copilot*.py`,
`CONTRACT_COPILOT_V1.md` and this document. The README receives only a new link
and usage section. No Stage 1/2 source, SQL, contract, test or workflow changes.

## Outcome

Explain existing inventory evidence in a reproducible, read-only assistant.
Answer “What failed?”, “Why is this finding present?”, “How did these benchmark
models compare?” and “Can I make a replenishment decision?”. Every reported
business fact has a reference to a selected run/finding or benchmark field.
The assistant does not rerun reconciliation, forecast new demand, fix stock,
create orders, invent missing inputs or interpret source text as instructions.

Stage 1 supplies contract-v1 reports and persisted runs. Stage 2 currently
supplies only the exact baseline benchmark on the shared baseline. The other
agent is authoring a separate planning contract and full implementation in
`codex/stage2-eligibility`; its evolving outputs have not been integrated here.
Parallel implementation can
therefore complete the evidence copilot now, with an explicit dependency gate
for replenishment. It cannot honestly supply order recommendations yet.

## Design and sequence

1. Freeze the separate [copilot contract](CONTRACT_COPILOT_V1.md). Do not amend
   Stage 1 v1 or guess the unfinished planning interface.
2. Add a small stdlib module accepting existing JSON reports and benchmarks.
   Validate their shape, identities, status consistency and exact quantities.
   Reject malformed/contradictory evidence rather than normalize it to a pass.
3. Expose four explicit intents. Reliability summarizes the original checks;
   finding explanation retains the full evidence and source rows; benchmark
   explanation retains rational scores, horizon and rolling origins; readiness
   evaluates the selected run at question time and reports missing planning
   prerequisites with a null order quantity.
4. Read a persisted run by explicit UUID through the existing `ii_runner` role
   in a Repeatable Read, READ ONLY transaction. Fetch only its run/check/finding
   records with bound SQL parameters. No “latest” heuristic, operational query,
   schema change, source write or appended reliability run.
5. Deliver JSON and Markdown CLI output, accepting saved reports or a database
   UUID. Keep the Stage 1 CLI intact. Offline use needs no database credentials,
   provider, service or new dependency. A small allowlist of question phrases
   maps to explicit intents. Optional Luna routing handles arbitrary phrasing
   through a strict intent schema; it never generates the business answer.
6. Validate with independent manual reports and scores, malformed inputs,
   unavailable evidence, freshness boundaries, exact large integers, refusal,
   hostile source strings, CLI exits and a real persisted-run round trip.
   Reuse existing synthetic outputs and local runtimes/database when available;
   run no crawler or full Stage 1 acceptance pipeline. The user authorized
   reuse of the existing `.env` and bounded live Luna smoke checks.

## Safety and explanation rules

- A historic pass describes the original covered inventory and cutoff; it is
  not a current inventory balance, complete sales history or planning approval.
- Decision freshness uses question time minus inventory cutoff, with exactly
  24 hours allowed by default. Future cutoff/evaluation or old data blocks it.
- A non-pass run blocks readiness globally. Filtering a finding cannot convert
  the overall run into a pass. V1 does not publish per-bucket readiness.
- Display source evidence verbatim as JSON data. Reason-specific next steps are
  review suggestions, not diagnoses of theft, loss, a software bug or causation.
- WAPE is a ratio; a zero-demand denominator remains null. Benchmarks describe
  the supplied mathematical experiment; there is no production model winner.
- No source SKU text, reason, evidence field or question can add a tool, execute
  SQL, request a URL or change a policy. Unsupported and write requests refuse.
- Saved JSON is caller-supplied evidence, not proof of persisted provenance.
  Explicit database loading is the authoritative retrieval path in this demo.
- Files and database results are bounded. Oversized evidence fails explicitly;
  do not truncate findings and present a partial explanation as complete.

## Acceptance and delivery

The delivered v1 combines an offline evidence core and optional language routing.
Tests must compare exact evidence IDs/rows/quantities and decisions, not counts
alone. Repeated explicit intents over unchanged inputs produce identical JSON and do
not mutate inputs or database history. A missing finding returns unavailable;
an invalid report exits 2; a blocked or refused answer exits 1. A correctly
explained failed reliability run exits 0 because the explanation succeeded.

Before commit, run the focused copilot suite, an offline CLI demonstration,
existing forecasting regression tests and whitespace checks. If using a local
database, prove retrieval matches an existing report and appends no history;
never reset another agent's database. Commit and push a focused task branch,
verify its remote ref, and leave merge and Stage 1/2 review to their owners.

## Follow-on handoffs

**Planning adapter:** after Stage 2 freezes and validates its planning contract,
consume its immutable forecast/proposal records, retain all input/cutoff/model
IDs, and explain its computed quantities without doing a second calculation.
Acceptance must include eligible, blocked and stale decisions and exact pack
rounding evidence. This is a dependency, not unfinished speculative scaffolding.

**Language routing — delivered:** the user authorized the existing ignored
`.env` (lowercase key spelling supported), with `gpt-6-luna` as default and
`gpt-6-sol` only on explicit selection. Use the
[Responses API structured output format](https://developers.openai.com/api/docs/guides/structured-outputs)
supported by [Luna](https://developers.openai.com/api/docs/models/gpt-6-luna).
Send only the question, ask for one allowlisted intent, validate the output and
render the deterministic answer. Do not ask the LLM to phrase factual answers,
select source identities, execute SQL or calculate readiness. Limit question,
response, output tokens and time; no retries or automatic expensive-model fallback.
On API failure, disclose offline fallback and refuse unknown questions. Known
phrases and explicit intents use no API. Stored source strings never enter the
model context. Local mocks cover malformed output, extra fields, refusals,
timeouts, credentials, redirects and attempts to change policy.

No vector store, multi-agent loop, web UI, cloud deployment or scheduler is
needed for the current evidence set. Full product-setup permission does not
create a need for these components. The pending Stage 2 adapter is the explicitly
permitted temporary fallback, not a fabricated order recommendation.

## Verified checkpoint — 2026-10-02

Python 3.12.14 / Psycopg 3.3.6 / PostgreSQL 17.6: 29 focused tests passed,
zero failures/errors/skips (13 evidence/CLI, 8 language, 3 real database and
5 existing forecast regression checks). PostgreSQL ran in a separate temporary
cluster with a Unix socket; no other agent's database was reset. Database tests
assert the original 109/107/-2 finding, complete persisted-report equality,
Repeatable Read + READ ONLY, unchanged source quantity and no appended history.
An actual future-cutoff metadata failure remains explainable rather than being
mistaken for a malformed report.

Three live synthetic `gpt-6-luna` questions routed correctly to reliability,
readiness and unsupported stock modification. This is a smoke test, not proof
of universal language accuracy; deterministic safeguards do not depend on it.
Offline demonstrations reused existing combined/clean reports and benchmark
JSON. See [operator examples](examples/copilot.md).

```sh
PYTHONPATH=src python -m unittest tests.test_copilot tests.test_copilot_language -v
# With an isolated bootstrapped acceptance DB and its two existing URLs:
PYTHONPATH=src python -m unittest tests.test_copilot_db tests.test_forecasting -v
```

## Three-stage integration review — 2026-10-02

The Stage 2 interface is now integrated on the review branch. The additive
[copilot-2 contract](CONTRACT_COPILOT_V2.md) reads explicit persisted forecasting,
benchmark and proposal runs. It retains exact evidence and explains blocked
plans without approving a current order. The legacy readiness route remains
fail closed. See [repeated validation and final benchmarks](THREE_STAGE_REVIEW.md).
