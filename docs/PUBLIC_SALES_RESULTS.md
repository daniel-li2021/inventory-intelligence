# Public observed-sales evidence and first forecast evaluation

Measured 2026-10-03 on the independent public-observed-sales task branch using
Python3.12.14/openpyxl3.1.5. This is offline research on one public retailer, not
operational accepted-order demand or historical inventory performance.
[Adapter protocol](PUBLIC_ADAPTER_V1.md), [forecast protocol](PUBLIC_FORECAST_V1.md),
and [exact aggregate artifact](review/public-sales-forecast-v1.json).

## Source and extraction

Chen, D. (2015), Online Retail, UCI Machine Learning Repository,
DOI10.24432/C5BW33. The [official source](https://archive.ics.uci.edu/dataset/352/online%2Bretail)
states [CC BY4.0](https://creativecommons.org/licenses/by/4.0/). The official archive
was acquired on2026-10-03 at15:16:37 UTC. Archive SHA-256:
`f5385cbb54bbebf7196389109c6b0621faab0c304e3702548165e71c84aede8b`.
Its workbook member hash, sizes, URL, UTC acquisition timestamp and immutable
source metadata are retained locally and in the aggregate provenance receipt.

The complete extraction has541909 raw rows and no invalid required rows:

- 531285 included gross positive non-cancelled rows, totaling 5660981 units.
- 9288 cancellation-coded rows excluded before quantity classification.
- 1336 nonpositive non-cancelled rows excluded.
- 10684 repeated invoice/stock pairs retained and diagnosed, never silently
  deduplicated. The archive/sheet/row identity is authoritative.

These counts exactly partition the source rows. Missing customer/description
fields do not become missing demand or invalid required identity/date/quantity.
Original source dates remain naive calendar labels. Source recording time,
historical ingestion time, availability and unconstrained demand remain unknown.
Return/cancellation quantities are not subtracted as negative demand.

All real raw rows, exclusions, item mappings, reconstructable daily series and
item-level results remain in ignored `data/raw/uci-online-retail/`. The Git
artifact contains only aggregate metrics/counts, hashes, boundaries, acquisition
metadata and attribution. Its schema was separately checked for absence of raw
customer/item attributes, identities, source series and item forecast records.

## Frozen subset and method selection

Training-prefix identities cover3838 StockCodes. Seed701 selects32 items using
only training positive-day rate and volume: dense/high7, medium/high6,
medium/low6, sparse/high6, sparse/low6, and one training-known zero control.
No holdout-only item or future quantity affects selection, as independent tests
verify. This stratified subset is not volume-weighted representative sampling.

Selection is2011-09-16 through2011-11-10; the final28 complete holdout dates are
2011-11-11 through2011-12-08. The potentially partial final source day2011-12-09
is excluded. All targets end inside their split. Per-item selection minimizes
28-day cumulative MAE; choices are frozen before holdout scoring. Selected method
counts: mean11, SBA6, Croston4, TSB4, naive4, seasonal-naive2, zero1.

## Held-out outcomes

All32 items have one28-day holdout origin, giving896 scored points and15373
actual observed units. Aggregate results (display rounded; artifact exact):

- Expanding mean: daily MAE 15.0173, cumulative MAE 247.8501, WAPE 0.8753.
- Frozen selection-chosen mix: daily MAE 26.7060, cumulative MAE 443.6063,
  WAPE 1.5565.
- Seasonal naive: daily MAE 24.7489, cumulative MAE 409.2188.
- SBA: daily MAE 20.5400, cumulative MAE 368.2038.
- TSB: daily MAE 22.9941, cumulative MAE 443.3245.

Mean outperforms the frozen selected mix at this horizon; selection-period
ranking does not guarantee held-out ranking. Mean also has the lowest aggregate
daily MAE across all three horizons. At7 days, SBA has lower cumulative MAE69.3068
versus mean72.1738, showing that daily and cumulative accuracy can rank methods
differently. At14 days, mean cumulative MAE133.8084 is below the selected
mix135.5642. All fixed candidates and training-defined segments are retained,
including null WAPE when a segment has no actual units.

Origin/point denominators: H7 has128/896; H14 has96/1344; H28 has32/896.
H14 targets overlap, so its22460 actual-unit denominator repeats origin/lead
observations and is not unique-period retailer volume. H7/H28 each cover the
same28 holdout dates. The one retailer, small stratified subset and dependent
origins/segments limit conclusions; no population confidence or savings claim.

## Validation, reproduction and gate decision

22 focused tests passed, including13 new adapter/forecast oracles plus existing
intermittent model tests. Tests independently cover exact totals, exclusions,
duplicate source identities, repeated business pairs, missing-versus-zero,
schema/formula/hash failures, train-only sampling, holdout isolation, partial-day
exclusion, deterministic ties and error denominators. Natural workbook extraction
passed541909-row/schema/calendar acceptance. Saved aggregate checks also verify
all code dependencies and segment count/denominator totals.

Exact cross-item rational sums exceeded Python's decimal integer conversion
limit. The artifact uses signed hexadecimal Fraction numerator/denominator
strings, preserving precision without changing process safety limits. A5000-digit
independent round-trip oracle proves the repair; the protocol gives the decoder.

```sh
python3.12 -m pip install '.[research]'
PYTHONPATH=src python3.12 -m unittest tests.test_public_sales tests.test_public_sales_benchmark tests.test_intermittent -q
# Official acquisition only if no already accepted local source exists:
PYTHONPATH=src python3.12 -m scripts.public_sales_adapter --acquire
PYTHONPATH=src python3.12 -m scripts.public_sales_benchmark --output output/public-sales-forecast-v1.json
```

Reuse the accepted source/derived cache; checksum changes are errors, never
silent replacements. Published metrics make this evaluation consumed. No new
model is promoted: simple mean remains strong, while the selector's instability
and specialized segment/horizon weaknesses need fresh confirmatory evidence.
ADIDA/IMAPA/LightGBM remain conditional. Sales-proxy inventory/safety simulation,
broader later-origin evaluation and another retailer are not completed by this
forecast-only package.
