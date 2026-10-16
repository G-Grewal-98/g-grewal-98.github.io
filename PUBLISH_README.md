# Portfolio release candidate — 16 October 2026

## Purpose
Recruiter-facing portfolio highlighting purchasing judgement, supplier comparison, margin analysis, product identity, evidence quality, Excel, Python, SQL, and Power BI reporting. Real project scope is presented separately from fictional, downloadable scenarios. The private V6 PBIX and real supplier prices are NOT included.

## What changed in this final polish
- Removed detailed software test-count scorekeeping from the visible homepage, case study and Power BI walkthrough. Replaced it with concise, practical descriptions of skills and safeguards. Reproducibility remains documented within downloaded technical resources.
- Preserved meaningful commercial metrics: 240+ product scope, 251 offers in the extended snapshot, 395 recorded retail observations, and the exact 222/240 = 92.5% legacy benchmark coverage.
- Kept the 8-page Power BI report overview, labelled public-safe aggregate graphic, readable public demonstration, and current versus historical source links.
- Improved mobile text hierarchy and explanatory copy, added descriptive search/social metadata, canonical addresses, robots.txt and sitemap.xml.
- Preserved existing fictional datasets, JS calculations, source/download links and polished public CV (personal contact details omitted).

## Validation executed
- `node tests/scenarios.test.mjs` — 96 scenario assertions passed.
- `node tests/controls_v6.test.mjs` — 73 control/event assertions passed.
- `python tests/link_check.py` — 70 local references, 0 broken.
- Chromium inline-asset rendering of 4 pages at desktop and mobile widths — all passed with no JavaScript exceptions or document-width overflow; homepage slider/reset/quantity/supplier interactions exercised.
- Public text source scan — no email addresses, phone numbers, Windows user paths, or obvious secret tokens found.
- Public CV Word content — no personal phone/email, school or Additional Information section detected. The portfolio URL remains.

### Verification boundary
The execution environment restricts direct browser navigation to local files and HTTP destinations. Browser QA therefore rendered the *same authored HTML, CSS and JS in memory*, rather than performing an end-to-end GitHub Pages test. The user has already confirmed links work in a local extracted copy; final verification of deployed link targets and downloadable files is still necessary.

## How to publish
1. Preserve the current public GitHub Pages repository in a backup or branch and retrieve the latest remote commit before replacing anything.
2. Review all website files and the public download ZIP for commercial/privacy suitability.
3. Deploy the **contents** of `portfolio_2026-10-16/` to the GitHub Pages site root (not an extra nested `portfolio_2026-10-16` directory). Retain `.nojekyll`.
4. Confirm that the homepage, `intelligence-case-study.html`, `power-bi-report.html`, fictional landed-cost page, CV downloads, and technical ZIP download all work at the *public URL*.
5. Check phone/mobile display and the margin, demand, product and supplier-quantity controls in the deployed version.

No deployment or publication was performed by this assistant.
