# Synthetic physical-count evidence — v1

Assigned under the continuing domain/evidence goal on 2026-10-03. Identifier
`physical-count-evidence-v1`. This additive pure offline research contract does
not change Stage1 rules/schema, operational planner eligibility, accepted orders,
Copilot/Lab or inventory sources. Freeze this boundary before implementation.
No database writes, automatic adjustments or real company counts are authorized.

## What the comparison can establish

Ledger/snapshot consistency is not physical warehouse truth. Compare a declared
assessable synthetic system-stock observation with separately identified physical
counts at one `(sku_id,warehouse_id)`/business cutoff. This layer validates the
provided evidence and a strict corroboration policy; it does not independently
run Stage1 SQL, authenticate source signers, prove observer independence or verify
that the actual warehouse was frozen. Those assertions remain source attestations.

Whole pieces only (`uom=each`). Missing, incomplete, ambiguous, future or conflicting
evidence must not become zero, a match or an approved adjustment. A first count,
even when it equals the book quantity, is unconfirmed. At least two distinct
source-declared blind observers and agreement of **all** valid count quantities
are required; same-observer recounts do not establish independent corroboration.
A third conflicting count cannot be hidden by majority voting or last-row wins.

## Inputs and clocks

`inventory_intelligence.physical_count.evaluate(system,manifest,counts,
*,evaluated_at,adjustment_reviews=())` consumes JSON-shaped observations and
returns a new report; it never mutates inputs. `evaluated_at` is an aware ISO8601
instant (invalid request clock raises ValueError). Source clocks must also be
aware; malformed source payload produces `not_assessable`/null conclusions.

System fields are exactly: `source_system,record_id,sku_id,warehouse_id,as_of,
observed_at,status,uom,quantity`. Status must be `pass`; quantity is a nonnegative
integer. This status is a declared synthetic upstream result, not newly verified
ledger reliability. Preserve source identity and both business/observation time.

Manifest fields are exactly: `source_system,session_id,sku_id,warehouse_id,as_of,
freeze_start,freeze_end,observed_at,uom,coverage_complete,frozen,expected_rows`.
Flags must be boolean True; expected raw rows a nonnegative integer equal to
len(counts). Freeze covers the requested cutoff and every actual count timestamp.
Manifest observation occurs after freeze end and all included row observations;
manifest/system must already be available by evaluated_at. A future complete
batch cannot become known at an earlier historical evaluation.

Each count has exactly `source_system,count_id,session_id,observer_id,blind_count,
sku_id,warehouse_id,as_of,counted_at,observed_at,quantity,uom`. Strings are nonempty,
quantities exact nonnegative integers, blind flag boolean True. Natural identity
is `(source_system,count_id)`; identical and contradictory duplicate identities
both block, never silently deduplicate. All rows belong to the same declared
session/grain/cutoff/uom. Business count time is in the frozen interval and not
before as_of; observed_at >= counted_at and <= manifest.observed_at. Unexpected
scope, incomplete coverage or a bad row blocks the entire single-key comparison.
This contract does not normalize moving stock between count timestamps.

## Report and evidence confidence

Report quantities `system_quantity,physical_quantity,variance_quantity` are
conclusions, not raw-data replacements. A blocked comparison leaves all three
null. Valid but uncorroborated evidence retains system quantity only; physical
quantity and variance remain null. Raw count quantities remain in evidence rows.

- `not_assessable`: invalid/incomplete/missing source context; confidence `none`.
- `recount_required`: fewer than two distinct observers (`none`/`single_observer`)
  or disagreeing quantities (`conflicting`). No physical conclusion.
- `confirmed_match`: at least two source-declared blind observers agree,
  physical-system=0; confidence `corroborated`.
- `confirmed_variance`: same corroboration, nonzero physical-system; confidence
  `corroborated`. Signed variance preserves shortage/surplus without classifying
  its cause as shrinkage, damage, theft or receiving error.

These are categorical evidence levels, not measured probabilities or warehouse
truth guarantees. Return sorted findings/reasons and source references, exact raw
count evidence, evaluated clock, canonical complete-input SHA256 and deterministic
run ID. Keep source file byte hashes separately in the experiment provenance.

## Adjustment evidence without execution

Only confirmed nonzero variance creates a read-only candidate proposal. Proposal
ID is SHA256 of canonical JSON `{system,manifest,counts}` with counts sorted by
natural identity. Full source facts/clocks are bound, not only the delta. Exclude
evaluation time and approval rows so the same facts can be reviewed later without
changing identity. Reordering count input does not change the proposal; a source
version, quantity, scope or clock change does.

A candidate records before/count quantities and signed delta, never changes book
stock. Adjustment status is `no_proposal`, `review_required`, `approved_evidence`,
`rejected` or `not_assessable`. `approved_adjustment_quantity` is null unless one
valid explicitly approved review binds exactly to the proposal. Even then this
field is advisory evidence, not an executed write or verified warehouse outcome.

Each review has exactly `source_system,review_id,proposal_id,reviewer_id,decision,
reason_code,reviewed_at,observed_at`. Decision approve/reject; reason_code one of
`shrinkage,damage,count_correction,receiving_error,unexplained_variance`. A reason
is source-declared classification, never inferred from the sign. Reviewer differs
from every count observer. Reviewed time >= all evidence observation times,
observed_at >= reviewed_at, both <= evaluated_at. Natural review identities are
unique; more than one selected review is ambiguous and requires reassessment.
Do not select the latest or silently ignore contradictory/late/unbound reviews.
An invalid review blocks approval while retaining independently confirmed count
conclusions. Reviews without a current proposal cannot authorize a quantity.

## Frozen finite controls and acceptance

Independent synthetic controls include book100/count100 corroboration,100/96
shortage,100/104 surplus, clean zero, missing/unassessable system, partial scope,
missing/duplicate/foreign counts, observer reuse, count conflict/majority, no
blindness, unfrozen inventory, incompatible count clocks, late batch/row/review,
naive timestamps, missing/float/bool quantities and stale proposal binding.
Approved/rejected/absent/ambiguous review evidence is separately measured.

Assert exact quantities/status/reasons and clean controls; counts alone do not
prove acceptance. Verify no source mutation, row-order invariance, stable proposal
identity across later evaluation, complete-source version binding and future
information rejection. Purposeful rehashed metadata/quantity mutations must still
be caught by semantic validation; hashes are integrity checks, not authenticated
source provenance or substitutes for corroboration.

Publish synthetic cases and exact expected outcomes, source/config/code hashes,
input-to-report lineage and reproducible output/acceptance receipts. Reuse saved
results only when pinned source bytes and semantic reconciliation agree; preserve
last good outputs on error. No probabilistic confidence calibration, production
truth, statistical shrinkage rate, operational promotion or real adjustment.
