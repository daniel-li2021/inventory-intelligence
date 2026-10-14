# Controlled synthetic replay and Insight Discovery V2

Assigned October 13, 2026. This additive local workflow preserves planning-v1,
prefix-stock-v1, original Lab and packaged inventory-product-evidence-v1 bytes.

## Bounded input and evidence contract

`synthetic-intake-v1` accepts JSON with an explicit synthetic declaration, dataset
and version identity, one business cutoff, fixed dimensions and complete key scope.
Maximum 50 SKUs × 2 locations, 12 chronological versions, 28 accepted-demand days,
16 reservations and 16 inbound lines per key; 2 MiB per input. Quantities are exact
nonnegative integer pieces (never float/bool). Null demand is missing, not zero.
Stock is a declared independent synthetic count; missing stock rejects intake.
Supply completeness is explicit. Each source version retains original bytes,
canonical digest, natural inbound/reservation identities and knowledge clocks.
This slice accepts independent snapshots, not arbitrary movement feeds or revisions.

CLI execution requires `--local-synthetic` and local PostgreSQL owner/runner URLs.
First admission refuses an occupied database; use a separately bootstrapped empty
synthetic database. Subsequent admission uses its immutable source registry.
Sources and results are separate. Admission of all versions is atomic; replays use
the actual reconciliation, mean forecast and prefix planner, reload persisted runs,
then validate and atomically publish an immutable content-addressed catalog.
Failures retain the previous catalogs. A retry of identical source identities is
idempotent; changed content under the same version is rejected. No HTTP upload or
source-write endpoint exists. Serving a selected catalog remains read-only.

## Predeclared controls (before implementation/outcomes)

New namespace `dynamic-controls-v1`: three cutoffs, two SKUs/two locations.
Complete daily series [2×14,4×14] has mean 3 and recent/older ratio 2; Harbor
stock 10, reservation 3, confirmed inbound 5 at day 1, lead 2/review 3,
safety 2/pack 6/MOQ 6 yields order 6 and balances 4/6/3/0/−3.
Same SKU at Upland has stock 80 and terminal balance 67; imbalance must cite both
keys without claiming a feasible transfer. Next cutoff: Harbor stock 4, mean 4,
inbound 3 at day 3 gives balances −3/−7/−11/−12/−16, order 18, supply reduction
2 and later ETA for the same natural inbound identity. Risk worsens then persists.
Quiet demand has undefined growth from zero and no demand-change alert. One null
day blocks forecast/planning and prevents a false resolved insight; incomplete
supply likewise blocks comparison. None of these are efficacy/financial claims.

Independent controls must also reject malformed/oversize/duplicate/inconsistent
source versions, unknown dimensions, future source clocks, fractional quantities,
changed historical reports and rehashed inconsistent evidence; validate retry,
reopen, restricted-role denial, rollback and last-good publication. Measure replay
latency, process memory, raw/compressed evidence bytes and read latency. Compare V2
against V1 detection sets, retaining misses/unsupported cause claims explicitly.

## Rules and dependency boundary

V2 adds exact demand changes, known supply reductions/ETA changes, persistent or
worsening planner exposure and same-SKU location imbalance. Rules cite the saved
inputs/runs and state observed facts separately from model hypotheses and unknown
causes. Missing or incompatible evidence suppresses cross-cutoff claims.
Quantity/ETA alternatives already have actual-planner stress evidence. Supplier
calendars/capacity require a new feasibility contract before transfers; this phase
does not claim those prerequisites exist. Public/runtime/reference/human gates stay
separate from this controlled local capability.

## One-review decision contrast (predeclared arithmetic controls)

Compare the actual saved proposal, no action and one alternative pack/MOQ quantity
using the existing execution FIFO semantics. This is one review, with no later
orders, rather than a repeated planner policy or the periodic simulator. Future
demand is declared synthetic input; initial stock, all confirmed inbound and new
orders are paid at 2/piece, positive inbound/orders at 2/setup, ending stock at
1/day and backlog at 10/day. All arms use 28 demand days + 5 common closure days.
Reservations enter FIFO before new demand. Pending inbound is excluded. Remaining
backlog is retained and charged; there is no salvage or forced settlement.
Nominal lead, packs and MOQ constrain new orders. Declared delay is 0–3 days;
no expedite, supplier capacity/calendar or transferable pieces are claimed.
Out-of-window existing supply blocks complete cost comparison.

Independent first-cutoff Harbor control: stock 10, obligation 3, existing receipt
5 on day 1, declared demand 4/day. No action / saved proposal 6 / alternative 12
have total paid cost 18039 / 16281 / 14609, terminal backlog 100 / 94 / 88,
terminal stock 0 in all arms. Three-day delay for the saved 6-piece order costs
16373; immediate new fill is 12 versus 18 pieces without delay, eventual new fill
18 in both. These are arithmetic scenario controls, not a policy promotion or
new decision-quality study. Invalid 5-piece orders and early receipt reject;
blocked sources yield null results. Larger orders need not improve other traces.

## Working local walkthrough

With the repository's Python `.[lab]` environment installed, serve the retained
actual replay without a database, Node runtime or model key:

```sh
python scripts/run_local_demo.py --port 8030 --catalog docs/review/dynamic-replay-v1.json.gz --journal output/dynamic-demo.sqlite
```

Open `http://127.0.0.1:8030/`. Choose April 6 → Insight Discovery V2 →
Same-item location imbalance → Investigate finding. Inspect observed demand,
model hypothesis, unknown external causes and both locations' report references.
Compare → alternative 12 pieces → Compare one review: paid costs are 18039
(no action), 16281 (saved 6), 14609 (alternative 12). Change declared delay to 3;
the old result is stale until recalculation, then the saved proposal costs 16373.
Five pieces violates pack/MOQ and retains the last good result marked stale.
Export retains the source/input digest, all 33 daily events and cost components.
History shows demand/supply changes, worsening risk April 13 and persistence
April 20. Choose B/Upland: missing demand April 6 and supply April 20 suppress
quantities. `/lab` and the original March Execution/journal stay available with
their separate clocks and evidence; new snapshot intake does not claim receipts
caused a stock change.

For a new local version set, copy the example JSON to an ignored output path,
retain fixed dimensions/dataset identity, add a new version/cutoff, and change
only declared synthetic facts. Create an empty disposable PostgreSQL database;
never point first admission at a previously populated demo or acceptance DB.

```sh
export TEST_DATABASE_URL='postgresql://LOCAL_OWNER@127.0.0.1:LOCAL_PORT/NEW_EMPTY_DB'
export FIXTURE_DATABASE_URL="$TEST_DATABASE_URL"
export DATABASE_URL='postgresql://ii_runner:ii_runner_local@127.0.0.1:LOCAL_PORT/NEW_EMPTY_DB'
python -m tests.bootstrap
python scripts/replay_synthetic.py --local-synthetic --input docs/examples/dynamic-controls-v1.json --output-dir output/replay-catalogs
```

Use the printed content-addressed archive with `--catalog`. A replay appends fresh
results; unchanged sources retain their identities. Archives are independently
selectable and never overwritten or silently activated. Supply accepts up to 16
lines, but the legacy periodic scenario controls require one current open
obligation and at most one confirmed receipt; unsupported shapes are withheld
and the one-review contrast remains available. The 50×2×12 parser bounds are not
a measured maximum-workload performance claim.

## Focused reproduction

```sh
python -m unittest tests.test_synthetic_replay tests.test_decision_contrast -v
python -m unittest tests.test_synthetic_replay_db -v
python scripts/measure_dynamic_replay.py --output output/new-dynamic-measurement.json
python scripts/check_dynamic_browser.py --base-url http://127.0.0.1:8030 --output output/new-dynamic-browser.json
```

Database controls require local `TEST_DATABASE_URL` / `DATABASE_URL` with owner
create-database privilege; they create/drop only their own fresh temporary DBs.
Browser controls pace requests within the unchanged anonymous 2/s rate and wait
for completed React requests. They are correctness/developer checks, not a load
campaign, human study or accessibility conformance. Saved measurements refuse an
existing output. Original archives and consumed quality studies are never replayed
for a new accuracy claim.


## Independent dataset generalization and source-bound review

Two new frozen designs extend the original 100-key/April controls without reusing
those source identities: coast3 SKUs×2 sites/three May cutoffs and inland6 SKUs×1
site/two November cutoffs with DST UTC08 origins. [Predeclared exact inputs/oracles](examples/generalization-protocol-v1.json)
precede execution; [actual PG17 receipt](review/generalization-v1/receipt.json) retains
30 exact key/cutoff cells,18 expected rule triggers and 65 persisted reports. Replay
single samples are0.889/0.392 seconds; total campaign3.189 seconds and native max RSS
67,158,016 bytes. These small measurements are not percentile/SLO/maximum-envelope
or unseen detection claims. The first harness attempt compared exact serialized
rational strings with Fraction objects and rejected; correcting normalization did
not change any frozen expected value or source input.

Controls preserve idempotent source retry, version-conflict and late-transaction
rollback, owner/runner write denial, fresh historical semantic rerun and atomic
last-good publication. Original report/source bytes are never rewritten. New
sources automatically regenerate actual saved runs; insights derive from the
validated selected catalog. CLI selection/activation remains explicit, with no
HTTP import or implicit operational repair.

`inventory-insights-v2` now exposes exact contributing stock/demand/reservation/
confirmed-inbound/safety/proposal factors and stable priority: risk before
opportunity, more pre-arrival shortage days, then larger proposal, rule/id tie-break.
The ordering explains attention, not causal certainty, calibrated risk or economic
value. IDs/V1 meanings remain unchanged. Unknown coverage/causes remain explicit.

`exception-review-v1` stores acknowledged/investigating/resolved notes in an
append-only local SQLite journal. Each note binds full finding calculation digest,
observation/archive/cutoff, source references and aware UTC review time. Wrong/stale
binding, conflicting event identity, backdated review and more than256 events reject.
Resolution never hides facts, repairs a source or waives planning. Changed observations
start a new chain; previous archive notes remain recoverable with their original
catalog. Read-only defaults and same-origin loopback writes are unchanged.

```sh
python scripts/generalization_study.py --output-dir output/new-diagnostic-generalization
python -m unittest tests.test_exception_review tests.test_insight_priority -v
```

The study needs owner/restricted URLs on a local PostgreSQL17 and creates/drops only
its own disposable databases. Published paths are now consumed diagnostic controls,
not another fresh accuracy evaluation. [Full platform walkthrough](PLATFORM_GUIDE.md)
connects this intake/discovery slice to [supplier feasibility](SUPPLIER_FEASIBILITY.md),
[donor-safe transfers](TRANSFERS.md) and independently saved actual feedback.
