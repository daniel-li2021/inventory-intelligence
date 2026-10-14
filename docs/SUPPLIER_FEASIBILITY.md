# Feasible synthetic supplier decisions

The additive `supplier-feasibility-v1` contract gives the saved actual planner
proposal, no action and an exact pack/MOQ alternative a source-bound supplier
promise. It preserves the original nominal-only `one-review-contrast-v1` and all
retained source archives. The planner remains advisory; these are locally declared
synthetic commitments and simulated business outcomes, not real supplier promises.

## Source and feasibility contract

A profile explicitly declares synthetic-only scope, supplier/version/key identity,
the known business day, distinct order/receipt weekdays, supplier-local cutoff
minute, and at most 33 dated dispatch capacities with reserved pieces. Pieces and
minutes are integers, never booleans or floats. Reserved capacity is external to
this local journal. Profiles are content-addressed; the comparison binds the
profile digest, original report/input digest, order minute and receipt scenario.
An admitted supplier/version/key identity cannot later name different profile bytes.
The profile is a separate declared synthetic source, not a fact reconstructed from
an existing planner archive.

An order before the cutoff can use the current ordering weekday. At or after the
cutoff it waits for the next ordering weekday. Calendar-day saved lead then advances
to the next permitted receiving weekday. Capacity must be explicitly present for
that acceptance day and cover the whole quantity after external reservations.
Exhaustion blocks the arm; it does not silently allocate another day, expedite,
truncate or split an order. A missing/future/wrong-key profile, missing capacity or
out-of-window promise cannot produce executable quantities/costs. Each infeasible
arm returns null outcomes with its reason. Compatible no-action outcomes remain
available when the underlying inventory/demand/supply evidence is assessable.
Missing operational evidence still blocks the entire comparison, including no
action. The original nominal contrast cannot be admitted as a supplier decision.

The example profile is explicitly a demonstration assumption: ordering Monday to
Friday, 17:00 cutoff, receiving every day, dated capacity 12 pieces. Calendar
controls additionally exercise weekday-only receiving. Supplier-local date/minute
is a declared input; this slice does not infer time zones or convert UTC timestamps.

## Outcomes, admission and feedback

`decision_contrast.compare(..., supplier=profile, order_minute=540)` evaluates each
feasible arm using its promise and the existing FIFO kernel over the same 33 paid
days. Initial stock, confirmed inbound and purchased pieces are paid, with the
same holding/backlog/setup economics. An optional `deliveries` mapping gives each
arm a declared future full or partial receipt scenario. Positive receipts must sum
exactly to that arm's order, use distinct chronological dates on receiving weekdays,
occur no earlier than the promise, and remain inside the common paid window.
These are assumed synthetic outcomes; alternative paths do not establish a policy
winner or an actual supplier update. The comparison exposes every daily quantity,
complete cost component, inventory exposure, service ratio and infeasibility.

`Journal.admit_supplier` revalidates the catalog and recomputes a feasible selected
arm. It ignores assumed outcome paths when admitting: only the bound quantity and
earliest feasible promise become the durable commitment. The natural source/key/day
decision identity prevents admitting two different choices for the same review.
An immediate transaction also sums previous journal allocations for that supplier
and acceptance day; multiple locations cannot reuse the same declared capacity.
An identical admission is idempotent; conflicting admission or overcapacity leaves
history untouched. Admission represents a local synthetic capacity reservation
for the calendar acceptance day, not an observed external supplier confirmation.

The existing append-only ETA/receipt events, coherent historical snapshots and
new-batch `publish_supply` projection then apply. Partial receipts conserve committed
pieces; future knowledge cannot rewrite earlier snapshots. Receipt events must not
precede the original feasible promise. A later ETA notification can revise expected
remaining inbound without changing original evidence. An early actual delivery
after the original promise can still occur after an ETA delay; the notification is
an expectation, not a rewritten physical fact. No source stock is silently updated.

## Independent acceptance and negative findings

[Frozen controls](examples/supplier-feasibility-controls-v1.json) preceded the new
implementation/outcomes. The calendar controls independently expect Friday before
17:00 plus lead two to arrive Monday with weekday receiving; Friday at 17:00 accepts
Monday and arrives Wednesday. An 18-piece order against 12 capacity blocks.

Saved April 6 Harbor controls retain the actual six-piece proposal and all original
source bytes. A full day-two receipt costs 16281; split receipts three on day two
and three on day four cost 16286 and reduce immediate fulfilled new demand from
18 to 17 pieces. A full day-five receipt costs 16373 and immediate fill falls to
12 pieces. All three eventually fulfil 18 new pieces and end with backlog 94.
No action costs 18039 and ends with backlog 100 in each comparison.

The cutoff counterexample matters: postponing the feasible six-piece receipt from
day two to day three reduces holding cost from 15 to 9, leaves immediate/eventual
fill unchanged at 18 pieces, and lowers total cost to 16275. Earlier arrivals are
not universally cheaper. These are arithmetic acceptance controls, not a fresh
efficacy study or commercial savings estimate.

Focused validation: eight new supplier controls, seven retained contrast controls
and six retained journal controls pass (21/21). They include exact conservation,
strict malformed/future/missing evidence, blocked arm/null outcomes, source digest
preservation, forbidden early receipts, capacity allocation, concurrent idempotency,
conflicting admission, append-only storage, partial receipts/ETA changes, reopen and
historical reproducibility. [Acceptance receipt](review/supplier-feasibility-v1.json).

```sh
PYTHONPATH=src python -m unittest tests.test_supplier_feasibility tests.test_decision_contrast tests.test_workflow -v
```

## Limits and stopping boundary

This slice supplies bounded single-review feasibility and durable synthetic
feedback. Supplier calendars/capacity are declared synthetic inputs, with no
authenticated supplier adapter, external confirmation, currency valuation,
cancellation/rebooking optimization, independent production executor or real
purchasing. Automatic replanning still requires explicit fresh operational source
admission; a journal receipt alone is not stock truth. PostgreSQL reference,
public-runtime, human usability and real operational security gates remain separate.
