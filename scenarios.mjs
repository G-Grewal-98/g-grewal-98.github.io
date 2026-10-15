// Browser-only extensions to the published synthetic baseline. No real business data.
export function scenario(r,premium=.1,demandScale=1){
 if(!Number.isFinite(premium)||premium<0||premium>.2||!Number.isFinite(demandScale)||demandScale<0||demandScale>2)throw new RangeError('Invalid scenario assumptions');
 const Shelf=r.Benchmark===null?null:Math.floor((r.Benchmark*(1+premium)+1e-9)*20)/20;
 const net=Shelf===null?null:Shelf/(1+r.VAT),MonthlyDemand=r.MonthlyDemand*demandScale;
 return {...r,Shelf,MonthlyDemand,BaseGM:net?1-r.BaseCost/net:null,BulkGM:net&&r.BulkCost!==null?1-r.BulkCost/net:null,
 BaseContribution:net===null?null:net-r.BaseCost-Shelf*r.FeeRate,BulkContribution:net===null||r.BulkCost===null?null:net-r.BulkCost-Shelf*r.FeeRate,
 BulkCover:MonthlyDemand>0?(r.OnHand+r.BulkUnits)/MonthlyDemand:null};
}
export function rankOffers(offers,quantity){
 if(!Number.isInteger(quantity)||quantity<=0)throw new RangeError('Quantity must be a positive integer');
 return offers.filter(o=>o.MinUnits<=quantity).map(o=>({...o,NetGoodsCost:o.UnitCost*quantity,PriceRank:1+new Set(offers.filter(x=>x.SKU===o.SKU&&x.MinUnits<=quantity&&x.UnitCost<o.UnitCost).map(x=>x.UnitCost)).size})).sort((a,b)=>a.SKU.localeCompare(b.SKU)||a.PriceRank-b.PriceRank);
}
