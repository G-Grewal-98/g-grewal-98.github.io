# Procurement intelligence: making supplier comparisons reviewable

## Problem and contribution

Wholesale price alone is a poor purchasing signal. Product variants, order multiples, delivery, uncertain stock and weak retail evidence can make apparently cheap offers unsuitable. This continuation extends an existing Excel/Python/SQL/Power BI procurement project with conservative validation and a reproducible comparison pipeline. It retains the original architecture and data rather than rebuilding the original report.

## Implementation

- Python standard-library CSV adapters map authorised exports to a stable listing registry.
- Supplier listings and canonical products are separate. Valid GTIN and complete matching variant attributes can support automatic matching; otherwise an auditable manual decision is needed.
- Retail observations retain their original inclusion flag alongside a derived evidence class. A price reference never proves stock availability.
- Decimal calculations evaluate 1, 12, 24 and 36 units with MOQ, ordering multiples, one bulk tier, delivery, minimum spend, VAT and demand checks. Single-supplier baskets apply shipping once across compatible order lines.
- SQLite foreign keys and unique keys support typed analytical exports. Rankings compare only eligible compatible products at the same quantity. A cost gap is not realised savings.
- Price history retains changed observations while unchanged imports update freshness without duplicate economic events. Variant changes withdraw identity approval.
- Complete generations are validated before their current pointer changes. Failed imports retain the previous successful output.

## Evidence to explore

Open `portfolio/index.html` to filter fictional quantity scenarios. Run `run_validation.py` for automated regression evidence; inspect `audit/test_results.json`. Run the basket CLI for a mixed-product example. Inspect `engine/rules.py`, `engine/registry.py` and the generation's `schema.sql`. Power Query and DAX are provided in `powerbi/continuation/`.

The synthetic history changes one listing from £24.95 to £22.95 and preserves both observations. This validates movement calculations; it does not show company savings. Test coverage includes missing SKUs/barcodes, language/pack/edition differences, supplier-scoped collisions, evidence conflicts, price changes, order constraints and refresh recovery.

## Honest limits

No live wholesaler API or authorised commercial feed has been connected. No ordering system is deployed. Uniform recoverable VAT and GBP are the supported calculation basis; mixed VAT and multiple bulk tiers need further work. Power BI integration files still require local Desktop application and acceptance testing. The original native report was preserved, not edited by this continuation. The HTML is a precomputed interactive equivalent, not an embedded Power BI dashboard.

## CV wording to use after reviewing and understanding the implementation

- Developed a procurement analytics project linking spreadsheet outputs, Python validation and SQLite analysis to compare supplier costs and flag purchasing constraints.
- Added product-identity reviews, retail-evidence quality checks and supplier price history, supported by automated regression tests and reproducible synthetic examples.
- Prepared Power Query and DAX reporting artifacts for quantity-specific supplier comparisons, with clear separation of verified inputs, test data and unresolved review items.

These statements describe project work, not a formal job title, implemented live integration or measured commercial gain. Only retain claims you can explain and demonstrate independently; the continuation includes AI-assisted implementation.
