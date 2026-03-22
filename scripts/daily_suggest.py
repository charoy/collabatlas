#!/usr/bin/env python3
"""Daily discovery bot for CollabAtlas.

Suggests a new catalogue entry each day by asking Claude Sonnet to propose
a relevant tool, method, framework, case study, or resource that doesn't
yet exist in the atlas.  Creates a GitHub issue labeled ``ai-suggestion``
for human review.

The category rotates daily (Mon=tool, Tue=method, Wed=framework,
Thu=case-study, Fri=resource).  Can also be triggered manually via
``workflow_dispatch`` with an optional category override.

Environment variables (set by GitHub Actions):
    GITHUB_TOKEN          GitHub token for creating issues
    ANTHROPIC_API_KEY     Anthropic API key
    GITHUB_REPOSITORY     owner/repo
    CATEGORY_OVERRIDE     (optional) force a specific category
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import anthropic
import requests
import yaml

from issue_parser import (
    COLLAB_TYPE_MAP,
    DOMAIN_MAP,
    MATURITY_MAP,
    MODALITY_MAP,
    SCALE_MAP,
    TYPE_DIRS,
)

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "entries"

# Categories that rotate daily (Mon-Fri)
DAILY_CATEGORIES = ["tool", "method", "framework", "case-study", "resource"]

CATEGORY_DESCRIPTIONS = {
    "tool": "a software tool or platform that enables or enhances collaboration (e.g., Miro, Figma, Overleaf, Zotero)",
    "method": "a research or design methodology used in collaborative settings (e.g., Delphi method, design sprints, pair programming)",
    "framework": "a theoretical or analytical framework for understanding collaboration (e.g., Activity Theory, CSCW matrix)",
    "case-study": "a documented real-world example of collaborative work (e.g., Linux kernel development, Wikipedia editing, ISS construction)",
    "resource": "an educational resource about collaboration (article, book, course, tutorial, report)",
}

# ---------------------------------------------------------------------------
# Load existing entries to avoid duplicates
# ---------------------------------------------------------------------------


def load_existing_entries() -> list[dict[str, Any]]:
    """Load all existing entries (id, title, type, domains)."""
    entries: list[dict[str, Any]] = []
    for type_key, type_dir in TYPE_DIRS.items():
        entry_dir = DATA_DIR / type_dir
        if not entry_dir.exists():
            continue
        for yaml_file in entry_dir.glob("*.yaml"):
            try:
                with open(yaml_file, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if data:
                    entries.append({
                        "id": data.get("id", yaml_file.stem),
                        "title": data.get("title", ""),
                        "type": data.get("type", type_key),
                        "tagline": data.get("tagline", ""),
                        "domains": data.get("domains", []),
                    })
            except Exception:
                continue
    return entries


def load_past_suggestions() -> set[str]:
    """Load titles of past ai-suggestion issues to avoid re-suggesting."""
    token = os.environ.get("GITHUB_TOKEN", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not token or not repo:
        return set()

    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    params = {"labels": "ai-suggestion", "state": "all", "per_page": 100}
    try:
        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        issues = resp.json()
        titles = set()
        for issue in issues:
            # Extract the entry name from "[AI Suggestion] Tool: Miro" format
            title = issue.get("title", "")
            match = re.search(r":\s*(.+)$", title)
            if match:
                titles.add(match.group(1).strip().lower())
        return titles
    except Exception:
        return set()


def build_taxonomy_context() -> str:
    """Build valid taxonomy values for the prompt."""
    lines = []
    lines.append("Valid domains: " + ", ".join(sorted(DOMAIN_MAP.values())))
    lines.append("Valid collaboration-types: " + ", ".join(sorted(COLLAB_TYPE_MAP.values())))
    lines.append("Valid scales: " + ", ".join(sorted(SCALE_MAP.values())))
    lines.append("Valid modalities: " + ", ".join(sorted(MODALITY_MAP.values())))
    lines.append("Valid maturity levels: " + ", ".join(sorted(MATURITY_MAP.values())))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Call Claude Sonnet
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a knowledgeable research assistant specializing in collaborative work, \
CSCW (Computer-Supported Cooperative Work), HCI, and digital collaboration tools.

Your task is to suggest a NEW entry for CollabAtlas — an open atlas cataloguing \
tools, methods, frameworks, case studies, and resources for collaborative work.

IMPORTANT RULES:
- Suggest something REAL and VERIFIABLE — it must exist and be well-known enough \
  to have documentation, publications, or a website.
- Do NOT invent fictional tools or methods.
- Only use taxonomy values from the provided valid lists.
- The suggestion must be relevant to collaboration, cooperative work, or collective practices.
- Provide a website URL when available.
- Respond ONLY with valid JSON, no markdown fences, no commentary.
"""


def build_user_prompt(
    category: str,
    entries: list[dict[str, Any]],
    past_suggestions: set[str],
    taxonomy_context: str,
) -> str:
    """Build the prompt for Claude Sonnet."""
    existing_names = [f"- {e['title']} ({e['type']})" for e in entries]
    existing_block = "\n".join(existing_names)

    past_block = ""
    if past_suggestions:
        past_block = "\nAlready suggested (do NOT re-suggest):\n" + \
            "\n".join(f"- {s}" for s in past_suggestions) + "\n"

    category_desc = CATEGORY_DESCRIPTIONS.get(category, category)

    return f"""\
Suggest a new **{category}** entry for CollabAtlas.

A {category} in this context is: {category_desc}

{taxonomy_context}

Entries already in the atlas (do NOT suggest duplicates):
{existing_block}
{past_block}
Please suggest ONE entry that would be a valuable addition. Choose something \
well-known, widely used or academically significant, and clearly related to \
collaborative work.

Respond with this JSON structure:
{{
  "title": "Name of the {category}",
  "tagline": "One-sentence summary (max 200 chars)",
  "description": "2-4 sentences explaining what it is, how it supports collaboration, and why it matters",
  "website_url": "https://... (if applicable, null otherwise)",
  "domains": ["from valid list"],
  "collaboration-types": ["from valid list"],
  "scales": ["from valid list"],
  "modalities": ["from valid list"],
  "maturity": "from valid list",
  "tags": ["3-6 relevant tags"],
  "related_entries": ["ids of existing entries that relate to this one"],
  "justification": "Why this entry is valuable for CollabAtlas (1-2 sentences)"
}}
"""


def call_claude(
    category: str,
    entries: list[dict[str, Any]],
    past_suggestions: set[str],
    taxonomy_context: str,
) -> dict[str, Any]:
    """Call Claude Sonnet and return parsed suggestion."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    user_prompt = build_user_prompt(category, entries, past_suggestions, taxonomy_context)

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = message.content[0].text.strip()
    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = re.sub(r"^```\w*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)

    return json.loads(raw)


# ---------------------------------------------------------------------------
# Create GitHub issue
# ---------------------------------------------------------------------------


def create_issue(category: str, suggestion: dict[str, Any]) -> str:
    """Create a GitHub issue with the AI suggestion."""
    token = os.environ.get("GITHUB_TOKEN", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not token or not repo:
        print("Error: GITHUB_TOKEN or GITHUB_REPOSITORY not set", file=sys.stderr)
        sys.exit(1)

    title = suggestion.get("title", "Unknown")
    tagline = suggestion.get("tagline", "")
    description = suggestion.get("description", "")
    website = suggestion.get("website_url", "")
    domains = suggestion.get("domains", [])
    collab_types = suggestion.get("collaboration-types", [])
    scales = suggestion.get("scales", [])
    modalities = suggestion.get("modalities", [])
    maturity = suggestion.get("maturity", "")
    tags = suggestion.get("tags", [])
    related = suggestion.get("related_entries", [])
    justification = suggestion.get("justification", "")

    # Build issue body
    body_lines = [
        f"## 🤖 AI Suggestion: New {category.title().replace('-', ' ')}",
        "",
        f"**{title}** — {tagline}",
        "",
        "### Description",
        "",
        description,
        "",
    ]

    if website:
        body_lines.extend(["### Website", "", website, ""])

    body_lines.extend([
        "### Taxonomy",
        "",
        f"- **Domains**: {', '.join(domains)}",
        f"- **Collaboration types**: {', '.join(collab_types)}",
        f"- **Scales**: {', '.join(scales)}",
        f"- **Modalities**: {', '.join(modalities)}",
        f"- **Maturity**: {maturity}",
        "",
    ])

    if tags:
        body_lines.extend([f"### Tags", "", ", ".join(tags), ""])

    if related:
        body_lines.extend([
            "### Related entries",
            "",
            ", ".join(f"`{r}`" for r in related),
            "",
        ])

    body_lines.extend([
        "### Why add this?",
        "",
        justification,
        "",
        "---",
        "",
        "### Next steps",
        "",
        "- [ ] Verify the information is accurate",
        "- [ ] Add any missing details",
        "- [ ] Approve and convert to a full entry",
        "",
        "*This suggestion was generated by Claude Sonnet. "
        "A human maintainer should verify before adding to the atlas.*",
    ])

    body = "\n".join(body_lines)

    # Human-readable category label
    cat_label = category if category in ("tool", "resource") else category.replace("-", " ")

    issue_title = f"[AI Suggestion] {cat_label.title()}: {title}"

    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    payload = {
        "title": issue_title,
        "body": body,
        "labels": ["ai-suggestion", "triage"],
    }

    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    issue_url = resp.json().get("html_url", "")
    print(f"Issue created: {issue_url}")
    return issue_url


# ---------------------------------------------------------------------------
# Determine today's category
# ---------------------------------------------------------------------------


def get_today_category(override: str | None = None) -> str:
    """Get the category for today based on day-of-week rotation."""
    if override and override.strip():
        cat = override.strip().lower()
        if cat in DAILY_CATEGORIES:
            return cat
        print(f"Warning: unknown category override '{cat}', using rotation", file=sys.stderr)

    weekday = datetime.now(timezone.utc).weekday()  # 0=Mon, 6=Sun
    if weekday >= len(DAILY_CATEGORIES):
        # Weekend — pick a random-ish category based on day of year
        day_of_year = datetime.now(timezone.utc).timetuple().tm_yday
        return DAILY_CATEGORIES[day_of_year % len(DAILY_CATEGORIES)]
    return DAILY_CATEGORIES[weekday]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry point: determine category, call Claude, create issue."""
    override = os.environ.get("CATEGORY_OVERRIDE", "")
    category = get_today_category(override if override else None)
    print(f"Today's category: {category}")

    # Load context
    entries = load_existing_entries()
    past_suggestions = load_past_suggestions()
    taxonomy_context = build_taxonomy_context()

    print(f"Existing entries: {len(entries)}")
    print(f"Past suggestions: {len(past_suggestions)}")

    # Call Claude Sonnet
    print("Calling Claude Sonnet for a suggestion...")
    suggestion = call_claude(category, entries, past_suggestions, taxonomy_context)
    print(f"Suggested: {suggestion.get('title', '?')}")

    # Create issue
    create_issue(category, suggestion)
    print("Done!")


if __name__ == "__main__":
    main()
