# Inventory Decision Lab

Local synthetic replay UI over reliability, forecasts, advisory replenishment,
a separate periodic simulator and saved evidence. This guide owns the delivered
architecture/API/UX. [EVIDENCE](EVIDENCE.md) binds original acceptance and source views.

## Run locally

Python 3.12, from the repository root, with the build tools in README installed:

```sh
python -m pip install --no-build-isolation '.[lab]'
python -m uvicorn inventory_intelligence.lab_api:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. The wheel includes frontend assets and synthetic
evidence. No database, external fonts/CDNs, model key or LLM request is needed.
API routes are GET `/api/lab`, POST `/api/scenarios`, GET `/api/evidence`.
Controls accept bounded integers only; unknown fields are rejected. The app has
no source-upload or order-execution endpoint.

## Interpreting results

- **Trusted state** means the synthetic inventory passed Stage 1 at the recorded
  replay cutoff and was revalidated by the saved planning run. It is historical
  evidence, not a current physical count. UUIDs refer to actual persisted runs.
- **Forecast** uses the existing mean baseline and exact rational arithmetic.
  Demand scenarios transform copies of training and declared future observations
  with `ceil(quantity × percent / 100)` whole pieces. The trace retains original
  observations and the transformation; accepted-order records are never changed.
- **Recommendation** comes from unchanged `replenishment.project`:
  prefix-stock-v1 protects the greatest post-arrival safety deficit. Positive need
  is ceiled, raised to MOQ and rounded to a pack. Zero need stays zero.
- **Simulated service/cost** comes from unchanged `decision.simulate` and its
  periodic inventory-position policy. Orders are reevaluated at each review;
  this is not an execution simulation of the prefix-stock-v1 proposal. The first
  simulator order can differ. Explicit prior reservations are disjoint from new
  demand, confirmed inbound is known initially, and pending inbound is excluded.
- **Supplier delay** is hidden from the simulator's order decisions. Changing
  it alone does not rewrite the planner's lead time. Change declared lead time
  separately to inspect its effect on prefix protection and forecast horizon.
- **Risk** describes this deterministic path: forecast shortages and surplus
  above declared safety. It is not a probability. Service target is a threshold
  for the measured immediate-fill ratio, not a calibrated guarantee or automatic
  safety calculation. Zero-demand/service denominators remain null.
- **Costs** are synthetic finite-window penalties, with declared rates for
  holding pieces/day, backlog pieces/day and each positive order setup. Scored
  days, fixed runoff, total components and terminal obligations remain visible.
  These amounts do not establish profit or real business savings.
  The UI displays both accounting-window lengths: each replay's runoff is
  `lead_days + supplier_delay_days + review_days`, so combined cost deltas can
  include different durations. Compare scored costs separately before drawing
  conclusions about a policy change.

The Decision Trace links reliability run → inventory input row IDs → eligible
demand and forecast → supply assumptions → policy → raw requirement → rounding
→ recommendation → simulated outcome. Lab run hashes identify copied scenario
inputs and deterministic calculations separately from persisted run UUIDs.
Derived forecast, raw requirement, rounding, proposal and simulation trace nodes
cite their lab calculation hash. Saved planning UUIDs are labelled as input-run
references so scenario values cannot appear to be stored baseline outputs.
The incomplete-supply control suppresses the scenario proposal, projection,
simulation, risk and costs; it retains the clean baseline for comparison.

## Adapter and API boundary

`lab.evaluate(overrides=None, evidence=None)` returns `contract_version`,
`metadata`, `defaults`, `controls`, `baseline`, `scenario`, `comparison`, and
`warnings`. Metadata retains synthetic key, cutoff, input UUIDs and archive digest;
trace/calculation hashes identify derived values separately. Each side retains
status/reasons, parameters, forecast, plan, simulation, costs, risk and trace.
`load_evidence()` validates the packaged archive. No runtime DB, LLM or source write
is used. The exporter alone loads a fresh synthetic database and saved real runs.

POST `/api/scenarios` accepts strict bounded integers with these defaults:

| Field | Default | Inclusive bounds |
|---|---:|---|
| demand_percent | 100 | 0–200 |
| lead_days | 2 | 1–14 |
| review_days | 3 | 1–7 |
| supplier_delay_days | 0 | 0–14 |
| inbound_day | 1 | 0–27 |
| reservation_qty | 3 | 0–100 |
| safety_qty | 2 | 0–100 |
| pack_size | 6 | 1–24 |
| moq | 10 | 1–100 |
| service_target_percent | 90 | 0–100 |

`evidence_case` is `clean` (default) or `incomplete_supply`. Unknown fields,
booleans, strings, floats, nulls and out-of-range values yield 422. Invalid/missing
archive evidence yields HTTP 503; direct adapter evaluation suppresses both sides.
`/api/lab/evidence` aliases `/api/evidence`. Injected archive/override inputs are
copied; the clean baseline stays immutable when a scenario is blocked.

The packaged frontend renders backend business values and exact rational tables;
number conversion is for chart/display coordinates only. Input edits mark results
stale; failed requests retain the last successful response and expose a focusable
error/retry. Server evidence is rendered as text. No external font/CDN/chart library,
frontend build or client-side business calculation is needed. Independent timing,
cost, conservation and rounding controls remain in the [validation evidence](RESULTS.md#lab-arithmetic-and-service).

## Regenerate the bundled evidence

Use a **fresh disposable** PostgreSQL database initialized with both project
schemas. Existing source batches are never overwritten. The exporter uses the
existing synthetic loader and the actual checker/forecast/planner, rather than
hand-authoring successful run reports. It exports the complete saved clean and
incomplete-supply results, plus a declared constant 28-day synthetic future trace.

```sh
export FIXTURE_DATABASE_URL=postgresql://ii_owner:ii_owner_local@localhost:55432/inventory_intelligence
export DATABASE_URL=postgresql://ii_runner:ii_runner_local@localhost:55432/inventory_intelligence
PYTHONPATH=src python scripts/export_lab_evidence.py --output /tmp/lab_evidence.json
```

Inspect the export before replacing the bundled file; raw source identifiers,
business/observation timestamps and run identities are retained. The archive
SHA-256 catches accidental changes, and the existing Copilot planning validator
recomputes saved recommendation arithmetic. It is a local integrity check, not a
cryptographic attestation of live business data. The local app exposes only this
packaged synthetic replay, with no arbitrary external evidence import.
Semantic checks also require consistent inventory reconciliation across all
retained keys, complete coverage/counts, temporal cutoffs, unique source identities,
supply manifests and saved report links. Recomputing hashes cannot approve a
contradictory archive. These checks cover this bounded zero-movement fixture;
they do not replace Stage 1 SQL validation for arbitrary operational data.

FastAPI's [static-file serving](https://fastapi.tiangolo.com/tutorial/static-files/)
and [TestClient](https://fastapi.tiangolo.com/tutorial/testing/) support the thin
same-origin application and API boundary checks.

## Validation

Independent prefix/periodic quantities, conservation, malformed-input boundaries,
installed-wheel outcomes and targeted accessibility measurements are consolidated
in [RESULTS](RESULTS.md#lab-arithmetic-and-service). Source/environment and combined
acceptance remain in [EVIDENCE](EVIDENCE.md#acceptance-history), with original
receipts/screenshots unchanged. These are bounded synthetic/local observations;
public service, full accessibility and production/business outcomes remain unverified.

## Product capability and experience boundary

The authorized product journey is Overview → Explore → Investigate → Compare →
Decide, with History linked from the selected key. The original replay remains at
`/lab`; its v1 APIs and saved archive retain their meanings. The product adapter
is additive, with a frozen [catalog and independent controls](product-contract.md).

The targeted capability review maps existing evidence as follows:

- **Inventory and apparel exploration (O06/O18):** operational styles/SKUs/warehouses,
  snapshot/opening/coverage rows and saved R001–R005 results support dimensions and
  recorded key-level stock. A complete global reliability pass is still required
  by the planner; local clean stock cannot waive it. The adapter adds bounded
  catalog/matrix/filter views, without relaxing the original fixed-Lab validator.
- **Discovery (O23):** saved prefix projections support replenishment exposure and
  pre-arrival shortage. A complete five-day no-order projection can support an
  excess opportunity above the declared safety threshold. Missing demand, supply
  or reconciliation becomes an Evidence Problem with null derived quantities.
  These business rules are separate from R001–R005; reliability can pass while an
  opportunity exists. Supplier lateness, lifecycle/age, valuation and feasible
  transfer insights lack the necessary sources and remain unavailable.
- **Explanation and comparison (O17/O24):** retained rule inputs, exact rounding and
  calculation/source references support deterministic explanations. Prefix balance
  with/without a proposal supports a projection comparison. Existing periodic
  simulation supports hidden-delay what-ifs with its own policy and accounting
  windows; it does not measure execution of the prefix proposal. Earlier lead time
  is an assumption. Arbitrary order quantities, transfers, purchase execution and
  commercial savings require later contracts.
- **History (O25/O21 minimum):** separately saved cutoff/known-at reports support
  key/rule observations and compatible exact deltas. Missing evidence is unknown;
  changed policy/model/horizon must explain noncomparability. Immutable reports
  retain their source bindings; later evidence cannot replace historical inputs.

Each screen needs loading, unavailable/retry and explicit replay-context states.
Explore has empty/filter/reset states. Investigate distinguishes recorded stock,
applicability and missing evidence. Compare keeps saved baseline, edited controls,
stale result and last successful result distinct. Decide renders advisory/blocked
status and required review, with no execution control. History distinguishes new,
persistent, worsening, improved and unknown observations. Saved local views and
shareable URLs bind filter schema and archive identity; they do not promise live
refresh or confer access.

Developer checks and automated browser observations remain separate from independent
human comprehension and accessibility conformance. Public TLS, hosting/cost, larger
engineering capacity and real/private workflows keep their existing gates. This
bounded product assignment does not reopen consumed model studies or planner
execution research. See the remaining [roadmap](ROADMAP.md#delivery-sequence-and-acceptance-gates).
