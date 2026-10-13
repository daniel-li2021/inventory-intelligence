# Product replay contract and frozen independent controls

Frozen 2026-10-13 before adapter implementation. Scope: synthetic only, read-only,
100 keys (50 SKUs × Harbor/Upland), three UTC cutoffs 2026-01-05/12/19.
First acceptance uses the first four SKUs × two locations (eight keys). Each cutoff
has independent immutable inventory/demand/supply batches and actual saved
reliability, mean forecast and prefix-stock-v1 planning runs. Source dimensions
are real `styles`/`skus`/`warehouses` mappings: 10 styles, five sizes per style,
alternating Ink/Clay colors; no inferred stock or real commercial evidence.

Independent arithmetic: 28 complete days of four accepted pieces/day; mean 4;
lead 2, review 3, safety 2, pack 6, MOQ 10; three reservations due day 0, five
confirmed inbound due day 1, pending 100 excluded. Stock 10 yields balances
3,4,0,-4,-8; raw need 10; order 12. Stock 4 yields -3,-2,-6,-10,-14; raw need 16;
order 18 and pre-arrival shortage days 0,1. Stock 22 yields 15,16,12,8,4; order 0.
Stock 40 yields 33,34,30,26,22; order 0, terminal surplus above safety 20.
Zero-demand control with stock 0, no reservations or inbound yields order 0,
undefined service denominator; missing evidence is never zero.

First eight keys in SKU-major/location-minor order:
0 stock 10→4→22: risk initial unknown→worsening→improved (risk resolved);
1 stock 40→10→10: opportunity initially, risk new→persistent;
2 stock 40 throughout: opportunity persistent;
3 zero demand/stock/supply quantities throughout: no business alert;
4 stock 10 throughout: risk persistent;
5 stock 10 throughout, final incomplete reservations: history unknown and
all recommendation/comparison quantities suppressed at final cutoff;
6 stock 40 throughout, first missing demand day: unknown→new opportunity;
7 stock 10 throughout, only pending inbound: order 18 (raw need 15).
Keys 8–99 repeat these control patterns by key index modulo eight.
An isolated duplicate snapshot archive produces a genuine nonpassing global
reliability run and blocks every key; it is excluded from normal cutoffs.

History compares identical key, rules version, mean/prefix policy and 28-day
training/5-day projection windows. Initial comparison is unknown; any missing
coverage is unknown. Same category/exposure is persistent, increased exposure is
worsening, lower/disappeared exposure improved; newly appearing category is new.
Stock snapshots are independently synthetic counts at each cutoff, not a physical
movement narrative. Future rows/revisions may be retained as source evidence but
never included in earlier origin-known forecasts or decisions.

## JSON/API contract

Functions: `load_catalog`, `overview(catalog,cutoff)`,
`explore(catalog,cutoff,filters,page=1,page_size=20,sort='priority')`,
`detail(catalog,cutoff,sku_id,warehouse_id)`, `history(catalog,sku_id,warehouse_id)`,
`scenario(catalog,cutoff,sku_id,warehouse_id,overrides)`.
Selectors require existing exact ISO cutoff and keys. Filters: style_id, color,
size, warehouse_id, category (risk/opportunity/evidence/none), status, search.
Sort: priority, sku, stock; page size 1–100; pagination counts are JSON integers.
Piece quantities are decimal strings. Exact calculated ratios are objects
`{numerator:'11',denominator:'28'}`. No floats. Missing values are JSON null.

Overview includes `contract_version`, `archive_digest`, `synthetic`, `cutoff`,
`cutoffs`, `summary` counts, `highlights` item cards and `dimensions`.
Explore includes `items`, `total`, `page`, `page_size`, `pages`, `dimensions` and
`matrix` cells, each carrying explicit assessable/blocked status.
Item cards: `id` stable key ID, sku_id, warehouse_id, sku_code, style_id, style,
color, size, location, category, status, title, explanation, on_hand,
proposed_order_qty, forecast_daily, exposure, history_state, reasons, references.
Detail adds `evidence` (saved reports/source rows), `trace`, `capabilities`.
History returns `points` cutoff/card pairs plus exact compatible deltas.
Scenario returns `baseline`, `scenario`, `comparison`, `parameters`, `controls`,
`capabilities`, `archive_digest`; each side has status, reasons, plan, simulation,
risk, costs, forecast, trace, run_id. Controls follow Lab BOUNDS; selected-key
saved defaults replace the single-SKU Lab defaults. Simulation is the distinct
periodic policy, not the actual prefix proposal's executed outcome. Transfer,
expedite, markdown, purchase execution and commercial savings remain unsupported.

Archive format: content-addressed normalized pool of immutable actual report
objects with per-object digests and per-cutoff report bindings. Reconstruction
reproduces original reports and input digests. Whole archive integrity is checked
with strict size/count/clock/semantic validation; hashes are integrity checks, not
producer authentication. Selected claim validation replays deterministic kernels.
