# Donor-safe synthetic transfers

`donor-safe-transfer-v1` adds a bounded one-SKU/two-location workflow to the existing
workbench. It consumes two assessable saved plans from the same catalog/cutoff,
explicit synthetic transport terms, and a source-bound supplier profile for any
purchase. Missing/contradictory location evidence yields null outcomes. It does
not convert a short-prefix location imbalance into authorization to dispatch.

## Protected stock and compatible economics

Simulate the donor without purchases over 28 declared demand days and five common
paid closure days, including every open obligation and confirmed receipt. The
available quantity is the minimum of opening stock minus safety and every daily
ending stock minus safety, bounded below by zero. Any donor backlog makes surplus
zero. Dispatch removes the full transfer from opening physical stock. Transport
needs positive full-day transit and explicit capacity, setup and per-piece costs.

Compare no action, purchase-only and transfer-before-purchase on the same demand,
reservations, receipts and 33 paid days. The residual purchase uses the existing
prefix projection with the transferred inbound; supplier calendars/cutoffs/capacity
must produce a feasible promise. This is a one-review heuristic, not a global
optimizer or repeated-policy ranking. Purchases, initial stock, confirmed external
inbound, holding, backlog, setup and transport are included. Transferred goods are
not purchased a second time. Each arm checks network conservation and unchanged
donor immediate service; missing purchase terms withhold that arm's outcomes.

The [frozen independent arithmetic](examples/transfer-controls-v1.json) predates
implementation: donor 30/recipient 0, five days of demand1/3, transfer 12, lead2,
pack6/MOQ6 gives protected surplus23, purchase-only 18 and residual6. Common paid
costs are 5545 / 1125 / 667; donor fills5/5 in every arm. The transfer network has
36 paid incoming pieces,20 consumed and 16 ending pieces. Concurrent12-piece
reservations cannot both consume23 pieces; excessive/early receipts and failed
transactions leave the previous state intact.

On the [fresh coast catalog](review/generalization-v1/generalization-two-site-v1.json.gz),
May4 donor stock 80 with declared1/day has protected surplus51. Transfer12 yields
costs 6763 / 5154 / 3533, recipient immediate fill3/28 / 9/28 / 15/28, donor 28/28 in
all arms. Expensive transport reverses the choice: transfer 5529 versus purchase 5154.
[Saved comparisons and arithmetic audit](review/transfer-comparisons-v1.json) retain
both outcomes. These are finite declared-demand synthetic costs, not savings or
unseen efficacy. The original April donor 80 with declared4/day is correctly blocked.

## Durable lifecycle and feedback

`TransferJournal.reserve(catalog, ...)` validates the catalog and recomputes the
comparison before atomically reserving donor stock. Natural cutoff/item/location
identity makes an identical retry harmless and a changed choice conflicting.
Reservations and all events are immutable SQLite rows. One source basis cannot
be reused beyond its protected surplus, including after receipt. A new donor basis
requires explicit reconciliation; a changed source cannot silently reset spent stock.
The sandbox allows 128 transfers/256 events, serializes writes, and preserves history
on reopen, concurrent admission, invalid events and transaction failure.

Dispatch must match the protected origin; late dispatch needs replanning. Supply
projection retains that original reservation date, so an undispatched late reservation
blocks as overdue instead of being silently moved to the new cutoff. It moves
reserved pieces to in-transit, with no recipient stock until an explicit receipt.
Partial receipts retain exact remaining pieces. Receipts cannot precede dispatch
plus original transit; overreceipt/backdated events reject. ETA notices retain their
knowledge date and cannot precede feasible transit. Historical snapshots expose the
then-known reservation, transit, receipt and ETA; future notices do not leak backward.

Transfer reservation allocates donor pieces only. A residual purchase shown in the
combined comparison requires **separate supplier admission**; the transfer button
does not allocate supplier capacity. Default wheel mode is read-only. Only the
explicit same-origin loopback sandbox enables synthetic writes.

`TransferJournal.supply_effects`/`publish_supply` separately stage known donor
reservations and recipient in-transit inbound. The synthetic owner must explicitly
supply complete external obligations/inbound and policy. New supply batches never
modify stock sources or earlier reports. Dispatch/receipts require independently
reconciled new stock evidence; the journal never silently adjusts an inventory table.
SQLite/PostgreSQL publication is not a cross-database atomic production handoff.

Actual PostgreSQL feedback control: a coast proposal 6 becomes0 after confirmed
transfer 12; after partial receipt5, an independent stock 6 count proposes4 without
inbound. Remaining7 with an overdue promise blocks planning; an origin-known revised
ETA then yields0. Original proposal/source/history remain unchanged. No real dispatch,
purchasing, operational exactly-once or stochastic donor-service guarantee is claimed.

## Reproduction

```sh
python scripts/run_local_demo.py --port 8040 --catalog docs/review/generalization-v1/generalization-two-site-v1.json.gz --journal output/new-transfer-demo.sqlite
python -m unittest tests.test_transfers tests.test_decision_options_api -v
python -m unittest tests.test_transfer_feedback -v
```

Database tests use fresh disposable owner/restricted-runner connections from
[VALIDATION](VALIDATION.md). The feedback test creates/drops only its own database.
In the workbench choose May4, coast SKU0/site0 → Compare. Select donor site1,
quantity12/transit1/capacity12 → Compare transfer before purchase. Reserve → Dispatch
May4 → Receive5 May5 → Receive7 May6. Inspect May4/5/6 history and exact exports.
Choose a fresh journal path for a fresh experiment; no automatic reset is provided.
