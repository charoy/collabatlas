# RSS Feeds Design

**Date:** 2026-04-03  
**Status:** Validated

## Overview

Add RSS feed support to CollabAtlas with three main section feeds and filtered feeds per taxonomy term (catalogue entries only).

## Feeds

### Section feeds

| Feed | URL |
|------|-----|
| Catalogue (all new entries) | `/catalogue/index.xml` |
| Blog | `/blog/index.xml` |
| Living Research | `/research-cases/index.xml` |

### Taxonomy-filtered feeds (catalogue entries only)

One feed per taxonomy term, restricted to catalogue entries:

| Example | URL |
|---------|-----|
| Healthcare domain | `/domains/healthcare/index.xml` |
| Open Source collaboration type | `/collaboration-types/open-source/index.xml` |
| Community scale | `/scales/community/index.xml` |

All taxonomy dimensions are covered: domains, collaboration-types, scales, modalities, research-methods, maturity-levels.

## Implementation

### 1. `hugo.toml` — output formats

Add `"RSS"` to section, taxonomy, and term outputs:

```toml
[outputs]
  home = ["HTML", "RSS"]
  section = ["HTML", "RSS"]
  taxonomy = ["HTML", "RSS"]
  term = ["HTML", "RSS"]
```

This enables RSS generation for all sections and all taxonomy term pages. No further config required for the three main section feeds.

### 2. Custom RSS template for taxonomy terms

Create `layouts/_default/term.rss.xml` to override the default taxonomy term RSS template. It filters pages to catalogue entries only using a `where` clause:

```go-html-template
{{- $pages := where .Pages "Section" "catalogue" -}}
{{- $limit := .Site.Config.Services.RSS.Limit -}}
{{- if ge $limit 1 -}}
  {{- $pages = $pages | first $limit -}}
{{- end -}}
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{{ .Title }} — CollabAtlas</title>
    <link>{{ .Permalink }}</link>
    <description>New catalogue entries tagged {{ .Title }}</description>
    <atom:link href="{{ .Permalink }}index.xml" rel="self" type="application/rss+xml" />
    <language>en-us</language>
    {{- range $pages }}
    <item>
      <title>{{ .Title }}</title>
      <link>{{ .Permalink }}</link>
      <pubDate>{{ .Date.Format "Mon, 02 Jan 2006 15:04:05 -0700" }}</pubDate>
      <guid>{{ .Permalink }}</guid>
      <description>{{ .Params.tagline | html }}</description>
    </item>
    {{- end }}
  </channel>
</rss>
```

### 3. RSS autodiscovery links

Add `<link rel="alternate">` tags in `layouts/partials/head.html` (or equivalent) so RSS readers detect feeds automatically:

```html
<!-- Section feeds -->
<link rel="alternate" type="application/rss+xml" title="CollabAtlas — Catalogue" href="{{ "/catalogue/index.xml" | absURL }}" />
<link rel="alternate" type="application/rss+xml" title="CollabAtlas — Blog" href="{{ "/blog/index.xml" | absURL }}" />
<link rel="alternate" type="application/rss+xml" title="CollabAtlas — Living Research" href="{{ "/research-cases/index.xml" | absURL }}" />

<!-- Current page feed (taxonomy term pages) -->
{{ if .IsTermPage }}
<link rel="alternate" type="application/rss+xml" title="CollabAtlas — {{ .Title }}" href="{{ .Permalink }}index.xml" />
{{ end }}
```

### 4. RSS link on taxonomy term pages

On each taxonomy term page (e.g. the "Healthcare" domain page), add a visible RSS icon linking to the filtered feed. This goes in the taxonomy term list template (`layouts/_default/terms.html` or equivalent):

```html
<a href="{{ .Permalink }}index.xml" title="Subscribe to RSS feed">
  <svg><!-- RSS icon --></svg>
</a>
```

## Out of scope

- Combined/multi-filter feeds (e.g. "methods × healthcare") — deferred
- Atom format — RSS 2.0 is sufficient
- Per-entry-type feeds within catalogue (tools only, methods only) — deferred

## Files to create/modify

| File | Action |
|------|--------|
| `hugo.toml` | Add RSS to `[outputs]` |
| `layouts/_default/term.rss.xml` | Create — custom taxonomy term RSS template |
| `layouts/partials/head.html` | Add autodiscovery `<link>` tags |
| Taxonomy term list template | Add visible RSS icon/link |
