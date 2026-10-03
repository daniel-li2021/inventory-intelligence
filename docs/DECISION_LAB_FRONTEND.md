# Decision Lab frontend

The Lab is a same-origin, dependency-free HTML/CSS/JavaScript interface in
`src/inventory_intelligence/lab_static`. It uses `GET /api/lab` for the baseline,
server-provided defaults and bounded controls, `POST /api/scenarios` for changed
assumptions, and `GET /api/evidence` for the immutable source archive. FastAPI
serves `/static/lab.css` and `/static/lab.js` alongside the root HTML page.

The interface exposes the trusted synthetic SKU/warehouse cutoff, scenario
controls and presets, exact baseline/scenario comparisons, forecasts, prefix
planning balances, scored physical inventory/backlog, separate runoff, synthetic
cost components, and the expandable nine-stage Decision Trace. JSON export
contains the displayed server response, including exact values, run identities
and parameters. Reset restores default inputs; Run explicitly evaluates them.

Business quantities, deltas, costs, decisions and risks come from the adapter.
The frontend does not calculate inventory, forecasts, recommendations or service
outcomes. Rational-to-number conversion is used only for chart coordinates and
percentage display; exact rational values remain in tables, evidence, exports
and metric titles. Signed planning balance and physical simulated stock are
separate views. The simulator's periodic policy is explicitly distinguished from
the planner's one-shot prefix proposal, and service threshold is labelled as a
comparison input rather than calibrated safety.

Incomplete scenario evidence preserves the clean baseline and displays blocked
outputs as not assessable. Undefined rate denominators remain undefined. Input
changes mark displayed results stale; requests disable scenario controls until
completion. Failed requests preserve the last successful results and expose a
keyboard-focusable error. Initial loading failure offers retry. Server messages
are rendered as text; no dynamic evidence is interpreted as HTML.

No external fonts, CDNs, chart libraries, frontend build, API keys or LLM calls
are needed. Semantic headings/forms, native integer bounds, visible focus,
live-region status, chart descriptions, exact-value tables, reduced motion and
responsive layouts support keyboard and small-screen use.

Validation: JavaScript syntax passes with the bundled Node runtime. Combined
API-backed browser checks verify demand and supplier-delay presets, blocked
evidence, zero-demand undefined fill, stale inputs, exact rounding trace and a
downloaded/parsed JSON export. Assets also pass from an installed wheel outside
the checkout. [Combined acceptance and screenshot](DECISION_LAB.md).
