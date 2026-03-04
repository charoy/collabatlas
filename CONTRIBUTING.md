# Contributing to CollabAtlas

Welcome! CollabAtlas is a community-governed knowledge platform for collaborative solutions. We appreciate contributions from researchers and practitioners across all domains.

By contributing, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## Ways to Contribute

- **Add a catalogue entry** — tools, methods, frameworks, case studies, datasets, or resources
- **Propose a research article** — via DOI, BibTeX import, or GitHub Issue
- **Write a blog post** — share insights, tutorials, or commentary
- **Improve documentation** — fix errors, clarify guides, add examples
- **Report issues** — broken links, inaccurate entries, missing information

---

## Adding a Catalogue Entry

### 1. Fork and clone the repository

```bash
git clone https://github.com/<your-username>/collabatlas.git
cd collabatlas
```

### 2. Create a YAML data file

Add a YAML file in the appropriate `data/entries/{type}/` directory. Each entry type has its own schema in `schemas/`.

**Example — adding a tool:**

```yaml
# data/entries/tools/my-tool.yaml
id: my-tool
type: tool
title: My Tool
tagline: A short description of what this tool does
description: >
  A longer description explaining the tool, its purpose,
  and how it supports collaborative work.
domains: [education, design]
collaboration_types: [co-design, distributed]
scales: [small-team, organization]
modalities: [remote, hybrid]
maturity: established
website_url: https://my-tool.example.com
open_source: true
license: MIT
external_links:
  - type: website
    url: https://my-tool.example.com
  - type: paper
    url: https://doi.org/10.xxxx/xxxxx
    title: "Paper evaluating My Tool"
related_entries: [miro, participatory-design]
tags: [real-time, visual]
created: 2026-02-18
last_reviewed: 2026-02-18
contributors: [your-github-username]
status: published
```

### 3. Create a content page

Add a matching Markdown file in `content/catalogue/{type}/`:

```markdown
---
title: "My Tool"
tagline: "A short description of what this tool does"
type: tool
domains: [education, design]
collaboration_types: [co-design, distributed]
scales: [small-team, organization]
modalities: [remote, hybrid]
maturity: established
status: published
---

A longer description of the tool with context about how it supports collaboration...
```

### 4. Validate your entry

```bash
pip install -r scripts/requirements.txt
python scripts/validate.py
```

### 5. Submit a Pull Request

Push your branch and open a PR. The CI pipeline will automatically validate your entry against the schema. A domain editor will review the content.

---

## Proposing a Research Article

There are three ways to add research articles:

### Option A: By DOI (recommended)

If you have a DOI, the metadata is fetched automatically:

```bash
python scripts/fetch_doi.py 10.1145/175222.175230
```

Then manually add `domains` and `tags` to the entry in `data/research-articles.yaml`.

### Option B: From BibTeX or RIS files

Export from Zotero, Mendeley, or Google Scholar and import in bulk:

```bash
python scripts/import_references.py --bibtex refs.bib --enrich
python scripts/import_references.py --ris export.ris --enrich
```

Use `--dry-run` to preview before writing. The `--enrich` flag fetches additional metadata (citations, open access status) from OpenAlex and CrossRef.

### Option C: Via GitHub Issue

Use the **"Suggest Research Article"** issue template. Provide the title, DOI (if available), and explain why the article is relevant to CollabAtlas. A domain editor will process it.

---

## Taxonomy Values

Valid taxonomy values are defined in `data/taxonomies/`:

| Taxonomy | File | Examples |
|----------|------|----------|
| Domains | `domains.yaml` | healthcare, education, design |
| Collaboration types | `collaboration_types.yaml` | co-design, participatory, distributed |
| Scales | `scales.yaml` | pair, small-team, organization |
| Research methods | `research_methods.yaml` | action-research, ethnography |
| Maturity levels | `maturity_levels.yaml` | emerging, established, well-documented |
| Modalities | `modalities.yaml` | in-person, remote, hybrid |

To propose a new taxonomy value, open an issue with the `taxonomy` label explaining the value and why it's needed. New values follow an RFC process (see [GOVERNANCE.md](GOVERNANCE.md)).

---

## Blog Posts

Create a Markdown file in `content/blog/` with the following front matter:

```markdown
---
title: "Your Post Title"
date: 2026-02-18
summary: "A one-sentence summary for the listing page."
category: "tutorial"  # tutorial, case-study, commentary, news
related_entries: [miro, participatory-design]
---

Your post content here...
```

---

## Review Process

After you submit a PR:

1. **Automated checks** run: schema validation, taxonomy verification, link checking
2. A **domain editor** reviews the content for accuracy, relevance, and quality
3. You may receive **feedback** — we aim to be constructive and specific
4. Once approved, a core maintainer **merges** the PR

See [REVIEW_CRITERIA.md](REVIEW_CRITERIA.md) for what we look for in entries.

---

## Development Setup

### Prerequisites

- [Hugo Extended](https://gohugo.io/installation/) v0.155+
- Python 3.12+

### Local development

```bash
# Install Python dependencies
pip install -r scripts/requirements.txt

# Validate all entries
python scripts/validate.py

# Run the local dev server
hugo server --buildDrafts

# Check external links (optional, slow)
python scripts/check-links.py
```

---

## Questions?

Open an issue or start a discussion on GitHub. We're happy to help!
