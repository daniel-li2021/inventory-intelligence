# Independent readiness review — 2026-10-03

Started from fetched/pruned `origin/main` at `429cc71`, including the complete
Decision Lab. Three isolated reviews covered the operational chain, Lab/API/UI
and next-step evidence. The integration owner reviewed their diffs, audited the
research artifacts and simplified the portfolio entry point.

**Ready for a technical portfolio demonstration within the synthetic boundary.**
The project demonstrates production-style data integrity and read-only advisory
engineering. It does not establish production operations, real inventory benefit,
calibrated service, population forecast performance or business savings.

## Findings and changes

1. **Persisted Copilot evidence could contradict its own eligible demand.**
   Null/gapped training, constrained or late day records, wrong keys/origins and
   scores inconsistent with cited truth could be explained as valid historical
   evidence. Validation now checks contiguous whole-piece eligible evidence,
   context/source clocks, shared fold schedule and truth/actual agreement, plus
   forecast/planner training and policy horizon consistency. Invalid evidence
   errors instead of becoming a number. Blocked historical runs remain explainable.
   Null WAPE now explicitly covers absent scoring evidence as well as zero volume.
   [Core review and regression evidence](READINESS_CORE_REVIEW.md).
2. **A matching archive hash did not ensure a coherent Lab replay.**
   Rehashed archives could carry missing clocks, unreconciled other inventory
   keys, duplicate demand identities, mismatched supply manifests or broken
   planner links. A null inbound identity could pass validation then fail during
   calculation. The bounded replay now validates these semantics before any
   scenario. Corrupt evidence returns HTTP 503 across evidence/scenario routes.
   [Lab review and adversarial cases](READINESS_LAB_REVIEW.md).
3. **UI interpretation needed tighter boundaries.**
   Prefix planner shortages and periodic simulation backlog are now explicitly
   distinguished. Cost comparison states each scored/runoff accounting window;
   totals can cover unequal durations. Initial evidence failure replaces loading
   placeholders with unavailable/not-assessable state and a retry control.
4. **The portfolio entry point described an unfinished Stage 1.**
   README now leads with the business problem, complete architecture and a
   standalone no-database Lab quickstart. It surfaces quantitative negative
   results and routes detailed operations/contracts/history to their own docs.
   Contribution guidance now agrees with integration-owner publication and CI
   policy. Historical evidence remains preserved.

No operational engine, forecast/model grid, dependency, schema, frozen contract,
source dataset or existing benchmark outcome changed.

## Confidence beyond happy paths

New mutation regressions preserve otherwise plausible reports while changing
source evidence, clocks, identity, counts or plan links; Lab mutations recompute
both saved-input and archive hashes. This challenges semantic validity rather
than merely detecting a changed checksum. Existing hand-calculated core and
simulation oracles remain independent and unchanged.

Two additional audits independently derive every retained decision/intermittent
selection and promotion pass from the exact recorded scores, including declared
tie order, service floors, reference choice and null/zero-cost rejection. They do
not call the harness selectors or refit consumed holdouts. All recorded choices
and summary totals agree. The 480 decision and 5,544 intermittent results and
bundled replay are reused; no benchmark generation or model API call is needed.

Fresh combined acceptance and browser results are recorded in the integration
receipt at `docs/review/readiness-acceptance.json` after the focused changes.
They are local synthetic checks; remote CI, cloud operations and live business
inputs are separate claims.

## What is strong enough to freeze

- Stage 1 exact reconciliation, completeness/coverage gates, atomic append-only
  evidence and source/runtime role separation within contract-v1.
- Origin-aware demand eligibility, gross acceptance revision semantics, exact
  baseline forecasts and fail-closed prefix planning within planning-v1.
- Deterministic, read-only Copilot output, explicit historical UUID selection,
  exact citations and no current order authorization.
- Independent simulator conservation/event/cost oracles and frozen research
  protocols. Keep existing evaluations as consumed regression evidence.
- The bounded local Lab architecture and synthetic packaged replay after these
  fixes. More scenario controls or application layers need a demonstrated purpose.

## Remaining gaps and manual review

**Evidence explanation is not source attestation.** Copilot validates retained
consistency and arithmetic but, under its frozen no-replay/no-forecasting
contract, does not regenerate predictions, select raw revisions again or certify
a coherently rewritten archive. The Lab has stricter fixture-specific validation;
neither checksum is a signature. A general deterministic provenance verifier
would require a coordinated design boundary rather than a private contract edit.

**Business semantics remain unvalidated externally.** A business reviewer must
check acceptance versus sales, reservation/new-demand overlap, supplier calendars,
cutoffs, availability evidence, units and cost/terminal assumptions before any
real adapter or operational use. No external data has been imported.

**Portfolio usability still needs a human cold start.** An interviewer should run
the README from a clean Python 3.12 environment, inspect a blocked and delayed
case, and explain the two policies without assistance. Review accessibility and
small-screen layout manually; browser checks are bounded, not a complete audit.
Repository protection settings, PostgreSQL 17.9 remote acceptance and any future
hosted-service controls remain separate from local evidence.

**Research conclusions are bounded.** Three stochastic seeds, repeated controls,
correlated windows, reset stock and repeated selection/holdout supplier traces
cannot establish generalization or calibrated service. Four dual-reference
passes are one declining-demand path. Historical safety can survive demand
collapse; improved forecasts cannot prevent a shortage before the first receipt.

## Best next work

Investigate **feasibility and evaluation attribution first**, using existing
models, independent timing bounds, fresh demand/supply traces and costed initial
stock or warmup counterfactuals in a separate frozen protocol. Distinguish early
unavoidable missed fill from later policy failure; retain every failed case.
Only then test one bounded safety-retention challenger if decline remains a
material cost/service weakness.

A public observed-sales benchmark can add external evidence, but requires a
separate dataset/license/target boundary and cannot validate latent demand or
historical stockouts. Hosting adds accessibility rather than model evidence;
additional model complexity is not yet justified. The
[ranked investigation](READINESS_NEXT_STEPS.md) records scope, sources, risks and
stop/advance criteria. Continued implementation is conditional, not the default.
