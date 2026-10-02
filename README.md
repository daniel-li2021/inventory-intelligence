# Inventory Intelligence

A public portfolio project that reconciles synthetic apparel inventory in PostgreSQL. The intended progression is **Inventory Reliability → Forecasting & Planning → Inventory Copilot**. Milestone 1 supplies source fixtures, a read-only checker, persisted findings, and independent database acceptance tests.

Inventory is finished garments in whole pieces at `(sku_id, warehouse_id)` grain. Missing or ambiguous inputs suppress unsupported quantity conclusions. The checker writes only to the `reliability` schema; it never repairs operational inventory.

## Quickstart

Requires Python 3.12 and Docker with Compose. From the repository root:

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install pip==25.2 setuptools==80.9.0 wheel==0.45.1 typing-extensions==4.16.0
python -m pip install --no-build-isolation .

export COMPOSE_PROJECT_NAME=ii_stage1_demo
export POSTGRES_PORT=55432
docker compose up -d --wait
export FIXTURE_DATABASE_URL=postgresql://ii_owner:ii_owner_local@localhost:55432/inventory_intelligence
export DATABASE_URL=postgresql://ii_runner:ii_runner_local@localhost:55432/inventory_intelligence
python -m synthetic.generate combined
```

The credentials are fictional local configuration. Compose initializes a **new** database volume from `sql/schema.sql`. The fixture loader refuses to overwrite an existing scenario. The owner connection loads fixtures; the restricted `ii_runner` connection checks them.

```sh
python -m inventory_intelligence \
  --ledger-batch combined:ledger --snapshot-batch combined:snapshot \
  --as-of 2026-01-02T00:00:00+00:00 \
  --evaluated-at 2026-01-02T02:00:00+00:00 \
  --code-version stage1-demo --format markdown
```

**Exit 1 is expected:** the combined fixture deliberately contains a duplicate movement, an invalid transfer, and a jacket quantity mismatch (expected 25, observed 26, delta +1). See the [verified example](docs/examples/combined.md). Exit 0 means all checks pass; exit 2 means configuration/execution failed. To run a clean control, load `clean` and substitute `clean:ledger` / `clean:snapshot` in the same command; expect exit 0. Every check appends a new run and preserves earlier history.

## Independent acceptance

Use a separate, fresh Compose project/volume; the named scenarios are loaded once and checked repeatedly inside the suite. Do not point acceptance tests at a business database or a populated demo volume.

```sh
export COMPOSE_PROJECT_NAME=ii_stage1_acceptance
export POSTGRES_PORT=55433
docker compose up -d --wait
export TEST_DATABASE_URL=postgresql://ii_owner:ii_owner_local@localhost:55433/inventory_intelligence
export DATABASE_URL=postgresql://ii_runner:ii_runner_local@localhost:55433/inventory_intelligence
python -m unittest discover -s tests -v
```

The standard-library suite checks manually calculated balances, exact fault evidence, time/watermark boundaries, incomplete inputs, immutable run history, CLI exits, and PostgreSQL permissions. Missing dependencies or database inputs fail the suite. GitHub CI runs the same suite against PostgreSQL 17.9 and retains the existing hygiene checks; intentionally dirty data passes only when assertions match the expected defects. [Validation details and commands](docs/VALIDATION.md).

## Contract and implementation

- [Frozen milestone 1 contract](docs/CONTRACT_V1.md)
- [Data bootstrap and scenarios](docs/DATA.md)
- [Checker, CLI, and SQL behavior](docs/ENGINE.md)
- [Path ownership and handoffs](docs/PARALLEL_WORK.md)
- [Stage 1 plan](docs/STAGE1_PLAN.md)
- [Stage 1 completion review](docs/STAGE1_REVIEW.md)
- [Stage 2 plan and initial baseline benchmark](docs/STAGE2_PLAN.md)
- [Research and reading guide](docs/RESEARCH.md)
- [Development workflow](CONTRIBUTING.md) and [shared agent instructions](AGENTS.md)

Stage 2 has started with a stdlib forecast/backtest benchmark, independent of
operational data. Run `PYTHONPATH=src python -m inventory_intelligence.forecasting`
for its synthetic demonstration. The [planning contract](docs/CONTRACT_PLANNING_V1.md) and demand eligibility adapter
now distinguish complete zeros from gaps and replay revisions as known at origins.
Origin-aware forecasts and 7/14/28-day evaluations now append versioned PostgreSQL
results with a separate final holdout. Replenishment is pending; Stage 2 is not complete.
Existing databases can add the isolated schemas once with owner-executed
`psql "$TEST_DATABASE_URL" -v ON_ERROR_STOP=1 -f sql/planning_schema.sql`.
Fresh Compose and test bootstrap install both schemas.

All business examples are synthetic. Never include company code, data, screenshots, credentials, or confidential schemas. Uploads/forms, scheduled jobs, deployment, and dashboards are outside the delivered milestone.

Original project material is available under the [MIT license](LICENSE). Dependencies retain their own licenses.
