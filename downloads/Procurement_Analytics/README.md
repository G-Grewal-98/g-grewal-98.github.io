# Procurement analytics

A public demonstration of supplier-price evaluation, margin modelling and bulk-purchase exposure, presented by Guramrit Grewal.

## Business question
When does a wholesale offer support a commercially viable selling price, and when does a bulk discount create excessive stock exposure?

This case study is based on the structure of a retail purchasing project. All 12 products, 24 observations, supplier costs and demand estimates in this public edition are fictional. The real business catalogue, supplier identities, customer information, personal notes and account details are excluded. No achieved savings or revenue improvements are claimed.

## Deliverables
| Component | Evidence |
|---|---|
| Excel | Editable assumptions and product inputs, linked formulas, VAT-aware margins, bulk quantities and stock-cover checks |
| SQLite | Primary and foreign keys, CTEs, joins, ranked benchmark selection and exception analysis |
| Python | Standard-library CSV ingestion, database generation, typed exports and automated behavioural checks |
| Power Query | Typed imports for the supplied CSV tables |
| DAX | Filter-context measures and a disconnected margin scenario |
| Web | Interactive scenario and filtered purchasing review |

## Reproduce
Requires Python 3.10+ and SQLite 3.25+. No external Python packages.

```sh
python run_pipeline.py
```

The command reads `data/Products.csv` and `data/Prices.csv`, creates a fresh SQLite database, executes `sql/model.sql`, checks results and writes `data/Metrics.csv`, `data/Settings.csv`, `demo.json` and `validation.json`. Only use exports from a successful run. The supplied checks use the fixture products as regression cases; update their expected results when deliberately changing the fixture.

`sql/analysis.sql` contains category summaries, within-category rankings, stock-exposure analysis, observation history and exception queries. Open `procurement.sqlite` with a SQLite client to run these queries.

## Model specification
1. Retain exact observations dated on or before the snapshot and no older than 30 days. Prefer in-stock listings, then the lowest price; break ties by date and source ID.
2. Cap the illustrative shelf price at benchmark × (1 + premium), rounded down to £0.05. VAT-exclusive revenue is shelf price ÷ (1 + VAT).
3. Gross margin = (VAT-exclusive revenue − purchase cost) ÷ VAT-exclusive revenue. Contribution also deducts payment fees charged on the shelf price.
4. Round the bulk threshold up to the next supplier order multiple. Bulk cash includes VAT. Cover = (existing stock + bulk quantity) ÷ estimated monthly demand.
5. Assess price feasibility separately from availability and stock exposure. Missing benchmarks remain missing; sold-out observations require review.

The demo assumes recoverable input VAT, excludes freight/returns/overheads and uses illustrative demand. It does not recommend real purchases. Actual cash and profit depend on terms, sales, costs and tax treatment.

## Excel and refresh boundaries
`Procurement_Demo.xlsx` is a standalone scenario workbook. The Summary assumptions and Inputs values drive the Model formulas. Benchmark cells are the baseline SQL selections, supplied as inputs. Change the workbook to inspect Excel scenarios; those changes do not update the CSV inputs or database. To refresh SQL and Power BI, edit the CSV inputs, run the pipeline, then refresh Desktop. A changed CSV dataset requires updating the workbook inputs separately.

The workbook has been recalculated and compared with the SQL outputs in the generation environment. Native Excel desktop execution has not been performed. Power Query and DAX are implementation files, not a completed or deployed PBIX report.

## Data dictionary
`Products`: one row per SKU; costs exclude VAT; quantities are individual units; MonthlyDemand is an assumption.
`Prices`: one fictional observation per SourceID; prices include VAT; MatchType is Exact or Similar.
`Settings`: one snapshot of scenario assumptions.
`Metrics`: one row per product, including unpriced products, with selected benchmark, economics and review status.

## Validation
The included validation report records executed checks. These cover key integrity, independent Python/SQL calculations, order-multiple rounding, unavailable and stale evidence, future dates, similar products, duplicate IDs, missing margins and stock-exposure cases. No live retailer-price validation is implied.

## Supplier comparison extension

Run `python compare_suppliers.py` after `python run_pipeline.py`. This creates `Suppliers` and `Offers` tables and writes `supplier_comparison.json`. There are six fictional offers across two suppliers and three products. The fixed request is 24 units per product. SQL joins product and supplier keys, filters out larger minimum quantities and uses `DENSE_RANK` to retain tied lowest prices. Five additional checks verify record count, keys, quantity eligibility, preferred offers and basket cost.

The comparison considers goods cost excluding VAT only. It excludes freight, credit terms, lead times and supplier reliability because no such evidence is supplied. These offers are a separate teaching fixture and do not replace the primary workbook's purchasing inputs. They are not real supplier quotes or achieved savings.

## Browser scenario extensions (15 October 2026)
The website adds adjustable shelf premium (0–20%), demand scaling (0–200%) and supplier requirement (12/24/72/144 units). Defaults reconcile to the original demo outputs. These controls do not edit the downloadable baseline workbook or CSV inputs. Zero demand triggers review and unknown cover. Reorder-point text assumes 14 days lead time, 30 days per month and zero safety stock; it is not an operational replenishment model. Actual lead times are unavailable.

`scenarios.mjs` and `logic.mjs` in the repository implement these extensions. `supplier_offers.json` retains all six fictional offers, including the 72-unit minimum excluded from the baseline SQL result. The unchanged SQL supplier query remains the 24-unit reference example.
