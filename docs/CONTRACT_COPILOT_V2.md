# Persisted planning explanations — copilot-2

This additive Stage 3 interface explains an explicit persisted `planning-v1` run.
The existing [copilot-1](CONTRACT_COPILOT_V1.md) reliability, finding, baseline and
readiness interfaces retain their scope. No Stage 1 table or report changes.

```python
from inventory_intelligence.copilot_planning import load_planning_run, answer_planning
load_planning_run(conn, run_id: str) -> dict
answer_planning(report: dict) -> dict
```

Loading requires an idle autocommit `ii_runner` connection and an explicit UUID.
It reads one `planning.runs` record in Repeatable Read, READ ONLY, using bound
parameters. It performs no source queries, reconciliation, forecasting, INSERT,
UPDATE or DELETE. Missing, malformed, inconsistent or oversized evidence errors;
results are never silently truncated. Complete replay benchmarks can exceed the
legacy 2 MiB report limit, so this separate loader permits at most 16 MiB.

Only `planning-v1`, `baselines-v1`, and forecast/backtest/replenishment kinds are
recognized. Validate exact values, envelope/result statuses, baseline scores on
shared folds, model selection, and selection truth knowledge before holdout.
Proposal validation checks its supplied projection/rounding arithmetic using the
existing exact planner; this is consistency validation, not a new stock decision.
No float quantities or fabricated zeros. Unsupported future contracts error.

Output retains the copilot shape with `contract_version="copilot-2"`,
`intent="planning"`, `status="answered"`, and `proposed_order_qty=null`.
A citation `planning:<UUID>` names `planning.runs` and keeps run/version/digest,
context, source identities and result fields. Forecast/proposal citations retain
the complete record; backtest citations select exact selection/holdout scores,
chosen method and all candidate origin/status fields, explicitly excluding raw
replay rows from presentation after validating the complete record.

A blocked historical plan is successfully explainable: its original status,
reasons and null quantity remain in the citation. An assessable historical
proposal retains its original quantity **inside the citation only**. Neither
answer approves a current order. Source freshness/completeness must be established
again at a new planning cutoff before action. No source evidence enters an LLM.
The new intent is explicit; natural-language routing is unchanged.

```sh
PYTHONPATH=src python -m inventory_intelligence.copilot \
  --intent planning --planning-run-id UUID --language-model offline
```

`--planning-run-id`, `--run-id` and `--report` are mutually exclusive. Planning
requires `--intent planning` plus `--planning-run-id` and `DATABASE_URL`.
Exit 0 means the explanation succeeded, even for a stored blocked plan; exit 2
means invalid input/retrieval/evidence. The ordinary readiness intent still
blocks without current validated planning inputs. Source strings remain data;
Markdown uses the existing fenced JSON renderer.
