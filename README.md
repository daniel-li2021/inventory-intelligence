# Inventory Intelligence

**Find inventory risk, trace the evidence, and compare replenishment decisions.**

An inventory decision workbench for apparel: identify stock at risk, surplus and
unreliable data across **50 SKUs at two locations**, then investigate source records
and compare purchase or transfer options. Built with **Python, PostgreSQL, FastAPI
and React/TypeScript**.

**[Open the live demo](https://inventory-intelligence-boss.onrender.com)** ·
[Six engineering case studies](docs/PLATFORM_GUIDE.md) ·
[Measured results](docs/RESULTS.md) · [Technical docs](docs/README.md)

Saved results: **[368/368 PostgreSQL tests passed](docs/review/full-platform-acceptance-v1/receipt.json)** ·
**[10.251s → 0.856s local reconciliation median](docs/RESULTS.md#engineering-continuation)**.

*Read-only demo with synthetic data; no real orders execute. The free host may
need about a minute to wake up. [Public smoke-check receipt](docs/review/render-public-smoke-v1.json).*

[![Inventory Intelligence Overview: 100 item locations with risk, opportunity and evidence problems, plus an attention queue linking to source investigation](docs/screenshots/ux-refinement/after-1280-overview.jpg)](https://inventory-intelligence-boss.onrender.com)

## Verified engineering results

- **10.251s → 0.856s median reconciliation time** on 1,000 item/location keys and
  100,000 movements, with identical report semantics and source hashes. Twelve
  measured calls per variant in a local paired benchmark; the x86/two-date reference
  gate remains open. [Method and limits](docs/RESULTS.md#engineering-continuation).
- **368/368 PostgreSQL regressions passed**, followed by a separate **126/126 focused
  audit** on PostgreSQL 17.9 ARM64 / Python 3.12.14. These are saved October 14
  acceptance runs, not additive coverage totals.
  [Full receipt](docs/review/full-platform-acceptance-v1/receipt.json) ·
  [Audit receipt](docs/review/final-functional-audit-v1/receipt.json).
- **Installed Python wheel runs the demo without Node, a database or a model key.**
  Packaged assets, evidence integrity and disabled default writes passed installed
  package checks. [Package evidence](docs/review/final-functional-audit-v1/receipt.json).

These results establish bounded local/synthetic behavior, not production capacity,
real business savings or independent human/accessibility acceptance.

## Architecture and product flow

```mermaid
flowchart LR
  S[Synthetic source records] --> K[Python + PostgreSQL: reconcile, forecast, plan]
  K --> E[Versioned evidence archives]
  E --> W[FastAPI + React workbench]
  M[Separate periodic simulator] --> W
```

The core preserves source identities, business/knowledge clocks and exact whole-piece
quantities. Missing, stale or contradictory evidence blocks planning with
`not_assessable` and null quantities. Copilot explains saved evidence; optional
language routing selects intent without calculating business quantities. The
simulator evaluates periodic policies separately from the planner's advisory proposal.
The hosted workbench reads packaged evidence and computes transient comparisons;
new core runs use PostgreSQL. [Contracts](docs/CONTRACTS.md) ·
[Design decisions](docs/DECISIONS.md).

**Overview → Explore → Investigate → Compare → Decide** connects evidence to action,
with saved views and three-cutoff history. The platform also supports
[controlled local synthetic intake/replay](docs/SYNTHETIC_REPLAY.md),
[feasible supplier choices](docs/SUPPLIER_FEASIBILITY.md),
[donor-safe transfers and receipt/ETA feedback](docs/TRANSFERS.md), and
[forecast-to-decision evaluation](docs/FORECAST_DECISION.md).
Explicit local configuration enables synthetic SQLite journals; the hosted demo
remains read-only. [Platform walkthrough and local journal command](docs/PLATFORM_GUIDE.md#run-the-working-platform).

All operational inputs are synthetic. Separate approved
[UCI observed-sales research](docs/RESULTS.md#public-observed-sales) keeps
raw/reconstructable observations local and publishes attributed aggregates.
Observed sales do not establish unconstrained demand or historical availability.
Evaluation retains losing policies and no winner; the JIT candidate was not adopted.
[Evidence and provenance](docs/EVIDENCE.md) · [Engineering limits](docs/ENGINEERING_SUPPORT.md) ·
[Knowledge and data rights](docs/KB.md) · [Remaining validation](docs/ROADMAP.md).

[Current project state](docs/STATE.md) · [Engineering plan](docs/PLAN.md) ·
[Development workflow](CONTRIBUTING.md)

## Try the Decision Workbench

The browser demo needs Python 3.12, with no database or model API key. From the
repository root:

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install pip==25.2 setuptools==80.9.0 wheel==0.45.1 typing-extensions==4.16.0
python -m pip install --no-build-isolation '.[lab]'
python -m uvicorn inventory_intelligence.lab_api:app --host 127.0.0.1 --port 8000
```

Open [the local workbench](http://127.0.0.1:8000). Node is needed only for frontend
changes; the Python package includes built React assets, licenses and evidence.
No source upload, purchase execution or model call is available.

Three-minute walkthrough:

1. Select **2026-01-05**, open **At-risk stock**, and investigate **II-00 / Harbor**.
   Recorded stock is 10 pieces; its advisory prefix proposal is 12. Inspect the
   origin-known accepted orders, confirmed supply, pack rounding and exact source
   references.
2. Open **Compare**, change demand to 125%, and run the comparison: the proposal
   becomes 18. A three-day hidden supplier delay alone keeps the proposal at 12;
   service/cost describe a separate periodic policy. No-order versus proposal
   balances are projections. Shared scored costs and unequal runoff remain separate.
3. Open **History** for the same key: stock 10 → 4 → 22 and proposal 12 → 18 → 0;
   its risk worsens, then improves. Revisit **2026-01-19 / II-02 / Upland** to see
   incomplete reservations block a decision while retaining recorded stock.
4. Explore **Excess stock** for a passing-reliability opportunity; switch to the
   apparel matrix, save a local view, share its archive-bound URL or export exact
   evidence. Missing/blocked quantities remain distinct from recorded zero.

The original [single-item Scenario Lab](http://127.0.0.1:8000/lab) and its v1 APIs
remain available:

![Synthetic Decision Lab baseline versus demand scenario](docs/review/decision-lab.jpg)

The baseline advises 12 pieces. Demand +25% advises 18, with simulated cost
351 versus 327. Hidden supplier delay of three days leaves the planner unchanged
but reduces simulated immediate fill to `11/28`, with 17 shortage days and cost
1171. Incomplete supply suppresses the scenario recommendation and outcome
metrics; zero-demand fill remains undefined. These are deterministic synthetic
cases, not commercial savings or service guarantees.
[Lab semantics, API and operating instructions](docs/DECISION_LAB.md).
[Hosted-demo readiness package](deploy/lab/README.md) prepares a bounded anonymous
entry point, pinned container/proxy templates and release acceptance. The October 15 [public smoke check](docs/review/render-public-smoke-v1.json)
verifies trusted HTTPS and a brief read-only journey. The [Render Free Blueprint and click-through guide](deploy/render/README.md)
prepare the complete read-only synthetic demo with GitHub CI-gated automatic deploys.
ARM64 container controls and one continuous HTTP campaign
have local evidence; remaining stability, reference, human and public-domain gates
are pending. [Current measured limits](docs/RESULTS.md#engineering-continuation).

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

### Actual execution and durable synthetic receipts

The **Execution** page separately shows the actual planner's seven controls and
12 paired stress traces, with paid costs, source reports, blocked reviews and the
retained cold-oracle arithmetic erratum. It preserves the existing advisory
100-key journey and distinct periodic simulation.

For the local synthetic receipt sandbox, after installing `.[lab]`:

```sh
python scripts/run_local_demo.py --port 8020 --journal output/local-demo.sqlite
```

Open `http://127.0.0.1:8020/#/execution`. Admit 12 → receive 5 → notify ETA → receive
7; choose historical dates and export the durable journal. Repeating identical
events is harmless. This writes synthetic journal events only. The default hosted
package stays read-only. No Node/database/model key is needed at demo runtime.
[Actual evidence, reproduction and limits](docs/PLANNER_EXECUTION.md).
