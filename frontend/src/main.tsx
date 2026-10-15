import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  pages,
  parseRoute,
  routeHash,
  preset,
  bindingMismatch,
  saveView,
  requestQuery,
  readSavedViews,
  scenarioOverrides,
  readSharedScenario,
} from "./state.mjs";
import type { Card, Context, Exact, Route } from "./types";
import { Boxes, LayoutDashboard, ListFilter, ScanLine, GitCompareArrows, ClipboardCheck, History as HistoryIcon, Activity, ShieldCheck, ChevronRight, ArrowUpRight, PanelRightClose, PanelRightOpen, CalendarDays, Database, Bookmark, FlaskConical } from "lucide-react";
import "./style.css";
import "./desk.css";

const pageIcons: Record<string, React.ElementType> = {overview: LayoutDashboard, explore: ListFilter, investigate: ScanLine, compare: GitCompareArrows, decide: ClipboardCheck, history: HistoryIcon, execution: Activity, evaluation: ShieldCheck};

const labels: Record<string, string> = {
  risk: "Risk",
  opportunity: "Opportunity",
  evidence: "Evidence problem",
  none: "No alert",
  assessable: "Assessable",
  not_assessable: "Blocked",
  worsening: "Worsening",
  improved: "Improved",
  persistent: "Persistent",
  new: "New",
  unknown: "Unknown",
};
const wholeInput = (s: string, minimum: number, maximum: number) => /^(0|[1-9]\d*)$/.test(s) && Number.isSafeInteger(Number(s)) && Number(s)>=minimum && Number(s)<=maximum;
const title = (s: string) =>
  labels[s] || s.replaceAll("_", " ").replace(/^./, (c) => c.toUpperCase());
function exact(value: Exact | undefined): string {
  if (value === null || value === undefined) return "Unknown";
  if (typeof value === "string") return value;
  if (
    typeof value.numerator !== "string" ||
    typeof value.denominator !== "string"
  )
    return "Unknown";
  if (value.denominator === "1") return value.numerator;
  return `${value.numerator}/${value.denominator}`;
}
function Badge({ value }: { value: string }) {
  return <span className={`badge ${value}`}>{title(value)}</span>;
}
function Download({
  data,
  name,
  label = "Export evidence",
}: {
  data: unknown;
  name: string;
  label?: string;
}) {
  return (
    <button
      onClick={() => {
        const url = URL.createObjectURL(
          new Blob([JSON.stringify(data, null, 2)], {
            type: "application/json",
          }),
        );
        const a = document.createElement("a");
        a.href = url;
        a.download = `${name}.json`;
        a.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
      }}
    >
      {label}
    </button>
  );
}
function useResource<T>(path: string | null, retry: number = 0) {
  const [state, set] = useState<{
    data?: T;
    error?: string;
    loading: boolean;
    path?: string;
  }>({ loading: true });
  useEffect(() => {
    if (!path) return;
    const controller = new AbortController();
    let active = true;
    set((s) => ({ ...s, error: undefined, loading: true }));
    fetch(path, { signal: controller.signal, cache: "no-store" })
      .then(async (r) => {
        if (!r.ok) throw Error(`Request failed (${r.status}).`);
        return r.json();
      })
      .then((data) => {
        if (active) set({ data, loading: false, path });
      })
      .catch((error) => {
        if (active && !controller.signal.aborted)
          set((s) => ({ ...s, error: error.message, loading: false }));
      });
    return () => {
      active = false;
      controller.abort();
    };
  }, [path, retry]);
  return { ...state, stale: Boolean(state.data && state.path !== path) };
}
function Notice({
  loading,
  error,
  stale,
  retry,
  data,
}: {
  loading: boolean;
  error?: string;
  stale: boolean;
  retry: () => void;
  data?: unknown;
}) {
  return (
    <>
      {loading && (
        <p className="notice" role="status">
          Loading saved evidence…
        </p>
      )}
      {(error || stale) && (
        <div className="notice warning" role="alert">
          <strong>
            {error
              ? data
                ? "Unable to refresh. Last successful result is retained."
                : "Unable to load saved evidence. No result is available."
              : "This result belongs to the previous selection."}
          </strong>
          <p>
            Review context before using it. Recommendations remain unavailable
            until this selection loads.
          </p>
          {error && <button onClick={retry}>Retry</button>}
        </div>
      )}
    </>
  );
}
function Facts({ facts }: { facts: [string, React.ReactNode][] }) {
  return (
    <dl className="facts">
      {facts.map(([k, v]) => (
        <div key={k}>
          <dt>{k}</dt>
          <dd>{v}</dd>
        </div>
      ))}
    </dl>
  );
}
function Inspector({
  data,
  name = "Saved evidence",
}: {
  data: unknown;
  name?: string;
}) {
  if (data === null || data === undefined)
    return <p>Unavailable. No quantity is inferred.</p>;
  if (typeof data !== "object")
    return <span className="value">{String(data)}</span>;
  if ("numerator" in data && "denominator" in data)
    return <span className="value">{exact(data as Exact)}</span>;
  if (Array.isArray(data))
    return (
      <div className="record-list">
        {data.length ? (
          data.map((r, i) => (
            <details key={i}>
              <summary>
                {typeof r === "object" && r
                  ? String(
                      r.label ||
                        r.id ||
                        r.date ||
                        r.day ||
                        r.kind ||
                        r.source ||
                        `${name} ${i + 1}`,
                    )
                  : `${name} ${i + 1}`}
              </summary>
              <Inspector data={r} />
            </details>
          ))
        ) : (
          <p>No records in this section.</p>
        )}
      </div>
    );
  return (
    <dl className="inspector">
      {Object.entries(data).map(([k, v]) => (
        <div key={k}>
          <dt>{title(k)}</dt>
          <dd>
            <Inspector data={v} name={title(k)} />
          </dd>
        </div>
      ))}
    </dl>
  );
}
function Execution() {
  const [retry, setRetry] = useState(0);
  const [selected, setSelected] = useState("clean");
  const [asOf, setAsOf] = useState("2026-03-20");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const overview = useResource<any>("/api/execution", retry);
  const digest = overview.data?.archive_digest;
  const detail = useResource<any>(digest ? `/api/execution/detail?name=${selected}&archive_digest=${digest}` : null, retry);
  const journal = useResource<any>(digest ? `/api/execution/journal?as_of=${asOf}&archive_digest=${digest}` : null, retry);
  const selectedData = !detail.stale && !detail.loading && !detail.error ? detail.data : undefined;
  const journalData = !journal.stale && !journal.loading && !journal.error ? journal.data : undefined;
  async function write(path: string, data: any) {
    if (busy || !digest) return;
    setBusy(true); setMessage("");
    try {
      const response = await fetch(`/api/execution/${path}`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...data, archive_digest: digest }),
      });
      if (!response.ok) throw Error(`Journal action rejected (${response.status}). Existing entries are retained.`);
      await response.json(); setRetry(v => v + 1);
      setMessage("Synthetic journal saved. Repeating the same event is idempotent.");
    } catch (error: any) { setMessage(error.message); }
    finally { setBusy(false); }
  }
  const cleanDecision = journalData?.decisions?.find((d: any) => d.id === "manual:clean:review-0");
  return <section className="execution-workbench">
    <div className="context-bar">
      <div><span className="context-label">ACTUAL PLANNER RESEARCH</span>
        <strong>March 7–20, 2026 · America/Los_Angeles</strong>
        <small>9 scored days + 5 paid closure days. Initial stock is purchased.</small>
        <small>This execution archive is separate from the January product cutoffs.</small>
      </div>
      {digest && <details className="archive"><summary>Execution archive & source</summary><code>{digest}</code><p>Committed implementation: {overview.data.code_commit}</p></details>}
    </div>
    <Notice {...overview} retry={() => setRetry(v => v + 1)} />
    {overview.data && !overview.stale && !overview.error && <>
      <h2>Actual proposals → receipts → fulfillment</h2>
      <p>These outcomes execute saved prefix-planner proposals. Each review rechecks physical inventory, origin-visible demand and supply. A blocked review creates no order.</p>
      <p className="notice warning">Original cold-shortage control had an arithmetic error: need 17 pieces rounds to 18, rather than 12. Its original bytes remain preserved with an explicit erratum.</p>
      <label>Execution control <select aria-label="Execution control" value={selected} onChange={e => setSelected(e.target.value)}>
        {overview.data.manual.map((c: any) => <option value={c.name} key={c.name}>{title(c.name.replaceAll("-", "_"))}</option>)}
      </select></label>
      <Notice {...detail} retry={() => setRetry(v => v + 1)} />
      {selectedData && <>
        <div className="metric-grid">
          <div><span>Full paid cost · synthetic units</span><strong>{selectedData.summary.total_cost}</strong></div>
          <div><span>Immediate pieces / accepted pieces</span><strong>{selectedData.summary.immediate_fulfilled} / {selectedData.summary.accepted}</strong></div>
          <div><span>Eventually fulfilled / accepted</span><strong>{selectedData.summary.eventual_fulfilled} / {selectedData.summary.accepted}</strong></div>
          <div><span>Terminal stock / backlog · pieces</span><strong>{selectedData.summary.terminal_stock} / {selectedData.summary.terminal_backlog}</strong></div>
        </div>
        <p>Initial purchased stock cost: {selectedData.initial_purchase_cost} synthetic units. Full cost includes initial purchase and every scored/closure day.</p>
        <Inspector data={selectedData.summary.cost_components} name="Full paid cost components" />
        <div className="table-scroll"><table><caption>Actual saved review decisions and evidence</caption><thead><tr><th>Origin known-at</th><th>Status</th><th>Proposal · pieces</th><th>Evidence</th></tr></thead><tbody>
          {selectedData.reviews.map((r: any) => <tr key={r.day}><td>{r.origin}</td><td><Badge value={r.status} /><small>{r.reasons.join(", ")}</small></td><td>{r.proposed_order_qty ?? "Blocked"}</td><td><a href={`/api/execution/evidence?name=${selected}&day=${r.day}&archive_digest=${digest}`} target="_blank" rel="noreferrer">Inspect saved report</a><small>{r.report_id}</small></td></tr>)}
        </tbody></table></div>
        <div className="table-scroll"><table><caption>Physical daily execution · exact pieces and paid cost units</caption><thead><tr><th>Date / phase</th><th>Receipts</th><th>Accepted</th><th>Immediate fill</th><th>Ending stock</th><th>Ending backlog</th><th>Daily cost</th></tr></thead><tbody>
          {selectedData.days.map((d: any) => <tr key={d.date}><td>{d.date}<small>{d.phase}</small></td><td>{d.receipts.map((r: any) => r.quantity).join(" + ") || "0"}</td><td>{d.accepted}</td><td>{d.new_filled}</td><td>{d.end_stock}</td><td>{d.end_backlog}</td><td>{Object.entries(d.cost).map(([k,v]) => `${k}: ${v}`).join(" · ")}</td></tr>)}
        </tbody></table></div>
        <Download data={selectedData} name={`actual-planner-${selected}`} label="Export execution" />
      </>}
      <h2>Paired decision quality</h2>
      <p>12 frozen stress traces × 3 policies. All policies respect the actual planner's evidence gates; demand, supplier rules and the paid 14-day window match. No tuning on these results.</p>
      <div className="table-scroll"><table><caption>Total paid synthetic cost units · identical score and closure windows</caption><thead><tr><th>Trace</th><th>Actual proposals</th><th>Do Nothing</th><th>Fixed 18 pieces</th></tr></thead><tbody>
        {overview.data.comparisons.map((c: any) => <tr key={c.name}><td>{title(c.name.replaceAll("-", "_"))}</td>{["actual", "do-nothing", "fixed-18"].map(p => <td key={p}>{c.policies[p].total_cost}<small>Immediate {c.policies[p].immediate_fulfilled}/{c.policies[p].accepted} · backlog {c.policies[p].terminal_backlog}</small></td>)}</tr>)}
      </tbody></table></div>
      <p className="notice">Quiet trace: Do Nothing costs 160 versus actual 330. These bounded synthetic paths establish no universal policy winner or commercial savings.</p>
      <h2>Durable synthetic commitment sandbox</h2>
      {overview.data.journal_enabled ? <>
        <p>This local journal writes synthetic decision and receipt events only. It preserves earlier source batches and never executes real purchases or changes stock tables.</p>
        <div className="view-tools">
          <button disabled={busy} onClick={() => write("admit", {name: "clean", day: 0})}>Admit clean proposal · 12 pieces</button>
          <button disabled={busy || !cleanDecision} onClick={() => write("event", {decision_id: cleanDecision.id, event_id: "demo:clean:partial-5", kind: "receipt", known_day: "2026-03-09", quantity: 5})}>Receive 5 pieces · March 9</button>
          <button disabled={busy || !cleanDecision} onClick={() => write("event", {decision_id: cleanDecision.id, event_id: "demo:clean:eta", kind: "eta", known_day: "2026-03-10", eta: "2026-03-11"})}>Notify ETA · March 11</button>
          <button disabled={busy || !cleanDecision} onClick={() => write("event", {decision_id: cleanDecision.id, event_id: "demo:clean:final-7", kind: "receipt", known_day: "2026-03-11", quantity: 7})}>Receive remaining 7 · March 11</button>
        </div>
        <p role="status">{message}</p>
        <label>Journal as of <input aria-label="Journal as of" type="date" value={asOf} onChange={e => setAsOf(e.target.value)} /></label>
        <Notice {...journal} retry={() => setRetry(v => v + 1)} />
        {journalData && <><p className="journal-totals">Received {journalData.received_pieces} pieces · pending {journalData.pending_pieces} pieces · {journalData.events.length} durable events</p><Inspector data={journalData} name="Origin-visible synthetic journal" /><Download data={journalData} name="synthetic-receipt-journal" label="Export journal" /></>}
      </> : <p>Read-only packaged mode. Launch the loopback local demo to exercise durable synthetic commitments and partial receipts.</p>}
      <ul>{overview.data.limitations.map((s: string) => <li key={s}>{s}</li>)}</ul>
    </>}
  </section>;
}

function App() {
  const [route, setRoute] = useState<Route>(
    () => parseRoute(location.hash) as Route,
  );
  const [retry, setRetry] = useState(0);
  const [message, setMessage] = useState("");
  const [showContext, setShowContext] = useState(true);
  const PageIcon = pageIcons[route.page] || LayoutDashboard;
  const focus = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    const handle = () => setRoute(parseRoute(location.hash) as Route);
    addEventListener("hashchange", handle);
    return () => removeEventListener("hashchange", handle);
  }, []);
  const navigate = (patch: Partial<Route>) => {
    location.hash = routeHash({ ...route, ...patch });
  };
  const overview = useResource<Context>(
    `/api/product/overview${route.snapshot ? "?cutoff=" + encodeURIComponent(route.snapshot) : ""}`,
    retry,
  );
  const context = overview.data;
  const bound = context
    ? bindingMismatch(route, {
        archive_id: context.archive_digest,
        schema_version: context.contract_version,
        cutoff: context.cutoff,
      })
    : false;
  const nav = (page: string) => navigate({ page });
  useEffect(() => {
    focus.current?.focus();
  }, [route.page]);
  const save = () => {
    if (!context) return;
    try {
      const existing = readSavedViews(localStorage.getItem("ii.views.v1"));
      const name = `${title(route.page)} · ${context.cutoff}`;
      const view = saveView(route, {
        archive_id: context.archive_digest,
        schema_version: context.contract_version,
        cutoff: context.cutoff,
      });
      localStorage.setItem(
        "ii.views.v1",
        JSON.stringify([...existing.slice(-9), { name, state: view }]),
      );
      setMessage("View saved on this browser.");
    } catch {
      setMessage(
        "Browser storage unavailable. Use Share view to keep this selection.",
      );
    }
  };
  let saved: { name: string; state: Route }[] = [];
  try {
    saved = readSavedViews(localStorage.getItem("ii.views.v1"));
  } catch {
    /* Invalid browser data is ignored. */
  }
  return (
    <>
      <a
        className="skip"
        href="#main"
        onClick={(event) => {
          event.preventDefault();
          document.getElementById("main")?.focus();
        }}
      >
        Skip to content
      </a>
      <div className="shell">
        <aside className="sidebar">
          <a className="brand" href="#/overview" aria-label="Inventory Intelligence overview"><Boxes size={26}/></a>
          <nav aria-label="Product navigation">
            {pages.map((page: string) => { const Icon = pageIcons[page]; return <a key={page} href={routeHash({ ...route, page })} aria-current={route.page === page ? "page" : undefined}><Icon size={21}/><span>{title(page)}</span></a>; })}
          </nav>
          <div className="sidebar-footer"><a href="/lab"><FlaskConical size={19}/><span>Scenario Lab</span></a></div>
        </aside>
        <div className="workspace">
          <header className="topbar"><span className="workspace-name"><strong>Inventory Intelligence</strong><ChevronRight size={15}/><span>Decision workbench</span></span><span className="environment-label"><span/>Synthetic workspace</span></header>
          <div className="workbench-viewbar"><div><PageIcon size={22}/><h1 ref={focus} tabIndex={-1}>{title(route.page)}</h1><span className="read-only">{route.page === "execution" ? "Synthetic research" : "Read only"}</span></div><div className="viewbar-actions">
          {!["execution","evaluation"].includes(route.page) && <label className="cutoff-control"><CalendarDays size={16}/><select aria-label="Cutoff" value={route.snapshot || context?.cutoff || ""} onChange={e=>navigate({snapshot:e.target.value,offset:0})}>{context?.cutoffs.map(c=><option key={c}>{c}</option>)}</select></label>}
          {["overview","explore"].includes(route.page) && <button className="context-toggle" aria-label={showContext?"Hide item context":"Show item context"} aria-pressed={showContext} onClick={()=>setShowContext(v=>!v)}>{showContext?<PanelRightClose size={20}/>:<PanelRightOpen size={20}/>}<span>Context</span></button>}</div></div>
          <main id="main" tabIndex={-1}>
            <p className="page-intro">{({overview:"Your inventory attention queue, with the evidence one click away.",explore:"Filter exact saved inventory by item, style, color, size and location.",investigate:"Trace the selected item from original inputs to the saved proposal.",compare:"Compare explicit alternatives, with cost, service and constraints in view.",decide:"Review the advisory decision, its evidence and supported next actions.",history:"Reopen immutable observations across business cutoffs.",execution:"Inspect actual saved planner reviews and synthetic commitment feedback.",evaluation:"Inspect forecast accuracy alongside actual service, cost and blocked reviews."} as Record<string,string>)[route.page]}</p>
            {!(["execution","evaluation"].includes(route.page)) && <><details className="source-context"><summary><Database size={15}/> Evidence context <span>· Business as of {context?.cutoff || "Loading"}</span></summary><div className="context-bar">
              <div>
                <span className="context-label">SOURCE BOUNDARY</span>
                <strong>Business as of {context?.cutoff || "Loading"}</strong>
                <small>Generation does not refresh the stock cutoff.</small>
                <small>
                  Known-at / evaluated:{" "}
                  {context?.highlights[0]
                    ? (context.highlights[0] as any).known_at
                    : "Unknown"}
                </small>
              </div>
              <details className="archive">
                <summary>Archive & contract</summary>
                <code>{context?.archive_digest}</code>
                <p>
                  {context?.contract_version} · Synthetic, historical replay
                </p>
              </details>
            </div></details>
            <Notice
              data={overview.data}
              loading={overview.loading}
              error={overview.error}
              stale={overview.stale}
              retry={() => setRetry((v) => v + 1)}
            />
            {bound && (
              <div className="notice warning" role="alert">
                <strong>
                  Saved view belongs to another archive or contract.
                </strong>
                <p>It cannot be applied as current evidence.</p>
                <button onClick={() => navigate({ archive: "", schema: "" })}>
                  Use current archive
                </button>
              </div>
            )}
            <details className="view-disclosure"><summary><Bookmark size={15}/> Saved views & sharing</summary><div className="view-tools">
              <button onClick={save} disabled={!context || bound}>
                Save view
              </button>
              <label>
                Saved views
                <select
                  aria-label="Saved views"
                  value=""
                  onChange={(e) => {
                    const view = saved[Number(e.target.value)];
                    if (view) location.hash = routeHash(view.state);
                  }}
                >
                  <option value="">Choose saved view</option>
                  {saved.map((v, i) => (
                    <option key={i} value={i}>
                      {v.name}
                    </option>
                  ))}
                </select>
              </label>
              <button
                onClick={async () => {
                  if (!context) return;
                  const view = saveView(route, {
                    archive_id: context.archive_digest,
                    schema_version: context.contract_version,
                    cutoff: context.cutoff,
                  });
                  const url =
                    location.origin + location.pathname + routeHash(view);
                  location.hash = routeHash(view);
                  try {
                    await navigator.clipboard.writeText(url);
                    setMessage("Share link copied.");
                  } catch {
                    setMessage("Share link is in the address bar.");
                  }
                }}
              >
                Share view
              </button>
              <button
                onClick={() => {
                  location.hash = "#/overview";
                  setMessage("View reset.");
                }}
              >
                Reset view
              </button>
              <span role="status">{message}</span>
            </div></details>
            </>}
            <div className={`workbench-layout ${showContext && ["overview","explore"].includes(route.page)?"with-context":""}`}><div className="workbench-content">
            {route.page === "evaluation" ? <Evaluation /> : route.page === "execution" ? <Execution /> : context && !bound && !overview.stale && (
              <>
                {route.page === "overview" ? (
                  <Overview data={context} route={route} go={navigate} />
                ) : route.page === "explore" ? (
                  <Explore route={route} context={context} go={navigate} />
                ) : (
                  <Selected route={route} context={context} go={navigate} />
                )}
              </>
            )}
            </div>{showContext && ["overview","explore"].includes(route.page) && context && !bound && !overview.stale && <FocusContext context={context} route={route} go={navigate}/>}</div>
            <footer className="product-footer">
              <strong>Evidence before action.</strong> Synthetic outcomes do not
              demonstrate commercial savings. Supplier and transfer terms are declared
              assumptions; real purchasing and operational dispatch remain excluded.{" "}
              <a href="/product-static/THIRD_PARTY_LICENSES.txt">
                Third-party notices
              </a>
            </footer>
          </main>
        </div>
      </div>
    </>
  );
}
function CardTable({
  items,
  go,
  unavailable = false,
}: {
  items: Card[];
  unavailable?: boolean;
  go: (r: Partial<Route>) => void;
}) {
  return (
    <div
      className="table-scroll"
      tabIndex={0}
      aria-label="Inventory results, horizontally scrollable"
    >
      <table>
        <caption className="sr-only">Saved inventory insight results</caption>
        <thead>
          <tr>
            <th>Item / location</th>
            <th>Insight</th>
            <th>On hand · pcs</th>
            <th>Proposal · pcs</th>
            <th>Evidence / change</th>
            <th>
              <span className="sr-only">Action</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {items.map((card) => (
            <tr key={card.id}>
              <td>
                <strong>{card.sku_code}</strong>
                <small>
                  {card.style} · {card.color} / {card.size}
                </small>
                <small>{card.location}</small>
              </td>
              <td>
                <Badge value={card.category} />
                <p>{card.title}</p>
              </td>
              <td className="numeric">{exact(card.on_hand)}</td>
              <td className="numeric">{exact(card.proposed_order_qty)}</td>
              <td>
                <Badge value={card.status} />
                <small>History: {title(card.history_state)}</small>
              </td>
              <td>
                <button
                  className="text-button"
                  disabled={unavailable}
                  onClick={() => go({ page: "investigate", item: card.id })}
                  aria-label={`Investigate ${card.sku_code} at ${card.location}`}
                >
                  Investigate →
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {!items.length && (
        <div className="empty">
          <strong>No matching results</strong>
          <p>
            Try another filter or cutoff. Missing coverage remains visible in
            the workspace summary.
          </p>
        </div>
      )}
    </div>
  );
}
function FocusContext({context,route,go}:{context:Context;route:Route;go:(r:Partial<Route>)=>void}) {
  const card=context.highlights.find(c=>c.id===route.item)||context.highlights.find(c=>c.category==='risk')||context.highlights[0];
  if(!card)return null;
  return <aside className="focus-context"><div className="context-heading"><ScanLine size={16}/> Review focus <Badge value={card.category}/></div><h2>{card.sku_code}</h2><p className="context-variant">{card.color} / {card.size} · {card.location}</p><div className="context-quantities"><div><span>On hand · pieces</span><strong>{exact(card.on_hand)}</strong></div><div><span>Saved proposal · pieces</span><strong>{exact(card.proposed_order_qty)}</strong></div></div><p className="eyebrow">Saved observation</p><h3>{card.title}</h3><p>{card.explanation}</p><button className="primary" onClick={()=>go({page:'investigate',item:card.id})}>Inspect original evidence<ArrowUpRight size={16}/></button><div className="context-links"><button onClick={()=>go({page:'compare',item:card.id})}><GitCompareArrows size={16}/>Compare</button><button onClick={()=>go({page:'history',item:card.id})}><HistoryIcon size={16}/>History</button></div><div className="context-source"><span>Business cutoff</span><strong>{context.cutoff}</strong><span>Saved source identity</span><code>{card.references[0]?.id}</code></div><p className="context-boundary"><ShieldCheck size={16}/>Saved synthetic evidence. Proposals are advisory; no real orders.</p></aside>;
}
function Overview({data,route,go}:{data:Context;route:Route;go:(r:Partial<Route>)=>void}) {
  return <>
    <section className="summary-grid" aria-label="Workspace coverage">{[["keys","Inventory scope","item locations"],["risk","Risk","needs attention"],["opportunity","Opportunity","to review"],["evidence","Evidence problem","blocked"]].map(([key,name,unit])=><button className={`stat ${key}`} key={key} onClick={()=>go(key==='keys'?{page:'explore',type:'',offset:0}:preset(route,key))}><span>{name}</span><strong>{data.summary[key]??"Unknown"}</strong><small>{unit}</small></button>)}</section>
    <section className="panel attention-panel"><div className="section-heading"><div><p className="eyebrow">Start here</p><h2>Attention queue</h2><p>Saved priorities across risk, surplus exposure and missing evidence.</p></div><button onClick={()=>go({page:'explore',offset:0})}>View all inventory<ArrowUpRight size={16}/></button></div><CardTable items={data.highlights} go={go}/><div className="coverage-note"><ShieldCheck size={14}/>{data.summary.assessable} of {data.summary.keys} item locations assessable · {data.summary.blocked} blocked<span>Quantities in exact pieces</span></div></section>
    <Discovery data={data.insight_discovery} go={go}/>
    {data.controls?.duplicate_inventory && <DuplicateControl context={data}/>}
    <div className="note-grid"><section className="panel note"><h3>What this workspace can tell you</h3><p>Exact stock, accepted demand, confirmed supply and advisory prefix proposals from saved synthetic runs.</p></section><section className="panel note"><h3>What still needs human review</h3><p>Forecast uncertainty remains uncalibrated. Synthetic costs are not observed commercial savings.</p><a href="/lab">Inspect the original Scenario Lab<ArrowUpRight size={14}/></a></section></div>
  </>;
}

function Discovery({ data, go }: { data: any; go?: (r: Partial<Route>) => void }) {
  if (!data) return null;
  return <section className="panel detail-panel" aria-label="Insight Discovery V2">
    <h2>Insight Discovery V2</h2>
    <p>{data.total_findings ?? data.findings.length} supported findings across {data.evaluated_keys} keys. {data.previous_cutoff ? `Prior cutoff: ${data.previous_cutoff}.` : "No previous cutoff."}</p>
    {data.total_findings > data.findings.length && <p>Showing the first {data.findings.length} findings. Investigate an exact key for its complete findings; the discovery API returns the full bounded set.</p>}
    <p>{data.boundary}</p>
    {data.findings.map((finding: any) => <article key={finding.id} className="panel">
      <p className="eyebrow">{finding.rule_id} · {finding.rules_version}</p>
      <h3>{finding.title}</h3>
      <p><strong>Observed evidence:</strong> {finding.observed}</p>
      {finding.model_hypothesis && <p><strong>Model hypothesis:</strong> {finding.model_hypothesis}</p>}
      <p><strong>Supported next step:</strong> {finding.next_step}</p>
      <p><strong>Missing evidence:</strong> {finding.missing_evidence.join(" ")}</p>
      <p><strong>Priority {finding.priority?.rank}:</strong> {finding.priority?.basis}</p>
      <Inspector data={{values:finding.values,contributing_factors:finding.contributing_factors,references:finding.references,known_at:finding.known_at}} name="Insight evidence" />
      {go && <button onClick={() => go({page:"investigate",item: finding.sku_id+"|"+finding.warehouse_id})}>Investigate finding →</button>}
    </article>)}
    {data.unknown.length > 0 && <details><summary>Evidence gaps ({data.total_unknown ?? data.unknown.length})</summary><Inspector data={data.unknown} name="Unknown evidence" /></details>}
    <ReviewControls discovery={data} />
    <Download data={data} name="insight-discovery-v2" label="Export insight discovery" />
  </section>;
}
function ReviewControls({discovery}: {discovery:any}) {
  const [expanded,setExpanded] = useState(false);
  const [retry,setRetry] = useState(0);
  const [selected,setSelected] = useState('');
  const [status,setStatus] = useState('investigating');
  const [note,setNote] = useState('');
  const [timestamp,setTimestamp] = useState('');
  const [busy,setBusy] = useState(false);
  const [message,setMessage] = useState('');
  const query = new URLSearchParams({cutoff:discovery.cutoff,archive_digest:discovery.archive_digest});
  const resource = useResource<any>(expanded ? '/api/product/reviews?' + query : null,retry);
  const current = discovery.findings.find((f:any)=>f.id===selected) || discovery.findings[0];
  const binding = resource.data?.bindings.find((b:any)=>b.finding_id===current?.id);
  async function save() {
    setBusy(true);setMessage('');
    try {
      const response = await fetch('/api/product/review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cutoff:discovery.cutoff,archive_digest:discovery.archive_digest,finding_id:current.id,calculation_digest:binding.calculation_digest,event_id:'review:'+crypto.randomUUID(),status,note,reviewed_at:timestamp || current.known_at})});
      if (!response.ok) throw Error(`Review rejected (${response.status}). Existing evidence and notes are retained.`);
      setMessage('Review saved. Facts and decision gates remain visible.');setRetry(v=>v+1);
    } catch(error:any){setMessage(error.message);}
    finally {setBusy(false);}
  }
  if (!discovery.findings.length) return null;
  return <details className="review-controls" onToggle={e=>setExpanded(e.currentTarget.open)}><summary>Review a source-bound finding</summary>
    <p>Track acknowledgment, investigation or resolution in the local synthetic journal. A resolved note does not hide the finding or waive a decision gate.</p>
    <Notice {...resource} retry={()=>setRetry(v=>v+1)} />
    {resource.data?.journal_enabled ? <><label>Finding<select aria-label="Review finding" value={current?.id || ''} onChange={e=>{setSelected(e.target.value);setTimestamp('');}}>{discovery.findings.map((f:any)=><option key={f.id} value={f.id}>{f.title} · {f.sku_id}</option>)}</select></label><div className="filter-grid"><label>Review state<select aria-label="Review state" value={status} onChange={e=>setStatus(e.target.value)}><option value="acknowledged">Acknowledged</option><option value="investigating">Investigating</option><option value="resolved">Resolved</option></select></label><label>Synthetic reviewed at · UTC<input aria-label="Review timestamp" value={timestamp || current?.known_at || ''} onChange={e=>setTimestamp(e.target.value)} /></label></div><label>Investigation note<textarea aria-label="Investigation note" value={note} maxLength={500} onChange={e=>setNote(e.target.value)} /></label><button disabled={busy || !note.trim() || !binding || resource.stale || Boolean(resource.error)} onClick={save}>Save finding review</button><p role="status">{message}</p><EvidenceDisclosure data={resource.data.history} name="Source-bound review history" /></> : resource.data && <p>Read-only mode. Run the loopback synthetic sandbox to save reviews.</p>}
  </details>;
}

function DuplicateControl({ context }: { context: Context }) {
  const [expanded, setExpanded] = useState(false);
  const [retry, setRetry] = useState(0);
  const query = new URLSearchParams({
    name: "duplicate_inventory",
    archive_digest: context.archive_digest,
  });
  const resource = useResource<any>(
    expanded ? "/api/product/control?" + query : null,
    retry,
  );
  const data = resource.data;
  return (
    <section className="panel detail-panel duplicate-control">
      <div className="section-heading">
        <div>
          <p className="eyebrow">INDEPENDENT NEGATIVE CONTROL</p>
          <h2>Duplicate inventory evidence</h2>
          <p>
            A separate synthetic defect fixture demonstrates the global
            reliability gate. It is excluded from the normal catalog and
            attention counts.
          </p>
        </div>
        <button
          aria-expanded={expanded}
          aria-controls="duplicate-inventory-control"
          onClick={() => setExpanded((value) => !value)}
        >
          {expanded
            ? "Collapse control"
            : "Inspect duplicate-inventory control"}
        </button>
      </div>
      {expanded && (
        <div id="duplicate-inventory-control">
          <Notice {...resource} retry={() => setRetry((value) => value + 1)} />
          {data && (
            <>
              <div className="notice warning">
                <strong>
                  Global inventory validation failed · recommendation withheld
                </strong>
                <p>{data.explanation}</p>
                <p>
                  The proposed quantity and projection are explicitly null;
                  duplicate observations cannot become trusted stock.
                </p>
              </div>
              <Facts
                facts={[
                  ["Defect fixture cutoff", data.cutoff || "Unknown"],
                  ["Source as-of", data.reliability?.as_of || "Unknown"],
                  ["Evaluated at", data.reliability?.evaluated_at || "Unknown"],
                  ["Reliability run", data.reliability?.run_id || "Unknown"],
                  [
                    "Proposal · pieces",
                    exact(data.blocked_plan?.proposed_order_qty),
                  ],
                  ["Plan run", data.blocked_plan?.run_id || "Unknown"],
                  [
                    "Action state",
                    <Badge
                      value={data.blocked_plan?.status || "not_assessable"}
                    />,
                  ],
                ]}
              />
              <h3>Blocked advisory plan</h3>
              <Inspector data={data.blocked_plan} />
              <h3>Saved reliability failure and duplicate rows</h3>
              <Inspector data={data.reliability} />
              <Download
                data={data}
                name="duplicate-inventory-control"
                label="Export duplicate control"
              />
            </>
          )}
        </div>
      )}
    </section>
  );
}
function Explore({
  route,
  context,
  go,
}: {
  route: Route;
  context: Context;
  go: (r: Partial<Route>) => void;
}) {
  const [retry, setRetry] = useState(0);
  const params = requestQuery({ ...route, snapshot: context.cutoff });
  params.set("archive_digest", context.archive_digest);
  const resource = useResource<any>("/api/product/explore?" + params, retry);
  const data = resource.data;
  const dimension = (key: string) => {
    const dims = data?.dimensions || context.dimensions;
    const values =
      key === "colors" || key === "sizes"
        ? [
            ...new Set(
              (dims.skus || []).map(
                (v: any) => v[key === "colors" ? "color" : "size"],
              ),
            ),
          ]
        : dims[key] || [];
    return Array.isArray(values)
      ? values.map((v: any) =>
          typeof v === "string"
            ? { id: v, label: v }
            : {
                id: v.id || v.style_id || v.warehouse_id || v.value,
                label:
                  v.name ||
                  v.label ||
                  v.style ||
                  v.location ||
                  v.style_code ||
                  v.warehouse_code ||
                  v.id,
              },
        )
      : Object.entries(values).map(([id, label]) => ({
          id,
          label: String(label),
        }));
  };
  const filters: [keyof Route, string, string][] = [
    ["style", "Style", "styles"],
    ["color", "Color", "colors"],
    ["size", "Size", "sizes"],
    ["location", "Location", "warehouses"],
  ];
  return (
    <>
      <div className="preset-tabs" aria-label="Explore presets">
        {[
          ["", "All inventory"],
          ["risk", "At-risk stock"],
          ["opportunity", "Excess stock"],
          ["evidence", "Untrusted evidence"],
        ].map(([type, label]) => (
          <button
            key={type}
            aria-pressed={(route.type || "") === type}
            onClick={() => go(preset(route, type))}
          >
            {label}
          </button>
        ))}
      </div>
      <section className="panel filters">
        <label className="search">
          Search items
          <input
            aria-label="Search items"
            value={route.q || ""}
            placeholder="SKU, style or location"
            onChange={(e) => go({ q: e.target.value, offset: 0 })}
          />
        </label>
        {filters.map(([key, label, dim]) => (
          <label key={key}>
            {label}
            <select
              aria-label={label}
              value={String(route[key] || "")}
              onChange={(e) => go({ [key]: e.target.value, offset: 0 })}
            >
              <option value="">All {label.toLowerCase()}s</option>
              {dimension(dim).map((v: any) => (
                <option value={v.id} key={v.id}>
                  {v.label}
                </option>
              ))}
            </select>
          </label>
        ))}
        <label>
          Insight type
          <select
            aria-label="Insight type"
            value={route.type || ""}
            onChange={(e) => go({ type: e.target.value, offset: 0 })}
          >
            <option value="">All insight types</option>
            {["risk", "opportunity", "evidence", "none"].map((v) => (
              <option value={v} key={v}>
                {title(v)}
              </option>
            ))}
          </select>
        </label>
        <label>
          Evidence status
          <select
            aria-label="Evidence status"
            value={route.status || ""}
            onChange={(e) => go({ status: e.target.value, offset: 0 })}
          >
            <option value="">All evidence states</option>
            <option value="assessable">Assessable</option>
            <option value="not_assessable">Blocked</option>
          </select>
        </label>
        <label>
          Sort
          <select
            aria-label="Sort"
            value={route.sort || "priority"}
            onChange={(e) => go({ sort: e.target.value, offset: 0 })}
          >
            <option value="priority">Priority</option>
            <option value="sku">SKU</option>
            <option value="stock">Stock</option>
          </select>
        </label>
      </section>
      <Notice {...resource} retry={() => setRetry((v) => v + 1)} />
      <div className="section-heading">
        <div>
          <h2>Inventory workbench</h2>
          <p>
            Workspace coverage: {context.summary.assessable} assessable /{" "}
            {context.summary.keys} expected keys; {context.summary.blocked}{" "}
            blocked. Filters do not restore missing evidence.
          </p>
        </div>
        <div className="segmented">
          <button
            aria-pressed={route.view !== "matrix"}
            onClick={() => go({ view: "table" })}
          >
            List
          </button>
          <button
            aria-pressed={route.view === "matrix"}
            onClick={() => go({ view: "matrix" })}
          >
            Apparel matrix
          </button>
        </div>
      </div>
      {data && (
        <>
          <section className="panel">
            {route.view === "matrix" ? (
              <Matrix
                matrix={data.matrix}
                unavailable={
                  resource.stale || resource.loading || Boolean(resource.error)
                }
                items={data.items}
                dimensions={data.dimensions || context.dimensions}
                go={go}
              />
            ) : (
              <CardTable
                items={data.items}
                go={go}
                unavailable={
                  resource.stale || resource.loading || Boolean(resource.error)
                }
              />
            )}
          </section>
          <div className="pagination">
            <p>
              {data.total} matching keys · Page {data.page} of {data.pages || 1}
            </p>
            <button
              disabled={data.page <= 1 || resource.loading}
              onClick={() => go({ offset: route.offset - 20 })}
            >
              Previous page
            </button>
            <button
              disabled={data.page >= data.pages || resource.loading}
              onClick={() => go({ offset: route.offset + 20 })}
            >
              Next page
            </button>
            <Download
              data={{
                archive_digest: context.archive_digest,
                contract_version: context.contract_version,
                filters: params.toString(),
                ...data,
              }}
              name="inventory-view"
              label="Export view"
            />
          </div>
        </>
      )}
      <div className="notice">
        <strong>Supply delays and transfer candidates</strong>
        <p>
          Observed supplier lateness and feasible transfers need additional
          lifecycle/transit evidence. These presets are not available; a
          hidden-delay scenario remains a labelled hypothesis.
        </p>
      </div>
    </>
  );
}
function Matrix({
  matrix,
  items,
  dimensions,
  go,
  unavailable = false,
}: {
  matrix: any;
  items: Card[];
  dimensions: any;
  unavailable?: boolean;
  go: (r: Partial<Route>) => void;
}) {
  const raw: any[] = Array.isArray(matrix) ? matrix : matrix?.cells || items;
  const cells: Card[] = raw.map((cell) => {
    const sku =
      (dimensions.skus || []).find((v: any) => v.sku_id === cell.sku_id) || {};
    const style =
      (dimensions.styles || []).find(
        (v: any) => v.style_id === cell.style_id,
      ) || {};
    const location =
      (dimensions.warehouses || []).find(
        (v: any) => v.warehouse_id === cell.warehouse_id,
      ) || {};
    return {
      ...sku,
      ...cell,
      style: cell.style || style.name || style.style_code || cell.style_id,
      location:
        cell.location ||
        location.name ||
        location.warehouse_code ||
        cell.warehouse_id,
    };
  });
  const groups = new Map<string, Card[]>();
  for (const cell of cells) {
    const key = `${cell.style} · ${cell.color} · ${cell.location}`;
    groups.set(key, [...(groups.get(key) || []), cell]);
  }
  const sizes = ["XS", "S", "M", "L", "XL"];
  return (
    <div
      className="table-scroll"
      tabIndex={0}
      aria-label="Apparel matrix, horizontally scrollable"
    >
      <table className="matrix">
        <caption>
          Exact pieces by color, size and location. Zero is recorded stock;
          Unknown is incomplete evidence. Each cell opens its exact key.
        </caption>
        <thead>
          <tr>
            <th>Style / color / location</th>
            {sizes.map((size) => (
              <th key={size}>{size}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {[...groups].map(([group, values]) => (
            <tr key={group}>
              <th scope="row">{group}</th>
              {sizes.map((size) => {
                const cell = values.find((v) => v.size === size);
                return (
                  <td key={size}>
                    {cell ? (
                      <button
                        disabled={unavailable}
                        className={`matrix-cell ${cell.status === "assessable" ? cell.category : "evidence"}`}
                        onClick={() =>
                          go({ page: "investigate", item: cell.id })
                        }
                        aria-label={`${group}, ${size}, ${exact(cell.on_hand)} pieces, ${title(cell.status)}`}
                      >
                        <strong>{exact(cell.on_hand)}</strong>
                        <small>
                          {title(
                            cell.status === "assessable"
                              ? cell.category
                              : cell.status,
                          )}
                        </small>
                      </button>
                    ) : (
                      <span className="unknown">Not in selection</span>
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
function EvidenceDisclosure({data,name="Saved evidence"}: {data:unknown;name?:string}) {
  return <details className="evidence-disclosure"><summary>{name}</summary><Inspector data={data} name={name} /></details>;
}

function FeedbackExample() {
  const [expanded,setExpanded] = useState(false);
  const [retry,setRetry] = useState(0);
  const resource = useResource<any>(expanded ? '/api/product/feedback-example' : null,retry);
  const data = resource.data;
  return <details className="lifecycle" onToggle={e=>setExpanded(e.currentTarget.open)}><summary>Inspect subsequent actual planner decisions</summary>
    <p>A saved coast demonstration shows separate owner publication and independently observed stock. It does not automatically change the source catalog currently selected here.</p>
    <Notice {...resource} retry={()=>setRetry(v=>v+1)} />
    {data && !resource.stale && !resource.error && <><div className="table-scroll"><table><caption>Source-bound actual planner feedback · synthetic pieces</caption><thead><tr><th>Known evidence</th><th>Business origin</th><th>Proposal</th><th>Reason / inspect</th></tr></thead><tbody>{Object.entries(data.reports).map(([name,value])=>{const report:any=value;return <tr key={name}><td>{title(name)}</td><td>{report.context.origin_day}</td><td>{report.result.proposed_order_qty ?? 'Blocked'}</td><td>{report.result.reasons.join(', ')}<EvidenceDisclosure data={report} name={`Original report · ${title(name)}`} /></td></tr>;})}</tbody></table></div><Download data={data} name="actual-transfer-feedback" label="Export actual feedback" /><EvidenceDisclosure data={data.journal_history} name="Then-known transfer and ETA history" /></>}
  </details>;
}

function Evaluation() {
  const [retry, setRetry] = useState(0);
  const resource = useResource<any>('/api/product/evaluation', retry);
  const data = resource.data;
  return <section className="panel detail-panel" aria-label="Forecast and decision evaluation">
    <h2>Forecast accuracy meets decision quality</h2>
    <p>Fresh synthetic paths separate baseline selection from evaluation. Every policy uses the actual planner and pays for opening stock, all purchases, holding, backlog and closure.</p>
    <Notice {...resource} retry={() => setRetry(v => v + 1)} />
    {data && !resource.stale && !resource.error && <>
      <div className="metric-grid"><div><span>Independent paths</span><strong>{data.independent_paths}</strong></div><div><span>Actual planner reviews</span><strong>{data.reviews}</strong></div><div><span>Blocked reviews retained</span><strong>{data.blocked_reviews}</strong></div><div><span>Decision gate passed</span><strong>{data.decision_gate_passes} / {data.families.length}</strong></div></div>
      <p className="notice">No global winner or policy promotion. Point forecasts provide no prediction intervals; calibration is undefined.</p>
      <div className="table-scroll"><table><caption>Independent evaluation outcomes · exact synthetic costs and pieces</caption><thead><tr><th>Demand / supply path</th><th>Selection choice</th><th>Cost versus mean</th><th>Decision gate</th><th>Inspect</th></tr></thead><tbody>{data.families.map((f: any) => <tr key={f.family}><td>{title(f.family.replaceAll('-', '_'))}</td><td>{title(f.selected_from_selection)}</td><td>{f.evaluation_cost_delta_vs_mean}<small>Fill {f.evaluation_fill ?? 'Undefined'} · {f.selected_blocked_reviews} blocked reviews</small></td><td>{f.decision_gate_passed ? 'Passed' : 'No promotion'}<small>{f.decision_gate_failures.join(', ')}</small></td><td><EvidenceDisclosure data={f.arms} name={`Accuracy, costs and service · ${f.family}`} /></td></tr>)}</tbody></table></div>
      <EvidenceDisclosure data={{protocol:data.protocol_sha256,source_artifact:data.source_artifact_sha256,runtime:data.runtime}} name="Study provenance" />
      <Download data={data} name="forecast-decision-evaluation" label="Export evaluation" />
    </>}
  </section>;
}

function DecisionOptions({card, context, unavailable=false}: {card: Card; context: Context; unavailable?:boolean}) {
  const [retry, setRetry] = useState(0);
  const [quantity, setQuantity] = useState('12');
  const [capacity, setCapacity] = useState('12');
  const [minute, setMinute] = useState('540');
  const [donor, setDonor] = useState('');
  const [transit, setTransit] = useState('1');
  const [purchaseResult, setPurchaseResult] = useState<any>(null);
  const [transferResult, setTransferResult] = useState<any>(null);
  const [purchaseBinding, setPurchaseBinding] = useState('');
  const [transferBinding, setTransferBinding] = useState('');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [transferId, setTransferId] = useState('');
  const [receipt, setReceipt] = useState('5');
  const [eventDay, setEventDay] = useState(context.cutoff);
  const [asOf, setAsOf] = useState(context.cutoff);
  const [purchaseId, setPurchaseId] = useState('');
  const [eta, setEta] = useState(context.cutoff);
  const base = {cutoff:context.cutoff, sku_id:card.sku_id, warehouse_id:card.warehouse_id, archive_digest:context.archive_digest};
  const query = new URLSearchParams(base);
  const config = useResource<any>('/api/product/decision-context?' + query, retry);
  const history = useResource<any>(config.data?.journal_enabled ? '/api/product/transfer-history?' + new URLSearchParams({as_of:asOf,archive_digest:context.archive_digest}) : null, retry);
  const purchases = useResource<any>(config.data?.journal_enabled ? '/api/product/purchase-history?' + new URLSearchParams({as_of:asOf,archive_digest:context.archive_digest}) : null, retry);
  const blocked = unavailable || config.loading || config.stale || Boolean(config.error);
  const locations = config.data?.locations.filter((w: any) => w.warehouse_id !== card.warehouse_id) || [];
  const donorId = donor || locations[0]?.warehouse_id || '';
  const supplier = config.data ? {...config.data.supplier, version_id:`declared-capacity-${capacity}-${context.cutoff}`, capacity:config.data.supplier.capacity.map((r: any) => ({...r,capacity:Number(capacity)}))} : null;
  const transport = config.data ? {...config.data.transport, version_id:`declared-transit-${transit}-${context.cutoff}`, transit_days:Number(transit)} : null;
  const purchaseBody = {...base,quantity:Number(quantity),order_minute:Number(minute),supplier};
  const transferBody = {...base,quantity:Number(quantity),donor_id:donorId,transport,supplier};
  const validPurchase = wholeInput(quantity,0,2000) && wholeInput(capacity,0,2000) && wholeInput(minute,0,1439);
  const validTransfer = validPurchase && wholeInput(transit,1,32);
  const purchaseStale = blocked || !validPurchase || purchaseBinding !== JSON.stringify(purchaseBody);
  const transferStale = blocked || !validTransfer || transferBinding !== JSON.stringify(transferBody);
  async function request(path: string, body: any) {
    if (busy || blocked) return null;
    setBusy(true); setMessage('');
    try {
      const response = await fetch('/api/product/' + path, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
      if (!response.ok) throw Error(`Request rejected (${response.status}). Retained results and history remain available.`);
      return await response.json();
    } catch (error: any) {setMessage(error.message);return null;}
    finally {setBusy(false);}
  }
  async function calculate(kind: 'supplier'|'transfer') {
    const body = kind === 'supplier' ? purchaseBody : transferBody;
    const result = await request(kind+'-contrast', body);
    if (result) {
      if (kind === 'supplier') {setPurchaseResult(result);setPurchaseBinding(JSON.stringify(body));}
      else {setTransferResult(result);setTransferBinding(JSON.stringify(body));}
    }
  }
  async function admit() {
    const data = await request('supplier-admit',purchaseBody);
    if (data) {setPurchaseId(data.id);setEta(data.feasibility?.promised_day || context.cutoff);setMessage('Synthetic commitment admitted. Receipts and ETA notices require explicit events.');setRetry(v=>v+1);}
  }
  async function reserve() {
    const data = await request('transfer-reserve',transferBody);
    if (data) {setTransferId(data.id);setMessage('Transfer reserved. Any residual purchase requires separate admission.');setRetry(v=>v+1);}
  }
  async function event(kind: 'dispatch'|'receipt', purchase=false) {
    const identity = purchase ? purchaseId : transferId;
    const body = {archive_digest:context.archive_digest, event_id:`ui:${identity}:${kind}:${eventDay}:${purchase ? 'purchase' : 'transfer'}:${kind==='receipt' ? receipt : ''}`, known_day:eventDay, kind, ...(purchase ? {decision_id:identity} : {transfer_id:identity}), ...(kind==='receipt' ? {quantity:Number(receipt)} : {})};
    if (await request(purchase ? 'purchase-event' : 'transfer-event',body)) {setMessage('Synthetic event saved. Identical events are idempotent.');setRetry(v=>v+1);}
  }
  return <section className="panel detail-panel decision-options" aria-label="Feasible decision explorer">
    <p className="eyebrow">FEASIBLE SYNTHETIC RESPONSES</p><h2>Purchase, transfer or no action</h2>
    <p>Compare one review over 33 paid days. Supplier and transport terms below are explicit synthetic assumptions. Full declared future demand protects the donor; a short-term imbalance alone does not authorize transfer.</p>
    <Notice {...config} retry={()=>setRetry(v=>v+1)} />
    <div className="filter-grid">
      <label>Alternative / transfer · pieces<input aria-label="Feasible alternative quantity" type="number" min="0" max="2000" step="1" value={quantity} onChange={e=>setQuantity(e.target.value)} /></label>
      <label>Supplier dispatch capacity · pieces<input aria-label="Supplier capacity" type="number" min="0" max="2000" value={capacity} onChange={e=>setCapacity(e.target.value)} /></label>
      <label>Supplier-local order minute<input aria-label="Supplier-local order minute" type="number" min="0" max="1439" value={minute} onChange={e=>setMinute(e.target.value)} /></label>
    </div>
    <p>Ordering Monday–Friday, daily cutoff 17:00; receiving every day. Missing dated capacity blocks purchase. These terms are independently versioned from stock evidence.</p>
    <button disabled={busy || blocked || !validPurchase || !config.data || config.stale || Boolean(config.error)} onClick={()=>calculate('supplier')}>Compare feasible purchases</button>
    <p role="status">{message}</p>
    {purchaseResult && <section className="decision-result" aria-label="Supplier decision results">
      {purchaseStale && <p className="notice warning">Retained comparison is stale. Recalculate after changing assumptions.</p>}
      <DecisionRows data={purchaseResult} />
      <EvidenceDisclosure data={purchaseResult} name="Supplier constraints, daily outcomes and provenance" />
      <Download data={{...purchaseResult,stale:purchaseStale}} name="feasible-purchase" label="Export feasible purchases" />
      {config.data?.journal_enabled && <button disabled={busy || blocked || purchaseStale || purchaseResult.arms?.alternative?.status!=='assessable' || Number(quantity)<=0} onClick={admit}>Admit alternative to synthetic journal</button>}
    </section>}
    <h3>Use donor-safe surplus</h3>
    {locations.length ? <><div className="filter-grid"><label>Donor location<select aria-label="Donor location" value={donorId} onChange={e=>setDonor(e.target.value)}>{locations.map((w:any)=><option key={w.warehouse_id} value={w.warehouse_id}>{w.name || w.location || w.warehouse_id}</option>)}</select></label><label>Transit · full days<input aria-label="Transfer transit days" type="number" min="1" max="32" value={transit} onChange={e=>setTransit(e.target.value)} /></label></div><p>Dispatch capacity 24 pieces. Transport costs 4 per dispatch + 1 per piece; no purchase charge for transferred stock.</p><button disabled={busy || blocked || !validTransfer || !config.data || config.stale || Boolean(config.error)} onClick={()=>calculate('transfer')}>Compare transfer before purchase</button></> : <p>A transfer needs two declared locations for this item.</p>}
    {transferResult && <section className="decision-result" aria-label="Transfer decision results">
      {transferStale && <p className="notice warning">Retained transfer comparison is stale. Recalculate before reserving.</p>}
      <p>Protected donor surplus: {transferResult.safe_surplus ?? 'Unknown'} pieces. {transferResult.reasons.join(', ')}</p>
      <DecisionRows data={transferResult} />
      <EvidenceDisclosure data={transferResult} name="Network conservation, donor service and evidence" />
      <Download data={{...transferResult,stale:transferStale}} name="transfer-comparison" label="Export transfer comparison" />
      {config.data?.journal_enabled && <button disabled={busy || blocked || transferStale || transferResult.status!=='assessable' || transferResult.arms?.transfer_before_purchase?.status!=='feasible' || Number(quantity)<=0} onClick={reserve}>Reserve synthetic transfer</button>}
    </section>}
    {config.data?.journal_enabled ? <details className="lifecycle"><summary>Synthetic commitments, dispatch and partial receipts</summary>
      <p>Transfer reservation allocates donor pieces only. It does not admit a residual purchase or write operational stock. Business dates cannot be backdated; late dispatch requires replanning.</p>
      <div className="filter-grid"><label>Transfer identity<input aria-label="Transfer identity" value={transferId} onChange={e=>setTransferId(e.target.value)} /></label><label>Purchase identity<input aria-label="Purchase identity" value={purchaseId} onChange={e=>setPurchaseId(e.target.value)} /></label><label>Event business date<input aria-label="Event business date" type="date" value={eventDay} onChange={e=>setEventDay(e.target.value)} /></label><label>Partial receipt · pieces<input aria-label="Partial receipt pieces" type="number" min="1" value={receipt} onChange={e=>setReceipt(e.target.value)} /></label></div>
      <div className="view-tools"><button disabled={busy || blocked || !transferId} onClick={()=>event('dispatch')}>Dispatch reserved transfer</button><button disabled={busy || blocked || !transferId} onClick={()=>event('receipt')}>Receive transfer pieces</button><button disabled={busy || blocked || !purchaseId} onClick={()=>event('receipt',true)}>Receive purchase pieces</button></div>
      <label>Revised supplier / transport ETA<input aria-label="Revised supplier ETA" type="date" value={eta} onChange={e=>setEta(e.target.value)} /></label><button disabled={busy || blocked || !purchaseId} onClick={async()=>{if(await request('purchase-event',{archive_digest:context.archive_digest,decision_id:purchaseId,event_id:`ui:${purchaseId}:eta:${eventDay}:${eta}`,kind:'eta',known_day:eventDay,eta})){setMessage('Synthetic ETA notice saved.');setRetry(v=>v+1);}}}>Notify revised ETA</button>
      <button disabled={busy || blocked || !transferId} onClick={async()=>{if(await request('transfer-event',{archive_digest:context.archive_digest,transfer_id:transferId,event_id:`ui:${transferId}:eta:${eventDay}:${eta}`,kind:'eta',known_day:eventDay,eta})){setMessage('Synthetic transport ETA saved.');setRetry(v=>v+1);}}}>Notify transfer ETA</button>
      <FeedbackExample />
      <label>History as of<input aria-label="Decision history as of" type="date" value={asOf} onChange={e=>setAsOf(e.target.value)} /></label>
      <Notice {...history} retry={()=>setRetry(v=>v+1)} /><Notice {...purchases} retry={()=>setRetry(v=>v+1)} />
      {!history.stale && history.data && <EvidenceDisclosure data={history.data} name="Transfer reservation, in-transit and receipt history" />}
      {!purchases.stale && purchases.data && <EvidenceDisclosure data={purchases.data} name="Supplier commitment and ETA history" />}
    </details> : <p>Packaged mode is read-only. The local loopback sandbox enables explicit synthetic commitments and events.</p>}
  </section>;
}

function DecisionRows({data}: {data:any}) {
  if (!data.arms) return <p className="notice warning">Not assessable: {data.reasons.join(', ')}. Unsafe outcome quantities are withheld.</p>;
  return <div className="table-scroll"><table><caption>Compatible 33-day outcomes · exact pieces and synthetic cost units</caption><thead><tr><th>Decision</th><th>Feasibility / promise</th><th>Paid cost</th><th>Service / exposure</th></tr></thead><tbody>{Object.entries(data.arms).map(([name,raw])=>{const arm:any=raw;return <tr key={name}><td>{title(name)}<small>Purchase {arm.purchase_quantity ?? arm.quantity ?? 'Unknown'} · transfer {arm.transfer_quantity ?? '0'}</small></td><td>{title(arm.status || 'assessable')}<small>{arm.feasibility?.promised_day || arm.purchase_promise?.promised_day || 'No purchase promise'}{arm.reasons?.join(', ')}</small></td><td>{arm.total_cost ?? 'Withheld'}</td><td>{arm.recipient ? `Recipient fill ${exact(arm.recipient.immediate_fill)} · donor fill ${exact(arm.donor.immediate_fill)}` : `Immediate ${arm.immediate_fulfilled ?? 'Unknown'} / ${arm.accepted ?? 'Unknown'}`}<small>Terminal backlog {arm.recipient?.terminal_backlog ?? arm.terminal_backlog ?? 'Unknown'}</small></td></tr>;})}</tbody></table></div>;
}

function Selected({
  route,
  context,
  go,
}: {
  route: Route;
  context: Context;
  go: (r: Partial<Route>) => void;
}) {
  const [retry, setRetry] = useState(0);
  const selectedId = route.item || context.highlights[0]?.id;
  useEffect(() => {
    if (selectedId && !route.item) go({ item: selectedId });
  }, [selectedId, route.item, go]);
  const split = selectedId?.split("|") || [];
  const params = new URLSearchParams({
    cutoff: context.cutoff,
    archive_digest: context.archive_digest,
    sku_id: split[0] || "",
    warehouse_id: split[1] || "",
  });
  const resource = useResource<any>(
    selectedId ? "/api/product/detail?" + params : null,
    retry,
  );
  const data = resource.data;
  const card: Card = data?.item || data;
  const historyParams = new URLSearchParams(params);
  historyParams.delete("cutoff");
  const history = useResource<any>(
    route.page === "history" && selectedId
      ? "/api/product/history?" + historyParams
      : null,
    retry,
  );
  if (!selectedId)
    return (
      <section className="panel empty">
        <h2>Select an inventory key</h2>
        <p>
          No insight is available at this cutoff. Use Explore to choose an exact
          item and location.
        </p>
        <button onClick={() => go({ page: "explore" })}>
          Explore inventory
        </button>
      </section>
    );
  return (
    <>
      <Notice {...resource} retry={() => setRetry((v) => v + 1)} />
      {data && card?.sku_id && (
        <>
          <section className="selected-context panel">
            <div>
              <p className="eyebrow">
                {card.sku_code} / {card.location}
              </p>
              <h2>
                {card.style}{" "}
                <span className="muted">
                  {card.color} · {card.size}
                </span>
              </h2>
              <p>{card.title}</p>
            </div>
            <div>
              <Badge value={card.category} />
              <Badge value={card.status} />
              <Badge value={card.history_state} />
            </div>
          </section>
          <nav className="journey-tabs" aria-label="Selected key journey">
            {["investigate", "compare", "decide", "history"].map((page) => (
              <button
                key={page}
                disabled={
                  (page === "compare" || page === "decide") &&
                  (resource.stale ||
                    resource.loading ||
                    Boolean(resource.error))
                }
                aria-current={route.page === page ? "step" : undefined}
                onClick={() => go({ page, item: selectedId })}
              >
                {title(page)}
              </button>
            ))}
          </nav>
          {route.page === "history" ? (
            <>
              <Notice {...history} retry={() => setRetry((v) => v + 1)} />
              <History data={history.data} go={go} item={selectedId} />
            </>
          ) : route.page === "compare" || route.page === "decide" ? (
            <><DecisionOptions key={context.archive_digest+context.cutoff+card.id} card={card} context={context} unavailable={resource.stale || resource.loading || Boolean(resource.error)} /><Comparison
              card={card}
              detail={data}
              context={context}
              route={{ ...route, item: selectedId }}
              go={go}
              unavailable={
                resource.stale || resource.loading || Boolean(resource.error)
              }
            /></>
          ) : (
            <div className="detail-grid">
              <section>
                <article className="panel detail-panel">
                  <p className="eyebrow">WHY IT DESERVES ATTENTION</p>
                  <h2>{card.title}</h2>
                  <p className="explanation">{card.explanation}</p>
                  <Facts
                    facts={[
                      ["On hand · pieces", exact(card.on_hand)],
                      ["Daily mean · pieces", exact(card.forecast_daily)],
                      [
                        "Prefix proposal · pieces",
                        exact(card.proposed_order_qty),
                      ],
                      ["Rule exposure", exact(card.exposure)],
                    ]}
                  />
                  {card.reasons?.length > 0 && (
                    <div className="notice warning">
                      <strong>Evidence blockers</strong>
                      <ul>
                        {card.reasons.map((r) => (
                          <li key={r}>{title(r)}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <button
                    className="primary"
                    disabled={
                      resource.stale ||
                      resource.loading ||
                      Boolean(resource.error)
                    }
                    onClick={() => go({ page: "compare", item: selectedId })}
                  >
                    Compare supported responses →
                  </button>
                </article>
                <article className="panel detail-panel">
                  <h3>Calculation trace</h3>
                  <p>
                    Exact saved kernel steps. Forecasts and quantities are not
                    generated by the interface.
                  </p>
                  <Inspector data={data.trace} name="Calculation step" />
                </article>
                <Discovery data={data.insight_discovery} />
                <article className="panel detail-panel">
                  <h3>Capability boundary</h3>
                  <Inspector data={data.capabilities} />
                </article>
              </section>
              <Evidence detail={data} context={context} params={params} />
            </div>
          )}
        </>
      )}
    </>
  );
}
function EvidenceRecords({rows}:{rows:Record<string,any>[]}) {
  if(!rows.length)return <p>No original rows in this section.</p>;
  const columns=Array.from(new Set(rows.flatMap(row=>Object.keys(row))));
  return <div className="table-scroll source-records" tabIndex={0} aria-label="Original evidence records, horizontally scrollable"><table><caption className="sr-only">Original saved evidence, exact values</caption><thead><tr>{columns.map(key=><th key={key}>{title(key)}</th>)}</tr></thead><tbody>{rows.map((row,i)=><tr key={i}>{columns.map(key=><td key={key}>{row[key]!==null&&typeof row[key]==='object'?<details><summary>Record details</summary><Inspector data={row[key]}/></details>:<Inspector data={row[key]}/>}</td>)}</tr>)}</tbody></table></div>;
}
function Evidence({detail,context,params}:{detail:any;context:Context;params:URLSearchParams}) {
  const [section,setSection]=useState("plan"),[page,setPage]=useState(1),[retry,setRetry]=useState(0);
  useEffect(()=>setPage(1),[context.cutoff,detail.id]);
  const query=new URLSearchParams(params);query.set('section',section);query.set('page',String(page));query.set('page_size','20');
  const resource=useResource<any>(section?'/api/product/evidence?'+query:null,retry);
  const current=resource.data&&!resource.stale&&!resource.loading&&!resource.error;
  return <aside className="panel detail-panel evidence-panel"><p className="eyebrow">Evidence inspector</p><h2>Sources behind this claim</h2><p>Business as of <strong>{context.cutoff}</strong>. Original source clocks and identities stay attached to the saved evidence.</p><div className="source-toolbar"><label>Source section<select aria-label="Source section" value={section} onChange={e=>{setSection(e.target.value);setPage(1);}}>{['inventory','training','supply','plan','forecast','reliability'].map(s=><option key={s} value={s}>{title(s)}</option>)}</select></label></div><Notice {...resource} retry={()=>setRetry(v=>v+1)}/>{current&&<><div className="source-coverage"><Badge value={resource.data.status}/><span>{resource.data.total} original rows</span></div><EvidenceRecords rows={resource.data.rows||[]}/><div className="pagination"><button disabled={page<=1} onClick={()=>setPage(v=>v-1)}>Earlier records</button><span>Page {page} of {resource.data.pages||1}</span><button disabled={!resource.data.pages||page>=resource.data.pages} onClick={()=>setPage(v=>v+1)}>More records</button><Download data={resource.data} name={'original-'+section} label="Export original records"/></div></>}<details className="evidence-metadata"><summary>Source identities, clocks & coverage</summary><div className="citation-list">{(detail.references||detail.item?.references||[]).map((ref:any,i:number)=><div key={i}><span>{ref.source}</span><code>{ref.id}</code></div>)}</div><Inspector data={detail.clocks}/><Inspector data={detail.coverage}/><Inspector data={detail.evidence}/><p>Archive hashes check integrity, not producer authenticity.</p></details><Download data={detail} name="selected-inventory-evidence"/></aside>;
}

function History({
  data,
  go,
  item,
}: {
  data: any;
  go: (r: Partial<Route>) => void;
  item: string;
}) {
  if (!data) return <p>Loading comparable cutoffs…</p>;
  return (
    <section className="panel detail-panel">
      <div className="section-heading">
        <div>
          <h2>Saved history</h2>
          <p>
            Independent snapshots, identical key/rules/policy windows. Missing
            coverage is Unknown; stock snapshots do not imply physical
            movements.
          </p>
        </div>
        <Download data={data} name="inventory-history" label="Export history" />
      </div>
      <div className="table-scroll" tabIndex={0}>
        <table>
          <caption>
            Comparability and exact deltas are determined by the saved evidence
            adapter.
          </caption>
          <thead>
            <tr>
              <th>Cutoff</th>
              <th>Insight / change</th>
              <th>On hand · pcs</th>
              <th>Proposal · pcs</th>
              <th>Stock delta · pcs</th>
              <th>Evidence</th>
              <th>Open</th>
            </tr>
          </thead>
          <tbody>
            {(data.points || []).map((point: any) => {
              const c: Card = point.item || point.card || point;
              return (
                <tr key={point.cutoff}>
                  <td>{point.cutoff}</td>
                  <td>
                    <Badge value={c.category} />
                    <small>
                      {title(
                        point.state ||
                          c.history_state ||
                          point.history_state ||
                          "unknown",
                      )}
                    </small>
                    {point.discovery_findings?.map((finding: any) => <small key={finding.id}>{finding.title}</small>)}
                  </td>
                  <td className="numeric">{exact(c.on_hand)}</td>
                  <td className="numeric">{exact(c.proposed_order_qty)}</td>
                  <td className="numeric">
                    {point.comparable ? exact(point.stock_delta) : "Unknown"}
                  </td>
                  <td>
                    <Badge value={c.status} />
                    {c.reasons?.map((r) => (
                      <small key={r}>{title(r)}</small>
                    ))}
                  </td>
                  <td>
                    <button
                      onClick={() =>
                        go({
                          page: "investigate",
                          snapshot: point.cutoff,
                          item,
                        })
                      }
                    >
                      Open cutoff
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <h3>Compatible change evidence</h3>
      <Inspector
        data={
          data.comparison_basis ||
          data.deltas ||
          data.comparability ||
          data.comparison
        }
      />
    </section>
  );
}
const controlLabels: Record<string, string> = {
  demand_percent: "Demand multiplier · percent",
  lead_days: "Declared lead time · days",
  supplier_delay_days: "Hidden supplier delay · days",
  review_days: "Review interval · days",
  inbound_day: "Confirmed inbound day",
  reservation_qty: "Reservation quantity · pieces",
  safety_qty: "Safety quantity · pieces",
  pack_size: "Pack size · pieces",
  moq: "Minimum order · pieces",
  service_target_percent: "Service target · percent",
};
function Comparison({
  card,
  detail,
  context,
  route,
  go,
  unavailable,
}: {
  card: Card;
  detail: any;
  context: Context;
  route: Route;
  go: (r: Partial<Route>) => void;
  unavailable: boolean;
}) {
  const [draft, setDraft] = useState<Record<string, string>>({});
  const [result, setResult] = useState<any>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [loadedKey, setLoadedKey] = useState("");
  const [resultDraft, setResultDraft] = useState("");
  const [invalidShared, setInvalidShared] = useState(false);
  const request = useRef<AbortController | null>(null);
  const key = JSON.stringify([card.id, context.cutoff, context.archive_digest]);
  const generation = useRef(0);
  const activeKey = useRef(key);
  activeKey.current = key;
  const run = async (
    overrides: Record<string, string>,
    signal: AbortSignal,
  ) => {
    const cleaned = scenarioOverrides(overrides);
    const response = await fetch("/api/product/scenario", {
      method: "POST",
      signal,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        cutoff: context.cutoff,
        sku_id: card.sku_id,
        warehouse_id: card.warehouse_id,
        archive_digest: context.archive_digest,
        overrides: cleaned,
      }),
    });
    if (!response.ok)
      throw Error(`Comparison unavailable (${response.status}).`);
    return response.json();
  };
  useEffect(() => {
    ++generation.current;
    const controller = new AbortController();
    request.current?.abort();
    request.current = controller;
    setLoading(true);
    setError("");
    let active = true;
    let initial: Record<string, string> = {};
    try {
      initial = readSharedScenario(route.scenario, Object.keys(controlLabels));
      setInvalidShared(false);
    } catch (error) {
      setInvalidShared(true);
      setError(
        error instanceof Error ? error.message : "Invalid shared assumptions.",
      );
      setLoading(false);
      return () => {
        active = false;
        ++generation.current;
        request.current?.abort();
        controller.abort();
      };
    }
    setDraft(initial);
    run(initial, controller.signal)
      .then((data) => {
        if (active) {
          setResult(data);
          setLoadedKey(key);
          setResultDraft(JSON.stringify(initial));
          setLoading(false);
        }
      })
      .catch((e) => {
        if (active && !controller.signal.aborted) {
          setError(e.message);
          setLoading(false);
        }
      });
    return () => {
      active = false;
      ++generation.current;
      request.current?.abort();
      controller.abort();
    };
  }, [key, route.scenario]);
  const dirty = resultDraft !== JSON.stringify(draft);
  const stale = loadedKey !== key || dirty || Boolean(error) || loading;
  const blocked =
    unavailable ||
    loading ||
    stale ||
    Boolean(error) ||
    card.status !== "assessable";
  const submit = () => {
    const submittedGeneration = generation.current;
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    setLoading(true);
    setError("");
    const submitted = JSON.stringify(draft);
    run(draft, controller.signal)
      .then((data) => {
        if (
          !controller.signal.aborted &&
          generation.current === submittedGeneration &&
          activeKey.current === key
        ) {
          setResult(data);
          setResultDraft(submitted);
          setLoadedKey(key);
          setLoading(false);
          go({ scenario: submitted });
        }
      })
      .catch((e) => {
        if (
          !controller.signal.aborted &&
          generation.current === submittedGeneration &&
          activeKey.current === key
        ) {
          setError(e.message);
          setLoading(false);
        }
      });
  };
  const reset = () => {
    setDraft({});
    if (route.scenario) go({ scenario: "" });
    else {
      const submittedGeneration = generation.current;
      request.current?.abort();
      const controller = new AbortController();
      request.current = controller;
      setLoading(true);
      setError("");
      run({}, controller.signal)
        .then((data) => {
          if (
            !controller.signal.aborted &&
            generation.current === submittedGeneration &&
            activeKey.current === key
          ) {
            setResult(data);
            setResultDraft("{}");
            setLoadedKey(key);
            setLoading(false);
          }
        })
        .catch((e) => {
          if (
            !controller.signal.aborted &&
            generation.current === submittedGeneration &&
            activeKey.current === key
          ) {
            setError(e.message);
            setLoading(false);
          }
        });
    }
  };
  const current = result?.scenario;
  const plan = current?.plan;
  const projection = plan?.projection || [];
  return (
    <>
      <div className="notice">
        <strong>Two policies, explicit assumptions</strong>
        <p>
          The prefix proposal compares known no-order stock with its proposed
          receipt. The periodic simulation separately reorders at reviews. Its
          service/cost metrics are not executed outcomes of the prefix proposal.
          Hidden delay is hypothetical, not observed supplier lateness.
        </p>
      </div>
      {route.page === "compare" && <OneReview key={key} card={card} context={context} unavailable={unavailable} />}
      {route.page === "decide" ? (
        <section className="panel detail-panel">
          <p className="eyebrow">ADVISORY DECISION</p>
          <h2>
            {blocked || current?.status !== "assessable"
              ? "Recommendation withheld"
              : "Review the supported proposal"}
          </h2>
          {blocked || current?.status !== "assessable" ? (
            <p>
              Evidence, comparison or assumptions are unavailable/stale. No
              order quantity is presented for approval.
            </p>
          ) : (
            <>
              <Facts
                facts={[
                  ["Prefix proposal · pieces", exact(plan?.proposed_order_qty)],
                  ["Selected key", `${card.sku_code} / ${card.location}`],
                  ["Business cutoff", context.cutoff],
                  ["Action state", "Advisory · not executed"],
                ]}
              />
              <p>
                Review pre-arrival shortages, receipt timing, pack/MOQ and the
                assumption table before acting. This product does not place
                orders, approve transfers or claim commercial savings.
              </p>
            </>
          )}
          <ul>
            {[...(card.reasons || []), ...(current?.reasons || [])].map(
              (r, i) => (
                <li key={i}>{title(r)}</li>
              ),
            )}
          </ul>
          <button onClick={() => go({ page: "compare" })}>
            Return to exact comparison →
          </button>
          <details>
            <summary>Supported and unsupported actions</summary>
            <Inspector data={detail.capabilities} />
          </details>
        </section>
      ) : (
        <>
          <section className="panel detail-panel">
            <div className="section-heading">
              <div>
                <h2>What-if decision explorer</h2>
                <p>
                  Saved baseline against declared scenario assumptions. Values
                  come from deterministic server calculations.
                </p>
              </div>
              <button onClick={reset}>Reset assumptions</button>
            </div>
            <div className="scenario-presets">
              <button
                disabled={loading || unavailable || invalidShared}
                onClick={() => setDraft({ ...draft, demand_percent: "150" })}
              >
                Demand spike
              </button>
              <button
                disabled={loading || unavailable || invalidShared}
                onClick={() => setDraft({ ...draft, lead_days: "7" })}
              >
                Longer declared lead
              </button>
              <button
                disabled={loading || unavailable || invalidShared}
                onClick={() => setDraft({ ...draft, supplier_delay_days: "3" })}
              >
                Hidden delay hypothesis
              </button>
            </div>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                submit();
              }}
            >
              <div className="control-grid">
                {Object.entries(result?.controls || {})
                  .filter(([name]) => name in controlLabels)
                  .map(([name, spec]: [string, any]) => (
                    <label key={name}>
                      {controlLabels[name]}
                      <input
                        aria-label={controlLabels[name]}
                        disabled={loading || unavailable || invalidShared}
                        type="number"
                        min={spec.min}
                        max={spec.max}
                        step="1"
                        value={
                          draft[name] ??
                          String(result?.parameters?.[name] ?? spec.default)
                        }
                        onChange={(e) =>
                          setDraft({ ...draft, [name]: e.target.value })
                        }
                      />
                      <small>
                        Supported {spec.min}–{spec.max}; saved baseline{" "}
                        {String(
                          result?.baseline?.parameters?.[name] ?? spec.default,
                        )}
                      </small>
                    </label>
                  ))}
              </div>
              <button
                type="submit"
                className="primary"
                disabled={loading || unavailable || invalidShared}
              >
                Run comparison
              </button>
            </form>
            {dirty && (
              <p className="notice warning" role="status">
                Assumptions changed. The displayed result is stale until you run
                comparison.
              </p>
            )}
            {loading && (
              <p className="notice" role="status">
                Calculating supported scenario…
              </p>
            )}
            {error && (
              <div className="notice warning" role="alert">
                <strong>
                  {error}{" "}
                  {result
                    ? "Last successful result retained."
                    : "No successful comparison is available."}
                </strong>
                <p>Decision remains blocked until retry succeeds.</p>
                <button onClick={submit} disabled={invalidShared}>
                  Retry
                </button>
              </div>
            )}
          </section>
          {result && (
            <>
              <section className="panel detail-panel">
                <div className="section-heading">
                  <div>
                    <h2>Exact comparison</h2>
                    <p>
                      {stale
                        ? "Stale result — do not use for a decision."
                        : "Current result · saved source inputs remain unchanged."}
                    </p>
                  </div>
                  <Download
                    data={{
                      ...result,
                      view_binding: {
                        archive_digest: context.archive_digest,
                        contract_version: context.contract_version,
                        cutoff: context.cutoff,
                        sku_id: card.sku_id,
                        warehouse_id: card.warehouse_id,
                      },
                      stale,
                      displayed_assumptions: resultDraft,
                      draft_assumptions: draft,
                    }}
                    name="inventory-comparison"
                    label="Export comparison"
                  />
                </div>
                <div className="table-scroll" tabIndex={0}>
                  <table>
                    <caption>
                      Baseline vs scenario. Exact ratios are authoritative;
                      undefined denominators remain Unknown.
                    </caption>
                    <thead>
                      <tr>
                        <th>Metric / policy</th>
                        <th>Baseline</th>
                        <th>Scenario</th>
                        <th>Exact delta</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(result.comparison?.fields || {}).map(
                        ([name, field]: [string, any]) => (
                          <tr key={name}>
                            <th scope="row">
                              {title(name)}
                              <small>
                                {name === "proposed_order_qty"
                                  ? "Prefix proposal"
                                  : "Periodic simulation / synthetic penalties"}
                              </small>
                            </th>
                            <td className="numeric">{exact(field.baseline)}</td>
                            <td className="numeric">{exact(field.scenario)}</td>
                            <td className="numeric">{exact(field.delta)}</td>
                          </tr>
                        ),
                      )}
                    </tbody>
                  </table>
                </div>
                <Facts
                  facts={[
                    [
                      "Shared scored window · days",
                      String(result.comparison?.scored_days ?? "Unknown"),
                    ],
                    [
                      "Baseline runoff · days",
                      String(
                        result.comparison?.baseline_runoff_days ?? "Unknown",
                      ),
                    ],
                    [
                      "Scenario runoff · days",
                      String(
                        result.comparison?.scenario_runoff_days ?? "Unknown",
                      ),
                    ],
                    ["Action execution", "Unsupported"],
                  ]}
                />
                <Inspector data={result.comparison?.notes} />
                {current?.status !== "assessable" && (
                  <div className="notice warning">
                    <strong>
                      Not assessable · comparison quantities suppressed
                    </strong>
                    <Inspector data={current?.reasons} />
                  </div>
                )}
              </section>
              <section className="panel detail-panel">
                <h2>Prefix stock: no order vs proposal</h2>
                <p>
                  Known stock/receipts/reservations, declared arrival and
                  accepted-demand mean. This is an exact projection, not
                  realized inventory or the periodic simulation.
                </p>
                <div className="table-scroll" tabIndex={0}>
                  <table>
                    <caption>
                      Projected piece balances for the selected scenario.
                    </caption>
                    <thead>
                      <tr>
                        <th>Day</th>
                        <th>Demand</th>
                        <th>Receipt</th>
                        <th>No-order balance</th>
                        <th>With proposal</th>
                      </tr>
                    </thead>
                    <tbody>
                      {projection.map((row: any, i: number) => (
                        <tr key={i}>
                          <td>{row.day ?? row.date ?? i}</td>
                          <td className="numeric">{exact(row.forecast)}</td>
                          <td className="numeric">
                            {exact(row.receipts ?? row.inbound)}
                          </td>
                          <td className="numeric">
                            {exact(
                              row.balance_without_order ?? row.balance_no_order,
                            )}
                          </td>
                          <td className="numeric">
                            {exact(row.balance_with_order)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {!projection.length && (
                  <p>No assessable projection is available.</p>
                )}
                <button
                  className="primary"
                  disabled={blocked}
                  onClick={() => go({ page: "decide" })}
                >
                  Review advisory decision →
                </button>
                <details>
                  <summary>
                    Scenario evidence and exact accounting windows
                  </summary>
                  <Inspector data={current?.costs} />
                  <Inspector data={current?.risk} />
                  <Inspector data={current?.trace} />
                </details>
              </section>
            </>
          )}
        </>
      )}
    </>
  );
}
function OneReview({ card, context, unavailable }: {card: Card; context: Context; unavailable: boolean}) {
  const [quantity, setQuantity] = useState("");
  const [delay, setDelay] = useState("0");
  const [submitted, setSubmitted] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);
  const params = new URLSearchParams({cutoff:context.cutoff,sku_id:card.sku_id,warehouse_id:card.warehouse_id,archive_digest:context.archive_digest,delay_days:delay});
  if(quantity) params.set("quantity",quantity);
  const path="/api/product/contrast?"+params;
  const resource = useResource<any>(submitted,retry);
  const stale=unavailable || submitted!==path || resource.stale || resource.loading || Boolean(resource.error);
  return <section className="panel detail-panel" aria-label="One-review execution comparison">
    <h2>One-review execution comparison</h2>
    <p>Actual saved prefix proposal versus no action and an optional alternative quantity. Uses saved inputs, independently of the periodic scenario controls below. FIFO execution over 28 declared demand days plus 5 common closure days, with no later orders. Supplier capacity and calendars remain unverified.</p>
    <label>Alternative order · pieces <input aria-label="Alternative order · pieces" type="number" min="0" max="2000" step="1" value={quantity} onChange={e=>setQuantity(e.target.value)} /></label>
    <label>Declared order delay · days <input aria-label="Declared order delay · days" type="number" min="0" max="3" step="1" value={delay} onChange={e=>setDelay(e.target.value)} /></label>
    <button disabled={unavailable || (Boolean(submitted) && resource.loading)} onClick={()=>{setSubmitted(path);setRetry(v=>v+1);}}>Compare one review</button>
    {submitted && <Notice {...resource} retry={()=>setRetry(v=>v+1)} />}
    {resource.data && <>
      {stale && <p role="status">Inputs changed or unavailable · saved contrast is stale.</p>}
      <p>{resource.data.semantics}</p>
      {resource.data.arms ? <div className="table-scroll" tabIndex={0}><table><caption>Common 33-day paid outcomes · synthetic cost units</caption><thead><tr><th>Decision</th><th>Quantity</th><th>Immediate new fill</th><th>Eventual new fill</th><th>Terminal backlog</th><th>Total paid cost</th></tr></thead><tbody>{Object.entries(resource.data.arms).map(([name,arm]:[string,any])=><tr key={name}><td>{title(name)}</td><td>{arm.quantity}</td><td>{arm.immediate_fulfilled}/{arm.accepted}</td><td>{arm.eventual_fulfilled}/{arm.accepted}</td><td>{arm.terminal_backlog}</td><td>{arm.total_cost}</td></tr>)}</tbody></table></div>:<p>Not assessable · {resource.data.reasons.join(", ")}</p>}
      <Inspector data={resource.data} name="Paid execution evidence" />
      <Download data={{...resource.data,stale}} name="one-review-contrast" label="Export one-review comparison" />
    </>}
  </section>;
}
createRoot(document.getElementById("root")!).render(<App />);
