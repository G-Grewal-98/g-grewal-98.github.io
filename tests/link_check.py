from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlparse,unquote
root=Path(__file__).resolve().parents[1]
pages=[root/'index.html',root/'intelligence-case-study.html',root/'power-bi-report.html',root/'downloads/Procurement_Intelligence_Public/portfolio/index.html']
issues=[];total=0
for page in pages:
 s=BeautifulSoup(page.read_text(),'html.parser')
 ids={n.get('id') for n in s.find_all(attrs={'id':True})}
 for n in s.find_all(['a','script','link']):
  url=n.get('href') or n.get('src')
  if not url: continue
  if url.startswith(('mailto:','tel:','javascript:')):continue
  p=urlparse(url)
  if p.scheme or p.netloc:continue
  total+=1
  if p.path:
   dest=(page.parent/unquote(p.path)).resolve()
   if not dest.is_relative_to(root) or not dest.exists():issues.append((page.relative_to(root).as_posix(),url,'missing file'))
   elif p.fragment and dest.suffix=='.html':
    ids_dest={t.get('id') for t in BeautifulSoup(dest.read_text(),'html.parser').find_all(attrs={'id':True})}
    if p.fragment not in ids_dest:issues.append((str(page),url,'missing target id'))
  elif p.fragment not in ids:issues.append((str(page),url,'missing fragment'))
print('Local references:',total,'problems:',len(issues))
for it in issues:print(it)
if issues:raise SystemExit(2)
