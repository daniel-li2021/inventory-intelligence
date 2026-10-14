"""Paced developer journey for feasible choices, transfer lifecycle and review evidence."""
import argparse
import json
from pathlib import Path
import check_product_browser as browser_check

JOURNEY=r"""
const {chromium}=require(process.env.PRODUCT_PLAYWRIGHT);
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.PRODUCT_CHROME});
 const context=await browser.newContext({viewport:{width:1280,height:900},acceptDownloads:true});
 const page=await context.newPage();let next=Date.now(),pending=0;
 await context.route('**/api/**',async route=>{pending++;try{const slot=Math.max(next,Date.now());next=slot+500;await new Promise(r=>setTimeout(r,Math.max(0,slot-Date.now())));await route.fulfill({response:await route.fetch()});}finally{pending--;}});
 const settle=async()=>{await new Promise(r=>setTimeout(r,100));while(pending)await new Promise(r=>setTimeout(r,100));await page.waitForLoadState('networkidle');};
 const checks=[],errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
 const check=n=>checks.push(n);
 const base=process.env.PRODUCT_BASE_URL;
 try {
  await page.goto(base+'/#/compare?snapshot=2026-05-04&item=product-coast%3Asku-0%7Cproduct-coast%3Asite-0',{waitUntil:'networkidle'});await settle();
  await page.getByRole('button',{name:'Compare feasible purchases',exact:true}).click();await settle();
  const purchases=page.getByRole('region',{name:'Supplier decision results',exact:true});
  await page.getByLabel('Supplier capacity',{exact:true}).fill('');assert.equal(await page.getByRole('button',{name:'Compare feasible purchases',exact:true}).isEnabled(),false);await page.getByLabel('Supplier capacity',{exact:true}).fill('12');check('missing_numeric_input_does_not_become_zero');
  assert.match(await purchases.innerText(),/2900/);assert.match(await purchases.innerText(),/2026-05-05/);check('feasible_calendar_paid_purchase');
  await page.getByLabel('Supplier capacity',{exact:true}).fill('5');assert.match(await purchases.innerText(),/stale/);
  await page.getByRole('button',{name:'Compare feasible purchases',exact:true}).click();await settle();
  assert.match(await purchases.innerText(),/Withheld/);assert.equal(await page.getByRole('button',{name:'Admit alternative to synthetic journal',exact:true}).isEnabled(),false);check('capacity_block_and_stale_state');
  await page.getByLabel('Supplier capacity',{exact:true}).fill('12');await page.getByRole('button',{name:'Compare feasible purchases',exact:true}).click();await settle();
  await page.getByRole('button',{name:'Admit alternative to synthetic journal',exact:true}).click();await settle();
  await page.getByText('Synthetic commitments, dispatch and partial receipts',{exact:true}).click();await settle();
  assert.match(await page.getByLabel('Purchase identity',{exact:true}).inputValue(),/^supplier:/);
  await page.getByLabel('Event business date',{exact:true}).fill('2026-05-05');await page.getByRole('button',{name:'Receive purchase pieces',exact:true}).click();await settle();
  await page.getByLabel('Decision history as of',{exact:true}).fill('2026-05-05');await settle();
  check('purchase_admission_partial_receipt_history');
  await page.getByRole('button',{name:'Compare transfer before purchase',exact:true}).click();await settle();
  const transfers=page.getByRole('region',{name:'Transfer decision results',exact:true});
  assert.match(await transfers.innerText(),/51 pieces/);for(const cost of ['6763','5154','3533'])assert.match(await transfers.innerText(),new RegExp(cost));check('complete_network_cost_and_donor_surplus');
  const download=page.waitForEvent('download');await page.getByRole('button',{name:'Export transfer comparison',exact:true}).click();
  const saved=JSON.parse(require('node:fs').readFileSync(await (await download).path(),'utf8'));
  assert.equal(saved.stale,false);assert.equal(saved.arms.transfer_before_purchase.donor.immediate_fulfilled,'28');assert.equal(saved.arms.transfer_before_purchase.purchase_quantity,'0');check('donor_service_and_source_bound_export');
  await page.getByRole('button',{name:'Reserve synthetic transfer',exact:true}).click();await settle();
  const transferId=await page.getByLabel('Transfer identity',{exact:true}).inputValue();assert.match(transferId,/^[0-9a-f]{64}$/);
  await page.getByLabel('Event business date',{exact:true}).fill('2026-05-04');await page.getByRole('button',{name:'Dispatch reserved transfer',exact:true}).click();await settle();
  await page.getByLabel('Event business date',{exact:true}).fill('2026-05-05');await page.getByRole('button',{name:'Receive transfer pieces',exact:true}).click();await settle();
  await page.getByLabel('Partial receipt pieces',{exact:true}).fill('7');await page.getByLabel('Event business date',{exact:true}).fill('2026-05-06');await page.getByRole('button',{name:'Receive transfer pieces',exact:true}).click();await settle();
  await page.getByLabel('Decision history as of',{exact:true}).fill('2026-05-06');await settle();check('reserved_dispatched_partial_full_transfer');
  await page.getByText('Inspect subsequent actual planner decisions',{exact:true}).click();await settle();assert.match(await page.locator('main').innerText(),/Overdue partial/);assert.match(await page.locator('main').innerText(),/Independent count/);check('source_bound_actual_feedback_reports');
  const overview=await (await context.request.get(base+'/api/product/overview?cutoff=2026-05-04')).json();
  const history=await (await context.request.get(base+'/api/product/transfer-history?as_of=2026-05-06&archive_digest='+overview.archive_digest)).json();
  assert.equal(history.transfers[0].received,'12');assert.equal(history.transfers[0].in_transit,'0');
  await page.getByLabel('Transfer transit days',{exact:true}).fill('2');assert.match(await transfers.innerText(),/stale/);assert.equal(await page.getByRole('button',{name:'Reserve synthetic transfer',exact:true}).isEnabled(),false);check('changed_transport_blocks_stale_admission');
  await page.screenshot({path:process.env.PRODUCT_DESKTOP_SCREENSHOT,fullPage:true});
  await page.screenshot({path:process.env.PRODUCT_DESKTOP_SCREENSHOT.replace('.png','-viewport.png'),fullPage:false});
  await page.getByRole('link',{name:'Investigate',exact:true}).click();await settle();
  await page.getByText('Review a source-bound finding',{exact:true}).click();await settle();
  await page.getByLabel('Investigation note',{exact:true}).fill('Synthetic review: donor-safe option inspected; source risk stays visible.');await page.getByRole('button',{name:'Save finding review',exact:true}).click();await settle();
  assert.match(await page.locator('main').innerText(),/Review saved/);assert.match(await page.locator('main').innerText(),/Observed evidence/);check('review_loop_keeps_facts_and_gates');
  await page.getByRole('link',{name:'Evaluation',exact:true}).click();await settle();assert.match(await page.locator('main').innerText(),/144/);assert.match(await page.locator('main').innerText(),/No global winner/);check('fresh_forecast_decision_counterexamples');
  await page.setViewportSize({width:320,height:800});await settle();assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.screenshot({path:process.env.PRODUCT_MOBILE_SCREENSHOT,fullPage:true});check('evaluation_actual_320px_layout');
  await page.getByRole('link',{name:'Compare',exact:true}).click();await settle();assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));check('decisions_actual_320px_layout');
  await page.keyboard.press('Tab');assert.ok(await page.evaluate(()=>document.activeElement!==document.body));check('keyboard_navigation');
  await page.getByRole('link',{name:'Overview',exact:true}).click();await settle();assert.equal(await page.getByRole('button',{name:'Inspect duplicate-inventory control',exact:true}).count(),0);check('only_available_archive_controls_shown');
  assert.deepEqual(errors,[]);check('no_console_page_errors');
  console.log(JSON.stringify({kind:'developer_platform_browser_acceptance',checks,viewport_checked:320,browser:browser.version(),human_comprehension:'not_performed',accessibility_conformance:'not_claimed',offer:'paced <=2/s; correctness, not load',console_errors:errors}));
 }catch(error){console.error(JSON.stringify({url:page.url(),checks,errors,text:(await page.locator('main').innerText()).slice(-4000)}));throw error;}finally{await browser.close();}
})().catch(e=>{console.error(e.stack);process.exit(1);});
"""

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url',default='http://127.0.0.1:8040')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--screenshot-dir',type=Path)
    args=parser.parse_args()
    if args.output and args.output.exists():raise ValueError('Refuse to overwrite browser acceptance')
    browser_check.JOURNEY=JOURNEY
    result=browser_check.check(args.base_url,screenshot_dir=args.screenshot_dir)
    if args.output:args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
