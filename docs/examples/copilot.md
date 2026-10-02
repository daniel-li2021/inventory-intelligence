# Copilot operator examples

Use complete Stage 1 JSON output, not the curated `combined.md` excerpt. Reuse
a previously saved synthetic report or select its explicit persisted UUID.
If saving the quickstart's existing combined check to `/tmp/reliability.json`,
its original checker exits 1 because of intentional data faults; that is expected.
The copilot explains that failed report and exits 0 when its answer succeeds.

```sh
PYTHONPATH=src python -m inventory_intelligence.copilot \
  --question 'What failed?' --report /tmp/reliability.json --format markdown
PYTHONPATH=src python -m inventory_intelligence.copilot \
  --intent finding --report /tmp/reliability.json --finding-id FINDING_ID
PYTHONPATH=src python -m inventory_intelligence.copilot \
  --intent reliability --run-id RUN_UUID
```

For the original combined jacket finding, the deterministic summary is
“Snapshot 26 minus ledger expectation 25 equals +1 pieces”, followed by its
exact `finding:<run UUID>:<finding ID>` reference. The citation retains SKU,
warehouse, all source row IDs, original evidence and the exact 25/26/+1 fields.
It suggests reviewing evidence; it does not assert why the mismatch occurred
or recommend a stock correction. Duplicate and transfer findings retain null
quantities. A report with missing rules or inconsistent deltas exits 2.

Readiness uses current UTC question time unless `--now` is supplied. For a
historical demonstration, supply a known question time deliberately; do not
backdate a live decision to hide stale evidence.

```sh
PYTHONPATH=src python -m inventory_intelligence.copilot \
  --question 'Can I make a replenishment decision?' \
  --report /tmp/reliability.json --now 2026-10-02T12:00:00+00:00
```

This exits 1 with `status=not_assessable` and `proposed_order_qty=null`.
A failed run blocks readiness globally; January inventory is stale in October.
Even fresh passing reliability evidence cannot replace the missing integrated
Stage 2 proposal interface. Missing coverage/data never becomes a zero order.

Reuse an existing Stage 2 benchmark JSON. If no saved benchmark exists, its small
stdlib demonstration produces one without API calls or a database:

```sh
PYTHONPATH=src python -m inventory_intelligence.forecasting > /tmp/benchmark.json
PYTHONPATH=src python -m inventory_intelligence.copilot \
  --question 'Compare the forecast baselines' --benchmark /tmp/benchmark.json
```

The weekly demo retains naive MAE `3`, mean MAE `12/7`, seasonal-naive MAE `0`,
and common origins `[14, 21, 28]`. WAPE values are ratios. All-zero actual demand
has null WAPE, not zero. These mathematical scores do not establish operational
demand eligibility or a production model choice.

## Optional natural-language routing

The user-authorized ignored `.env` supplies the API key; environment values take
precedence. No shell sourcing, secret copying or new dependency is needed.
Known phrases use the local allowlist; other questions use one Luna request.
No inventory evidence is sent. The output identifies the selected intent and
`routing.source=model|allowlist|offline|fallback`. Model routing can be mistaken;
use `--intent` for reproducible scripted questions.

```sh
PYTHONPATH=src python -m inventory_intelligence.copilot \
  --question 'Please summarize the failures in the saved inventory check.' \
  --report /tmp/reliability.json
# Explicit fallback: no API call, even if a key is present.
PYTHONPATH=src python -m inventory_intelligence.copilot \
  --question 'What failed?' --report /tmp/reliability.json --language-model offline
```

Questions requesting stock writes, order placement, SQL execution or policy
override have no execution path. Unknown/unsupported questions refuse with
exit 1. A service outage refuses an unknown question and reports a safe fallback
limitation. Malformed source evidence/configuration errors exit 2. Markdown
renders the complete answer in fenced JSON, keeping hostile source strings inert.
