#!/usr/bin/env python3
"""Fix migrated YAML entries by adding missing required fields.

Reads description from the markdown body, adds default contributors,
and adds type-specific required fields (resource_type, source_url).
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "entries"
CONTENT_DIR = ROOT / "content" / "catalogue"

TYPE_DIRS = {
    "tools": "tool",
    "methods": "method",
    "frameworks": "framework",
    "case-studies": "case-study",
    "datasets": "dataset",
    "resources": "resource",
}

# Guessed resource types based on title keywords
RESOURCE_TYPE_HINTS = {
    "toolkit": "tutorial",
    "guide": "tutorial",
    "playbook": "tutorial",
    "manual": "book",
    "handbook": "book",
    "book": "book",
    "primer": "book",
    "art of": "book",
    "patterns": "tutorial",
    "principles": "article",
    "spectrum": "article",
}


def guess_resource_type(title: str) -> str:
    """Guess resource_type from the title."""
    title_lower = title.lower()
    for hint, rtype in RESOURCE_TYPE_HINTS.items():
        if hint in title_lower:
            return rtype
    return "article"  # default


def extract_description_from_md(md_path: Path) -> str | None:
    """Extract the first paragraph from markdown body as description."""
    text = md_path.read_text(encoding="utf-8")
    # Skip frontmatter
    match = re.match(r"^---\s*\n.*?\n---\s*\n?(.*)", text, re.DOTALL)
    if not match:
        return None
    body = match.group(1).strip()
    if not body:
        return None
    # Take first paragraph (up to double newline)
    paragraphs = body.split("\n\n")
    if paragraphs:
        return paragraphs[0].strip()
    return None


def fix_entry(yaml_path: Path, type_dir: str) -> bool:
    """Fix a single YAML entry. Returns True if modified."""
    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data:
        return False

    modified = False
    entry_id = data.get("id", yaml_path.stem)

    # Add description from markdown body if missing
    if "description" not in data or not data["description"]:
        md_path = CONTENT_DIR / type_dir / f"{entry_id}.md"
        if md_path.exists():
            desc = extract_description_from_md(md_path)
            if desc:
                data["description"] = desc
                modified = True
                print(f"  + description for {entry_id}")

    # Add default contributors if missing
    if "contributors" not in data or not data["contributors"]:
        data["contributors"] = ["collabatlas-team"]
        modified = True

    # Type-specific required fields
    entry_type = TYPE_DIRS.get(type_dir)

    if entry_type == "dataset" and ("source_url" not in data or not data["source_url"]):
        # Use website_url if available, otherwise placeholder
        if "website_url" in data and data["website_url"]:
            data["source_url"] = data["website_url"]
        else:
            data["source_url"] = f"https://example.com/{entry_id}"
        modified = True
        print(f"  + source_url for {entry_id}")

    if entry_type == "resource" and ("resource_type" not in data or not data["resource_type"]):
        title = data.get("title", "")
        data["resource_type"] = guess_resource_type(title)
        modified = True
        print(f"  + resource_type={data['resource_type']} for {entry_id}")

    if modified:
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True,
                      sort_keys=False, width=120)

    return modified


def main() -> None:
    total = 0
    for type_dir in TYPE_DIRS:
        entry_dir = DATA_DIR / type_dir
        if not entry_dir.exists():
            continue
        for yaml_file in sorted(entry_dir.glob("*.yaml")):
            if fix_entry(yaml_file, type_dir):
                total += 1

    print(f"\nFixed {total} entries")


if __name__ == "__main__":
    main()
