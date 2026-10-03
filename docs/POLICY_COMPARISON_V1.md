# Policy comparison v1 — frozen before outcomes

This offline synthetic experiment holds forecasts, initial stock, known prior
commitments, known inbound, review calendar and costs constant. It varies only
the scored ordering rule. It neither executes purchases nor replaces planning-v1.

## Three rules

- `periodic_up_to`: existing simulator inventory-position order-up-to. At every
  review, target is the L+R forecast plus safety plus known future commitments;
  position is stock + all outstanding supply − due backlog.
- `periodic_sS`: same reviews, forecast and target; order only when position is
  at or below the L-day forecast plus safety plus commitments strictly before
  the lead boundary. This is a periodic threshold rule, not continuous review.
- `prefix_projection`: calls the unchanged planning-v1 `project` arithmetic.
  Due unfilled backlog becomes a current-review carryover reservation; known
  future commitments retain their due dates. Original backlog identities, kinds
  and due days remain in the receipt and simulator FIFO queue. Confirmed pending
  supply uses its promised arrival date. Whole-piece ceiling, MOQ and pack
  rounding are identical across rules.

The prefix adapter exercises arithmetic in a closed loop, **not** the operational
`run_plan` source/reliability gates or its treatment of overdue source records.
It does not certify an operational proposal. Missing supply or hidden nonzero
delays are outside this protocol and rejected by the wrapper. The kernel's
private ordering hook receives copied origin-known inputs, never future demand
or hidden realized arrival dates. Default simulator callers remain unchanged.

## Frozen inputs and accounting

Generator version `policy-comparison-v1`, seeds 7301/7709/8027. Training 84 days,
scored demand 56 days; stochastic lumpy and temporary-pause families use all
three seeds. Constant, weekly, zero and known-late-inbound controls use one
label each: ten scenario labels. L=2, R=7, phase=0, stock=10, pack=2, MOQ=4;
late-inbound control has 80 confirmed pieces arriving day 12, plus a known
8-piece prior commitment due day 4. Other scenarios have no prior/inbound.

Cross fixed `mean` and `seasonal_naive` with safety 0/4 and all three rules:
120 logical arms / 80 paired contrasts against `periodic_up_to`. No fitting,
selection or promotion. Training and forecast updates use completed demand
only, identically across policies. Exact generator definitions live in the
hashed benchmark source. All zero demand makes fill undefined.

Backlog semantics and receipt→prior fulfillment→review→new demand event timing
are unchanged. Common fixed nine-day settlement uses the original simulator
backlog-clearing rule for every arm, with no forecasts or safety. It is an
accounting closure, not a continued policy experiment. Charge initial stock,
all confirmed inbound and every purchased piece at 2 units; holding 1 per
piece-day, backlog 10 per piece-day, order setup 2, throughout scored days and
settlement. Residual stock has zero credit. Report scored costs separately from
full acquisition+exposure+setup costs; no free starting inventory.

## Evidence and interpretation

Archive exact input/trajectory hashes, origin forecasts, ordering receipts,
FIFO fulfillment, terminal conservation and full cost breakdown. Assert equal
forecast receipts across policies before comparing immediate new-demand fill,
on-time prior service, complete-cycle service, backlog and costs. Publish
signed paired differences and null denominators, not additive shortage causes,
statistical significance or profit claims. Deterministic controls and correlated
cycles are not independent samples. Changing policy is not a forecast improvement.
No operational policy or model is promoted from this finite synthetic grid.
