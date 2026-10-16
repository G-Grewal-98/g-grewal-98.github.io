# Procurement intelligence — public synthetic demo

Every commercial row in this archive is fictional. No private workbook, company catalogue, original PBIX, customer records or actual supplier quotations are included. This fixture exercises the same new engine delivered with the private continuation; it does not replace the original project.

Python 3.10+. CSV/TSV runtime paths use the standard library; XLSX imports and the complete test suite also require openpyxl (see requirements-xlsx.txt). From this folder:

```sh
python run_validation.py
python refresh_v2.py --as-of 2026-10-15 --terms config/demo_terms.json --demand config/demo_demand.json
python refresh_v2.py --as-of 2026-10-15 --import-file config/demo_import.csv --adapter config/demo_adapter.json --terms config/demo_terms.json --demand config/demo_demand.json
python basket_cli.py config/demo_basket.json --output audit/demo_basket_result.json
```

Open `portfolio/index.html` locally; no server, account or network calls are needed. Its embedded data is a fixed snapshot, so rerunning the pipeline does not automatically rebuild the HTML. For fresh figures read the current generation CSVs. The demonstration includes four offers, two products, two fictional suppliers and the £24.95→£22.95 history test. Engine fixtures manually approve fictional identities; this is not real-world identity verification.

`CASE_STUDY.md` explains the implementation and limits. `powerbi/continuation/` contains standalone M/DAX artifacts, not a compiled report. The schedule launcher reads local files only; no supplier feed or schedule has been installed. CSV adapters require explicit export authorisation. Templates deliberately contain unknown commercial terms.

No public deployment was performed in this update. Review the safe package before publishing. The private original project must never be substituted for this demo in a public repository.


## V6 continuation (16 October 2026)

CSV and TSV runtime import paths use the Python standard library. For XLSX imports and the complete 56-test suite, first run `python -m pip install -r requirements-xlsx.txt` in your chosen environment. Use an isolated environment and retain its package versions. `python run_validation.py` discovers all test files and fails if a regression or available legacy SQL check fails. Supplier adapters require explicit authorisation and exact column mappings; no live supplier endpoint is configured.
