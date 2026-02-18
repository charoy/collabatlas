# Review Criteria

This document outlines the quality standards domain editors use when reviewing contributions to CollabAtlas.

---

## Catalogue Entries

### Required Checklist

Every catalogue entry must pass these checks before merging:

- [ ] **Schema valid** — passes `python scripts/validate.py` without errors
- [ ] **Required fields complete** — all fields marked required in the schema are present and non-empty
- [ ] **Taxonomy values valid** — all domain, scale, modality, collaboration_type, and research_method values exist in `data/taxonomies/`
- [ ] **ID format correct** — lowercase, hyphenated, unique (e.g., `participatory-design`)
- [ ] **Description is accurate** — factual, not marketing copy, not copied from the source website
- [ ] **Tagline is concise** — under 200 characters, describes the entry clearly
- [ ] **External links are live** — all URLs return a valid response
- [ ] **Related entries exist** — all IDs in `related_entries` correspond to real entries in the catalogue
- [ ] **Maturity level justified** — the chosen level matches the actual state of documentation and adoption
- [ ] **Content page exists** — a matching Markdown file in `content/catalogue/{type}/`

### Quality Dimensions

Entries are evaluated on four dimensions:

| Dimension | What we look for |
|-----------|-----------------|
| **Completeness** | All optional fields filled where applicable (external links, tags, related entries) |
| **Accuracy** | Information is verifiable, up-to-date, and correctly attributed |
| **Connectivity** | Related entries linked, tags meaningful, taxonomy dimensions well-chosen |
| **Richness** | Multiple external links (website, papers, repositories), descriptive content |

### Type-Specific Criteria

**Tools:** website URL present, license and open-source status specified, supported platforms listed if applicable.

**Methods:** steps described, when-to-use and limitations filled, research method dimension specified.

**Frameworks:** key concepts listed, seminal works referenced with proper citations.

**Case Studies:** organization and year specified, outcomes described, methods and tools used cross-referenced.

**Datasets:** source URL present and accessible, format and size specified, license stated.

**Resources:** resource type specified, authors and year present, access level (open/restricted/paid) correct.

---

## Research Articles

### Required Checklist

- [ ] **ID unique** — follows `author-year` pattern, no duplicates
- [ ] **Title correct** — matches the actual publication title
- [ ] **DOI verified** — resolves to the correct article (if provided)
- [ ] **Domains appropriate** — accurately reflects the article's subject areas within CollabAtlas scope
- [ ] **Tags descriptive** — specific, useful for discovery (not generic terms)
- [ ] **Relevance justified** — the article meaningfully relates to collaboration research or practice
- [ ] **Not a duplicate** — no existing entry with the same DOI or title

### What Makes a Strong Article Entry

- Has a DOI and verified metadata (via `fetch_doi.py`)
- Abstract present (fetched or manually added)
- Citation count available (indicates established work)
- Multiple domains tagged (enables cross-domain discovery)
- Related catalogue entries linked (connects articles to tools/methods)

---

## What Gets Rejected

- **Marketing content** — entries that read as product promotion rather than neutral description
- **Unverifiable claims** — descriptions making claims without sources or evidence
- **Duplicates** — entries that duplicate existing catalogue items
- **Out of scope** — content with no meaningful connection to collaboration research or practice
- **Incomplete entries** — missing required fields with no plan to fill them
- **Broken links** — external links that don't resolve (should be fixed before merge)
- **Invalid taxonomy values** — using values not defined in `data/taxonomies/`

---

## Review Process

1. **Automated checks** run on every PR (schema, taxonomy, links)
2. **Domain editor** reviews accuracy, relevance, and quality
3. **Feedback** is provided as PR comments — we aim to be specific and constructive
4. **Revision** — contributor addresses feedback
5. **Approval** — domain editor approves, core maintainer merges

Reviewers should:
- Be constructive and specific in feedback
- Suggest improvements rather than just rejecting
- Acknowledge the contributor's effort
- Complete reviews within 1 week when possible
