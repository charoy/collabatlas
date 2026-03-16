# Phase 1: Stabilization — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Stabilize the CollabAtlas codebase by committing pending work, fixing broken links, adding test coverage for core scripts, integrating monitoring into CI, and cleaning up orphan files.

**Architecture:** No architectural changes. This phase hardens the existing Hugo + Python pipeline: atomic commits for in-flight work, pytest coverage for validation/enrichment scripts, CI workflow additions for link checking and build monitoring.

**Tech Stack:** Hugo, Python 3.12, pytest, GitHub Actions, YAML, JSON Schema

---

## Task 1: Commit pending work as atomic commits

**Context:** 14 modified files and 5 untracked files sit uncommitted. They represent multiple logical features (search refactor, pagination, comparison, visualization enhancements, research article enrichment, schema updates). These must be split into coherent commits.

**Files:**
- All modified and untracked files per `git status`

**Step 1: Create commit — Search index externalization**

These files refactored search from inline DOM parsing to async JSON fetch:

```bash
git add layouts/home.json assets/js/site-search.js assets/js/search-page.js layouts/_default/baseof.html
git commit -m "feat(search): externalize search index to /index.json with async loading

Replace inline DOM-based search index with external JSON endpoint.
site-search.js now lazy-loads index via fetch() on first interaction.
search-page.js updated for the new index format.
baseof.html simplified by removing inline search data."
```

**Step 2: Create commit — Pagination and list layout improvements**

```bash
git add layouts/partials/pagination.html layouts/_default/list.html layouts/blog/list.html layouts/catalogue/section.html
git commit -m "feat(layout): add pagination partial and update list templates

New reusable pagination.html partial with prev/next and page info.
Updated list, blog, and catalogue section templates to use it."
```

**Step 3: Create commit — Comparison feature data partial**

```bash
git add layouts/partials/compare-data.html
git commit -m "feat(compare): add comparison data partial for client-side filtering

New partial generates JSON catalogue data for side-by-side comparison."
```

**Step 4: Create commit — Visualization enhancements**

```bash
git add assets/js/catalogue-visualize.js layouts/catalogue/visualize.html
git commit -m "feat(visualize): enhance interactive visualization with distribution charts"
```

**Step 5: Create commit — CSS improvements**

```bash
git add assets/css/main.css
git commit -m "style: add styles for pagination, comparison dock, and visualization matrix"
```

**Step 6: Create commit — Schema and data updates**

```bash
git add schemas/dataset.schema.json schemas/resource.schema.json data/research_articles.yaml
git commit -m "feat(data): add metrics fields to schemas and enrich research articles

Add stars/forks/open_issues/last_commit to dataset and resource schemas.
Enrich research articles with ORCID IDs, source services, and fetched_at."
```

**Step 7: Create commit — Hugo config update**

```bash
git add hugo.toml
git commit -m "chore: update Hugo configuration"
```

**Step 8: Create commit — Backlog update**

```bash
git add BACKLOG.md
git commit -m "docs: mark completed features in backlog (comparison, visualization, scaling stage 1)"
```

**Step 9: Create commit — Build monitor script**

```bash
git add scripts/monitor_build_size.py
git commit -m "feat(scripts): add build size monitoring with threshold warnings"
```

**Step 10: Remove orphan debug file**

```bash
rm css_dump.txt
```

**Step 11: Run validation to confirm nothing broke**

Run: `python scripts/validate.py --check-refs`
Expected: `0 error(s)` — All entries valid.

---

## Task 2: Fix broken external links

**Context:** `check-links.py` found 10 broken links. Some are genuine 404s to fix, others are 403s from servers blocking automated requests (DOI resolvers, publisher sites). We must distinguish and fix what we can.

**Files:**
- Modify: `data/entries/frameworks/open-innovation.yaml`
- Modify: `data/entries/frameworks/practice-based-computing.yaml`
- Modify: `data/entries/frameworks/socio-technical-systems.yaml`
- Modify: `data/entries/methods/action-research.yaml`
- Modify: `data/entries/methods/participatory-design.yaml`
- Modify: `data/entries/methods/world-cafe.yaml`
- Modify: `data/entries/resources/collaboration-in-the-cloud.yaml`
- Modify: `data/entries/resources/working-together.yaml`
- Modify: `data/entries/tools/google-docs.yaml`

**Step 1: Triage broken links**

Classify each link:
- **403 from DOI resolvers** (doi.org): These are false positives — DOI resolvers block bots. Keep these links, they work in browsers. Affected:
  - `practice-based-computing.yaml` — `https://doi.org/10.1093/oso/9780198733249.001.0001`
  - `socio-technical-systems.yaml` — `https://doi.org/10.1177/001872676501800106`
  - `action-research.yaml` — `https://doi.org/10.1177/1476750306070101`
  - `participatory-design.yaml` — `https://doi.org/10.1145/142750.142769`
- **403 from publisher sites**: Likely bot blocking too. Verify manually:
  - `open-innovation.yaml` — `https://www.hbs.edu/faculty/Pages/item.aspx?num=13798`
- **Genuine 404s** — need replacement URLs:
  - `practice-based-computing.yaml` — `https://doi.org/10.1007/978-3-319-58551-0`
  - `collaboration-in-the-cloud.yaml` — `https://www.wiley.com/...`
  - `working-together.yaml` — `https://www.morganclaypoolpublishers.com/olson/`
  - `google-docs.yaml` — `https://support.google.com/docs`
- **Timeout**:
  - `world-cafe.yaml` — `http://www.theworldcafe.com/`

**Step 2: Fix genuine 404 links**

For each 404, search for the correct current URL:
- `google-docs.yaml`: Replace `https://support.google.com/docs` with `https://support.google.com/a/users/answer/9300503`
- `collaboration-in-the-cloud.yaml`: Search for current Wiley book page or use an alternative like the publisher's ISBN lookup
- `working-together.yaml`: Morgan & Claypool was acquired by Springer — find new URL
- `practice-based-computing.yaml` (Springer 404): Verify DOI and fix
- `world-cafe.yaml`: Update to `https://theworldcafe.com/` (HTTPS, no www)

**Step 3: Update check-links.py to reduce false positives**

Add a browser-like User-Agent and skip known DOI resolver 403s:

Modify: `scripts/check-links.py`

Add after imports:
```python
# DOI resolvers and publisher sites that block automated requests
SKIP_DOMAINS = {"doi.org", "dx.doi.org"}
```

In the `check_url` function, before the request:
```python
from urllib.parse import urlparse
if urlparse(url).hostname in SKIP_DOMAINS:
    return url, "SKIPPED (DOI)", source
```

Update the User-Agent:
```python
headers = {
    "User-Agent": "Mozilla/5.0 (compatible; CollabAtlas-LinkChecker/1.0)"
}
```

**Step 4: Run check-links.py again and verify**

Run: `python scripts/check-links.py`
Expected: Only genuine issues remain (the ones we chose to keep or couldn't resolve).

**Step 5: Commit**

```bash
git add data/entries/ scripts/check-links.py
git commit -m "fix: update broken external links and improve link checker

Fix 404s in google-docs, collaboration-in-the-cloud, working-together,
practice-based-computing, and world-cafe entries.
Skip DOI resolver domains in link checker (403 false positives)."
```

---

## Task 3: Add pytest infrastructure and tests for validate.py

**Context:** Only `test_issue_to_entry.py` (unittest) exists. No tests for the core validation pipeline. Adding pytest with fixtures for validate.py ensures schema and taxonomy validation don't regress.

**Files:**
- Create: `scripts/conftest.py`
- Create: `scripts/test_validate.py`
- Modify: `scripts/requirements.txt` (add pytest)

**Step 1: Add pytest to requirements**

Modify: `scripts/requirements.txt`

Add line:
```
pytest>=8.0.0
```

**Step 2: Install dependencies**

Run: `pip install -r scripts/requirements.txt`

**Step 3: Write test fixtures in conftest.py**

Create: `scripts/conftest.py`

```python
"""Shared pytest fixtures for CollabAtlas script tests."""

import json
import tempfile
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def tmp_project(tmp_path):
    """Create a minimal project structure for validation tests."""
    # Schemas
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()

    # Taxonomies
    tax_dir = tmp_path / "data" / "taxonomies"
    tax_dir.mkdir(parents=True)

    domains = [{"id": "software-engineering", "title": "Software Engineering"},
               {"id": "education", "title": "Education"}]
    collab_types = [{"id": "co-design", "title": "Co-Design"},
                    {"id": "open-source", "title": "Open Source"}]
    scales = [{"id": "pair", "title": "Pair"},
              {"id": "small-team", "title": "Small Team"},
              {"id": "community", "title": "Community"}]
    modalities = [{"id": "remote", "title": "Remote"},
                  {"id": "hybrid", "title": "Hybrid"}]
    maturity = [{"id": "emerging", "title": "Emerging"},
                {"id": "well-documented", "title": "Well-Documented"}]
    research_methods = [{"id": "case-study", "title": "Case Study"}]

    for name, data in [("domains", domains), ("collaboration_types", collab_types),
                       ("scales", scales), ("modalities", modalities),
                       ("maturity_levels", maturity), ("research_methods", research_methods)]:
        (tax_dir / f"{name}.yaml").write_text(yaml.dump(data), encoding="utf-8")

    # Entries directory
    (tmp_path / "data" / "entries" / "tools").mkdir(parents=True)
    (tmp_path / "data" / "entries" / "methods").mkdir(parents=True)

    return tmp_path


@pytest.fixture
def valid_tool_entry():
    """A minimal valid tool entry."""
    return {
        "id": "test-tool",
        "type": "tool",
        "title": "Test Tool",
        "tagline": "A test tool for validation",
        "description": "A longer description of the test tool used for validation testing.",
        "domains": ["software-engineering"],
        "collaboration-types": ["open-source"],
        "scales": ["small-team"],
        "modalities": ["remote"],
        "maturity": "well-documented",
        "status": "published",
        "contributors": ["collabatlas-team"],
    }
```

**Step 4: Run conftest to verify it loads**

Run: `cd scripts && python -m pytest --collect-only 2>&1 | head -5`
Expected: Fixtures are collected without errors.

**Step 5: Write validation tests**

Create: `scripts/test_validate.py`

```python
"""Tests for validate.py — CollabAtlas schema and taxonomy validation."""

import json
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from validate import load_taxonomy_values, validate_entry, check_references


class TestLoadTaxonomyValues:
    """Tests for taxonomy loading."""

    def test_loads_all_taxonomies(self, tmp_project):
        """Should load all taxonomy files from the taxonomies directory."""
        tax_dir = tmp_project / "data" / "taxonomies"
        # Monkey-patch the module constant
        import validate
        original = validate.TAXONOMIES_DIR
        validate.TAXONOMIES_DIR = tax_dir
        try:
            result = load_taxonomy_values()
            assert "domains" in result
            assert "software-engineering" in result["domains"]
            assert "scales" in result
            assert "modalities" in result
        finally:
            validate.TAXONOMIES_DIR = original


class TestValidateEntry:
    """Tests for single entry validation."""

    def test_valid_entry_passes(self, tmp_project, valid_tool_entry):
        """A well-formed entry should produce no errors."""
        schema_file = tmp_project / "schemas" / "tool.schema.json"
        # Copy real schema
        real_schema = Path(__file__).resolve().parent.parent / "schemas" / "tool.schema.json"
        schema = json.loads(real_schema.read_text(encoding="utf-8"))
        schema_file.write_text(json.dumps(schema), encoding="utf-8")

        entry_file = tmp_project / "data" / "entries" / "tools" / "test-tool.yaml"
        entry_file.write_text(yaml.dump(valid_tool_entry), encoding="utf-8")

        tax_dir = tmp_project / "data" / "taxonomies"
        import validate
        original = validate.TAXONOMIES_DIR
        validate.TAXONOMIES_DIR = tax_dir
        try:
            taxonomies = load_taxonomy_values()
            errors = validate_entry(entry_file, schema, taxonomies)
            assert errors == []
        finally:
            validate.TAXONOMIES_DIR = original

    def test_missing_required_field(self, tmp_project, valid_tool_entry):
        """Missing a required field should produce a schema error."""
        real_schema = Path(__file__).resolve().parent.parent / "schemas" / "tool.schema.json"
        schema = json.loads(real_schema.read_text(encoding="utf-8"))

        bad_entry = {k: v for k, v in valid_tool_entry.items() if k != "title"}
        entry_file = tmp_project / "data" / "entries" / "tools" / "bad.yaml"
        entry_file.write_text(yaml.dump(bad_entry), encoding="utf-8")

        tax_dir = tmp_project / "data" / "taxonomies"
        import validate
        original = validate.TAXONOMIES_DIR
        validate.TAXONOMIES_DIR = tax_dir
        try:
            taxonomies = load_taxonomy_values()
            errors = validate_entry(entry_file, schema, taxonomies)
            assert len(errors) > 0
            assert any("title" in e for e in errors)
        finally:
            validate.TAXONOMIES_DIR = original

    def test_invalid_taxonomy_value(self, tmp_project, valid_tool_entry):
        """An invalid taxonomy value should be caught."""
        real_schema = Path(__file__).resolve().parent.parent / "schemas" / "tool.schema.json"
        schema = json.loads(real_schema.read_text(encoding="utf-8"))

        bad_entry = {**valid_tool_entry, "domains": ["nonexistent-domain"]}
        entry_file = tmp_project / "data" / "entries" / "tools" / "bad-tax.yaml"
        entry_file.write_text(yaml.dump(bad_entry), encoding="utf-8")

        tax_dir = tmp_project / "data" / "taxonomies"
        import validate
        original = validate.TAXONOMIES_DIR
        validate.TAXONOMIES_DIR = tax_dir
        try:
            taxonomies = load_taxonomy_values()
            errors = validate_entry(entry_file, schema, taxonomies)
            assert len(errors) > 0
            assert any("nonexistent-domain" in e for e in errors)
        finally:
            validate.TAXONOMIES_DIR = original

    def test_empty_file(self, tmp_project):
        """An empty YAML file should produce an error."""
        entry_file = tmp_project / "data" / "entries" / "tools" / "empty.yaml"
        entry_file.write_text("", encoding="utf-8")

        errors = validate_entry(entry_file, None, {})
        assert errors == ["File is empty"]

    def test_invalid_yaml(self, tmp_project):
        """Malformed YAML should produce a parse error."""
        entry_file = tmp_project / "data" / "entries" / "tools" / "broken.yaml"
        entry_file.write_text("key: [unclosed", encoding="utf-8")

        errors = validate_entry(entry_file, None, {})
        assert len(errors) > 0
        assert any("YAML parse error" in e for e in errors)


class TestCheckReferences:
    """Tests for cross-reference validation."""

    def test_valid_references(self):
        """Valid cross-references should produce no errors."""
        entries = {
            "tool-a": {"related_entries": ["tool-b"]},
            "tool-b": {"related_entries": ["tool-a"]},
        }
        errors = check_references(entries)
        assert errors == []

    def test_broken_reference(self):
        """A reference to a nonexistent entry should produce an error."""
        entries = {
            "tool-a": {"related_entries": ["nonexistent"]},
        }
        errors = check_references(entries)
        assert len(errors) == 1
        assert "nonexistent" in errors[0]

    def test_broken_tools_used(self):
        """A tools_used reference to a nonexistent entry should error."""
        entries = {
            "case-a": {"tools_used": ["missing-tool"]},
        }
        errors = check_references(entries)
        assert len(errors) == 1
        assert "missing-tool" in errors[0]
```

**Step 6: Run tests**

Run: `cd scripts && python -m pytest test_validate.py -v`
Expected: All tests pass.

**Step 7: Commit**

```bash
git add scripts/conftest.py scripts/test_validate.py scripts/requirements.txt
git commit -m "test: add pytest infrastructure and validation tests

Add conftest.py with shared fixtures (tmp_project, valid_tool_entry).
Add test_validate.py covering:
- Taxonomy loading
- Valid entry passes
- Missing required field detection
- Invalid taxonomy value detection
- Empty file handling
- Malformed YAML handling
- Cross-reference validation (valid, broken, tools_used)
Add pytest to requirements.txt."
```

---

## Task 4: Add tests for enrich_catalogue.py

**Context:** The enrichment script fetches GitHub metrics and updates YAML files. Testing it requires mocking HTTP calls. Focus on the YAML update logic, not the API calls.

**Files:**
- Create: `scripts/test_enrich.py`

**Step 1: Read enrich_catalogue.py to understand testable units**

Read: `scripts/enrich_catalogue.py` — identify pure functions (YAML merging, slug extraction, metric parsing).

**Step 2: Write tests for testable units**

Create: `scripts/test_enrich.py`

Test the functions that don't require network access:
- Extracting GitHub repo slug from URLs
- Merging metrics into existing YAML data
- Handling missing/malformed github_repo fields

Exact test code depends on Step 1 findings — write tests after reading the source.

**Step 3: Run tests**

Run: `cd scripts && python -m pytest test_enrich.py -v`
Expected: All tests pass.

**Step 4: Commit**

```bash
git add scripts/test_enrich.py
git commit -m "test: add unit tests for catalogue enrichment script"
```

---

## Task 5: Integrate monitor_build_size.py into CI

**Context:** The script exists but isn't in any workflow. It should run after `hugo --minify` in deploy.yml to warn about bloating assets.

**Files:**
- Modify: `.github/workflows/deploy.yml`

**Step 1: Read current deploy.yml**

Read: `.github/workflows/deploy.yml` — find the step after `hugo --minify`.

**Step 2: Add monitoring step**

Add a new step after the Hugo build step:

```yaml
      - name: Monitor build size
        run: python scripts/monitor_build_size.py
```

This should be a non-blocking warning (the script prints warnings but doesn't exit 1 by default).

**Step 3: Verify monitor script exit codes**

Read: `scripts/monitor_build_size.py` — check if it exits with code 0 on warnings. If it exits non-zero on warnings, adjust to only fail on critical thresholds.

**Step 4: Commit**

```bash
git add .github/workflows/deploy.yml
git commit -m "ci: add build size monitoring to deploy workflow

Run monitor_build_size.py after hugo build to detect asset bloat.
Warns on search index >2MB, CSS >150KB, JS >50KB."
```

---

## Task 6: Integrate check-links.py into CI (weekly schedule)

**Context:** Link checking is slow (network-bound) and shouldn't block deploys. Add it as a scheduled weekly workflow.

**Files:**
- Create: `.github/workflows/check-links.yml`

**Step 1: Create the workflow**

Create: `.github/workflows/check-links.yml`

```yaml
name: Check External Links

on:
  schedule:
    - cron: "0 6 * * 1"  # Every Monday at 6 UTC
  workflow_dispatch:

jobs:
  check-links:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install -r scripts/requirements.txt

      - name: Check external links
        run: python scripts/check-links.py 2>&1 | tee link-report.txt

      - name: Create issue if broken links found
        if: failure()
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('link-report.txt', 'utf8');
            await github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: 'Broken external links detected',
              body: `## Weekly Link Check Report\n\n\`\`\`\n${report}\n\`\`\`\n\nPlease review and update broken links.`,
              labels: ['maintenance']
            });
```

**Step 2: Verify check-links.py exit code on broken links**

Read: `scripts/check-links.py` — ensure it exits with code 1 when broken links are found (needed for the `if: failure()` condition).

**Step 3: Commit**

```bash
git add .github/workflows/check-links.yml
git commit -m "ci: add weekly link checking workflow

Runs check-links.py every Monday at 6 UTC.
Creates GitHub issue with report if broken links found."
```

---

## Task 7: Add tests to CI workflow

**Context:** Tests exist but aren't run in CI. Add pytest to the validate workflow.

**Files:**
- Modify: `.github/workflows/validate.yml`

**Step 1: Add test step to validate workflow**

Add after the existing validation steps:

```yaml
      - name: Run tests
        run: cd scripts && python -m pytest -v
```

**Step 2: Commit**

```bash
git add .github/workflows/validate.yml
git commit -m "ci: run pytest in validation workflow"
```

---

## Task 8: Final validation pass

**Step 1: Run full validation**

Run: `python scripts/validate.py --check-refs`
Expected: 0 errors.

**Step 2: Run all tests**

Run: `cd scripts && python -m pytest -v`
Expected: All tests pass.

**Step 3: Build the site**

Run: `hugo --minify`
Expected: Clean build, no errors.

**Step 4: Run build monitor**

Run: `python scripts/monitor_build_size.py`
Expected: All sizes under thresholds.

**Step 5: Verify git status is clean**

Run: `git status`
Expected: Nothing to commit, working tree clean.

---

## Summary

| Task | What | Commits |
|------|------|---------|
| 1 | Commit pending work (9 atomic commits) | 9 |
| 2 | Fix broken links + improve checker | 1 |
| 3 | pytest infra + validate.py tests | 1 |
| 4 | enrich_catalogue.py tests | 1 |
| 5 | Build monitor in CI | 1 |
| 6 | Link checker in CI (weekly) | 1 |
| 7 | Tests in CI | 1 |
| 8 | Final validation pass | 0 |
| **Total** | | **15 commits** |
