# Official UCI observed-sales adapter — v1

Implementation assigned by the user on 2026-10-03. This separate offline adapter
implements the public-data portion of the long-term plan; it does not relax
operational accepted-order or synthetic-demo boundaries.

Official source: Chen, D. (2015), Online Retail, DOI10.24432/C5BW33,
[UCI source](https://archive.ics.uci.edu/dataset/352/online%2Bretail),
CC BY4.0. Official archive URL:
`https://archive.ics.uci.edu/static/public/352/online%2Bretail.zip`.
The source/license was rechecked on 2026-10-03. Preserve attribution and the
[license](https://creativecommons.org/licenses/by/4.0/).

Acquire only that archive, at most64MiB, atomically into ignored
`data/raw/uci-online-retail/`. Record real UTC acquisition time, response URL,
archive size/hash, member size/hash, source page/version/license, sheet names,
exact header and row counts. Reuse a valid accepted archive/manifest; reject
hash/schema/count changes without overwriting the acceptance record. No mirror,
automatic license inference or raw-data publication.

Read the official `Online Retail.xlsx` using optional research-only
openpyxl3.1.5 in read-only mode. Do not modify the workbook. Expect541909 data
rows, eight columns in this exact order: InvoiceNo, StockCode, Description,
Quantity, InvoiceDate, UnitPrice, CustomerID, Country. Validate required identity,
date and quantity independently of UCI metadata. Required formulas, blank keys,
booleans, fractional/noninteger quantities, ambiguous date strings and aware
timestamps block adaptation. Preserve recorded naive calendar labels rather
than inventing a source timezone or recording/ingestion clock.

Source row identity is(dataset, archive SHA-256, sheet, original row number),
not(invoice, stock code). Repeated source identities block. Repeated invoice/
stock pairs are counted and retained without silent deduplication because they
do not prove duplicate source rows. Cancellation-coded invoices are excluded
first, then nonpositive non-cancelled quantities. Never subtract returns as
negative demand. Invalid rows block the whole extraction; audit and raw evidence
remain local, while derived series become unavailable rather than a partial pass.

Target: gross positive non-cancelled invoiced units per StockCode/source date,
across the dataset retailer. Country is customer residence, not a warehouse.
StockCode mapping preserves string codes and maps numeric cells to their decimal
identifier; source-row identity remains authoritative. The scope identifier
`dataset-retailer` is an aggregation label, not physical location evidence.
Descriptions/customer IDs/prices/countries are not forecast features.

Only verified complete archive extraction permits observed-sales zeros in the
declared archive calendar. That does not prove availability, latent demand,
lost sales or business completeness outside this archive. The final potentially
partial2011-12-09 is excluded from benchmark dates; raw audit still includes it.
Raw archives, all row/invalid/exclusion evidence, reconstructable series and item
selection manifests stay ignored/local. Git may contain only adapter/benchmark
code, synthetic tests, protocols and attributed aggregate metrics.

Synthetic acceptance must precede acquisition: independent exact totals,
cancellation/nonpositive exclusions, numeric/text IDs, dates, source identity
collisions, retained invoice/stock repetitions, missing-versus-zero, count/schema
failures and refused cache/hash replacement. Subsequent benchmark uses only
training-prefix item identities/volume/sparsity for seed701 selection and freezes
the prior public-sales time boundaries. No advanced model is automatically added.
