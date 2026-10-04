# Stage 2 operations and acceptance

[Planning v1](CONTRACT_PLANNING_V1.md) is separate from frozen Stage 1. The
implementation includes demand eligibility, persisted forecast/backtest runs,
and inventory projection/proposals. All three slices and the Stage 3 planning
explanation adapter are integrated on `main`; the combined review was merged through
[PR 7](https://github.com/daniel-li2021/inventory-intelligence/pull/7).
The bounded synthetic Stage 2 milestone is complete; this does not establish
real demand accuracy or inventory cost/service performance. See
[current state](STATE.md), [validation guide](VALIDATION.md) and [active plan](PLAN.md).

## Fresh-database demonstration

Use a NEW disposable database/Compose project, not a previous test/demo volume.
Existing Stage 1 databases can install the final additive planning schema once
as owner; never reset a populated schema to run a demo. Python and runtime pins
are in the README. No new dependency is needed.

```sh
export COMPOSE_PROJECT_NAME=ii_stage2_demo
export POSTGRES_PORT=55437
docker compose up -d --wait
export FIXTURE_DATABASE_URL=postgresql://ii_owner:ii_owner_local@localhost:55437/inventory_intelligence
export DATABASE_URL=postgresql://ii_runner:ii_runner_local@localhost:55437/inventory_intelligence
python -m synthetic.planning_demo --format json > /tmp/stage2-demo.json
```

The demo inserts source fixtures through the owner, checks inventory through the
restricted runner, then persists five benchmarks and two proposals. It refuses
reloads rather than overwriting inputs. `--format markdown` produces a compact
report instead (choose the format before loading; rerun on a fresh database).
Full evidence lives in `planning.runs.context/result`; the concise report includes
run IDs for retrieval. [Verified summary](examples/stage2.md).

Expected independent outcomes: constant/zero choose naive on ties; weekly and
intermittent choose seasonal naive with zero errors on these deterministic
patterns. Each clean group has 14 shared selection origins for 7/14/28-day scores,
plus the separate final 28-day holdout. The blocked control has no selected model.
The complete supply proposes 12 pieces; the incomplete supply is `not_assessable`
with null order. This proves wiring and arithmetic on synthetic controls, not
model performance in a real business. No advanced model is justified by this toy
benchmark.

## Library entry points

Use an idle Psycopg autocommit connection for every result-producing function.
`run_forecast`, `run_benchmark` and `run_plan` each own one Repeatable Read
transaction, set UTC serialization, read immutable inputs and append a new run.
They never load fixtures or modify inputs. `demand.read_series` is read-only and
runs under its caller's transaction.

```python
from inventory_intelligence.planning_runs import run_forecast, run_benchmark
from inventory_intelligence.replenishment import run_plan

# All dates are datetime.date, and evaluated_at is an aware datetime.
run_forecast(conn, batch_id=batch, sku_id=sku, warehouse_id=warehouse,
             start_day=start, origin_day=origin, method="mean", horizon=7,
             code_version="reviewed-commit")
run_benchmark(conn, batch_id=batch, sku_id=sku, warehouse_id=warehouse,
              group="weekly", start_day=start, end_day=end,
              evaluated_at=evaluation_cutoff, code_version="reviewed-commit")
run_plan(conn, batch_id=batch, sku_id=sku, warehouse_id=warehouse,
         start_day=start, origin_day=origin, method="mean",
         reliability_run_id=inventory_run, supply_batch_id=supply,
         code_version="reviewed-commit")
```

Demand zero requires complete daily coverage AND available stock evidence, with
matching order-line count. Both source recording and observation time gate each
revision. Cancellations preserve gross accepted quantity; corrections revise it
only from the time they become known. No shipments are used as demand. Origin
training excludes the current business day and never compresses unavailable days.

Reservations are remaining, unshipped commitments from before the origin. Forecasts
cover new acceptances, assumed to require stock on acceptance day. Confirmed inbound
arrives at day start; forecast and reservations consume at day end. The new order
arrives after L FULL calendar days; lead 1 starts at the origin, so order arrival
is zero-based index L. Need covers the maximum safety deficit from L through H-1,
where H=L+review. Earlier shortages are explicitly reported and remain unsolved by
that order. Policy bounds H to 366; no estimated lead time or calibrated safety
stock is invented. Pack/MOQ rounding never forces an order when raw need is zero.

A historical passing inventory run is insufficient: cutoff/evaluation must match
origin, records must be known then, the key must be covered, and current Stage 1
SQL revalidation must still pass. V1 source owners retain their preservation duty;
the planner also stores the evidence actually read. Missing/incomplete inputs
append `not_assessable` with no proposal. Invalid API arguments and database errors
raise and roll back, rather than becoming missing-data results.

## Independent acceptance

On a fresh, separate disposable database:

```sh
export TEST_DATABASE_URL=postgresql://ii_owner:ii_owner_local@localhost:55438/inventory_intelligence
export DATABASE_URL=postgresql://ii_runner:ii_runner_local@localhost:55438/inventory_intelligence
# For a native database without Compose initialization only:
python -m tests.bootstrap
python -m unittest discover -s tests -v
```

`tests/planning_oracle.py` manually supplies demand/inventory/supply and exact
expected outcomes; it does not use the synthetic demand/demo generator. Checks
assert predictions, all scores, shared origins, holdout isolation, zero versus
gaps, cancellations/corrections, duplicate identities, late clocks, DST, raw
projection prefixes, order timing, MOQ/pack/ceil and large integer boundaries.
They assert persisted history, operational immutability, source revalidation,
restricted roles, and rollback. A separate downstream demo check verifies the
180-day groups through persisted PostgreSQL benchmark/proposal results.

Local final acceptance uses Python 3.12.14 / Psycopg 3.3.6 / PostgreSQL 17.6;
pinned CI uses Python 3.12.12 / PostgreSQL 17.9. Both environments are reported
explicitly. The schema/report/contract integration review is complete.

Remote final-code evidence: [CI run 36999887817](https://github.com/daniel-li2021/inventory-intelligence/actions/runs/36999887817)
on PR 5 head `f01a2e7` passed both jobs; the PostgreSQL job log reports 45 tests,
`OK`. Eligibility PR 3 and benchmark PR 4 also passed their pinned CI jobs.
That 45-test result is historical slice evidence. PRs 3/4/5 are now merged;
the later combined [main CI run 37044676872](https://github.com/daniel-li2021/inventory-intelligence/actions/runs/37044676872)
at `dcada27` passed all 76 tests and both jobs on the pinned environment.

Selection truth is frozen no later than holdout start, including source recording
and observation gates on revisions. Holdout truth alone uses the final evaluation
cutoff. This prevents a correction learned during holdout from changing model
selection even when its business day belongs to a selection fold. The repeated
[three-stage review](THREE_STAGE_REVIEW.md) includes this independent oracle.
