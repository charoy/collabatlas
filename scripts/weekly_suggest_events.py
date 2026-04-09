#!/usr/bin/env python3
"""Weekly event suggestion bot for CollabAtlas.

Asks Claude Sonnet to suggest upcoming conferences, seminars, workshops,
or schools relevant to collaborative research. Creates a PR with new events.

Environment variables:
    ANTHROPIC_API_KEY     Anthropic API key
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

import anthropic
import yaml

ROOT = Path(__file__).resolve().parent.parent
EVENTS_FILE = ROOT / "data" / "events.yaml"

SYSTEM_PROMPT = """\
You are a knowledgeable research assistant specializing in CSCW, HCI, \
collaborative work, and related academic fields.

Your task is to suggest upcoming academic events (conferences, workshops, \
seminars, summer/winter schools) that are relevant to collaborative research.

IMPORTANT RULES:
- Only suggest REAL events that actually exist and have been announced.
- Each event must have verifiable dates and a website or announcement URL.
- Focus on events starting in the next 6-12 months.
- Prioritize: CSCW, CHI, ECSCW, GROUP, JCSCW, DIS, INTERACT, PDC, \
  and related HCI/collaboration venues.
- Also include relevant workshops, doctoral consortia, and summer schools.
- Respond ONLY with valid JSON, no markdown fences.
"""


def load_existing_events() -> list[dict[str, Any]]:
    if EVENTS_FILE.exists():
        with open(EVENTS_FILE, encoding="utf-8") as f:
            return yaml.safe_load(f) or []
    return []


def call_claude(existing: list[dict[str, Any]]) -> list[dict[str, Any]]:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    existing_block = "\n".join(
        f"- {e['title']} ({e.get('date_start', '?')})" for e in existing
    )

    user_prompt = f"""\
Today is {date.today().isoformat()}.

Events already in CollabAtlas (do NOT re-suggest):
{existing_block}

Suggest 2-3 upcoming events relevant to collaborative research, CSCW, HCI, \
or cooperative systems. Include conferences, workshops, or schools starting \
in the next 6-12 months.

Respond with this JSON array:
[
  {{
    "title": "Event Name",
    "type": "conference|seminar|workshop|school",
    "date_start": "YYYY-MM-DD",
    "date_end": "YYYY-MM-DD",
    "location": "City, Country",
    "url": "https://...",
    "description": "One-sentence description",
    "domains": ["cscw", "other-relevant-domain"]
  }}
]
"""

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```\w*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)

    return json.loads(raw)


def title_to_id(title: str) -> str:
    s = title.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s-]+", "-", s)
    return s.strip("-")


def main() -> None:
    existing = load_existing_events()
    existing_ids = {e["id"] for e in existing}
    print(f"Existing events: {len(existing)}")

    print("Calling Claude Sonnet for event suggestions...")
    suggestions = call_claude(existing)
    print(f"Received {len(suggestions)} suggestions")

    added = []
    for s in suggestions:
        eid = title_to_id(s["title"])
        if eid in existing_ids:
            print(f"  Skipping duplicate: {s['title']}")
            continue
        event = {
            "id": eid,
            "title": s["title"],
            "type": s.get("type", "conference"),
            "date_start": s.get("date_start", ""),
            "date_end": s.get("date_end", ""),
            "location": s.get("location", ""),
            "url": s.get("url", ""),
            "description": s.get("description", ""),
            "domains": s.get("domains", []),
            "status": "upcoming",
        }
        existing.append(event)
        existing_ids.add(eid)
        added.append(event)
        print(f"  Added: {s['title']}")

    if not added:
        print("No new events to add.")
        sys.exit(0)

    existing.sort(key=lambda e: e.get("date_start", ""))
    with open(EVENTS_FILE, "w", encoding="utf-8") as f:
        yaml.dump(existing, f, default_flow_style=False,
                  allow_unicode=True, sort_keys=False, width=120)

    # Output for GitHub Actions
    github_output = os.environ.get("GITHUB_OUTPUT", "")
    if github_output:
        titles = ", ".join(e["title"] for e in added)
        with open(github_output, "a") as f:
            f.write(f"events_added={len(added)}\n")
            f.write(f"events_titles={titles}\n")

    print(f"Done! {len(added)} events added.")


if __name__ == "__main__":
    main()
