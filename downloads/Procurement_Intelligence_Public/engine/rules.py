"""Pure rules shared by refresh, baskets and regression tests. Amounts use Decimal."""
from decimal import Decimal, InvalidOperation, ROUND_CEILING
from datetime import date, datetime, timezone
import re

D=Decimal

def number(value, default=None):
    if value is None or str(value).strip()=='': return default
    try:
        x=D(str(value))
        if not x.is_finite(): raise ValueError('non-finite number')
        return x
    except InvalidOperation as exc: raise ValueError('invalid number') from exc

def timestamp(value):
    if not value: raise ValueError('ObservedAt is required')
    v=datetime.fromisoformat(str(value).replace('Z','+00:00'))
    if v.tzinfo is None: raise ValueError('ObservedAt must include timezone')
    return v.astimezone(timezone.utc).isoformat(timespec='microseconds').replace('+00:00','Z')

def gtin(value):
    x=str(value or '').strip()
    if not x.isdigit() or len(x) not in (8,12,13,14):return None
    digits=list(map(int,x));total=sum(v*(3 if i%2==0 else 1) for i,v in enumerate(reversed(digits[:-1])))
    return x.zfill(14) if (10-total%10)%10==digits[-1] else None

def identity_match(a,b):
    """Auto-match only a valid GTIN AND every required variant attribute; names never suffice."""
    fields=('Language','ProductType','PackQuantity','Edition','Region','Variant')
    norm=lambda x:re.sub(r'\s+',' ',str(x or '').strip().casefold())
    if not gtin(a.get('Barcode')) or gtin(a.get('Barcode'))!=gtin(b.get('Barcode')):
        return {'status':'Review','confidence':'Insufficient','reason':'No shared valid GTIN'}
    for key in fields:
        if not norm(a.get(key)) or not norm(b.get(key)):
            return {'status':'Review','confidence':'Insufficient','reason':f'Missing {key}'}
        if norm(a[key])!=norm(b[key]):return {'status':'Separate','confidence':'High','reason':f'Conflicting {key}'}
    return {'status':'Approved','confidence':'High','reason':'Valid GTIN and complete exact variant attributes'}

def evidence(row,as_of,fresh_days=30):
    """Include is preserved as source intent; derived eligibility is independently assessed."""
    result={'EvidenceClass':'Excluded','BenchmarkEligible':0,'ImmediateReference':0,'Reason':''}
    def done(kind,reason,eligible=0,current=0):return {**result,'EvidenceClass':kind,'Reason':reason,'BenchmarkEligible':eligible,'ImmediateReference':current}
    if row.get('Include')!='Yes':return done('Excluded','Source Include is not Yes')
    if row.get('Match')!='Exact':return done('Similar / unverified match','Exact product match is absent')
    if row.get('UKComparable')!='Yes':return done('Excluded','UK/unit comparison is not confirmed')
    try:
        price=number(row.get('PriceIncVAT',row.get('Price')))
        checked=date.fromisoformat(str(row.get('CheckedDate',''))[:10]);age=(date.fromisoformat(as_of)-checked).days
    except (ValueError,TypeError):return done('Unverified','Missing/invalid price or date')
    if price is None or price<=0 or age<0:return done('Excluded','Non-positive price or future observation')
    if not str(row.get('URL','')).startswith(('https://','http://')):return done('Unverified','Missing source URL')
    stock=str(row.get('Availability','')).lower()
    note=str(row.get('Evidence','')).lower()
    # This exact phrase in the original audit states the absence of a variant conflict.
    note=note.replace('no conflicting variant identified','')
    if 'conflict' in stock or 'conflict' in note:return done('Conflicting evidence','Availability/source conflict requires review')
    if 'restricted' in stock:return done('Restricted reference','Terms are not generally comparable')
    if age>fresh_days:return done('Stale indicative','Older than freshness limit; never immediate evidence',1)
    if 'historical' in stock:return done('Historical indicative','Not revalidated',1)
    if 'sold out' in stock or 'preorder' in stock or 'backorder' in stock:
        return done('Out-of-stock / preorder reference','Price reference only',1)
    if stock=='in stock':return done('Current recorded in-stock','Exact dated listing records stock; not live-rechecked',1,1)
    return done('Unverified availability','Price is indicative; stock unconfirmed',1)

def benchmark(rows):
    valid=[x for x in rows if x.get('BenchmarkEligible')]
    if not valid:return None
    return min(valid,key=lambda x:(-int(x['ImmediateReference']),number(x.get('PriceIncVAT',x.get('Price'))),str(x.get('ObservationKey',x.get('SourceID','')))))

def evaluate(offer,qty,terms=None,retail=None,demand=None,as_of='2026-10-15'):
    terms=terms or {};issues=[]
    q=number(qty)
    if q is None or q<=0 or q!=q.to_integral_value():raise ValueError('Quantity must be a positive integer')
    get=lambda key:number(offer.get(key))
    base=get('BaseCostExVAT');bulk=get('BulkCostExVAT');threshold=get('BulkThreshold');moq=get('MOQ');multiple=get('OrderMultiple');stock=get('SupplierStock')
    if base is None or base<=0:issues.append('Invalid base cost')
    if moq is None or moq<=0 or moq!=moq.to_integral_value():issues.append('Invalid or unknown MOQ')
    if multiple is None or multiple<=0 or multiple!=multiple.to_integral_value():issues.append('Invalid or unknown order multiple')
    if moq and q<moq:issues.append('Below MOQ')
    if multiple and multiple>0 and q%multiple:issues.append('Not an order multiple')
    if bulk is not None and (bulk<=0 or threshold is None or threshold<=0 or threshold!=threshold.to_integral_value()):issues.append('Invalid bulk tier')
    unit=bulk if bulk is not None and threshold and q>=threshold else base
    if stock is None:issues.append('Unknown supplier stock')
    elif stock<0 or stock!=stock.to_integral_value():issues.append('Invalid supplier stock')
    elif stock<q:issues.append('Insufficient supplier stock')
    if offer.get('Availability')!='In stock':issues.append('Availability unconfirmed')
    if offer.get('Currency')!='GBP':issues.append('Unsupported or unknown currency')
    if offer.get('IdentityApproved') is not True:issues.append('Identity review required')
    try:
        age=(date.fromisoformat(as_of)-date.fromisoformat(str(offer.get('SnapshotDate',offer.get('CostDate','')))[:10])).days
        if not 0<=age<=int(terms.get('FreshDays',30)):issues.append('Stale or future supplier cost')
    except (ValueError,TypeError):issues.append('Unknown cost date')
    if terms.get('Confirmed') is not True:issues.append('Supplier terms unconfirmed')
    if terms.get('Restrictions'):issues.append('Supplier restriction: '+str(terms['Restrictions']))
    vat=number(terms.get('VATRate'));shipping=number(terms.get('ShippingExVAT'));minimum=number(terms.get('MinimumSpendExVAT'));extras=number(terms.get('OtherChargesExVAT'))
    for k,v in [('VAT rate',vat),('shipping',shipping),('minimum spend',minimum),('other charges',extras)]:
        if v is None or v<0:issues.append('Unknown or invalid '+k)
    if vat is not None and vat>1:issues.append('Invalid VAT rate')
    if terms.get('InputVATRecoverable') is not True:issues.append('VAT recovery not confirmed; comparison unsupported')
    goods=unit*q if unit is not None and unit>0 else None
    free=number(terms.get('FreeShippingThresholdExVAT'))
    if free is not None and free<0:issues.append('Invalid free shipping threshold')
    if goods is not None and free is not None and free>=0 and goods>=free:shipping=D(0)
    if goods is not None and minimum is not None and goods<minimum:issues.append('Below supplier minimum spend')
    landed=goods+shipping+extras if goods is not None and shipping is not None and shipping>=0 and extras is not None and extras>=0 else None
    net=number(retail.get('PriceIncVAT'))/(1+vat) if retail and vat is not None and 0<=vat<=1 else None
    margin=(net-landed/q)/net if net and landed is not None else None
    markup=(net-landed/q)/(landed/q) if net and landed is not None and landed>0 else None
    fee=number(terms.get('FeeRate'));contribution=net-landed/q-number(retail['PriceIncVAT'])*fee if net and landed is not None and fee is not None and fee>=0 else None
    ready_issues=[]
    if not retail or not retail.get('ImmediateReference'):ready_issues.append('Current retail evidence unavailable')
    if fee is None or not 0<=fee<=1:ready_issues.append('Payment fee unknown')
    monthly=number((demand or {}).get('MonthlyDemand'));onhand=number((demand or {}).get('OnHand'));cover=None
    if not demand or demand.get('Verified') is not True or monthly is None or monthly<=0 or onhand is None or onhand<0:ready_issues.append('Reliable demand/on-hand data unavailable')
    else:cover=(onhand+q)/monthly
    maxcover=number(terms.get('MaxCoverMonths'));target=number(terms.get('TargetGM'))
    if maxcover is None:ready_issues.append('Stock cover limit unknown')
    elif cover is not None and cover>maxcover:ready_issues.append('Excess stock exposure')
    if target is None or not 0<=target<1 or margin is None or margin<target:ready_issues.append('Target margin not established')
    if contribution is None or contribution<=0:ready_issues.append('Positive contribution not established')
    target_retail=(landed/q)/(1-target)*(1+vat) if landed is not None and target is not None and 0<=target<1 and vat is not None and 0<=vat<=1 else None
    return {'SelectedRetailIncVAT':number(retail.get('PriceIncVAT')) if retail else None,'TargetRetailIncVAT':target_retail,'UnitGrossProfitExVAT':net-landed/q if net is not None and landed is not None else None,'ScenarioQty':int(q),'UnitCostExVAT':unit,'MerchandiseExVAT':goods,'ShippingExVAT':shipping,'OrderLandedExVAT':landed,'LandedUnitExVAT':landed/q if landed is not None else None,'EstimatedCashOutlayGBP':landed*(1+vat) if landed is not None and vat is not None and 0<=vat<=1 else None,'GrossMarginPct':margin,'MarkupPct':markup,'UnitContribution':contribution,'StockCoverMonths':cover,'CostEligible':int(not issues),'Blockers':'; '.join(issues),'ReviewReasons':'; '.join(ready_issues),'PurchasingReadiness':'Review-ready — human decision' if not issues and not ready_issues else 'Review required'}

def basket(lines,terms,as_of):
    """One-supplier basket: spend test and shipping once, proportionate landed cost allocation."""
    if not lines:raise ValueError('Empty basket')
    if len({o['SupplierKey'] for o,q in lines})!=1:raise ValueError('A basket must have one supplier')
    if len({o['OfferKey'] for o,q in lines})!=len(lines):raise ValueError('Combine duplicate offer lines first')
    line_terms={**terms,'MinimumSpendExVAT':0,'ShippingExVAT':0,'OtherChargesExVAT':0}
    evaluations=[evaluate(o,q,line_terms,as_of=as_of) for o,q in lines]
    goods=sum((x['MerchandiseExVAT'] or D(0) for x in evaluations),D(0));ship=number(terms.get('ShippingExVAT'));extra=number(terms.get('OtherChargesExVAT'));minimum=number(terms.get('MinimumSpendExVAT'));vat=number(terms.get('VATRate'));free=number(terms.get('FreeShippingThresholdExVAT'))
    if free is not None and free<0:issues_free=True
    else:issues_free=False
    if free is not None and free>=0 and goods>=free:ship=D(0)
    issues=[x['Blockers'] for x in evaluations if x['Blockers']]
    if issues_free:issues.append('Invalid free shipping threshold')
    if minimum is None or minimum<0 or goods<minimum:issues.append('Supplier minimum spend not met/unknown')
    if ship is None or ship<0 or extra is None or extra<0:issues.append('Shipping/charges unknown or invalid')
    landed=goods+ship+extra if ship is not None and ship>=0 and extra is not None and extra>=0 else None
    for result in evaluations:
        result['AllocatedChargesExVAT']=(ship+extra)*result['MerchandiseExVAT']/goods if landed is not None and goods>0 and result['MerchandiseExVAT'] is not None else None
    return {'MerchandiseExVAT':goods,'ShippingExVAT':ship,'OrderLandedExVAT':landed,'EstimatedCashOutlayGBP':landed*(1+vat) if landed is not None and vat is not None and 0<=vat<=1 else None,'CostEligible':int(not issues),'Blockers':'; '.join(issues),'PurchasingReadiness':'Review required — basket does not establish demand or retail viability','Lines':evaluations}
