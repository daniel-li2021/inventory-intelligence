# Assigned public observed-sales research — v1

Prepared 2026-10-02; **assigned by the user on 2026-10-03** as part of the
[long-term roadmap](https://github.com/daniel-li2021/inventory-intelligence/blob/208d5b3e1a9f2beb78ea94258800dfe4407150c8/docs/RESEARCH_ROADMAP.md). This authorizes official UCI acquisition
and the bounded separate research described here. It is not a relaxation of the
operational planning contract or permission to import confidential inputs.
The operational portfolio stays synthetic. Public observations would live in a
separate offline research adapter and ignored local outputs, never as accepted
orders, verified inventory, warehouses or uncensored demand.

## Dataset and rights

Use the investigation's UCI fallback, **Online Retail**, Chen (2015), DOI
[10.24432/C5BW33](https://doi.org/10.24432/C5BW33). The
[official dataset page](https://archive.ics.uci.edu/dataset/352/online%2Bretail)
was checked 2026-10-02 and explicitly identifies CC BY 4.0. Its linked archive
contains `Online Retail.xlsx` (approximately 22.6 MB); metadata records 541,909
transactions from 2010-12-01 through 2011-12-09. Retain attribution, the
[license](https://creativecommons.org/licenses/by/4.0/) and retrieval provenance.
M5's [rules](https://www.kaggle.com/competitions/m5-forecasting-accuracy/rules)
and [data page](https://www.kaggle.com/competitions/m5-forecasting-accuracy/data)
returned no readable terms in this check. M5 acquisition/publication remains
unapproved; do not substitute an unofficial mirror or infer rights from MIT.

Acquire only the official UCI archive into ignored `data/raw/uci-online-retail/`.
Record real UTC retrieval time, exact URLs, license/version, archive/file SHA-256,
file sizes, workbook sheet names, schema and row counts. Preserve source row
identity `(dataset, archive_sha256, sheet, row_number)`; invoice/product pairs
are not proven unique line identities. Raw rows and reconstructable derived
series, customer identifiers and descriptions stay outside Git. Publish only
code, synthetic adapter tests, protocol and aggregate research metrics with
dataset attribution. No public-data screenshots or operational import.

## Target and completeness

Target is **gross positive non-cancelled invoiced unit sales per StockCode and
source date**, across the dataset's retailer. Customer Country is not a store
or fulfillment warehouse. Use recorded InvoiceDate calendar labels; no invented
timezone, acceptance time, recording time or historical ingestion clock.
Acquisition time is separate from a modeled end-of-day release assumption.

Cancellation-coded invoices and nonpositive quantities are excluded from gross
positive sales, with exact exclusion counts/reasons retained. Do not subtract
returns as negative demand, reconstruct hidden demand, silently drop duplicates
or infer product availability from first positive sale. Invalid required
quantity/date/identity rows block adaptation and are reported. Preserve original
row evidence outside Git, including excluded rows. Dates missing for a selected
item have observed sales zero only within a verified complete extraction of the
declared archive range; this never proves zero unconstrained demand or availability.
No prices, promotions or customer attributes enter forecasting features.

## Frozen bounded benchmark

Use source dates [2010-12-01,2011-12-09), excluding the final potentially partial
day. Final 28 complete dates [2011-11-11,2011-12-09) are the internal holdout.
Selection is the preceding 56 dates [2011-09-16,2011-11-11); earlier dates train.
Choose at most 32 StockCodes using seed 701 **only from the training prefix**,
stratified by positive-day rate and total observed volume. Preserve selection
manifest, bin boundaries, all-zero controls if present, inclusions/exclusions
and canonical item IDs; never inspect holdout to pick products.

Compare approved baselines, zero, Croston/SBA/TSB and the already frozen safety
grid; no new fit grid or holdout tuning. Report daily MAE/bias/nullable WAPE,
cumulative 7/14/28-day errors at complete predeclared origins, training-only
denominators, and exact offline policy outcomes under the declared proxy-sales
trace. Supplier traces, initial stock, packs/MOQ, costs, service floors and
promotion rules remain synthetic and versioned. Do not call resulting stockouts
historical shortages, or finite penalties retailer profit/savings. Windows and
products are correlated; no population confidence claim.

The adapter and its synthetic row oracles must pass before acquisition. Abort
on schema/row-count/hash changes, never replace an accepted archive silently.
Holdout cannot authorize promotion without required service and clean/important
segment checks. Aggregate results may justify a new aggregation or global-model
handoff; ADIDA/IMAPA/LightGBM are not automatic additions. A failed or blocked
benchmark leaves the existing approved methods untouched.

## Historical implementation checkpoint

The [adapter](PUBLIC_ADAPTER_V1.md) and [forecast-only evaluation](PUBLIC_FORECAST_V1.md)
are implemented and independently validated on the public-observed-sales task
branch. [Measured results](PUBLIC_SALES_RESULTS.md) preserve raw/derived observations
locally and publish aggregates only. Initial forecast comparison and train-only
subset selection are complete. The dependent public-safety-service branch adds
the [frozen sales-proxy safety study](PUBLIC_SAFETY_V1.md) and
[achieved-service results](PUBLIC_SAFETY_RESULTS.md), with paid continuous warmup,
q90/q95 coverage/pinball and synthetic supply timing. The original forecast report
remains forecast-only. These exploratory reused observations authorize no advanced
method or operational import. See the research roadmap in PR14 for remaining work.

The subsequent [disjoint-item protocol](PUBLIC_CALIBRATION_V1.md) commits a
training-only seed-1709 subset/grid before any new-item simulation, excludes all
32 consumed identities and reuses attested source caches. Its
[measured replication](PUBLIC_CALIBRATION_RESULTS.md) retains all 768 arms and
null denominators, with no policy/model promotion. This is cross-item evidence
in the same retailer/calendar, not independent-market or later-time validation.
