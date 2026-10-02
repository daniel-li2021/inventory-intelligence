# Verified synthetic Stage 2 demo

Executed 2026-10-02 on fresh PostgreSQL 17.6, Python 3.12.14, Psycopg 3.3.6.
Raw report: `python -m synthetic.planning_demo --format json`. Results are persisted
in PostgreSQL; run IDs vary and are intentionally omitted here. Synthetic inputs only.

| Group | Status | Selected baseline | Included / excluded selection origins |
| --- | --- | --- | --- |
| constant | assessable | naive | 14 / 0 |
| weekly | assessable | seasonal_naive | 14 / 0 |
| intermittent | assessable | seasonal_naive | 14 / 0 |
| zero | assessable | naive | 14 / 0 |
| blocked | not_assessable | — | 0 / 14 |

For the weekly group, every horizon has naive MAE 3, bias +3, WAPE 3/4;
mean MAE 12/7, bias 0, WAPE 3/7; seasonal-naive MAE/bias/WAPE 0.
Zero demand has MAE/bias 0 and WAPE null. WAPE is a ratio, not a percentage.
The same exact weekly scores hold on the separate 28-day holdout.

| Supply | Result | Order pieces |
| --- | --- | --- |
| complete | assessable | 12 |
| incomplete | not_assessable | — |

Complete supply: on hand 10, reservation 3 on day 1, confirmed inbound 5
on day 2, forecast 4/day for 5 days, lead 2 full days, review 3 days, safety 2.
Balances without order: **3, 4, 0, −4, −8**. Maximum post-arrival safety deficit
is 10 pieces. MOQ 10 / pack 6 gives **12 pieces**, arriving at day 3 start.
Balances with order: **3, 4, 12, 8, 4**. Pending inbound 100 contributes zero.

Incomplete reservation coverage yields `not_assessable` with null order and
null projection. Previous results remain immutable. Safety is a declared policy.
Implementation awaits integration acceptance; this example does not mark Stage 2 complete.
