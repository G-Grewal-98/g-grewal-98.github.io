"""Rebuild the portfolio database and BI exports. Python 3.10+, standard library only.
Usage: python run_pipeline.py path/to/recalculated_workbook.xlsx
Reads cached Excel results, never edits the workbook. Fails on missing/stale caches.
"""
import argparse, csv, datetime as dt, json, pathlib, sqlite3, zipfile
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent
NS = {'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
PRODUCTS = 'SKU Product Category Barcode Language Supplier BaseCost BulkThreshold BulkCost MOQ OrderMultiple SupplierStock CostDate LandedExtras DemandRating MonthlySales OnHand PlannedQty ShelfOverride Active CostReview Notes ProductType'.split()
PRICES = 'SourceID SKU Retailer ListingTitle URL Price CheckedDate Availability Match UKComparable Include Evidence Delivery DeliveryNotes Origin SubmittedURL Language SupplierFormat OriginalLink'.split()
DECISIONS = 'SKU Product Recommendation Rating BulkVerdict Benchmark Shelf BaseGM BulkGM BulkUnits BulkCash BulkCover PlannedQty PlannedCash PlannedContribution Explanation BaseCost BulkCost LandedExtras LowestExact LowestAvailable Basis CheckedDate Retailer URL MaxBuyCost UnitDiscount BulkGoods CostStatus PriceStatus BaseFeasible BulkFeasible EffectiveCost UnitContribution PlannedGoods PlannedGrossProfit PlannedCover InputStatus DemandRating MonthlySales OnHand MOQ OrderMultiple SupplierStock CostDate LookupKey LineStatus SelectedGM'.split()

def read_workbook(path):
    """Minimal read-only XLSX extraction; IDs remain strings and nulls remain null."""
    with zipfile.ZipFile(path) as z:
        strings=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            strings=[''.join(e.itertext()) for e in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si',NS)]
        rel={e.attrib['Id']:e.attrib['Target'] for e in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        sheets={}
        for sh in ET.fromstring(z.read('xl/workbook.xml')).findall('m:sheets/m:sheet',NS):
            target=rel[sh.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
            target=target.lstrip('/') if target.startswith('/') else 'xl/'+target
            rows={}
            for row in ET.fromstring(z.read(target)).findall('m:sheetData/m:row',NS):
                cells={}
                for c in row:
                    v=c.find('m:v',NS); t=c.attrib.get('t'); val=None
                    if t=='e': raise ValueError(f"Excel error: {sh.attrib['name']}!{c.attrib['r']}")
                    if t=='inlineStr': val=''.join(c.find('m:is',NS).itertext())
                    elif v is not None and v.text is not None:
                        val=strings[int(v.text)] if t=='s' else v.text if t=='str' else float(v.text)
                    col=''.join(x for x in c.attrib['r'] if x.isalpha())
                    n=0
                    for x in col:n=n*26+ord(x)-64
                    cells[n-1]=val if val!='' else None
                rows[int(row.attrib['r'])]=cells
            sheets[sh.attrib['name']]=rows
        return sheets

def iso(v):
    return (dt.datetime(1899,12,30)+dt.timedelta(days=float(v))).date().isoformat() if v is not None else None

def records(sheets,sheet,headers,datecols=()):
    out=[]
    for n,row in sorted(sheets[sheet].items()):
        if n<5 or row.get(0) is None:continue
        obj={k:row.get(i) for i,k in enumerate(headers)}
        for k in datecols:obj[k]=iso(obj[k])
        for k in ['SKU','Barcode','SourceID']:
            if k in obj and obj[k] is not None:
                x=obj[k];obj[k]=str(int(x)) if isinstance(x,float) and x.is_integer() else str(x)
        out.append(obj)
    return out

def export(db,query,path):
    cur=db.execute(query)
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.writer(f);writer.writerow([c[0] for c in cur.description]);writer.writerows(cur)

def build(path):
    sheets=read_workbook(path)
    products=records(sheets,'Products',PRODUCTS,['CostDate'])
    prices=records(sheets,'Price Sources',PRICES,['CheckedDate'])
    decisions=records(sheets,'Buying Review',DECISIONS,['CheckedDate','CostDate'])
    if not products or len(products)!=len(decisions):raise ValueError('Missing calculated decisions. Recalculate and save in Excel.')
    if any(d['InputStatus']!='Valid' for d in decisions):raise ValueError('Resolve invalid workbook inputs before publishing data.')
    c=sheets['Controls']; value=lambda r:c[r].get(1)
    settings={'AsOfDate':iso(value(4)),'VAT':value(5),'TargetGM':value(6),'MinimumGM':value(7),'StrongGM':value(8),'Premium':value(9),'FeeRate':value(10),'FreshDays':value(11),'MaxCover':value(12),'MinDemand':value(13),'CashBudget':value(14),'MinimumOrder':value(15),'TermsConfirmed':value(16),'Freight':value(17),'MinContribution':value(20),'OrderSupplier':value(24)}
    db=sqlite3.connect(':memory:');db.execute('PRAGMA foreign_keys=ON')
    textfields=set('SKU Product Category Barcode Language Supplier CostDate Active CostReview Notes ProductType SourceID Retailer ListingTitle URL CheckedDate Availability Match UKComparable Include Evidence DeliveryNotes Origin SubmittedURL SupplierFormat Recommendation BulkVerdict Explanation Basis CostStatus PriceStatus BaseFeasible BulkFeasible InputStatus LookupKey LineStatus AsOfDate TermsConfirmed OrderSupplier'.split())
    for name,rows,key in [('Products',products,'SKU'),('Prices',prices,'SourceID'),('Decisions',decisions,'SKU'),('Settings',[settings],None)]:
        cols=list(rows[0]);defs=[f'"{k}" '+('TEXT' if k in textfields else 'REAL')+(' PRIMARY KEY NOT NULL' if k==key else '') for k in cols]
        if name in ('Prices','Decisions'):defs.append('FOREIGN KEY(SKU) REFERENCES Products(SKU)')
        db.execute(f'CREATE TABLE {name} ({",".join(defs)})')
        db.executemany(f'INSERT INTO {name} VALUES ({",".join("?" for _ in cols)})',[[r[k] for k in cols] for r in rows])
    db.executescript((ROOT/'sql/model.sql').read_text())
    checks={}
    def check(name,condition):
        checks[name]=bool(condition)
        if not condition:raise AssertionError(name)
    check('foreign_keys',not db.execute('PRAGMA foreign_key_check').fetchall())
    check('unique_source_ids',len({p['SourceID'] for p in prices})==len(prices))
    check('positive_base_cost',all(p['BaseCost'] and p['BaseCost']>0 for p in products))
    check('benchmark_reconciliation',db.execute('SELECT COUNT(*) FROM v_reconciliation WHERE BenchmarkMismatch=1').fetchone()[0]==0)
    check('margin_reconciliation',db.execute('SELECT COUNT(*) FROM v_reconciliation WHERE MarginMismatch=1').fetchone()[0]==0)
    check('rating_reconciliation',db.execute('SELECT COUNT(*) FROM v_reconciliation WHERE RatingMismatch=1').fetchone()[0]==0)
    check('bulk_units_reconciliation',db.execute('SELECT COUNT(*) FROM v_reconciliation WHERE BulkUnitsMismatch=1').fetchone()[0]==0)
    check('price_and_date_validity',db.execute('SELECT COUNT(*) FROM v_eligible WHERE Price<=0 OR CheckedDate> (SELECT AsOfDate FROM Settings)').fetchone()[0]==0)
    # Isolated behavioural tests: these never alter the exported database.
    from tests.test_rules import run_tests
    checks.update(run_tests(db))
    out=ROOT/'data';out.mkdir(exist_ok=True)
    for name,query in {'Products':'SELECT * FROM Products','Prices':'SELECT * FROM Prices','Decisions':'SELECT * FROM Decisions','Settings':'SELECT * FROM Settings','Retailers':'SELECT DISTINCT Retailer FROM Prices ORDER BY Retailer','SQLMetrics':'SELECT * FROM v_economics'}.items():export(db,query,out/(name+'.csv'))
    dates=[p['CheckedDate'] for p in prices if p['CheckedDate']]+[settings['AsOfDate']]
    start=dt.date.fromisoformat(min(dates));end=dt.date.fromisoformat(max(dates))
    with (out/'Dates.csv').open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.writer(f);writer.writerow(['Date','Year','Month','MonthName'])
        while start<=end:writer.writerow([start.isoformat(),start.year,start.month,start.strftime('%b')]);start+=dt.timedelta(days=1)
    target=ROOT/'procurement.sqlite'
    if target.exists():target.unlink()
    with sqlite3.connect(target) as dest:db.backup(dest)
    report={'as_of':settings['AsOfDate'],'products':len(products),'observations':len(prices),'benchmarked':db.execute('SELECT COUNT(*) FROM v_economics WHERE Benchmark IS NOT NULL').fetchone()[0],'in_stock':db.execute("SELECT COUNT(*) FROM v_benchmarks WHERE Availability='In stock'").fetchone()[0],'checks':checks,'power_bi_execution':'Not executed: Desktop validation required','excel_execution':'Artifact engine tested; native Excel recalculation not executed'}
    (ROOT/'validation.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    db.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('workbook',type=pathlib.Path)
    build(parser.parse_args().workbook)
