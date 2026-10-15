import test from 'node:test';
import assert from 'node:assert/strict';
import {parseRoute,routeHash,exact,whole,currentResource} from '../src/model.mjs';
test('URL selection round trips identifiers and filters exactly',()=>{const r={page:'compare',cutoff:'2026-05-04',item:'product-coast:sku-0|product-coast:site-0',search:'Slate & XS',category:'risk',warehouse:'product-coast:site-0',sort:'stock'};assert.deepEqual(parseRoute(routeHash(r)),r);});
test('unknown page falls back to overview without changing item',()=>{assert.equal(parseRoute('#/missing?item=abc').page,'overview');assert.equal(parseRoute('#/missing?item=abc').item,'abc');});
test('null evidence never renders as zero',()=>{assert.equal(exact(null),'Unknown');assert.equal(exact(undefined),'Unknown');assert.equal(exact('0'),'0');});
test('rational exactness and integers remain unrounded',()=>{assert.equal(exact({numerator:'9007199254740993',denominator:'7'}),'9007199254740993/7');assert.equal(exact({numerator:'3',denominator:'1'}),'3');});
test('scenario controls reject fractions, exponents and negative pieces',()=>{for(const s of ['','-1','1.2','1e2','NaN','Infinity','2001','01'])assert.equal(whole(s),false,s);for(const s of ['0','12','2000'])assert.equal(whole(s),true,s);assert.equal(whole('4',0,3),false);});
test('old response is hidden immediately on selection or cutoff changes',()=>{const old={path:'/a',data:{proposed_order_qty:'6'},loading:false};assert.deepEqual(currentResource(old,'/b'),{loading:true});assert.equal(currentResource(old,'/a').data.proposed_order_qty,'6');assert.deepEqual(currentResource(old,null),{loading:false});});
