# Guramrit Grewal — Commercial and Procurement Portfolio

A public case study connecting retail purchasing questions with Excel modelling, SQL analysis and reproducible data validation.

**Website:** https://g-grewal-98.github.io/

## Explore

- [Interactive decision model](https://g-grewal-98.github.io/#demo): filter categories, change target margin, inspect individual calculations.
- [Public CV](downloads/Guramrit_Grewal_CV_Public.pdf): contact details omitted from the public copy.
- [Excel model](downloads/Procurement_Analytics/Procurement_Demo.xlsx): editable fictional inputs and calculations.
- [Complete technical package](downloads/Procurement_Analytics.zip).
- [Technical documentation](downloads/Procurement_Analytics/README.md).

## Scope and authenticity

All published product names, prices, demand estimates and supplier offers are synthetic. No private employer workbook, customer information or wholesale agreements are included. This is a portfolio demonstration, not a production purchasing system or a claim of realised savings.

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
