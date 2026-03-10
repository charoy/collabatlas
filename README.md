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
- Visual catalogue overview with a lightweight domain × entry type matrix
- Automated validation, build checks, and freshness tracking scripts

## Current Product Status

### Available now

- Global search across catalogue pages, guides, blog, governance pages, and research resources
- Dedicated search page at `/search/`
- Shareable filtered views for catalogue and research pages
- Interactive wizard for finding relevant methods and tools
- Side-by-side comparison for 2–4 catalogue entries
- Visual exploration on the catalogue landing page via a clickable taxonomy matrix
- Data-driven Hugo build with validation and import scripts

### Planned next

- Visual exploration components
- External metadata enrichment beyond the first OpenAlex, Crossref, Zotero, and Zenodo integrations

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

### Importing External Metadata

#### Research articles

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

# Import from a public Zotero library
python scripts/import_references.py --zotero-library groups/123456 --enrich

# Import from a Zotero CSL-JSON export
python scripts/import_references.py --zotero-json zotero-export.json --enrich

# Enrich existing articles (fill missing abstracts, citations, OpenAlex IDs)
python scripts/fetch_doi.py --enrich-missing

# Look up DOIs for articles that don't have one
python scripts/fetch_doi.py --lookup-doi

```

When a DOI is available, enrichment now merges OpenAlex and Crossref metadata,
records the contributing `source_services`, and stores author ORCID profile URLs
when those services expose them.

#### Datasets from Zenodo

Zenodo support is currently available as a maintenance/import script rather than
as a visible site button. It can create a new dataset entry or refresh an
existing one from a Zenodo record ID, DOI, or record URL.

```bash
# Start the interactive Zenodo import assistant
python scripts/fetch_zenodo.py

# Create or refresh a dataset entry from Zenodo
python scripts/fetch_zenodo.py 14839172 --entry-id my-dataset --domains software-engineering --collaboration-types open-source distributed --scales community --modalities remote

# Preview a Zenodo import without writing files
python scripts/fetch_zenodo.py https://doi.org/10.5281/zenodo.14839172 --entry-id my-dataset --dry-run

# List accepted taxonomy IDs before creating a dataset
python scripts/fetch_zenodo.py --list-taxonomies
```

Zenodo imports can create new dataset entries or refresh existing dataset YAML +
content files while preserving CollabAtlas-specific taxonomy and editorial fields.
Running the script with no arguments now starts an interactive assistant that
prompts for the Zenodo identifier, target entry ID, taxonomy mapping, and write
mode.

#### Tools and resources from GitHub

GitHub support is available as an import / enrichment script for tool and
resource entries. It can create a new entry or refresh an existing one from a
repository URL or `owner/repo` identifier.

```bash
# Start the interactive GitHub import assistant
python scripts/fetch_github.py

# Create or refresh a tool entry from GitHub
python scripts/fetch_github.py cli/cli --entry-id github-cli --domains software-engineering --collaboration-types open-source distributed --scales small-team organization --modalities remote

# Create or refresh a resource entry from GitHub
python scripts/fetch_github.py cli/cli --entry-type resource --entry-id github-cli-guide --resource-type tutorial --authors "GitHub CLI Team" --year 2024 --access open --domains software-engineering --collaboration-types open-source distributed --scales small-team organization --modalities remote

# Preview a GitHub import without writing files
python scripts/fetch_github.py cli/cli --entry-id github-cli --dry-run

# List accepted taxonomy IDs before creating a tool or resource entry
python scripts/fetch_github.py --list-taxonomies
```

Running the script with no arguments starts an interactive assistant that
prompts for the repository, entry type, target entry ID, taxonomy mapping, and
final write confirmation. In resource mode, it also asks for resource type,
authors, year, and access level.

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
