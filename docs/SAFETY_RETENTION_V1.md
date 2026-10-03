# Declining-demand safety retention — v1

Frozen before evaluating outcomes on 2026-10-03. `safety-retention-v1` is
research-only and leaves the old empirical-safety contract unchanged.
Fresh-warmup-v1 paths are consumed and do not tune this study.

Use independent version/family/demand seed namespaces 3301/3709/4027, with
constant, zero, lumpy, temporary pause/recovery, seasonal low, gradual decline
and permanent obsolescence. Generate 420 days: 196 historical days, 56 warmup,
then three 56-day score blocks (selection-period, holdout, later holdout).
The pause covers days252–279; obsolescence begins day280. Seasonal lows occupy
the last28 of each112-day period; declining occurrence probability decreases
after day196. Families and size/probability rules reuse the declared Wave 1
shape, with an independent RNG namespace. No automatic retirement semantics.

Each candidate starts with ten pieces and no backlog/pipeline at day196 and
runs continuously through warmup/scoring. L2/R7/pack2/MOQ4, h1/b10/setup2/unit2.
One independent absolute-calendar supplier trace per family/seed has daily
hidden delays [0,0,1,3] across all operating and settlement days. Common final
settlement extends twelve days past the final scoring day. Physical initial
stock and every ordered piece are paid for; no salvage or disposal shortcut.

Hold the point forecast **TSB alpha1/5 beta1/5** identical while comparing:

- fixed safety0;
- expanding-history empirical q90 (existing reference);
- q90 of the most recent12 completed non-overlapping protection-period errors;
- decay-weighted q90 of all completed errors, each older sample weighted by
  (4/5)^age, youngest weight1. Weighted quantile is the first sorted residual
  whose cumulative weight reaches q*total weight.

Add fixed mean/safety0 as a second forecast reference. Training fits always use
the full origin-known demand prefix; retention changes only which completed
residuals contribute to safety, not the underlying forecast. Minimum train28
and minimum8 complete calibration labels; reject insufficient calibration rather
than falling back to free zero safety. Recent retention has min(12, count)
samples. Decay reports raw count, weights and exact effective sample size
(sum weights)^2 / sum squared weights; raw minimum8 does not imply eight
independent effective observations. Ranks/weights and thresholds are exact.

Report full-window operating/procurement costs, starting/ending state, terminal
stock, score-only fill/cycle/backlog/stock, target coverage/pinball and safety
trajectories. Also report the three score blocks separately and pause recovery
days280–307 (including carried backlog). No forecast/calibration target may
cross a reported segment boundary. Report null unit service for zero demand;
low safety cannot dispose of inventory already owned.

All candidates are predeclared; no winner is selected using these outcomes.
Descriptive full-run gates require at least5% lower full cost versus expanding
TSB/q90 **and** fixed mean, immediate fill>=9/10, cycle>=4/5 and no service-rate
regression against either reference. Report failure causes. Segment failures,
especially recovery, remain visible even if aggregate service passes; no
operational promotion follows from a passed research gate.

Independent tests cover nearest-rank recent truncation, exact weighted quantile
and effective count, positive/negative safety clipping, minimum samples,
incomplete target exclusion, identical point forecasts across retention policies,
and prefix invariance. Save complete reproducible synthetic inputs, dependency
hashes, exact metrics, compact safety evidence and full trajectory hashes.
