"""Schedule-ready entry point. Config stores local paths, never account credentials."""
import argparse,json,subprocess,sys,datetime
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('config',type=Path);a=p.parse_args();c=json.loads(a.config.read_text())
root=Path(__file__).resolve().parent
cmd=[sys.executable,str(root/'refresh_v2.py'),'--root',str(root),'--as-of',datetime.date.today().isoformat()]
for key,flag in [('import_file','--import-file'),('adapter','--adapter'),('terms','--terms'),('demand','--demand')]:
    if c.get(key):cmd += [flag,str((a.config.parent/c[key]).resolve())]
log=root/'audit/scheduled_refresh.log';log.parent.mkdir(exist_ok=True)
with log.open('a',encoding='utf-8') as f:
    f.write('\nRun '+datetime.datetime.now(datetime.timezone.utc).isoformat()+'\n');f.flush();r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
raise SystemExit(r.returncode)
