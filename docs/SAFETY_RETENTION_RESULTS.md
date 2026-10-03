# Safety retention: lower safety is not lower owned inventory

Measured on 2026-10-03 under Python 3.12.14. The
[frozen protocol](SAFETY_RETENTION_V1.md) uses independent demand/supplier seed
namespaces, seven families and three seeds, producing 21 labels, 17 distinct
demand paths and 105 continuous warmup/score simulations.
[Exact evidence](review/safety-retention-v1.json) includes full inputs, code
dependencies, costs, every safety review, segment service and trajectory hashes.
Point forecasts are verified identical among the four TSB safety policies.

```sh
PYTHONPATH=src python3.12 -m scripts.safety_retention_benchmark --output output/safety-retention-v1.json
PYTHONPATH=src python3.12 -m unittest tests.test_safety_retention tests.test_research_warmup tests.test_intermittent -q
```

The 27 focused tests passed, including eight independent retention/gate oracles.
The weighted-tail oracle explicitly distinguishes old versus new large errors
and verifies exact effective sample size. Future/incomplete labels cannot change
earlier decisions; insufficient samples fail rather than inventing zero safety.

Both recent12 and decay(4/5) reduce final safety to zero on all three permanent
obsolescence paths, versus expanding safety23/30/16. They do **not** dispose of
already owned stock. Settled terminal stock on seeds3301/3709/4027 is:

- Expanding q90: 58/70/56 pieces.
- Recent q90: 62/60/60 pieces.
- Decay q90: 102/74/68 pieces.

Recent minus expanding full cost is +700/-2036/+1020; decay is
+7716/+386/+1710. Early purchases and different backlog/receipt timing persist
after the safety estimate shrinks. On obsolescence/3301, decay ends with safety0
but owns102 pieces and loses1/20 of full-score fill versus expanding. Declaring a
SKU obsolete or simply zeroing safety would not reverse those historical orders.

Temporary-pause controls show the other side of adaptation. On pause/3709,
recovery fill is23/33 expanding,43/66 recent and17/22 decay. Recent retention
shrinks its tail at the cost of weaker recovery; decay has better recovery here
but higher complete cost. On pause/4027, recent reduces complete cost by2232
while aggregate fill regresses7/185; it is not a cost-and-service success.
Seasonal-low and gradual-decline controls remain in the artifact, including their
three block-level denominators and service failures.

Neither challenger passes the declared dual-reference full-run gate on any of
the21 path labels: recent0/21, decay0/21. This is a descriptive negative result,
not21 independent replications or a test of real business demand. The same
underlying path supplies correlated segments, and repeated constant/zero controls
collapse to two unique paths. No policy or model is promoted. These traces are
now consumed; further tuning needs fresh evidence.

The next useful study is supply/review timing and intervention attribution,
followed by observed-sales realism. Increasing model complexity does not solve
the demonstrated retained-ownership problem by itself.
