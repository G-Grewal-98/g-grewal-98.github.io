import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const root=new URL('../',import.meta.url);
const elements={};
function el(id){return elements[id]??=({value:'',textContent:'',innerHTML:'',events:{},children:[],addEventListener(k,f){this.events[k]=f},replaceChildren(){this.children=[]},append(...items){this.children.push(...items)},focus(){}});}
for(const [k,v] of Object.entries({margin:'30',premium:'10',demand:'100',category:'All categories','supplier-qty':'24','supplier-product':'P002'}))el(k).value=v;
const doc={querySelector:s=>el(s.slice(1)),getElementById:el,createElement:()=>({children:[],textContent:'',append(...items){this.children.push(...items)}})};
const demo=JSON.parse(fs.readFileSync(new URL('downloads/Procurement_Analytics/demo.json',root)));
const offers=JSON.parse(fs.readFileSync(new URL('downloads/Procurement_Analytics/supplier_offers.json',root)));
const context=vm.createContext({document:doc,window:{PORTFOLIO_FIXTURES:{demo,offers}},Intl});
vm.runInContext(fs.readFileSync(new URL('app.js',root),'utf8'),context);
let checks=0;const ok=x=>{assert.ok(x);checks++};
ok(el('count').textContent===12);ok(el('products').innerHTML.includes('data-sku="P004"'));ok(el('detail').innerHTML.includes('P004'));
const original=el('products').innerHTML;
el('margin').value='50';el('margin').events.input();ok(el('margin-value').textContent==='50%');ok(el('products').innerHTML!==original);
el('premium').value='0';el('premium').events.input();ok(el('premium-value').textContent==='0%');
el('demand').value='0';el('demand').events.input();ok(el('detail').innerHTML.includes('cannot be calculated'));
el('reset').events.click();ok(el('products').innerHTML===original);ok(el('margin').value===30&&el('premium').value===10&&el('demand').value===100);
const category=demo.rows[0].Category;el('category').value=category;el('category').events.change();ok(el('count').textContent===demo.rows.filter(r=>r.Category===category).length);
// Supplier comparison uses selected product and correctly handles excluded offers.
el('supplier-qty').value='12';el('supplier-qty').events.change();ok(el('supplier-status').textContent.startsWith('0 of 2'));ok(el('supplier-rows').innerHTML.includes('Excluded'));
el('supplier-qty').value='24';el('supplier-qty').events.change();ok(el('supplier-insight').innerHTML.includes('Demonstration supplier A'));
el('supplier-qty').value='72';el('supplier-qty').events.change();ok(el('supplier-insight').innerHTML.includes('Demonstration supplier B'));
el('supplier-product').value='P001';el('supplier-product').events.change();ok(el('supplier-status').textContent.startsWith('2 of 2'));
// Exercise independent four-offer landed-cost demo with its existing fictional engine rows.
const html=fs.readFileSync(new URL('downloads/Procurement_Intelligence_Public/portfolio/index.html',root),'utf8');
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
el('product').value='DEMO_P1';el('qty').value='12';el('supplier').value='';
const landedContext=vm.createContext({document:doc,Intl});vm.runInContext(script,landedContext);
for(const product of ['DEMO_P1','DEMO_P2'])for(const qty of ['1','12','24','36'])for(const supplier of ['','SYN_A','SYN_B']){
 el('product').value=product;el('qty').value=qty;el('supplier').value=supplier;el('qty').events.change();
 ok(el('results').children.length===(supplier?1:2));
 ok(el('status').textContent.includes('human review'));
 if(qty==='1'&&supplier==='SYN_B'){ok(el('status').textContent.includes('0 eligible'));ok(el('results').children[0].children[4].textContent==='Below supplier minimum spend');}
}
el('product').value='DEMO_P1';el('qty').value='12';el('supplier').value='SYN_A';el('supplier').events.change();
ok(el('results').children[0].children[1].textContent==='£22.95');ok(el('results').children[0].children[2].textContent==='£330.48');ok(el('results').children[0].children[3].textContent==='54.1%');
ok(el('price-old').textContent==='£24.95');ok(el('price-new').textContent==='£22.95');ok(el('price-move').textContent==='-8.02%');
console.log(checks+' control/event assertions passed; browser rendering tested separately.');
