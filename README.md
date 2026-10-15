# Guramrit Grewal | Commercial & Data Analytics Portfolio

A public case study connecting retail purchasing questions with Excel modelling, SQL analysis and reproducible data validation.

**Website:** https://g-grewal-98.github.io/

## Explore

- [Interactive decision model](https://g-grewal-98.github.io/#demo): filter categories, change target margin, inspect individual calculations.
- [Public CV](downloads/Guramrit_Grewal_CV_Public.pdf): contact details omitted from the public copy.
- [Excel model](downloads/Procurement_Analytics/Procurement_Demo.xlsx): editable fictional inputs and calculations.
- [Complete technical package](downloads/Procurement_Analytics.zip).
- [Technical documentation](downloads/Procurement_Analytics/README.md).

## Scope and authenticity

Published project scope and source methods describe the real 240-product workbook. All public row-level product names, prices, demand estimates and supplier offers are synthetic. No private employer workbook, customer information or wholesale agreements are included. The featured real case study and supporting synthetic demonstration are separate. Neither claims a production purchasing system or realised savings.

The primary sample has 12 products and 24 retail observations. The supplier comparison extension contains six offers across two fictional suppliers for three products. These datasets have distinct purposes; alternate supplier offers do not overwrite the primary Excel model.

## Run locally

Python 3.10+ and SQLite 3.25+; Python standard library only.

```sh
cd downloads/Procurement_Analytics
python run_pipeline.py
python compare_suppliers.py
cd ../..
python -m http.server 8000
```

Visit `http://localhost:8000`. Opening `index.html` directly via `file://` will not reliably load JSON or ES modules.

## Architecture

CSV source fixtures feed typed SQLite tables through Python. SQL views select eligible retail benchmarks and calculate purchasing economics. The pipeline exports JSON and CSV. Browser JavaScript applies the same recommendation rules to adjustable target margins. The separate Excel workbook models the primary demonstration. Power Query and DAX files document the reporting implementation.

| Folder or file | Purpose |
| --- | --- |
| `index.html`, `styles.css` | Accessible static portfolio layout |
| `app.js`, `logic.mjs` | Scenario controls and decision rules |
| `downloads/Procurement_Analytics/data/` | Fictional input data and calculated exports |
| `downloads/Procurement_Analytics/sql/` | Model, analysis and supplier comparison queries |
| `downloads/Procurement_Analytics/powerbi/` | Power Query, DAX and report specification |
| `downloads/Procurement_Analytics/run_pipeline.py` | Rebuild primary model and 33 checks |
| `downloads/Procurement_Analytics/compare_suppliers.py` | Rebuild supplier comparison and five checks |

## Verification boundary

Python and SQL are executed. Excel formulas were recalculated and compared with SQL in the generation environment, including an input-change test. Power BI Desktop and native Excel have not been run. The Power BI material is an implementation pack, not a completed or deployed PBIX report. The browser demonstration is a working interactive equivalent, not an embedded Power BI dashboard.

No live price scraping, automated supplier refresh or sales forecasting is claimed. Stock cover uses fictional monthly-demand assumptions.

## Hosting

Static GitHub Pages, `main` branch, repository root. No build step, paid hosting, tracking scripts or private credentials are required.

## Featured real project
[Public methods edition](downloads/Real_Project_Methods/README.md) contains original Python, SQL, Power Query and DAX, formula excerpts and an aggregate structure/validation report. The original workbook is private and is not included. The source pipeline requires it; the synthetic package remains independently runnable. Read the methods README for the important freshness-rule and schema differences.

Verified real snapshot: 240 products, 395 retail observations, 222 exact benchmarks, 119 in-stock selected benchmarks. Snapshot date 14 October; rerun 15 October 2026. 15 private pipeline checks passed; no new live price collection. Public scope describes analytical work, not financial results.

## Preserve and recover
The previous release is retained in branch `backup-before-real-case-study-2026-10-15`, commit `a3323db920cc7f948399c6fe99b618c7626523fc`. Git history preserves publication changes.

## Browser and calculation tests
Run `node tests/scenarios.test.mjs` from the repository root. It checks default browser/SQL parity for all 12 products, margin and quantity scenarios, nulls and zero-demand behavior. Run both Python scripts as above for the 33 primary checks and five supplier checks. Excel desktop and Power BI Desktop validation remain outstanding.
