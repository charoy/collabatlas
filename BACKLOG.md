# CollabAtlas Backlog

This backlog captures the main remaining work for the site after the first round of dynamic improvements to discovery and the "Find Your Method" wizard.

## Current status

### Completed recently

**Community contribution infrastructure (March 2026):**

- GitHub Issue Forms for all 6 entry types + blog posts + research articles.
- Issue templates with guided descriptions and taxonomy help on every field.
- Automated issue-to-PR pipeline (GitHub Actions) with YAML/Markdown generation.
- Parser fixes: correct field names, platform casing, related entry slugification.
- Sveltia CMS at `/admin/` with GitHub OAuth via Cloudflare Workers.
- "Contribute" section on homepage with cards linking to each issue form.
- "Suggest a {Type}" buttons on every catalogue section page.
- "Write a Post" button on the blog listing page.
- Comparison dock dismiss button (close with ×).
- CodeRabbit automated PR review integration.

**Earlier phases:**

- Wizard data now comes from live Hugo content and data files.
- Wizard results can be shared via URL.
- Wizard results now explain matches more clearly.
- Wizard markup was moved into a shortcode for easier maintenance.
- Global search is now available in the header.
- A dedicated search page is now available.
- Catalogue filters now persist in the URL and expose active chips.
- Research page filters now persist in the URL and expose active chips.
- Catalogue visual exploration is now available via a matrix and lightweight stats panels.
- Local personalization now supports browser-stored favorites for catalogue entries.

### Still open

- External knowledge sources are only partially integrated.
- Some documentation still needs contributor-oriented technical details.
- Issue-to-PR automation requires enabling "Allow GitHub Actions to create PRs" in repo settings.
- GitHub Actions validation bot for issue quality feedback not yet implemented.
- Contributing guide page on the site (Hugo page at /contribute/) not yet created.

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

**Status:** implemented in second version.

### 4. Add entry comparison (COMPLETED)

**Goal:** help users compare 2–4 entries side by side.

Tasks:

- [x] Add compare checkboxes on entry cards.
- [x] Create a comparison page or panel.
- [x] Compare maturity, scales, modalities, domains, limitations, and when-to-use fields.
- [x] Support comparison links that can be shared.

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

**Status:** implemented in first version.

### 6. Improve related-entry recommendations

**Goal:** better connect entries across the catalogue.

#### Tasks

- Combine manual related entries with automatic taxonomy-based suggestions.
- Show related tools, methods, and frameworks separately when relevant.
- Avoid duplicate or weak recommendations.

#### Definition of done

- Entry pages encourage deeper browsing with meaningful related links.

**Status:** implemented in first version.

---

## Priority 4 — Integrate external resources

### 7. Connect bibliographic and research APIs

**Goal:** enrich entries and research references automatically.

### Status

First iteration now supports merged OpenAlex + Crossref enrichment, ORCID capture
from available author metadata, Zotero library / CSL-JSON imports for research
articles, Zenodo-based dataset creation / refresh, and GitHub-based tool entry
creation / refresh. Broader catalogue-entry enrichment partially complete.

Candidates:

- OpenAlex
- Crossref
- ORCID
- Zotero API
- Zenodo
- GitHub API

Tasks:

- [x] Decide which sources are most valuable for the first iteration. (GitHub)
- [x] Define a small enrichment workflow for scripts in `scripts/`. (`enrich_catalogue.py`)
- [x] Store normalized identifiers where relevant.
- [x] Add attribution and rate-limit-safe fetching.

Definition of done:

- [x] External metadata can be imported or refreshed with a documented workflow.
- [x] The source of enriched metadata is visible and traceable.
- [x] The UI exposes these metrics clearly.

**Status:** implemented in first version.

---

## Priority 5 — Visualize the catalogue (COMPLETED)

### 8. Add visual exploration components (Done)

**Goal:** make the site feel more exploratory and dynamic.

### Status

First release implemented with a lightweight domain × entry type matrix and a
small statistics dashboard on the catalogue landing page. Additional
visualizations include interactive distribution charts on the `/catalogue/visualize/` page.

Possible components:

- [x] Taxonomy matrix (methods × domains, tools × modalities, etc.)
- [x] Statistics dashboard for the catalogue
- [x] Interactive distribution charts (Domains, Maturity, Scales, etc.)
- [ ] Network graph of related entries (deferred)
- [ ] Timeline of recent additions and reviews (deferred)

Tasks:

- [x] Choose one lightweight visualization for a first release.
- [x] Ensure it works without making the site heavy or fragile.
- [x] Reuse existing taxonomy and entry metadata.

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

## Priority 7 — Prepare catalogue scalability

### 11. Plan the transition to a larger catalogue

**Goal:** keep discovery fast and maintainable when the atlas grows to hundreds
or thousands of entries.

### Why this matters

The current architecture is a good fit for a still-growing static catalogue, but
some patterns will become expensive at larger scale:

- global client-side search indexes injected into the page shell;
- client-side filtering over all visible cards at once;
- large all-in-one catalogue pages;
- visual components that try to render too much raw data at once.

### Scaling stages

#### Stage 1 — up to ~500 entries (COMPLETED)

**Approach:** keep the current static-site architecture, but reduce unnecessary
payloads and make navigation more sectional.

Tasks:

- [x] Extract search index from the DOM into a fetchable JSON asset.
- [x] Limit page-level data injection to what each page actually needs.
- [x] Strengthen pagination and section-specific browsing.
- [x] Keep visualizations aggregated rather than exhaustive.
- [x] Monitor build size and client-side script payload size.

Definition of done:

- Catalogue pages remain fast to load and filter.
- No page needs to preload the entire atlas unless strictly necessary.

#### Stage 2 — ~500 to 2,000 entries

**Approach:** introduce more specialized indexes and a stronger static-search
strategy.

Tasks:

- Split search, compare, and visualization data into separate generated assets.
- Evaluate or adopt a static-search engine such as Pagefind.
- Prefer paginated and taxonomy-first list pages over one large aggregated view.
- Precompute more aggregate statistics and relationship hints at build time.

Definition of done:

- Search stays responsive without loading a large monolithic JSON blob.
- Catalogue discovery remains usable on modest devices.

#### Stage 3 — beyond ~2,000 entries

**Approach:** preserve the static-first model where possible, but be ready for a
more dedicated search and indexing layer.

Tasks:

- Reassess whether client-side filtering should remain card-based or move to
	JSON-backed result rendering.
- Keep visual exploration limited to aggregated dashboards, timelines, and
	summaries rather than full dense graphs.
- Precompute automatic related-entry suggestions and store them as derived data.
- Consider an external search service only if static search is no longer
	sufficient.

Definition of done:

- Discovery still scales without making the site fragile.
- Any move beyond pure-static search is justified by actual catalogue size and
	usage needs.

### Recommended future implementation order

1. Reduce global data injection in the base template.
2. Add or strengthen pagination for catalogue-heavy views.
3. Introduce split JSON assets for search, comparison, and visual summaries.
4. Evaluate Pagefind as the next search layer.
5. Precompute related-entry and visualization aggregates during the Hugo build.

### Status

Planning only for now. Active track as of first scalability improvements.

Tasks:

- [x] Limit page-level data injection to what each page actually needs (Search index extracted).
- [ ] Strengthen pagination and section-specific browsing.
- [x] Keep visualizations aggregated rather than exhaustive (Visual exploration separate page).
- [ ] Monitor build size and client-side script payload size.

---

---

## Priority 8 — Community growth and attractiveness

### 12. Make the site inviting to new contributors

**Goal:** lower the barrier to entry and make contributing feel rewarding.

#### Quick wins (low effort, high impact)

- [ ] Create a `/contribute/` Hugo page with a visual guide (what to contribute, how, what happens after).
- [ ] Add contributor attribution on entry pages ("Added by @username").
- [ ] Add a "Contributors" section on the homepage or about page showing avatars and contribution counts.
- [ ] Add a "Recently added" feed on the homepage (replacing or complementing the static blog section).
- [ ] Add Open Graph / social media meta tags for rich link previews when sharing entries.

#### Community engagement (medium effort)

- [ ] Add a "Suggest an edit" button on every entry page (links to GitHub issue pre-filled with entry ID).
- [ ] Create a GitHub Discussions space for questions, feature requests, and community conversation.
- [ ] Add a monthly changelog or "What's new" blog post template (can be semi-automated from git log).
- [ ] Implement a GitHub Actions bot that validates new issues and comments with suggestions (e.g., "You selected 0 domains — did you forget?").
- [ ] Add entry quality badges (completeness score based on filled fields).

#### Content seeding (to reach critical mass)

- [ ] Batch-import entries from curated lists (Awesome lists, CSCW proceedings, etc.).
- [ ] Add a DOI/URL-based quick-add: paste a URL, auto-extract metadata via OpenAlex/Crossref.
- [ ] Invite domain experts to curate specific taxonomy sections (e.g., "Healthcare collaboration tools").
- [ ] Write 3-5 high-quality blog posts that demonstrate the atlas's value (tool comparisons, domain guides).

#### Trust and governance (longer term)

- [ ] Add a review workflow: draft → community review → published (currently draft → published).
- [ ] Display review status on entry pages (peer-reviewed vs. community-submitted).
- [ ] Add entry versioning (show edit history via git blame / GitHub API).
- [ ] Create domain editor roles (trusted contributors who can merge PRs for their domain).

---

## Nice-to-have

- Add printable or downloadable comparison views.
- Add multilingual support for the wizard and catalogue UI.
- Add analytics for anonymous feature usage, if governance permits it.
- Network graph of related entries.
- Timeline of recent additions and reviews.

---

## Suggested implementation order (updated)

**Done:**

1. ~~Wizard scoring improvements~~
2. ~~Entry comparison~~
3. ~~Freshness indicators~~
4. ~~External metadata enrichment~~
5. ~~Visual exploration components~~
6. ~~Community contribution infrastructure (issue forms, CMS, automation)~~

**Next priorities:**

7. Community growth quick wins (contributor attribution, recently-added feed, OG tags)
8. Documentation alignment (README, contributing guide page)
9. Content seeding (batch imports, quick-add by URL)
10. Issue validation bot
11. Trust and governance (review workflow, domain editors)
