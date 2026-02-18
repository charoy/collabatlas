#!/usr/bin/env python3
"""Generate a freshness report for CollabAtlas entries.

Flags entries whose last_reviewed date is older than a threshold (default 12 months).
Outputs a Markdown report suitable for creating a GitHub issue.
"""

import sys
from datetime import date, timedelta
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
ENTRIES_DIR = ROOT / "data" / "entries"
REPORT_FILE = ROOT / "freshness-report.md"
STALE_THRESHOLD_DAYS = 365


def main():
    today = date.today()
    threshold = today - timedelta(days=STALE_THRESHOLD_DAYS)
    stale_entries = []

    for yaml_file in sorted(ENTRIES_DIR.rglob("*.yaml")):
        with open(yaml_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data:
            continue

        last_reviewed = data.get("last_reviewed")
        if not last_reviewed:
            stale_entries.append(
                {
                    "file": str(yaml_file.relative_to(ROOT)),
                    "title": data.get("title", yaml_file.stem),
                    "last_reviewed": "never",
                    "domains": data.get("domains", []),
                }
            )
            continue

        if isinstance(last_reviewed, str):
            last_reviewed = date.fromisoformat(last_reviewed)

        if last_reviewed < threshold:
            stale_entries.append(
                {
                    "file": str(yaml_file.relative_to(ROOT)),
                    "title": data.get("title", yaml_file.stem),
                    "last_reviewed": str(last_reviewed),
                    "domains": data.get("domains", []),
                }
            )

    if not stale_entries:
        print("No stale entries found.")
        # Remove report file if it exists so the CI step doesn't create an issue
        REPORT_FILE.unlink(missing_ok=True)
        return

    # Group by domain for domain editors
    by_domain: dict[str, list] = {}
    for entry in stale_entries:
        for domain in entry["domains"]:
            by_domain.setdefault(domain, []).append(entry)
        if not entry["domains"]:
            by_domain.setdefault("uncategorized", []).append(entry)

    lines = [
        f"# Freshness Report — {today.isoformat()}",
        "",
        f"**{len(stale_entries)} entries** have not been reviewed in over "
        f"{STALE_THRESHOLD_DAYS} days.",
        "",
    ]

    for domain in sorted(by_domain):
        lines.append(f"## {domain}")
        lines.append("")
        for entry in by_domain[domain]:
            lines.append(
                f"- **{entry['title']}** (`{entry['file']}`) — "
                f"last reviewed: {entry['last_reviewed']}"
            )
        lines.append("")

    lines.append("---")
    lines.append(
        "Domain editors: please review the entries in your area and update "
        "`last_reviewed` dates after verification."
    )

    report = "\n".join(lines)
    REPORT_FILE.write_text(report, encoding="utf-8")
    print(f"Freshness report written to {REPORT_FILE}")
    print(f"{len(stale_entries)} stale entries found.")


if __name__ == "__main__":
    main()
