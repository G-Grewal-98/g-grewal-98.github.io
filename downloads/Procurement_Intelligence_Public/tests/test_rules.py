"""Meaningful SQL boundary tests run inside a rolled-back savepoint."""
def run_tests(db):
    checks={}
    def test(name,truth):
        assert truth,name
        checks[name]=True
    db.execute('SAVEPOINT behavioural_tests')
    sku=db.execute('SELECT SKU FROM Products LIMIT 1').fetchone()[0]
    db.execute('DELETE FROM Prices WHERE SKU=?',(sku,))
    db.execute('UPDATE Products SET BaseCost=8,BulkThreshold=10,BulkCost=5,MOQ=1,OrderMultiple=1,ShelfOverride=NULL,LandedExtras=0 WHERE SKU=?',(sku,))
    def source(id,price,stock,match='Exact',date='2026-10-14'):
        db.execute('INSERT INTO Prices(SourceID,SKU,Price,Availability,Match,UKComparable,Include,CheckedDate) VALUES(?,?,?,?,?,?,?,?)',(id,sku,price,stock,match,'Yes','Yes',date))
    db.execute("UPDATE Settings SET AsOfDate='2026-10-14',VAT=.2,Premium=.1,TargetGM=.3,FeeRate=.015,MinContribution=0")
    source('TEST1',8,'Sold out');source('TEST2',10,'In stock')
    get=lambda col:db.execute('SELECT '+col+' FROM v_economics WHERE SKU=?',(sku,)).fetchone()[0]
    test('available_price_preferred_over_cheaper_sold_out',get('Benchmark')==10)
    test('bulk_required_boundary',get('BulkVerdictSQL')=='Bulk required')
    db.execute('UPDATE Products SET OrderMultiple=6 WHERE SKU=?',(sku,))
    test('bulk_rounds_up_to_order_multiple',get('BulkUnits')==12)
    source('TEST3',1,'In stock','Similar');source('TEST4',2,'In stock',date='2027-01-01')
    test('similar_and_future_sources_excluded',get('Benchmark')==10)
    db.execute("UPDATE Prices SET Availability='Sold out' WHERE SourceID='TEST2'")
    test('sold_out_falls_back_to_reference_price',get('Benchmark')==8)
    db.execute('DELETE FROM Prices WHERE SKU=?',(sku,))
    test('missing_price_remains_null',get('Benchmark') is None and get('Rating') is None)
    try:
        db.execute('INSERT INTO Products(SKU) VALUES(?)',(sku,))
        raise AssertionError('duplicate_sku_rejected')
    except __import__('sqlite3').IntegrityError:checks['duplicate_sku_rejected']=True
    db.execute('ROLLBACK TO behavioural_tests');db.execute('RELEASE behavioural_tests')
    return checks
