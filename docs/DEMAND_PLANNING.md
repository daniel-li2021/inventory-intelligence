# Demand Planning

The Desk workspace at `/#/demand` compares synthetic demand forecasts and a
temporary future-only adjustment. It does not save a business plan or place an
order. This implementation is pending owner product acceptance. Source push was
authorized October 29; deployment remains unassigned.

## Run and review

Use the Python 3.12 [demo setup](../README.md#try-the-decision-workbench), or from an already
configured checkout:

```sh
PYTHONPATH=src python -m uvicorn inventory_intelligence.lab_hosted:app --host 127.0.0.1 --port 8766
```

Open [Demand Planning](http://127.0.0.1:8766/#/demand?snapshot=2026-01-05).
The built assets are packaged; no Node, database or model key is required for
serving. Frontend edits require `cd frontend && npm run build` followed by a
server restart so the hosting asset allowlist uses the new filenames.

The Overview **Plan future demand** shortcut opens this workspace. **How to use**
explains the full journey. Example adjustment buttons only fill the draft for the
selected dates; **Apply adjustment** runs the calculation. **Inspect this item's
evidence** preserves item and cutoff and opens saved inventory evidence; a temporary
adjustment is not carried into that workspace. Invalid item/location links stay
visibly unavailable until you choose a valid pair or **Use first available item**.

1. Choose **2026-01-05**, **II-00**, **Harbor**, **28 days**. Historical mean is
   4 pieces/day and forecast demand is 112 pieces. Compare all three existing
   methods; constant history makes their forecasts agree.
2. Apply **+25%** across the displayed future period: demand becomes 140 pieces,
   and the advisory order changes from 12 to 18 pieces. **+1 piece/day** produces
   the same result. History remains unchanged.
3. Start the +1 piece/day adjustment on **2026-01-10**. Demand becomes 135 pieces,
   while the order stays 12: the five-day protection window ends January 9.
4. Try **-5 pieces/day**: negative future demand rejects and the page clearly
   returns to baseline. Reset clears the applied comparison. Changing inputs
   invalidates the old comparison before a new one can be used or exported.
5. Switch Daily/Weekly and 7/14/28 days. Expand exact values for calendar coverage.
   Week buckets split at the historical/future boundary and label partial weeks.
6. At **2026-01-19**, **II-02 / Upland** retains valid demand but blocks inventory
   impact on incomplete supply. **II-03 / Harbor** at **2026-01-05** has missing
   demand and no forecast. Missing demand is not zero.
7. Export the current baseline or adjusted comparison; inspect the source archive,
   calculation identity and original run references in its JSON. Reloading starts
   from a baseline, not a saved plan.

Suggested acceptance screenshots: daily +25% chart and totals; out-of-window
unchanged-order explanation; weekly period coverage; blocked evidence; mobile
selection/chart/adjustment layout. Developer checks do not establish independent
human comprehension or WCAG conformance.

## Contract and calculation boundaries

`demand-planning-v1` adds GET `/api/product/demand` and POST
`/api/product/demand-scenario`. Both require cutoff/SKU/warehouse selection; POST
also requires the current archive digest. Forecast horizon is 7, 14 or 28 days;
method is `mean` (operational default), `naive` or `seasonal_naive`. GET accepts
`archive_digest` to bind a selection; the Desk always supplies it.

POST adds optional `adjustment={kind,value,start_day,end_day}`. Kind is `percent`
or `pieces`; value is an exact signed whole integer, bounded to [-100,100] percent
or [-1000,1000] expected pieces/day. Dates are inclusive ISO calendar dates inside
the selected future horizon. Unknown fields, invalid ranges and negative resulting
demand reject with 422; changed archives return 409 and invalid source archives
503. Read-only hosting retains its existing admission/body limits and permits
these calculations without enabling journals or operational writes.

For each selected future day, adjusted expectation is baseline × (100+value)/100
or baseline + value. Fractional expectations remain exact; they are not rounded
into observed physical pieces. Historical records, obligations, confirmed supply,
saved forecasts and policy remain unchanged. `forecasting.forecast` calculates
all methods. `replenishment.project` calculates both full protection windows with
the existing safety/MOQ/pack rules. A protection window can exceed a shorter
display horizon; undisplayed future days retain their baseline expectations.

Daily/weekly quantities, totals, deltas and proposals come from the backend.
The frontend converts exact values to approximate numbers only for SVG chart
coordinates; tables and exports retain exact quantities. Weekly totals become
unavailable if any covered daily value is unavailable; they never hide missing
days by summing the remainder. Bounded day counts are calendar metadata.

The current archive has 28 training days and no matching per-item backtest reports.
MAE, bias and WAPE remain null with an explanation. The separate Evaluation study
is never relabeled as the selected item's accuracy. Forecasts have no prediction
intervals. Expected net inventory deficits are modeled exposure, not observed
stockouts, physical negative stock or achieved service. The periodic simulator's
cost/service metrics are not attached to this prefix proposal.

The new calculation digest binds contract version, archive, source plan/forecast,
key, cutoff, method, horizon and adjustment. Existing report bytes, scenario
semantics, forecast kernels and the mean operational default are preserved.
Request cancellation, selection remounts and generation checks discard obsolete
GET/POST results; draft edits and reset immediately restore the labeled baseline.

## Validation

[Local receipt](review/demand-planning-v1/receipt.json): 48/48 focused Python tests,
11/11 frontend tests, type/build checks and the installed offline wheel pass.
Browser checks cover adjustment/reset/export, loading recovery, an eight-second
delayed response, missing/blocked evidence and 1280/768/390-pixel layouts.
[Desktop](screenshots/demand-planning/desktop.png),
[mobile](screenshots/demand-planning/mobile.png) and
[blocked supply](screenshots/demand-planning/blocked-supply.png) captures use actual
local synthetic results. These are developer checks, not new forecasting evidence.

Run focused controls from the checkout with the configured Python environment:

```sh
PYTHONPATH=src python -m unittest tests.test_demand_planning tests.test_forecasting tests.test_product tests.test_lab_api tests.test_lab_hosted -q
cd frontend
npm test
npm run build
```

The adapter tests independently check every one of the 300 packaged key/cutoff
cells, exact manual adjustment/projection quantities, distinct methods on a
hand-specified library control, missing/blocked evidence, negative rejection,
partial calendar weeks, binding and read-only hosting. These are regression
controls, not a new forecasting study. Original evidence stays immutable.
