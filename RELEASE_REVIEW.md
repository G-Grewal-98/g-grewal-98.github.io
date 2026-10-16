# Recruiter-facing website revision — local review candidate

**Published?** No. This is a revised copy of the supplied ZIP, not a change to the live GitHub Pages site.

## Scope of modifications

- Preserved the existing palette, layout system, original Python/SQL examples and fictional source data.
- Updated the homepage narrative to lead with commercial decisions, real experience and the meaning of price evidence.
- Made the 12-product simulator and supplier comparison self-contained for offline opening (no module or fetch permissions required). Retained source modules and added a reproducible JSON-bundle generator.
- Added product-specific supplier comparisons, displaying excluded minimum orders as well as eligible offers. An explanatory summary now changes with quantity: at 24 Harbour units, supplier A is eligible; at 72, the lower goods-price supplier B qualifies.
- Redesigned the separate landed-cost page with a clear business problem, dynamic lowest-eligible-cost interpretation, sample price history and restrained technical disclosures. Precomputed public engine values were preserved.
- Updated website Word/PDF downloads to the latest contact-free public CV, with only the portfolio link shown in the CV header. All original private application CVs remain outside this release.
- Put detailed formula assumptions behind an optional disclosure, retaining technical methodology for those who want it.
- Kept strong and explicit simulated-data disclaimers, plus human-review caveats; no live supplier data, savings or stock availability are invented.

## Verification performed

- Original scenario calculation suite: **96 assertions passed**.
- Updated control and event suite: **73 assertions passed**, including supplier eligibility changes and the standalone landed-cost views.
- Rendered main and standalone pages at desktop **1440px** and mobile **390px** using Chromium; zero uncaught script exceptions and no page-wide horizontal overflow. On-page table scroll is intentional on narrow screens.
- Interacted with selectors in Chromium; verified initial 12-product load, supplier eligibility at 24 and 72 units, quantity-dependent landed-cost summaries, and recorded £24.95→£22.95 history.
- Checked **38 local links/references** across three pages; none missing.
- Latest public CV PDF checked for absence of the removed school/additional-info sections, personal contact details and an extra GitHub link.

**Limits:** Browser testing used `set_content` with inline copies of the same static HTML/CSS/JS files because the environment blocks navigation to localhost. The standalone script and its data were executed in Chromium, but the full on-disk site and download interactions still need a smoke test using its actual URL. External GitHub destinations were not exhaustively verified. The business engine's earlier private tests are unchanged, not rerun by this website revision.

## Publication steps

1. Extract ZIP into a clean review folder; do not overwrite the original website.
2. Open `index.html` in a browser and test interactive controls.
3. Check the public CV downloads and `downloads/Procurement_Intelligence_Public/portfolio/index.html`.
4. Obtain explicit approval before merging into the existing GitHub Pages site.
5. Confirm relative links, production interactions and mobile appearance at the published URL.
