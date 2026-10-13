# Inventory Decision Workbench frontend

The product at `/` uses React/TypeScript/Vite because the accepted workbench has
six routes sharing cutoff, exact-key selection, filters and scenario/history state.
The existing Python Scenario Lab remains at `/lab`. No frontend tooling is needed
to start the packaged Python demo; the wheel includes the built assets.

## Development and reproducible build

Use Node 22 or newer (Vite 6 supports the current 22.11 runtime). From `frontend/`:

```sh
npm ci --ignore-scripts
npm test
npm run build
```

Vite is pinned to the maintained Node-compatible 6.x line; dependencies are exact
and their transitive versions/integrities are frozen in `package-lock.json`.
`dependency-licenses.json` records package/license metadata from that lockfile.
The build writes flat hashed local assets to `product_static/`; there are no CDN,
font, model or external data requests. `npm run dev` proxies the API to localhost
8765. To use another serving port, change the developer proxy only.

## Contracts and budgets

API schema is `inventory-product-v1`, with exact decimal strings and rational
`{numerator, denominator}` values; the UI never computes business quantities.
All source calculations run in the saved-evidence Python adapter. Filters and
pagination are server-owned. The apparel matrix is bounded to the selected
100-key envelope and drills into one exact SKU/location.

Before migration: JS <=250 KiB gzip, CSS <=40 KiB gzip, initial data <=200 KiB.
The build verifies asset budgets and writes `bundle-receipt.json`; the API/browser
acceptance checks initial network data separately. Evidence records are fetched
only after selecting their source section. Expensive full reports stay on the
server. Overview also offers a lazy independent duplicate-inventory control: its
original failed reliability run and null proposal stay separate from normal keys. Browser tests and comprehension review are separate acceptance evidence;
a developer screenshot is not accessibility conformance or a user study.

Hash URLs preserve selected key, cutoff, filters, matrix/list, page, scenario
assumptions and archive/contract bindings. Saved views are browser-local (at most
ten); Share view binds a URL to the original archive and contract. A mismatch
blocks application until the user explicitly chooses the current archive. New
requests cancel old ones; loading/failure retains the last good result with stale
context and blocks decisions. Scenario drafts remain stale until recalculated.
Exports identify their source context and whether the displayed comparison was
stale. No orders or source input rows are written.

The interface uses semantic forms/tables, text states alongside color, keyboard
focus, wrapped mobile navigation, native disclosure, forced-color styles and
bounded horizontal scroll areas. Unsupported lifecycle/transfer/execution actions
have explicit reasons; periodic simulations and prefix advisory projections are
separately labelled.

For distribution, `python scripts/build_product_wheel.py --output-dir /tmp/new-wheels`
from the repository root builds in a clean temporary source tree and verifies exact
asset/archive bytes. This avoids obsolete hashed assets retained by incremental
setuptools builds. [Packaging reproduction](../docs/EVIDENCE.md#product-journey).

Execution adds separate March research clocks, actual proposals/paid trajectories,
paired stress costs and an optional durable local receipt sandbox. Its APIs use
`/api/execution`; default packaged mode has journal writes disabled. Both default
and sandbox browser journeys cover execution export, blocked history and 320px
layout. Synthetic receipts never execute real orders or modify source stock.

Insight Discovery V2 appears in Overview, Investigate and History. Observed facts,
model hypotheses, missing causes and supported next steps retain exact source refs.
Overview caps displayed findings at eight with complete counts; selected-key detail
and the read-only discovery API expose the complete bounded set. Compare adds one
saved-review FIFO execution contrast against no action/pack-MOQ alternatives, with
33 common paid days and a 0–3-day declared delay. It is separate from the periodic
scenario controls; source mismatch/errors retain stale last-good results.
[Controlled local replay walkthrough](../docs/SYNTHETIC_REPLAY.md).
