# Decision Lab backend adapter

The first slice replays one immutable synthetic `planning-demo:tee-m` /
`planning-demo:harbor` key at its recorded cutoff. `lab.evaluate` reuses
`forecasting.forecast`, `replenishment.project`, and `decision.simulate` without
changing any core module. Business arithmetic remains integer/Fraction arithmetic;
rational estimates, ratios, costs and deltas serialize as exact strings.

## Evidence and replay

`scripts/export_lab_evidence.py` loads `synthetic.planning_demo.load_inputs` into
an explicitly fresh disposable PostgreSQL database and calls the real reliability,
forecast, clean planning and incomplete-supply planning APIs. The exporter refuses
existing fixture identities through the loader's primary keys. It retains the
complete saved reports, raw source rows, clocks, source identities and UUIDs in
`lab_evidence.json`, plus a declared 28-day constant synthetic future demand trace.
Future demand is a declared what-if assumption, not observed demand evidence.

The archive SHA-256 covers canonical JSON excluding its own `digest` field.
`load_evidence` checks bounded size, exact types, the digest, saved input digests,
existing Copilot planning validators, original forecast arithmetic and source/key/
cutoff consistency. Archive validation verifies a historical replay. The digest
is content integrity, not a signature or independent certification of live stock.
No database, network, LLM or source writes are used while serving scenarios.

`evaluate(overrides=None, evidence=None)` returns the frozen `decision-lab-v1`
response documented in `DECISION_LAB_PLAN.md`. Baseline always uses clean defaults.
Invalid/missing archives suppress every business output on both sides. The
incomplete-supply scenario suppresses its forecast, proposal, projection,
simulation, costs and risk while retaining evidence-gate trace information.

## Scenario semantics

- Demand percent changes copies of both historical training and future synthetic
  demand using whole-piece `ceil(source * percent / 100)`. Original accepted-order
  records remain in the trace; each copied training day cites its source rows.
- Prefix-stock-v1 planning covers declared lead plus review days. Its proposal
  arrives after the full lead time and cannot repair earlier shortages.
- The 28-day decision simulation uses the distinct periodic inventory-position
  policy and completed historical demand only. It reevaluates orders and is not
  execution of the prefix recommendation. Its first review target, position,
  raw requirement and rounded order are exposed beside the prefix proposal.
- Supplier delay affects each simulated order's arrival. It is hidden from
  ordering and does not change the planner's declared lead time. The full delay
  vector includes runoff review slots.
- Only the existing five confirmed inbound pieces count; pending inbound stays
  excluded. Inbound timing may change. Reservation quantity is separate prior
  demand due at day zero.
- Service target compares the simulation's immediate fill rate. Zero future
  demand has an undefined fill denominator and produces a null threshold result.
  Cycle service remains separately visible with its complete-cycle denominator.
  The target does not calibrate safety quantity.
- Stockout/excess are deterministic projection exposures. Excess is positive
  projected balance above declared safety, never a probability or optimized cost.
  Synthetic holding/backlog/setup rates are fixed at 1/10/2. Scored and runoff
  holding/backlog/setup costs and exact baseline/scenario deltas are separate.

## Local API

With the project's `lab` extra installed:

```sh
python -m uvicorn inventory_intelligence.lab_api:app --host 127.0.0.1 --port 8000
```

`GET /api/lab` evaluates defaults; `POST /api/scenarios` accepts the bounded strict
integer fields in the plan and `evidence_case`. Unknown fields, booleans, strings,
floats and out-of-range values yield 422. `GET /api/evidence` (alias
`/api/lab/evidence`) returns the validated immutable archive. Unavailable or
invalid evidence returns 503. Packaged same-origin HTML/CSS/JS is served at `/`.
`create_app(evidence=None)` supports isolated offline tests and defensively copies
injected evidence. Inputs supplied to `evaluate` are also copied before use.

Verification during implementation used the exporter against a fresh local
PostgreSQL database and the actual saved archive: baseline raw requirement 10,
proposal 12, scored holding 219/setup 20, runoff holding 88, total cost 327.
Demand 150% proposes 24; 50% proposes zero. Zero demand leaves fill-target status
null. Extreme bounded lead/review/delay/reservation values conserve all pieces;
strict API booleans return 422. Independent acceptance tests own the final oracles.
