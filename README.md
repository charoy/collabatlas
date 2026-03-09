# CollabAtlas

**Navigate the landscape of collaborative solutions for research and practice.**

CollabAtlas is an open, community-governed knowledge platform that catalogues, connects, and contextualizes collaborative methods, tools, frameworks, and case studies across domains.

## What's Inside

- **Tools** — Software and platforms for collaboration (Miro, Zotero, Jupyter, ...)
- **Methods** — Structured approaches (Participatory Design, Delphi Method, ...)
- **Frameworks** — Conceptual and theoretical models (Activity Theory, CSCW, ...)
- **Case Studies** — Real-world applications of collaborative approaches
- **Datasets** — Pointers to relevant research datasets
- **Resources** — Articles, books, courses, and guides

Every entry is tagged across multiple dimensions: domain, collaboration type, scale, research method, modality, and maturity level.

## Features

- Browsable catalogue with taxonomy-based navigation
- Global site search with instant results and a dedicated search page
- Shareable client-side filters for catalogue and research pages
- Interactive "Find Your Method" decision wizard with shareable results
- Automated validation, build checks, and freshness tracking scripts

## Current Product Status

### Available now

- Global search across catalogue pages, guides, blog, governance pages, and research resources
- Dedicated search page at `/search/`
- Shareable filtered views for catalogue and research pages
- Interactive wizard for finding relevant methods and tools
- Data-driven Hugo build with validation and import scripts

### Planned next

- Side-by-side entry comparison
- Richer wizard scoring and explanations
- Visual exploration components
- External metadata enrichment from research and repository APIs

See [BACKLOG.md](BACKLOG.md) for the current roadmap.

## Contributing

We welcome contributions from researchers and practitioners. See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add or update entries.

All contributions go through a review process by domain editors. See [GOVERNANCE.md](GOVERNANCE.md) for details about our editorial board model.

## Development

### Prerequisites

- [Hugo Extended](https://gohugo.io/installation/) v0.155+ — static site generator
- [Python 3.12+](https://www.python.org/) — for validation and import scripts

#### Installing Hugo (Windows)

```bash
winget install Hugo.Hugo.Extended
```

#### Installing Hugo (macOS / Linux)

```bash
# macOS
brew install hugo

# Linux (Debian/Ubuntu) — see https://gohugo.io/installation/linux/
sudo snap install hugo
```

### Local Development

```bash
# Clone the repository
git clone https://github.com/charoy/collabatlas.git
cd collabatlas

# Install Python dependencies
pip install -r scripts/requirements.txt

# Validate all entries and cross-references
python scripts/validate.py --check-refs

# Run local dev server (with draft content)
hugo server --buildDrafts
```

The site will be available at `http://localhost:1313/collabatlas/`.

You can then test:

- `/search/` for the full search page
- `/catalogue/?domain=education` for shareable catalogue filters
- `/research/?access=open` for shareable research filters

### Importing Research Articles

CollabAtlas supports multiple import methods for research articles:

```bash
# Import by DOI
python scripts/fetch_doi.py 10.1145/175222.175230

# Import from a BibTeX file
python scripts/import_references.py --bibtex refs.bib --enrich

# Import from a RIS file
python scripts/import_references.py --ris export.ris --enrich

# Import by OpenAlex Work ID
python scripts/fetch_doi.py --openalex W54955629

# Batch import from a file of OpenAlex IDs
python scripts/import_references.py --openalex-ids ids.txt

# Enrich existing articles (fill missing abstracts, citations, OpenAlex IDs)
python scripts/fetch_doi.py --enrich-missing

# Look up DOIs for articles that don't have one
python scripts/fetch_doi.py --lookup-doi
```

### Project Structure

```text
data/entries/       # YAML entry files (tools, methods, etc.)
data/taxonomies/    # Taxonomy dimension definitions
data/research-articles.yaml  # Research article references
schemas/            # JSON Schema validation files
content/            # Markdown content pages
layouts/            # Hugo templates
assets/             # CSS and JavaScript
scripts/            # Validation, import, and maintenance scripts
.github/workflows/  # CI/CD (validate, deploy, freshness check)
```

## Deployment

The site is deployed automatically to GitHub Pages via GitHub Actions.

**Setup (one-time):**

1. Go to your repo on GitHub → **Settings** → **Pages**
2. Under **Source**, select **GitHub Actions**
3. Push to `main` — the `deploy.yml` workflow will build and deploy the site

**Workflows:**

- **`validate.yml`** — Runs on PRs: validates entries against JSON schemas and checks cross-references
- **`deploy.yml`** — Runs on push to `main`: validates, builds with Hugo, deploys to GitHub Pages
- **`freshness.yml`** — Monthly: reports stale entries and creates a GitHub issue

The site is published at: [https://charoy.github.io/collabatlas/](https://charoy.github.io/collabatlas/)

## Governance

CollabAtlas is maintained by an editorial board of domain experts. See [GOVERNANCE.md](GOVERNANCE.md) for the full governance model.

## License

Content is licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Code is licensed under MIT.
