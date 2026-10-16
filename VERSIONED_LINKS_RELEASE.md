# V6 public portfolio — source link audit and release notes

**Publication status:** Local review copy only; not deployed to GitHub Pages.

## What was actually linked in the previous draft?

The Power BI showcase/walkthrough described the **privately validated V6 eight-page report** using public-safe aggregate evidence. The old Technical Evidence links, however, mostly pointed to **original workbook-era DAX and Power Query** in the existing GitHub repository; Python links likewise referenced earlier code. The prominent "Download synthetic technical package" button still downloaded the older 12-product `Procurement_Analytics.zip`. None of these was the final V6 `.pbix` file.

## Current review links (and what they prove)

| Public link | Destination | Scope/status |
|---|---|---|
| Power BI walkthrough | `power-bi-report.html` | **V6 private report summary:** 8 pages, 30 native DAX checks, refreshed in Desktop. Visuals are recreated aggregate diagrams, not actual PBIX screenshots. |
| Public QA DAX example | `downloads/Procurement_Intelligence_Public/powerbi/continuation/measures.dax` | **Latest supplied public synthetic QA code**, NOT a verbatim export of the compiled V6 private semantic model. |
| Public QA evaluation query | `downloads/Procurement_Intelligence_Public/powerbi/continuation/QA_Evaluation.pq` | **Latest supplied public synthetic QA Power Query example**, not final private report code. |
| Public QA integration notes | `downloads/Procurement_Intelligence_Public/powerbi/continuation/INTEGRATION.md` | Explicit limitations: standalone artifacts not compiled as their own public PBIX. |
| Original project DAX | `downloads/Real_Project_Methods/powerbi/measures.dax` | **Earlier original project source**, intentionally retained as historical methods. |
| Original SQL/Python | `downloads/Real_Project_Methods/...` | Original project source; clearly labelled historical. |
| Latest fictional Python engine | `downloads/Procurement_Intelligence_Public/refresh_v2.py` | Updated public engine demonstration supporting authorised imported exports and historical price logic. |
| Latest fictional ZIP | `downloads/Procurement_Intelligence_Public.zip` | Updated fictional engine, data, test cases and QA M/DAX artifacts; replaces older 12-product ZIP as primary download. |
| Earlier 12-product Excel workbook | `downloads/Procurement_Analytics/Procurement_Demo.xlsx` | Historical **fictional sample** retained for Excel demonstrations; not the private production workbook. |
| Public CV Word / PDF | `downloads/Guramrit_Grewal_CV_Public.{docx,pdf}` | Latest approved/polished public-safe CV in this conversation; content files matched byte-for-byte. |

**No native Power BI V6 PBIX was included:** the validated V6 Desktop report is private and was not uploaded as part of this website ZIP. Its latest complete M/DAX definitions were not available for independent public redistribution. The public synthetic QA artifacts must not be represented as direct exports of the private validated model.

## Fixes in this revision

- Repaired the broken "View validated report walkthrough" link that previously occupied its own narrow grid column. Links now live inside the correct technical evidence content column.
- Grouped and labelled the public QA examples and earlier original sources, with explicit version and provenance notes.
- Removed stale direct GitHub file links from technical sections, using included local resources instead so the site works before and after publication.
- Changed the primary technical download from the older `Procurement_Analytics.zip` to the newer `Procurement_Intelligence_Public.zip` while retaining access to the older workbook sample.
- Added a **Which source files are available?** section to the V6 Power BI walkthrough.
- Kept synthetic/private-data disclaimers and preserved pricing-scenario JavaScript unchanged.
- Incremented stylesheet cache token for clean browser refresh on eventual publication.

## Checks run on 16 October 2026

- 96 scenario assertions passed.
- 73 control/event assertions passed, total 169.
- 70 local references checked and present, zero missing.
- Chromium with identical inline site HTML/CSS/JS at 1440px and 390px rendered the fixed Technical Evidence and Power BI source sections: no JavaScript errors or page-wide overflow; all versioned links appear as horizontal, appropriately sized items.
- Browser direct `file://` navigation was blocked in this test environment; the corrected pages were instead rendered from their own inline source content. Final direct-open and deployed-site smoke tests remain recommended.

## Publication safeguards

1. Extract into a new folder and review the site and all download buttons, especially the current fictional ZIP and public CV.
2. Do not add private `V6.pbix`, private supplier terms, wholesale quotes or real business data to the public website.
3. Get explicit owner approval and compare current GitHub `main` before publishing. The existing live website has **not** been changed here.

## Product-scale presentation update (16 October 2026)

- The website headline and case study now say **240+ products**, which accurately describes the project as it evolves.
- The original workbook remains documented as a 240-product historical snapshot; the pinned extended model contains **246 product identities**, including labelled synthetic test additions.
- The **240 legacy buying decisions** remain an exact count; the benchmark calculation stays **222/240 = 92.5%**. No SQL, source data, test results or DAX figures were changed.
- The private V6 PBIX remains unpublished.
