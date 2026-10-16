# Recruiter-focused Power BI showcase — review release (16 October 2026)

This is a local review candidate. **It has not been published to GitHub Pages.** It extends the prior `Procurement_Portfolio_Improved_Review.zip` without altering its fictional calculations or private procurement project.

## What changed

- Added a clearly labelled, public-safe Power BI section to the homepage (`index.html#power-bi`) with a polished aggregate dashboard summary and a link to an extended report walkthrough.
- Added `power-bi-report.html` describing the verified V6 Power BI model: benchmark denominator reconciliation, recorded retail evidence categories, unverified supplier-term safeguards, eight-page reporting workflow and native DAX testing.
- Added a Power BI navigation link and cross-link from the technical case study.
- Corrected section numbering from the old duplicate `03` through `06`.
- Increased site body and small descriptive font sizes for recruiter readability while retaining the existing palette and design.
- Extended the internal link checker to include the new report walkthrough.
- Preserved the earlier interactive 12-product, supplier comparison and landed-cost demonstrations and retained the previously updated public-safe CV.

## Reporting integrity

The dashboard-like presentation uses **validated aggregate record counts** from the V6 completion review, not actual screenshots of the private PBIX. It must not be described as an exported dashboard screenshot, a public Power BI Service report, a live supplier feed, or evidence of realised savings.

- 251 recorded offers, 246 product identities, 395 retail observations.
- 240 legacy decisions: 222 with a benchmark and 18 without; coverage 92.5%. 11 additional offers lack legacy decisions.
- 1,004 quantity scenarios with **zero** cost-eligible rankings due to missing verified supplier terms.
- Evidence observation classifications: 132 recorded recent in-stock, 80 out-of-stock/preorder references, 37 availability conflicts, 6 unverified availability, 140 excluded; together they total 395 observations. These are not current stock checks.
- Private V6 report recorded 30/30 native DAX acceptance checks and save/close/reopen/full refresh acceptance in Power BI Desktop, as reported in `COMPLETION_REPORT.md`.

## Quality assurance for this release

- `node tests/scenarios.test.mjs`: **96 assertions passed**.
- `node tests/controls_v6.test.mjs`: **73 assertions passed**.
- `python tests/link_check.py`: **56 local links/references checked, zero missing** across four public pages.
- Chromium rendered the homepage and new walkthrough at **1440px** and **390px** with in-memory inline copies of the shipped HTML/CSS/JS. Existing 12-product rows loaded; no uncaught JavaScript exceptions; no page-wide horizontal overflow. The report walkthrough displayed all eight report-page summaries.
- Public CV remains contact-free with a single portfolio URL. The existing supplier calculation data, packages and original downloads were not modified.

## Outstanding publication gates

1. Open the actual extracted `index.html`, try scenario controls and `power-bi-report.html` and check the download links in your own browser. Browser restrictions in the build environment prevented direct `file://` navigation. The same source contents were nevertheless rendered and checked in Chromium.
2. If desired, supply **approved, thoroughly redacted screenshots** from the final V6 PBIX. These can be incorporated as real Power BI screenshots on a later update. The current walkthrough intentionally uses reconstructed aggregate panels instead.
3. Review public-facing claims and confirm that the contact-free public CV is the one you want to publish.
4. Obtain explicit publication approval and compare against current GitHub `main` before deploying. Do not upload or publish private PBIX files, supplier accounts, private commercial exports, private CVs or credentials.
