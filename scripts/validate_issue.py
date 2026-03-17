#!/usr/bin/env python3
"""Validate a GitHub Issue Form submission and post a helpful feedback comment.

This script is invoked by the ``validate-issue.yml`` GitHub Action when
a new issue is opened with the ``new-entry`` label.  It parses the issue
body, checks for common problems, and suggests improvements.

Environment variables (set by the calling GitHub Action):
    ISSUE_BODY      Full Markdown body of the issue
    ISSUE_TITLE     Issue title (e.g. "[New Tool] My Cool Tool")
    ISSUE_LABELS    Comma-separated labels (e.g. "new-entry,tool,triage")
"""

from __future__ import annotations

import os
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import yaml

# Import shared parsing utilities
from issue_parser import (
    COLLAB_TYPE_MAP,
    DOMAIN_MAP,
    MATURITY_MAP,
    MODALITY_MAP,
    SCALE_MAP,
    TYPE_DIRS,
    detect_entry_type,
    extract_clean_title,
    get_checked_count,
    get_comma_list,
    get_text,
    get_total_checkboxes,
    parse_issue_body,
    title_to_id,
)

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "entries"

# ---------------------------------------------------------------------------
# Load existing entries for suggestions
# ---------------------------------------------------------------------------


def load_existing_entries() -> list[dict[str, Any]]:
    """Load all existing YAML entries for tag/related suggestions."""
    entries: list[dict[str, Any]] = []
    for type_dir in TYPE_DIRS.values():
        entry_dir = DATA_DIR / type_dir
        if not entry_dir.exists():
            continue
        for yaml_file in entry_dir.glob("*.yaml"):
            try:
                with open(yaml_file, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if data:
                    entries.append(data)
            except Exception:
                continue
    return entries


def collect_existing_tags(entries: list[dict[str, Any]]) -> dict[str, int]:
    """Collect all tags from existing entries with their frequency."""
    tag_counts: dict[str, int] = {}
    for entry in entries:
        for tag in entry.get("tags", []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    return tag_counts


def suggest_tags(description: str, existing_tags: dict[str, int]) -> list[str]:
    """Suggest tags based on description keywords matching existing tags."""
    if not description:
        return []
    desc_lower = description.lower()
    suggestions: list[str] = []
    for tag, _count in sorted(existing_tags.items(), key=lambda x: -x[1]):
        # Check if the tag or a variant appears in the description
        tag_words = tag.replace("-", " ").replace("_", " ")
        if tag_words in desc_lower or tag in desc_lower:
            suggestions.append(tag)
        if len(suggestions) >= 5:
            break
    return suggestions


def suggest_related_entries(
    title: str, entries: list[dict[str, Any]]
) -> list[str]:
    """Suggest related entries based on fuzzy title matching."""
    if not title:
        return []
    title_lower = title.lower()
    scored: list[tuple[float, str, str]] = []
    for entry in entries:
        entry_title = entry.get("title", "")
        entry_id = entry.get("id", "")
        ratio = SequenceMatcher(None, title_lower, entry_title.lower()).ratio()
        # Also check keyword overlap
        title_words = set(title_lower.split())
        entry_words = set(entry_title.lower().split())
        overlap = len(title_words & entry_words)
        score = ratio + (overlap * 0.2)
        if score > 0.3 and entry_id != title_to_id(title):
            scored.append((score, entry_id, entry_title))
    scored.sort(reverse=True)
    return [f"`{eid}` ({etitle})" for _, eid, etitle in scored[:5]]


# ---------------------------------------------------------------------------
# Validation checks
# ---------------------------------------------------------------------------


class Check:
    """A single validation check result."""

    def __init__(self, passed: bool, message: str, suggestion: str = ""):
        self.passed = passed
        self.message = message
        self.suggestion = suggestion

    def to_markdown(self) -> str:
        icon = "✅" if self.passed else "⚠️"
        line = f"{icon} {self.message}"
        if self.suggestion:
            line += f"\n   > {self.suggestion}"
        return line


def validate_issue(
    sections: dict[str, str],
    entry_type: str | None,
    entries: list[dict[str, Any]],
) -> list[Check]:
    """Run all validation checks and return results."""
    checks: list[Check] = []

    # --- Title ---
    title = get_text(sections, "Title")
    if title:
        checks.append(Check(True, "Title provided"))
        # Check for duplicate
        existing_ids = {e.get("id") for e in entries}
        new_id = title_to_id(title)
        if new_id in existing_ids:
            checks.append(Check(
                False,
                f"An entry with ID `{new_id}` already exists",
                "If this is an update, consider using the Update Entry template instead.",
            ))
    else:
        checks.append(Check(False, "Title is missing"))

    # --- Tagline ---
    tagline = get_text(sections, "Tagline")
    if tagline:
        if len(tagline) > 200:
            checks.append(Check(
                False,
                f"Tagline is {len(tagline)} characters (max 200)",
                "Try to shorten it to a single concise sentence.",
            ))
        else:
            checks.append(Check(True, f"Tagline provided ({len(tagline)} chars)"))
    else:
        checks.append(Check(False, "Tagline is missing"))

    # --- Description ---
    description = get_text(sections, "Full Description")
    if description:
        if len(description) < 80:
            checks.append(Check(
                False,
                f"Description is quite short ({len(description)} chars)",
                "Aim for 2-5 sentences explaining what it is, how it supports collaboration, and why it matters.",
            ))
        else:
            checks.append(Check(True, f"Description provided ({len(description)} chars)"))
    else:
        checks.append(Check(False, "Description is missing"))

    # --- Website URL (tools, datasets) ---
    if entry_type in ("tool", "dataset"):
        url_label = "Website URL" if entry_type == "tool" else "Source URL"
        url = get_text(sections, url_label)
        if url:
            if re.match(r"^https?://", url):
                checks.append(Check(True, f"{url_label} provided"))
            else:
                checks.append(Check(
                    False,
                    f"{url_label} doesn't look like a URL",
                    "Make sure it starts with https:// or http://",
                ))
        else:
            checks.append(Check(False, f"{url_label} is missing"))

    # --- Domains ---
    domain_count = get_checked_count(
        sections, "Relevant Domains (select all that apply)"
    )
    domain_total = get_total_checkboxes(
        sections, "Relevant Domains (select all that apply)"
    )
    if domain_count > 0:
        checks.append(Check(True, f"{domain_count} domain(s) selected"))
    else:
        checks.append(Check(
            False,
            "No domains selected",
            "Select at least one domain where this entry is relevant.",
        ))

    # --- Collaboration Types ---
    collab_count = get_checked_count(
        sections, "Collaboration Types (select all that apply)"
    )
    if collab_count > 0:
        checks.append(Check(True, f"{collab_count} collaboration type(s) selected"))
    else:
        checks.append(Check(
            False,
            "No collaboration types selected",
            "Select at least one type of collaboration this entry involves.",
        ))

    # --- Scale ---
    scale_count = get_checked_count(
        sections, "Scale (select all that apply)"
    )
    if scale_count > 0:
        checks.append(Check(True, f"{scale_count} scale(s) selected"))
    else:
        checks.append(Check(
            False,
            "No scale selected",
            "Select at least one group size this entry works with.",
        ))

    # --- Modality ---
    modality_count = get_checked_count(
        sections, "Modality (select all that apply)"
    )
    if modality_count > 0:
        checks.append(Check(True, f"{modality_count} modality/modalities selected"))
    else:
        checks.append(Check(
            False,
            "No modality selected",
            "Select at least one: In-Person, Remote, or Hybrid.",
        ))

    # --- Maturity ---
    maturity = get_text(sections, "Maturity Level")
    if maturity:
        checks.append(Check(True, "Maturity level selected"))
    else:
        checks.append(Check(
            False,
            "Maturity level not selected",
            "Choose Emerging, Established, or Well-Documented.",
        ))

    # --- Tags (suggestion, not required) ---
    tags = get_comma_list(sections, "Tags (comma-separated)")
    existing_tags = collect_existing_tags(entries)
    if tags:
        checks.append(Check(True, f"{len(tags)} tag(s) provided"))
    else:
        suggested = suggest_tags(description or "", existing_tags)
        if suggested:
            tag_list = ", ".join(f"`{t}`" for t in suggested)
            checks.append(Check(
                False,
                "No tags provided",
                f"Consider adding tags like: {tag_list}",
            ))
        else:
            checks.append(Check(
                False,
                "No tags provided",
                "Tags help with search and discovery. Add a few keywords.",
            ))

    # --- Related entries (suggestion, not required) ---
    related = get_comma_list(
        sections, "Related CollabAtlas Entries (comma-separated IDs)"
    )
    if related:
        # Check that related IDs actually exist
        existing_ids = {e.get("id") for e in entries}
        unknown = [r for r in related if r not in existing_ids]
        if unknown:
            unknown_list = ", ".join(f"`{u}`" for u in unknown)
            checks.append(Check(
                False,
                f"Some related entry IDs not found: {unknown_list}",
                "Browse the catalogue to find valid entry IDs (the URL slug is the ID).",
            ))
        else:
            checks.append(Check(True, f"{len(related)} related entry/entries linked"))
    else:
        suggested = suggest_related_entries(title or "", entries)
        if suggested:
            rel_list = ", ".join(suggested[:3])
            checks.append(Check(
                False,
                "No related entries linked",
                f"You might want to relate this to: {rel_list}",
            ))

    return checks


# ---------------------------------------------------------------------------
# Comment builder
# ---------------------------------------------------------------------------


def build_comment(
    entry_type: str | None,
    checks: list[Check],
) -> str:
    """Build a Markdown comment from validation results."""
    type_label = entry_type or "catalogue"
    passed = sum(1 for c in checks if c.passed)
    total = len(checks)
    has_issues = any(not c.passed for c in checks)

    lines: list[str] = []
    lines.append(
        f"👋 Thanks for submitting a new **{type_label}** entry! "
        f"Here's a quick review ({passed}/{total} checks passed):"
    )
    lines.append("")

    for check in checks:
        lines.append(check.to_markdown())

    lines.append("")

    if has_issues:
        lines.append(
            "💡 **Don't worry** — these are suggestions, not blockers. "
            "A maintainer will review your submission and can help fill in any gaps."
        )
    else:
        lines.append(
            "🎉 **Looks great!** All checks passed. "
            "A maintainer will review your submission shortly."
        )

    lines.append("")
    lines.append(
        "📚 See the [Contributing Guide]"
        "(https://charoy.github.io/collabatlas/guides/contributing/) "
        "for taxonomy reference tables and tips."
    )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry point: parse issue, validate, and output comment."""
    issue_body = os.environ.get("ISSUE_BODY", "")
    issue_title = os.environ.get("ISSUE_TITLE", "")
    issue_labels = os.environ.get("ISSUE_LABELS", "")

    if not issue_body.strip():
        print("Error: ISSUE_BODY is empty.", file=sys.stderr)
        sys.exit(1)

    sections = parse_issue_body(issue_body)
    entry_type = detect_entry_type(issue_labels, issue_title)
    entries = load_existing_entries()

    checks = validate_issue(sections, entry_type, entries)
    comment = build_comment(entry_type, checks)

    # Write comment to file for the workflow to pick up
    output_file = os.environ.get("COMMENT_OUTPUT", "")
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(comment)
        print(f"Comment written to {output_file}")
    else:
        # Print to stdout for local testing
        print(comment)


if __name__ == "__main__":
    main()
