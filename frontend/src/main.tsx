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
import "./style.css";

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
          <a className="brand" href="#/overview">
            <span className="brand-icon" aria-hidden="true">
              ▤
            </span>
            <span>
              Inventory
              <br />
              <strong>Intelligence</strong>
            </span>
          </a>
          <div className="workspace-label">DECISION WORKBENCH</div>
          <nav aria-label="Product navigation">
            {pages.map((page: string, i: number) => (
              <a
                key={page}
                href={routeHash({ ...route, page })}
                aria-current={route.page === page ? "page" : undefined}
              >
                <span className="nav-index" aria-hidden="true">
                  {String(i + 1).padStart(2, "0")}
                </span>
                {title(page)}
              </a>
            ))}
          </nav>
          <div className="sidebar-footer">
            <span className="badge synthetic">Synthetic workspace</span>
            <p>
              Saved evidence. Exact pieces.
              <br />
              Advisory decisions.
            </p>
            <a href="/lab">Open Scenario Lab ↗</a>
          </div>
        </aside>
        <div className="workspace">
          <header className="topbar">
            <span className="breadcrumb">
              Inventory / <strong>{title(route.page)}</strong>
            </span>
            <span className="read-only">{route.page === "execution" ? "Synthetic research · No real orders" : "Read only · No order execution"}</span>
          </header>
          <main id="main" tabIndex={-1}>
            <div className="page-heading">
              <div>
                <p className="eyebrow">INVENTORY DECISION JOURNEY</p>
                <h1 ref={focus} tabIndex={-1}>
                  {route.page === "overview"
                    ? "Focus on the decisions that matter"
                    : title(route.page)}
                </h1>
                <p className="subtitle">
                  {
                    (
                      {
                        overview:
                          "Discover risk, opportunity and evidence gaps from saved synthetic outputs.",
                        explore:
                          "Explore exact stock by style, color, size and location.",
                        investigate:
                          "Understand the trigger, its assumptions and original evidence.",
                        compare:
                          "Compare supported assumptions without changing operational inputs.",
                        decide:
                          "Review the advisory proposal and the boundaries of this decision.",
                        history:
                          "See what appeared, persisted or changed across saved cutoffs.",
                        execution:
                          "Inspect actual synthetic planner outcomes and trace commitments through receipts.",
                      } as Record<string, string>
                    )[route.page]
                  }
                </p>
              </div>
            </div>
            {route.page !== "execution" && <><div className="context-bar">
              <label>
                Cutoff
                <select
                  aria-label="Cutoff"
                  value={route.snapshot || context?.cutoff || ""}
                  onChange={(e) =>
                    navigate({ snapshot: e.target.value, offset: 0 })
                  }
                >
                  {context?.cutoffs.map((c) => (
                    <option key={c}>{c}</option>
                  ))}
                </select>
              </label>
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
            </div>
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
            <div className="view-tools">
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
            </div>
            </>}
            {route.page === "execution" ? <Execution /> : context && !bound && !overview.stale && (
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
            <footer className="product-footer">
              <strong>Evidence before action.</strong> Synthetic inputs do not
              demonstrate commercial savings. Transfers, real purchase execution and
              observed supplier lateness are unsupported.{" "}
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
                <small>{title(card.history_state)}</small>
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
function Overview({
  data,
  route,
  go,
}: {
  data: Context;
  route: Route;
  go: (r: Partial<Route>) => void;
}) {
  return (
    <>
      <section className="summary-grid" aria-label="Workspace coverage">
        {[
          ["keys", "Inventory keys"],
          ["assessable", "Assessable keys"],
          ["blocked", "Blocked keys"],
          ["risk", "Risk signals"],
        ].map(([key, label]) => (
          <div className="stat" key={key}>
            <span>{label}</span>
            <strong>{data.summary[key] ?? "Unavailable"}</strong>
            <small>
              {key === "keys"
                ? "SKU × location"
                : key === "assessable"
                  ? "Complete selected evidence"
                  : key === "blocked"
                    ? "Recommendation withheld"
                    : "Deterministic rule triggers"}
            </small>
          </div>
        ))}
      </section>
      <div className="section-heading">
        <div>
          <h2>Attention queue</h2>
          <p>
            Prioritized by evidence state and deterministic exposure, not an AI
            confidence score.
          </p>
        </div>
        <button onClick={() => go({ page: "explore", offset: 0 })}>
          Explore all items →
        </button>
      </div>
      <div className="preset-grid">
        {[
          [
            "risk",
            "At-risk stock",
            "Review projected shortages and supported responses.",
          ],
          [
            "opportunity",
            "Excess stock",
            "Inspect surplus with passing source evidence.",
          ],
          [
            "evidence",
            "Untrusted evidence",
            "Resolve incomplete evidence before a proposal.",
          ],
        ].map(([type, label, desc]) => (
          <button
            className={`preset ${type}`}
            key={type}
            onClick={() => go(preset(route, type))}
          >
            <span>
              <Badge value={type} />{" "}
              <span className="preset-count">{data.summary[type]} signals</span>
            </span>
            <strong>{label} →</strong>
            <span>{desc}</span>
          </button>
        ))}
      </div>
      <section className="panel">
        <CardTable items={data.highlights} go={go} />
      </section>
      <Discovery data={data.insight_discovery} go={go} />
      {data.controls?.duplicate_inventory && <DuplicateControl context={data} />}
      <div className="note-grid">
        <section className="panel note">
          <h3>What this workspace can tell you</h3>
          <p>
            Exact stock, accepted demand, confirmed supply and prefix planning
            proposals from independently saved synthetic runs.
          </p>
        </section>
        <section className="panel note">
          <h3>What still needs human review</h3>
          <p>
            Forecast uncertainty is uncalibrated. Proposed pieces are advisory;
            a separate periodic simulation does not prove the actual proposal's
            outcome.
          </p>
          <a href="/lab">Inspect the original Scenario Lab →</a>
        </section>
      </div>
    </>
  );
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
      <Inspector data={{values:finding.values,references:finding.references,known_at:finding.known_at}} name="Insight evidence" />
      {go && <button onClick={() => go({page:"investigate",item: finding.sku_id+"|"+finding.warehouse_id})}>Investigate finding →</button>}
    </article>)}
    {data.unknown.length > 0 && <details><summary>Evidence gaps ({data.total_unknown ?? data.unknown.length})</summary><Inspector data={data.unknown} name="Unknown evidence" /></details>}
    <Download data={data} name="insight-discovery-v2" label="Export insight discovery" />
  </section>;
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
            <Comparison
              card={card}
              detail={data}
              context={context}
              route={{ ...route, item: selectedId }}
              go={go}
              unavailable={
                resource.stale || resource.loading || Boolean(resource.error)
              }
            />
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
function Evidence({
  detail,
  context,
  params,
}: {
  detail: any;
  context: Context;
  params: URLSearchParams;
}) {
  const [section, setSection] = useState("");
  const [page, setPage] = useState(1);
  const [retry, setRetry] = useState(0);
  const query = new URLSearchParams(params);
  query.set("section", section);
  query.set("page", String(page));
  query.set("page_size", "20");
  const resource = useResource<any>(
    section ? "/api/product/evidence?" + query : null,
    retry,
  );
  return (
    <aside className="panel detail-panel evidence-panel">
      <p className="eyebrow">EVIDENCE INSPECTOR</p>
      <h2>Sources behind this claim</h2>
      <p>
        Business as of <strong>{context.cutoff}</strong>. Known-at/source clocks
        remain attached to each original row. Archive hashes check integrity,
        not producer authenticity.
      </p>
      <div className="citation-list">
        {(detail.references || detail.item?.references || []).map(
          (ref: any, i: number) => (
            <div key={i}>
              <span>{ref.source}</span>
              <code>{ref.id}</code>
            </div>
          ),
        )}
      </div>
      <h3>Clocks and coverage</h3>
      <Inspector data={detail.clocks} />
      <Inspector data={detail.coverage} />
      <Inspector data={detail.evidence} />
      <label>
        Source section
        <select
          aria-label="Source section"
          value={section}
          onChange={(e) => {
            setSection(e.target.value);
            setPage(1);
          }}
        >
          <option value="">Select original records</option>
          {[
            "inventory",
            "training",
            "supply",
            "plan",
            "forecast",
            "reliability",
          ].map((s) => (
            <option key={s} value={s}>
              {title(s)}
            </option>
          ))}
        </select>
      </label>
      {section && (
        <>
          <Notice {...resource} retry={() => setRetry((v) => v + 1)} />
          {resource.data && (
            <>
              <Inspector data={resource.data} />
              <div className="pagination">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((v) => v - 1)}
                >
                  Earlier records
                </button>
                <button
                  disabled={!resource.data.pages || page >= resource.data.pages}
                  onClick={() => setPage((v) => v + 1)}
                >
                  More records
                </button>
              </div>
            </>
          )}
        </>
      )}
      <Download data={detail} name="selected-inventory-evidence" />
    </aside>
  );
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
