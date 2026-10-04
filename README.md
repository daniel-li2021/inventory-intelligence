# Inventory Intelligence

**Can this stock be trusted—and what should we replenish if it can?**

A Python/PostgreSQL portfolio system for finished apparel measured in whole
pieces: reconcile inventory, compute evidence-gated advisory replenishment, and
explain saved results. Missing, stale or contradictory evidence yields
`not_assessable` and null quantities. Inputs are never repaired and no orders execute.

[Current project state](docs/STATE.md) · [Engineering plan](docs/PLAN.md) ·
[Knowledge and evidence](docs/README.md) · [Development workflow](CONTRIBUTING.md)

```mermaid
flowchart LR
  S[Source records + completeness] --> R[Inventory reliability]
  D[Origin-known accepted orders] --> F[Baseline forecasts]
  R --> P[Evidence-gated planning]
  F --> P
  P --> C[Read-only evidence copilot]
  R --> L[Decision Lab: saved synthetic replay]
  P --> L
  B[Separate offline decision simulator] --> L
```

Reliability compares ledger/snapshot quantities at aligned cutoffs and watermarks.
Planning requires trusted stock, eligible demand and complete reservations/inbound.
Copilot reports exact saved evidence; optional language routing chooses intent only.
The separate periodic simulator reevaluates orders rather than executing the
planner's prefix proposal. [Durable design decisions](docs/DECISIONS.md).

The operational demo is synthetic. Separate approved [UCI observed-sales research](docs/RESULTS.md#public-observed-sales)
keeps raw/reconstructable observations local and publishes aggregates. Sales do not
establish unconstrained demand, historical availability or real business benefit.
[Measured results](docs/RESULTS.md) include routing failures, negative safety-policy
outcomes and service/cost tradeoffs. [Evidence](docs/EVIDENCE.md) binds their original
source views; [knowledge](docs/KB.md) retains lessons and conditional questions.
The documentation index routes current interfaces and operations; STATE owns status.

## Try the Decision Lab

The browser demo needs Python 3.12, with no database or model API key. From the
repository root:

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install pip==25.2 setuptools==80.9.0 wheel==0.45.1 typing-extensions==4.16.0
python -m pip install --no-build-isolation '.[lab]'
python -m uvicorn inventory_intelligence.lab_api:app --host 127.0.0.1 --port 8000
```

Open [the local Lab](http://127.0.0.1:8000). Start with demand +25%, hidden supplier
delay, or incomplete supply. Compare the clean baseline, exact scenario outputs,
stock/backlog trajectories and Decision Trace; download the comparison JSON.
The bundled evidence comes from actual persisted runs against synthetic inputs
at a recorded historical cutoff.

![Synthetic Decision Lab baseline versus demand scenario](docs/review/decision-lab.jpg)

The baseline advises 12 pieces. Demand +25% advises 18, with simulated cost
351 versus 327. Hidden supplier delay of three days leaves the planner unchanged
but reduces simulated immediate fill to `11/28`, with 17 shortage days and cost
1171. Incomplete supply suppresses the scenario recommendation and outcome
metrics; zero-demand fill remains undefined. These are deterministic synthetic
cases, not commercial savings or service guarantees.
[Lab semantics, API and operating instructions](docs/DECISION_LAB.md).
[Hosted-demo readiness package](deploy/lab/README.md) prepares a bounded anonymous
entry point, pinned container/proxy templates and release acceptance. No public
service has been deployed; container and public-domain checks remain pending.

Keyboard users can run the presets, inspect focusable evidence tables with arrow
keys and use the skip link. [Local accessibility review and limits](docs/RESULTS.md#browser-and-accessibility-results)
records focus, contrast and narrow-screen validation.

## Run the PostgreSQL core

Use the Python environment above and Docker with Compose. From the repository
root, start a new demo volume:

```sh
export COMPOSE_PROJECT_NAME=ii_stage1_demo
export POSTGRES_PORT=55432
docker compose up -d --wait
export FIXTURE_DATABASE_URL=postgresql://ii_owner:ii_owner_local@localhost:55432/inventory_intelligence
export DATABASE_URL=postgresql://ii_runner:ii_runner_local@localhost:55432/inventory_intelligence
python -m synthetic.generate combined
python -m inventory_intelligence \
  --ledger-batch combined:ledger --snapshot-batch combined:snapshot \
  --as-of 2026-01-02T00:00:00+00:00 \
  --evaluated-at 2026-01-02T02:00:00+00:00 \
  --code-version stage1-demo --format markdown
```

**Exit 1 is expected:** this deliberately dirty fixture contains a duplicate,
invalid transfer and jacket mismatch (expected 25, observed 26, delta +1).
Load `clean` and substitute `clean:ledger` / `clean:snapshot` for exit 0.
Exit 2 means configuration/execution failed. Fixture loaders refuse overwrite;
each check preserves prior history. Credentials above are fictional local setup.
[Verified core example](docs/examples/combined.md),
[planning demo](docs/OPERATIONS.md#planning), [Copilot examples](docs/examples/copilot.md).

## Independent acceptance

Use a separate **fresh disposable** database; named fixtures are loaded once.
Never point the suite at a business database or populated demo volume.

```sh
export COMPOSE_PROJECT_NAME=ii_stage1_acceptance
export POSTGRES_PORT=55433
docker compose up -d --wait
export TEST_DATABASE_URL=postgresql://ii_owner:ii_owner_local@localhost:55433/inventory_intelligence
export DATABASE_URL=postgresql://ii_runner:ii_runner_local@localhost:55433/inventory_intelligence
python -m unittest discover -s tests -v
```

CI runs the same suite with pinned PostgreSQL 17.9 / Python 3.12.12. Local
acceptance versions and actual results are recorded separately in the
[acceptance catalog](docs/EVIDENCE.md#acceptance-history). The separate
[main CI acceptance](https://github.com/daniel-li2021/inventory-intelligence/actions/runs/37164884160)
passes 240 tests at `9d7c55f`; test-suite duration is not a scale benchmark.
[Validation commands and independent oracles](docs/VALIDATION.md).

Offline regression checks need neither database nor model API:

```sh
PYTHONPATH=src python -m unittest tests.test_decision tests.test_decision_benchmark tests.test_forecasting tests.test_intermittent tests.test_intermittent_benchmark -v
```

Reuse retained results. Historical reproduction uses complete original Git snapshots
in [EVIDENCE](docs/EVIDENCE.md); new experiments require a fresh assigned protocol/output.

## Boundaries

Frozen operational contracts remain separate from offline research. Source uploads,
real inventory imports, source repair and order execution are outside the demo.
Public hosting has separate runtime/release/cost gates. Never include company code,
data, screenshots, credentials or confidential schemas. Original material is
[MIT licensed](LICENSE); dependencies and approved public data retain their licenses.
