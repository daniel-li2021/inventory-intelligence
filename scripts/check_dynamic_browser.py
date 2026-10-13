"""Bounded developer browser controls for the additive local replay journey."""
import argparse
import json
from pathlib import Path
import check_product_browser as browser_check

JOURNEY = r"""
const {chromium}=require(process.env.PRODUCT_PLAYWRIGHT);
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.PRODUCT_CHROME});
 const context=await browser.newContext({viewport:{width:1280,height:900},acceptDownloads:true});
 let next=Date.now(),pending=0;
 const settle=async()=>{await new Promise(r=>setTimeout(r,75));while(pending)await new Promise(r=>setTimeout(r,50));await page.waitForLoadState('networkidle');};
 await context.route('**/api/**',async route=>{pending++;try{const slot=Math.max(next,Date.now());next=slot+500;await new Promise(r=>setTimeout(r,Math.max(0,slot-Date.now())));const response=await route.fetch();await route.fulfill({response});}finally{pending--;}});
 const page=await context.newPage();const checks=[],errors=[],expectedErrors=[];
 page.on('pageerror',e=>errors.push(e.message));
 page.on('console',m=>{if(m.type()==='error'){if(/422/.test(m.text()))expectedErrors.push(m.text());else errors.push(m.text());}});
 const check=name=>checks.push(name);
 const nav=async name=>{await page.getByRole('link',{name,exact:true}).click();await settle();};
 const base=process.env.PRODUCT_BASE_URL;
 try {
  await page.goto(base,{waitUntil:'networkidle'});
  await settle();await page.getByRole('heading',{name:'Insight Discovery V2',exact:true}).waitFor();
  assert.match(await page.locator('main').innerText(),/Persistent replenishment risk/);check('latest_v2_discovery');
  await page.getByLabel('Cutoff',{exact:true}).selectOption('2026-04-06');await settle();
  assert.equal(await page.getByRole('heading',{name:'Recent demand increase',exact:true}).count(),2);
  const imbalance=page.getByRole('heading',{name:'Same-item location imbalance',exact:true}).locator('..');
  await imbalance.getByRole('button',{name:'Investigate finding',exact:false}).click();await settle();
  assert.match(page.url(),/product-dynamic%3Aa%7Cproduct-dynamic%3Aharbor/);check('cross_location_insight_exact_key_drilldown');
  assert.match(await page.locator('main').innerText(),/Model hypothesis:/);
  assert.match(await page.locator('main').innerText(),/Supported next step:/);
  assert.match(await page.locator('main').innerText(),/Missing evidence:/);check('observed_hypothesis_unknown_distinction');
  await nav('Compare');
  await page.getByLabel('Alternative order · pieces',{exact:true}).fill('12');
  await page.getByRole('button',{name:'Compare one review',exact:true}).click();await settle();
  const panel=page.getByRole('region',{name:'One-review execution comparison',exact:true});
  assert.match(await panel.innerText(),/18039/);assert.match(await panel.innerText(),/16281/);assert.match(await panel.innerText(),/14609/);check('independent_33day_paid_quantity_controls');
  await page.getByLabel('Declared order delay · days',{exact:true}).fill('3');
  assert.match(await panel.innerText(),/stale/);
  await page.getByRole('button',{name:'Compare one review',exact:true}).click();await settle();
  assert.match(await panel.innerText(),/16373/);check('delay_stale_and_common_window');
  const download=page.waitForEvent('download');await page.getByRole('button',{name:'Export one-review comparison',exact:true}).click();
  const saved=JSON.parse(require('node:fs').readFileSync(await (await download).path(),'utf8'));
  assert.equal(saved.stale,false);assert.equal(saved.common_days,33);assert.equal(saved.arms.actual_proposal.total_cost,'16373');check('source_bound_export');
  await page.getByLabel('Alternative order · pieces',{exact:true}).fill('5');
  const failure=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/product/contrast');
  await page.getByRole('button',{name:'Compare one review',exact:true}).click();assert.equal((await failure).status(),422);await settle();
  assert.match(await panel.innerText(),/stale/);assert.match(await panel.innerText(),/16373/);check('invalid_pack_last_good_retained_stale');
  await nav('History');assert.match(await page.locator('main').innerText(),/Worsening replenishment risk/);assert.match(await page.locator('main').innerText(),/Persistent replenishment risk/);check('discovery_history_three_cutoffs');
  await page.goto(base+'/#/compare?snapshot=2026-04-20&item=product-dynamic%3Ab%7Cproduct-dynamic%3Aupland',{waitUntil:'networkidle'});
  await settle();await page.getByRole('button',{name:'Compare one review',exact:true}).click();await settle();
  assert.match(await page.getByRole('region',{name:'One-review execution comparison',exact:true}).innerText(),/Not assessable/);check('incomplete_supply_blocks_contrast');
  await nav('Overview');await page.setViewportSize({width:320,height:800});await settle();
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.screenshot({path:process.env.PRODUCT_MOBILE_SCREENSHOT,fullPage:true});check('actual_320px_layout');
  await page.setViewportSize({width:1280,height:900});await page.screenshot({path:process.env.PRODUCT_DESKTOP_SCREENSHOT,fullPage:true});
  const legacy=await (await context.request.get(base+'/api/lab')).json();assert.ok(JSON.stringify(legacy).includes('12'));check('legacy_lab_available');
  const denied=await context.request.post(base+'/api/product/ingest',{data:{synthetic:true}});assert.equal(denied.status(),404);check('no_http_ingestion');
  await page.goto(base+'/#/overview?archive='+'0'.repeat(64)+'&schema=inventory-product-v1',{waitUntil:'networkidle'});
  await page.getByText('Saved view belongs to another archive or contract.',{exact:true}).waitFor();check('archive_binding_blocks_saved_view');
  assert.deepEqual(errors,[]);check('no_unexpected_browser_errors');
  console.log(JSON.stringify({kind:'developer_dynamic_browser_acceptance',checks,browser:browser.version(),viewport_checked:320,console_errors:errors,expected_422_console_messages:expectedErrors,human_comprehension:'not_performed',accessibility_conformance:'not_claimed',api_offer:'paced at <=2/s; correctness, not load acceptance'}));
 }catch(error){console.error(JSON.stringify({url:page.url(),checks,errors,visible_text:(await page.locator('body').innerText()).slice(-4000)}));throw error;}finally{await browser.close();}
})().catch(e=>{console.error(e.stack);process.exit(1);});
"""


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url',default='http://127.0.0.1:8030')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--screenshot-dir',type=Path)
    args=parser.parse_args()
    browser_check.JOURNEY=JOURNEY
    result=browser_check.check(args.base_url,screenshot_dir=args.screenshot_dir)
    if args.output:args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
