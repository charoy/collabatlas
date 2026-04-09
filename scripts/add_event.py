#!/usr/bin/env python3
"""Add an event from a GitHub issue to data/events.yaml."""
import os
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from issue_parser import parse_event_issue

ROOT = Path(__file__).resolve().parent.parent
EVENTS_FILE = ROOT / "data" / "events.yaml"


def main() -> None:
    body = os.environ.get("ISSUE_BODY", "")
    if not body:
        print("No issue body found")
        sys.exit(1)

    event = parse_event_issue(body)
    if not event["title"]:
        print("Could not parse event title")
        sys.exit(1)

    # Load existing events
    events = []
    if EVENTS_FILE.exists():
        with open(EVENTS_FILE, encoding="utf-8") as f:
            events = yaml.safe_load(f) or []

    # Check for duplicates
    existing_ids = {e["id"] for e in events}
    if event["id"] in existing_ids:
        print(f"Event {event['id']} already exists, skipping")
        sys.exit(0)

    events.append(event)

    # Sort by date_start ascending
    events.sort(key=lambda e: e.get("date_start", ""))

    with open(EVENTS_FILE, "w", encoding="utf-8") as f:
        yaml.dump(events, f, default_flow_style=False,
                  allow_unicode=True, sort_keys=False, width=120)

    print(f"Added event: {event['title']}")


if __name__ == "__main__":
    main()
