# Current project state

Updated: 2026-10-14 (America/Los_Angeles).

Integration mode: AUTO

Phase: full master roadmap implementation; final local acceptance/integration in
progress. Execution is sequential at the user's preference. Operational inputs
remain synthetic; real orders, confidential data and public/paid deployment excluded.

## Implemented and focused acceptance

- Existing Increments0–4,100-key/three-cutoff product archive, actual planner loop,
  immutable commitments/ETA/receipts, original Lab and original411 artifact hashes
  are retained. [Original acceptance](review/increments-0-4-acceptance.json).
- A/B: two independent dataset designs,30 exact key/cutoff cells,18 discovery
  triggers and65 saved reports on PostgreSQL17.9; rollback/retry/role/last-good/
  historical rerun controls pass. Priority factors are deterministic/cited; source-
  bound review notes never suppress facts or waive gates. [Replay](SYNTHETIC_REPLAY.md).
- C: declared supplier calendars/cutoffs/dated capacity, feasible quantity choices,
  common paid costs, assumed partial receipts and supplier-bound durable admission.
  A later arrival can reduce holding cost without changing service. [Guide](SUPPLIER_FEASIBILITY.md).
- D: donor-safe reservations/dispatch/transit/partial receipts/ETA history, complete
  network costs and conservation. Coast costs6763/5154/3533 retain an expensive-
  transport reversal5529>5154. Actual feedback6→0; new count4→overdue block→0 after
  known ETA. No implicit stock repair or residual purchase admission. [Transfers](TRANSFERS.md).
- E:16 independent paths,48 actual loops,144 reviews,39 blocked;2/8 accuracy-selected
  choices pass the decision gate. Losing/tied/undefined paths remain; no model or
  policy promotion. [Fresh evaluation](FORECAST_DECISION.md).
- F: bounded persisted evidence inspection above old aggregate caps preserves
  semantic reader gates. JIT candidate fails adoption (4.02% versus20% required);
  no planner change. [Engineering support](ENGINEERING_SUPPORT.md).
- Compact light workbench integrates supplier/transfer comparisons, readable evidence,
  local review/lifecycle and Evaluation.13 new browser controls pass at1280/320px;
  eight frontend state controls pass. Human/WCAG acceptance remains unverified.

## Remaining acceptance and gates

- Latest PostgreSQL17 full suite exercised365 tests:363 pass; two reconnection
  harness errors lose masked DSN credentials. Fix/recheck before accepting the suite.
  Reference runtime is PostgreSQL17.9 ARM64/Python3.12.14; exact pinned Python3.12.12,
  x86/two-date performance and public-runtime evidence remain separate gates.
- Next: final regression receipt, installed-wheel/legacy browser confirmation,
  canonical case studies/docs and verified AUTO integration/remote main.
- [ROADMAP](ROADMAP.md) owns this full assignment; [PLAN](PLAN.md) retains external
  continuity/hardware/human/public gates. Sustained HTTP and dense-producer acceptance
  are not established by page inspection or developer browser tests.
- Preserve unmerged planner commits55f4170/538d29d and their original branch.
  No real intake/authenticated multi-user executor, stochastic donor guarantee,
  global optimizer, commercial savings or operational exactly-once claim.

Read [index](README.md), [workflow](../CONTRIBUTING.md), [decisions](DECISIONS.md).
