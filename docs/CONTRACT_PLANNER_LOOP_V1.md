# Synthetic operational-planner execution research v1

Frozen before implementation and outcomes. This additive research protocol runs
the real `run_checks`, `run_plan` and persisted planning-report validator. It does
not change planning-v1, accepted-order backlog semantics, source permissions or
the separate periodic simulator. No real purchase or operational inventory write
is authorized. Run only against a fresh disposable synthetic PostgreSQL database.

## Evidence and execution boundary

- Source owner inserts new immutable inventory, demand and supply batches at
  each review; it never updates/deletes an earlier source row. Natural event,
  order and reservation identities survive their new archive row IDs. Opening
  balance, posted movements and the independently maintained physical state
  must reconcile through the real Stage 1 SQL and restricted `ii_runner`.
- At local midnight: receive actual arrivals, apply supplier notifications known
  now, publish evidence, run reliability, run the operational planner, reload and
  validate its persisted report, then admit one decision for this scenario/date.
  Receipt precedes review. Acceptance/fulfilment follows review during the day.
  Local dates use America/Los_Angeles calendar midnights, including DST.
- A decision binds the exact origin, SKU/warehouse, demand/supply batches, training
  start, method and reliability run. Its identity uses scenario/date, rather than
  a random planning UUID. Rerunning a planner cannot execute a review twice.
  Blocked and assessable-zero decisions are distinct; neither creates an order.
  The in-memory research journal has one caller and is not a durable commercial
  executor or an exactly-once guarantee across processes/crashes.
- Every positive proposal becomes a synthetic confirmed inbound of that exact
  quantity and promised date. A separate hidden physical supplier schedule
  controls receipt. The planner sees only the promise and subsequent notification,
  never future actual receipt dates or future demand.
- A notification at the first missed promise declares a revised ETA in a new
  immutable batch. Without a notification the old ETA remains overdue and blocks
  planning. This experiment assumes a truthful supplier update when enabled; it
  does not establish supplier authenticity or model arbitrary revisions.
- Prior accepted orders consume FIFO stock before new acceptances. Remaining
  backlog keeps its original due date; it is never re-dated to bypass the planner.
  A day with any unfilled new acceptance is marked `stockout`, even when accepted
  quantity is known. The existing training eligibility gate therefore blocks
  until that day leaves the rolling 28-day window. Unfilled historical backlog
  is not silently converted to a zero demand, lost sale or fulfilled order.
- Rolling training contains only 28 completed days known at origin. The source
  archive may retain earlier completed days. Current/future days are absent.
  The first 28 days are informational demand history, not a simulated or free
  warmup state. Starting stock is explicitly purchased at the scored start.

## Frozen bounded controls and economics

Start 2026-03-07, crossing the March 8 DST transition. Nine scored days with
reviews on days 0/3/6, then five common no-demand/no-order closure days. No review
in closure. Maximum configured extra delay is three days, so every admitted
order arrives by the common end. Terminal stock/backlog are retained and reported;
closure does not erase debt or grant receipts. This is a manual control suite,
not an independent random-path efficacy benchmark or a policy ranking.

Default history and daily scored acceptance: 3 pieces. Lead 2 local calendar days,
review 3, safety 2, pack 6, MOQ 10, mean forecast. Initial stock 10 unless stated.
Cost units: purchase 2/piece (initial plus all ordered units), holding 1/piece/day,
backlog 10/piece/day, setup 2/positive order. End-of-day stock/backlog is charged
through score AND closure; costs are undiscounted, with no terminal salvage credit.
Immediate fill is new demand filled that day / all scored acceptances. Eventual
fill includes later FIFO fulfilment through common closure. Zero demand has null
fill. Cost components and phase subtotals must reconcile exactly.

The following independent outcomes are hand-calculated before running code:

| Control | Review proposals (day 0/3/6) | End stock by scored day | End backlog by scored day | Immediate / eventual | Terminal stock/backlog | Full cost |
|---|---|---|---|---|---|---|
| clean | 12/12/12 | 7,4,13,10,7,16,13,10,19 | 0,0,0,0,0,0,0,0,0 | 27/27; 27/27 | 19/0 | 292 |
| zero: history/acceptances 0 | 0/0/0 | 10,10,10,10,10,10,10,10,10 | 0,0,0,0,0,0,0,0,0 | null; null | 10/0 | 160 |
| cold shortage: initial 0 | 12/blocked/blocked | 0,0,3,0,0,0,0,0,0 | 3,6,0,0,3,6,9,12,15 | 6/27; 12/27 | 0/15 | 1319 |
| spike: first demand 12 | 12/blocked/blocked | 0,0,4,1,0,0,0,0,0 | 2,5,0,0,2,5,8,11,14 | 17/36; 22/36 | 0/14 | 1221 |
| missing: day-0 inbound completeness false | blocked/18/blocked | 7,4,1,0,0,10,7,4,1 | 0,0,0,2,5,0,0,0,0 | 22/27; 27/27 | 1/0 | 167 |
| notified delay: first order +3 days | 12/12/blocked | 7,4,1,0,0,16,13,10,7 | 0,0,0,2,5,0,0,0,0 | 22/27; 27/27 | 7/0 | 235 |
| unannounced delay: first order +3 days | 12/blocked/blocked | 7,4,1,0,0,4,1,0,0 | 0,0,0,2,5,0,0,2,5 | 17/27; 22/27 | 0/5 | 453 |

Every control must also check physical conservation, FIFO fulfilment, integer
quantities, reliable snapshots, persisted proposal identity, no future leakage,
immutable earlier inputs, and day-3/day-6 blocked reason/availability evidence.
Equivalent fresh-database executions have identical normalized daily/actions/
cost outputs; UUIDs, source namespace and wall-clock creation times differ.

## Verification and retained evidence

Freeze this protocol and machine-readable hand expectations before implementation.
Commit implementation/oracles before generating the saved research archive.
Targeted tests use the actual restricted-runner PostgreSQL path, with separate
owner source inserts. Include duplicate admission (including a new planner UUID),
wrong-origin/batch binding, contradictory persisted quantity, hidden future demand
and delay, withheld notification, completeness recovery and unchanged old batches.
Do not claim a blocked planner as an assessable zero or relax a source contract to
make this experiment look successful.

The archive retains full persisted planning/reliability reports, source identities,
physical movements, supplier notifications, executions and daily costs. Bind code,
protocol and expectation hashes to complete Git snapshots. A saved-only audit must
check manual outcomes, conservation and cost/service denominators without calling
the database, forecast, planner or simulator. Source equality/declared provenance
does not authenticate real business evidence. This slice establishes synthetic
execution behavior; any subsequent policy change needs new frozen demand/supply
traces and a fresh paid comparison before claiming decision improvement.
