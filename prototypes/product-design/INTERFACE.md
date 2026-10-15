# Prototype implementation contract
Both directions are independent layouts over the same current APIs. Root agent owns shared.tsx, base.css, main.tsx, package/config, docs and browser QA. Agents own only brief.tsx/brief.css or desk.tsx/desk.css. No backend/product frontend files changed. No business calculations or made-up observations. All shared imports from './shared'. Type any acceptable for prototype envelopes. CSS scope .brief or .desk. Components below use common classes .panel, .section-head, .eyebrow, .muted, .metric, .metrics, .badge, .data-table, .table-scroll, .toolbar, .button, .primary, .callout, .stack, .two-col, .evidence-panel. Style as needed.

Exports:
- type Workspace = ReturnType<typeof useWorkspace>
- useWorkspace(): {route:{page,cutoff,item,search,category,warehouse,sort},go(patch),overview:{data,error,loading,retry},explore:{data,error,loading,retry},detail:{data,error,loading,retry},history:{data,error,loading,retry},params: Record<string,string>,select(item,page='investigate')}
- Route pages overview/explore/investigate/compare/decide/history/execution/evaluation; default May 4 2026, COAST-0 site0. URL hash persists state and browser back. Params bound to archive_digest; changing cutoff invalidates old resources immediately. overview.data has .summary .highlights .insight_discovery .dimensions .cutoffs; explore.data.items server-filtered by search/category/warehouse/sort.
- exact(value) string; label(string) humanizes underscores; dateLabel(ISO) readable date.
- Badge({value}), Notice({resource}), Export({data,name?,children?}), DataTable({items,onSelect,selected?}) inventory rows (Item/location/category/on_hand/proposed order/status). Use exact values; no generated product names.
- EvidencePanel({w}) section picker + clocks + original tables + references + export.
- ComparisonPanel({w}) saved prefix vs no action + alternative quantity/delay controls; backend computes on explicit button; stale suppressed. Supplier capacity comparison and donor-safe transfer optional tabs from existing endpoints.
- HistoryPanel({w}) per-key immutable cutoff history with reopen.
- DecisionPanel({w}) advisory summary and checklist, no mutations; export.
- ExecutionPanel({w}) saved actual-planner reviews and journal feedback timeline; no mutations.
- EvaluationPanel() actual saved 16-path/48-loop results.

Variant components export default function Brief({w}:{w:Workspace}) / Desk(...). Root passes w. Import lucide-react for any icons. Both fully navigate all pages. Each direction has switch link href '?direction=desk' / '?direction=brief' (preserve hash if easy). Brief: warm paper/off-white, green restrained accent, editorial decision desk, generous evidence reading, side navigation, split dossier. Desk: cool light central workspace, graphite navigation/topbar with violet or blue accent, compact analytical table, persistent contextual pane, dense metric strips. Distinct IA and content composition, not just colors.

API example shapes saved /private/tmp/ii-design-{detail,contrast,history,evaluation,feedback-example}.json; actual API http://127.0.0.1:8041 (read only, no journal). Root shared layer handles fetching. Source names COAST-0 Slate XS / coast site 0; COAST-1 Ochre M; COAST-2 Cloud XL. There are 6 keys, 5 assessable, 1 blocked. Category counts 1 risk/2 opportunity/1 evidence/2 none. Do not invent chart trajectories. Can use mini stat bars only from actual numeric fields (geometry only).
