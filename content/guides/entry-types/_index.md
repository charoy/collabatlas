---
title: "Entry Types Reference"
description: "Detailed reference for each catalogue entry type, their required fields, and examples."
---

CollabAtlas organizes its catalogue into six entry types. Each type has shared fields and type-specific fields that capture what makes that category unique.

## Shared Fields

Every entry, regardless of type, includes these fields:

| Field | Required | Description |
|-------|:--------:|-------------|
| `id` | Yes | Unique identifier, matches the filename (lowercase, hyphens) |
| `type` | Yes | Entry type: `tool`, `method`, `framework`, `case-study`, `dataset`, `resource` |
| `title` | Yes | Display name |
| `tagline` | Yes | One-sentence summary |
| `description` | Yes | Paragraph-length explanation |
| `domains` | Yes | List of domains from the taxonomy |
| `collaboration_type` | Yes | List of collaboration types |
| `scale` | Yes | List of scale levels |
| `modality` | Yes | List of modalities |
| `maturity` | Yes | One of: `emerging`, `well-documented`, `established` |
| `status` | Yes | One of: `published`, `draft`, `archived` |
| `contributors` | Yes | List of contributor identifiers |
| `created` | Yes | Creation date (YYYY-MM-DD) |
| `last_reviewed` | Yes | Last review date (YYYY-MM-DD) |
| `external_links` | No | List of related links with `type`, `url`, and `title` |
| `related_entries` | No | List of IDs of related catalogue entries |
| `tags` | No | Free-form tags for search |

---

## Tools

Software, platforms, and instruments that support collaborative work.

### Type-Specific Fields

| Field | Required | Description |
|-------|:--------:|-------------|
| `website_url` | Yes | Official website URL |
| `license` | No | License type (e.g., MIT, Proprietary) |
| `open_source` | No | Boolean: is the tool open source? |
| `supported_platforms` | No | List of platforms (Web, macOS, Windows, iOS, Android) |

### Example

```yaml
id: figma
type: tool
title: Figma
tagline: Collaborative interface design tool with real-time multiplayer editing.
description: >-
  Figma is a browser-based design tool that enables teams to
  collaborate in real time on interface design, prototyping,
  and design systems.
website_url: https://figma.com
license: Proprietary
open_source: false
supported_platforms: [Web, macOS, Windows]
```

---

## Methods

Structured approaches and processes for collaborative work.

### Type-Specific Fields

| Field | Required | Description |
|-------|:--------:|-------------|
| `when_to_use` | Recommended | Guidance on when this method is appropriate |
| `limitations` | Recommended | Known constraints or challenges |
| `steps` | Recommended | Ordered list of steps in the method |
| `research_method` | No | Associated research methodologies |

### Example

```yaml
id: world-cafe
type: method
title: World Cafe
tagline: Conversational process for collaborative dialogue in large groups.
when_to_use: >-
  Use when you need to engage a large group in meaningful dialogue
  around questions that matter to them.
limitations: >-
  Requires skilled facilitation and adequate physical space.
  Less effective for highly technical or adversarial topics.
steps:
  - "Set up small tables of 4-5 people with paper tablecloths"
  - "Pose a clear, open-ended question for discussion"
  - "After 20 minutes, participants rotate to new tables"
  - "Table hosts summarize previous conversations for new arrivals"
  - "Harvest collective insights in a plenary session"
```

---

## Frameworks

Theoretical or analytical models for understanding collaboration.

### Type-Specific Fields

| Field | Required | Description |
|-------|:--------:|-------------|
| `key_concepts` | Recommended | List of core concepts in the framework |
| `seminal_works` | Recommended | List of foundational publications with `title`, `authors`, `year`, and optional `url` |
| `limitations` | No | Known critiques or limitations |

### Example

```yaml
id: communities-of-practice
type: framework
title: Communities of Practice
tagline: Theory of learning and identity formation through participation in shared practice.
key_concepts:
  - "Legitimate peripheral participation"
  - "Shared repertoire"
  - "Mutual engagement"
  - "Joint enterprise"
seminal_works:
  - title: "Communities of Practice: Learning, Meaning, and Identity"
    authors: ["Etienne Wenger"]
    year: 1998
    url: https://doi.org/10.1017/CBO9780511803932
```

---

## Case Studies

Real-world examples of collaboration in practice.

### Type-Specific Fields

| Field | Required | Description |
|-------|:--------:|-------------|
| `outcomes` | Recommended | Summary of what the collaboration achieved |
| `key_concepts` | No | Concepts illustrated by the case |
| `limitations` | No | Limitations of the case or approach |

### Example

```yaml
id: openstreetmap
type: case-study
title: OpenStreetMap
tagline: Volunteer-driven open mapping project demonstrating crowd-sourced geographic data creation.
outcomes: >-
  OpenStreetMap has produced a comprehensive, freely-available global map
  maintained by over 10 million registered contributors, used by
  humanitarian organizations, tech companies, and governments worldwide.
```

---

## Datasets

Data sources for studying or analyzing collaboration.

### Type-Specific Fields

| Field | Required | Description |
|-------|:--------:|-------------|
| `source_url` | Yes | URL to access or download the dataset |
| `format` | Yes | Data format (e.g., CSV, JSON, Parquet) |
| `size` | No | Approximate dataset size |
| `license` | Recommended | Data license (e.g., CC0, CC-BY) |
| `temporal_coverage` | No | Time period covered |
| `platform` | No | Hosting platform identifier |
| `platform_id` | No | Identifier on the hosting platform |

### Example

```yaml
id: stack-overflow-survey
type: dataset
title: Stack Overflow Developer Survey
tagline: Annual survey of developer practices, tools, and collaboration patterns.
source_url: https://insights.stackoverflow.com/survey
format: CSV
size: ~100 MB per year
license: ODbL
temporal_coverage: "2011-present"
platform: stack-overflow
```

---

## Resources

Books, handbooks, reference materials, and educational content.

### Type-Specific Fields

| Field | Required | Description |
|-------|:--------:|-------------|
| `resource_type` | Yes | One of: `book`, `report`, `handbook`, `guide`, `video`, `course` |
| `authors` | Yes | List of author names |
| `year` | Yes | Publication year |
| `doi` | No | Digital Object Identifier |
| `access` | No | One of: `open`, `paid`, `freemium` |

### Example

```yaml
id: the-open-source-way
type: resource
title: The Open Source Way
tagline: Community guidebook for open source project management and collaboration.
resource_type: guide
authors: ["Red Hat Community"]
year: 2020
access: open
```

---

## Taxonomy Values

All taxonomy values must come from the official taxonomy definitions in `data/taxonomies/`. Current taxonomies:

- **Domains**: healthcare, education, urban-planning, software-engineering, design, environmental-science, social-sciences, public-policy, business, arts-culture, disaster-response, citizen-science, manufacturing, agriculture
- **Collaboration types**: co-design, co-creation, distributed, open-source, interdisciplinary, transdisciplinary, crowdsourcing
- **Scale**: individual, small-team, organization, community, multi-org, global
- **Modality**: in-person, remote, hybrid
