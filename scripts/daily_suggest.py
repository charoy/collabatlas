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
    load_all_entries,
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
    """Load all existing entries (YAML + Markdown frontmatter)."""
    return load_all_entries(str(ROOT))


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
# Generate entry files (YAML + Markdown)
# ---------------------------------------------------------------------------


def generate_entry_files(category: str, suggestion: dict[str, Any]) -> tuple[str, str, str]:
    """Generate YAML and Markdown files for the suggestion.

    Returns (entry_id, yaml_path, md_path) relative to ROOT.
    """
    from issue_parser import title_to_id

    title = suggestion.get("title", "Unknown")
    entry_id = title_to_id(title)
    type_dir = TYPE_DIRS.get(category, category + "s")

    # Build YAML data
    entry_data: dict[str, Any] = {
        "id": entry_id,
        "type": category,
        "title": title,
        "tagline": suggestion.get("tagline", ""),
        "description": suggestion.get("description", ""),
    }

    for field in ("domains", "collaboration-types", "scales", "modalities"):
        values = suggestion.get(field, [])
        if values:
            entry_data[field] = values

    maturity = suggestion.get("maturity")
    if maturity:
        entry_data["maturity"] = maturity

    entry_data["status"] = "published"
    entry_data["contributors"] = ["collabatlas-bot"]
    entry_data["created"] = date.today().isoformat()
    entry_data["last_reviewed"] = date.today().isoformat()

    website = suggestion.get("website_url")
    if website:
        entry_data["website_url"] = website

    tags = suggestion.get("tags", [])
    if tags:
        entry_data["tags"] = tags

    related = suggestion.get("related_entries", [])
    if related:
        entry_data["related_entries"] = related

    # Write YAML
    yaml_dir = DATA_DIR / type_dir
    yaml_dir.mkdir(parents=True, exist_ok=True)
    yaml_path = yaml_dir / f"{entry_id}.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(entry_data, f, default_flow_style=False,
                  allow_unicode=True, sort_keys=False, width=120)

    # Write Markdown
    content_dir = ROOT / "content" / "catalogue" / type_dir
    content_dir.mkdir(parents=True, exist_ok=True)
    md_path = content_dir / f"{entry_id}.md"
    md_content = f'---\ntitle: "{title}"\ndata_id: "{entry_id}"\n---\n'
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"  Generated {yaml_path.relative_to(ROOT)}")
    print(f"  Generated {md_path.relative_to(ROOT)}")

    return entry_id, str(yaml_path.relative_to(ROOT)), str(md_path.relative_to(ROOT))


# ---------------------------------------------------------------------------
# Create GitHub issue (for reference / tracking)
# ---------------------------------------------------------------------------


def create_issue(category: str, suggestion: dict[str, Any], pr_url: str = "") -> str:
    """Create a GitHub issue with the AI suggestion."""
    token = os.environ.get("GITHUB_TOKEN", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not token or not repo:
        print("Skipping issue creation: GITHUB_TOKEN or GITHUB_REPOSITORY not set")
        return ""

    title_text = suggestion.get("title", "Unknown")
    tagline = suggestion.get("tagline", "")
    description = suggestion.get("description", "")
    justification = suggestion.get("justification", "")
    cat_label = category if category in ("tool", "resource") else category.replace("-", " ")

    body_lines = [
        f"## AI Suggestion: New {cat_label.title()}",
        "",
        f"**{title_text}** - {tagline}",
        "",
        "### Description",
        "",
        description,
        "",
        "### Why add this?",
        "",
        justification,
        "",
    ]

    if pr_url:
        body_lines.extend([
            "---",
            "",
            f"A pull request has been created automatically: {pr_url}",
            "",
            "**Review the PR and merge if the entry looks good.**",
        ])

    body_lines.extend([
        "",
        "*This suggestion was generated by Claude Sonnet.*",
    ])

    body = "\n".join(body_lines)
    issue_title = f"[AI Suggestion] {cat_label.title()}: {title_text}"

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
    """Entry point: determine category, call Claude, generate files."""
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
    title = suggestion.get("title", "?")
    print(f"Suggested: {title}")

    # Generate entry files (YAML + MD)
    entry_id, yaml_path, md_path = generate_entry_files(category, suggestion)

    # Output for GitHub Actions to pick up
    github_output = os.environ.get("GITHUB_OUTPUT", "")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"entry_id={entry_id}\n")
            f.write(f"entry_type={category}\n")
            f.write(f"entry_title={title}\n")

    # Store suggestion JSON for issue creation step
    suggestion_path = ROOT / "suggestion.json"
    with open(suggestion_path, "w", encoding="utf-8") as f:
        json.dump({"category": category, "suggestion": suggestion}, f,
                  ensure_ascii=False, indent=2)

    print("Done! Files generated, ready for branch + PR creation.")


if __name__ == "__main__":
    main()
