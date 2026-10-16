"""Extend the supplied listing registry without replacing its keys or old price events."""
import sqlite3,json,hashlib,uuid,csv
from urllib.parse import urlsplit,urlunsplit
from .rules import timestamp,number,identity_match

def urlkey(value):
    if not value:return ''
    u=urlsplit(value)
    if u.scheme not in ('https','http') or not u.netloc:raise ValueError('Invalid listing URL')
    if u.username or u.password:raise ValueError('Credentials must not be stored in URLs')
    # Preserve query parameters: they may identify product variants.
    return urlunsplit((u.scheme.lower(),u.netloc.lower(),u.path.rstrip('/') or '/',u.query,''))

def connect(path):
    db=sqlite3.connect(path);db.row_factory=sqlite3.Row;db.execute('PRAGMA foreign_keys=ON')
    db.executescript('''CREATE TABLE IF NOT EXISTS listings (
      ListingID TEXT PRIMARY KEY,OfferKey TEXT UNIQUE NOT NULL,SupplierID TEXT NOT NULL,SupplierName TEXT NOT NULL,
      SupplierSKU TEXT,ExternalListingID TEXT,ListingURL TEXT,Product TEXT,Category TEXT,Barcode TEXT,Language TEXT,
      ProductType TEXT,PackQuantity TEXT,CanonicalProductKey TEXT NOT NULL,MatchStatus TEXT NOT NULL,IdentityBasis TEXT NOT NULL,
      ReviewReason TEXT NOT NULL DEFAULT '',CurrentPayload TEXT NOT NULL,FirstSeenAt TEXT NOT NULL,LastSeenAt TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS aliases(SupplierID TEXT NOT NULL,AliasType TEXT NOT NULL,AliasValue TEXT NOT NULL,ListingID TEXT NOT NULL REFERENCES listings(ListingID),PRIMARY KEY(SupplierID,AliasType,AliasValue));
      CREATE TABLE IF NOT EXISTS price_events(EventKey TEXT PRIMARY KEY,ListingID TEXT NOT NULL REFERENCES listings(ListingID),ObservedAt TEXT NOT NULL,Payload TEXT NOT NULL,UNIQUE(ListingID,ObservedAt));
      CREATE TABLE IF NOT EXISTS import_audit(ImportID TEXT PRIMARY KEY,SourceHash TEXT NOT NULL,ImportedAt TEXT NOT NULL,Rows INTEGER NOT NULL);
      CREATE TABLE IF NOT EXISTS identity_audit(AuditID TEXT PRIMARY KEY,ListingID TEXT NOT NULL,OldProductKey TEXT,NewProductKey TEXT,Reason TEXT,ChangedAt TEXT);
    ''');return db

def economic_payload(p):
    fields=('BaseCostExVAT','BulkCostExVAT','BulkThreshold','MOQ','OrderMultiple','SupplierStock','Availability','Currency','Language','ProductType','PackQuantity','Barcode','Edition','Region','Variant')
    out={k:str(p.get(k,'') or '').strip() for k in fields}
    for k in ('BaseCostExVAT','BulkCostExVAT','BulkThreshold','MOQ','OrderMultiple','SupplierStock'):
        n=number(out[k]);out[k]=str(n.normalize()) if n is not None else ''
    return out

def import_rows(db,rows,source_hash,imported_at):
    results=[]
    with db:
        for row in rows:
            p={k:('' if v is None else str(v).strip()) for k,v in row.items()};supplier=p.get('SupplierID')
            if not supplier:raise ValueError('SupplierID is required')
            at=timestamp(p.get('ObservedAt'));p['ObservedAt']=at
            for k in ['BaseCostExVAT','MOQ','OrderMultiple']:
                n=number(p.get(k))
                if n is None or n<=0 or (k!='BaseCostExVAT' and n!=n.to_integral_value()):raise ValueError('Invalid '+k)
            for k in ['BulkCostExVAT','BulkThreshold','SupplierStock','LeadDays','PackQuantity']:
                n=number(p.get(k))
                if n is not None and (n<0 or (k!='BulkCostExVAT' and n!=n.to_integral_value())):raise ValueError('Invalid '+k)
            aliases=[('external',p.get('ExternalListingID','')),('url',urlkey(p.get('ListingURL',''))),('sku',p.get('SupplierSKU',''))];aliases=[a for a in aliases if a[1]]
            if not aliases:
                results.append({'Status':'Quarantined','Reason':'No supplier listing ID, URL or SKU; no product identity invented','SupplierID':supplier});continue
            hits={x[0] for kind,value in aliases for x in db.execute('SELECT ListingID FROM aliases WHERE SupplierID=? AND AliasType=? AND AliasValue=?',(supplier,kind,value))}
            # Supplied registries can predate alias convention: also use original field values.
            for field in ('ExternalListingID','SupplierSKU','ListingURL'):
                if p.get(field):hits.update(x[0] for x in db.execute(f'SELECT ListingID FROM listings WHERE SupplierID=? AND {field}=?',(supplier,p[field])))
            if len(hits)>1:raise ValueError('Conflicting listing aliases; manual identity review required')
            old=db.execute('SELECT * FROM listings WHERE ListingID=?',(next(iter(hits)),)).fetchone() if hits else None
            if old and at<timestamp(old['LastSeenAt']):results.append({'Status':'Older observation skipped','ListingID':old['ListingID']});continue
            listing=old['ListingID'] if old else 'L_'+uuid.uuid4().hex.upper();offer=old['OfferKey'] if old else 'O_'+uuid.uuid4().hex.upper()
            product=old['CanonicalProductKey'] if old else 'P_'+uuid.uuid4().hex.upper();status=old['MatchStatus'] if old else 'Unmatched - review required';reason=old['ReviewReason'] if old else 'No approved canonical match'
            old_payload=json.loads(old['CurrentPayload']) if old else None
            variant_fields=('Barcode','Language','ProductType','PackQuantity','Edition','Region','Variant')
            variant_change=old and any(str(old_payload.get(k,'') or '')!=p.get(k,'') for k in variant_fields)
            if variant_change:
                newproduct='P_'+uuid.uuid4().hex.upper();reason='Listing variant changed; prior canonical approval withdrawn'
                db.execute('INSERT INTO identity_audit VALUES(?,?,?,?,?,?)',(uuid.uuid4().hex,listing,product,newproduct,reason,at));product=newproduct;status='Unmatched - review required'
            if not old:
                matches=[]
                for other in db.execute('SELECT CanonicalProductKey,CurrentPayload FROM listings'):
                    if identity_match(p,json.loads(other['CurrentPayload']))['status']=='Approved':matches.append(other['CanonicalProductKey'])
                if len(set(matches))==1:product=matches[0];status='Auto-verified GTIN + complete variant attributes';reason='Strict GTIN/variant rule'
                elif len(set(matches))>1:reason='Multiple canonical candidates; manual review'
            payload=json.dumps(p,sort_keys=True)
            existing=next((x for x in db.execute('SELECT Payload,ObservedAt FROM price_events WHERE ListingID=?',(listing,)) if timestamp(x['ObservedAt'])==at),None)
            if existing and economic_payload(json.loads(existing[0]))!=economic_payload(p):raise ValueError('Conflicting data at the same observation timestamp')
            changed=not old or economic_payload(old_payload)!=economic_payload(p)
            values=(listing,offer,supplier,p.get('SupplierName',supplier),p.get('SupplierSKU',''),p.get('ExternalListingID',''),p.get('ListingURL',''),p.get('Product',''),p.get('Category',''),p.get('Barcode',''),p.get('Language',''),p.get('ProductType',''),p.get('PackQuantity',''),product,status,aliases[0][0],reason,payload,old['FirstSeenAt'] if old else at,at)
            db.execute('INSERT INTO listings VALUES('+','.join('?'*len(values))+') ON CONFLICT(ListingID) DO UPDATE SET '+','.join(f'{k}=excluded.{k}' for k in ['SupplierName','SupplierSKU','ExternalListingID','ListingURL','Product','Category','Barcode','Language','ProductType','PackQuantity','CanonicalProductKey','MatchStatus','ReviewReason','CurrentPayload','LastSeenAt']),values)
            for kind,value in aliases:db.execute('INSERT OR IGNORE INTO aliases VALUES(?,?,?,?)',(supplier,kind,value,listing))
            if changed and not existing:db.execute('INSERT INTO price_events VALUES(?,?,?,?)',('E_'+uuid.uuid4().hex.upper(),listing,at,payload))
            results.append({'Status':'Changed' if changed else 'Unchanged','ListingID':listing,'OfferKey':offer})
        db.execute('INSERT OR IGNORE INTO import_audit VALUES(?,?,?,?)',(source_hash,source_hash,imported_at,len(rows)))
    return results

def history(db):
    result=[];previous={}
    for r in sorted(db.execute('SELECT e.*,l.OfferKey,l.SupplierID FROM price_events e JOIN listings l USING(ListingID)').fetchall(),key=lambda r:(r['ListingID'],timestamp(r['ObservedAt']),r['EventKey'])):
        p=json.loads(r['Payload']);cost=number(p.get('BaseCostExVAT'));old=previous.get(r['ListingID']);same=old is not None and old['Currency']==p.get('Currency') and all(old.get(k,'')==p.get(k,'') for k in ['Language','ProductType','PackQuantity','Barcode','Edition','Region','Variant'])
        prev=number(old.get('BaseCostExVAT')) if same else None
        result.append({'EventKey':r['EventKey'],'ListingID':r['ListingID'],'OfferKey':r['OfferKey'],'SupplierID':r['SupplierID'],'ObservedAt':r['ObservedAt'],'BaseCostExVAT':cost,'PreviousCostExVAT':prev,'AbsoluteChange':cost-prev if cost is not None and prev is not None else None,'PercentageChange':(cost-prev)/prev if cost is not None and prev is not None and prev!=0 else None,'Currency':p.get('Currency'),'MovementComparable':int(same),'SourceURL':p.get('ListingURL','')})
        previous[r['ListingID']]=p
    return result

def read_adapter(path,config):
    """Explicit authorised CSV/XLSX mapping; never evaluate workbook formulas."""
    if config.get('authorized_export') is not True:raise ValueError('Adapter requires an authorised export declaration')
    from pathlib import Path
    mapping=config.get('columns',{})
    if not mapping:raise ValueError('Adapter columns mapping is required')
    suffix=Path(path).suffix.lower()
    if suffix=='.xlsx':
        try:from openpyxl import load_workbook
        except ImportError as exc:raise RuntimeError('XLSX import requires openpyxl; install requirements-xlsx.txt') from exc
        workbook=load_workbook(path,read_only=True,data_only=False,keep_links=False)
        try:
            sheet=config.get('sheet')
            if sheet is None and len(workbook.sheetnames)!=1:raise ValueError('Select an explicit sheet for a multi-sheet export')
            if sheet is not None and sheet not in workbook.sheetnames:raise ValueError('Configured sheet is missing')
            ws=workbook[sheet] if sheet is not None else workbook[workbook.sheetnames[0]]
            cells=list(ws.iter_rows())
            if not cells:raise ValueError('Empty source')
            headers=[c.value for c in cells[0]]
            values=[]
            for row in cells[1:]:
                if all(c.value is None for c in row):continue
                for dest,src in mapping.items():
                    if src not in headers:continue
                    c=row[headers.index(src)]
                    if c.data_type=='f':raise ValueError('Mapped formulas are not accepted; supply a verified values-only export')
                    if dest in ('SupplierSKU','ExternalListingID','Barcode') and c.value is not None and not isinstance(c.value,str):
                        raise ValueError('Listing identifiers and barcodes must be stored as text to preserve leading zeroes')
                values.append([c.value for c in row])
        finally:workbook.close()
    elif suffix in ('.csv','.tsv'):
        with open(path,encoding=config.get('encoding','utf-8-sig'),newline='') as f:
            reader=csv.reader(f,delimiter=config.get('delimiter','\t' if suffix=='.tsv' else ','))
            headers=next(reader,[]);values=[row for row in reader if any(row)]
    else:raise ValueError('Supported exports are CSV, TSV and XLSX; convert legacy XLS explicitly')
    if not headers or any(not isinstance(h,str) or not h.strip() for h in headers):raise ValueError('Missing or blank source headers')
    if len(headers)!=len(set(headers)):raise ValueError('Duplicate source headers')
    missing=set(mapping.values())-set(headers)
    if missing:raise ValueError('Missing adapter columns: '+','.join(sorted(missing)))
    if any(len(row)!=len(headers) for row in values):raise ValueError('Source row length does not match headers')
    rows=[{**{dst:row[headers.index(src)] for dst,src in mapping.items()},**config.get('constants',{})} for row in values]
    for row in rows:
        if row.get('SupplierID')!=config['supplier_id']:raise ValueError('Supplier scope mismatch')
        row['IsSynthetic']='Yes' if config.get('synthetic') is True else 'No'
    return rows


def apply_reviews(db,reviews,as_of):
    """Explicit analyst decisions; evidence and reviewer required, original events untouched."""
    with db:
        for r in reviews:
            required=('ListingID','ProductKey','Reviewer','Evidence','ReviewedAt','Decision')
            if any(not r.get(k) for k in required):raise ValueError('Incomplete identity review')
            at=timestamp(r['ReviewedAt'])
            if at[:10]>as_of:raise ValueError('Future identity review')
            old=db.execute('SELECT * FROM listings WHERE ListingID=?',(r['ListingID'],)).fetchone()
            if not old:raise ValueError('Unknown listing for identity review')
            if r['Decision'] not in ('Approve','Keep separate'):raise ValueError('Invalid identity decision')
            reason='Manual '+r['Decision']+' by '+r['Reviewer']+': '+r['Evidence']
            if r['Decision']=='Keep separate' and r['ProductKey']!=old['CanonicalProductKey']:raise ValueError('Keep separate must retain current product key')
            state='Approved match - manual evidence review' if r['Decision']=='Approve' else 'Unmatched - review required'
            audit=hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest()
            if db.execute('SELECT 1 FROM identity_audit WHERE AuditID=?',(audit,)).fetchone():continue
            db.execute('INSERT INTO identity_audit VALUES(?,?,?,?,?,?)',(audit,r['ListingID'],old['CanonicalProductKey'],r['ProductKey'],reason,at))
            db.execute('UPDATE listings SET CanonicalProductKey=?,MatchStatus=?,ReviewReason=? WHERE ListingID=?',(r['ProductKey'],state,reason,r['ListingID']))
