# Living Research — Design Document

**Date:** 2026-03-18
**Status:** Approved

## Overview

Add a new top-level section "Living Research" to CollabAtlas. Research cases document ongoing research (typically PhD theses) with their context, methods, observed artefacts, and identified issues. They link to existing catalogue entries (tools, methods, frameworks) and evolve over time.

## Data Model (`data/entries/research-cases/*.yaml`)

```yaml
id: demoor-book-design
type: research-case
title: "Collaborative Book Layout Design"
tagline: "Exploring graphic intent communication in publishing workflows"

researcher:
  name: "Emma-Jade De Moor"
  role: "1st year PhD Student in HCI and Design"
  supervisors:
    - "Michel Beaudouin-Lafon"
    - "Wendy Mackay"
    - "Lorène Picard"

studied_domain: "Free text describing the studied domain"
research_methodologies: "Free text describing methodologies"
observed_practices: "Free text describing observed practices"
observed_artefacts: "Free text describing artefacts in use or designed"

issues_organizational: "Free text or empty"
issues_technical: "Free text or empty"
issues_governance: "Free text or empty"
issues_policy: "Free text or empty"

publications:
  - url: "https://..."
    title: "Paper title"
datasets:
  - url: "https://..."
    title: "Dataset title"
software:
  - url: "https://..."
    title: "Software title"

# Standard catalogue fields for cross-linking
domains: []
collaboration-types: []
scales: []
modalities: []
related_entries: []   # Links to existing catalogue entries
status: published
contributors: []
created: "2026-03-18"
last_reviewed: "2026-03-18"
tags: []
```

## URL Structure

- List page: `/research-cases/`
- Single page: `/research-cases/demoor-book-design/`
- Menu label: "Living Research"

## Layout — Single Page

1. **Header**: title, tagline, freshness badge
2. **Researcher card**: name, role, supervisors
3. **Context section**: studied domain, methodologies, observed practices, observed artefacts (each in a labelled block)
4. **Identified Issues section**: organizational, technical, governance, policy — shown only if non-empty
5. **Outputs section**: publications, datasets, software — shown only if non-empty
6. **Sidebar/footer**: domains, collaboration-types, scales, related_entries (clickable links to catalogue), contributors
7. **Action buttons**: Suggest an edit, Save to favorites

## Files to Create

- `data/entries/research-cases/demoor-book-design.yaml`
- `content/research-cases/_index.md`
- `content/research-cases/demoor-book-design.md`
- `layouts/research-cases/single.html`
- `layouts/research-cases/list.html`
- `.github/ISSUE_TEMPLATE/new-research-case.yml`
- CSS additions in `assets/css/main.css`

## Files to Modify

- `hugo.toml` — add "Living Research" menu entry
- `static/admin/config.yml` — add research-cases collection
- `scripts/issue_to_entry.py` — support research-case type
- `layouts/index.html` — optionally include in Recently Added

## Not in Scope

- Recommendation engine (suggesting catalogue links from free text) — future enhancement
- Dedicated search/filter on the list page — use existing pagefind
