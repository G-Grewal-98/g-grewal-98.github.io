"""Synthetic supplier comparison; run after run_pipeline.py. No live suppliers."""
import csv,json,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def build():
    with sqlite3.connect(ROOT/'procurement.sqlite') as db:
        db.row_factory=sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('DROP TABLE IF EXISTS Offers')
        db.execute('DROP TABLE IF EXISTS Suppliers')
        db.execute('CREATE TABLE Suppliers(SupplierID TEXT PRIMARY KEY NOT NULL, Supplier TEXT NOT NULL)')
        db.execute('CREATE TABLE Offers(OfferID TEXT PRIMARY KEY NOT NULL, SKU TEXT NOT NULL REFERENCES Products(SKU), SupplierID TEXT NOT NULL REFERENCES Suppliers(SupplierID), UnitCost REAL NOT NULL CHECK(UnitCost>0), MinUnits INTEGER NOT NULL CHECK(MinUnits>0))')
        for table in ['Suppliers','Offers']:
            with (ROOT/'data'/f'{table}.csv').open() as f:
                data=csv.reader(f); headers=next(data)
                db.executemany(f'INSERT INTO {table} VALUES ({",".join("?" for _ in headers)})',list(data))
        rows=[dict(r) for r in db.execute((ROOT/'sql/supplier_comparison.sql').read_text())]
        checks={'six_offers':db.execute('SELECT COUNT(*) FROM Offers').fetchone()[0]==6,
          'foreign_keys':not db.execute('PRAGMA foreign_key_check').fetchall(),
          'minimum_quantity_exclusion':len(rows)==5 and all(r['MinUnits']<=24 for r in rows),
          'three_preferred_offers':len([r for r in rows if r['PriceRank']==1])==3,
          'basket_cost':all(abs(r['NetGoodsCost']-r['UnitCost']*24)<1e-9 for r in rows)}
        assert all(checks.values()), checks
        (ROOT/'supplier_comparison.json').write_text(json.dumps({'requested_units':24,'rows':rows,'checks':checks},indent=2))
        print(json.dumps({'supplier_checks_passed':len(checks),'eligible_offers':len(rows)}))
if __name__=='__main__':build()
