export function decide(r,target=.3){
 if(r.Benchmark===null)return {verdict:'Missing evidence',recommendation:'Research price'};
 if(r.MonthlyDemand<=0)return {verdict:'Demand assumption missing',recommendation:'Review demand'};
 const base=r.BaseGM>=target&&r.BaseContribution>0;
 const bulk=r.BulkCost!==null&&r.BulkCost<r.BaseCost&&r.BulkGM>=target&&r.BulkContribution>0;
 const verdict=r.BulkCost===null?'No bulk offer':r.BulkCost>=r.BaseCost?'No unit saving':base?'Bulk optional':bulk?'Bulk required':'Below target';
 const recommendation=r.Availability!=='In stock'?'Verify availability':base?'Trial candidate':bulk?(r.BulkCover===null||r.BulkCover>r.MaxCover?'Review stock exposure':'Bulk candidate'):'Below target';
 return {verdict,recommendation};
}
