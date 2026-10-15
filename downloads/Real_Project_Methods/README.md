# Real project — public methods edition

This is source evidence from the actual 240-product procurement project, not the commercial dataset. The private workbook, CSV exports, SQLite database, supplier prices, URLs and internal notes are deliberately excluded. The separate Procurement_Analytics package is runnable with fictional data.

## Verified scope
The workbook snapshot is dated 14 October 2026. A new pipeline run on 15 October confirmed 240 product records, 395 retail-price observations, 222 selected exact benchmarks and 119 in-stock benchmarks. The other 103 selected prices are reference-only; 18 products lack a benchmark. These are project coverage figures, not realised financial outcomes. No fresh retailer research was performed in this review.

## Architecture
Products and Price Sources feed the workbook Buying Review. Controls contain assumptions. Checks and Audit Log preserve reviewability. The Python pipeline reads saved XLSX values/caches, builds typed Products, Prices, Decisions and Settings tables, executes independent SQL views, reconciles results and exports CSV for reporting. It does not calculate Excel formulas or collect live web data.

## Execution and privacy
The original pipeline was executed privately with the retained workbook: 15 pipeline checks passed. The six analysis queries executed. The public source files are retained to show the real extraction/schema/reconciliation implementation. They require the private workbook and therefore are not a standalone public reproduction. To reproduce without private data, use ../Procurement_Analytics and run its run_pipeline.py followed by compare_suppliers.py.

Original private command: python run_pipeline.py /path/to/recalculated_workbook.xlsx
Never commit that workbook or the resulting database/CSV exports to the public repository.

## Reporting model
Products[SKU] filters Decisions, Prices and SQLMetrics (single direction). Retailers filters Prices; Dates filters Prices[CheckedDate]. Settings and TargetMargin remain disconnected. PQ files type identifiers as text, replace blanks with nulls, and parse dates/numbers using en-GB. The joins are in SQL and proposed model relationships; no unsupported claim of Power Query merges is made.

The original DAX covers weighted order margin, contribution, coverage and target-margin scenarios. Power Query and DAX have not been executed in Desktop. No PBIX, cloud refresh, gateway or deployed report is claimed. For a runnable public reporting fixture use the separate synthetic package and its Desktop build guide.

## Important differences from the demonstration
The original model keeps exact non-future benchmark references and separately flags freshness for review. The small demonstration excludes observations older than 30 days before choosing its benchmark. Do not interpret identical-looking fields as identical filtering rules. The original supplier snapshot evaluates one catalogue against retail evidence; multi-supplier comparison is a separate fictional six-offer extension, not evidence of a full multi-supplier commercial dataset.

The original workbook includes six tables, a chart, conditional formatting and validation. Formula lookups use INDEX/MATCH and aggregate/conditional functions. No PivotTable is present in this workbook; broader Excel experience should not be confused with features in this artifact. Demand is estimated, not transaction-history forecasting. The existing model has stock-cover analysis; the browser reorder illustration is an additional synthetic scenario, not a deployed stock-replenishment process.
