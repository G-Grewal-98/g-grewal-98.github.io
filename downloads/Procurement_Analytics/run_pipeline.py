"""Rebuild the public synthetic procurement demonstration. Python 3.10+, stdlib only.
Run: python run_pipeline.py
Inputs are data/Products.csv and data/Prices.csv. Never uses private business files.
"""
import csv, json, math, pathlib, sqlite3
ROOT=pathlib.Path(__file__).resolve().parent

def export(db,query,path):
    cur=db.execute(query)
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow([d[0] for d in cur.description]);w.writerows(cur)

def build():
    db=sqlite3.connect(':memory:'); db.row_factory=sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.executescript((ROOT/'sql/model.sql').read_text())
    for table in ['Products','Prices']:
        with (ROOT/'data'/f'{table}.csv').open(newline='',encoding='utf-8') as f:
            rows=csv.DictReader(f); fields=rows.fieldnames
            db.executemany(f'INSERT INTO {table} VALUES ({",".join("?" for _ in fields)})',
                          [[r[k] if r[k]!='' else None for k in fields] for r in rows])
    checks={}
    def check(name,condition):
        if not condition: raise AssertionError(name)
        checks[name]=True
    check('foreign_keys',not db.execute('PRAGMA foreign_key_check').fetchall())
    check('one_metric_per_product',db.execute('SELECT COUNT(*) FROM v_metrics').fetchone()[0]==db.execute('SELECT COUNT(*) FROM Products').fetchone()[0])
    rows=[dict(r) for r in db.execute('SELECT * FROM v_metrics ORDER BY SKU')]
    for r in rows:
        if r['Benchmark'] is not None:
            shelf=math.floor(round(r['Benchmark']*1.1*20,8))/20
            check('python_sql_margin_'+r['SKU'],math.isclose(r['BaseGM'],1-r['BaseCost']/(shelf/1.2),abs_tol=1e-10))
        check('bulk_rounding_'+r['SKU'],r['BulkUnits']==math.ceil(r['BulkThreshold']/r['OrderMultiple'])*r['OrderMultiple'])
    check('missing_and_stale_evidence_excluded',next(r for r in rows if r['SKU']=='P005')['Benchmark'] is None)
    check('sold_out_requires_review',next(r for r in rows if r['SKU']=='P006')['Recommendation']=='Verify availability')
    check('bulk_stock_exposure',next(r for r in rows if r['SKU']=='P004')['Recommendation']=='Review stock exposure')
    check('bulk_candidate',next(r for r in rows if r['SKU']=='P002')['Recommendation']=='Bulk candidate')
    # Mutate inside a savepoint to prove selection, exclusions and missing-value behaviour.
    db.execute('SAVEPOINT test_rules')
    db.execute("INSERT INTO Prices VALUES ('TEST1','P001','Demo seller',0.1,'2026-10-14','In stock','Similar')")
    db.execute("INSERT INTO Prices VALUES ('TEST2','P001','Demo seller',0.2,'2027-01-01','In stock','Exact')")
    check('similar_and_future_excluded',db.execute("SELECT Benchmark FROM v_metrics WHERE SKU='P001'").fetchone()[0]==rows[0]['Benchmark'])
    db.execute("INSERT INTO Prices VALUES ('TEST3','P001','Demo seller',0.3,'2026-10-14','Sold out','Exact')")
    check('in_stock_preferred',db.execute("SELECT Benchmark FROM v_metrics WHERE SKU='P001'").fetchone()[0]==rows[0]['Benchmark'])
    db.execute("DELETE FROM Prices WHERE SKU='P001'")
    check('missing_margin_remains_null',db.execute("SELECT BaseGM FROM v_metrics WHERE SKU='P001'").fetchone()[0] is None)
    try:
        db.execute("INSERT INTO Products SELECT * FROM Products WHERE SKU='P001'")
        raise AssertionError('duplicate_sku')
    except sqlite3.IntegrityError: checks['duplicate_sku_rejected']=True
    db.execute('ROLLBACK TO test_rules');db.execute('RELEASE test_rules')
    export(db,'SELECT * FROM v_metrics ORDER BY SKU',ROOT/'data/Metrics.csv')
    export(db,'SELECT * FROM Settings',ROOT/'data/Settings.csv')
    report={'dataset':'Fictional demonstration; no actual commercial data',
      'products':len(rows),'observations':db.execute('SELECT COUNT(*) FROM Prices').fetchone()[0],
      'benchmarked':sum(r['Benchmark'] is not None for r in rows),'checks':checks,
      'power_bi':'Power Query and DAX supplied; not executed in Desktop'}
    # Write only after all checks succeed. Atomic database replacement.
    temp=ROOT/'procurement.tmp.sqlite'
    if temp.exists():temp.unlink()
    db.commit()
    with sqlite3.connect(temp) as target:db.backup(target)
    temp.replace(ROOT/'procurement.sqlite')
    (ROOT/'validation.json').write_text(json.dumps(report,indent=2))
    (ROOT/'demo.json').write_text(json.dumps({'rows':rows,'validation':report},indent=2))
    print(json.dumps({'products':len(rows),'checks_passed':len(checks),'benchmarked':report['benchmarked']}))

if __name__=='__main__':build()
