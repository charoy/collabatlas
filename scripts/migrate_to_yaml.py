#!/usr/bin/env python3
"""Migrate catalogue entries from Markdown frontmatter to separate YAML files.

For each content/catalogue/<type>/<entry>.md that does NOT have a
corresponding data/entries/<type>/<entry>.yaml, this script:

1. Extracts the YAML frontmatter
2. Creates a proper data/entries/<type>/<entry>.yaml with id + type fields
3. Strips the data fields from the .md, keeping only title + data_id + body text

Usage:
    python scripts/migrate_to_yaml.py [--dry-run]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

# Type directory mapping (content dir name → entry type)
TYPE_MAP = {
    "tools": "tool",
    "methods": "method",
    "frameworks": "framework",
    "case-studies": "case-study",
    "datasets": "dataset",
    "resources": "resource",
    "research-cases": "research-case",
}

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content" / "catalogue"
DATA_DIR = ROOT / "data" / "entries"

# Fields that stay in the Markdown frontmatter
MD_KEEP_FIELDS = {"title", "data_id"}

# Fields to skip in YAML (they're derived, not source data)
YAML_SKIP_FIELDS = {"data_id"}


def extract_frontmatter(text: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and body from a markdown file."""
    match = re.match(r"^---\s*\n(.+?)\n---\s*\n?(.*)", text, re.DOTALL)
    if not match:
        return {}, text
    fm = yaml.safe_load(match.group(1)) or {}
    body = match.group(2)
    return fm, body


def build_yaml_data(fm: dict, entry_id: str, entry_type: str) -> dict:
    """Build YAML data dict from frontmatter, adding id and type."""
    data = {"id": entry_id, "type": entry_type}

    # Copy fields from frontmatter (except those we skip)
    field_order = [
        "title", "tagline", "description",
        "domains", "collaboration-types", "scales", "modalities",
        "maturity", "status",
        "website_url", "source_url", "doi", "license", "open_source",
        "supported_platforms", "external_links", "related_entries",
        "tags", "contributors", "created", "last_reviewed",
        # Research case specific
        "researcher", "studied_domain", "research_methodologies",
        "observed_practices", "observed_artefacts",
        "issues_organizational", "issues_technical",
        "issues_governance", "issues_policy",
        "publications", "datasets", "software",
        # Dataset specific
        "data_format", "access", "hosting_platform",
        "size_description", "temporal_coverage",
        # Resource specific
        "resource_type", "authors", "year",
        # Method specific
        "seminal_works", "research_methods",
        # Framework specific
        "key_concepts",
    ]

    for field in field_order:
        if field in fm and field not in YAML_SKIP_FIELDS:
            data[field] = fm[field]

    # Copy any remaining fields not in the ordered list
    for key, val in fm.items():
        if key not in data and key not in YAML_SKIP_FIELDS and key not in MD_KEEP_FIELDS:
            data[key] = val

    return data


def build_slim_markdown(title: str, data_id: str, body: str) -> str:
    """Build a slim markdown file with just title, data_id, and body."""
    lines = [
        "---",
        f'title: "{title}"',
        f'data_id: "{data_id}"',
        "---",
        "",
    ]

    # Keep body text if it's not just auto-generated filler
    body_stripped = body.strip()
    if body_stripped:
        lines.append(body_stripped)
        lines.append("")

    return "\n".join(lines)


def migrate_entry(md_path: Path, type_dir: str, entry_type: str, dry_run: bool) -> bool:
    """Migrate a single entry. Returns True if migrated."""
    entry_id = md_path.stem
    yaml_path = DATA_DIR / type_dir / f"{entry_id}.yaml"

    # Skip if YAML already exists
    if yaml_path.exists():
        return False

    # Read markdown
    text = md_path.read_text(encoding="utf-8")
    fm, body = extract_frontmatter(text)

    if not fm:
        print(f"  SKIP {md_path.name}: no frontmatter")
        return False

    # Ensure data_id
    data_id = fm.get("data_id", entry_id)

    # Build YAML
    yaml_data = build_yaml_data(fm, data_id, entry_type)

    # Build slim markdown
    title = fm.get("title", entry_id)
    slim_md = build_slim_markdown(title, data_id, body)

    if dry_run:
        print(f"  WOULD CREATE {yaml_path.relative_to(ROOT)}")
        print(f"  WOULD UPDATE {md_path.relative_to(ROOT)}")
        return True

    # Write YAML
    yaml_path.parent.mkdir(parents=True, exist_ok=True)
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True,
                  sort_keys=False, width=120)

    # Update markdown
    md_path.write_text(slim_md, encoding="utf-8")

    print(f"  CREATED {yaml_path.relative_to(ROOT)}")
    print(f"  UPDATED {md_path.relative_to(ROOT)}")
    return True


def main() -> None:
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("=== DRY RUN ===\n")

    total_migrated = 0

    for type_dir, entry_type in TYPE_MAP.items():
        section_dir = CONTENT_DIR / type_dir
        if not section_dir.exists():
            continue

        md_files = sorted(section_dir.glob("*.md"))
        section_count = 0

        for md_file in md_files:
            if md_file.name.startswith("_"):
                continue  # skip _index.md

            if migrate_entry(md_file, type_dir, entry_type, dry_run):
                section_count += 1

        if section_count > 0:
            print(f"\n{type_dir}: {section_count} entries migrated")
            total_migrated += section_count

    print(f"\nTotal: {total_migrated} entries migrated")


if __name__ == "__main__":
    main()
