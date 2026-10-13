"""Repeatable local synthetic journey checks using an installed Playwright/Chrome.

These are developer browser checks, not independent human comprehension or WCAG
conformance acceptance. No operational records, model APIs or purchases are used.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


JOURNEY = r"""
const {chromium}=require(process.env.PRODUCT_PLAYWRIGHT);
const assert=require('node:assert/strict');
(async()=>{
  const browser=await chromium.launch({headless:true,...(process.env.PRODUCT_CHROME ? {executablePath:process.env.PRODUCT_CHROME} : {})});
  const context=await browser.newContext({viewport:{width:1280,height:900},acceptDownloads:true});
  const page=await context.newPage();
  const errors=[], checks=[], responses=[], expectedFailureMessages=[];
  let injectedFailures=0;
  page.on('pageerror',e=>errors.push(e.message));
  page.on('console',m=>{if(m.type()==='error') {
    if(injectedFailures>expectedFailureMessages.length&&m.location().url.includes('/api/product/scenario')&&/503/.test(m.text())) expectedFailureMessages.push(m.text());
    else errors.push(m.text());
  }});
  page.on('response',r=>{if(r.url().includes('/api/product/')||r.url().includes('/api/execution')) responses.push({url:r.url(),bytes:r.body().then(body=>body.length).catch(()=>null)});});
  const check=(name)=>checks.push(name);
  const nav=async name=>{await page.getByRole('link',{name,exact:true}).click();await page.waitForFunction(n=>document.querySelector('h1')?.textContent===(n==='Overview'?'Focus on the decisions that matter':n),name);await page.waitForLoadState('networkidle');};
  const resetView=async()=>{await page.getByRole('button',{name:'Reset view',exact:true}).click();await page.waitForFunction(()=>location.hash==='#/overview'&&document.querySelector('h1')?.textContent==='Focus on the decisions that matter');};
  const base=process.env.PRODUCT_BASE_URL;
  try {
    await page.goto(base,{waitUntil:'networkidle'});
    await page.locator('h1').waitFor();
    await page.getByLabel('Cutoff',{exact:true}).selectOption('2026-01-05');
    await page.waitForFunction(()=>document.querySelector('.context-bar')?.textContent?.includes('Business as of 2026-01-05'));
    await page.screenshot({path:process.env.PRODUCT_DESKTOP_SCREENSHOT,fullPage:true});
    const initialViewBytes=(await Promise.all(responses.map(r=>r.bytes))).reduce((sum,n)=>sum+(n||0),0);
    assert.ok(initialViewBytes<=200*1024,'initial JSON view exceeded 200 KiB');
    check('overview_loaded');
    assert.ok(!responses.some(response=>new URL(response.url).pathname==='/api/product/control'),'defect control must load lazily');
    const defectResponse=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/product/control');
    await page.getByRole('button',{name:'Inspect duplicate-inventory control',exact:true}).click();
    const defect=await (await defectResponse).json();
    assert.equal(defect.reliability.overall_status,'fail');
    assert.equal(defect.blocked_plan.status,'not_assessable');
    assert.equal(defect.blocked_plan.proposed_order_qty,null);
    const finding=defect.reliability.findings.find(f=>f.reason==='duplicate_snapshot');
    assert.equal(finding.observed_qty,null);
    assert.deepEqual(finding.evidence.source_records.map(r=>r.record.on_hand_qty),['22','22']);
    await page.getByRole('button',{name:'Collapse control',exact:true}).waitFor();
    const controlPanel=page.locator('.duplicate-control');
    await page.getByRole('button',{name:'Export duplicate control',exact:true}).waitFor();
    assert.match(await controlPanel.innerText(),/Duplicate|duplicate/);
    assert.match(await controlPanel.innerText(),/Unknown|suppressed|withheld/i);
    assert.match(await controlPanel.innerText(),new RegExp(defect.reliability.run_id));
    const findingRecord=controlPanel.locator('dt').filter({hasText:/^Findings$/}).locator('..').locator('details').first();
    await findingRecord.locator('summary').first().click();
    const sourceRecords=findingRecord.locator('dt').filter({hasText:/^Source records$/}).locator('..').locator('details');
    assert.equal(await sourceRecords.count(),2);
    for(let i=0;i<2;i++) await sourceRecords.nth(i).locator('summary').first().click();
    for(const row of finding.evidence.source_records) assert.match(await controlPanel.innerText(),new RegExp(row.record.row_id));
    await page.getByRole('button',{name:'Collapse control',exact:true}).click();
    check('lazy_duplicate_control_original_rows_and_blocked_proposal');
    for (const name of ['Overview','Explore','Investigate','Compare','Decide','History'])
      assert.equal(await page.getByRole('link',{name,exact:true}).count(),1,`${name} navigation`);
    await nav('Explore');
    await page.getByRole('button',{name:'At-risk stock',exact:true}).click();
    await page.waitForFunction(()=>document.querySelector('.pagination p')?.textContent?.startsWith('49 matching keys'));
    const preset=await page.locator('table').first().innerText();
    await resetView();
    await page.getByLabel('Cutoff',{exact:true}).selectOption('2026-01-05');
    await page.waitForLoadState('networkidle');
    await nav('Explore');
    await page.getByLabel('Insight type',{exact:true}).selectOption('risk');
    await page.waitForFunction(()=>document.querySelector('.pagination p')?.textContent?.startsWith('49 matching keys'));
    assert.equal(await page.locator('table').first().innerText(),preset,'preset equals manual risk filter');
    check('preset_manual_equivalence');
    await page.getByRole('button',{name:'Save view',exact:true}).click();
    assert.equal(await page.getByLabel('Saved views',{exact:true}).locator('option').count(),2);
    await resetView();
    await page.getByLabel('Saved views',{exact:true}).selectOption('0');
    await page.waitForLoadState('networkidle');
    await page.getByRole('button',{name:'Share view',exact:true}).click();
    const savedURL=page.url();
    assert.match(savedURL,/archive=[a-f0-9]{64}/);
    await page.reload({waitUntil:'networkidle'});
    assert.equal(page.url(),savedURL);
    assert.equal(await page.getByLabel('Insight type',{exact:true}).inputValue(),'risk');
    check('url_reload_saved_view');
    await page.getByRole('button',{name:/Investigate/}).first().click();
    await page.getByRole('heading',{name:/Investigat/}).first().waitFor();
    assert.match(await page.locator('main').innerText(),/Evidence|Source|Trace/);
    const evidenceResponse=page.waitForResponse(r=>r.url().includes('/api/product/evidence')&&new URL(r.url()).searchParams.get('section')==='plan');
    await page.getByLabel('Source section',{exact:true}).selectOption('plan');
    const evidence=await (await evidenceResponse).json();
    assert.deepEqual(evidence.rows.map(row=>row.balance_without_order),['3','-1','-5','-9','-13']);
    assert.deepEqual(evidence.rows.map(row=>row.balance_with_order),['3','-1','13','9','5']);
    check('saved_source_projection_independent_quantities');
    check('investigate_evidence');
    await nav('Compare');
    await page.getByRole('button',{name:'Run comparison',exact:true}).click();
    await page.waitForLoadState('networkidle');
    assert.match(await page.locator('main').innerText(),/advisory|proposal/i);
    check('compare_supported_scenario');
    await page.getByLabel('Demand multiplier · percent',{exact:true}).fill('125');
    assert.match(await page.locator('main').innerText(),/stale|changed/i);
    await nav('Decide');
    assert.match(await page.locator('main').innerText(),/Recommendation withheld/);
    await nav('Compare');
    await page.getByRole('button',{name:'Reset assumptions',exact:true}).click();
    check('stale_reset');
    await page.route('**/api/product/scenario*',r=>{injectedFailures++;return r.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'Acceptance injected failure'})});});
    await page.getByRole('button',{name:'Run comparison',exact:true}).click();
    await page.getByRole('button',{name:'Retry',exact:true}).waitFor();
    assert.match(await page.locator('main').innerText(),/last|previous|retained/i);
    await page.unroute('**/api/product/scenario*');
    await page.getByRole('button',{name:'Retry',exact:true}).click();
    await page.waitForLoadState('networkidle');
    check('error_retry_last_good');
    const downloadPromise=page.waitForEvent('download');
    await page.getByRole('button',{name:'Export comparison',exact:true}).click();
    const download=await downloadPromise;
    assert.match(download.suggestedFilename(),/\.json$/);
    const exported=JSON.parse(require('node:fs').readFileSync(await download.path(),'utf8'));
    assert.equal(exported.view_binding.cutoff,'2026-01-05');
    assert.match(exported.view_binding.archive_digest,/^[a-f0-9]{64}$/);
    assert.equal(exported.stale,false);
    assert.equal(exported.baseline.plan.proposed_order_qty,'18');
    assert.equal(exported.scenario.plan.proposed_order_qty,'18');
    check('export');
    let release, intercepted;
    const held=new Promise(resolve=>{release=resolve;});
    const firstRequest=new Promise(resolve=>{intercepted=resolve;});
    let heldOne=false;
    await page.route('**/api/product/scenario*',async route=>{
      const body=route.request().postDataJSON();
      if(!heldOne&&body.cutoff==='2026-01-05'&&body.overrides.demand_percent===125) {
        heldOne=true;intercepted();const response=await route.fetch();await held;
        try {await route.fulfill({response});} catch { /* Aborted old selection is expected. */ }
      } else await route.continue();
    });
    await page.getByLabel('Demand multiplier · percent',{exact:true}).fill('125');
    await page.getByRole('button',{name:'Run comparison',exact:true}).click();
    await firstRequest;
    const freshResponse=page.waitForResponse(r=>r.url().includes('/api/product/scenario')&&r.request().method()==='POST'&&r.request().postDataJSON().cutoff==='2026-01-19');
    await page.getByLabel('Cutoff',{exact:true}).selectOption('2026-01-19');
    await freshResponse;
    release();
    await page.waitForLoadState('networkidle');
    await page.unroute('**/api/product/scenario*');
    const racedDownload=page.waitForEvent('download');
    await page.getByRole('button',{name:'Export comparison',exact:true}).click();
    const raced=JSON.parse(require('node:fs').readFileSync(await (await racedDownload).path(),'utf8'));
    assert.equal(raced.view_binding.cutoff,'2026-01-19');
    assert.equal(raced.scenario.plan.proposed_order_qty,'18');
    assert.equal(raced.parameters.demand_percent,100);
    check('late_old_scenario_cannot_replace_new_cutoff');
    await nav('Decide');
    assert.match(await page.locator('main').innerText(),/advisory|not executed|no purchase/i);
    check('decide_advisory');
    await nav('History');
    assert.match(await page.locator('main').innerText(),/2026-01-05/);
    assert.match(await page.locator('main').innerText(),/2026-01-19/);
    check('history_three_cutoffs');
    await nav('Explore');
    await page.getByRole('button',{name:'Untrusted evidence',exact:true}).click();
    await page.waitForLoadState('networkidle');
    await page.getByRole('button',{name:/Investigate/}).first().click();
    await page.waitForLoadState('networkidle');
    assert.match(await page.locator('main').innerText(),/Evidence incomplete|Evidence blockers/);
    await nav('Compare');
    await page.waitForLoadState('networkidle');
    assert.match(await page.locator('main').innerText(),/comparison quantities suppressed/i);
    await nav('Decide');
    assert.match(await page.locator('main').innerText(),/Recommendation withheld/);
    await nav('History');
    assert.match(await page.locator('main').innerText(),/Unknown/);
    check('blocked_journey_missing_is_unknown');
    await nav('Execution');
    await page.getByLabel('Execution control',{exact:true}).selectOption('cold-shortage');
    await page.waitForFunction(()=>document.querySelector('.execution-workbench .metric-grid')?.textContent?.includes('776'));
    assert.match(await page.locator('.execution-workbench').innerText(),/original|Original/);
    assert.match(await page.locator('.execution-workbench').innerText(),/Quiet trace: Do Nothing costs 160 versus actual 330/);
    assert.match(await page.locator('.execution-workbench').innerText(),/2026-03-07T08:00:00/);
    assert.match(await page.locator('.execution-workbench').innerText(),/2026-03-10T07:00:00/);
    const executionDownload=page.waitForEvent('download');
    await page.getByRole('button',{name:'Export execution',exact:true}).click();
    const executed=JSON.parse(require('node:fs').readFileSync(await (await executionDownload).path(),'utf8'));
    assert.deepEqual(executed.summary.proposals,['18',null,null]);
    assert.equal(executed.summary.total_cost,'776');
    check('actual_planner_execution_blocked_history_cost_and_export');
    const executionMode=await (await context.request.get(base+'/api/execution')).json();
    if(executionMode.journal_enabled) {
      await page.getByRole('button',{name:'Admit clean proposal · 12 pieces',exact:true}).click();
      await page.getByRole('button',{name:'Receive 5 pieces · March 9',exact:true}).waitFor();
      await page.waitForFunction(()=>document.querySelector('.journal-totals')?.textContent?.includes('pending 12'));
      await page.getByRole('button',{name:'Receive 5 pieces · March 9',exact:true}).click();
      await page.waitForFunction(()=>document.querySelector('.journal-totals')?.textContent?.includes('Received 5 pieces · pending 7 pieces'));
      await page.getByRole('button',{name:'Notify ETA · March 11',exact:true}).click();
      await page.waitForFunction(()=>document.querySelector('.journal-totals')?.textContent?.includes('3 durable events'));
      await page.getByRole('button',{name:'Receive remaining 7 · March 11',exact:true}).click();
      await page.waitForFunction(()=>document.querySelector('.journal-totals')?.textContent?.includes('Received 12 pieces · pending 0 pieces'));
      await page.reload({waitUntil:'networkidle'});
      await page.waitForFunction(()=>document.querySelector('.journal-totals')?.textContent?.includes('4 durable events'));
      await page.getByRole('button',{name:'Admit clean proposal · 12 pieces',exact:true}).click();
      await page.waitForLoadState('networkidle');
      assert.match(await page.locator('.journal-totals').innerText(),/4 durable events/);
      await page.getByLabel('Journal as of',{exact:true}).fill('2026-03-08');
      await page.waitForFunction(()=>document.querySelector('.journal-totals')?.textContent?.includes('Received 0 pieces · pending 12 pieces'));
      check('durable_partial_receipt_eta_reopen_idempotency_and_history');
    } else {
      assert.match(await page.locator('.execution-workbench').innerText(),/Read-only packaged mode/);
      check('packaged_execution_keeps_journal_disabled');
    }
    await page.setViewportSize({width:320,height:740});
    await nav('Execution');
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1),'execution mobile body must not overflow');
    check('execution_mobile_320_no_body_overflow');
    await nav('Explore');
    assert.equal(await page.evaluate(()=>window.innerWidth),320);
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1),'mobile body must not overflow');
    await page.screenshot({path:process.env.PRODUCT_MOBILE_SCREENSHOT,fullPage:true});
    check('mobile_320_no_body_overflow');
    await page.keyboard.press('Tab');
    assert.ok(await page.evaluate(()=>document.activeElement!==document.body));
    check('keyboard_focus');
    await page.emulateMedia({forcedColors:'active'});
    await page.setViewportSize({width:1280,height:900});
    await page.locator('body').evaluate(el=>{el.style.zoom='4';});
    assert.equal(await page.getByRole('link',{name:'Overview',exact:true}).isVisible(),true);
    await page.keyboard.press('Tab');
    assert.ok(await page.evaluate(()=>document.activeElement!==document.body));
    check('zoom_400_forced_colors_keyboard');
    assert.deepEqual(errors,[],'console/page errors');
    check('no_console_errors');
    const unique=[...new Map(responses.map(r=>[r.url,r])).values()];
    const sizes=[];
    for(const response of unique) {
      const bytes=await response.bytes;
      if(bytes===null) continue; // An explicitly aborted stale request has no response body.
      assert.ok(bytes<=2*1024*1024,`${response.url} exceeded 2 MiB view envelope`);
      sizes.push({path:new URL(response.url).pathname,bytes});
    }
    const assets=[];
    for(const entry of new Set(await page.evaluate(()=>performance.getEntriesByType('resource').filter(r=>/product-static/.test(r.name)).map(r=>r.name)))) {
      const bytes=await (await context.request.get(entry)).body();
      const gzipBytes=require('node:zlib').gzipSync(bytes).length;
      const path=new URL(entry).pathname;
      assert.ok(bytes.length<512*1024,'each compiled asset must fit 512 KiB');
      assert.ok(gzipBytes<(/\.css$/.test(path)?40:250)*1024,'compiled gzip asset budget');
      assets.push({path,bytes:bytes.length,gzip_bytes:gzipBytes});
    }
    check('bounded_assets_and_view_data');
    console.log(JSON.stringify({kind:'developer_browser_acceptance',browser:browser.version(),viewport_checked:320,zoom_check:'CSS 400 percent with keyboard focus',checks,initial_view_bytes:initialViewBytes,api_response_sizes:sizes,assets,console_errors:errors,injected_failure_console_messages:expectedFailureMessages,human_comprehension:'not_performed',accessibility_conformance:'not_claimed'}));
  } catch(error) {console.error(JSON.stringify({url:page.url(),visible_text:(await page.locator('body').innerText()).slice(0,3000),checks}));throw error;} finally {await browser.close();}
})().catch(e=>{console.error(e.stack);process.exit(1);});
"""


def check(base_url, *, node=None, playwright=None, chrome=None, screenshot_dir=None):
    runtime = Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node'
    node = node or os.environ.get('PRODUCT_NODE') or shutil.which('node') or str(runtime/'bin/node')
    local = Path(__file__).resolve().parents[1]/'frontend/node_modules/playwright'
    bundled = runtime/'node_modules/playwright'
    discovered = str(local if local.is_dir() else bundled) if local.is_dir() or bundled.is_dir() else 'playwright'
    playwright = playwright or os.environ.get('PLAYWRIGHT_MODULE') or discovered
    chrome = chrome or os.environ.get('CHROME_EXECUTABLE')
    if chrome is None:
        chrome = next((str(path) for path in (Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),
                                             Path('/opt/google/chrome/chrome')) if path.is_file()), '')
    if chrome and not Path(chrome).is_file():
        raise ValueError('The chosen Chrome executable is unavailable; use --chrome')
    screenshots = Path(screenshot_dir or ('/private/tmp' if Path('/private/tmp').is_dir() else tempfile.gettempdir()))
    screenshots.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PRODUCT_BASE_URL=base_url.rstrip('/'),
               PRODUCT_PLAYWRIGHT=playwright, PRODUCT_CHROME=chrome,
               PRODUCT_DESKTOP_SCREENSHOT=str(screenshots/'ii-product-overview.png'),
               PRODUCT_MOBILE_SCREENSHOT=str(screenshots/'ii-product-mobile.png'))
    completed = subprocess.run([node, '-e', JOURNEY], env=env, text=True,
                               capture_output=True, timeout=180, check=False)
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or 'Browser check failed without diagnostics')
    return json.loads(completed.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://127.0.0.1:8000')
    parser.add_argument('--node')
    parser.add_argument('--playwright')
    parser.add_argument('--chrome')
    parser.add_argument('--screenshot-dir', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = check(args.base_url, node=args.node, playwright=args.playwright, chrome=args.chrome,
                   screenshot_dir=args.screenshot_dir)
    if args.output:
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
