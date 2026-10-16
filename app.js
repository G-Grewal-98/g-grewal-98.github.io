// Portfolio runtime: original source calculations are retained in logic.mjs and scenarios.mjs.
function decide(r,target=.3){
 if(r.Benchmark===null)return {verdict:'Missing evidence',recommendation:'Research price'};
 if(r.MonthlyDemand<=0)return {verdict:'Demand assumption missing',recommendation:'Review demand'};
 const base=r.BaseGM>=target&&r.BaseContribution>0;
 const bulk=r.BulkCost!==null&&r.BulkCost<r.BaseCost&&r.BulkGM>=target&&r.BulkContribution>0;
 const verdict=r.BulkCost===null?'No bulk offer':r.BulkCost>=r.BaseCost?'No unit saving':base?'Bulk optional':bulk?'Bulk required':'Below target';
 const recommendation=r.Availability!=='In stock'?'Verify availability':base?'Trial candidate':bulk?(r.BulkCover===null||r.BulkCover>r.MaxCover?'Review stock exposure':'Bulk candidate'):'Below target';
 return {verdict,recommendation};
}

// Browser-only extensions to the published synthetic baseline. No real business data.
function scenario(r,premium=.1,demandScale=1){
 if(!Number.isFinite(premium)||premium<0||premium>.2||!Number.isFinite(demandScale)||demandScale<0||demandScale>2)throw new RangeError('Invalid scenario assumptions');
 const Shelf=r.Benchmark===null?null:Math.floor((r.Benchmark*(1+premium)+1e-9)*20)/20;
 const net=Shelf===null?null:Shelf/(1+r.VAT),MonthlyDemand=r.MonthlyDemand*demandScale;
 return {...r,Shelf,MonthlyDemand,BaseGM:net?1-r.BaseCost/net:null,BulkGM:net&&r.BulkCost!==null?1-r.BulkCost/net:null,
 BaseContribution:net===null?null:net-r.BaseCost-Shelf*r.FeeRate,BulkContribution:net===null||r.BulkCost===null?null:net-r.BulkCost-Shelf*r.FeeRate,
 BulkCover:MonthlyDemand>0?(r.OnHand+r.BulkUnits)/MonthlyDemand:null};
}
function rankOffers(offers,quantity){
 if(!Number.isInteger(quantity)||quantity<=0)throw new RangeError('Quantity must be a positive integer');
 return offers.filter(o=>o.MinUnits<=quantity).map(o=>({...o,NetGoodsCost:o.UnitCost*quantity,PriceRank:1+new Set(offers.filter(x=>x.SKU===o.SKU&&x.MinUnits<=quantity&&x.UnitCost<o.UnitCost).map(x=>x.UnitCost)).size})).sort((a,b)=>a.SKU.localeCompare(b.SKU)||a.PriceRank-b.PriceRank);
}


'use strict';
const $=s=>document.querySelector(s);
const money=n=>n===null||n===undefined?'—':new Intl.NumberFormat('en-GB',{style:'currency',currency:'GBP'}).format(Number(n));
const pct=n=>n===null||n===undefined?'—':(Number(n)*100).toFixed(1)+'%';
const safe=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fixture=window.PORTFOLIO_FIXTURES;
let selected='P004';
const rows=fixture?.demo?.rows ?? [];
const allOffers=fixture?.offers ?? [];

function showDetail(r,target){
 const d=decide(r,target),net=r.Shelf===null?null:r.Shelf/(1+r.VAT);
 $('#detail').innerHTML=`<p class="detail-eyebrow">SELECTED PRODUCT · ${safe(r.SKU)}</p><h3>${safe(r.Product)}</h3><p class="detail-verdict"><strong>${safe(d.recommendation)}</strong> · ${safe(d.verdict)}</p><div class="formula-grid"><div><span>Selling revenue before VAT</span><strong>${money(net)}</strong><p>${money(r.Shelf)} retail including VAT</p></div><div><span>Base contribution per unit</span><strong>${money(r.BaseContribution)}</strong><p>Net sale − cost − payment fee</p></div><div><span>Estimated stock cover after bulk</span><strong>${r.BulkCover===null?'Not established':Number(r.BulkCover).toFixed(1)+' months'}</strong><p>Calculated from fictional on-hand stock and demand</p></div></div><p class="detail-explanation">${r.Benchmark===null?'There is no suitable retail price reference, so no gross margin is calculated.':`Retail reference: ${money(r.Benchmark)} at ${safe(r.Retailer)} (${safe(r.Availability.toLowerCase())}).`} ${r.BulkCost===null?'No wholesale bulk price is recorded.':`The simulated bulk quantity respects a ${safe(r.BulkThreshold)}-unit threshold and order multiples of ${safe(r.OrderMultiple)}.`}</p><p class="scenario-note">${r.MonthlyDemand>0?`Illustrative reorder threshold: ${Math.ceil(r.MonthlyDemand*14/30)} units, assuming a 14-day lead time and no safety stock.`:'With no estimated demand, reorder timing and stock cover cannot be calculated.'} This is a fictional planning illustration, not a sales forecast or purchasing approval.</p>`;
}
function render(){
 if(!rows.length){$('#products').innerHTML='<tr><td colspan="6">Demo data unavailable. See the downloadable technical sample.</td></tr>';return;}
 const target=Number($('#margin').value)/100,category=$('#category').value;
 $('#margin-value').textContent=Math.round(target*100)+'%';
 $('#premium-value').textContent=$('#premium').value+'%';
 $('#demand-value').textContent=$('#demand').value+'%';
 const adjusted=rows.map(r=>scenario(r,Number($('#premium').value)/100,Number($('#demand').value)/100));
 const shown=adjusted.filter(r=>category==='All categories'||r.Category===category);
 const data=shown.map(r=>({...r,...decide(r,target)}));
 $('#count').textContent=shown.length;
 $('#coverage').textContent=shown.filter(r=>r.Benchmark!==null).length+'/'+shown.length;
 $('#trials').textContent=data.filter(r=>r.recommendation==='Trial candidate').length;
 $('#bulk').textContent=data.filter(r=>r.recommendation==='Bulk candidate').length;
 if(!shown.some(r=>r.SKU===selected))selected=shown[0]?.SKU;
 $('#products').innerHTML=data.length?data.map(r=>`<tr class="${selected===r.SKU?'selected':''}"><td><button type="button" data-sku="${safe(r.SKU)}" aria-pressed="${selected===r.SKU}">${safe(r.Product)}</button></td><td>${pct(r.BaseGM)}</td><td>${pct(r.BulkGM)}</td><td>${money(r.BulkCash)}</td><td>${r.BulkCost===null||r.BulkCover===null?'—':r.BulkCover.toFixed(1)+' mo'}</td><td><span class="pill ${r.recommendation.includes('candidate')?'':r.recommendation==='Below target'?'no':'review'}">${safe(r.recommendation)}</span></td></tr>`).join(''):'<tr><td colspan="6">No products match this category.</td></tr>';
 if(shown.length)showDetail(shown.find(r=>r.SKU===selected),target);
 else $('#detail').textContent='Select another category to explore a product.';
}
$('#products').addEventListener('click',e=>{const button=e.target.closest('button[data-sku]');if(button){selected=button.dataset.sku;render();$('#products button[data-sku="'+selected+'"]').focus();}});
for(const id of ['premium','demand','margin'])$('#'+id).addEventListener('input',render);
$('#category').addEventListener('change',render);
$('#reset').addEventListener('click',()=>{$('#margin').value=30;$('#premium').value=10;$('#demand').value=100;$('#category').value='All categories';selected='P004';render();});
render();

const supplierSkuList=[...new Map(allOffers.map(o=>[o.SKU,o.Product])).entries()];
const supplierProduct=$('#supplier-product');
supplierProduct.innerHTML=supplierSkuList.map(([id,name])=>`<option value="${safe(id)}" ${id==='P002'?'selected':''}>${safe(name)}</option>`).join('');
function renderSuppliers(){
 const qty=Number($('#supplier-qty').value),sku=supplierProduct.value;
 const match=allOffers.filter(o=>o.SKU===sku), eligible=rankOffers(match,qty);
 const least=eligible[0], cheapest=least?eligible.filter(o=>o.UnitCost===least.UnitCost):[];
 $('#supplier-status').textContent=`${eligible.length} of ${match.length} fictional supplier offers meet the ${qty}-unit minimum.`;
 $('#supplier-insight').innerHTML=least?
 `<strong>${cheapest.length===1?safe(least.Supplier)+' is the lowest eligible goods-cost option.':'The lowest eligible goods-cost offers are tied.'}</strong><span>${cheapest.length===1?`${money(least.UnitCost)} per unit, ${money(least.NetGoodsCost)} for ${qty} units.`:`${money(least.UnitCost)} per unit.`} This ranking excludes delivery, credit terms and unverified stock; it is not a purchasing recommendation.</span>`:
 `<strong>No offer meets this quantity.</strong><span>Try a higher order quantity, or review supplier minimums. An advertised price is not an eligible price if its minimum is not met.</span>`;
 const byKey=new Map(eligible.map(o=>[o.OfferID,o]));
 $('#supplier-rows').innerHTML=match.map(o=>{
  const e=byKey.get(o.OfferID);return `<tr class="${e?'':'excluded-row'}"><td>${safe(o.Supplier)}</td><td>${money(o.UnitCost)}</td><td>${safe(o.MinUnits)} units</td><td>${e?money(e.NetGoodsCost):'—'}</td><td>${e?`<span class="pill">Eligible · rank ${e.PriceRank}</span>`:`<span class="pill review">Excluded · min ${safe(o.MinUnits)}</span>`}</td></tr>`;
 }).join('')||'<tr><td colspan="5">No offers are included for this product.</td></tr>';
}
$('#supplier-qty').addEventListener('change',renderSuppliers);
supplierProduct.addEventListener('change',renderSuppliers);
renderSuppliers();
