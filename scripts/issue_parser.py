#!/usr/bin/env python3
"""Shared parsing utilities for GitHub Issue Form bodies.

This module contains the common parsing logic, mapping tables, and field
extractors used by both ``issue_to_entry.py`` (entry generation) and
``validate_issue.py`` (submission feedback bot).
"""

from __future__ import annotations

import re
import sys
import unicodedata
from typing import Any

# ---------------------------------------------------------------------------
# Mapping tables — human labels → taxonomy IDs
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

VALID_TYPES = set(TYPE_DIRS.keys())

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
            if current_label is not None:
                sections[current_label] = "\n".join(current_lines).strip()
            current_label = header_match.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)

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
            # Strip description suffix from label (e.g., "Healthcare — hospitals..." → "Healthcare")
            human_label = human_label.split(" — ")[0].strip()
            taxonomy_id = mapping.get(human_label)
            if taxonomy_id:
                result.append(taxonomy_id)
            else:
                print(f"  Warning: unmapped checkbox value '{human_label}' in '{label}'",
                      file=sys.stderr)
    return result


def get_checked_count(sections: dict[str, str], label: str) -> int:
    """Count the number of checked checkboxes in a section (no mapping needed)."""
    raw = sections.get(label, "")
    count = 0
    for line in raw.splitlines():
        if re.match(r"^\s*-\s*\[([xX])\]\s*(.+)$", line):
            count += 1
    return count


def get_total_checkboxes(sections: dict[str, str], label: str) -> int:
    """Count the total number of checkboxes (checked + unchecked) in a section."""
    raw = sections.get(label, "")
    count = 0
    for line in raw.splitlines():
        if re.match(r"^\s*-\s*\[[ xX]\]\s*(.+)$", line):
            count += 1
    return count


def get_dropdown(sections: dict[str, str], label: str, mapping: dict[str, str]) -> str | None:
    """Parse a single-value dropdown and map it via *mapping*."""
    raw = get_text(sections, label)
    if raw is None:
        return None
    # Strip description suffix (e.g., "Emerging — new or experimental..." → "Emerging")
    raw = raw.split(" — ")[0].strip()
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


# ---------------------------------------------------------------------------
# Entry type detection
# ---------------------------------------------------------------------------


def detect_entry_type(labels: str, title: str) -> str | None:
    """Detect the entry type from issue labels or title pattern."""
    label_list = [l.strip().lower() for l in labels.split(",")]

    for label in label_list:
        if label in VALID_TYPES:
            return label

    m = re.match(r"^\[New\s+(\w[\w\s-]*)\]", title, re.IGNORECASE)
    if m:
        raw_type = m.group(1).strip().lower()
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
