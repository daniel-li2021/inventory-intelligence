# Inventory Decision Lab: first vertical slice

Assigned implementation, 2026-10-03. Synthetic-only local replay; no orders or
source edits. Preserve every existing core module and frozen contract.

## Architecture and reuse

- Export one immutable tee-m / Harbor synthetic replay using
  `synthetic.planning_demo.load_inputs`, `reliability.run_checks`,
  `planning_runs.run_forecast`, and `replenishment.run_plan`. Include the complete
  saved clean and incomplete-supply planning evidence. Verify it on load with
  `copilot_planning.answer_planning`; retain run UUIDs, row IDs and cutoffs.
- Small adapter calls `forecasting.forecast`, `replenishment.project`, and
  `decision.simulate` unchanged. Fractions serialize exactly as rational strings.
  Content hashes identify lab calculations, separately from persisted run UUIDs.
- Optional FastAPI/Uvicorn extra serves same-origin JSON and packaged plain
  HTML/CSS/JavaScript. No Node build, database, API key or network needed at run
  time. A separate explicit exporter uses a fresh disposable PostgreSQL database.
- The replay is trusted at its recorded cutoff, never current live inventory.
  No uploads, arbitrary database selectors, writes, LLM calculation or execution.

## UX

One synthetic key, trust/cutoff strip, scenario controls, baseline/scenario metric
comparison, forecast/prefix projection and simulated stock/backlog charts with
accessible tables, synthetic holding/backlog/setup costs, and expandable Decision
Trace. Each trace node exposes exact structured evidence and its identifiers:
reliability → inventory → demand/forecast → supply → policy → raw requirement →
ceil/MOQ/pack → recommendation → simulation. Export the whole comparison JSON.
An incomplete-supply control demonstrates suppression of unsupported outputs.

Show prefix-stock-v1 recommendation and periodic inventory-position simulation
as distinct policies. The simulation reevaluates orders; it does not execute the
prefix proposal. Delay is hidden from simulated ordering, and cannot silently
change the planner's declared lead time. Show pre-arrival shortages explicitly.
Excess means deterministic projected surplus above declared safety, not a
probability. Service target is a comparison threshold, not calibrated safety.

## Thin API handoff

`inventory_intelligence.lab.evaluate(overrides=None, evidence=None)` returns an
exact-JSON dict: `contract_version`, `metadata`, `defaults`, `controls`,
`baseline`, `scenario`, `comparison`, `warnings`. Each side includes `status`,
`reasons`, `parameters`, `forecast`, `plan`, `simulation`, `costs`, `risk`,
`trace`, and `run_id`. Metadata includes the synthetic key, recorded cutoff,
source run identities and archive digest. Trace nodes have `stage`, `label`,
`explanation`, `references`, `data`. `load_evidence()` returns packaged archive.

GET `/api/lab` returns the default paired evaluation. POST `/api/scenarios`
accepts only bounded integer fields below and `evidence_case` (`clean` or
`incomplete_supply`), all defaulted. GET `/api/evidence` returns the archive.
Invalid fields/types/ranges yield 422; incomplete evidence returns
`not_assessable` with null recommendation/projection/simulation/costs/risk.

| Field | Default | Inclusive bounds |
| --- | ---: | --- |
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

Demand multiplier applies to a counterfactual copy of both training and the
declared 28-day future demand trace: `ceil(q * percent / 100)` whole pieces.
Original accepted-order evidence is immutable. Confirmed inbound quantity stays
5; reservation is disjoint prior demand due day zero. Pending inbound is excluded.
Cost rates remain declared synthetic (holding, backlog, setup) = (1, 10, 2).
The delay vector covers all review slots including runoff; expose all assumptions.
Baseline always uses clean replay/default parameters, including when the scenario
demonstrates incomplete supply. All deltas use backend exact arithmetic; null
denominators remain null. No automatic model or policy selection.

## Ownership and acceptance

- Backend agent: `src/inventory_intelligence/lab.py`, `lab_api.py`, exporter,
  backend notes. No shared core edits.
- Frontend agent: `src/inventory_intelligence/lab_static/**`, frontend notes.
- Independent validation agent: `tests/test_lab.py`, `tests/test_lab_api.py`,
  lab validation notes. Hand-calculate control oracles independently.
- Integration owner: this plan, optional dependencies/package assets, generated
  evidence, README, combined acceptance, review and one integration PR.

Each agent commits on its isolated branch without pushing or opening a PR.
Owner combines commits, validates exact baseline and changed/blocked cases,
API boundaries, package installation and a real browser scenario/trace/export.
New dependencies and portfolio milestone use one integration PR, then validated
integration under standing authorization. Preserve unrelated active branches.
