# Current project state

Updated: 2026-10-29 (America/Los_Angeles).

Integration mode: AUTO

Phase: [Demand Planning MVP](DEMAND_PLANNING.md) and guidance/recovery validated
locally; [CI repairs](VALIDATION.md#documentation-and-retained-provenance) pass locally; owner acceptance pending.
Source push authorized October 29; deployment unassigned. Earlier synthetic core retains Functional Closure and the white Desk.

Render Free: [Blueprint/setup](../deploy/render/README.md) and [local receipt](review/render-free-v1.json)
serve one read-only Python/React demo, no database/secrets, GitHub CI-gated deploys.
[Public smoke check](review/render-public-smoke-v1.json): trusted TLS, health, 18 HTTP checks and brief browser journey pass.
Name: Inventory Intelligence; existing provider identity retained. Cold-start/capacity/account logs remain unchecked.

## Coherent platform

- Original Increments0–4,100-key/three-cutoff archive, actual planner controls,
  immutable purchase/ETA/receipt workflow, original Lab and 411 original artifact
  hashes remain intact. No consumed study was tuned or rewritten.
- A/B: two independent dataset designs pass 30 exact key/cutoff cells,18 discovery
  triggers and 65 actual PG17 reports. Immutable staging/version/replay/rollback,
  historical recovery, explainable factors/priority and local source-bound review
  integrate with the workbench; resolution never suppresses facts or gates.
- C: declared calendars/cutoffs/dated capacity, feasible quantities, no action,
  complete common costs, partial-receipt scenarios and durable supplier admission.
  Shared supplier/day contradictions cannot expand capacity; zero decisions remain
  bounded. Later arrival can lower holding cost without changing service.
- D: donor-safe reservation/dispatch/transit/partial receipt/ETA history, exact
  conservation, transport economics and actual planner feedback. Coast costs
  6763/5154/3533 retain an expensive-transfer reversal5529>5154; donor remains28/28.
  Feedback6→0; independent count4→overdue block→0 after known ETA. Original
  reservation dates/history remain unchanged; stock is never silently repaired.
- E:16 independent paths,48 actual loops,144 reviews,39 blocked;2/8 accuracy-selected
  choices pass the decision gate. Losses/ties/undefined service remain; no promotion.
- F: bounded persisted inspection above old aggregate reader caps preserves semantic
  gates. JIT candidate fails20% adoption gate (4.02% benefit); no kernel change.
- Compact light workbench integrates insights/evidence, feasible comparisons,
  journals, saved actual feedback and Evaluation. The wheel works offline without
  Node, database or model key; default mode is read-only, writes opt into loopback.

## Product design selection

- Owner selected white Desk; the isolated Brief alternative remains runnable.
  [Initial selection and validation](PRODUCT_DESIGN.md#selection-and-validation).
- Product-wide refinement adds compact findings, task-based sections, secondary
  filters, semantic badges and mobile navigation. 32 route/viewport cells,
  21 browser interactions, 10 frontend and 72 focused Python tests plus the installed
  offline wheel pass. All602 original backend/test/SQL/evidence files retain bytes.
  [Audit, before/after and limits](PRODUCT_DESIGN.md#product-wide-ux-refinement--october-15).
- [Demand Planning](DEMAND_PLANNING.md): additive local MVP; [validation](review/demand-planning-v1/receipt.json).
- [Guidance and recovery](PRODUCT_DESIGN.md#workflow-guidance-and-recovery--october-29): local task shortcuts, demand presets, explicit selection recovery and stale-export guards.

## Accepted evidence and remaining gates

- [Final functional audit](review/final-functional-audit-v1/receipt.json):126/126
  focused regressions, actual PG17 feedback and installed offline wheel pass.
  Equal-length evidence selections now have distinct bindings; reservations obey
  the event budget; dated demo transport versions allow later independent items.
  All477 existing evidence/control/research files retain baseline bytes.
- [Final receipt](review/full-platform-acceptance-v1/receipt.json):368/368 latest
  regressions on PostgreSQL17.9 ARM64/Python3.12.14, eight frontend controls,
  16 platform and 22 legacy browser controls, installed-wheel/source integrity.
  Initial two masked-DSN reconnect test errors are retained and corrected.
- [README](../README.md) now leads with value, demo, current UI and qualified results.
  [Six case studies](PLATFORM_GUIDE.md) retain the full journey and synthetic limits.
  Completed master narrative lives in Git; current O01–O25 audit belongs in KB.
- [ROADMAP](ROADMAP.md) retains independent product/reference acceptance;
  [PLAN](PLAN.md) retains exact Python3.12.12/x86/two-date, sustained serving,
  dense-producer/whole semantic-reader and sustained public-runtime gates. Developer
  checks do not establish human comprehension, WCAG or production readiness.
- No remaining confirmed high-impact defect in the bounded core was found. Valuable
  future work requires explicit donor-basis reconciliation/fresh multi-review
  studies before expanding network execution, approved operational identity/adapters,
  or lifecycle inputs when justified.
  No global optimizer, stochastic donor guarantee or operational exactly-once claim.
- Original planner commits `55f4170`/`538d29d` are preserved by tag
  `archive/integrated/planner-closed-loop`; identical controls are on main at `6fff524`.

Read [index](README.md), [workflow](../CONTRIBUTING.md), [decisions](DECISIONS.md).
