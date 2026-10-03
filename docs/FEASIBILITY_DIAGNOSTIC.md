# Startup feasibility and common accounting diagnostic — v1

Protocol frozen 2026-10-03 before this diagnostic's outcomes were generated.
Identifier `lab-feasibility-diagnostic-v1`. This is the first bounded slice of
[the next investigation](READINESS_NEXT_STEPS.md), using the existing synthetic
Lab replay. It is attribution and accounting sensitivity, not a new benchmark,
policy, tuning set or evidence of generalization. Frozen simulator, planner and
Lab interfaces and prior artifacts remain unchanged.

## Predeclared replay and accounting window

Evaluate the existing clean baseline, hidden supplier delay3, demand125%,
zero-demand and incomplete-supply controls with unchanged Lab defaults otherwise.
Reuse the bundled persisted archive; record its digest, source UUIDs, exact
counterfactual inputs and calculation identities. No database, model API,
external data, random generation or benchmark refit is required.

All assessable controls score days [0,28). Compare synthetic costs over the
common window [0,36): 28 scored days plus eight runoff days, sufficient for the
maximum declared lead2 + delay3 + review3. Preserve each arm's original scored,
runoff and total costs. For arms settled earlier, carry their terminal stock
with no new demand, supply or safety orders to day36, charging the same exact
holding rate per additional day. This is algebraically equivalent to extending
the simulator's no-demand, backlog-clearance runoff after all obligations and
pipeline have settled. Unsettled terminal backlog/pipeline or a common window
shorter than any arm's original window is an error, never truncation. Terminal
stock retains its original zero salvage/acquisition valuation.

Report scored costs, original runoff costs, extension holding cost, common
runoff and common total separately, with terminal stock and common-minus-baseline
deltas. This establishes equal exposure duration, not equal demand or comparable
commercial profit. No automatic selection or promotion is performed.

## Independent startup bound

Find the earliest *possible* arrival of a new policy order over every scored
review slot: min(review day + declared lead + hidden delay for that slot).
This includes slots with zero actual orders; it is a favorable evaluation
counterfactual and cannot use a candidate's later chosen first order. A later
review with a shorter hidden delay can arrive before the first review's order.
If no receipt can occur within scoring, the startup interval covers all scored
days. Ordering never sees the hidden delays or future demand.

Before that arrival, replay only initial stock, known confirmed inbound and
disjoint prior commitments. Respect old-backlog priority, then today's prior
commitments, then new demand. Receipts occur before obligations. Count new units
that cannot be immediately filled and prior units that cannot be filled on their
due day; later backlog fulfillment never repairs either count. Known inbound can
reduce the bound only when it arrives, not retrospectively.

For total new demand D and inevitable startup new misses U, immediate new fill
cannot exceed (D-U)/D; D=0 returns null. Report realized new misses before and
at/after the earliest possible receipt separately, plus their exact denominators.
Actual startup misses must equal the independently computed bound and total fill
must not exceed its ceiling. Retain infeasible and null-service controls in the
report. Later misses are not all forecast error: stock, packs, review timing,
safety, commitments and supply remain possible contributors.

## Acceptance and limits

Hand-calculated controls must cover FIFO prior commitments and backlog, timed
known inbound, shorter-delay later reviews, no review/no receipt inside scoring,
zero demand, exact rational holding costs and common-window rejection. Replay
regressions must preserve the baseline and hidden-delay original costs, keep
incomplete evidence null, and match extension cost to a longer no-demand ledger.

The bundled demand path and consumed holdouts cannot support fresh population
claims. Warmup/carryover, fresh independent demand/supplier traces, multiple later
origin blocks and declining-safety challengers remain separate future work. Stop
this slice after attribution and accounting checks; no additional model grid.
