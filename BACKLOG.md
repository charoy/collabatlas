# CollabAtlas Backlog

This backlog captures the main remaining work for the site after the first round of dynamic improvements to discovery and the "Find Your Method" wizard.

## Current status

### Completed recently

- Wizard data now comes from live Hugo content and data files.
- Wizard results can be shared via URL.
- Wizard results now explain matches more clearly.
- Wizard markup was moved into a shortcode for easier maintenance.
- Global search is now available in the header.
- A dedicated search page is now available.
- Catalogue filters now persist in the URL and expose active chips.
- Research page filters now persist in the URL and expose active chips.

### Still open

- Data visualizations are not yet available.
- External knowledge sources are only partially integrated.
- Some documentation still needs contributor-oriented technical details.

---

## Priority 1 — Improve discovery

### Current integration status

Core discovery improvements are now implemented.

### Follow-up improvements

- Improve search ranking with taxonomy-aware synonyms and boosting.
- Consider a grouped result view by content type.
- Consider highlighting matched terms in the dedicated search page.

### 1. Add global search

**Goal:** let visitors search across tools, methods, frameworks, case studies, datasets, blog posts, and resources.

Tasks:

- Generate a lightweight JSON search index at build time.
- Include title, tagline, type, taxonomies, and URL in the index.
- Add a search UI in the header or catalogue landing page.
- Support instant filtering and keyboard navigation.
- Add empty-state and no-result messaging.

Definition of done:

- A user can find an entry from a keyword without browsing section by section.
- Search works on desktop and mobile.
- Hugo build still succeeds without external services.

**Status:** implemented in first version.

### 2. Improve catalogue filtering

**Goal:** make filters easier to understand and share.

Tasks:

- Persist catalogue filters in the URL.
- Add active-filter chips with one-click removal.
- Add a result count near the filter bar.
- Improve mobile layout for filters.
- Audit taxonomy labels for consistency.

Definition of done:

- A filtered catalogue view can be bookmarked and shared.
- The filtering UI remains usable on narrow screens.

**Status:** implemented for catalogue and research pages in first version.

---

## Priority 2 — Improve decision support

### 3. Refine wizard scoring

**Goal:** make recommendations more relevant and transparent.

Tasks:

- Weight some criteria more strongly than others.
- Distinguish between exact matches and broad matches.
- Add a "why this result" explanation block per entry.
- Add a "modify my answers" action from the results screen.
- Consider an optional preferred entry type question.

Definition of done:

- Users understand why a result appears.
- Results feel more relevant for varied contexts.

### 4. Add entry comparison

**Goal:** help users compare 2–4 entries side by side.

Tasks:

- Add compare checkboxes on entry cards.
- Create a comparison page or panel.
- Compare maturity, scales, modalities, domains, limitations, and when-to-use fields.
- Support comparison links that can be shared.

Definition of done:

- Users can compare multiple candidate approaches before deciding.

**Status:** implemented in first version.

---

## Priority 3 — Enrich content and trust signals

### 5. Add freshness and editorial signals

**Goal:** show which entries are current, reviewed, or need attention.

Tasks:

- Highlight recently reviewed entries.
- Surface stale entries on editor-facing pages or reports.
- Add a "last reviewed" badge or freshness indicator to cards and entry pages.
- Create a small editorial dashboard page if useful.

Definition of done:

- Visitors can see whether an entry is current.
- Editors can identify outdated content quickly.

### 6. Improve related-entry recommendations

**Goal:** better connect entries across the catalogue.

#### Tasks

- Combine manual related entries with automatic taxonomy-based suggestions.
- Show related tools, methods, and frameworks separately when relevant.
- Avoid duplicate or weak recommendations.

#### Definition of done

- Entry pages encourage deeper browsing with meaningful related links.

---

## Priority 4 — Integrate external resources

### 7. Connect bibliographic and research APIs

**Goal:** enrich entries and research references automatically.

### Status

First iteration now supports merged OpenAlex + Crossref enrichment, ORCID capture
from available author metadata, Zotero library / CSL-JSON imports for research
articles, Zenodo-based dataset creation / refresh, and GitHub-based tool entry
creation / refresh. Broader catalogue-entry enrichment remains open.

Candidates:

- OpenAlex
- Crossref
- ORCID
- Zotero API
- Zenodo
- GitHub API

Tasks:

- Decide which sources are most valuable for the first iteration.
- Define a small enrichment workflow for scripts in `scripts/`.
- Store normalized identifiers where relevant.
- Add attribution and rate-limit-safe fetching.

Definition of done:

- External metadata can be imported or refreshed with a documented workflow.
- The source of enriched metadata is visible and traceable.

---

## Priority 5 — Visualize the catalogue

### 8. Add visual exploration components

**Goal:** make the site feel more exploratory and dynamic.

### Status

First release implemented with a lightweight domain × entry type matrix on the
catalogue landing page. Additional visualizations can build on the same
metadata later.

Possible components:

- Taxonomy matrix (methods × domains, tools × modalities, etc.)
- Network graph of related entries
- Statistics dashboard for the catalogue
- Timeline of recent additions and reviews

Tasks:

- Choose one lightweight visualization for a first release.
- Ensure it works without making the site heavy or fragile.
- Reuse existing taxonomy and entry metadata.

Definition of done:

- Visitors can discover content through at least one visual interface.

**Status:** first release implemented.

---

## Priority 6 — Content and documentation alignment

### 9. Align documentation with actual implementation

**Goal:** keep project docs accurate.

Tasks:

- Review README feature claims.
- Mark implemented features vs planned features.
- Add links to the wizard and any future compare/search pages.
- Add a short roadmap section or link to this backlog.

Definition of done:

- Repository documentation matches the current product state.

### 10. Add contributor guidance for dynamic features

**Goal:** make the new site behavior maintainable.

Tasks:

- Document how the wizard data is generated.
- Explain where UI components live (`layouts/`, `assets/js/`, `assets/css/`).
- Add testing/build expectations for future JS enhancements.

Definition of done:

- A contributor can extend the interactive parts of the site without reverse-engineering the setup.

---

## Nice-to-have

- Save favorite entries locally in the browser.
- Add printable or downloadable comparison views.
- Add multilingual support for the wizard and catalogue UI.
- Add analytics for anonymous feature usage, if governance permits it.

## Suggested implementation order

1. Wizard scoring improvements
2. Entry comparison
3. Freshness indicators
4. Documentation alignment
5. External metadata enrichment
6. Visual exploration components
