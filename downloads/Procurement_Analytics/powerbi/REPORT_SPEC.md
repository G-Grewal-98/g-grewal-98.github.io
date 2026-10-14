# Power BI model specification

Implementation status: Power Query and DAX files are supplied. They have not been executed in Power BI Desktop, and no PBIX report or cloud deployment is included.

## Import and relationships
Create a text parameter named BaseFolder pointing to the extracted Procurement_Analytics folder, with a trailing slash. Import each `.pq` query under the matching name. Create the following single-direction, one-to-many relationships, with Products filtering the fact tables:

| Dimension | Fact |
|---|---|
| Products[SKU] | Metrics[SKU] |
| Products[SKU] | Prices[SKU] |

Keep Settings and TargetMargin disconnected. Do not connect Prices to Metrics: observation filters must not silently change the saved purchasing snapshot. Create TargetMargin using calculated_tables.dax, then create each measure in measures.dax in dependency order.

## Report views
**Overview:** product count, benchmark coverage, trial/bulk candidates and a category matrix. Use Products[Category] as the slicer.

**Purchasing review:** product, base and bulk margins, bulk cash, cover, recommendation and scenario target. The scenario measure tests price feasibility only; it does not change saved recommendations.

**Evidence:** observation table with dates, retailer labels, availability and match type. Keep evidence-level filters on this page.

Format currency as GBP, margins as percentages and IDs as text. Do not average SKU margins and label them as an order margin. The sample has no transaction history; do not present observation dates as sales trends.

## Acceptance
Compare unfiltered totals with validation.json and data/Metrics.csv. Confirm category slicers filter all product measures, missing benchmarks remain blank, P005 requires price research, P006 requires availability review, P004 requires stock-exposure review and P002 is a bulk candidate at the default target. Confirm TargetMargin changes the scenario measure while snapshot recommendations stay fixed. Record Desktop results before claiming a completed report.
