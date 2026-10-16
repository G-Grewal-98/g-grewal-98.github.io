# Procurement analytics portfolio — recruiter-facing release candidate

**Status:** local/public-safe website candidate. Nothing has been published from this archive. The private Power BI report is intentionally not distributed.

## What this website demonstrates

- Real-world retail purchasing experience and a methodical procurement analytics case study.
- Two distinct fictional demonstrations: a 12-product margin/demand simulator and a six-offer, three-product supplier comparison.
- A separate four-offer, two-product landed-cost demonstration using precomputed public Python engine outputs and a retained synthetic £24.95 → £22.95 history event.
- SQL, Python, Excel, Power Query/DAX source-method examples without publishing actual commercial quotations.

The expanded private Power BI V6 report was reported as saved, reopened and refreshed with 30 native DAX acceptance checks; the public downloadable models and M/DAX samples do **not** represent a publicly deployed PBIX. Real supplier ingestion and purchase approval are outside the scope of this website.

## Preview

Open `index.html` directly in a modern browser. The main page's examples are bundled with public fixture data and no longer require network access to fetch JSON. The separate landed-cost page at `downloads/Procurement_Intelligence_Public/portfolio/index.html` is also self-contained.

For realistic local URL/download behaviour, serve the folder using Python:

```sh
python -m http.server 8000
```

Then open `http://localhost:8000`. Publication to GitHub Pages requires the website owner's review and approval.

## Refresh fictional data

The original JSON and Python/SQL source files remain present. If updating either `downloads/Procurement_Analytics/demo.json` or `supplier_offers.json`, regenerate the static `public-data.js` by running:

```sh
python tools/build_public_data.py
```

The standalone landed-cost page contains its own frozen public scenario fixture from the separate runnable public package. Update that page with matching tested outputs if the underlying public scenario data changes; do not insert private business records.

## Local checks

```sh
node tests/scenarios.test.mjs
node tests/controls_v6.test.mjs
python tests/link_check.py
```

Browser interaction and responsive layout were also checked using headless Chromium on 1440px and 390px renderings in the editing environment, with data/script content injected without network requests. This does not replace a live deployment smoke test in desktop/mobile browsers.

## Privacy and deployment

The public CV files `downloads/Guramrit_Grewal_CV_Public.pdf` and `.docx` were updated to the owner's reviewed contact-free versions. No private supplier costs, customer information or private PBIX are part of this package.

**Before publication:** review the whole website and CV content, verify external GitHub URLs, test the actual site after deployment, and confirm approval to overwrite or merge with the current repository. Preserve the existing live website until then.

## New Power BI reporting showcase — 16 October 2026

The homepage includes a new `#power-bi` section and `power-bi-report.html` public-safe report walkthrough. The visuals are **reconstructions from validated aggregate V6 results**, not exported screenshots from the private PBIX. See `SHOWCASE_RELEASE_NOTES.md` for QA checks, scope and publication limits.
