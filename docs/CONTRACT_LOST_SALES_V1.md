# Research-only lost sales and matched backlog comparison — v1

Assigned under the continuing evaluation/decision-quality goal on 2026-10-03.
Identifier `lost-sales-research-v1`. Freeze this contract before implementing or
scoring the experiment. It is additive offline synthetic research, not a change
to decision-benchmark-v1 accepted orders, planning-v1, database/Copilot/Lab
interfaces or operational fulfillment. No purchases are executed.

## Meaning and observation boundary

A new demand value is an attempted purchase due today. In lost sales, stock not
available that day permanently loses the remaining attempted units. Later
receipts cannot repair the immediate or eventual fill of those units. There is
no backlog. Prior accepted commitments are unsupported and must be rejected;
turning an accepted obligation into a lost sale would change its contract.

The matched study deliberately assumes completed **attempted demand** is captured
in synthetic feedback, including unfilled attempts. Both kernels use identical
history plus attempts strictly before each review origin. This isolates demand
fulfillment semantics and preserves identical forecasts. It is not a model of
ordinary censored sales feedback; real lost demand is usually unavailable from
sales alone. Censored feedback needs a separately frozen experiment, not an
unannounced method change. No public observed-sales data enters this study.

## Inputs and lost-sales interface

`inventory_intelligence.lost_sales.simulate(history, demand, *, method, on_hand,
lead_days, review_days, safety_qty=0, pack_size=1, moq=1, review_phase=0,
commitments=(), inbound=(), supplier_delays=(), holding_cost=1,
lost_cost=10, order_cost=0)` returns version, days, reviews, metrics, terminal
and assumptions. Use unchanged baseline forecast arithmetic plus zero diagnostic.
Nonempty contiguous history/attempts are nonnegative whole integers; missing,
negative, float and boolean quantities are errors. Seasonal history needs seven
days. Stock/safety are nonnegative, lead/review/pack/MOQ positive, phase in [0,R),
horizon H=L+R <=366. Nonempty commitments are rejected.

Initial inbound has unique `{id,arrival_day,quantity}` rows with positive pieces
and day inside [0,N), known initially. All outstanding quantities contribute to
position even when their receipt is later than a protection target. The complete
hidden delay trace has one nonnegative value per possible review across scored
and runoff dates; empty means no delay. Index by absolute calendar review slot,
including slots with no order. Cost rates accept nonnegative int/Fraction only.
The kernel excludes acquisition; the study separately pays every owned piece.

## Daily timing and conservation

1. Receive due initial inbound and previously placed orders at day start.
2. On t=phase+kR before today's attempts, forecast H from completed attempts only.
   Target = sum(forecast)+safety. Position = on_hand+all outstanding quantities.
   Need=max(0,target-position); positive order=pack*ceil(max(ceil(need),MOQ)/pack).
   Order arrives at t+L+hidden_delay[t//R]; policy cannot see hidden realized delays.
3. Observe today's attempts; fill min(on_hand,attempts), permanently lose the rest,
   then append today's attempts to completed history. No same-day receipt from
   a new order (lead >=1), no later fulfillment of lost units.
4. Charge h*ending stock + p*new lost units + K*positive order.

Append exactly L+max(declared delay)+R runoff days. No new attempts, forecasts,
safety replenishment or orders during runoff; receive the outstanding pipeline
and charge holding. Fail on residual pipeline. End backlog is explicitly zero.
Conserve initial stock+receipts=served+ending stock; attempts=served+lost. Keep
whole-piece daily state, lost events, receipts, orders and exact cost components.
Zero-demand fill is undefined; empty shelves without attempted misses are not
shortages. Complete-cycle service counts cycles with no newly lost units.

## Predeclared paired experiment

Fresh seeds 9101/9127/9181, families constant/weekly/zero/lumpy/pause-recovery/
cessation. Each has 56 prior-history dates, 56 paid warmup dates and 28 score dates.
Constant=3, weekly=0..6 repeated, zero=0. Lumpy draws `(0,0,0,0,0,2,8,16)` with
its own seed namespace. Pause/recovery and cessation use random 1..5 base values;
pause at absolute dates98..118 then recovery, cessation from absolute date112.
Prior history/warmup/score slices come from one 140-day generated path.
Repeated deterministic controls are labelled separately from distinct paths.

Supplier paths use an independent namespace. For variable supply, shuffle
blocks `(0,0,1,1,2,4)` into absolute seven-day review slots. All zero is the fixed
reference. Trace prefixes include a four-day delay; both kernels get the same
appropriate complete prefix. Hidden supply is not indexed by order count.

Use mean/seasonal-naive, safety0/6, lead2/5, review7, phase0, initial stock10,
pack2/MOQ4, no initial inbound/commitments. All6*3*2*2*2*2=288 semantics pairs /
576 logical arms. Cache identical physical simulations and report distinct demand,
supplier and physical counts. No tuning, selection, policy promotion or confidence
claim. These new synthetic traces are consumed after viewing the first outcome.

Initial stock and every placed order cost2 per piece, charged at ownership/order
placement, not free receipts. h=1, setup2, backlog10 per ending piece-day in the
unchanged backlog kernel. Lost-unit penalty is10 in the lost kernel; also reprice
its exact retained events at40. Repricing adds no physical simulation and is not
an independent replication. Penalities have different units: unit-day for an
owed backlog versus unit once for a permanently lost attempt. Neither is retailer
profit or interchangeable economic valuation.

All arms account over the same100-day physical window:84 demand dates plus16
settlement dates. Extend each native settled run with holding of residual stock,
no salvage credit. Separate paid warmup, score and settlement costs/state. Score
new demand only on dates56..83: four complete cycles and28 dates. Use common
**new-demand shortage-free cycles** for paired service, based on newly unmet
attempts in either kernel. Native backlog cycle service also counts old debt;
record that distinction rather than silently calling it the paired measure.
Eventual backlog fill settles obligations; eventual lost-sales fill equals
immediate fill, never one unless all attempts were actually served.

Report full purchased pieces/orders, first action, warm boundary stock/backlog/
pipeline, lost/unmet units, immediate/eventual fill, score service and both cost
valuations. Paired costs are conditional counterfactuals, not a claim the same
business can cancel accepted promises. If lost units>0, report the algebraic
lost-unit penalty at which paid full lost-sales cost equals backlog full cost
with its fixed backlog rate; undefined when lost units=0. Negative/equal threshold
is retained, not clipped into a desirable business result.

## Acceptance and artifacts

Independent hand calculations cover day-zero miss not later restored, late
receipt, initial inbound, identical first forecasts but different subsequent
orders, packs/MOQ, phase/delay indexing across zero orders, no future observation,
zero nulls, exact costs, physical/attempt conservation and paid common settlement.
Reject accepted commitments, incomplete delays and malformed inputs.

Freeze protocol/generator before scores; implement and validate kernels/oracles
before fresh experiment. Publish full synthetic inputs, source/input/trajectory
hashes, exact trajectories and paired denominators. A separate saved-artifact
check must reconcile event/receipt quantities, paid costs, unchanged forecasts,
matched calendars and repricing without refitting or replaying the experiment.
Purposeful rehashed mutations must still be detected. Historical backlog source,
contracts/results and operational interfaces remain byte-for-byte unchanged.
