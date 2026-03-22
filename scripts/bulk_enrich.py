#!/usr/bin/env python3
"""Bulk-enrich incomplete catalogue entries using Claude Sonnet.

For each entry where description == tagline (or missing URL/tags/related),
calls Claude to generate proper content and updates the YAML.

Usage:
    ANTHROPIC_API_KEY=sk-... python scripts/bulk_enrich.py [--dry-run] [--limit N]
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

import anthropic
import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "entries"

TYPE_DIRS = {
    "tools": "tool",
    "methods": "method",
    "frameworks": "framework",
    "case-studies": "case-study",
    "datasets": "dataset",
    "resources": "resource",
}


def load_all_entries() -> dict[str, dict]:
    """Load all entries keyed by id."""
    entries = {}
    for type_dir in TYPE_DIRS:
        d = DATA_DIR / type_dir
        if not d.exists():
            continue
        for f in d.glob("*.yaml"):
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
            if data:
                entries[data.get("id", f.stem)] = data
    return entries


def find_incomplete(entries: dict[str, dict]) -> list[tuple[str, str, dict]]:
    """Find entries that need enrichment."""
    incomplete = []
    for eid, data in entries.items():
        desc = data.get("description", "")
        tagline = data.get("tagline", "")
        needs_work = (
            desc == tagline
            or not data.get("tags")
            or not data.get("related_entries")
            or (not data.get("website_url") and not data.get("source_url") and not data.get("doi"))
        )
        if needs_work:
            etype = data.get("type", "unknown")
            incomplete.append((eid, etype, data))
    return incomplete


def build_context(entries: dict[str, dict]) -> str:
    """Build list of all entry IDs for related suggestions."""
    lines = []
    for eid, data in sorted(entries.items()):
        lines.append(f"- {eid} ({data.get('type', '?')}): {data.get('title', '')}")
    return "\n".join(lines)


SYSTEM = """\
You are an expert in collaborative work, CSCW, and HCI. You enrich catalogue \
entries for CollabAtlas with accurate, factual information.

RULES:
- All information must be REAL and VERIFIABLE
- website_url must be an actual working URL (official website or Wikipedia)
- Description should be 2-4 sentences explaining what it is and why it matters for collaboration
- Tags should be 3-6 lowercase hyphenated keywords
- related_entries must be IDs from the provided list
- Respond ONLY with valid JSON, no markdown fences
"""


def enrich_one(client: anthropic.Anthropic, entry: dict, context: str) -> dict:
    """Call Claude to enrich one entry."""
    title = entry.get("title", "")
    etype = entry.get("type", "")
    tagline = entry.get("tagline", "")
    domains = entry.get("domains", [])
    desc = entry.get("description", "")
    has_desc = desc and desc != tagline

    prompt = f"""\
Enrich this CollabAtlas {etype} entry:

Title: {title}
Tagline: {tagline}
Domains: {", ".join(domains)}
Current description: {"(adequate, keep as-is)" if has_desc else "(missing or same as tagline, please write one)"}
Current website_url: {entry.get("website_url", "(missing)")}
Current tags: {entry.get("tags", "(missing)")}
Current related_entries: {entry.get("related_entries", "(missing)")}

Existing catalogue entries (use these IDs for related_entries):
{context}

Return JSON:
{{
  "description": "2-4 sentence description (or null if current is adequate)",
  "website_url": "official URL or Wikipedia page (or null if already set)",
  "tags": ["3-6 tags"],
  "related_entries": ["2-5 existing entry IDs that relate to this"]
}}
"""

    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=512,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = msg.content[0].text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```\w*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)


def apply_enrichment(entry: dict, enrichment: dict) -> bool:
    """Apply enrichment to entry dict. Returns True if modified."""
    modified = False

    desc = enrichment.get("description")
    if desc and (entry.get("description", "") == entry.get("tagline", "") or not entry.get("description")):
        entry["description"] = desc
        modified = True

    url = enrichment.get("website_url")
    if url and not entry.get("website_url") and not entry.get("source_url"):
        entry["website_url"] = url
        modified = True

    tags = enrichment.get("tags")
    if tags and not entry.get("tags"):
        entry["tags"] = tags
        modified = True

    related = enrichment.get("related_entries")
    if related and not entry.get("related_entries"):
        entry["related_entries"] = related
        modified = True

    return modified


def main():
    dry_run = "--dry-run" in sys.argv
    limit = 999
    for i, arg in enumerate(sys.argv):
        if arg == "--limit" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("Error: set ANTHROPIC_API_KEY", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    all_entries = load_all_entries()
    incomplete = find_incomplete(all_entries)
    context = build_context(all_entries)

    print(f"Found {len(incomplete)} entries to enrich (limit: {limit})")
    if dry_run:
        print("DRY RUN — no files will be modified\n")

    enriched = 0
    for eid, etype, entry in incomplete[:limit]:
        print(f"\n[{enriched+1}/{min(limit, len(incomplete))}] {etype}/{eid}...")
        try:
            result = enrich_one(client, entry, context)
            if dry_run:
                print(f"  Would set: {json.dumps(result, ensure_ascii=False)[:200]}")
            else:
                if apply_enrichment(entry, result):
                    # Find and write the YAML file
                    type_dir = ""
                    for td, tt in TYPE_DIRS.items():
                        if tt == etype:
                            type_dir = td
                            break
                    yaml_path = DATA_DIR / type_dir / f"{eid}.yaml"
                    with open(yaml_path, "w", encoding="utf-8") as f:
                        yaml.dump(entry, f, default_flow_style=False,
                                  allow_unicode=True, sort_keys=False, width=120)
                    print(f"  [OK] Updated {yaml_path.name}")
                else:
                    print(f"  [--] No changes needed")
            enriched += 1
            # Rate limiting: ~1 request per second
            time.sleep(0.5)
        except Exception as e:
            print(f"  [ERR] Error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            continue

    print(f"\nDone: {enriched} entries enriched")


if __name__ == "__main__":
    main()
