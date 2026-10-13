# Product replay contract and frozen independent controls

Frozen 2026-10-13 before adapter implementation. Scope: synthetic only, read-only,
100 keys (50 SKUs × Harbor/Upland), three business-date cutoffs 2026-01-05/12/19.
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
training/5-day projection windows. Initial comparison is unknown; current missing coverage is unknown. An
insight first visible after previous missing coverage is new, with unavailable
quantitative comparability (it does not establish that the previous problem resolved). Same category/exposure is persistent, increased exposure is
worsening, lower/disappeared exposure improved; newly appearing category is new.
Opportunity threshold is terminal surplus of at least 20 pieces above safety.
Business dates use the existing America/Los_Angeles calendar; origin-known clocks
are its midnight converted to UTC (08:00 UTC at these dates).
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

## Delivered bounded replay and validation

Product cards retain trusted recorded stock even when demand or supply blocks a
proposal (`inventory_status` is separate from applicability). All derived proposal,
forecast and exposure values remain null when blocked. Overview selects up to
three highest-priority risks, two surplus opportunities and three evidence blockers;
Explore retains the complete deterministic category/exposure/key ordering.

Insight IDs bind rule version/rule/key; observation IDs also bind cutoff and saved
run. Cards expose origin-known and business/evaluation clocks. Quantitative history
deltas require both adjacent points to be assessable; an emerging insight after
missing coverage is `new` with `comparable:false`, never proof that a prior evidence
problem resolved. Evidence inspection selects one key and section and pages retained
rows; it never sends the whole 100-key inventory source.

Scenario controls preserve saved selected-key defaults and Lab integer bounds.
Counterfactual incomplete supply may suppress values but `clean` cannot waive a
saved blocked run. Counterfactual traces cite `product.calculation` and label original
saved runs as `planning.runs.inputs`. Prefix without/with advisory-order trajectories
are supported exact comparisons; periodic service/cost outcomes remain separate.
Costs expose 28 scored days and distinct runoff windows. Total-cost deltas are null
when runoff lengths differ; scored holding/backlog/setup/total comparisons remain
available on the common 28-day window. Undefined denominators stay null.

Fresh native PostgreSQL 18 database, owner plus restricted `ii_runner`, produced:

- Eight-key fixture first: 53 actual appended reports, normalized 1,314,369 bytes,
  digest `f04e01ae8175e615203038736f01ef763ecf26637074f48a7372ca98bd75347a`.
  Retained [eight-key export](review/product-small-evidence.json.gz); independent
  quantity/category and clock checks passed before the expanded export.
- Expanded fixture: 605 actual appended reports (600 planning, three normal
  reliability, one isolated duplicate reliability and one blocked control plan),
  normalized 15,394,381 bytes, 568,269 gzip bytes, digest
  `b28d05232183ee4352cc3a1d2ed670d5888b4bb32f1288c021678096b6f8f9c9`.
  Bundled `src/inventory_intelligence/product_evidence.json.gz`.
- Exact first/second/third category counts: risk 49/62/37, opportunity 26/25/25,
  evidence 12/0/12, none 13/13/26. These totals describe synthetic rules, not
  commercial benefit or release accuracy.
- One local postvalidation call sample: full archive validation 2.10 s;
  overview/explore/detail about 8 ms, scenario about 2 ms. This is a local
  developer observation, not a benchmark or public-runtime capacity claim.

Reproduction requires a **fresh disposable database** and schema bootstrap as owner:
`sql/schema.sql` then `sql/planning_schema.sql`. Set `FIXTURE_DATABASE_URL` to
owner and `DATABASE_URL` to restricted runner, then run
`python scripts/export_product_evidence.py --output /tmp/new-product.json.gz`.
The loader refuses existing identities and exporter refuses existing output files.
For the first control, use a separate fresh database with `--sku-count 4
--prefix product-small`. Export saves actual `run_checks`, `run_forecast` and
`run_plan` reports; normalized expansion reproduces each original report hash and
planning input digest. Source snapshots are immutable independent synthetic counts;
no source row or historical artifact was updated.

Focused validation: `python -m unittest tests.test_product tests.test_product_journey`.
Retained report hashes are integrity/provenance checks, not producer signatures.
Public runtime/TLS, human comprehension, operational imports, authenticated action
execution, supplier feasibility and commercial benefit remain separate gates.

Archive boundary checks additionally require literal boolean supply-completeness
flags, unique nonempty retained supply row IDs, nonempty natural source identities,
and the isolated duplicate control's exact snapshot rows/key/origin. Rehashed
malformed manifests or fabricated duplicate evidence are rejected. New exports
record the actual PostgreSQL server version from the restricted connection rather
than assuming a major version; the retained PostgreSQL 18 evidence is unchanged.

Product observation clocks distinguish the saved business cutoff, decision known-at,
inventory evaluated-at and actual planning report creation time. Creating the archive
later does not refresh historical stock or admit later knowledge.

History cards carry a comparison signature over key/unit, rule/model/policy
versions, business timezone, training/projection windows and lead/review/safety/
pack/MOQ fields. Any signature mismatch makes the transition unknown, quantitative
comparability false and numeric deltas null, with an explicit comparison reason.
V1 replay accepts exactly one open reservation and one confirmed plus one pending
inbound row, matching its scenario controls; it does not accept arbitrary supplier
or operational uploads. Zero-quantity declared rows retain those identities.
