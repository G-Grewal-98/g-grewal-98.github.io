import unittest,tempfile,sqlite3,json,shutil
from pathlib import Path
from openpyxl import Workbook
from engine.registry import read_adapter
from refresh_v2 import refresh
ROOT=Path(__file__).resolve().parents[1]
def cfg():return {'authorized_export':True,'supplier_id':'SYN_X','synthetic':True,'columns':{'SupplierSKU':'sku','BaseCostExVAT':'cost'},'constants':{'SupplierID':'SYN_X'}}
class ExportTests(unittest.TestCase):
    def xlsx(self,path,rows,extra_sheet=False):
        w=Workbook();s=w.active;s.title='Catalogue'
        for row in rows:s.append(row)
        if extra_sheet:w.create_sheet('Notes')
        w.save(path);w.close()
    def test_xlsx_preserves_text_ids_and_nulls(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'export.xlsx';self.xlsx(p,[['sku','cost'],['00123',24.95],['00004',None]])
            rows=read_adapter(p,cfg());self.assertEqual(rows[0]['SupplierSKU'],'00123');self.assertIsNone(rows[1]['BaseCostExVAT']);self.assertEqual(rows[0]['IsSynthetic'],'Yes')
    def test_xlsx_requires_authorisation(self):
        with self.assertRaises(ValueError):read_adapter(Path('absent.xlsx'),{**cfg(),'authorized_export':False})
    def test_xlsx_rejects_formula_price(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'export.xlsx';self.xlsx(p,[['sku','cost'],['00123','=20+5']])
            with self.assertRaisesRegex(ValueError,'formulas'):read_adapter(p,cfg())
    def test_xlsx_rejects_numeric_identity(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'export.xlsx';self.xlsx(p,[['sku','cost'],[123,24.95]])
            with self.assertRaisesRegex(ValueError,'text'):read_adapter(p,cfg())
    def test_xlsx_requires_sheet_selection(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'export.xlsx';self.xlsx(p,[['sku','cost'],['00123',24.95]],True)
            with self.assertRaisesRegex(ValueError,'explicit sheet'):read_adapter(p,cfg())
            self.assertEqual(len(read_adapter(p,{**cfg(),'sheet':'Catalogue'})),1)
    def test_xlsx_rejects_missing_sheet(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'export.xlsx';self.xlsx(p,[['sku','cost']])
            with self.assertRaisesRegex(ValueError,'sheet is missing'):read_adapter(p,{**cfg(),'sheet':'Missing'})
    def test_duplicate_csv_headers_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'export.csv';p.write_text('sku,cost,cost\n00123,1,2\n')
            with self.assertRaisesRegex(ValueError,'Duplicate'):read_adapter(p,cfg())
    def test_malformed_csv_row_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'export.csv';p.write_text('sku,cost\n00123,1,extra\n')
            with self.assertRaisesRegex(ValueError,'row length'):read_adapter(p,cfg())
    def test_tsv_export(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'export.tsv';p.write_text('sku\tcost\n00123\t1\n')
            self.assertEqual(read_adapter(p,cfg())[0]['SupplierSKU'],'00123')
    def test_failed_refresh_releases_database_and_lock(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);shutil.copytree(ROOT/'model_v2/data',r/'model_v2/data');shutil.copy2(ROOT/'model_v2/listing_registry.sqlite',r/'model_v2/listing_registry.sqlite')
            refresh(r,'2026-10-15');pointer=(r/'model_v2/refreshed/current.json').read_bytes()
            for _ in range(2):
                with self.assertRaises(ValueError):refresh(r,'2026-10-15',Path('missing.csv'))
                self.assertEqual(pointer,(r/'model_v2/refreshed/current.json').read_bytes())
                self.assertFalse((r/'model_v2/refreshed/refresh.lock').exists());self.assertFalse(list((r/'model_v2/refreshed').glob('.staging-*')))
            refresh(r,'2026-10-15')
    def test_active_lock_prevents_concurrent_refresh(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);o=r/'model_v2/refreshed';o.mkdir(parents=True);(o/'refresh.lock').write_text('test active process')
            with self.assertRaisesRegex(RuntimeError,'locked'):refresh(r,'2026-10-15')
            self.assertEqual((o/'refresh.lock').read_text(),'test active process')
