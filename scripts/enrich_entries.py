#!/usr/bin/env python3
"""Enrich catalogue entries with body content based on frontmatter.

Reads each entry's frontmatter (title, tagline, type, domains, taxonomy values)
and generates meaningful markdown body content. Idempotent — skips entries
that already have body content.

Usage:
    python scripts/enrich_entries.py [--dry-run]
"""

from __future__ import annotations

import argparse
import re
import sys
import textwrap
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content" / "catalogue"
DATA_DIR = ROOT / "data" / "entries"

# Human-readable labels for taxonomy values
DOMAIN_LABELS = {
    "healthcare": "Healthcare",
    "education": "Education",
    "urban-planning": "Urban Planning",
    "software-engineering": "Software Engineering",
    "design": "Design",
    "environmental-science": "Environmental Science",
    "social-sciences": "Social Sciences",
    "public-policy": "Public Policy",
    "business": "Business",
    "arts-culture": "Arts & Culture",
    "disaster-response": "Disaster Response",
    "citizen-science": "Citizen Science",
    "manufacturing": "Manufacturing",
    "agriculture": "Agriculture",
    "publishing": "Publishing",
}

COLLAB_LABELS = {
    "co-design": "co-design",
    "co-creation": "co-creation",
    "co-production": "co-production",
    "participatory": "participatory",
    "distributed": "distributed",
    "crowdsourcing": "crowdsourcing",
    "open-source": "open source",
    "interdisciplinary": "interdisciplinary",
    "transdisciplinary": "transdisciplinary",
    "community-based": "community-based",
}

SCALE_LABELS = {
    "pair": "pair work",
    "small-team": "small teams",
    "organization": "organizational settings",
    "multi-org": "multi-organization networks",
    "community": "community-scale initiatives",
}

MODALITY_LABELS = {
    "in-person": "in-person",
    "remote": "remote",
    "hybrid": "hybrid",
}


def parse_frontmatter(path: Path) -> tuple[dict, str]:
    """Parse YAML frontmatter and body content from a markdown file."""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)", text, re.DOTALL)
    if not m:
        return {}, text
    fm = yaml.safe_load(m.group(1)) or {}
    body = m.group(2).strip()
    return fm, body


def load_data_file(subsection: str, data_id: str) -> dict:
    """Load the YAML data file for an entry if it exists."""
    data_path = DATA_DIR / subsection / f"{data_id}.yaml"
    if data_path.exists():
        with open(data_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def humanize_list(items: list[str], labels: dict[str, str]) -> str:
    """Convert a list of IDs to human-readable comma-separated string."""
    readable = [labels.get(item, item.replace("-", " ").title()) for item in items]
    if len(readable) == 0:
        return ""
    if len(readable) == 1:
        return readable[0]
    return ", ".join(readable[:-1]) + " and " + readable[-1]


def generate_body(fm: dict, data: dict, subsection: str) -> str:
    """Generate markdown body content for an entry."""
    title = fm.get("title", "This entry")
    tagline = fm.get("tagline", "")
    domains = fm.get("domains", [])
    collab_types = fm.get("collaboration-types", [])
    scales = fm.get("scales", [])
    modalities = fm.get("modalities", [])
    maturity = fm.get("maturity", "")
    description = data.get("description", "")

    # Build the content based on entry type
    sections = []

    # Overview paragraph
    overview = _build_overview(title, tagline, description, subsection, domains)
    sections.append(overview)

    # Context paragraph (collaboration types, scales, modalities)
    context = _build_context(title, collab_types, scales, modalities, subsection)
    if context:
        sections.append(context)

    # Type-specific content
    type_content = _build_type_specific(title, subsection, maturity, data)
    if type_content:
        sections.append(type_content)

    return "\n\n".join(sections) + "\n"


def _build_overview(
    title: str,
    tagline: str,
    description: str,
    subsection: str,
    domains: list[str],
) -> str:
    """Build the overview paragraph."""
    type_label = {
        "tools": "tool",
        "methods": "method",
        "frameworks": "framework",
        "case-studies": "case study",
        "datasets": "dataset",
        "resources": "resource",
    }.get(subsection, "entry")

    domain_text = humanize_list(domains, DOMAIN_LABELS)

    if description:
        para = description
    elif tagline:
        para = f"{title} is a {type_label} for collaborative work. {tagline}"
    else:
        para = f"{title} is a {type_label} catalogued in CollabAtlas."

    if domain_text and domain_text.lower() not in para.lower():
        para += f" It is particularly relevant in {domain_text}."

    return para


def _build_context(
    title: str,
    collab_types: list[str],
    scales: list[str],
    modalities: list[str],
    subsection: str,
) -> str:
    """Build the collaboration context paragraph."""
    parts = []

    if collab_types:
        ct_text = humanize_list(collab_types, COLLAB_LABELS)
        parts.append(f"{title} supports {ct_text} collaboration")

    if scales:
        sc_text = humanize_list(scales, SCALE_LABELS)
        if parts:
            parts.append(f"and is suited for {sc_text}")
        else:
            parts.append(f"{title} is suited for {sc_text}")

    if modalities:
        mod_text = humanize_list(modalities, MODALITY_LABELS)
        if parts:
            parts.append(f"in {mod_text} settings")
        else:
            parts.append(f"{title} works in {mod_text} settings")

    if not parts:
        return ""

    return " ".join(parts) + "."


def _build_type_specific(
    title: str, subsection: str, maturity: str, data: dict
) -> str:
    """Build type-specific content."""
    maturity_text = {
        "emerging": f"As an emerging {_type_noun(subsection)}, {title} is still developing its evidence base and community adoption.",
        "established": f"{title} is an established {_type_noun(subsection)} with a solid track record of use across multiple contexts.",
        "well-documented": f"{title} is classified as a well-documented {_type_noun(subsection)}, indicating broad adoption and available documentation.",
    }.get(maturity, "")

    if subsection == "tools":
        extra = _tool_extra(title, data)
    elif subsection == "methods":
        extra = _method_extra(title, data)
    elif subsection == "frameworks":
        extra = _framework_extra(title, data)
    elif subsection == "case-studies":
        extra = _case_study_extra(title, data)
    elif subsection == "datasets":
        extra = _dataset_extra(title, data)
    elif subsection == "resources":
        extra = _resource_extra(title, data)
    else:
        extra = ""

    parts = [p for p in [maturity_text, extra] if p]
    return " ".join(parts) if parts else ""


def _type_noun(subsection: str) -> str:
    return {
        "tools": "tool",
        "methods": "method",
        "frameworks": "framework",
        "case-studies": "case study",
        "datasets": "dataset",
        "resources": "resource",
    }.get(subsection, "entry")


def _tool_extra(title: str, data: dict) -> str:
    parts = []
    if data.get("open_source"):
        license_val = data.get("license", "open source")
        parts.append(f"It is open source (licensed under {license_val})")
    elif data.get("open_source") is False:
        parts.append("It is a proprietary platform")
    platforms = data.get("supported_platforms", [])
    if platforms:
        parts.append(f"available on {', '.join(platforms[:4])}")
    return (", ".join(parts) + ".") if parts else ""


def _method_extra(title: str, data: dict) -> str:
    steps = data.get("steps", [])
    if steps and len(steps) >= 3:
        return (
            f"The {title} method involves a structured process including: "
            + ", ".join(steps[:3])
            + ", and further steps."
        )
    return ""


def _framework_extra(title: str, data: dict) -> str:
    concepts = data.get("key_concepts", [])
    if concepts:
        return f"Key concepts include {', '.join(concepts[:4])}."
    return ""


def _case_study_extra(title: str, data: dict) -> str:
    org = data.get("organization", "")
    year = data.get("year", "")
    parts = []
    if org:
        parts.append(f"from {org}")
    if year:
        parts.append(f"({year})")
    if org and year:
        return f"This case study examines the collaborative practices at {org}, drawing on experiences since {year}."
    elif org:
        return f"This case study examines collaborative practices at {org}."
    elif year:
        return f"This case study examines collaborative practices documented since {year}."
    return "This case study examines real-world application of collaborative approaches."


def _dataset_extra(title: str, data: dict) -> str:
    platform = data.get("platform", "")
    fmt = data.get("format", "")
    parts = []
    if platform:
        parts.append(f"hosted on {platform}")
    if fmt:
        parts.append(f"in {fmt} format")
    if parts:
        return f"The dataset is {', '.join(parts)}."
    return ""


def _resource_extra(title: str, data: dict) -> str:
    rtype = data.get("resource_type", "")
    authors = data.get("authors", [])
    year = data.get("year", "")
    parts = []
    if rtype:
        parts.append(f"This {rtype}")
    else:
        parts.append("This resource")
    if authors:
        parts.append(f"by {', '.join(authors[:2])}")
    if year:
        parts.append(f"({year})")
    parts.append("provides valuable reference material for researchers and practitioners.")
    return " ".join(parts)


def write_enriched(path: Path, fm: dict, body: str) -> None:
    """Write the enriched markdown file, preserving original frontmatter."""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^(---\s*\n.*?\n---\s*\n?)", text, re.DOTALL)
    if m:
        header = m.group(1)
        if not header.endswith("\n"):
            header += "\n"
        path.write_text(header + "\n" + body, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Enrich catalogue entries with body content")
    parser.add_argument("--dry-run", action="store_true", help="Print changes without writing")
    args = parser.parse_args()

    enriched = 0
    skipped = 0

    for section_dir in sorted(CONTENT_DIR.iterdir()):
        if not section_dir.is_dir():
            continue
        subsection = section_dir.name
        if subsection.startswith("_"):
            continue

        for md_file in sorted(section_dir.glob("*.md")):
            if md_file.name == "_index.md":
                continue

            fm, existing_body = parse_frontmatter(md_file)
            if not fm:
                continue

            # Skip if already has body content
            if existing_body.strip():
                skipped += 1
                continue

            data_id = fm.get("data_id", md_file.stem)
            data = load_data_file(subsection, data_id)

            body = generate_body(fm, data, subsection)

            if args.dry_run:
                print(f"  Would enrich: {md_file.relative_to(ROOT)}")
                print(f"    Body preview: {body[:100]}...")
            else:
                write_enriched(md_file, fm, body)
                enriched += 1
                print(f"  Enriched: {md_file.relative_to(ROOT)}")

    print(f"\nDone: {enriched} enriched, {skipped} skipped (already have content)")


if __name__ == "__main__":
    main()
