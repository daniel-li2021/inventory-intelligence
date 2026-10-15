# Product design exploration

Investigated October 14, 2026. Two isolated, navigable React prototypes use the
existing local product APIs and the saved Coast synthetic catalog. The owner selected the direct white **Desk** direction, requested larger fonts and
more readable margins/columns, and authorized implementation. The more editorial
**Brief** direction remains preserved for a future switch. [STATE](STATE.md) owns current status.

## Research and workflow fit

Research preceded prototype implementation. Inspected the existing workbench's
Overview, Explore and Investigate flow in the browser; primary product documentation,
published interface examples, a live shadcn block, Tremor components, and both actual
local FinRAG prototypes. No authenticated competitor workspace or paid template was
used. Screenshots under [product-design](screenshots/product-design/baseline-overview.jpg)
record the actual pages visited; documentation demonstrations are not hands-on tests
of authenticated competitor features.

- **Linear:** the [2026 interface refresh](https://linear.app/now/behind-the-latest-design-refresh)
  separates location from view controls, dims supporting navigation and reduces
  competing borders. Apply to the persistent shell, stable cutoff position, active
  navigation and restrained status accents. Avoid copying issue-tracker workflows.
- **Rill:** [filters and comparisons](https://docs.rilldata.com/guide/dashboards/filters)
  demonstrates dimensional selection, visible filters and URL state. Apply to
  inventory exploration and repeatable cutoff/item/filter links. Keep backend-defined
  dimensions and exact quantities; do not invent continuous trends between snapshots.
- **Metabase:** [drill-through](https://www.metabase.com/docs/latest/questions/visualizations/drill-through?use_case=ea)
  connects a selected value to the records behind it. Apply to an inventory row →
  contextual evidence → original section, preserving the selected item and cutoff.
  Do not add a query builder or imply arbitrary unsupported analyses.
- **shadcn/ui:** inspected the [live dashboard block](https://ui.shadcn.com/view/new-york-v4/dashboard-01)
  and [data-table guidance](https://ui.shadcn.com/docs/components/base/data-table).
  Apply consistent controls, quiet boundaries, semantic tables and aligned action
  bars. Its revenue/card hierarchy does not suit evidence-led inventory decisions.
- **Tremor:** inspected the [live component examples](https://www.tremor.so/).
  Apply a stable number/unit hierarchy, compact metrics, tabs and restrained table
  styling. No fabricated sparklines, market-like feeds or commercial savings cards.
- **FinRAG Folio/Meridian:** inspected the existing saved local builds at port3101
  and their design guide. Folio's reading rhythm suits an investigation/decision
  brief; Meridian's compact comparison and persistent inspector suit repeated item
  scanning. Both preserve source identity beside analysis. No financial data or
  backend logic is imported into Inventory Intelligence.

## Initial workbench findings

1. **Overview:** source clocks, archive disclosure and saved-view controls consume
   the first screen before the attention queue. Repeated title/context/card framing
   gives navigation metadata similar weight to a decision. Move compact cutoff
   context into the shell and lead with the review task.
2. **Explore:** many equal-weight filters occupy substantial space before item rows.
   Put search and the most useful dimensions in a compact view bar; retain visible
   clear/reset behavior and exact item/location links.
3. **Investigate:** the selected-item summary and context precede the actual
   explanation/evidence, increasing the distance between a claim and its sources.
   Group the item, reason and proposal with a readable adjacent inspector; disclose
   long clocks and identities progressively.

The baseline already correctly labels synthetic evidence, advisory proposals,
missing data and exact quantities. Those semantics are retained. Findings above
are developer observations from screenshots, not independent comprehension results.

## Prototype boundaries and design system

Both directions share a small tokenized React component system: semantic buttons,
labels, visible focus, native selects/disclosures, status badges with text, exact
inventory/source tables, evidence inspector, comparisons, decision brief, immutable
history, saved execution and evaluation. React/Vite match the current frontend;
Lucide supplies icons. Self-hosted OFL fonts are DM Sans, IBM Plex Mono and Libre
Caslon Display; license files accompany the fonts. No full dashboard template or
paid component code was copied.

The separate [prototype app](../prototypes/product-design/README.md) preserves both
exploration versions. The selected implementation adapts the existing production
frontend, retaining its full comparison, review, journal and lifecycle controls. Existing API handlers perform all business calculations.
The API preview has no journal, and no order/admission/event endpoints are called.
Supplier and transfer comparisons use existing non-persistent calculation endpoints.
Original saved reports, source archives and historical results remain untouched.
Changing item/cutoff hides the previous response immediately; changed comparison
assumptions withhold old outcomes until explicitly recomputed. Unknown stays Unknown.

## Selection and validation

The owner selected Desk after inspecting both runnable directions. Desk favors
repeated inventory scanning: compact navigation, aligned quantities, an attention
queue and optional context. Brief favors considered reading: editorial headings,
more whitespace and a sequential evidence dossier; it takes more scrolling and
shows fewer inventory rows at once. Brief remains a runnable, versioned alternative
in the prototype app; switching the production shell later would require adapting
its layout to the full existing lifecycle controls.

The selected production implementation increases body text to 15px, table text to
14px and numeric cells to 16px, with 18px cell padding. Context moves below the
working area on narrower screens; wide evidence tables scroll inside their panels.
Original evidence records precede identity/clock disclosures. Native system fonts
keep the existing packaged-asset contract; Lucide icons include ISC notices.

- Frontend: 8/8 focused state/control tests; prototype: 6/6 model/state tests;
  hosted product: 3/3 tests. Both TypeScript production builds and the frozen
  production bundle budgets pass (92,337 gzip JS bytes; 7,518 CSS bytes).
- [Installed-wheel check](review/ui-desk-v1/installed-wheel.json): clean wheel,
  served assets, original evidence, read-only default, independent proposals
  12/18/Unknown, saved execution/evaluation; no database or Node runtime needed.
- [Browser receipt](review/ui-desk-v1/browser.json): all eight selected production
  screens at 1440×1000 and 390×844, plus all eight at 320×800 without page-level
  horizontal overflow. Both exploration directions were inspected at desktop and
  mobile sizes. [Desktop Desk](screenshots/product-design/selected-desk-desktop-overview.jpg),
  [mobile Desk](screenshots/product-design/selected-desk-mobile-overview.jpg),
  [desktop Brief](screenshots/product-design/brief-desktop-overview.jpg).
- Exact feasible supplier costs remain 2900/4509/1685; transfer outcomes remain
  6763/5154/3533. Changed assumptions suppress stale results; blocked capacity
  withholds purchase. Original evidence sections and training pagination pass.
  Coast's unsupported legacy periodic comparison remains withheld; the independent
  feasible purchase/transfer path remains usable.
- [Isolated lifecycle receipt](review/ui-desk-v1/lifecycle.json): browser reservation
  12 → dispatch 12 → receipt 5 leaves 7 in transit. Only a temporary loopback
  synthetic journal was written; no original archive was modified.
- [Integrity receipt](review/ui-desk-v1/integrity.json): all 521 protected original
  backend/evidence files retain their hashes; existing comparison, decision options,
  one-review, execution and evaluation function bodies remain unchanged.

Accessibility observations are bounded developer checks; no WCAG certification,
human task acceptance or production readiness is claimed. Independent product/runtime
gates in [ROADMAP](ROADMAP.md) remain open.

## Product-wide UX refinement · October 15

The owner assigned a rendered audit and substantial usability improvements across
all eight routes, continuing the selected Desk direction. The baseline browser
review found a 15,810px Overview at 1440×900: expanded discovery reports dominated
its length. Investigation repeated explanations, raw traces and nested evidence
scrolling; Explore put eight equal-weight filters before results; Compare stacked
three different models, while Decide put controls before its recommendation.
Mobile navigation consumed a fixed side rail and delayed the first useful facts.
History and Evaluation had sound evidence tables but oversized rows and metadata.

| Route | Implemented structure | Desktop before / after |
|---|---|---|
| Overview | Compact coverage and attention rows; four finding summaries, explicit expansion, full exports and evidence gaps | [Before](screenshots/ux-refinement/before-overview.jpg) / [After](screenshots/ux-refinement/after-1440-overview.jpg) |
| Explore | Search, location and sort first; secondary filters with active count and clear action; existing list/matrix and pagination | [Before](screenshots/ux-refinement/before-explore.jpg) / [After](screenshots/ux-refinement/after-1440-explore.jpg) |
| Investigate | Key facts first; Findings, Demand/stock/inbound, Source records, Calculation/limits sections | [Before](screenshots/ux-refinement/before-investigate.jpg) / [After](screenshots/ux-refinement/after-1440-investigate.jpg) |
| Compare | Feasible responses, One-review outcomes and What-if model sections; drafts/results remain mounted when switching | [Before](screenshots/ux-refinement/before-compare.jpg) / [After](screenshots/ux-refinement/after-1440-compare.jpg) |
| Decide | Advisory recommendation first, then policy boundary and feasible response controls; stale/blocked gates retained | [Before](screenshots/ux-refinement/before-decide.jpg) / [After](screenshots/ux-refinement/after-1440-decide.jpg) |
| History | Denser cutoff table; compatible-change evidence disclosed on demand | [Before](screenshots/ux-refinement/before-history.jpg) / [After](screenshots/ux-refinement/after-1440-history.jpg) |
| Execution | Review decisions, Daily outcomes, Policy comparison, Commitments/receipts; material erratum stays visible | [Before](screenshots/ux-refinement/before-execution.jpg) / [After](screenshots/ux-refinement/after-1440-execution.jpg) |
| Evaluation | Consistent metrics and compact result table; readable gate reasons, original arm evidence and provenance | [Before](screenshots/ux-refinement/before-evaluation.jpg) / [After](screenshots/ux-refinement/after-1440-evaluation.jpg) |

Shared native-button navigation and text-labelled semantic badges replace ad hoc
status classes; unrecognized codes receive a neutral tone rather than success.
Saved previous/current values appear directly in [compact insight rows](screenshots/ux-refinement/after-compact-insights.jpg),
without client business arithmetic. Observed inputs, modeled exposure, hypotheses,
missing evidence and supported next steps remain distinct. Source identity,
cutoff, filters and item selections survive related-route transitions; Back to
inventory results restores the filtered view. Optional context now fetches the
exact selected item rather than substituting an unrelated priority highlight.

Desk styling is organized in one readable theme file. The document owns vertical
scrolling; source tables deliberately scroll horizontally. On mobile, an eight-link
navigation grid replaces the space-consuming rail. Compare [mobile before](screenshots/ux-refinement/before-mobile-investigate.jpg)
with [mobile after](screenshots/ux-refinement/after-390-investigate.jpg).

Validation is saved in [browser layout cells](review/ux-refinement-v1/browser.json),
[interaction checks](review/ux-refinement-v1/interactions.json),
[installed-wheel check](review/ux-refinement-v1/installed-wheel.json),
[integrity check](review/ux-refinement-v1/integrity.json) and
[validation receipt](review/ux-refinement-v1/validation.json).

- All eight routes at 1440×900, 1280×800, 768×1024 and 390×844: 32 browser layout
  cells pass without page-level horizontal overflow or nested vertical main scroll.
  Representative rendered screenshots were inspected; every cell has a capture.
- Default Overview height is 2,337px at 1440×900, versus 15,810px before. Its four
  collapsed insight rows are about 160px each; longer explanations remain available.
  These are developer layout measurements, not task-completion or comprehension data.
- 21 browser interaction checks cover empty filters, exact item/cutoff retention,
  driver/source/calculation navigation, original 28-row evidence pagination and an
  eight-row page-two JSON export, supplier staleness, one-review and 12→18 scenario
  comparisons, blocked decisions, keyboard focus and exact optional item context.
  A new temporary synthetic journal admits 12 and receives 5, leaving 7 pending.
- 10 frontend tests, TypeScript/build/bundle budgets and 72 focused existing Python
  regressions pass. The clean installed wheel serves current assets without Node or
  database calls; expected proposals remain 12/18/Unknown. All 602 protected original
  backend/test/SQL/evidence/state/type files retain their bytes. No dependency added.

Remaining limits: wide tables require horizontal movement on narrow screens;
expanded original evidence can still be long by design. Section choices are local
UI state; existing shared routes preserve item, source binding, cutoff, filters and
scenario assumptions. Rapid automated browsing exercised the normal demo rate limit
and Retry recovered; final layout cells used a loopback-only increased allowance,
without changing public safeguards. Human comprehension, assistive-technology
acceptance, full WCAG conformance and post-push public deployment remain unverified.
