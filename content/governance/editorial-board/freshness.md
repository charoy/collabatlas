---
title: "Content Freshness Dashboard"
description: "Overview of content review status across the catalogue."
---

This dashboard lists all entries and their review status based on the `last_reviewed` field.

{{< freshness-table >}}

### Status Types

- **Fresh:** Reviewed within the last 6 months (180 days).
- **Current:** Reviewed within the last 12 months (365 days).
- **Stale:** Not reviewed in over 12 months.
- **Missing:** `last_reviewed` field is missing.
