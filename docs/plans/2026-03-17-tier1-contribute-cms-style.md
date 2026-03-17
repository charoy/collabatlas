# Tier 1: Contribute, CMS, Entry Enrichment & Style Refresh

**Goal:** Make CollabAtlas easier to contribute to, administrate, and visually appealing.

**Branch:** `feat/tier1-contribute-cms-style`

**Architecture:** GitHub-native contribution pipeline (issue templates + automation) + Sveltia CMS for trusted editors + enriched entry content + modern homepage styling.

---

## What was built

### 1. Contribute Buttons (commits a48ab08)

- **Hero button:** "Contribute" in hero links to `#contribute` anchor
- **Section pages:** Each catalogue section (Tools, Methods, etc.) shows a "+ Suggest a {Type}" button in the header, linking to the correct GitHub Issue template
- **Homepage CTA:** New "Contribute to CollabAtlas" section with 6 entry-type cards + "Suggest a Research Article" and "Update an Existing Entry" buttons
- **CSS:** `.btn-outline`, `.btn-sm`, `.page-header-row`, `.home-contribute`, `.contribute-grid`, `.contribute-card`

### 2. Sveltia CMS Admin Panel (commit 36951c2)

- `static/admin/index.html` — loads Sveltia CMS from CDN
- `static/admin/config.yml` — 6 collections (tools, methods, frameworks, case-studies, datasets, resources) with full taxonomy fields
- Authenticates via GitHub OAuth, no server needed
- Datasets have extra `platform` field

### 3. Entry Enrichment (commit a7cb255)

- `scripts/enrich_entries.py` — generates body content from frontmatter + YAML data files
- 119 entries enriched with overview paragraphs, collaboration context, and type-specific details
- Idempotent (skips entries with existing body content)

### 4. Homepage Style Refresh (commit 548342a)

- **Hero:** richer multi-color gradient, larger title, pill-shaped metric counter, gradient fade divider
- **Stats bar:** more breathing room, larger numbers, softer hover
- **Sections:** gradient fade dividers instead of hard borders, more whitespace
- **Catalogue tiles:** larger icons, thicker accent borders, stronger hover lift
- **Feature cards:** gradient background, larger emoji icons
- **Contribute section:** multi-color gradient background
- **Domain tiles:** added shadow for depth
- **Mobile:** responsive contribute grid, stat wrapping, softer dividers

## Existing infrastructure leveraged

- GitHub Issue templates for all 6 entry types (`.github/ISSUE_TEMPLATE/`)
- `issue-to-pr.yml` workflow + `issue_to_entry.py` parser (auto-creates PRs from issues)
- Validation workflows (schema, links, freshness)

## Next steps (Tier 2)

- Giscus comments on entry pages (GitHub Discussions-backed)
- Local favorites export/import and shareable collections
- Test the issue-to-PR pipeline end-to-end with a real submission
