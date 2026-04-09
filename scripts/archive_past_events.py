#!/usr/bin/env python3
"""Archive past events by setting status to 'past'."""
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
EVENTS_FILE = ROOT / "data" / "events.yaml"


def main() -> None:
    if not EVENTS_FILE.exists():
        print("No events file found")
        return

    with open(EVENTS_FILE, encoding="utf-8") as f:
        events = yaml.safe_load(f) or []

    today = date.today().isoformat()
    changed = 0
    for event in events:
        if event.get("status") == "upcoming":
            end = event.get("date_end") or event.get("date_start", "")
            if end and end < today:
                event["status"] = "past"
                changed += 1
                print(f"  Archived: {event['title']}")

    if changed == 0:
        print("No events to archive.")
        return

    with open(EVENTS_FILE, "w", encoding="utf-8") as f:
        yaml.dump(events, f, default_flow_style=False,
                  allow_unicode=True, sort_keys=False, width=120)

    print(f"Archived {changed} events.")


if __name__ == "__main__":
    main()
