# Editorial Spotlight & Events Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add editorial curation ("A la une" spotlight) and an events system (conferences, seminars, schools) to CollabAtlas, with automated suggestion, contribution, and archiving workflows.

**Architecture:** Data-driven approach using Hugo's `data/` directory. `data/featured.yaml` for editorial picks. `data/events.yaml` for events. New homepage sections inserted between stats and "Recently Added". Dedicated `/events/` page. Three GitHub Actions workflows for event automation: issue-to-event, weekly AI suggestions, and auto-archiving.

**Tech Stack:** Hugo templates, YAML data files, GitHub Actions, Claude Sonnet (Anthropic Python SDK), GitHub Issues

---

### Task 1: Featured Spotlight Data & Template

**Files:**
- Create: `data/featured.yaml`
- Modify: `layouts/index.html`
- Modify: `assets/css/main.css`

**Step 1: Create `data/featured.yaml` with seed data**

```yaml
# data/featured.yaml
# Editorial picks shown in the "A la une" section on the homepage.
# Supports: entry (catalogue), article (research), event, custom.
# Max 3 items displayed.

- type: entry
  id: miro
  section: tools
  highlight: "Widely adopted for remote participatory design workshops"

- type: article
  title: "The CSCW Research Landscape"
  url: "https://doi.org/example"
  authors: "Smith et al., 2025"
  highlight: "A recent survey mapping the field of computer-supported cooperative work"

- type: custom
  title: "Call for Contributions"
  description: "CollabAtlas is looking for case studies in collaborative urban planning"
  url: "/catalogue/case-studies/"
  badge: "Call"
```

**Step 2: Add spotlight section to `layouts/index.html`**

Insert after the `.home-stats` div (line ~45), before the Recently Added section. The template iterates over `$.Site.Data.featured`, handling each `type`:

- `entry`: looks up the catalogue page via `.Site.GetPage` using the `section` field, merges YAML data for tagline
- `article`: renders title, authors, URL directly
- `custom`: renders title, description, URL, badge

```html
{{ $featured := .Site.Data.featured }}
{{ if $featured }}
<section class="home-section">
  <div class="home-section-header">
    <h2 class="home-section-title">A la une</h2>
  </div>
  <div class="featured-grid">
    {{ range first 3 $featured }}
      {{ if eq .type "entry" }}
        {{ $path := printf "catalogue/%s/%s" .section .id }}
        {{ $page := site.GetPage $path }}
        {{ if $page }}
        <a href="{{ $page.RelPermalink }}" class="featured-card featured-entry">
          <span class="featured-badge">{{ .section | singularize | title }}</span>
          <strong>{{ $page.Title }}</strong>
          {{ with .highlight }}<p class="featured-highlight">{{ . }}</p>{{ end }}
        </a>
        {{ end }}
      {{ else if eq .type "article" }}
        <a href="{{ .url }}" target="_blank" rel="noopener" class="featured-card featured-article">
          <span class="featured-badge">Research</span>
          <strong>{{ .title }}</strong>
          {{ with .authors }}<span class="featured-meta">{{ . }}</span>{{ end }}
          {{ with .highlight }}<p class="featured-highlight">{{ . }}</p>{{ end }}
        </a>
      {{ else if eq .type "event" }}
        {{ $events := site.Data.events }}
        {{ range $events }}
          {{ if eq .id ($.id | default "") }}
          <a href="{{ .url }}" target="_blank" rel="noopener" class="featured-card featured-event">
            <span class="featured-badge">Event</span>
            <strong>{{ .title }}</strong>
            <span class="featured-meta">{{ .date_start }} · {{ .location }}</span>
            {{ with $.highlight }}<p class="featured-highlight">{{ . }}</p>{{ end }}
          </a>
          {{ end }}
        {{ end }}
      {{ else if eq .type "custom" }}
        <a href="{{ .url | relURL }}" class="featured-card featured-custom">
          {{ with .badge }}<span class="featured-badge">{{ . }}</span>{{ end }}
          <strong>{{ .title }}</strong>
          {{ with .description }}<p class="featured-highlight">{{ . }}</p>{{ end }}
        </a>
      {{ end }}
    {{ end }}
  </div>
</section>
{{ end }}
```

**Step 3: Add CSS for `.featured-grid` and `.featured-card`**

```css
/* Featured / Spotlight */
.featured-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(18rem, 1fr));
  gap: 1.25rem;
}
.featured-card {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1.25rem;
  border: 2px solid var(--color-border);
  border-radius: var(--radius);
  text-decoration: none;
  color: inherit;
  transition: border-color 0.2s, box-shadow 0.2s, transform 0.2s;
}
.featured-card:hover {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
}
.featured-badge {
  display: inline-block;
  width: fit-content;
  padding: 0.15rem 0.6rem;
  border-radius: 1rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.featured-entry .featured-badge { background: #dcfce7; color: #166534; }
.featured-article .featured-badge { background: #dbeafe; color: #1e40af; }
.featured-event .featured-badge { background: #fef3c7; color: #92400e; }
.featured-custom .featured-badge { background: #f3e8ff; color: #6b21a8; }
.featured-highlight {
  font-size: 0.9rem;
  color: var(--color-text-muted);
  margin: 0;
}
.featured-meta {
  font-size: 0.8rem;
  color: var(--color-text-muted);
}
```

**Step 4: Build and verify**

Run: `hugo --gc --minify 2>&1 | tail -5`
Expected: Build succeeds with no errors.

**Step 5: Commit**

```bash
git add data/featured.yaml layouts/index.html assets/css/main.css
git commit -m "feat: add editorial spotlight section to homepage"
```

---

### Task 2: Events Data & Homepage Section

**Files:**
- Create: `data/events.yaml`
- Modify: `layouts/index.html`
- Modify: `assets/css/main.css`

**Step 1: Create `data/events.yaml` with seed data**

```yaml
- id: cscw-2026
  title: "CSCW 2026"
  type: conference
  date_start: "2026-11-07"
  date_end: "2026-11-11"
  location: "San Jose, CA, USA"
  url: "https://cscw.acm.org/2026/"
  description: "ACM Conference on Computer-Supported Cooperative Work and Social Computing"
  domains: [cscw]
  status: upcoming

- id: chi-2026
  title: "CHI 2026"
  type: conference
  date_start: "2026-04-25"
  date_end: "2026-04-30"
  location: "Yokohama, Japan"
  url: "https://chi2026.acm.org/"
  description: "ACM CHI Conference on Human Factors in Computing Systems"
  domains: [cscw, digital-humanities]
  status: upcoming

- id: ecscw-2026
  title: "ECSCW 2026"
  type: conference
  date_start: "2026-06-14"
  date_end: "2026-06-18"
  location: "Zurich, Switzerland"
  url: "https://ecscw.eusset.eu/2026/"
  description: "European Conference on Computer-Supported Cooperative Work"
  domains: [cscw]
  status: upcoming

- id: coop-school-2026
  title: "COOP Summer School 2026"
  type: school
  date_start: "2026-07-06"
  date_end: "2026-07-10"
  location: "Nancy, France"
  url: ""
  description: "Summer school on cooperative systems design and research methods"
  domains: [cscw, education]
  status: upcoming
```

**Step 2: Add "Upcoming Events" section to `layouts/index.html`**

Insert after the spotlight section, before "Recently Added". Filters events with `status: upcoming`, sorts by `date_start`, shows first 3.

```html
{{ $events := .Site.Data.events }}
{{ $upcoming := slice }}
{{ range $events }}
  {{ if eq .status "upcoming" }}
    {{ $upcoming = $upcoming | append . }}
  {{ end }}
{{ end }}
{{ $upcoming = sort $upcoming "date_start" "asc" }}
{{ $upcomingDisplay := first 3 $upcoming }}
{{ if $upcomingDisplay }}
<section class="home-section">
  <div class="home-section-header">
    <h2 class="home-section-title">Upcoming Events</h2>
    <a href="{{ "events" | relURL }}/" class="home-section-link">All events →</a>
  </div>
  <div class="events-grid">
    {{ range $upcomingDisplay }}
    <a href="{{ .url }}" target="_blank" rel="noopener" class="event-card">
      <div class="event-date">
        <span class="event-month">{{ (time .date_start).Format "Jan" }}</span>
        <span class="event-day">{{ (time .date_start).Format "02" }}</span>
      </div>
      <div class="event-info">
        <span class="event-type-badge event-type-{{ .type }}">{{ .type }}</span>
        <strong>{{ .title }}</strong>
        <span class="event-location">{{ .location }}</span>
        {{ with .description }}<p class="event-desc">{{ . }}</p>{{ end }}
      </div>
    </a>
    {{ end }}
  </div>
</section>
{{ end }}
```

**Step 3: Add CSS for events cards**

```css
/* Events */
.events-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(20rem, 1fr));
  gap: 1.25rem;
}
.event-card {
  display: flex;
  gap: 1rem;
  padding: 1.25rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  text-decoration: none;
  color: inherit;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.event-card:hover {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-md);
}
.event-date {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 3.5rem;
  padding: 0.5rem;
  background: var(--color-surface, #f8fafc);
  border-radius: var(--radius);
  text-align: center;
}
.event-month {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--color-primary);
}
.event-day {
  font-size: 1.5rem;
  font-weight: 700;
  line-height: 1;
}
.event-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.event-type-badge {
  display: inline-block;
  width: fit-content;
  padding: 0.1rem 0.5rem;
  border-radius: 1rem;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
}
.event-type-conference { background: #dbeafe; color: #1e40af; }
.event-type-seminar { background: #dcfce7; color: #166534; }
.event-type-school { background: #fef3c7; color: #92400e; }
.event-type-workshop { background: #f3e8ff; color: #6b21a8; }
.event-location {
  font-size: 0.85rem;
  color: var(--color-text-muted);
}
.event-desc {
  font-size: 0.85rem;
  color: var(--color-text-muted);
  margin: 0.25rem 0 0;
}
```

**Step 4: Build and verify**

Run: `hugo --gc --minify 2>&1 | tail -5`
Expected: Build succeeds.

**Step 5: Commit**

```bash
git add data/events.yaml layouts/index.html assets/css/main.css
git commit -m "feat: add events data and Upcoming Events section to homepage"
```

---

### Task 3: Dedicated Events Page

**Files:**
- Create: `content/events/_index.md`
- Create: `layouts/events/list.html`
- Modify: `hugo.toml` (add Events to menu)
- Modify: `assets/css/main.css`

**Step 1: Create `content/events/_index.md`**

```markdown
---
title: "Events"
description: "Conferences, seminars, workshops, and schools related to collaborative research"
---
```

**Step 2: Create `layouts/events/list.html`**

Full page listing upcoming events (sorted by date asc) then past events (sorted by date desc). Filterable by type via CSS class toggles (JS).

```html
{{ define "main" }}
<section class="events-page">
  <header class="page-header">
    <div class="page-header-row">
      <h1>{{ .Title }}</h1>
      <a href="{{ .Site.Params.github_repo }}/issues/new?template=new-event.yml" target="_blank" rel="noopener" class="btn btn-outline btn-sm">+ Suggest an Event</a>
    </div>
    {{ with .Params.description }}<p class="page-description">{{ . }}</p>{{ end }}
  </header>

  {{ $events := .Site.Data.events }}

  <div class="events-filters">
    <button class="event-filter-btn active" data-filter="all">All</button>
    <button class="event-filter-btn" data-filter="conference">Conferences</button>
    <button class="event-filter-btn" data-filter="seminar">Seminars</button>
    <button class="event-filter-btn" data-filter="workshop">Workshops</button>
    <button class="event-filter-btn" data-filter="school">Schools</button>
  </div>

  {{ $upcoming := slice }}
  {{ $past := slice }}
  {{ range $events }}
    {{ if eq .status "upcoming" }}
      {{ $upcoming = $upcoming | append . }}
    {{ else }}
      {{ $past = $past | append . }}
    {{ end }}
  {{ end }}
  {{ $upcoming = sort $upcoming "date_start" "asc" }}
  {{ $past = sort $past "date_start" "desc" }}

  {{ if $upcoming }}
  <h2 class="events-section-title">Upcoming</h2>
  <div class="events-list">
    {{ range $upcoming }}
    <a href="{{ .url }}" target="_blank" rel="noopener" class="event-row" data-type="{{ .type }}">
      <div class="event-date">
        <span class="event-month">{{ (time .date_start).Format "Jan" }}</span>
        <span class="event-day">{{ (time .date_start).Format "02" }}</span>
        <span class="event-year">{{ (time .date_start).Format "2006" }}</span>
      </div>
      <div class="event-info">
        <span class="event-type-badge event-type-{{ .type }}">{{ .type }}</span>
        <strong>{{ .title }}</strong>
        <span class="event-location">{{ .location }}</span>
        {{ with .date_end }}
          <span class="event-dates">{{ (time $.date_start).Format "Jan 2" }} – {{ (time .).Format "Jan 2, 2006" }}</span>
        {{ end }}
      </div>
      <div class="event-desc-col">
        {{ with .description }}<p class="event-desc">{{ . }}</p>{{ end }}
      </div>
    </a>
    {{ end }}
  </div>
  {{ end }}

  {{ if $past }}
  <h2 class="events-section-title events-past-title">Past Events</h2>
  <div class="events-list events-past">
    {{ range $past }}
    <a href="{{ .url }}" target="_blank" rel="noopener" class="event-row" data-type="{{ .type }}">
      <div class="event-date">
        <span class="event-month">{{ (time .date_start).Format "Jan" }}</span>
        <span class="event-day">{{ (time .date_start).Format "02" }}</span>
        <span class="event-year">{{ (time .date_start).Format "2006" }}</span>
      </div>
      <div class="event-info">
        <span class="event-type-badge event-type-{{ .type }}">{{ .type }}</span>
        <strong>{{ .title }}</strong>
        <span class="event-location">{{ .location }}</span>
      </div>
    </a>
    {{ end }}
  </div>
  {{ end }}
</section>

<script>
document.addEventListener('DOMContentLoaded', function() {
  const btns = document.querySelectorAll('.event-filter-btn');
  const rows = document.querySelectorAll('.event-row');
  btns.forEach(function(btn) {
    btn.addEventListener('click', function() {
      btns.forEach(function(b) { b.classList.remove('active'); });
      btn.classList.add('active');
      var filter = btn.dataset.filter;
      rows.forEach(function(row) {
        row.style.display = (filter === 'all' || row.dataset.type === filter) ? '' : 'none';
      });
    });
  });
});
</script>
{{ end }}
```

**Step 3: Add events page CSS**

```css
/* Events page */
.events-page { max-width: 74rem; margin: 0 auto; padding: 2rem; }
.events-filters {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}
.event-filter-btn {
  padding: 0.4rem 1rem;
  border: 1px solid var(--color-border);
  border-radius: 2rem;
  background: transparent;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s;
}
.event-filter-btn.active,
.event-filter-btn:hover {
  background: var(--color-primary);
  color: #fff;
  border-color: var(--color-primary);
}
.events-section-title {
  font-size: 1.25rem;
  margin: 2rem 0 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid var(--color-border);
}
.events-past-title { color: var(--color-text-muted); }
.events-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.event-row {
  display: flex;
  gap: 1.25rem;
  align-items: flex-start;
  padding: 1rem 1.25rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  text-decoration: none;
  color: inherit;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.event-row:hover {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-md);
}
.events-past .event-row { opacity: 0.7; }
.events-past .event-row:hover { opacity: 1; }
.event-year {
  font-size: 0.7rem;
  color: var(--color-text-muted);
}
.event-dates {
  font-size: 0.8rem;
  color: var(--color-text-muted);
}
.event-desc-col {
  flex: 1;
  min-width: 0;
}
.event-desc-col .event-desc {
  margin: 0;
}
@media (max-width: 640px) {
  .event-row { flex-wrap: wrap; }
  .event-desc-col { width: 100%; }
}
```

**Step 4: Add "Events" to nav menu in `hugo.toml`**

Insert after Blog (weight 6), before About (weight 7):

```toml
  [[menu.main]]
    name = 'Events'
    url = '/events/'
    weight = 6
```

And bump About to weight 8.

**Step 5: Build and verify**

Run: `hugo --gc --minify 2>&1 | tail -5`
Expected: Build succeeds, `/events/` page generated.

**Step 6: Commit**

```bash
git add content/events/_index.md layouts/events/list.html hugo.toml assets/css/main.css
git commit -m "feat: add dedicated events page with filtering"
```

---

### Task 4: GitHub Issue Template for Events

**Files:**
- Create: `.github/ISSUE_TEMPLATE/new-event.yml`

**Step 1: Create the issue template**

```yaml
name: "Suggest an Event"
description: "Suggest a conference, seminar, workshop, or school related to collaborative research."
title: "[New Event] "
labels: ["new-event", "triage"]
body:
  - type: markdown
    attributes:
      value: |
        ## Suggest an Event

        Know of an upcoming event relevant to collaborative research? Fill in the details below.

  - type: input
    id: title
    attributes:
      label: Event name
      placeholder: "e.g., CSCW 2027"
    validations:
      required: true

  - type: dropdown
    id: event_type
    attributes:
      label: Event type
      options:
        - conference
        - seminar
        - workshop
        - school
    validations:
      required: true

  - type: input
    id: date_start
    attributes:
      label: Start date
      description: "YYYY-MM-DD format"
      placeholder: "2027-01-15"
    validations:
      required: true

  - type: input
    id: date_end
    attributes:
      label: End date
      description: "YYYY-MM-DD format (same as start for single-day events)"
      placeholder: "2027-01-18"
    validations:
      required: true

  - type: input
    id: location
    attributes:
      label: Location
      placeholder: "City, Country"
    validations:
      required: true

  - type: input
    id: url
    attributes:
      label: Website URL
      placeholder: "https://..."
    validations:
      required: false

  - type: textarea
    id: description
    attributes:
      label: Description
      description: "Brief description of the event and its relevance to collaborative research."
      placeholder: "International conference on..."
    validations:
      required: false

  - type: checkboxes
    id: domains
    attributes:
      label: Related domains
      options:
        - label: CSCW
        - label: Healthcare
        - label: Education
        - label: Urban Planning
        - label: Software Engineering
        - label: Digital Humanities
        - label: Environmental Science
        - label: Citizen Science
        - label: Open Science
        - label: Design
        - label: Innovation
        - label: Crisis Management
        - label: Governance
        - label: Manufacturing
        - label: Media & Journalism
```

**Step 2: Commit**

```bash
git add .github/ISSUE_TEMPLATE/new-event.yml
git commit -m "feat: add GitHub issue template for suggesting events"
```

---

### Task 5: Workflow — Issue to Event

**Files:**
- Create: `.github/workflows/event-from-issue.yml`
- Modify: `scripts/issue_parser.py` (add event parsing helpers)

**Step 1: Add event parsing to `issue_parser.py`**

Add a `parse_event_issue()` function and a `DOMAIN_CHECKBOX_MAP` that maps checkbox labels to domain IDs (same as DOMAIN_MAP but inverted for checkbox parsing):

```python
def parse_event_issue(body: str) -> dict[str, Any]:
    """Parse a new-event issue body into an event dict."""
    sections = parse_issue_body(body)
    title = get_text(sections, "Event name") or ""
    event_id = title_to_id(title)

    domains_checked = get_checkboxes(sections, "Related domains", DOMAIN_MAP)

    return {
        "id": event_id,
        "title": title,
        "type": get_dropdown(sections, "Event type", {
            "conference": "conference",
            "seminar": "seminar",
            "workshop": "workshop",
            "school": "school",
        }) or "conference",
        "date_start": get_text(sections, "Start date") or "",
        "date_end": get_text(sections, "End date") or "",
        "location": get_text(sections, "Location") or "",
        "url": get_text(sections, "Website URL") or "",
        "description": get_text(sections, "Description") or "",
        "domains": domains_checked,
        "status": "upcoming",
    }
```

**Step 2: Create the workflow**

```yaml
# .github/workflows/event-from-issue.yml
name: Event from Issue

on:
  issues:
    types: [labeled]

concurrency:
  group: event-issue-${{ github.event.issue.number }}
  cancel-in-progress: true

jobs:
  create-event:
    if: contains(github.event.issue.labels.*.name, 'new-event') && contains(github.event.issue.labels.*.name, 'approved')
    runs-on: ubuntu-latest
    permissions:
      contents: write
      issues: write
    steps:
      - uses: actions/checkout@v6

      - uses: actions/setup-python@v6
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install pyyaml

      - name: Add event to data file
        env:
          ISSUE_BODY: ${{ github.event.issue.body }}
          ISSUE_TITLE: ${{ github.event.issue.title }}
        run: python scripts/add_event.py

      - name: Commit and push
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ISSUE_NUMBER: ${{ github.event.issue.number }}
        run: |
          git config user.name "collabatlas-bot"
          git config user.email "bot@collabatlas.org"
          git add data/events.yaml
          git commit -m "feat: add event from issue #${ISSUE_NUMBER}"
          git push origin main

      - name: Close issue
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh issue close ${{ github.event.issue.number }} \
            --comment "Event added to CollabAtlas. Thank you!"
```

**Step 3: Create `scripts/add_event.py`**

```python
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
```

**Step 4: Commit**

```bash
git add scripts/issue_parser.py scripts/add_event.py .github/workflows/event-from-issue.yml
git commit -m "feat: add workflow to create events from GitHub issues"
```

---

### Task 6: Weekly Event Suggestion Bot

**Files:**
- Create: `scripts/weekly_suggest_events.py`
- Create: `.github/workflows/weekly-suggest-events.yml`

**Step 1: Create `scripts/weekly_suggest_events.py`**

Pattern follows `daily_suggest.py`. Loads existing events from `data/events.yaml`, asks Claude Sonnet for 2-3 upcoming events relevant to collaborative research, writes them to `data/events.yaml`.

```python
#!/usr/bin/env python3
"""Weekly event suggestion bot for CollabAtlas.

Asks Claude Sonnet to suggest upcoming conferences, seminars, workshops,
or schools relevant to collaborative research. Creates a PR with new events.

Environment variables:
    ANTHROPIC_API_KEY     Anthropic API key
    GITHUB_TOKEN          GitHub token
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
```

**Step 2: Create the workflow**

```yaml
# .github/workflows/weekly-suggest-events.yml
name: Weekly Event Suggestions

on:
  schedule:
    - cron: '0 9 * * 1'   # Every Monday at 9:00 UTC
  workflow_dispatch: {}

jobs:
  suggest-events:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v6

      - uses: actions/setup-python@v6
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install -r scripts/requirements.txt

      - name: Suggest events
        id: suggest
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: python scripts/weekly_suggest_events.py

      - name: Create PR if events added
        if: steps.suggest.outputs.events_added != '' && steps.suggest.outputs.events_added != '0'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          TITLES: ${{ steps.suggest.outputs.events_titles }}
        run: |
          BRANCH="ai-suggest/events/$(date +%Y-%m-%d)"
          git config user.name "collabatlas-bot"
          git config user.email "bot@collabatlas.org"
          git checkout -b "$BRANCH"
          git add data/events.yaml
          git commit -m "feat: add AI-suggested events

          Events: ${TITLES}"
          git push --force-with-lease origin "$BRANCH"

          gh pr create \
            --title "AI Suggestion: New events" \
            --body "## Weekly Event Suggestions

          The following events were suggested by Claude Sonnet:

          ${TITLES}

          ### Review checklist
          - [ ] Events are real and dates are correct
          - [ ] URLs are valid
          - [ ] Events are relevant to collaborative research

          *Auto-generated by the weekly event suggestion bot.*" \
            --label "ai-suggestion,review-needed" \
            --base main
```

**Step 3: Commit**

```bash
git add scripts/weekly_suggest_events.py .github/workflows/weekly-suggest-events.yml
git commit -m "feat: add weekly event suggestion bot with Claude Sonnet"
```

---

### Task 7: Auto-Archive Past Events

**Files:**
- Create: `.github/workflows/archive-past-events.yml`
- Create: `scripts/archive_past_events.py`

**Step 1: Create `scripts/archive_past_events.py`**

```python
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
```

**Step 2: Create the workflow**

```yaml
# .github/workflows/archive-past-events.yml
name: Archive Past Events

on:
  schedule:
    - cron: '0 6 * * 0'   # Every Sunday at 6:00 UTC
  workflow_dispatch: {}

jobs:
  archive:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v6

      - uses: actions/setup-python@v6
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install pyyaml

      - name: Archive past events
        run: python scripts/archive_past_events.py

      - name: Commit if changed
        run: |
          git config user.name "collabatlas-bot"
          git config user.email "bot@collabatlas.org"
          git diff --quiet data/events.yaml && exit 0
          git add data/events.yaml
          git commit -m "chore: archive past events"
          git push origin main
```

**Step 3: Commit**

```bash
git add scripts/archive_past_events.py .github/workflows/archive-past-events.yml
git commit -m "feat: add weekly auto-archiving of past events"
```

---

## Summary of Deliverables

| Task | What | Files |
|------|------|-------|
| 1 | Editorial spotlight ("A la une") | `data/featured.yaml`, `layouts/index.html`, CSS |
| 2 | Events data + homepage section | `data/events.yaml`, `layouts/index.html`, CSS |
| 3 | Dedicated `/events/` page | `content/events/_index.md`, `layouts/events/list.html`, `hugo.toml`, CSS |
| 4 | Issue template for events | `.github/ISSUE_TEMPLATE/new-event.yml` |
| 5 | Issue-to-event workflow | `.github/workflows/event-from-issue.yml`, `scripts/add_event.py`, `scripts/issue_parser.py` |
| 6 | Weekly AI event suggestions | `scripts/weekly_suggest_events.py`, `.github/workflows/weekly-suggest-events.yml` |
| 7 | Auto-archive past events | `scripts/archive_past_events.py`, `.github/workflows/archive-past-events.yml` |
