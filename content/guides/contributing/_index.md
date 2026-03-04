---
title: "How to Contribute"
description: "Step-by-step guide for adding new entries, improving existing ones, or suggesting edits to CollabAtlas."
---

CollabAtlas is built by its community. Whether you want to add a new tool, document a method, or share a case study, this guide walks you through the process.

## Quick Contribution (No Git Required)

The easiest way to contribute is through our **GitHub Issue forms**. You only need a free [GitHub account](https://github.com/signup) — no Git knowledge, no local setup, no coding.

### Propose a new catalogue entry

1. Go to the [New Issue](https://github.com/charoy/collabatlas/issues/new/choose) page
2. Choose the template matching your entry type:
   - [New Tool](https://github.com/charoy/collabatlas/issues/new?template=new-tool.yml) — Software, platforms, instruments
   - [New Method](https://github.com/charoy/collabatlas/issues/new?template=new-method.yml) — Structured approaches and processes
   - [New Framework](https://github.com/charoy/collabatlas/issues/new?template=new-framework.yml) — Theoretical or analytical models
   - [New Case Study](https://github.com/charoy/collabatlas/issues/new?template=new-case-study.yml) — Real-world examples
   - [New Dataset](https://github.com/charoy/collabatlas/issues/new?template=new-dataset.yml) — Data for collaboration research
   - [New Resource](https://github.com/charoy/collabatlas/issues/new?template=new-resource.yml) — Books, articles, reference materials
3. Fill in the form fields (required fields are marked)
4. Submit the issue

A bot will **automatically create a Pull Request** from your submission. A maintainer will review it, may suggest edits, and publish it to the site.

### Suggest a research article

1. Go to [Suggest Research Article](https://github.com/charoy/collabatlas/issues/new?template=suggest-article.yml)
2. Fill in the title, DOI (if available), authors, and relevance
3. Submit — a PR will be created automatically

### Propose an update to an existing entry

1. Go to [Update Entry](https://github.com/charoy/collabatlas/issues/new?template=update-entry.yml)
2. Provide the entry ID and describe what should change
3. A maintainer will review and implement the update

---

## Advanced Contribution (via Git)

For contributors comfortable with Git and YAML, you can create entries directly and submit Pull Requests.

### Before You Start

Each catalogue entry consists of **two files**:

1. A **YAML data file** in `data/entries/{type}/{id}.yaml` — contains structured metadata (description, links, taxonomy tags, etc.)
2. A **Markdown content file** in `content/catalogue/{type}/{id}.md` — contains front matter (title, taxonomy values, status) and optional long-form content

The `{type}` corresponds to the entry category: `tools`, `methods`, `frameworks`, `case-studies`, `datasets`, or `resources`.

### Step 1 — Fork and Clone

Fork the [CollabAtlas repository](https://github.com/charoy/collabatlas) on GitHub and clone it locally:

```bash
git clone https://github.com/YOUR-USERNAME/collabatlas.git
cd collabatlas
```

### Step 2 — Choose Your Entry Type

CollabAtlas organizes entries into six types. Pick the one that best fits your contribution:

| Type | What it covers | Examples |
|------|---------------|----------|
| **Tool** | Software, platforms, instruments | Miro, GitHub, Jupyter |
| **Method** | Structured approaches and processes | Scrum, World Cafe, Action Research |
| **Framework** | Theoretical or analytical models | Actor-Network Theory, Communities of Practice |
| **Case Study** | Real-world examples of collaboration | OpenStreetMap, Linux Kernel Development |
| **Dataset** | Data sources for studying collaboration | GH Archive, Stack Overflow Survey |
| **Resource** | Books, handbooks, reference materials | Handbook of STS, The Open Source Way |

See the [Entry Types Reference]({{< relref "/guides/entry-types" >}}) for detailed field descriptions.

### Step 3 — Create the YAML Data File

Create a new file at `data/entries/{type}/{your-id}.yaml`. Use a short, URL-friendly identifier (lowercase, hyphens, no spaces).

Here is a minimal example for a **tool**:

```yaml
id: my-tool
type: tool
title: My Tool
tagline: A short one-line description of the tool.
description: >-
  A longer paragraph explaining what the tool does, who uses it,
  and why it is relevant to collaborative work.
domains:
  - software-engineering
collaboration_types:
  - distributed
scales:
  - small-team
modalities:
  - remote
maturity: well-documented
status: published
contributors:
  - your-github-username
created: "2025-06-01"
last_reviewed: "2025-06-01"
website_url: https://example.com
external_links:
  - type: website
    url: https://example.com
    title: Official Website
tags:
  - relevant-tag
```

#### Required Fields (All Types)

- `id` — unique identifier matching the filename
- `type` — one of: `tool`, `method`, `framework`, `case-study`, `dataset`, `resource`
- `title` — display name
- `tagline` — one sentence summary
- `description` — paragraph-length explanation
- `domains` — at least one domain from the [taxonomy]({{< relref "/governance" >}})
- `collaboration_types` — at least one type
- `scales` — at least one scale level
- `modalities` — at least one modality
- `maturity` — one of: `emerging`, `well-documented`, `established`
- `status` — use `published`
- `contributors` — list of contributor identifiers
- `created` — date in YYYY-MM-DD format
- `last_reviewed` — date in YYYY-MM-DD format

#### Type-Specific Fields

- **Tools**: `website_url`, `license`, `open_source`, `supported_platforms`
- **Methods**: `when_to_use`, `limitations`, `steps`, `research_methods`
- **Frameworks**: `key_concepts`, `seminal_works`, `limitations`
- **Case Studies**: `outcomes`, `key_concepts`, `limitations`
- **Datasets**: `source_url`, `format`, `size`, `license`, `temporal_coverage`, `platform`, `platform_id`
- **Resources**: `resource_type`, `authors`, `year`, `doi`, `access`

### Step 4 — Create the Markdown Content File

Create a matching file at `content/catalogue/{type}/{your-id}.md`:

```markdown
---
title: "My Tool"
tagline: "A short one-line description of the tool."
data_id: "my-tool"
domains: ["software-engineering"]
collaboration_types: ["distributed"]
scales: ["small-team"]
modalities: ["remote"]
maturity: "well-documented"
status: "published"
---

Optional long-form content goes here. You can include detailed analysis,
usage notes, screenshots, or comparison with related tools.
```

The `data_id` field **must match** the `id` in your YAML file. Taxonomy values in the front matter should mirror those in the YAML.

### Step 5 — Preview Locally

Install [Hugo Extended](https://gohugo.io/installation/) and run the development server:

```bash
hugo server -D
```

Navigate to your new entry at `http://localhost:1313/collabatlas/catalogue/{type}/{your-id}/` to verify it renders correctly.

### Step 6 — Submit a Pull Request

Create a branch, commit your files, and open a pull request:

```bash
git checkout -b add-my-tool
git add data/entries/tools/my-tool.yaml content/catalogue/tools/my-tool.md
git commit -m "Add my-tool to catalogue"
git push origin add-my-tool
```

In your pull request description, briefly explain:
- What the entry is and why it belongs in CollabAtlas
- Which domains and collaboration types it relates to
- Any sources or references you used

## What Happens Next

1. **Automated checks** validate your YAML schema and taxonomy values
2. A **domain editor** reviews accuracy, clarity, and taxonomy fit
3. After approval, a maintainer **merges** your contribution
4. Your entry appears on the site within minutes

See the [Review Process]({{< relref "/governance/review-process" >}}) for full details.

## Other Ways to Contribute

- **Improve an existing entry** — Fix errors, update links, add missing fields
- **Report a problem** — [Open an issue](https://github.com/charoy/collabatlas/issues) for broken links, outdated content, or missing features
