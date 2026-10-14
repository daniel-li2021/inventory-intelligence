# Inventory Decision Intelligence: local platform and case studies

The platform connects trustworthy source admission, proactive insights, evidence
investigation, feasible comparisons, synthetic commitments/transfers and subsequent
planner feedback. Every business outcome below is simulated on synthetic inputs.
No real purchase, warehouse dispatch, monetary savings or production readiness is
claimed. Existing kernels, original source archives and consumed studies are retained.

## Run the working platform

Install the project with `.[lab]` using the [project setup](../README.md), then run:

```sh
python scripts/run_local_demo.py --port 8040 --catalog docs/review/generalization-v1/generalization-two-site-v1.json.gz --journal output/my-platform-demo.sqlite
```

Open `http://127.0.0.1:8040/`. The local server binds loopback and explicitly enables
synthetic journal writes. Use a new journal filename for a new experiment; repeat
events are idempotent and there is no destructive reset. To serve the packaged
read-only original catalog instead:

```sh
python -m uvicorn inventory_intelligence.lab_hosted:app --host 127.0.0.1 --port 8041
```

Both interfaces run without Node, PostgreSQL or a model key after package installation.
Source ingestion, actual new planner studies and owner supply publication require a
separate disposable PostgreSQL database. SQLite journals and source/results are
separate: a UI receipt never silently changes an inventory snapshot.

## Six connected engineering case studies

### 1. A new dataset arrives

Problem: a fixed archive cannot establish generalization or source recovery.
Architecture: explicit local synthetic JSON → immutable source registry → restricted
actual reconciliation/forecast/planner runs → validated content-addressed catalog.
Two frozen independent designs change identities, styles, dimensions, policies,
cutoffs and DST clock context. They cover six keys at two/one locations and three/
two cutoffs respectively. Thirty exact key/cutoff cells, eighteen rule triggers and
sixty-five reports pass their hand-independent oracles. Version conflict, late
transaction failure, restricted-role denial, retry, historical fresh rerun and failed
publication preserve old sources/results/last-good bytes.

[Contract and reproduction](SYNTHETIC_REPLAY.md) ·
[protocol](examples/generalization-protocol-v1.json) ·
[actual receipt](review/generalization-v1/receipt.json).
The six-key designs demonstrate changed-input correctness, not maximum 50×2×12
performance, unseen detection accuracy or source-owner authenticity.

### 2. Changed demand/supply becomes explainable risk

Choose Overview → May 11 → coast SKU0/site0 → Investigate. Inspect demand change,
known supply/risk history, contributing stock/forecast/obligation/inbound factors,
model hypotheses, unknown causes and original references. Deterministic priority
orders risk, pre-arrival shortage days and proposal pieces; it is not a probability
or weighted business-value score. May 18 retains persistent risk. Missing training
and incomplete supply remain explicit unknowns rather than resolved alerts.

Open Review a source-bound finding. Record a synthetic investigation note; resolution
never hides the facts or clears a gate. Changed finding evidence requires a new exact
binding. [Rules and review contract](SYNTHETIC_REPLAY.md).

### 3. Feasible replenishment alternatives

Select May 4, coast SKU0/site0 → Compare. Supplier terms explicitly declare weekday
ordering, 17:00 cutoff, daily receiving and twelve pieces of dated capacity. Compare
saved six pieces, no action and twelve pieces over thirty-three paid days. Saved
six costs 2900 recipient units and promises May 5; reducing capacity to five withholds
both purchase outcomes while no action remains inspectable. Editing assumptions
marks retained results stale and disables admission until recalculation.

The [supplier controls](SUPPLIER_FEASIBILITY.md) independently establish calendar,
cutoff, capacity, exact partial receipts, full costs and knowledge clocks. They retain
a counterexample where later arrival lowers holding cost without reducing service.
Terms and future deliveries are declared synthetic scenarios, not supplier observations.

### 4. Donor-safe transfer competes with purchasing

Use the same May 4 item/location → donor site1, transfer twelve, transit one day →
Compare transfer before purchase. Full declared donor demand leaves fifty-one safe
pieces; the short-prefix signal alone does not authorize dispatch. Network no-action/
purchase/transfer costs are 6763/5154/3533; recipient immediate service is 3/28,
9/28 and15/28; donor remains28/28. A costly transport reverses the choice to
purchase5154 versus transfer5529. Every arm retains exact conservation and paid
stock, backlog, transport and purchase components.

Reserve → Dispatch May 4 → Receive five May 5 → Receive seven May 6. Inspect the
historical reservation/in-transit/receipt totals. Reserve allocates transfer pieces
only; a residual purchase needs separate supplier admission. [Transfer guide](TRANSFERS.md)
· [both saved outcomes](review/transfer-comparisons-v1.json).
No stochastic donor guarantee, global optimum or real transport is claimed.

### 5. New commitment/receipt/ETA evidence changes actual plans

The supplier and transfer journals preserve identities, partial quantities and the
then-known ETA. Owner publication creates a new complete supply batch; independent
new counts remain separate source evidence. Actual PostgreSQL transfer feedback:
proposal6→0 with confirmed twelve inbound; partial five leaves seven; independently
observed stock six would propose four; overdue remaining inbound blocks; a known
revised ETA restores an assessable zero. Historical proposal six is unchanged.

`tests.test_transfer_feedback` executes this with the real restricted planner in its
own disposable database. Existing [supplier feedback](PLANNER_EXECUTION.md) independently
preserves the original12→0 control. Neither journal is an operational exactly-once
executor or cross-database atomic handoff.

### 6. Unsafe evidence blocks without corrupting history

Choose coast SKU1/site1 with missing demand. Comparison has null outcomes and no
transfer reservation; review notes cannot repair it. Original duplicate-count
controls still block all planning despite superficially valid stock. Rehashed source
contradictions, future knowledge, fractional pieces, overreceipt and changed natural
identities reject. Last-good catalogs/journal states remain available; stale UI results
retain their explicit status. [Validation](VALIDATION.md), [source recovery](SYNTHETIC_REPLAY.md)
and [transfer negative controls](TRANSFERS.md).

## Evaluation and product design

Evaluation shows sixteen fresh independent paths, forty-eight actual loops and144
restricted reviews. Accuracy-selected alternatives pass only2/8 downstream decision
gates;39 blocked reviews, losses, ties and undefined zero-demand service remain.
Point baselines have no predictive intervals, so calibration is unavailable. Existing
intermittent/calibration/supply/recovery research is retained, not retuned. No new
model family or policy promotion is justified. [Full fresh study](FORECAST_DECISION.md).

The owner's selected compact light direction adapts FinRAG Meridian's structured
numeric comparison and Folio's readable evidence inspection. It retains React/Vite,
semantic navigation, original values and exact exports. Main comparisons show cost,
service, constraints and next action first; detailed daily/source evidence is a named
progressive disclosure. Narrow views stack controls and scroll tables; selected
original evidence remains inspectable. No other project's data, business logic,
assets or frontend framework were copied.

Developer browser controls cover constraints/staleness, admissions, partial lifecycle,
source-bound review, exact exports, evaluation and1280/320px layout. These checks are
separate from human comprehension or WCAG conformance. [Browser receipt](review/platform-browser-v1.json).
[Engineering support](ENGINEERING_SUPPORT.md) retains the JIT no-adoption result,
bounded evidence inspection, upgrades and recovery. [RESULTS](RESULTS.md) owns final
acceptance counts; [EVIDENCE](EVIDENCE.md) owns historical/source audit boundaries.

## Valuable work beyond this local master scope

Obtain independent human/accessibility task acceptance and exact reference runtime/
hardware/sustained serving evidence before broader claims. Reconcile new donor source
bases explicitly before repeated network execution; freeze fresh multi-review/
uncertainty studies before expanding allocation. Operational producer identity,
authenticated multi-user isolation and real supplier/transport adapters need explicit
data rights and action contracts. Lifecycle/aging/margin decisions need inputs that
currently do not exist. Advanced optimizers, new forecast families, services and
public hosting need measured unmet value; none follows automatically from this demo.
