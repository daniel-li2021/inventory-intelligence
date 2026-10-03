# Inventory Intelligence

**Can this stock be trusted—and what should we replenish if it can?**

Inventory Intelligence is a Python/PostgreSQL portfolio project for finished
apparel measured in whole pieces. It reconciles source inventory before allowing
an advisory replenishment calculation, then explains the evidence behind it.
Missing, stale or contradictory inputs produce `not_assessable` and null
quantities. Operational inputs are never repaired and no orders are executed.

The core system, offline decision research and local **Decision Lab** are complete
within their synthetic scope. Real demand performance, calibrated service and
business savings remain unmeasured. [Current independent assessment](docs/READINESS_REVIEW.md).

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

Reliability checks exact ledger/snapshot balances at a shared business cutoff
and watermark. Planning requires eligible demand, trusted stock and complete
reservations/inbound. The Copilot explains saved results with exact quantities
and citations; its optional language model routes intent only. The offline
simulator evaluates a separate periodic ordering policy and does not simulate
execution of the planner's proposal.

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

## What the evidence shows

- **Engineering:** exact arithmetic, two knowledge clocks, append-only run
  history, restricted database roles, independent hand-calculated oracles, and
  fail-closed API/evidence boundaries. See [fresh review and acceptance](docs/READINESS_REVIEW.md).
- **Decision research:** 480 forecast/policy/split simulations across 60 cells.
  All eight selected lumpy-demand cells fail held-out service floors. Forecast
  accuracy alone does not establish inventory decision quality.
- **Intermittent research:** 5,544 candidate/split results across 84 cells,
  from 2,376 unique simulations. Four dual-reference passes represent one
  declining-demand path repeated across cost/delay regimes. There is no global
  winning model; 18 cells have no eligible selection.
- **Negative results matter:** stock can run out before any order can arrive,
  and historically calibrated safety stock can persist after demand collapses.
  Adding a more complex forecast does not necessarily solve either problem.

[Decision protocol/results](docs/DECISION_BENCHMARK.md),
[intermittent protocol/results](docs/INTERMITTENT_BENCHMARK.md), and
[ranked next investigations](docs/READINESS_NEXT_STEPS.md).
The [startup/accounting diagnostic](docs/FEASIBILITY_DIAGNOSTIC_RESULTS.md)
attributes eight of the delayed replay's 68 missed units to unavoidable startup;
60 occur later. Its cost disadvantage persists over a common 36-day window.
Existing holdouts are consumed; they are regression evidence, not fresh tuning
sets. Optional live Copilot routing has a bounded synthetic evaluation, separate
from deterministic evidence checks. [Routing evidence](docs/STAGE3_STABILIZATION.md).

The [long-term roadmap](docs/RESEARCH_ROADMAP.md) records 22 assigned or gated
directions. Its first [fresh warmup study](docs/FRESH_WARMUP_RESULTS.md) evaluates
720 arms with fully costed inventory carryover: warmup improves fill in 70/360
pairs, regresses it in 35/360, and lowers complete intervention cost in only two.
Empirical 90%/95% forecast targets still do not guarantee achieved inventory
service. Repeated controls and origins are not independent replications.

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
[planning demo](docs/PLANNING.md), [Copilot examples](docs/examples/copilot.md).

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
[review](docs/READINESS_REVIEW.md); a local pass is not remote CI evidence.
[Detailed validation and historical checkpoints](docs/VALIDATION.md).

Offline regression checks need neither database nor model API:

```sh
PYTHONPATH=src python -m unittest tests.test_decision tests.test_decision_benchmark tests.test_forecasting tests.test_intermittent tests.test_intermittent_benchmark -v
```

The full synthetic benchmark rerun commands are in their protocol documents;
retained valid outputs can be reused without regenerating experiments.

## Reading guide and boundaries

Start with [the current assessment](docs/READINESS_REVIEW.md) and
[the Lab](docs/DECISION_LAB.md). For implementation details:

- Reliability: [frozen contract](docs/CONTRACT_V1.md), [data](docs/DATA.md), [engine](docs/ENGINE.md).
- Forecast/planning: [contract](docs/CONTRACT_PLANNING_V1.md), [operations and oracles](docs/PLANNING.md).
- Copilot: [reliability interface](docs/CONTRACT_COPILOT_V1.md), [saved planning explanations](docs/CONTRACT_COPILOT_V2.md).
- Research: [decision contract](docs/CONTRACT_DECISION_V1.md), [intermittent contract](docs/CONTRACT_INTERMITTENT_V1.md), [public-sales proposal](docs/PUBLIC_SALES_PROTOCOL_V1.md).
- Development: [workflow](CONTRIBUTING.md), [checkpoint](docs/AUTOMATION_PROGRESS.md), [original stage handoffs](docs/PARALLEL_WORK.md).

All business examples are synthetic. Accepted orders, observed sales and
unconstrained demand are distinct targets. Public-data acquisition needs a
separate boundary decision; no real observations have been imported. Source
uploads, cloud deployment, scheduled operational jobs and order execution remain
outside this project. Never include company code, data, screenshots, credentials
or confidential schemas. Original material is [MIT licensed](LICENSE);
dependencies retain their own licenses.
