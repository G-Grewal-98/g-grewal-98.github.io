"""Evaluate an explicit single-supplier basket JSON; never places an order."""
import argparse,json
from engine.rules import basket
p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('--output',required=True);a=p.parse_args()
with open(a.input,encoding='utf-8') as f:cfg=json.load(f)
r=basket([(x['offer'],x['quantity']) for x in cfg['lines']],cfg['terms'],cfg['as_of'])
with open(a.output,'w',encoding='utf-8') as f:json.dump(r,f,indent=2,default=str)
print('Basket saved; '+r['PurchasingReadiness'])
