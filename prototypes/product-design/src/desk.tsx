import { useState } from 'react';
import { Boxes, LayoutDashboard, ListFilter, ScanLine, GitCompareArrows, ClipboardCheck, History, Activity, ShieldCheck, ChevronRight, ArrowUpRight, Search, PanelRightClose, PanelRightOpen, SlidersHorizontal, CircleDot, ArrowRight, CalendarDays, Layers3, Database, Command, X } from 'lucide-react';
import { type Workspace, Badge, Notice, DataTable, EvidencePanel, ComparisonPanel, DecisionPanel, HistoryPanel, ExecutionPanel, EvaluationPanel, Export, exact, dateLabel, label } from './shared';
import './desk.css';

const navigation = [
  {page:'overview', name:'Overview', icon:LayoutDashboard},
  {page:'explore', name:'Inventory', icon:ListFilter},
  {page:'investigate', name:'Evidence', icon:ScanLine},
  {page:'compare', name:'Compare', icon:GitCompareArrows},
  {page:'decide', name:'Decision', icon:ClipboardCheck},
  {page:'history', name:'History', icon:History},
  {page:'execution', name:'Execution', icon:Activity},
  {page:'evaluation', name:'Evaluation', icon:ShieldCheck},
];
const descriptions:Record<string,string> = {
  overview:'Your inventory attention queue, with the evidence one click away.',
  explore:'Filter the saved inventory. Select a row to inspect its context.',
  investigate:'Trace the selected item from original inputs to the saved proposal.',
  compare:'Compare explicit alternatives against the saved baseline.',
  decide:'Review the advisory decision and its boundaries.',
  history:'Reopen immutable observations across business cutoffs.',
  execution:'Inspect saved planner reviews and execution feedback.',
  evaluation:'Inspect the saved synthetic end-to-end evaluation.',
};

function Context({w}:{w:Workspace}) {
  const d=w.detail.data;
  return <>
    <div className="desk-inspector-label"><span><ScanLine size={14}/> Item context</span><span className="desk-live-dot"/></div>
    <Notice resource={w.detail}/>
    {d && <>
      <div className="desk-item-heading"><div className="desk-swatch" data-color={d.color}/><div><h2>{d.sku_code}</h2><p>{d.color} / {d.size}</p></div><Badge value={d.category}/></div>
      <div className="desk-location"><Layers3 size={14}/>{d.location}<span>{label(d.status)}</span></div>
      <div className="desk-context-numbers"><div><span>On hand</span><strong>{exact(d.on_hand)}<small> pieces</small></strong></div><div><span>Proposed order</span><strong>{exact(d.proposed_order_qty)}<small> pieces</small></strong></div></div>
      <div className="desk-context-story"><div className="eyebrow">Saved observation</div><h3>{d.title}</h3><p>{d.explanation}</p><button className="button primary" onClick={()=>w.go({page:'investigate'})}>Inspect original evidence <ArrowUpRight size={14}/></button></div>
      <div className="desk-context-findings"><div className="section-head"><h3>Related findings</h3><span className="desk-count">{d.insight_discovery?.findings?.length ?? 0}</span></div>{d.insight_discovery?.findings?.map((f:any)=><button key={f.id} className="desk-finding-link" onClick={()=>w.go({page:'investigate'})}><span className={'desk-dot '+f.category}/><span>{f.title}<small>{f.rule_id} · {f.references?.length ?? 0} source references</small></span><ChevronRight size={14}/></button>)}{!d.insight_discovery?.findings?.length && <p className="muted">No additional findings in this saved observation.</p>}</div>
      <div className="desk-clock"><span>Business cutoff</span><strong>{dateLabel(w.route.cutoff)}</strong><span>Archive</span><code>{d.archive_digest?.slice(0,12)}…</code></div>
      <div className="desk-context-actions"><button className="button" onClick={()=>w.go({page:'compare'})}><GitCompareArrows size={14}/> Compare</button><button className="button" onClick={()=>w.go({page:'history'})}><History size={14}/> History</button></div>
      <p className="desk-context-boundary"><ShieldCheck size={14}/> Synthetic archive. Proposals are advisory and do not place orders.</p>
    </>}
  </>;
}

function Filters({w}:{w:Workspace}) {
  return <div className="desk-filters">
    <label className="desk-search"><Search size={15}/><input aria-label="Search inventory" placeholder="Search item or location…" value={w.route.search || ''} onChange={e=>w.go({search:e.target.value})}/>{w.route.search && <button aria-label="Clear search" onClick={()=>w.go({search:''})}><X size={13}/></button>}</label>
    <label className="desk-select"><SlidersHorizontal size={14}/><select aria-label="Category" value={w.route.category || ''} onChange={e=>w.go({category:e.target.value})}><option value="">All categories</option><option value="risk">Risk</option><option value="opportunity">Opportunity</option><option value="evidence">Evidence problem</option><option value="none">No finding</option></select></label>
    <label className="desk-select"><Layers3 size={14}/><select aria-label="Location" value={w.route.warehouse || ''} onChange={e=>w.go({warehouse:e.target.value})}><option value="">All locations</option>{w.overview.data?.dimensions?.warehouses?.map((x:any)=><option key={x.warehouse_id} value={x.warehouse_id}>{x.name}</option>)}</select></label>
    <label className="desk-select desk-sort"><select aria-label="Sort inventory" value={w.route.sort || 'priority'} onChange={e=>w.go({sort:e.target.value})}><option value="priority">Priority first</option><option value="sku">Item code</option><option value="stock">On hand ↑</option></select></label>
  </div>;
}

function Overview({w}:{w:Workspace}) {
  const o=w.overview.data;
  return <>
    {o && <>
      <div className="desk-summary-strip">
        <button onClick={()=>w.go({page:'explore',category:'',search:'',warehouse:''})}><span className="desk-summary-icon"><Boxes size={17}/></span><span><small>Inventory scope</small><strong>{o.summary.keys}<em> item locations</em></strong></span></button>
        <button onClick={()=>w.go({page:'explore',category:'risk'})}><span className="desk-dot risk"/><span><small>Risk</small><strong>{o.summary.risk}<em> needs attention</em></strong></span></button>
        <button onClick={()=>w.go({page:'explore',category:'opportunity'})}><span className="desk-dot opportunity"/><span><small>Opportunity</small><strong>{o.summary.opportunity}<em> to review</em></strong></span></button>
        <button onClick={()=>w.go({page:'explore',category:'evidence'})}><span className="desk-dot evidence"/><span><small>Evidence problem</small><strong>{o.summary.evidence}<em> blocked</em></strong></span></button>
      </div>
      <section className="panel desk-queue"><div className="section-head"><div><div className="eyebrow">Start here</div><h2>Attention queue <span className="desk-count">{o.highlights?.length}</span></h2></div><button className="button" onClick={()=>w.go({page:'explore',category:''})}>View all inventory <ArrowRight size={14}/></button></div><p className="desk-section-note">Saved priorities across risk, surplus exposure and missing evidence.</p><DataTable items={o.highlights || []} onSelect={(item:any)=>w.select(item,'overview')} selected={w.route.item}/><div className="desk-table-footer"><span><CircleDot size={12}/> {o.summary.assessable} of {o.summary.keys} item locations assessable</span><span>Quantities in exact pieces</span></div></section>
      <section className="panel desk-discovery"><div className="section-head"><div><div className="eyebrow">Across the archive</div><h2>What changed in the inputs</h2></div><span className="desk-version">RULES V2</span></div><div className="desk-finding-grid">{o.insight_discovery?.findings?.map((f:any)=><button className="desk-discovery-card" key={f.id} onClick={()=>w.go({item:f.members?.[0] || `${f.sku_id}|${f.warehouse_id}`,page:'investigate'})}><div><Badge value={f.category}/><ArrowUpRight size={15}/></div><h3>{f.title}</h3><p>{f.sku_id?.replace('product-coast:sku-','COAST-')} · {f.warehouse_id?.replace('product-coast:site-','site ')}</p><span>Inspect finding <ArrowRight size={13}/></span></button>)}</div><p className="desk-discovery-foot">Observed input changes and modeled exposure are distinct. Future persistence and commercial impact are unmeasured.</p></section>
      <div className="desk-workflow"><div><Database size={18}/><span><strong>A reviewable path to a decision</strong><small>Stay with one item from its original records to a declared comparison.</small></span></div><button onClick={()=>w.go({page:'investigate'})}>Evidence <ChevronRight size={13}/></button><button onClick={()=>w.go({page:'compare'})}>Compare <ChevronRight size={13}/></button><button onClick={()=>w.go({page:'decide'})}>Decision <ArrowUpRight size={13}/></button></div>
    </>}
  </>;
}

export default function Desk({w}:{w:Workspace}) {
  const [inspector,setInspector]=useState(true);
  const page=w.route.page;
  const active=navigation.find(n=>n.page===page) || navigation[0];
  const isItem=['investigate','compare','decide','history','execution'].includes(page);
  return <div className="desk">
    <a className="skip-link" href="#main" onClick={e=>{e.preventDefault();document.getElementById('main')?.focus();}}>Skip to content</a>
    <aside className="desk-rail"><button className="desk-logo" aria-label="Inventory Intelligence overview" onClick={()=>w.go({page:'overview'})}><Boxes size={24}/></button><div className="desk-rail-divider"/><nav aria-label="Main navigation">{navigation.map(n=><button title={n.name} aria-label={n.name} aria-current={page===n.page?'page':undefined} key={n.page} className={page===n.page?'active':''} onClick={()=>w.go({page:n.page})}><n.icon size={20}/><span>{n.name}</span></button>)}</nav><div className="desk-rail-bottom"><span>II</span></div></aside>
    <div className="desk-shell"><header className="desk-topbar"><div className="desk-workspace-name"><strong>Inventory Intelligence</strong><ChevronRight size={14}/><span>Coast workspace</span></div><div className="desk-topbar-actions"><span className="desk-environment"><i/>Synthetic archive</span><a href={'?direction=brief'+window.location.hash}>Explore Brief <ArrowUpRight size={12}/></a><span className="desk-avatar">D</span></div></header>
      <div className="desk-viewbar"><div className="desk-view-title"><active.icon size={20}/><h1>{active.name === 'Inventory' ? 'Inventory explorer' : active.name}</h1><span className="desk-view-divider"/><span className="desk-readonly">Read only</span></div><div className="desk-view-controls"><label className="desk-cutoff"><CalendarDays size={14}/><select aria-label="Business cutoff" value={w.route.cutoff} onChange={e=>w.go({cutoff:e.target.value})}>{(w.overview.data?.cutoffs || [w.route.cutoff]).map((c:string)=><option value={c} key={c}>{dateLabel(c)}</option>)}</select></label><button className={'desk-inspector-toggle '+(inspector?'selected':'')} aria-label={inspector?'Hide item context':'Show item context'} onClick={()=>setInspector(!inspector)}>{inspector?<PanelRightClose size={18}/>:<PanelRightOpen size={18}/>}</button></div></div>
      <div className={'desk-layout '+(!inspector?'desk-full':'')}><main id="main" tabIndex={-1} className="desk-main"><div className="desk-page-intro"><p>{descriptions[page]}</p><span><span className="desk-live-dot"/> Saved evidence</span></div>
        <Notice resource={w.overview}/>
        {isItem && <div className="desk-item-path"><button onClick={()=>w.go({page:'explore'})}>Inventory</button><ChevronRight size={13}/><strong>{w.detail.data?.sku_code || 'Selected item'}</strong><span>{w.detail.data?.location}</span></div>}
        {['investigate','compare','decide'].includes(page) && <nav className="desk-item-tabs" aria-label="Item review journey">{[{page:'investigate',name:'01  Evidence',icon:ScanLine},{page:'compare',name:'02  Comparison',icon:GitCompareArrows},{page:'decide',name:'03  Decision',icon:ClipboardCheck}].map(n=><button key={n.page} className={page===n.page?'active':''} onClick={()=>w.go({page:n.page})}><n.icon size={15}/>{n.name}</button>)}</nav>}
        {page==='overview' && <Overview w={w}/>}
        {page==='explore' && <section className="panel desk-inventory-panel"><div className="section-head"><h2>Item locations <span className="desk-count">{w.explore.data?.items?.length ?? '…'}</span></h2><Export data={w.explore.data} name="inventory-explorer">Export</Export></div><Filters w={w}/><Notice resource={w.explore}/>{w.explore.data && <><DataTable items={w.explore.data.items} onSelect={(item:any)=>w.select(item,'explore')} selected={w.route.item}/><div className="desk-table-footer"><span>Click a row to inspect item context</span><button onClick={()=>w.go({page:'investigate'})}>Open evidence <ArrowUpRight size={13}/></button></div></>}</section>}
        {page==='investigate' && <EvidencePanel w={w}/>}
        {page==='compare' && <ComparisonPanel w={w}/>}
        {page==='decide' && <DecisionPanel w={w}/>}
        {page==='history' && <HistoryPanel w={w}/>}
        {page==='execution' && <ExecutionPanel w={w}/>}
        {page==='evaluation' && <EvaluationPanel/>}
        <footer className="desk-main-footer"><span>INVENTORY INTELLIGENCE <span> / </span> DESK</span><span>Original records → reviewable decisions</span></footer>
      </main>{inspector && <aside className="desk-inspector"><Context w={w}/></aside>}</div>
    </div>
  </div>;
}
