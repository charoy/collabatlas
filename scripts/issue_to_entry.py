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
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any

import yaml

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
# Mapping tables
# ---------------------------------------------------------------------------

DOMAIN_MAP: dict[str, str] = {
    "Healthcare": "healthcare",
    "Education": "education",
    "Urban Planning": "urban-planning",
    "Software Engineering": "software-engineering",
    "Design": "design",
    "Environmental Science": "environmental-science",
    "Social Sciences": "social-sciences",
    "Public Policy": "public-policy",
    "Business": "business",
    "Arts & Culture": "arts-culture",
    "Disaster Response": "disaster-response",
    "Citizen Science": "citizen-science",
    "Manufacturing": "manufacturing",
    "Agriculture": "agriculture",
    "Publishing": "publishing",
}

COLLAB_TYPE_MAP: dict[str, str] = {
    "Co-Design": "co-design",
    "Co-Creation": "co-creation",
    "Co-Production": "co-production",
    "Participatory": "participatory",
    "Distributed": "distributed",
    "Crowdsourcing": "crowdsourcing",
    "Open Source": "open-source",
    "Interdisciplinary": "interdisciplinary",
    "Transdisciplinary": "transdisciplinary",
    "Community-Based": "community-based",
}

SCALE_MAP: dict[str, str] = {
    "Pair": "pair",
    "Small Team (3-10)": "small-team",
    "Organization (11-100)": "organization",
    "Multi-Organization": "multi-org",
    "Community (100+)": "community",
}

MODALITY_MAP: dict[str, str] = {
    "In-Person": "in-person",
    "Remote": "remote",
    "Hybrid": "hybrid",
}

MATURITY_MAP: dict[str, str] = {
    "Emerging": "emerging",
    "Established": "established",
    "Well-Documented": "well-documented",
}

RESEARCH_METHOD_MAP: dict[str, str] = {
    "Action Research": "action-research",
    "Ethnography": "ethnography",
    "Experimental": "experimental",
    "Survey": "survey",
    "Case Study": "case-study",
    "Design Science": "design-science",
    "Mixed Methods": "mixed-methods",
    "Systematic Review": "systematic-review",
    "Grounded Theory": "grounded-theory",
    "Participatory Action Research": "participatory-action-research",
}

PLATFORM_MAP: dict[str, str] = {
    "Zenodo": "zenodo",
    "Kaggle": "kaggle",
    "Figshare": "figshare",
    "Dataverse": "dataverse",
    "Dryad": "dryad",
    "OSF": "osf",
    "HuggingFace": "huggingface",
    "Google BigQuery": "google-bigquery",
    "ACM DL": "acm-dl",
    "Other": "other",
}

RESOURCE_TYPE_MAP: dict[str, str] = {
    "Article": "article",
    "Book": "book",
    "Course": "course",
    "Video": "video",
    "Tutorial": "tutorial",
    "Report": "report",
}

ACCESS_MAP: dict[str, str] = {
    "Open": "open",
    "Restricted": "restricted",
    "Paid": "paid",
    "Unknown": "unknown",
}

TYPE_DIRS: dict[str, str] = {
    "tool": "tools",
    "method": "methods",
    "framework": "frameworks",
    "case-study": "case-studies",
    "dataset": "datasets",
    "resource": "resources",
}

# ---------------------------------------------------------------------------
# Issue body parser
# ---------------------------------------------------------------------------

_NO_RESPONSE = "_No response_"


def parse_issue_body(body: str) -> dict[str, str]:
    """Parse a GitHub Issue Form Markdown body into {label: content} pairs.

    GitHub Issue Forms render each field as::

        ### Label

        content (possibly multi-line)

    Empty / unanswered fields contain the literal text ``_No response_``.
    """
    sections: dict[str, str] = {}
    current_label: str | None = None
    current_lines: list[str] = []

    for line in body.splitlines():
        header_match = re.match(r"^###\s+(.+)$", line)
        if header_match:
            # Store previous section
            if current_label is not None:
                sections[current_label] = "\n".join(current_lines).strip()
            current_label = header_match.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)

    # Store the final section
    if current_label is not None:
        sections[current_label] = "\n".join(current_lines).strip()

    return sections


def is_empty(value: str | None) -> bool:
    """Return True when a parsed field is absent or unanswered."""
    if value is None:
        return True
    stripped = value.strip()
    return stripped == "" or stripped == _NO_RESPONSE


# ---------------------------------------------------------------------------
# Field extractors
# ---------------------------------------------------------------------------


def get_text(sections: dict[str, str], label: str) -> str | None:
    """Return a plain-text field value, or None if empty."""
    value = sections.get(label)
    if is_empty(value):
        return None
    return value.strip()  # type: ignore[union-attr]


def get_checkboxes(sections: dict[str, str], label: str, mapping: dict[str, str]) -> list[str]:
    """Parse checked checkbox items and map them via *mapping*.

    Checkbox lines look like ``- [X] Label`` (checked) or ``- [ ] Label``.
    """
    raw = sections.get(label, "")
    result: list[str] = []
    for line in raw.splitlines():
        m = re.match(r"^\s*-\s*\[([xX])\]\s*(.+)$", line)
        if m:
            human_label = m.group(2).strip()
            taxonomy_id = mapping.get(human_label)
            if taxonomy_id:
                result.append(taxonomy_id)
            else:
                print(f"  Warning: unmapped checkbox value '{human_label}' in '{label}'",
                      file=sys.stderr)
    return result


def get_dropdown(sections: dict[str, str], label: str, mapping: dict[str, str]) -> str | None:
    """Parse a single-value dropdown and map it via *mapping*."""
    raw = get_text(sections, label)
    if raw is None:
        return None
    mapped = mapping.get(raw)
    if mapped is None:
        print(f"  Warning: unmapped dropdown value '{raw}' in '{label}'",
              file=sys.stderr)
    return mapped


def get_comma_list(sections: dict[str, str], label: str) -> list[str]:
    """Split a comma-separated field into a trimmed list."""
    raw = get_text(sections, label)
    if raw is None:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def get_external_links(sections: dict[str, str], label: str) -> list[dict[str, str]]:
    """Parse external links in ``type | url | title`` format (one per line)."""
    raw = get_text(sections, label)
    if raw is None:
        return []
    links: list[dict[str, str]] = []
    for line in raw.splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 2:
            link: dict[str, str] = {"type": parts[0], "url": parts[1]}
            if len(parts) >= 3 and parts[2]:
                link["title"] = parts[2]
            links.append(link)
    return links


def get_seminal_works(sections: dict[str, str], label: str) -> list[dict[str, Any]]:
    """Parse seminal works in ``Title | Authors | Year | URL(optional)`` format."""
    raw = get_text(sections, label)
    if raw is None:
        return []
    works: list[dict[str, Any]] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 3:
            work: dict[str, Any] = {
                "title": parts[0],
                "authors": [a.strip() for a in parts[1].split(",") if a.strip()],
            }
            try:
                work["year"] = int(parts[2])
            except ValueError:
                work["year"] = parts[2]
            if len(parts) >= 4 and parts[3]:
                work["url"] = parts[3]
            works.append(work)
    return works


def get_lines_as_list(sections: dict[str, str], label: str) -> list[str]:
    """Return non-empty lines as a list of strings."""
    raw = get_text(sections, label)
    if raw is None:
        return []
    return [line.strip() for line in raw.splitlines() if line.strip()]


def get_bool(sections: dict[str, str], label: str) -> bool | None:
    """Parse a Yes/No/Partially dropdown into a boolean."""
    raw = get_text(sections, label)
    if raw is None:
        return None
    lowered = raw.lower().strip()
    if lowered == "yes":
        return True
    if lowered == "no":
        return False
    if lowered == "partially":
        return True
    return None


def get_int(sections: dict[str, str], label: str) -> int | None:
    """Parse an integer field, returning None on failure."""
    raw = get_text(sections, label)
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        print(f"  Warning: could not parse integer from '{raw}' in '{label}'",
              file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# ID generation
# ---------------------------------------------------------------------------


def title_to_id(title: str) -> str:
    """Convert a title to a kebab-case id matching ``^[a-z0-9-]+$``."""
    s = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s]+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


def article_author_year_id(authors: str | None, year: int | None) -> str:
    """Generate an article ID in ``author-year`` format."""
    first_author = (authors or "unknown").split(",")[0].strip().split()[-1].lower()
    first_author = re.sub(r"[^a-z0-9]", "", first_author)
    yr = year if year else "xxxx"
    return f"{first_author}-{yr}"


# ---------------------------------------------------------------------------
# Entry type detection
# ---------------------------------------------------------------------------

VALID_TYPES = set(TYPE_DIRS.keys())


def detect_entry_type(labels: str, title: str) -> str | None:
    """Detect the entry type from issue labels or title pattern.

    Labels are checked first.  Falls back to title patterns like
    ``[New Tool]``, ``[New Method]``, etc.
    """
    label_list = [l.strip().lower() for l in labels.split(",")]

    for label in label_list:
        if label in VALID_TYPES:
            return label

    # Fallback: parse from title "[New XYZ] ..."
    m = re.match(r"^\[New\s+(\w[\w\s-]*)\]", title, re.IGNORECASE)
    if m:
        raw_type = m.group(1).strip().lower()
        # Normalise common forms
        type_aliases: dict[str, str] = {
            "tool": "tool",
            "method": "method",
            "framework": "framework",
            "case study": "case-study",
            "case-study": "case-study",
            "dataset": "dataset",
            "resource": "resource",
        }
        return type_aliases.get(raw_type)

    return None


def extract_clean_title(issue_title: str) -> str:
    """Remove a ``[New XYZ]`` prefix from the issue title if present."""
    cleaned = re.sub(r"^\[New\s+\w[\w\s-]*\]\s*", "", issue_title, flags=re.IGNORECASE)
    return cleaned.strip()


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
        data["collaboration_type"] = collab_types

    scale = get_checkboxes(sections, "Scale (select all that apply)", SCALE_MAP)
    if scale:
        data["scale"] = scale

    modality = get_checkboxes(sections, "Modality (select all that apply)", MODALITY_MAP)
    if modality:
        data["modality"] = modality

    maturity = get_dropdown(sections, "Maturity Level", MATURITY_MAP)
    if maturity:
        data["maturity"] = maturity

    data["status"] = "draft"

    data["contributors"] = [author]
    data["created"] = today
    data["last_reviewed"] = today

    return data


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
        data["supported_platforms"] = platforms


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


TYPE_FIELD_HANDLERS: dict[str, Any] = {
    "tool": add_tool_fields,
    "method": add_method_fields,
    "framework": add_framework_fields,
    "case-study": add_case_study_fields,
    "dataset": add_dataset_fields,
    "resource": add_resource_fields,
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
        data["related_entries"] = related

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
    lines.append(f'tagline: "{data.get("tagline", "")}"')
    lines.append(f'data_id: "{data["id"]}"')

    for field in ("domains", "collaboration_type", "scale", "modality"):
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

    # ── Article path ──────────────────────────────────────────────────────
    label_list = [l.strip().lower() for l in issue_labels.split(",")]
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
