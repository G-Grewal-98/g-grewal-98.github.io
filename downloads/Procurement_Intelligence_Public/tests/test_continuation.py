import unittest,tempfile,copy,json,csv,sqlite3,shutil,hashlib
from pathlib import Path
from decimal import Decimal as D
from engine.rules import *
from engine.registry import connect,import_rows,history,read_adapter
from refresh_v2 import refresh
ROOT=Path(__file__).resolve().parents[1]
ASOF='2026-10-15'
def offer(**kw):
    return dict(OfferKey='O1',SupplierKey='SYN_A',IdentityApproved=True,BaseCostExVAT='10',BulkCostExVAT='8',BulkThreshold='24',MOQ='1',OrderMultiple='1',SupplierStock='100',Availability='In stock',Currency='GBP',SnapshotDate=ASOF,**kw)
def terms():return dict(Confirmed=True,VATRate='.2',ShippingExVAT='6',MinimumSpendExVAT='0',OtherChargesExVAT='0',InputVATRecoverable=True,FeeRate='.015',TargetGM='.3',MaxCoverMonths='3')
def obs(**kw):
    r=dict(Include='Yes',Match='Exact',UKComparable='Yes',PriceIncVAT='24',CheckedDate=ASOF,URL='https://retailer.example/item',Availability='In stock');r.update(kw);return r
def listing(**kw):
    r=dict(SupplierID='SYN_A',SupplierName='Fictional A',ExternalListingID='A1',SupplierSKU='',ListingURL='https://a.example/1',Product='Synthetic unit',BaseCostExVAT='24.95',MOQ='1',OrderMultiple='1',ObservedAt=ASOF+'T10:00:00Z',Currency='GBP',Language='English',ProductType='Box',PackQuantity='1',Barcode='4006381333931',Edition='Demo',Region='UK',Variant='Standard');r.update(kw);return r
class EvidenceTests(unittest.TestCase):
    def test_current(self):self.assertEqual(evidence(obs(),ASOF)['ImmediateReference'],1)
    def test_conflict(self):self.assertFalse(evidence(obs(Availability='Stock conflict'),ASOF)['BenchmarkEligible'])
    def test_stale(self):self.assertEqual(evidence(obs(CheckedDate='2026-01-01'),ASOF)['ImmediateReference'],0)
    def test_future(self):self.assertFalse(evidence(obs(CheckedDate='2027-01-01'),ASOF)['BenchmarkEligible'])
    def test_similar(self):self.assertFalse(evidence(obs(Match='Similar'),ASOF)['BenchmarkEligible'])
    def test_missing_url(self):self.assertFalse(evidence(obs(URL=''),ASOF)['BenchmarkEligible'])
    def test_unknown(self):self.assertEqual(evidence(obs(Availability='Unknown'),ASOF)['ImmediateReference'],0)
    def test_soldout(self):self.assertEqual(evidence(obs(Availability='Sold out'),ASOF)['ImmediateReference'],0)
    def test_priority(self):
        a=obs(PriceIncVAT='1',Availability='Sold out');b=obs();self.assertEqual(benchmark([{**x,**evidence(x,ASOF)} for x in [a,b]])['PriceIncVAT'],'24')
class IdentityTests(unittest.TestCase):
    def test_exact(self):self.assertEqual(identity_match(listing(),listing())['status'],'Approved')
    def test_missing_barcode(self):self.assertEqual(identity_match(listing(Barcode=''),listing())['status'],'Review')
    def test_bad_checksum(self):self.assertEqual(identity_match(listing(Barcode='4006381333932'),listing())['status'],'Review')
    def test_different_variants(self):
        for k,v in [('Language','Japanese'),('PackQuantity','6'),('Edition','Other'),('Region','US')]:
            with self.subTest(k=k):self.assertEqual(identity_match(listing(**{k:v}),listing())['status'],'Separate')
    def test_missing_attribute(self):self.assertEqual(identity_match(listing(Edition=''),listing())['status'],'Review')
class EconomicsTests(unittest.TestCase):
    def test_scenarios(self):
        for q,c in [(1,10),(12,10),(24,8),(36,8)]:
            with self.subTest(q=q):
                r=evaluate(offer(),q,terms(),as_of=ASOF);self.assertEqual(r['UnitCostExVAT'],D(c));self.assertEqual(r['OrderLandedExVAT'],D(c*q+6));self.assertEqual(r['CostEligible'],1)
    def test_vat_margin(self):
        r=evaluate(offer(),12,terms(),{'PriceIncVAT':'24','ImmediateReference':1},{'MonthlyDemand':'10','OnHand':'0','Verified':True},ASOF)
        self.assertEqual(r['EstimatedCashOutlayGBP'],D('151.2'));self.assertEqual(r['GrossMarginPct'],D('.475'));self.assertEqual(r['PurchasingReadiness'],'Review-ready — human decision')
    def test_moq_multiple(self):
        o=offer();o.update(MOQ='12',OrderMultiple='6');self.assertFalse(evaluate(o,1,terms(),as_of=ASOF)['CostEligible']);self.assertTrue(evaluate(o,12,terms(),as_of=ASOF)['CostEligible'])
    def test_stock(self):
        o=offer();o['SupplierStock']='11';self.assertFalse(evaluate(o,12,terms(),as_of=ASOF)['CostEligible'])
    def test_unknown_terms(self):self.assertFalse(evaluate(offer(),12,as_of=ASOF)['CostEligible'])
    def test_fx(self):
        o=offer();o['Currency']='EUR';self.assertFalse(evaluate(o,12,terms(),as_of=ASOF)['CostEligible'])
    def test_no_demand(self):self.assertIn('demand',evaluate(offer(),12,terms(),as_of=ASOF)['ReviewReasons'])
    def test_no_vat_recovery(self):
        t=terms();t['InputVATRecoverable']=False;self.assertFalse(evaluate(offer(),12,t,as_of=ASOF)['CostEligible'])
    def test_minimum_and_free_shipping(self):
        t=terms();t.update(MinimumSpendExVAT=200,FreeShippingThresholdExVAT=250);self.assertFalse(evaluate(offer(),12,t,as_of=ASOF)['CostEligible']);self.assertEqual(evaluate(offer(),36,t,as_of=ASOF)['ShippingExVAT'],0)
    def test_basket(self):
        b=offer();b['OfferKey']='O2';t=terms();t['MinimumSpendExVAT']=200
        r=basket([(offer(),12),(b,12)],t,ASOF);self.assertEqual(r['OrderLandedExVAT'],246);self.assertTrue(r['CostEligible']);self.assertEqual(sum(x['AllocatedChargesExVAT'] for x in r['Lines']),6)
    def test_basket_invalid_minimum(self):
        t=terms();t['MinimumSpendExVAT']=-1;self.assertFalse(basket([(offer(),12)],t,ASOF)['CostEligible'])
    def test_basket_mixed_suppliers(self):
        b=offer();b.update(OfferKey='O2',SupplierKey='SYN_B')
        with self.assertRaises(ValueError):basket([(offer(),1),(b,1)],terms(),ASOF)
class RegistryTests(unittest.TestCase):
    def setUp(self):self.db=connect(':memory:')
    def tearDown(self):self.db.close()
    def put(self,rows):return import_rows(self.db,rows,'hash',ASOF+'T16:00:00Z')
    def test_price_history_regression(self):
        self.put([listing()]);self.put([listing(BaseCostExVAT='22.95',ObservedAt=ASOF+'T15:00:00Z')]);h=history(self.db);self.assertEqual(len(h),2);self.assertEqual(h[-1]['AbsoluteChange'],D('-2'));self.assertEqual(h[-1]['PercentageChange'],D('-2')/D('24.95'))
    def test_duplicate_unchanged(self):
        self.put([listing()]);self.put([listing()]);self.put([listing(ObservedAt=ASOF+'T15:00:00Z')]);self.assertEqual(len(history(self.db)),1)
    def test_url_change_retains_identity(self):
        a=self.put([listing()])[0];b=self.put([listing(ListingURL='https://a.example/new',ObservedAt=ASOF+'T15:00:00Z')])[0];self.assertEqual(a['ListingID'],b['ListingID']);self.assertEqual(len(history(self.db)),1)
    def test_cross_supplier_sku(self):
        a=self.put([listing(SupplierSKU='X')])[0];b=self.put([listing(SupplierID='SYN_B',SupplierSKU='X')])[0];self.assertNotEqual(a['ListingID'],b['ListingID']);self.assertEqual(len({r[0] for r in self.db.execute('SELECT CanonicalProductKey FROM listings')}),1)
    def test_conflicting_timestamp_rollback(self):
        self.put([listing()]);before=history(self.db)
        with self.assertRaises(ValueError):self.put([listing(BaseCostExVAT='20')])
        self.assertEqual(history(self.db),before)
    def test_variant_revised(self):
        self.put([listing()]);self.put([listing(Language='Japanese',ObservedAt=ASOF+'T15:00:00Z')]);self.assertEqual(self.db.execute('SELECT COUNT(*) FROM identity_audit').fetchone()[0],1);self.assertEqual(history(self.db)[-1]['MovementComparable'],0)
    def test_missing_keys(self):
        r=self.put([listing(ExternalListingID='',ListingURL='',SupplierSKU='')]);self.assertEqual(r[0]['Status'],'Quarantined');self.assertEqual(len(history(self.db)),0)
    def test_bad_number_atomic(self):
        with self.assertRaises(ValueError):self.put([listing(),listing(ExternalListingID='A2',BaseCostExVAT='NaN')])
        self.assertEqual(len(history(self.db)),0)
    def test_adapter(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'input.csv';p.write_text('cost,id\n24.95,A1\n');cfg=dict(authorized_export=True,supplier_id='SYN_A',synthetic=True,columns={'BaseCostExVAT':'cost','ExternalListingID':'id'},constants={'SupplierID':'SYN_A'})
            self.assertEqual(read_adapter(p,cfg)[0]['BaseCostExVAT'],'24.95');cfg['authorized_export']=False
            with self.assertRaises(ValueError):read_adapter(p,cfg)
class RefreshTests(unittest.TestCase):
    def test_atomic_repeat_and_preservation(self):
        with tempfile.TemporaryDirectory(prefix='project with spaces ') as d:
            root=Path(d);shutil.copytree(ROOT/'model_v2/data',root/'model_v2/data');shutil.copy2(ROOT/'model_v2/listing_registry.sqlite',root/'model_v2/listing_registry.sqlite')
            hashes={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
            a=refresh(root,ASOF);b=refresh(root,ASOF);self.assertEqual(a['history_events'],b['history_events']);self.assertEqual(a['scenario_rows'],b['scenario_rows']);pointer=(root/'model_v2/refreshed/current.json').read_bytes()
            with self.assertRaises(ValueError):refresh(root,ASOF,Path('missing.csv'))
            self.assertEqual(pointer,(root/'model_v2/refreshed/current.json').read_bytes());self.assertEqual(json.loads((root/'model_v2/refreshed/last_attempt.json').read_text())['status'],'FAILED')
            for f,h in hashes.items():self.assertEqual(hashlib.sha256((root/f).read_bytes()).hexdigest(),h)

class AdditionalTests(unittest.TestCase):
    def test_manual_review_audit(self):
        from engine.registry import apply_reviews
        db=connect(':memory:');a=import_rows(db,[listing()],'h','2026-10-15T16:00:00Z')[0]
        review=dict(ListingID=a['ListingID'],ProductKey='KNOWN_PRODUCT',Reviewer='Fixture Analyst',Evidence='Synthetic exact variant assessment',ReviewedAt='2026-10-15T16:00:00Z',Decision='Approve')
        apply_reviews(db,[review],ASOF);apply_reviews(db,[review],ASOF)
        self.assertEqual(db.execute('SELECT COUNT(*) FROM identity_audit').fetchone()[0],1);self.assertEqual(db.execute('SELECT CanonicalProductKey FROM listings').fetchone()[0],'KNOWN_PRODUCT');self.assertEqual(len(history(db)),1);db.close()
    def test_alias_conflict_rolls_back(self):
        db=connect(':memory:');import_rows(db,[listing(),listing(ExternalListingID='A2',ListingURL='https://a.example/2')],'h','2026-10-15T16:00:00Z')
        with self.assertRaises(ValueError):import_rows(db,[listing(ExternalListingID='A1',ListingURL='https://a.example/2')],'h2','2026-10-15T16:00:00Z')
        self.assertEqual(len(history(db)),2);db.close()
    def test_fractional_timestamp_order(self):
        db=connect(':memory:');import_rows(db,[listing()],'h','2026-10-15T16:00:00Z');import_rows(db,[listing(BaseCostExVAT='22.95',ObservedAt='2026-10-15T10:00:00.5Z')],'h2','2026-10-15T16:00:00Z');self.assertEqual(history(db)[-1]['AbsoluteChange'],D('-2'));db.close()
    def test_invalid_target_cannot_be_ready(self):
        t=terms();t['TargetGM']=-1;r=evaluate(offer(),12,t,{'PriceIncVAT':'24','ImmediateReference':1},{'MonthlyDemand':10,'OnHand':0,'Verified':True},ASOF);self.assertEqual(r['PurchasingReadiness'],'Review required')
    def test_zero_quantity(self):
        with self.assertRaises(ValueError):evaluate(offer(),0,terms(),as_of=ASOF)
    def test_typed_rankings(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);shutil.copytree(ROOT/'model_v2/data',root/'model_v2/data');shutil.copy2(ROOT/'model_v2/listing_registry.sqlite',root/'model_v2/listing_registry.sqlite');refresh(root,ASOF)
            ptr=json.loads((root/'model_v2/refreshed/current.json').read_text());db=sqlite3.connect(root/'model_v2/refreshed'/ptr['generation']/'validated.sqlite')
            self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(),[]);self.assertEqual(db.execute('SELECT COUNT(*) FROM Rankings').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT COUNT(DISTINCT ScenarioQty) FROM Evaluation').fetchone()[0],4);db.close()

class SourceLanguageTests(unittest.TestCase):
    def test_negative_conflict_phrase(self):
        self.assertEqual(evidence(obs(Evidence='Language checked; no conflicting variant identified.'),ASOF)['ImmediateReference'],1)
    def test_affirmative_conflict_after_negative(self):
        self.assertFalse(evidence(obs(Evidence='No conflicting variant identified. Conflicting page stock signals.'),ASOF)['BenchmarkEligible'])

class TargetTests(unittest.TestCase):
    def test_target_retail_and_gross_profit(self):
        r=evaluate(offer(),12,terms(),{'PriceIncVAT':'24','ImmediateReference':1},as_of=ASOF)
        self.assertEqual(r['TargetRetailIncVAT'],D('18'));self.assertEqual(r['UnitGrossProfitExVAT'],D('9.5'))
