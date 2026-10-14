import {decide} from './logic.mjs';
const $=s=>document.querySelector(s),money=n=>n===null?'—':new Intl.NumberFormat('en-GB',{style:'currency',currency:'GBP'}).format(n),pct=n=>n===null?'—':(n*100).toFixed(1)+'%';
let rows=[],selected='P004';
function showDetail(r,target){
 const d=decide(r,target); const net=r.Shelf===null?null:r.Shelf/1.2;
 $('#detail').innerHTML=`<h3>${r.Product} <span class="muted">${r.SKU}</span></h3><p>${d.recommendation} · ${d.verdict}</p><div class="formula-grid"><div><span>VAT-exclusive revenue</span><strong>${money(net)}</strong><p>${money(r.Shelf)} ÷ 1.20</p></div><div><span>Base contribution per unit</span><strong>${money(r.BaseContribution)}</strong><p>Net revenue − ${money(r.BaseCost)} cost − 1.5% shelf-price fee</p></div><div><span>Bulk stock cover</span><strong>${r.BulkCover===null?'Unknown':r.BulkCover.toFixed(1)+' months'}</strong><p>(${r.OnHand} on hand + ${r.BulkUnits} units) ÷ ${r.MonthlyDemand} units/month</p></div></div><p>${r.Benchmark===null?'No eligible benchmark: margin is left blank.':`Selected ${money(r.Benchmark)} from ${r.Retailer}; ${r.Availability.toLowerCase()}.`} Bulk units round the ${r.BulkThreshold}-unit threshold up to a multiple of ${r.OrderMultiple}. ${r.BulkCost===null?'No bulk price is offered; the quantity calculation is hypothetical.':''}</p>`;
}
function render(){
 const target=Number($('#margin').value)/100,category=$('#category').value;
 $('#margin-value').textContent=Math.round(target*100)+'%';
 const shown=rows.filter(r=>category==='All categories'||r.Category===category),data=shown.map(r=>({...r,...decide(r,target)}));
 $('#count').textContent=shown.length;$('#coverage').textContent=shown.filter(r=>r.Benchmark!==null).length+'/'+shown.length;
 $('#trials').textContent=data.filter(r=>r.recommendation==='Trial candidate').length;$('#bulk').textContent=data.filter(r=>r.recommendation==='Bulk candidate').length;
 if(!shown.some(r=>r.SKU===selected))selected=shown[0]?.SKU;
 $('#products').innerHTML=data.map(r=>`<tr class="${selected===r.SKU?'selected':''}"><td><button type="button" data-sku="${r.SKU}" aria-pressed="${selected===r.SKU}">${r.Product}</button></td><td>${pct(r.BaseGM)}</td><td>${pct(r.BulkGM)}</td><td>${money(r.BulkCash)}</td><td>${r.BulkCost===null||r.BulkCover===null?'—':r.BulkCover.toFixed(1)+' mo'}</td><td><span class="pill ${r.recommendation.includes('candidate')?'':r.recommendation==='Below target'?'no':'review'}">${r.recommendation}</span></td></tr>`).join('');
 if(shown.length)showDetail(shown.find(r=>r.SKU===selected),target);
}
$('#products').addEventListener('click',e=>{const button=e.target.closest('button[data-sku]');if(button){selected=button.dataset.sku;render();$('#products button[data-sku="'+selected+'"]').focus();}});
$('#margin').addEventListener('input',render);$('#category').addEventListener('change',render);$('#reset').addEventListener('click',()=>{$('#margin').value=30;$('#category').value='All categories';selected='P004';render();});
fetch('downloads/Procurement_Analytics/demo.json').then(r=>{if(!r.ok)throw Error('Data unavailable');return r.json();}).then(data=>{rows=data.rows;$('#checks').textContent=Object.values(data.validation.checks).filter(Boolean).length+' checks passed';render();}).catch(()=>{$('#products').innerHTML='<tr><td colspan="6">The demonstration could not load. Download the Excel model to explore the calculations.</td></tr>';});

fetch('downloads/Procurement_Analytics/supplier_comparison.json').then(r=>{if(!r.ok)throw Error('Data unavailable');return r.json();}).then(data=>{document.querySelector('#supplier-rows').innerHTML=data.rows.map(r=>`<tr><td>${r.Product}</td><td>${r.Supplier}</td><td>${money(r.UnitCost)}</td><td>${money(r.NetGoodsCost)}</td><td>${r.PriceRank===1?'1 · Lowest eligible price':r.PriceRank}</td></tr>`).join('');}).catch(()=>{document.querySelector('#supplier-rows').innerHTML='<tr><td colspan="5">Download the package to inspect the supplier comparison.</td></tr>';});
