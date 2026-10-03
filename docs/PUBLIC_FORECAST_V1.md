# Public observed-sales forecast evaluation — v1

Frozen before scoring real observations on 2026-10-03. Identifier
`uci-observed-sales-forecast-v1`. This first public evaluation implements forecast
realism and provenance; synthetic-stock policy/safety-grid evaluation remains a
separate later part of the public-sales protocol, not a claimed completed task.

Use only a complete, attested official adapter extraction. Benchmark source dates
[2010-12-01,2011-12-09); the final source date is excluded as potentially partial.
Training ends2011-09-16; selection is56 days to2011-11-11; holdout is28 days to
2011-12-09. Historical end-of-day release is a declared modeling assumption,
not original availability/ingestion evidence. Forecasts use completed dates only.

Choose at most32 items using seed701, only from identities actually present in
raw training-prefix rows (including exclusions). Positive-day-rate bins: zero,
(0,1/10], (1/10,1/2], (1/2,1]. Split each positive bin at the training positive-
item total-volume median (<=median versus >median). Shuffle sorted pools with
seed701 and take one per nonempty sorted bin per round until32; include at most
one known training-zero item if present. Preserve exact bin boundaries/features,
item mapping, exclusions, selected order and manifest hash locally. New holdout-
only items or changed future quantities cannot affect this choice.

Compare naive, expanding mean, seasonal-naive7, zero diagnostic, Croston, SBA,
TSB, using unchanged kernels/default alpha/beta1/5. Horizons7/14/28, rolling origins
every7 days within each split; targets must end within that split. Selection
chooses a method separately per item by smallest cumulative MAE at horizon28,
ties in the listed order. The chosen method is frozen before holdout; completed
holdout observations may update its forecast, never its method choice.

Publish aggregate scores by training-defined segment and overall: item/origin/
point counts, actual-unit denominator, exact daily MAE/bias/nullable WAPE and
cumulative MAE/bias. Report the fixed selection-chosen candidate alongside all
predeclared methods, plus selected-method counts. WAPE uses evaluated actual
units; bin/scale/identity decisions use training data only. Do not mix those
denominators or silently drop zero/undefined cells.

Raw observations, item-level scores/predictions, reconstructed series and the
selection manifest stay local and ignored. Published artifacts contain only
aggregate results, counts, source/archive/adapter/subset/code hashes, exact
protocol boundaries, acquisition metadata and attribution. Missing customers,
prices and descriptions are not required demand inputs or forecast features.

Exact Fraction values use signed hexadecimal numerator/denominator strings.
Decode as `Fraction(int(value["numerator_hex"],16), int(value["denominator_hex"],16))`.
Large cross-item rational sums can exceed Python's decimal conversion limit;
this lossless encoding preserves exactness without disabling that safety limit.
Counts remain ordinary JSON integers. Selection is calculated and frozen before
the holdout scoring call, as well as mathematically independent of holdout truth.

No observed-sale is labeled accepted-order demand. No observed zero establishes
availability or uncensored demand. This benchmark does not estimate historical
stockouts/profit, simulate real suppliers or justify automatic advanced-model
promotion. Correlated series/origins from one retailer limit external conclusions.
Keep negative/null outcomes; additional models require repeated, fresh evidence
of a specific baseline weakness and a separately frozen challenger protocol.
