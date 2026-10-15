import fs from 'node:fs';import assert from 'node:assert/strict';
import {scenario,rankOffers} from '../scenarios.mjs';import {decide} from '../logic.mjs';
const rows=JSON.parse(fs.readFileSync(new URL('../downloads/Procurement_Analytics/demo.json',import.meta.url))).rows;
let n=0;const ok=(x)=>{assert.ok(x);n++};
for(const r of rows){const x=scenario(r);for(const k of ['Shelf','BaseGM','BulkGM','BaseContribution','BulkContribution','BulkCover'])ok(r[k]===null?x[k]===null:Math.abs(x[k]-r[k])<1e-8);ok(decide(x).recommendation===r.Recommendation);}
const p=rows.find(r=>r.SKU==='P004');ok(decide(scenario(p,.1,0)).recommendation==='Review demand');ok(scenario(p,.1,2).BulkCover===4.75);ok(scenario(rows[4]).BaseGM===null);ok(scenario(p,0).Shelf===5);ok(scenario(p,.2).Shelf===6);
assert.throws(()=>scenario(p,.1,-1));n++;
const offers=JSON.parse(fs.readFileSync(new URL('../downloads/Procurement_Analytics/supplier_offers.json',import.meta.url)));
ok(rankOffers(offers,12).length===0);ok(rankOffers(offers,24).length===5);ok(rankOffers(offers,72).length===6);ok(rankOffers(offers,72).find(x=>x.OfferID==='O04').PriceRank===1);ok(rankOffers(offers,72).find(x=>x.OfferID==='O04').NetGoodsCost===216);assert.throws(()=>rankOffers(offers,0));n++;
console.log(n+' scenario assertions passed');
