---
title: "Review Process"
description: "How contributions to CollabAtlas are reviewed and published."
---

All contributions to CollabAtlas go through a structured review process to ensure quality, accuracy, and consistency with platform standards.

## Contribution Workflow

### 1. Fork and Prepare

Fork the [CollabAtlas repository](https://github.com/collabatlas/collabatlas) and create a new branch for your contribution. Follow the entry templates in `archetypes/` and the schema definitions in `schemas/` for the relevant entry type.

### 2. Automated Checks

When you open a pull request, automated checks run immediately:

- **Schema validation** — your YAML entry is validated against the JSON schema for its type
- **Taxonomy verification** — all taxonomy values are checked against the official taxonomy definitions
- **Link checking** — external URLs are verified to be reachable
- **Freshness metadata** — `created` and `last_reviewed` dates are checked for valid format

Pull requests that fail automated checks will not be reviewed until the issues are resolved.

### 3. Editorial Review

Once automated checks pass, the pull request is assigned to the relevant domain editor. The editor will:

- Verify factual accuracy of the entry
- Check that the description is clear, neutral, and appropriately detailed
- Confirm that taxonomy tags are appropriate and consistent
- Suggest improvements or request changes if needed

The target review turnaround is **10 business days**.

### 4. Merge and Publication

After editorial approval, a core maintainer merges the pull request. The entry is published on the next site build, which runs automatically on every merge to `main`.

## Updating Existing Entries

To update an existing entry, follow the same process. In your pull request description, explain what has changed and why the update is needed. If you are flagging an entry as outdated, you can open an issue instead of a pull request.

## Archiving Entries

Entries that are no longer relevant, accurate, or maintained may be archived. Archived entries remain visible in the catalogue with an "archived" status badge but are excluded from recommendation features. Archiving decisions are made by domain editors in consultation with core maintainers.

## Freshness Policy

Entries not reviewed in 12 or more months are automatically flagged in the monthly freshness report. Domain editors are notified and asked to either review and update the entry or mark it for archiving.
