# Architecture and maintenance

## Data flow and isolation

Original `data/`, `model_v2/data/`, `procurement.sqlite`, `model_v2/listing_registry.sqlite` and PBIX are read-only inputs. `refresh_v2.py` copies the last successful registry into a staging directory, validates baseline dimensions, imports an optional approved CSV, TSV or XLSX, TSV or XLSX, applies optional documented identity decisions, derives evidence and economics, writes a typed SQLite database and CSVs, then commits one immutable generation and atomically switches `current.json`. Failure records `last_attempt.json` while preserving the prior pointer. Original legacy calculations are preserved as historical outputs, not silently relabelled as the new methodology.

Concurrent refreshes are blocked by an exclusive lock file. Do not delete a lock until you confirm its process is no longer running. There is no network retry because no network integration is installed. A failed local import is corrected and rerun; identical economic observations do not duplicate history. Registry mutations roll back as a batch. Quarantined rows appear in ImportResults; invalid numeric input fails the batch. Copy the previous generation name into a temporary pointer and atomically rename it to current.json for recovery; retain its registry as well as its CSVs. Do not delete the only previous good generation.

## Data dictionary and SQL grains

| Entity | Grain / key | Meaning |
|---|---|---|
| Products | ProductKey | Canonical or separate unverified internal product identity |
| Suppliers | SupplierKey | Supplier identity, not evidence of account access |
| Offers | OfferKey | One supplier listing; product/supplier foreign keys |
| Evaluation | OfferKey + ScenarioQty | Independent single-offer order at 1,12,24,36 units |
| Rankings view | Eligible evaluation row | Dense cost rank within canonical product and quantity; ties share rank |
| EvidenceQuality | ObservationKey | Preserved source row plus eligibility and reason |
| SelectedBenchmarks | ProductKey | Cheapest current recorded exact evidence, otherwise cheapest allowed indicative reference |
| PriceHistory | EventKey | Changed economic/variant payload, not every unchanged observation |
| Exceptions | Offer + quantity + issue | Actionable blockers/review reasons, deliberately not a unique offer count |
| RefreshStatus | RunID | Committed run and review date |

`validated.sqlite` enforces offer/product/supplier foreign keys and evaluation uniqueness. Its exact executable DDL is included as `schema.sql` in each generation. Money is calculated with Python Decimal; SQLite exports use REAL for analytical display, not financial posting. Do not sum alternative quantities. DifferenceFromBestPerUnit is a comparable cost gap, not realised savings. No exchange rates are invented: non-GBP offers are blocked.

`listing_registry.sqlite` preserves original listings, aliases and price_events. New import_audit stores source hash, ingestion time and row count; identity_audit records old/new product keys and documented reasons. Listing aliases are supplier-scoped. SourceFile and payloads remain private. CurrentPayload retains the latest source fields. Import hashes are provenance, not a substitute for dated observations.

## Identity rules

Separate ListingID, OfferKey and ProductKey. Resolve supplier external ID, URL and SKU aliases; ambiguous aliases fail the batch. Without any stable source identifier, quarantine the row. Internal generated keys are explicitly internal and never represented as supplier SKUs. New cross-supplier matches need a checksum-valid GTIN and matching nonblank language, product type, pack quantity, edition, region and variant. Names alone are insufficient. Record explicit 'Not applicable' attributes only when evidence establishes that fact. Conflicting variants remain separate. Existing reviewed matches are retained; a changed variant withdraws approval, creates a new product identity and preserves old events. Missing attributes replacing known attributes also trigger review. New manual decisions must use `--identity-reviews`; they do not rewrite historical price payloads. Full user authentication for reviewer names is outside this local CLI.

## Evidence rules

Source Include is never overwritten. Include!=Yes, non-exact matches, non-UK comparable rows, non-positive/future prices and missing source URLs do not enter benchmarks. Stock/source conflicts and restricted offers are excluded pending review. Stale (>30 days), historical, sold-out, preorder and unknown-availability prices may remain indicative references but never immediate evidence. A dated exact 'In stock' record is 'Current recorded in-stock', not a live verification. Conflict detection also checks the supplied Evidence notes. Selection prioritises immediate references, then lowest price, then observation ID. This deliberately differs from older Include-only logic. No crawling or revalidation was performed.

## Economics and limitations

All supported offers use compatible GBP sellable units and ex-VAT acquisition prices. Positive integer quantities must meet MOQ and order multiples. Base or single bulk tier is selected at its threshold. Unknown stock, unavailable products, unapproved identity, stale/future costs and unconfirmed terms block cost ranking. Different pack sizes must never share a product key. Multiple discount tiers remain preserved in original exports but are not generalised by this continuation; a live source with more than one bulk tier requires an adapter/engine extension before ranking.

Goods = selected ex-VAT unit cost × quantity. Landed order cost = goods + shipping + other order charges; free-shipping threshold is tested against goods. Supplier minimum spend is also assessed on ex-VAT goods. Cash estimate = landed cost × (1+VAT rate). This explicitly supports uniform standard VAT and recoverable input VAT only. Mixed VAT rates, margin-scheme goods, nonrecoverable VAT, import duties and deferred-payment cash timing are not modelled; do not mark such terms Confirmed. There is no tax advice or inferred supplier tax treatment.

Retail ex VAT = recorded retail price / (1+VAT rate). Gross margin = (retail net − landed unit cost)/retail net. Markup uses landed unit cost as denominator. Target retail including VAT = landed unit cost / (1 − target margin) × (1 + VAT rate). Unit gross profit uses net revenue less landed unit cost. Contribution subtracts payment fee rate × retail gross price. Stock cover = (on-hand + order quantity)/verified monthly demand. Unknown or nonpositive demand stays unknown. A 'Review-ready — human decision' row also needs immediate retail evidence, verified demand/on-hand, cover limit, target margin and positive contribution. Nothing approves or places an order.

Mixed-product baskets require one supplier and no duplicate offer lines. MOQ, stock and unit rules apply per line; minimum spend and shipping apply once to combined goods. Charges are allocated in proportion to goods value. Line evaluations expose their standalone zero-shipping base values plus AllocatedChargesExVAT; the basket total is authoritative. Basket evaluation does not establish retail viability or demand and always requires review. Multi-supplier orders are separate baskets.

## Adapter contract

CSV/TSV/XLSX mapping is destination-field -> actual source column. `authorized_export` must be true after permission is established; `supplier_id` must match every output row. Required values: SupplierID, positive BaseCostExVAT, positive integer MOQ/OrderMultiple, timezone-aware ObservedAt and at least one source identity (ExternalListingID, URL or SKU). Optional price-tier, stock, pack and lead quantities must be valid numbers. CostDate, Currency, Availability and matching attributes are required for economic/matching eligibility, even though incomplete listings can be retained for review. Blank is unknown, never zero. Dates use ISO 8601. Synthetic declaration is explicit. Raw URLs must not embed credentials. Never include secrets in configuration.

Adapter templates are generic and tested with fixtures; mappings for actual supplier exports cannot be asserted until sample schemas and permission are available. Source receipt timestamps must not be substituted for supplier price timestamps. Imported rows older than last observed are logged and skipped, not inserted out of order. Same-timestamp conflicting payloads fail. Unchanged later observations update LastSeenAt and URL aliases without duplicate events. Price movement is suppressed across currency or variant changes.

## Refresh and scheduling

`python scheduled_refresh.py config/schedule.json` runs the same pipeline with today's freshness date, preserves subprocess exit codes and appends an audit log. Populate optional local paths after validating authorised exports. `config/register_task.ps1` registers a daily Windows task only when explicitly run locally; it has not been executed here. The Python wrapper is tested here; Windows Task Scheduler is not. No unattended website login or automatic supplier downloads exist. Pin Power BI to one completed generation to avoid mixed snapshots; see INTEGRATION.md.

## Tests

Run `python run_validation.py`. Tests use temporary databases and directories, including paths with spaces. Seven original SQL boundary tests run against an in-memory backup. The new suite covers evidence, identity variants, Decimal economics, baskets, import history and atomic refresh preservation. `audit/test_results.json` records actual outcome; a failed test yields nonzero exit code. Native Power BI interactions require the separate Desktop acceptance checklist.


## V6 verified changes — 16 October 2026

Failed refresh cleanup now closes both SQLite connections before staging removal on Windows. Eleven additional tests exercise repeated failure/recovery, refresh locking, TSV and XLSX import controls. The suite now runs 56 tests, plus seven original SQL checks in the private project. Install `requirements-xlsx.txt` to run the full suite; CSV/TSV runtime paths remain standard-library only. XLSX uses openpyxl, explicit sheet selection for multi-sheet files and values-only mapped cells. Text identifiers are mandatory; numeric SKU/barcode cells are rejected rather than silently losing zeroes. Blank and duplicate headers and inconsistent delimited row widths fail validation. Legacy .xls is not supported; obtain an authorised values-only .xlsx or CSV export.

The private native Power BI report was integrated and validated in Desktop. See `audit/DESKTOP_ACCEPTANCE.md` and `audit/desktop_dax_acceptance.json`. The separate public fictional package supplies M/DAX files; it is not a separately compiled public PBIX. Historical documentation below/elsewhere that says Desktop validation was outstanding describes the previous delivery, not this private V6 acceptance.


