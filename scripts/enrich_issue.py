#!/usr/bin/env python3
"""AI-powered issue enrichment for CollabAtlas.

When a new issue is submitted (new-entry or quick-add), this script:
1. Evaluates the relevance of the submission
2. Fills empty taxonomy/description fields via Claude Haiku
3. Posts a summary comment and updates the issue body

Environment variables (set by GitHub Actions):
    ISSUE_BODY      Full Markdown body of the issue
    ISSUE_TITLE     Issue title
    ISSUE_LABELS    Comma-separated labels
    ISSUE_NUMBER    Issue number
    GITHUB_TOKEN    GitHub token for API calls
    ANTHROPIC_API_KEY  Anthropic API key
    GITHUB_REPOSITORY  owner/repo
"""

from __future__ import annotations

import json
import os
import re
import sys
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
    detect_entry_type,
    extract_clean_title,
    get_checkboxes,
    get_checked_count,
    get_comma_list,
    get_dropdown,
    get_text,
    load_all_entries,
    parse_issue_body,
    title_to_id,
)

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "entries"

# ---------------------------------------------------------------------------
# Load catalogue context for the LLM
# ---------------------------------------------------------------------------


def load_existing_entries() -> list[dict[str, Any]]:
    """Load all existing entries (YAML + Markdown frontmatter)."""
    return load_all_entries(str(ROOT))


def build_taxonomy_context() -> str:
    """Build a text block listing all valid taxonomy values."""
    lines = []
    lines.append("Valid domains: " + ", ".join(sorted(DOMAIN_MAP.values())))
    lines.append("Valid collaboration-types: " + ", ".join(sorted(COLLAB_TYPE_MAP.values())))
    lines.append("Valid scales: " + ", ".join(sorted(SCALE_MAP.values())))
    lines.append("Valid modalities: " + ", ".join(sorted(MODALITY_MAP.values())))
    lines.append("Valid maturity levels: " + ", ".join(sorted(MATURITY_MAP.values())))
    return "\n".join(lines)


def build_entries_context(entries: list[dict[str, Any]]) -> str:
    """Build a compact text listing existing entries for related suggestions."""
    lines = []
    for e in entries:
        domains = ", ".join(e.get("domains", []))
        lines.append(f"- {e['id']} ({e['type']}): {e['title']} — {e.get('tagline', '')} [{domains}]")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parse what the contributor already filled in
# ---------------------------------------------------------------------------


def extract_filled_fields(sections: dict[str, str]) -> dict[str, Any]:
    """Extract what the contributor already provided."""
    filled: dict[str, Any] = {}

    title = get_text(sections, "Title")
    if title:
        filled["title"] = title

    tagline = get_text(sections, "Tagline")
    if tagline:
        filled["tagline"] = tagline

    description = get_text(sections, "Full Description")
    if description:
        filled["description"] = description

    # URL from Quick Add
    url = get_text(sections, "URL")
    if url:
        filled["url"] = url

    # Entry type from Quick Add
    entry_type = get_text(sections, "Entry type")
    if entry_type:
        filled["entry_type"] = entry_type

    # Why relevant from Quick Add
    why = get_text(sections, "Why is this relevant?")
    if why:
        filled["why_relevant"] = why

    domains = get_checkboxes(sections, "Relevant Domains (select all that apply)", DOMAIN_MAP)
    if domains:
        filled["domains"] = domains

    collab = get_checkboxes(sections, "Collaboration Types (select all that apply)", COLLAB_TYPE_MAP)
    if collab:
        filled["collaboration-types"] = collab

    scales = get_checkboxes(sections, "Scale (select all that apply)", SCALE_MAP)
    if scales:
        filled["scales"] = scales

    modalities = get_checkboxes(sections, "Modality (select all that apply)", MODALITY_MAP)
    if modalities:
        filled["modalities"] = modalities

    maturity = get_dropdown(sections, "Maturity Level", MATURITY_MAP)
    if maturity:
        filled["maturity"] = maturity

    tags = get_comma_list(sections, "Tags (comma-separated)")
    if tags:
        filled["tags"] = tags

    related = get_comma_list(sections, "Related CollabAtlas Entries (comma-separated IDs)")
    if related:
        filled["related_entries"] = related

    return filled


# ---------------------------------------------------------------------------
# Call Claude Haiku
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are an editorial assistant for CollabAtlas, an open collaborative atlas \
of tools, methods, frameworks, case studies, datasets, and resources for \
collaborative work.

Your task is to evaluate a new submission and suggest enrichments.

IMPORTANT RULES:
- Only suggest values from the provided valid taxonomy lists.
- Never overwrite fields the contributor already filled in.
- Be concise and factual.
- Respond ONLY with valid JSON, no markdown fences, no commentary.
"""


def build_user_prompt(
    filled: dict[str, Any],
    entry_type: str | None,
    taxonomy_context: str,
    entries_context: str,
) -> str:
    """Build the user prompt for Claude."""
    return f"""\
Here is a new submission for the CollabAtlas catalogue.

Entry type: {entry_type or "unknown"}
Fields provided by the contributor:
{json.dumps(filled, indent=2, ensure_ascii=False)}

{taxonomy_context}

Existing catalogue entries (for suggesting related_entries):
{entries_context}

Please respond with a JSON object containing:
{{
  "verdict": "accepted" | "needs-discussion" | "rejected",
  "verdict_reason": "short explanation in the language of the submission",
  "domains": ["only if contributor left this empty"],
  "collaboration-types": ["only if contributor left this empty"],
  "scales": ["only if contributor left this empty"],
  "modalities": ["only if contributor left this empty"],
  "maturity": "only if contributor left this empty",
  "description": "enriched description only if the provided one is too short (<30 words) or missing",
  "related_entries": ["ids of related existing entries, max 5"],
  "tags": ["suggested tags, max 8"]
}}

Criteria for verdict:
- "accepted": the submission is about a collaborative tool, method, framework, case study, dataset, or resource
- "needs-discussion": unclear relevance, potential duplicate, or insufficient information
- "rejected": clearly off-topic (not related to collaboration at all)

Only include fields that you are adding or improving. Omit fields the contributor already filled correctly.
"""


def call_claude(filled: dict[str, Any], entry_type: str | None,
                taxonomy_context: str, entries_context: str) -> dict[str, Any]:
    """Call Claude Haiku and return parsed JSON suggestions."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    user_prompt = build_user_prompt(filled, entry_type, taxonomy_context, entries_context)

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
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
# Update issue body (fill empty checkbox/dropdown fields)
# ---------------------------------------------------------------------------


def update_issue_body(body: str, suggestions: dict[str, Any], filled: dict[str, Any]) -> str:
    """Update the issue body by checking unchecked boxes for suggested values."""
    updated = body

    # Map suggestion keys to checkbox labels and value maps
    checkbox_fields = {
        "domains": ("Relevant Domains (select all that apply)", {v: k for k, v in DOMAIN_MAP.items()}),
        "collaboration-types": ("Collaboration Types (select all that apply)", {v: k for k, v in COLLAB_TYPE_MAP.items()}),
        "scales": ("Scale (select all that apply)", {v: k for k, v in SCALE_MAP.items()}),
        "modalities": ("Modality (select all that apply)", {v: k for k, v in MODALITY_MAP.items()}),
    }

    for field_key, (section_label, reverse_map) in checkbox_fields.items():
        if field_key in filled:
            continue  # Don't overwrite contributor's choices
        suggested_values = suggestions.get(field_key, [])
        if not suggested_values:
            continue
        # Find the human labels for the suggested taxonomy IDs
        human_labels = set()
        for val in suggested_values:
            label = reverse_map.get(val)
            if label:
                human_labels.add(label)
        # Check the corresponding boxes in the issue body
        for label in human_labels:
            # Match "- [ ] Label" and check it, being careful with description suffixes
            pattern = re.compile(
                r"(- \[ \] " + re.escape(label) + r"(?:\s*—[^\n]*)?)",
                re.MULTILINE,
            )
            updated = pattern.sub(
                lambda m: m.group(0).replace("- [ ]", "- [x]", 1),
                updated,
            )

    # Update description if suggested and original was short/missing
    if "description" in suggestions and "description" not in filled:
        # Find the Full Description section and replace content
        desc_pattern = re.compile(
            r"(### Full Description\s*\n\n)(_No response_|.{0,60}?)(\n\n###|\Z)",
            re.DOTALL,
        )
        replacement = suggestions["description"]
        updated = desc_pattern.sub(
            lambda m: m.group(1) + replacement + m.group(3),
            updated,
        )

    return updated


# ---------------------------------------------------------------------------
# GitHub API helpers
# ---------------------------------------------------------------------------


def github_api(method: str, endpoint: str, **kwargs: Any) -> requests.Response:
    """Make a GitHub API request."""
    token = os.environ.get("GITHUB_TOKEN", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    url = f"https://api.github.com/repos/{repo}{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    resp = requests.request(method, url, headers=headers, **kwargs)
    resp.raise_for_status()
    return resp


def update_issue(issue_number: int, body: str | None = None, labels_add: list[str] | None = None) -> None:
    """Update an issue's body and/or labels."""
    if body is not None:
        github_api("PATCH", f"/issues/{issue_number}", json={"body": body})

    if labels_add:
        github_api("POST", f"/issues/{issue_number}/labels", json={"labels": labels_add})


def post_comment(issue_number: int, comment: str) -> None:
    """Post a comment on an issue."""
    github_api("POST", f"/issues/{issue_number}/comments", json={"body": comment})


# ---------------------------------------------------------------------------
# Build the summary comment
# ---------------------------------------------------------------------------


def build_comment(
    suggestions: dict[str, Any],
    filled: dict[str, Any],
    entry_type: str | None,
) -> str:
    """Build a Markdown comment summarizing the AI enrichment."""
    verdict = suggestions.get("verdict", "accepted")
    reason = suggestions.get("verdict_reason", "")
    type_label = entry_type or "catalogue"

    lines: list[str] = []

    # Verdict header
    if verdict == "accepted":
        lines.append(f"## 🤖 AI Review — Accepted")
        lines.append("")
        lines.append(f"This **{type_label}** submission looks relevant to CollabAtlas. {reason}")
    elif verdict == "needs-discussion":
        lines.append(f"## 🤖 AI Review — Needs Discussion")
        lines.append("")
        lines.append(f"⚠️ {reason}")
        lines.append("")
        lines.append("A maintainer will review this submission to decide whether it fits the atlas.")
    else:  # rejected
        lines.append(f"## 🤖 AI Review — Off Topic")
        lines.append("")
        lines.append(f"❌ {reason}")
        lines.append("")
        lines.append("This submission doesn't appear to be related to collaborative tools, methods, or practices. "
                      "A maintainer may close this issue. If you believe this is a mistake, please explain "
                      "how this entry relates to collaboration.")

    # Enrichments applied (only for accepted)
    if verdict == "accepted":
        changes: list[str] = []

        for field in ("domains", "collaboration-types", "scales", "modalities"):
            if field not in filled and field in suggestions and suggestions[field]:
                values = ", ".join(f"`{v}`" for v in suggestions[field])
                changes.append(f"- **{field}**: {values}")

        if "maturity" in suggestions and "maturity" not in filled:
            changes.append(f"- **maturity**: `{suggestions['maturity']}`")

        if "description" in suggestions and "description" not in filled:
            changes.append(f"- **description**: enriched (was too short or missing)")

        if "related_entries" in suggestions and suggestions["related_entries"]:
            rels = ", ".join(f"`{r}`" for r in suggestions["related_entries"])
            changes.append(f"- **related entries**: {rels}")

        if "tags" in suggestions and suggestions["tags"]:
            tags = ", ".join(f"`{t}`" for t in suggestions["tags"])
            changes.append(f"- **tags**: {tags}")

        if changes:
            lines.append("")
            lines.append("### Suggested enrichments (applied to issue body where possible)")
            lines.append("")
            lines.extend(changes)
            lines.append("")
            lines.append("> 💡 Review the changes above and edit the issue if anything looks wrong.")
        else:
            lines.append("")
            lines.append("The submission looks complete — no enrichments needed.")

    lines.append("")
    lines.append("---")
    lines.append("*This review was generated automatically by Claude Haiku. "
                 "A human maintainer will make the final decision.*")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry point: parse issue, call Claude, update issue, post comment."""
    issue_body = os.environ.get("ISSUE_BODY", "")
    issue_title = os.environ.get("ISSUE_TITLE", "")
    issue_labels = os.environ.get("ISSUE_LABELS", "")
    issue_number = int(os.environ.get("ISSUE_NUMBER", "0"))

    if not issue_body.strip():
        print("Error: ISSUE_BODY is empty.", file=sys.stderr)
        sys.exit(1)

    if issue_number == 0:
        print("Error: ISSUE_NUMBER not set.", file=sys.stderr)
        sys.exit(1)

    # Parse issue
    sections = parse_issue_body(issue_body)
    entry_type = detect_entry_type(issue_labels, issue_title)

    # For quick-add issues, use the Entry type field
    if not entry_type:
        raw_type = get_text(sections, "Entry type")
        if raw_type:
            entry_type = raw_type.lower().strip()

    filled = extract_filled_fields(sections)
    print(f"Entry type: {entry_type}")
    print(f"Filled fields: {list(filled.keys())}")

    # Load catalogue context
    entries = load_existing_entries()
    taxonomy_context = build_taxonomy_context()
    entries_context = build_entries_context(entries)

    # Call Claude
    print("Calling Claude Haiku for enrichment...")
    suggestions = call_claude(filled, entry_type, taxonomy_context, entries_context)
    print(f"Verdict: {suggestions.get('verdict', 'unknown')}")
    print(f"Suggestions: {json.dumps(suggestions, indent=2, ensure_ascii=False)}")

    verdict = suggestions.get("verdict", "accepted")

    # Update issue body (only for accepted submissions)
    if verdict == "accepted":
        updated_body = update_issue_body(issue_body, suggestions, filled)
        if updated_body != issue_body:
            print("Updating issue body with enrichments...")
            update_issue(issue_number, body=updated_body)

    # Add labels
    labels_to_add = ["ai-enriched"]
    if verdict == "needs-discussion":
        labels_to_add.append("needs-review")
    elif verdict == "rejected":
        labels_to_add.append("off-topic")

    update_issue(issue_number, labels_add=labels_to_add)

    # Post comment
    comment = build_comment(suggestions, filled, entry_type)
    post_comment(issue_number, comment)
    print("Comment posted successfully.")


if __name__ == "__main__":
    main()
