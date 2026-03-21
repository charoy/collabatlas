# AI Issue Enrichment — Design Document

**Date:** 2026-03-21
**Status:** Approved

## Goal

When a contributor submits an issue (new entry or quick-add), a GitHub Actions bot powered by Claude Haiku automatically:

1. Evaluates the relevance of the submission
2. Enriches the issue by filling empty fields (taxonomies, description, related entries, tags)
3. Posts a summary comment explaining what was changed or flagged

## Architecture

### Trigger

Workflow triggers on `issues: [opened, labeled]` with labels `new-entry`, `quick-add`, or `update`. Skips issues already labeled `ai-enriched`.

### Steps

1. **Collect context** — Extract issue body + load catalogue data (entries, valid taxonomies)
2. **Call Claude Haiku** — Send issue content + catalogue context with structured prompt
3. **Evaluate relevance** — Three verdicts:
   - **Accepted** — Pertinent. Bot enriches fields and comments.
   - **Needs discussion** — Uncertain relevance or potential duplicate. Bot comments with doubts, adds `needs-review` label. No auto-edit.
   - **Rejected** — Off-topic. Bot comments politely, adds `off-topic` label, suggests closing. Never closes automatically.
4. **Update issue body** — Fill empty fields only, never overwrite contributor-provided values
5. **Post comment** — Recap of changes and suggestions
6. **Add label** — `ai-enriched` to prevent re-processing

### Prompt structure

```
Tu es un assistant éditorial pour CollabAtlas, un atlas collaboratif.
Voici une soumission de type {type}. Analyse le contenu et propose :
1. Un verdict de pertinence (accepted / needs-discussion / rejected) avec justification
2. Les taxonomies manquantes parmi les valeurs autorisées
3. Une description enrichie si celle fournie est trop courte (<30 mots)
4. Les entrées existantes qui pourraient être liées
5. Des tags pertinents

Réponds en JSON strict.
Ne propose que des valeurs provenant des listes autorisées.
N'écrase pas les champs déjà remplis par le contributeur.
```

### Context provided to LLM

- Valid taxonomy values (domains, collaboration-types, scales, modalities, maturity)
- Existing entries (id + title + tagline + domains) for related_entries suggestions
- Entry type (tool, method, framework, etc.)

### Cost estimate

~2000 tokens input + ~500 tokens output per issue → < $0.01 per enrichment with Haiku.

## Files

| File | Role |
|------|------|
| `.github/workflows/enrich-issue.yml` | GitHub Actions workflow |
| `scripts/enrich_issue.py` | Main enrichment script |

## Dependencies

- `anthropic` Python SDK
- `ANTHROPIC_API_KEY` GitHub secret
- `GITHUB_TOKEN` (native to Actions)
- Labels: `ai-enriched`, `needs-review`, `off-topic`

## What this does NOT change

- No changes to Hugo site or templates
- No new infrastructure beyond GitHub Actions
- Bot never closes issues — humans decide
