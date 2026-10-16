"""Reproducible continuation from supplied model_v2 exports. All original files remain read-only."""
import argparse,csv,json,sqlite3,hashlib,os,shutil,tempfile,uuid,datetime,traceback
from pathlib import Path
from decimal import Decimal
from collections import Counter
from engine.rules import evidence,benchmark,evaluate,number
from engine.registry import connect,import_rows,read_adapter,history,apply_reviews
ROOT=Path(__file__).resolve().parent

def read(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def dump(path,value):path.write_text(json.dumps(value,indent=2,default=lambda x:float(x) if isinstance(x,Decimal) else str(x)),encoding='utf-8')

def write_csv(path,rows,headers=None):
    headers=headers or (list(rows[0]) if rows else ['Status'])
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=headers,extrasaction='ignore');w.writeheader();w.writerows(rows)

def baseline_audit(root):
    base=root/'model_v2/data';tables={p.stem:read(p) for p in base.glob('*.csv')}
    unique={'DimOffers':'OfferKey','DimProducts':'ProductKey','DimSuppliers':'SupplierKey','FactRetailObservations':'ObservationKey'}
    for t,k in unique.items():
        ids=[x[k] for x in tables[t]]
        if len(ids)!=len(set(ids)) or any(not x for x in ids):raise ValueError(f'Duplicate/missing key {t}.{k}')
    products={x['ProductKey'] for x in tables['DimProducts']};suppliers={x['SupplierKey'] for x in tables['DimSuppliers']};offers={x['OfferKey'] for x in tables['DimOffers']}
    for x in tables['DimOffers']:
        if x['ProductKey'] not in products or x['SupplierKey'] not in suppliers:raise ValueError('Orphan offer dimension')
    for t in ['FactOfferSnapshots','FactProcurementDecisions','FactOfferPriceTiers']:
        if any(x['OfferKey'] not in offers for x in tables[t]):raise ValueError('Orphan '+t)
    ds=tables['FactProcurementDecisions'];obs=tables['FactRetailObservations'];o=tables['DimOffers'];bulk=[x for x in ds if x['BulkVerdict'] in ['Bulk required','Bulk optional']]
    return tables,{'offers':len(o),'products':len(products),'suppliers':len(suppliers),'retail_observations':len(obs),'legacy_decisions':len(ds),'offers_without_legacy_decision':len(offers-{x['OfferKey'] for x in ds}),'legacy_benchmarked':sum(bool(x['Benchmark']) for x in ds),'legacy_missing':sum(not x['Benchmark'] for x in ds),'legacy_coverage':sum(bool(x['Benchmark']) for x in ds)/len(ds) if ds else None,'identity_reviews':sum(x['MatchReviewNeeded']=='Yes' for x in o),'missing_supplier_sku':sum(not x['SupplierSKU'] for x in o),'bulk_required':sum(x['BulkVerdict']=='Bulk required' for x in ds),'bulk_optional':sum(x['BulkVerdict']=='Bulk optional' for x in ds),'bulk_without_stock_cover':sum(not x['BulkCover'] for x in bulk)}

def refresh(root,as_of,import_path=None,adapter_path=None,terms_path=None,demand_path=None,review_path=None):
    datetime.date.fromisoformat(as_of)
    root=Path(root);output=root/'model_v2/refreshed';output.mkdir(parents=True,exist_ok=True)
    lock=output/'refresh.lock'
    try:fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    except FileExistsError:raise RuntimeError('Refresh already locked; investigate interrupted process before removing lock')
    os.write(fd,str(os.getpid()).encode());os.close(fd);stage=None
    started=datetime.datetime.now(datetime.timezone.utc).isoformat();run=uuid.uuid4().hex
    registry=None;db=None
    try:
        tables,counts=baseline_audit(root);stage=Path(tempfile.mkdtemp(prefix='.staging-',dir=output));(stage/'data').mkdir()
        old_pointer=output/'current.json';old=json.loads(old_pointer.read_text()) if old_pointer.exists() else None
        seed=output/old['generation']/'listing_registry.sqlite' if old else root/'model_v2/listing_registry.sqlite'
        if seed.exists():shutil.copy2(seed,stage/'listing_registry.sqlite')
        registry=connect(stage/'listing_registry.sqlite');imports=[]
        if import_path:
            if not adapter_path:raise ValueError('--adapter required with --import-file')
            cfg=json.loads(Path(adapter_path).read_text());incoming=read_adapter(import_path,cfg)
            if any(str(x.get('ObservedAt',''))[:10]>as_of for x in incoming):raise ValueError('Future observation relative to review date')
            imports=import_rows(registry,incoming,hashlib.sha256(Path(import_path).read_bytes()).hexdigest(),started)
        if review_path:
            reviews=read(Path(review_path));known={x['ProductKey'] for x in tables['DimProducts']}|{x[0] for x in registry.execute('SELECT CanonicalProductKey FROM listings')}
            if any(r.get('ProductKey') not in known for r in reviews):raise ValueError('Review references unknown canonical product')
            apply_reviews(registry,reviews,as_of)
        offers={x['OfferKey']:dict(x) for x in tables['DimOffers']};snapshots={}
        for s in tables['FactOfferSnapshots']:
            if s['OfferKey'] not in snapshots or s['SnapshotDate']>snapshots[s['OfferKey']]['SnapshotDate']:snapshots[s['OfferKey']]=dict(s)
        suppliers={x['SupplierKey']:dict(x) for x in tables['DimSuppliers']};products={x['ProductKey']:dict(x) for x in tables['DimProducts']}
        for l in registry.execute('SELECT * FROM listings'):
            p=json.loads(l['CurrentPayload']);k=l['OfferKey']
            offers[k]={**offers.get(k,{}),'OfferKey':k,'ProductKey':l['CanonicalProductKey'],'SupplierKey':l['SupplierID'],'SupplierSKU':l['SupplierSKU'],'SupplierProductName':l['Product'],'ListingID':l['ListingID'],'ListingURL':l['ListingURL'],'MatchStatus':l['MatchStatus'],'MatchReviewNeeded':'No' if l['MatchStatus'].startswith(('Approved','Auto-verified')) else 'Yes'}
            snapshots[k]={'OfferKey':k,**p,'SnapshotDate':p.get('CostDate',''),'SourceType':'Authorised CSV import' if p.get('IsSynthetic')=='No' else 'Synthetic/imported listing; provenance requires review'}
            suppliers.setdefault(l['SupplierID'],{'SupplierKey':l['SupplierID'],'SupplierName':l['SupplierName'],'SupplierStatus':'Imported; verify terms'})
            products.setdefault(l['CanonicalProductKey'],{'ProductKey':l['CanonicalProductKey'],'Product':l['Product'],'Language':l['Language'],'Barcode':l['Barcode'],'ProductType':l['ProductType'],'ProductKeySource':'Registry preserved/generated internal key'})
        terms=json.loads(Path(terms_path).read_text()) if terms_path else {};demands=json.loads(Path(demand_path).read_text()) if demand_path else {}
        qualified=[{**x,**evidence(x,as_of)} for x in tables['FactRetailObservations']]
        byproduct={}
        for row in qualified:byproduct.setdefault(row['ProductKey'],[]).append(row)
        selected={p:benchmark(rows) for p,rows in byproduct.items()};evals=[];issues=[]
        for o in offers.values():
            s=snapshots.get(o['OfferKey'],{});t=terms.get(o['SupplierKey'],{})
            if t.get('Synthetic') and 'SYN' not in o['SupplierKey']:raise ValueError('Synthetic terms cannot apply to legacy/real supplier')
            full={**s,**o,'IdentityApproved':o.get('MatchStatus','').startswith(('Approved match','Auto-verified'))}
            for qty in [1,12,24,36]:
                result=evaluate(full,qty,t,selected.get(o['ProductKey']),demands.get(o['ProductKey']),as_of)
                row={'OfferKey':o['OfferKey'],'ProductKey':o['ProductKey'],'SupplierKey':o['SupplierKey'],'IsSynthetic':int('SYN' in o['SupplierKey'] or s.get('IsSynthetic')=='Yes'),**result};evals.append(row)
                for kind in ['Blockers','ReviewReasons']:
                    for issue in filter(None,result[kind].split('; ')):issues.append({'OfferKey':o['OfferKey'],'ProductKey':o['ProductKey'],'SupplierKey':o['SupplierKey'],'ScenarioQty':qty,'Severity':'Block' if kind=='Blockers' else 'Review','Issue':issue})
        hist=history(registry);registry.close()
        db=sqlite3.connect(stage/'validated.sqlite');db.execute('PRAGMA foreign_keys=ON')
        db.executescript('''CREATE TABLE Suppliers(SupplierKey TEXT PRIMARY KEY,SupplierName TEXT);
        CREATE TABLE Products(ProductKey TEXT PRIMARY KEY,Product TEXT);
        CREATE TABLE Offers(OfferKey TEXT PRIMARY KEY,ProductKey TEXT REFERENCES Products,SupplierKey TEXT REFERENCES Suppliers,MatchStatus TEXT,SupplierSKU TEXT);
        CREATE TABLE Evaluation(OfferKey TEXT REFERENCES Offers,ProductKey TEXT REFERENCES Products,SupplierKey TEXT REFERENCES Suppliers,ScenarioQty INTEGER CHECK(ScenarioQty>0),CostEligible INTEGER,UnitCostExVAT REAL,OrderLandedExVAT REAL,LandedUnitExVAT REAL,GrossMarginPct REAL,PurchasingReadiness TEXT,PRIMARY KEY(OfferKey,ScenarioQty));
        CREATE VIEW Rankings AS SELECT *,DENSE_RANK() OVER(PARTITION BY ProductKey,ScenarioQty ORDER BY LandedUnitExVAT) AS PriceRank,COUNT(*) OVER(PARTITION BY ProductKey,ScenarioQty) AS EligibleOfferCount, LandedUnitExVAT-MIN(LandedUnitExVAT) OVER(PARTITION BY ProductKey,ScenarioQty) AS DifferenceFromBestPerUnit FROM Evaluation WHERE CostEligible=1;
        ''')
        db.executemany('INSERT INTO Suppliers VALUES(?,?)',[(k,x['SupplierName']) for k,x in suppliers.items()]);db.executemany('INSERT INTO Products VALUES(?,?)',[(k,x['Product']) for k,x in products.items()]);db.executemany('INSERT INTO Offers VALUES(?,?,?,?,?)',[(k,x['ProductKey'],x['SupplierKey'],x['MatchStatus'],x.get('SupplierSKU','')) for k,x in offers.items()]);fields=[x[1] for x in db.execute('PRAGMA table_info(Evaluation)')]
        db.executemany('INSERT INTO Evaluation VALUES('+','.join('?'*len(fields))+')',[[float(x[k]) if isinstance(x[k],Decimal) else x[k] for k in fields] for x in evals]);db.commit();db.row_factory=sqlite3.Row;rankings=[dict(x) for x in db.execute('SELECT * FROM Rankings')]
        if db.execute('PRAGMA foreign_key_check').fetchall():raise ValueError('Output foreign keys failed')
        schema=';\n'.join(x[0] for x in db.execute("select sql from sqlite_master where sql is not null"))+';\n';(stage/'schema.sql').write_text(schema);db.close()
        outputs={'Offers':list(offers.values()),'Products':list(products.values()),'Suppliers':list(suppliers.values()),'EvidenceQuality':qualified,'SelectedBenchmarks':[{'ProductKey':k,**v} for k,v in selected.items() if v],'Evaluation':evals,'Rankings':rankings,'Exceptions':issues,'PriceHistory':hist,'ImportResults':imports,'IdentityReview':[x for x in offers.values() if x.get('MatchReviewNeeded')=='Yes']}
        defaults={'ImportResults':['Status','Reason','SupplierID','ListingID','OfferKey'],'SelectedBenchmarks':['ProductKey','ObservationKey','PriceIncVAT','ImmediateReference'],'Exceptions':['OfferKey','ProductKey','SupplierKey','ScenarioQty','Severity','Issue'],'IdentityReview':['OfferKey','ProductKey','SupplierKey','MatchReviewNeeded'],'Rankings':['OfferKey','ProductKey','SupplierKey','ScenarioQty','CostEligible','UnitCostExVAT','OrderLandedExVAT','LandedUnitExVAT','GrossMarginPct','PurchasingReadiness','PriceRank','EligibleOfferCount','DifferenceFromBestPerUnit'],'PriceHistory':['EventKey','ListingID','OfferKey','SupplierID','ObservedAt','BaseCostExVAT','PreviousCostExVAT','AbsoluteChange','PercentageChange','Currency','MovementComparable','SourceURL']}
        for name,rows in outputs.items():
            headers=list(dict.fromkeys(k for row in rows for k in row)) if rows else defaults.get(name,['Status'])
            write_csv(stage/'data'/f'{name}.csv',rows,headers)
        report={'status':'PASS_WITH_REVIEW_ITEMS','as_of':as_of,'run_id':run,'original_snapshot':counts,'current_offers':len(offers),'current_products':len(products),'current_suppliers':len(suppliers),'scenario_rows':len(evals),'cost_eligible_rows':len(rankings),'evidence_classes':dict(Counter(x['EvidenceClass'] for x in qualified)),'history_events':len(hist),'imports':imports,'issues':len(issues),'baseline_preserved':True,'limitations':['No live supplier feeds','Unknown terms block cost rankings','Desktop validation is recorded separately; public standalone M/DAX fixture not compiled','Original PBIX unchanged','Price references are recorded evidence, not live rechecks']}
        dump(stage/'validation.json',report);write_csv(stage/'data/RefreshStatus.csv',[{'AsOfDate':as_of,'Status':report['status'],'Offers':len(offers),'ReviewItems':len(issues),'RunID':run}])
        generation='generation-'+run;os.replace(stage,output/generation);stage=None
        tmp=output/'current.next.json';dump(tmp,{'generation':generation,'as_of':as_of,'run_id':run});os.replace(tmp,output/'current.json')
        dump(output/'last_attempt.json',{'status':'SUCCESS','run_id':run,'as_of':as_of});return report
    except Exception as exc:
        dump(output/'last_attempt.json',{'status':'FAILED','run_id':run,'error':str(exc),'previous_success_unchanged':True});raise
    finally:
        # Windows cannot remove staged SQLite files while a connection is open.
        # Close on every failure path as well as on successful publication.
        if registry is not None:registry.close()
        if db is not None:db.close()
        if stage:shutil.rmtree(stage)
        lock.unlink(missing_ok=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--as-of',default=datetime.date.today().isoformat());p.add_argument('--import-file',type=Path);p.add_argument('--adapter',type=Path);p.add_argument('--terms',type=Path);p.add_argument('--demand',type=Path);p.add_argument('--identity-reviews',type=Path);a=p.parse_args()
    try:print(json.dumps(refresh(a.root,a.as_of,a.import_file,a.adapter,a.terms,a.demand,a.identity_reviews),indent=2,default=str))
    except Exception as e:print('REFRESH FAILED:',e);raise SystemExit(1)
