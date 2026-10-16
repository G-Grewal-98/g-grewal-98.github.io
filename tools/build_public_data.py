"""Regenerate public-data.js from the site's fictional, versioned JSON fixtures."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
data={
    'demo':json.loads((ROOT/'downloads/Procurement_Analytics/demo.json').read_text()),
    'offers':json.loads((ROOT/'downloads/Procurement_Analytics/supplier_offers.json').read_text()),
}
text='// Public fictional data only. Regenerated from downloads/Procurement_Analytics JSON fixtures.\n'
text+='window.PORTFOLIO_FIXTURES = '+json.dumps(data,ensure_ascii=True,separators=(',',':')).replace('<','\\u003c')+';\n'
(ROOT/'public-data.js').write_text(text)
print('Regenerated public-data.js (fictional data only)')
