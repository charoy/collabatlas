#!/usr/bin/env python3
"""Parse a GitHub issue form body and generate CollabAtlas catalogue entry files.

This script is invoked by a GitHub Action when an issue is opened with the
``new-entry`` or ``article`` label.  It reads the Markdown body produced by
a GitHub Issue Form, maps human-readable labels to taxonomy IDs, and writes:

* A YAML data file in ``data/entries/{type_dir}/{id}.yaml``
* A Markdown content file in ``content/catalogue/{type_dir}/{id}.md``

For articles (``article`` label) it appends to ``data/research_articles.yaml``.

Environment variables (set by the calling GitHub Action):
    ISSUE_BODY      Full Markdown body of the issue
    ISSUE_TITLE     Issue title (e.g. "[New Tool] My Cool Tool")
    ISSUE_NUMBER    Issue number
    ISSUE_AUTHOR    GitHub username of the issue author
    ISSUE_LABELS    Comma-separated labels (e.g. "new-entry,tool,triage")
"""

from __future__ import annotations

import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

import yaml

# Import shared parsing utilities
from issue_parser import (
    ACCESS_MAP,
    COLLAB_TYPE_MAP,
    DOMAIN_MAP,
    MATURITY_MAP,
    MODALITY_MAP,
    PLATFORM_MAP,
    RESEARCH_METHOD_MAP,
    RESOURCE_TYPE_MAP,
    SCALE_MAP,
    TYPE_DIRS,
    VALID_TYPES,
    detect_entry_type,
    extract_clean_title,
    get_bool,
    get_checkboxes,
    get_comma_list,
    get_dropdown,
    get_external_links,
    get_int,
    get_lines_as_list,
    get_seminal_works,
    get_text,
    is_empty,
    parse_issue_body,
    title_to_id,
)

# ---------------------------------------------------------------------------
# Custom YAML dumper — match existing entry style (2-space list indentation)
# ---------------------------------------------------------------------------


class _IndentedDumper(yaml.SafeDumper):
    """A YAML dumper that indents list items with 2 spaces under their parent key.

    Default pyyaml produces::

        domains:
        - foo

    This dumper produces the style used in existing entries::

        domains:
          - foo
    """

    def increase_indent(self, flow: bool = False, indentless: bool = False) -> None:  # type: ignore[override]
        """Override to never use indentless sequences."""
        return super().increase_indent(flow, False)


def _str_representer(dumper: yaml.Dumper, data: str) -> yaml.ScalarNode:
    """Use block style (``>``) for multi-line strings, plain style otherwise."""
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=">")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


_IndentedDumper.add_representer(str, _str_representer)


def _yaml_dump(data: Any, stream: Any) -> None:
    """Dump *data* to *stream* with the project's canonical YAML style."""
    yaml.dump(
        data,
        stream,
        Dumper=_IndentedDumper,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        indent=2,
    )


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "entries"
CONTENT_DIR = ROOT / "content" / "catalogue"
ARTICLES_FILE = ROOT / "data" / "research_articles.yaml"


# ---------------------------------------------------------------------------
# Article ID helper (not shared — specific to entry generation)
# ---------------------------------------------------------------------------


def article_author_year_id(authors: str | None, year: int | None) -> str:
    """Generate an article ID in ``author-year`` format."""
    first_author = (authors or "unknown").split(",")[0].strip().split()[-1].lower()
    first_author = re.sub(r"[^a-z0-9]", "", first_author)
    yr = year if year else "xxxx"
    return f"{first_author}-{yr}"


# ---------------------------------------------------------------------------
# YAML data file builder (per type)
# ---------------------------------------------------------------------------


def build_common_fields(
    entry_id: str,
    entry_type: str,
    sections: dict[str, str],
    author: str,
) -> dict[str, Any]:
    """Build fields shared across all catalogue entry types."""
    today = date.today().isoformat()

    data: dict[str, Any] = {}
    data["id"] = entry_id
    data["type"] = entry_type

    title = get_text(sections, "Title")
    data["title"] = title or entry_id

    tagline = get_text(sections, "Tagline")
    if tagline:
        data["tagline"] = tagline

    description = get_text(sections, "Full Description")
    if description:
        data["description"] = description

    domains = get_checkboxes(sections, "Relevant Domains (select all that apply)", DOMAIN_MAP)
    if domains:
        data["domains"] = domains

    collab_types = get_checkboxes(
        sections, "Collaboration Types (select all that apply)", COLLAB_TYPE_MAP
    )
    if collab_types:
        data["collaboration-types"] = collab_types

    scale = get_checkboxes(sections, "Scale (select all that apply)", SCALE_MAP)
    if scale:
        data["scales"] = scale

    modality = get_checkboxes(sections, "Modality (select all that apply)", MODALITY_MAP)
    if modality:
        data["modalities"] = modality

    maturity = get_dropdown(sections, "Maturity Level", MATURITY_MAP)
    if maturity:
        data["maturity"] = maturity

    data["status"] = "draft"

    data["contributors"] = [author]
    data["created"] = today
    data["last_reviewed"] = today

    return data


PLATFORM_CANONICAL: dict[str, str] = {
    "windows": "Windows",
    "macos": "macOS",
    "linux": "Linux",
    "android": "Android",
    "ios": "iOS",
    "web": "Web",
    "chromeos": "ChromeOS",
}


def normalize_platform(name: str) -> str:
    """Normalize platform name to canonical casing (e.g. 'windows' → 'Windows')."""
    return PLATFORM_CANONICAL.get(name.lower().strip(), name.strip())


def add_tool_fields(data: dict[str, Any], sections: dict[str, str]) -> None:
    """Add tool-specific fields."""
    website_url = get_text(sections, "Website URL")
    if website_url:
        data["website_url"] = website_url

    license_val = get_text(sections, "License")
    if license_val:
        data["license"] = license_val

    open_source = get_bool(sections, "Is it open source?")
    if open_source is not None:
        data["open_source"] = open_source

    platforms = get_comma_list(sections, "Supported Platforms (comma-separated)")
    if platforms:
        data["supported_platforms"] = [normalize_platform(p) for p in platforms]


def add_method_fields(data: dict[str, Any], sections: dict[str, str]) -> None:
    """Add method-specific fields."""
    research_methods = get_checkboxes(
        sections, "Associated Research Methods", RESEARCH_METHOD_MAP
    )
    if research_methods:
        data["research_method"] = research_methods

    steps = get_lines_as_list(sections, "Method Steps (one per line)")
    if steps:
        data["steps"] = steps

    when_to_use = get_text(sections, "When to Use")
    if when_to_use:
        data["when_to_use"] = when_to_use

    limitations = get_text(sections, "Limitations")
    if limitations:
        data["limitations"] = limitations


def add_framework_fields(data: dict[str, Any], sections: dict[str, str]) -> None:
    """Add framework-specific fields."""
    research_methods = get_checkboxes(
        sections, "Associated Research Methods", RESEARCH_METHOD_MAP
    )
    if research_methods:
        data["research_method"] = research_methods

    key_concepts = get_comma_list(sections, "Key Concepts (comma-separated)")
    if key_concepts:
        data["key_concepts"] = key_concepts

    seminal_works = get_seminal_works(sections, "Seminal Works")
    if seminal_works:
        data["seminal_works"] = seminal_works

    limitations = get_text(sections, "Limitations")
    if limitations:
        data["limitations"] = limitations


def add_case_study_fields(data: dict[str, Any], sections: dict[str, str]) -> None:
    """Add case-study-specific fields."""
    research_methods = get_checkboxes(
        sections, "Associated Research Methods", RESEARCH_METHOD_MAP
    )
    if research_methods:
        data["research_method"] = research_methods

    organization = get_text(sections, "Organization")
    if organization:
        data["organization"] = organization

    year = get_int(sections, "Year")
    if year:
        data["year"] = year

    outcomes = get_text(sections, "Outcomes")
    if outcomes:
        data["outcomes"] = outcomes

    key_concepts = get_comma_list(sections, "Key Concepts (comma-separated)")
    if key_concepts:
        data["key_concepts"] = key_concepts

    methods_used = get_comma_list(sections, "Methods Used (CollabAtlas IDs, comma-separated)")
    if methods_used:
        data["methods_used"] = methods_used

    tools_used = get_comma_list(sections, "Tools Used (CollabAtlas IDs, comma-separated)")
    if tools_used:
        data["tools_used"] = tools_used


def add_dataset_fields(data: dict[str, Any], sections: dict[str, str]) -> None:
    """Add dataset-specific fields."""
    source_url = get_text(sections, "Source URL")
    if source_url:
        data["source_url"] = source_url

    platform = get_dropdown(sections, "Hosting Platform", PLATFORM_MAP)
    if platform:
        data["platform"] = platform

    platform_id = get_text(sections, "Platform Identifier")
    if platform_id:
        data["platform_id"] = platform_id

    fmt = get_text(sections, "Data Format")
    if fmt:
        data["format"] = fmt

    size = get_text(sections, "Dataset Size")
    if size:
        data["size"] = size

    license_val = get_text(sections, "License")
    if license_val:
        data["license"] = license_val

    temporal = get_text(sections, "Temporal Coverage")
    if temporal:
        data["temporal_coverage"] = temporal


def add_resource_fields(data: dict[str, Any], sections: dict[str, str]) -> None:
    """Add resource-specific fields."""
    resource_type = get_dropdown(sections, "Resource Type", RESOURCE_TYPE_MAP)
    if resource_type:
        data["resource_type"] = resource_type

    authors = get_comma_list(sections, "Authors (comma-separated)")
    if authors:
        data["authors"] = authors

    year = get_int(sections, "Publication Year")
    if year:
        data["year"] = year

    doi = get_text(sections, "DOI (if available)")
    if doi:
        data["doi"] = doi

    access = get_dropdown(sections, "Access Level", ACCESS_MAP)
    if access:
        data["access"] = access


def _parse_titled_links(sections: dict[str, str], label: str) -> list[dict[str, str]]:
    """Parse lines formatted as 'Title | URL' into a list of dicts."""
    raw = get_text(sections, label) or ""
    result: list[dict[str, str]] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        if "|" in line:
            parts = line.split("|", 1)
            result.append({"title": parts[0].strip(), "url": parts[1].strip()})
        elif line.startswith("http"):
            result.append({"title": line, "url": line})
    return result


def add_research_case_fields(data: dict[str, Any], sections: dict[str, str]) -> None:
    """Add research-case-specific fields."""
    researcher_name = get_text(sections, "Researcher Name")
    researcher_role = get_text(sections, "Researcher Role")
    supervisors = get_lines_as_list(sections, "Supervisors")

    researcher: dict[str, Any] = {}
    if researcher_name:
        researcher["name"] = researcher_name
    if researcher_role:
        researcher["role"] = researcher_role
    if supervisors:
        researcher["supervisors"] = supervisors
    if researcher:
        data["researcher"] = researcher

    studied_domain = get_text(sections, "Studied Domain")
    if studied_domain:
        data["studied_domain"] = studied_domain

    methodologies = get_text(sections, "Research / Design Methodologies")
    if methodologies:
        data["research_methodologies"] = methodologies

    practices = get_text(sections, "Observed / Supported Practices")
    if practices:
        data["observed_practices"] = practices

    artefacts = get_text(sections, "Observed Artefacts in Use / Designed Artefacts")
    if artefacts:
        data["observed_artefacts"] = artefacts

    issues_org = get_text(sections, "Identified Organizational Issues")
    if issues_org:
        data["issues_organizational"] = issues_org

    issues_tech = get_text(sections, "Identified Technical Issues")
    if issues_tech:
        data["issues_technical"] = issues_tech

    issues_gov = get_text(sections, "Identified Governance Issues")
    if issues_gov:
        data["issues_governance"] = issues_gov

    issues_pol = get_text(sections, "Identified Policy Issues")
    if issues_pol:
        data["issues_policy"] = issues_pol

    publications = _parse_titled_links(sections, "Publications")
    if publications:
        data["publications"] = publications

    datasets = _parse_titled_links(sections, "Datasets")
    if datasets:
        data["datasets"] = datasets

    software = _parse_titled_links(sections, "Software")
    if software:
        data["software"] = software


TYPE_FIELD_HANDLERS: dict[str, Any] = {
    "tool": add_tool_fields,
    "method": add_method_fields,
    "framework": add_framework_fields,
    "case-study": add_case_study_fields,
    "dataset": add_dataset_fields,
    "resource": add_resource_fields,
    "research-case": add_research_case_fields,
}


def add_trailing_common_fields(
    data: dict[str, Any], sections: dict[str, str]
) -> None:
    """Add fields that appear after the type-specific block (links, tags, etc.)."""
    external_links = get_external_links(sections, "External Links")
    if external_links:
        data["external_links"] = external_links

    related = get_comma_list(sections, "Related CollabAtlas Entries (comma-separated IDs)")
    if related:
        data["related_entries"] = [title_to_id(r) for r in related]

    tags = get_comma_list(sections, "Tags (comma-separated)")
    if tags:
        data["tags"] = tags


# ---------------------------------------------------------------------------
# Markdown front matter builder
# ---------------------------------------------------------------------------


def _flow_list(items: list[str]) -> str:
    """Format a list as compact YAML flow style: ``["a", "b"]``."""
    inner = ", ".join(f'"{item}"' for item in items)
    return f"[{inner}]"


def build_frontmatter(data: dict[str, Any]) -> str:
    """Build Hugo-compatible Markdown front matter from the YAML data dict."""
    lines: list[str] = ["---"]
    lines.append(f'title: "{data.get("title", "")}"')
    if data.get("type") == "research-case":
        lines.append('type: "research-case"')
    lines.append(f'tagline: "{data.get("tagline", "")}"')
    lines.append(f'data_id: "{data["id"]}"')

    for field in ("domains", "collaboration-types", "scales", "modalities"):
        value = data.get(field, [])
        if value:
            lines.append(f"{field}: {_flow_list(value)}")

    maturity = data.get("maturity", "")
    if maturity:
        lines.append(f'maturity: "{maturity}"')

    lines.append(f'status: "{data.get("status", "draft")}"')

    # Include dataset platform in frontmatter (matches existing pattern)
    if data.get("type") == "dataset" and data.get("platform"):
        lines.append(f'platform: "{data["platform"]}"')

    lines.append("---")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# File writers
# ---------------------------------------------------------------------------


def write_yaml_entry(data: dict[str, Any], entry_type: str) -> Path:
    """Write the YAML data file and return its path."""
    type_dir = TYPE_DIRS[entry_type]
    out_dir = DATA_DIR / type_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"{data['id']}.yaml"
    with open(out_path, "w", encoding="utf-8") as f:
        _yaml_dump(data, f)
    print(f"  Created: {out_path.relative_to(ROOT)}")
    return out_path


def write_markdown_entry(data: dict[str, Any], entry_type: str) -> Path:
    """Write the Markdown content file and return its path."""
    type_dir = TYPE_DIRS[entry_type]
    # Research cases live outside the catalogue at content/research-cases/
    if entry_type == "research-case":
        out_dir = ROOT / "content" / "research-cases"
    else:
        out_dir = CONTENT_DIR / type_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"{data['id']}.md"
    frontmatter = build_frontmatter(data)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(frontmatter)
    print(f"  Created: {out_path.relative_to(ROOT)}")
    return out_path


# ---------------------------------------------------------------------------
# Article handling
# ---------------------------------------------------------------------------


def handle_article(sections: dict[str, str], author: str) -> tuple[str, str]:
    """Parse article fields, append to research_articles.yaml, return (id, type)."""
    title = get_text(sections, "Article Title")
    doi = get_text(sections, "DOI")
    authors = get_text(sections, "Authors")
    year = get_int(sections, "Year")
    journal = get_text(sections, "Journal / Conference")
    access_raw = get_text(sections, "Access Type")
    abstract = get_text(sections, "Abstract (optional)")

    # Map access type
    access = ACCESS_MAP.get(access_raw, access_raw) if access_raw else None

    # Domains from checkboxes or comma-separated suggestions
    domains = get_checkboxes(sections, "Suggested Domains", DOMAIN_MAP)
    if not domains:
        # Fallback: comma-separated domain IDs
        domains = get_comma_list(sections, "Suggested Domains")

    tags = get_comma_list(sections, "Suggested Tags")
    related = get_comma_list(sections, "Related CollabAtlas Entries (comma-separated IDs)")
    if not related:
        related = get_comma_list(sections, "Related CollabAtlas Entries")

    # Build the article entry
    article: dict[str, Any] = {}
    if title:
        article["title"] = title
    if authors:
        article["authors"] = authors
    if journal:
        article["journal"] = journal
    if year:
        article["year"] = year
    if doi:
        article["doi"] = doi
        article["url"] = f"https://doi.org/{doi}"
    if access:
        article["access"] = access
    if abstract:
        article["abstract"] = abstract

    # Generate ID
    article_id = article_author_year_id(authors, year)

    # Load existing articles and check for duplicates
    existing_articles: list[dict[str, Any]] = []
    if ARTICLES_FILE.exists():
        with open(ARTICLES_FILE, encoding="utf-8") as f:
            existing_articles = yaml.safe_load(f) or []

    existing_ids = {a.get("id") for a in existing_articles}

    # Deduplicate the ID
    base_id = article_id
    counter = 2
    while article_id in existing_ids:
        article_id = f"{base_id}-{counter}"
        counter += 1

    article["id"] = article_id

    if domains:
        article["domains"] = domains
    if tags:
        article["tags"] = tags
    if related:
        article["related_entries"] = related

    # Append and save
    existing_articles.append(article)
    ARTICLES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ARTICLES_FILE, "w", encoding="utf-8") as f:
        _yaml_dump(existing_articles, f)
    print(f"  Appended article '{article_id}' to {ARTICLES_FILE.relative_to(ROOT)}")

    return article_id, "research-article"


# ---------------------------------------------------------------------------
# Blog post handling
# ---------------------------------------------------------------------------

BLOG_DIR = ROOT / "content" / "blog"

BLOG_CATEGORY_MAP: dict[str, str] = {
    "Guide": "Guide",
    "Tool Review": "Tool Review",
    "Case Study Analysis": "Case Study Analysis",
    "Research Insight": "Research Insight",
    "Community Update": "Community Update",
}


def handle_blog_post(sections: dict[str, str], author: str) -> tuple[str, str]:
    """Parse blog post fields, write blog markdown file, return (id, type)."""
    title = get_text(sections, "Post Title")
    if not title:
        print("Error: blog post has no title.", file=sys.stderr)
        sys.exit(1)

    post_id = title_to_id(title)
    today = date.today().isoformat()

    summary = get_text(sections, "Summary") or ""

    # Parse category (strip description suffix)
    raw_category = get_text(sections, "Category") or "Guide"
    category = raw_category.split(" — ")[0].strip()
    category = BLOG_CATEGORY_MAP.get(category, category)

    # Author: use provided name or fall back to GitHub username
    author_name = get_text(sections, "Author Name") or author

    # Post content (the actual blog body)
    content = get_text(sections, "Post Content") or ""

    # Related entries and tags
    related = get_comma_list(sections, "Related CollabAtlas Entries (comma-separated IDs)")
    related = [title_to_id(r) for r in related]
    tags = get_comma_list(sections, "Tags (comma-separated)")

    # Build frontmatter
    lines: list[str] = ["---"]
    lines.append(f'title: "{title}"')
    lines.append(f'summary: "{summary}"')
    lines.append(f"date: {today}")
    lines.append(f'author: "{author_name}"')
    lines.append(f'category: "{category}"')
    if related:
        inner = ", ".join(f'"{r}"' for r in related)
        lines.append(f"related_entries: [{inner}]")
    if tags:
        inner = ", ".join(f'"{t}"' for t in tags)
        lines.append(f"tags: [{inner}]")
    lines.append("---")
    lines.append("")

    # Append body content
    if content:
        lines.append(content)
        lines.append("")

    # Write the file
    BLOG_DIR.mkdir(parents=True, exist_ok=True)
    out_path = BLOG_DIR / f"{post_id}.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  Created: {out_path.relative_to(ROOT)}")

    return post_id, "blog-post"


# ---------------------------------------------------------------------------
# GitHub Actions output
# ---------------------------------------------------------------------------


def set_output(entry_id: str, entry_type: str) -> None:
    """Write entry_id and entry_type to $GITHUB_OUTPUT (or stdout for local runs)."""
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"entry_id={entry_id}\n")
            f.write(f"entry_type={entry_type}\n")
        print(f"  Set GITHUB_OUTPUT: entry_id={entry_id}, entry_type={entry_type}")
    else:
        print(f"  entry_id={entry_id}")
        print(f"  entry_type={entry_type}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry point: read environment, parse issue, generate files."""
    issue_body = os.environ.get("ISSUE_BODY", "")
    issue_title = os.environ.get("ISSUE_TITLE", "")
    issue_number = os.environ.get("ISSUE_NUMBER", "0")
    issue_author = os.environ.get("ISSUE_AUTHOR", "unknown")
    issue_labels = os.environ.get("ISSUE_LABELS", "")

    if not issue_body.strip():
        print("Error: ISSUE_BODY is empty.", file=sys.stderr)
        sys.exit(1)

    print(f"Processing issue #{issue_number}: {issue_title}")
    print(f"  Author: {issue_author}")
    print(f"  Labels: {issue_labels}")

    sections = parse_issue_body(issue_body)

    label_list = [l.strip().lower() for l in issue_labels.split(",")]

    # ── Blog post path ────────────────────────────────────────────────────
    if "blog-post" in label_list:
        print("  Detected type: blog-post")
        post_id, post_type = handle_blog_post(sections, issue_author)
        set_output(post_id, post_type)
        return

    # ── Article path ──────────────────────────────────────────────────────
    if "article" in label_list:
        print("  Detected type: research-article")
        article_id, article_type = handle_article(sections, issue_author)
        set_output(article_id, article_type)
        return

    # ── Catalogue entry path ──────────────────────────────────────────────
    entry_type = detect_entry_type(issue_labels, issue_title)
    if entry_type is None:
        print(
            "Error: could not detect entry type from labels or title. "
            f"Labels='{issue_labels}', Title='{issue_title}'",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"  Detected type: {entry_type}")

    # Determine the entry title and ID
    raw_title = get_text(sections, "Title")
    if not raw_title:
        raw_title = extract_clean_title(issue_title)
    entry_id = title_to_id(raw_title)

    if not entry_id:
        print("Error: could not generate a valid entry ID from the title.",
              file=sys.stderr)
        sys.exit(1)

    print(f"  Entry ID: {entry_id}")

    # Build data dict with common fields
    data = build_common_fields(entry_id, entry_type, sections, issue_author)

    # Add type-specific fields
    handler = TYPE_FIELD_HANDLERS.get(entry_type)
    if handler:
        handler(data, sections)

    # Add trailing common fields (external links, tags, related entries)
    add_trailing_common_fields(data, sections)

    # Write files
    write_yaml_entry(data, entry_type)
    write_markdown_entry(data, entry_type)

    # Set GitHub Actions output
    set_output(entry_id, entry_type)

    print("Done.")


if __name__ == "__main__":
    main()
