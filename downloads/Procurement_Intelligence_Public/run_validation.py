"""Run new regression suite plus preserved legacy SQL tests; write structured evidence."""
import unittest,sqlite3,json,io,importlib.util,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
stream=io.StringIO();suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_*.py')
r=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
legacy={}
if (ROOT/'procurement.sqlite').exists():
    db=sqlite3.connect(':memory:');src=sqlite3.connect('file:'+str(ROOT/'procurement.sqlite')+'?mode=ro',uri=True);src.backup(db);src.close()
    spec=importlib.util.spec_from_file_location('legacy_rules',ROOT/'tests/test_rules.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);legacy=m.run_tests(db);db.close()
passed=r.wasSuccessful() and all(value is True for value in legacy.values())
report={'status':'PASS' if passed else 'FAIL','new_tests_run':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'legacy_checks':legacy,'legacy_checks_passed':sum(value is True for value in legacy.values()),'details':stream.getvalue(),'limitations':['Private Power BI acceptance is separate; this public M/DAX fixture is not compiled as a PBIX','No authorised live supplier endpoint tested']}
(ROOT/'audit').mkdir(exist_ok=True);(ROOT/'audit/test_results.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='details'},indent=2));raise SystemExit(0 if passed else 1)
