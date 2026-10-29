import React, { useEffect, useRef, useState } from 'react';
import { ArrowRight, RotateCcw, SlidersHorizontal } from 'lucide-react';
import type { Context, Exact, Route } from './types';
import { Download, exact, Notice, useResource } from './resources';
import { ViewNav } from './ui';
import './demand.css';

type Point = { day: string; end_day: string; period: string; history: Exact; baseline: Exact; adjusted: Exact; day_count: number; partial: boolean };
type Projection = { day: string; balance_without_order: Exact; balance_with_order: Exact };
type Plan = { proposed_order_qty: Exact; order_arrival_day: string; pre_arrival_shortage_days: string[]; projection: Projection[] };
type Demand = {
  contract_version: string; archive_digest: string; calculation_digest: string; cutoff: string;
  sku_id: string; warehouse_id: string; method: string; horizon: number; protection_days: number;
  forecast_status: string; forecast_reasons: string[]; daily: Point[]; weekly: Point[];
  totals: { historical_daily_mean: Exact; baseline: Exact; adjusted: Exact; delta: Exact };
  methods: { method: string; total: Exact }[];
  accuracy: { reason: string };
  impact: { status: string; reasons: string[]; baseline: Plan | null; adjusted: Plan | null; order_delta: Exact; explanation: string; protection_start: string; protection_end: string };
  clocks: { business_timezone: string; known_at: string; training_start: string; training_end_inclusive: string };
  references: { source: string; id: string }[];
};
type Draft = { kind: string; value: string; start_day: string; end_day: string };
const methodNames: Record<string, string> = { mean: 'Historical mean', naive: 'Last observed day', seasonal_naive: 'Weekly seasonal' };
const shortDate = (value: string) => value.slice(5).replace('-', '/');
const reason = (value: string) => value.replaceAll('_', ' ');

// Approximate coordinates only. All demand, order, aggregation and delta arithmetic is server-owned.
function plotNumber(value: Exact): number | null {
  if (value === null) return null;
  return typeof value === 'string' ? Number(value) : Number(value.numerator) / Number(value.denominator);
}

function DemandChart({ rows, grain }: { rows: Point[]; grain: string }) {
  const [selected, setSelected] = useState<number | null>(null);
  const container = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(980);
  useEffect(() => setSelected(null), [rows]);
  useEffect(() => {
    const observer = new ResizeObserver(entries => setWidth(Math.max(240, Math.min(980, entries[0].contentRect.width))));
    if (container.current) observer.observe(container.current);
    return () => observer.disconnect();
  }, []);
  const fields = ['history', 'baseline', 'adjusted'] as const;
  const numbers = rows.flatMap(row => fields.map(field => plotNumber(row[field]))).filter((v): v is number => v !== null);
  const maximum = Math.max(1, ...numbers) * 1.15;
  const x = (i: number) => 52 + i * ((width-70) / Math.max(1, rows.length - 1));
  const y = (v: number) => 284 - v / maximum * 220;
  const firstFuture = rows.findIndex(row => row.period === 'forecast');
  const boundary = firstFuture > 0 ? (x(firstFuture - 1) + x(firstFuture)) / 2 : 52;
  const point = selected === null ? null : rows[selected];
  return <>
    <div ref={container} className="demand-chart-scroll" aria-label="Demand chart">
      <svg className="demand-chart" viewBox={`0 0 ${width} 332`} role="img" aria-labelledby="demand-chart-title demand-chart-desc">
        <title id="demand-chart-title">Historical accepted demand and future demand forecast</title>
        <desc id="demand-chart-desc">{grain === 'daily' ? 'Daily expected pieces' : 'Calendar-week pieces, partial weeks use covered days only'}. Historical demand is gray, baseline forecast is violet and adjusted forecast is green. Missing values are gaps. Exact values are available below the chart.</desc>
        <rect x={boundary} y="45" width={width-12-boundary} height="239" className="forecast-region" />
        {[0, 1, 2, 3, 4].map(i => <g key={i}><line x1="52" x2={width-12} y1={y(maximum*i/4)} y2={y(maximum*i/4)} className="chart-grid"/><text x="40" y={y(maximum*i/4)+4} textAnchor="end">{(maximum*i/4).toLocaleString(undefined, {maximumFractionDigits: 1})}</text></g>)}
        <line x1={boundary} x2={boundary} y1="43" y2="285" className="forecast-divider"/>
        <text x="52" y="24" className="chart-period">{width < 550 ? 'History' : 'Historical demand'}</text>
        <text x={boundary+12} y="24" className="chart-period">{width < 550 ? 'Forecast' : 'Future forecast'}</text>
        {fields.map(field => {
          let path = ''; let connected = false;
          rows.forEach((row, i) => {
            const n = plotNumber(row[field]);
            if (n === null) { connected = false; return; }
            path += `${connected ? 'L' : 'M'}${x(i)},${y(n)} `; connected = true;
          });
          return <path key={field} d={path} className={`demand-line line-${field}`} />;
        })}
        {rows.map((row, i) => {
          const n = plotNumber(row.adjusted ?? row.history);
          return n === null ? null : <circle key={i} cx={x(i)} cy={y(n)} r="6" className="chart-point" tabIndex={0}
            aria-label={`${row.period === 'history' ? 'Historical' : 'Forecast'} ${row.day}${row.partial ? `, partial week, ${row.day_count} days` : ''}: historical ${exact(row.history)}, baseline ${exact(row.baseline)}, adjusted ${exact(row.adjusted)}`}
            onMouseEnter={() => setSelected(i)} onFocus={() => setSelected(i)} onClick={() => setSelected(i)}>
            <title>{row.day} · {row.partial ? `${row.day_count}-day partial week · ` : ''}Historical {exact(row.history)} · Baseline {exact(row.baseline)} · Adjusted {exact(row.adjusted)}</title>
          </circle>;
        })}
        {rows.map((row, i) => i === 0 || i === firstFuture || i === rows.length-1 || i === Math.floor(firstFuture/2) || i === Math.floor((firstFuture+rows.length-1)/2)
          ? <text key={i} x={x(i)} y="313" textAnchor="middle">{shortDate(row.day)}</text> : null)}
      </svg>
    </div>
    <div className="chart-legend"><span className="legend-history">Historical accepted demand</span><span className="legend-baseline">Baseline forecast</span><span className="legend-adjusted">Adjusted forecast</span></div>
    <p className="chart-inspection" aria-live="polite">{point ? <>{point.day}{point.end_day !== point.day ? ` – ${point.end_day}` : ''}{point.partial ? ` · Partial week: ${point.day_count} covered days` : ''} · {point.period === 'history' ? `Historical: ${exact(point.history)}` : `Baseline: ${exact(point.baseline)} · Adjusted: ${exact(point.adjusted)}`} pieces</> : <>Hover or focus a point for exact values. {grain === 'weekly' ? 'Partial weeks show only their covered days.' : 'Expected demand may include fractional pieces.'}</>}</p>
  </>;
}

export function DemandPlanning({ context, route, go }: { context: Context; route: Route; go: (patch: Partial<Route>) => void }) {
  const [horizon, setHorizon] = useState(28);
  const [method, setMethod] = useState('mean');
  const [grain, setGrain] = useState('daily');
  const skus = context.dimensions.skus as {sku_id: string; sku_code: string; color: string; size: string}[];
  const warehouses = context.dimensions.warehouses as {warehouse_id: string; name: string}[];
  const [sku, warehouse] = route.item ? route.item.split('|') : [skus[0].sku_id, warehouses[0].warehouse_id];
  const validSku = skus.some(s => s.sku_id === sku);
  const validWarehouse = warehouses.some(w => w.warehouse_id === warehouse);
  const query = new URLSearchParams({cutoff: context.cutoff, sku_id: sku, warehouse_id: warehouse || '', archive_digest: context.archive_digest, horizon: String(horizon), method});
  return <section className="demand-workspace" aria-label="Demand Planning workspace">
    <div className="demand-intro"><div><h2>What if demand changes?</h2><p>Choose an item and horizon, apply a temporary adjustment, then compare the forecast and advisory order below.</p></div><button disabled={!validSku || !validWarehouse} onClick={()=>go({page:'investigate',item:`${sku}|${warehouse}`,scenario:''})}>Inspect this item's evidence<ArrowRight size={16}/></button><small>Investigation uses saved inventory evidence. Temporary adjustments are not carried into other workspaces.</small></div>
    <div className="demand-scope panel">
      <label>Item / SKU<select aria-label="Demand SKU" value={sku} onChange={e => go({item: `${e.target.value}|${warehouse || ''}`})}>{!validSku && <option value={sku}>{sku} · unavailable</option>}{skus.map(s => <option value={s.sku_id} key={s.sku_id}>{s.sku_code} · {s.color} / {s.size}</option>)}</select></label>
      <label>Location<select aria-label="Demand location" value={warehouse || ''} onChange={e => go({item: `${sku}|${e.target.value}`})}>{!validWarehouse && <option value={warehouse || ''}>{warehouse || 'Missing location'} · unavailable</option>}{warehouses.map(w => <option value={w.warehouse_id} key={w.warehouse_id}>{w.name}</option>)}</select></label>
      <label>Forecast horizon<select aria-label="Forecast horizon" value={horizon} onChange={e => setHorizon(Number(e.target.value))}>{[7,14,28].map(h => <option key={h} value={h}>{h} days</option>)}</select></label>
    </div>
    {validSku && validWarehouse ? <PlanningSelection key={query.toString()} query={query.toString()} grain={grain} setGrain={setGrain} setMethod={setMethod}/> : <div className="notice warning" role="alert"><p>This item or location is unavailable in the current archive. Choose an available selection above.</p><button onClick={()=>go({item:''})}>Use first available item</button></div>}
  </section>;
}

function PlanningSelection({query, grain, setGrain, setMethod}: {query: string; grain: string; setGrain: (v: string) => void; setMethod: (v: string) => void}) {
  const [retry, setRetry] = useState(0);
  const resource = useResource<Demand>('/api/product/demand?' + query, retry);
  return <><Notice {...resource} retry={() => setRetry(v => v+1)}/>
    {resource.data && !resource.loading && !resource.stale && !resource.error && <PlanningEditor base={resource.data} grain={grain} setGrain={setGrain} setMethod={setMethod}/>}</>;
}

function PlanningEditor({base, grain, setGrain, setMethod}: {base: Demand; grain: string; setGrain: (v: string) => void; setMethod: (v: string) => void}) {
  const initial: Draft = {kind: 'percent', value: '25', start_day: base.cutoff, end_day: base.daily[base.daily.length-1].day};
  const [draft, setDraft] = useState<Draft>(initial);
  const [scenario, setScenario] = useState<Demand | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const request = useRef<AbortController | null>(null);
  const generation = useRef(0);
  useEffect(() => () => {generation.current++; request.current?.abort();}, []);
  const invalidate = () => { generation.current++; request.current?.abort(); setLoading(false); setScenario(null); setError(''); };
  const edit = (patch: Partial<Draft>) => { invalidate(); setDraft(v => ({...v, ...patch})); };
  const result = scenario || base;
  const impact = result.impact;
  const apply = async (event: React.FormEvent) => {
    event.preventDefault(); invalidate();
    if (!/^[+-]?\d+$/.test(draft.value) || !Number.isSafeInteger(Number(draft.value))) {
      setError('Enter a signed whole number.'); return;
    }
    const token = ++generation.current;
    const controller = new AbortController(); request.current = controller; setLoading(true);
    try {
      const response = await fetch('/api/product/demand-scenario', {method: 'POST', signal: controller.signal,
        headers: {'Content-Type': 'application/json'}, body: JSON.stringify({cutoff: base.cutoff, sku_id: base.sku_id,
          warehouse_id: base.warehouse_id, archive_digest: base.archive_digest, horizon: base.horizon, method: base.method,
          adjustment: {...draft, value: Number(draft.value)}})});
      const data = await response.json();
      if (!response.ok) throw Error(typeof data.detail === 'string' ? data.detail : `Invalid adjustment (${response.status}). Check the whole number and date range.`);
      if (generation.current === token && !controller.signal.aborted) setScenario(data);
    } catch (e) {
      if (generation.current === token && !controller.signal.aborted) setError((e as Error).message);
    } finally {
      if (generation.current === token) setLoading(false);
    }
  };
  const rows = grain === 'daily' ? result.daily : result.weekly;
  return <>
    <div className="demand-totals" aria-label="Demand totals">
      <div><span>Historical daily mean</span><strong>{exact(result.totals.historical_daily_mean)}<small> pcs / day</small></strong><small>28 historical days · gaps are unavailable</small></div>
      <div><span>Baseline demand</span><strong>{exact(result.totals.baseline)}<small> pcs</small></strong><small>{base.horizon} future days · {methodNames[base.method]}</small></div>
      <div className={scenario ? 'adjustment-applied' : ''}><span>Adjusted demand</span><strong>{exact(result.totals.adjusted)}<small> pcs</small></strong><small>{scenario ? `Change: ${exact(result.totals.delta)} pieces` : 'Baseline · no adjustment applied'}</small></div>
    </div>
    <section className="panel detail-panel demand-visual">
      <div className="section-heading"><div><h2>Demand forecast</h2><p>History through {base.clocks.training_end_inclusive} · Forecast from {base.cutoff}</p></div><ViewNav label="Demand time view" value={grain} onChange={setGrain} options={[["daily","Daily"],["weekly","Weekly"]]}/></div>
      {base.forecast_status !== 'assessable' && <p className="notice warning" role="alert">Forecast unavailable: {base.forecast_reasons.map(reason).join(' · ')}. Missing demand is not zero.</p>}
      <p className="demand-chart-unit">{grain === 'daily' ? 'Pieces per day' : 'Pieces per calendar week · partial periods labeled below'} · Point forecasts; uncertainty is not quantified.</p>
      <DemandChart rows={rows} grain={grain}/>
      <div className="demand-methods" aria-label="Forecast methods">{base.methods.map(m => <button key={m.method} aria-pressed={base.method === m.method} onClick={() => setMethod(m.method)}><span>{methodNames[m.method]}{m.method === 'mean' && <small>Operational default</small>}</span><strong>{exact(m.total)}<small> pcs / {base.horizon} days</small></strong></button>)}</div>
      <p className="demand-method-note">Baselines can agree when historical demand is constant. Choosing one here does not change the operational default.</p>
      <p className="demand-accuracy"><strong>Per-item accuracy unavailable.</strong> {base.accuracy.reason} <a href="#/evaluation">Inspect the separate saved evaluation study</a>.</p>
      <details className="demand-records"><summary>Exact {grain} demand values{grain === 'weekly' ? ' and period coverage' : ''}</summary><div className="table-scroll" tabIndex={0}><table><caption>Accepted historical demand and expected future demand · exact pieces</caption><thead><tr><th>Period</th><th>Dates / coverage</th><th>Historical</th><th>Baseline</th><th>Adjusted</th></tr></thead><tbody>{rows.map((r,i) => <tr key={i}><td>{r.period === 'history' ? 'Historical' : 'Future'}</td><td>{r.day}{r.end_day !== r.day && ` – ${r.end_day}`}{r.partial && <small>Partial week · {r.day_count} days</small>}</td><td>{r.period === 'history' ? exact(r.history) : '—'}</td><td>{r.period === 'forecast' ? exact(r.baseline) : '—'}</td><td>{r.period === 'forecast' ? exact(r.adjusted) : '—'}</td></tr>)}</tbody></table></div></details>
    </section>
    <div className="demand-planning-grid">
      <section className="panel detail-panel demand-adjustment"><h2><SlidersHorizontal size={18}/> Adjust future demand</h2><p>One temporary adjustment. Recorded history stays unchanged.</p>
        <div className="adjustment-presets" aria-label="Example adjustments">{[['percent','25','Try +25%'],['percent','-25','Try −25%'],['pieces','1','Try +1 piece/day']].map(([kind,value,label])=><button type="button" key={label} disabled={base.forecast_status !== 'assessable'} onClick={()=>edit({kind,value})}>{label}</button>)}</div>
        <p className="field-help">Examples fill the draft for the dates below. Select Apply adjustment to calculate.</p>
        <form onSubmit={apply}>
          <label>Adjustment type<select aria-label="Adjustment type" value={draft.kind} onChange={e => edit({kind:e.target.value})}><option value="percent">Percentage change</option><option value="pieces">Pieces per day</option></select></label>
          <label>{draft.kind === 'percent' ? 'Change · %' : 'Change · whole pieces / day'}<input aria-label="Demand change" type="text" inputMode="text" required value={draft.value} onChange={e => edit({value:e.target.value})} aria-describedby="demand-adjustment-help"/></label>
          <p id="demand-adjustment-help" className="field-help">{draft.kind === 'percent' ? '−100 to +100%. For example, +25 increases the baseline by 25%.' : '−1000 to +1000 whole expected pieces each selected day.'} Negative resulting demand is rejected.</p>
          <div className="demand-dates"><label>From<input aria-label="Adjustment from" type="date" min={base.cutoff} max={initial.end_day} value={draft.start_day} required onChange={e => edit({start_day:e.target.value})}/></label><label>Through<input aria-label="Adjustment through" type="date" min={base.cutoff} max={initial.end_day} value={draft.end_day} required onChange={e => edit({end_day:e.target.value})}/></label></div>
          <div className="demand-actions"><button className="primary" disabled={loading || base.forecast_status !== 'assessable'} type="submit">{loading ? 'Calculating…' : 'Apply adjustment'}<ArrowRight size={16}/></button><button type="button" onClick={() => {invalidate(); setDraft({...initial, value:'0'});}}><RotateCcw size={15}/>Reset</button></div>
        </form>
        <div aria-live="polite">{loading && <p role="status">Calculating adjustment. Showing baseline until the comparison is ready.</p>}{error && <p className="notice warning" role="alert">{error} Showing baseline; no adjustment is applied.</p>}{scenario && <p className="demand-applied">Temporary adjustment applied. No business plan or order is saved.</p>}</div>
        <p className="field-help">Changing item, cutoff, method or horizon resets the temporary adjustment.</p>
      </section>
      <section className="panel detail-panel demand-impact" aria-label="Inventory impact"><h2>Inventory & replenishment impact</h2>
        <p><strong>{base.protection_days}-day protection window</strong> · {impact.protection_start} through {impact.protection_end}. The demand view covers {base.horizon} days; today’s proposal protects lead time plus review interval.</p>
        {impact.status === 'assessable' ? <><div className="demand-order-comparison"><div><span>Baseline order</span><strong>{exact(impact.baseline?.proposed_order_qty)}<small> pcs</small></strong></div><ArrowRight size={20}/><div><span>Adjusted order</span><strong>{exact(impact.adjusted?.proposed_order_qty)}<small> pcs</small></strong></div></div><p>Order change: <strong>{exact(impact.order_delta)} pieces</strong> · Proposed arrival: {impact.adjusted?.order_arrival_day}</p></> : <p className="notice warning" role="alert">Replenishment blocked: {impact.reasons.map(reason).join(' · ')}. No order quantity is inferred.</p>}
        <p className="demand-impact-explanation">{impact.explanation}</p>
        {impact.baseline && impact.adjusted && <><p>Pre-arrival shortage exposure: baseline {impact.baseline.pre_arrival_shortage_days.length} day(s); adjusted {impact.adjusted.pre_arrival_shortage_days.length} day(s). A later order cannot repair these earlier deficits.</p><details><summary>Daily projected balances</summary><p>Expected net inventory after each side’s advisory order. Negative balances indicate modeled deficits, not physical negative stock or observed stockouts.</p><div className="table-scroll" tabIndex={0}><table><caption>Protection-window projection · exact expected pieces</caption><thead><tr><th>Day</th><th>Baseline with proposal</th><th>Adjusted with proposal</th></tr></thead><tbody>{impact.baseline.projection.map((r,i) => <tr key={r.day}><td>{r.day}</td><td>{exact(r.balance_with_order)}</td><td>{exact(impact.adjusted!.projection[i].balance_with_order)}</td></tr>)}</tbody></table></div></details></>}
      </section>
    </div>
    <div className="demand-export"><div><strong>{scenario ? 'Adjusted comparison' : 'Baseline comparison'}</strong><small>Synthetic · temporary · no operational writes</small></div>{!loading && <Download data={result} name="demand-planning-comparison" label="Export comparison"/>}</div>
    <details className="panel detail-panel demand-provenance"><summary>Sources, clocks & planning limits</summary><p>Business calendar: {base.clocks.business_timezone}. Evidence known at {base.clocks.known_at}. Forecasts use earlier recorded accepted demand, not shipments or future outcomes. No prediction intervals, achieved service or commercial savings are calculated.</p><p>Method selection here does not change the operational mean default. Inventory projections reuse prefix-stock-v1 with saved supply and policy.</p><dl><dt>Calculation</dt><dd><code>{result.calculation_digest}</code></dd><dt>Source archive</dt><dd><code>{base.archive_digest}</code></dd>{base.references.map(r => <React.Fragment key={r.id}><dt>{r.source}</dt><dd><code>{r.id}</code></dd></React.Fragment>)}</dl></details>
  </>;
}
