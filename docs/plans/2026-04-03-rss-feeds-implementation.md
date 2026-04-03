# RSS Feeds Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add RSS feeds for the blog, living research, and catalogue sections, plus filtered feeds per taxonomy term (catalogue entries only).

**Architecture:** Enable Hugo's native RSS output for sections and taxonomy terms via `hugo.toml`. Override the taxonomy term RSS template to filter to catalogue entries only. Add autodiscovery `<link>` tags to `baseof.html` and visible RSS icons on taxonomy term pages.

**Tech Stack:** Hugo 0.155.3 (extended), Go templates, RSS 2.0

---

### Task 1: Enable RSS output for sections and taxonomy terms

**Files:**
- Modify: `hugo.toml:74-76`

**Step 1: Add RSS to outputs**

Replace the existing `[outputs]` block:

```toml
[outputs]
  home = ["HTML", "RSS"]
  section = ["HTML", "RSS"]
  taxonomy = ["HTML", "RSS"]
  term = ["HTML", "RSS"]
```

**Step 2: Build the site and verify feeds are generated**

```bash
hugo --buildDrafts 2>&1 | grep -i rss
```

Expected: no errors. Then check:

```bash
ls public/blog/index.xml public/research-cases/index.xml public/catalogue/index.xml
```

Expected: all three files exist.

**Step 3: Spot-check a taxonomy term feed**

```bash
ls public/domains/healthcare/index.xml
```

Expected: file exists. Open it and verify it contains entries from all sections (blog + catalogue mixed) — this is expected at this stage, Task 2 will fix it.

**Step 4: Commit**

```bash
git add hugo.toml
git commit -m "feat(rss): enable RSS output for sections and taxonomy terms"
```

---

### Task 2: Custom RSS template for taxonomy terms (catalogue only)

**Files:**
- Create: `layouts/_default/term.rss.xml`

**Context:** Hugo uses `layouts/_default/rss.xml` as the default RSS template. To override it for taxonomy term pages only, create `layouts/_default/term.rss.xml`. This applies to all term pages (e.g. `/domains/healthcare/`, `/scales/community/`). The `where .Pages "Section" "catalogue"` filter restricts items to catalogue entries.

**Step 1: Create the template**

```xml
{{- $pages := where .Pages "Section" "catalogue" -}}
{{- $limit := .Site.Config.Services.RSS.Limit -}}
{{- if ge $limit 1 -}}
  {{- $pages = $pages | first $limit -}}
{{- end -}}
<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{{ .Title }} — {{ .Site.Title }}</title>
    <link>{{ .Permalink }}</link>
    <description>New catalogue entries tagged &#34;{{ .Title }}&#34;</description>
    <generator>Hugo</generator>
    <language>{{ site.Language.LanguageCode }}</language>
    <atom:link href="{{ .Permalink }}index.xml" rel="self" type="application/rss+xml" />
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

**Step 2: Rebuild and verify the healthcare feed contains only catalogue entries**

```bash
hugo --buildDrafts && cat public/domains/healthcare/index.xml
```

Expected: `<item>` elements only link to `/catalogue/` URLs, not `/blog/`.

**Step 3: Verify the blog feed is unaffected**

```bash
cat public/blog/index.xml | grep "<link>"
```

Expected: links point to `/blog/` entries only (blog uses the default RSS template, not this one).

**Step 4: Commit**

```bash
git add layouts/_default/term.rss.xml
git commit -m "feat(rss): add custom taxonomy term RSS template filtered to catalogue entries"
```

---

### Task 3: RSS autodiscovery in `<head>`

**Files:**
- Modify: `layouts/_default/baseof.html:21` (after the CSS `<link>` tag)

**Context:** RSS autodiscovery uses `<link rel="alternate">` tags in the `<head>`. Browsers and feed readers use these to detect available feeds. We add permanent links for the three main feeds, and a dynamic link for taxonomy term pages.

**Step 1: Add autodiscovery links inside `<head>`, after the CSS link (line 21)**

```html
  {{/* RSS autodiscovery */}}
  <link rel="alternate" type="application/rss+xml" title="{{ .Site.Title }} — Catalogue" href="{{ "/catalogue/index.xml" | absURL }}" />
  <link rel="alternate" type="application/rss+xml" title="{{ .Site.Title }} — Blog" href="{{ "/blog/index.xml" | absURL }}" />
  <link rel="alternate" type="application/rss+xml" title="{{ .Site.Title }} — Living Research" href="{{ "/research-cases/index.xml" | absURL }}" />
  {{- if .IsTermPage }}
  <link rel="alternate" type="application/rss+xml" title="{{ .Site.Title }} — {{ .Title }}" href="{{ .Permalink }}index.xml" />
  {{- end }}
```

**Step 2: Rebuild and check the HTML source of the homepage**

```bash
hugo --buildDrafts && grep -A1 'rel="alternate"' public/index.html
```

Expected: three `<link rel="alternate">` tags for catalogue, blog, and living research.

**Step 3: Check a taxonomy term page**

```bash
grep 'rel="alternate"' public/domains/healthcare/index.html
```

Expected: four tags — the three permanent ones plus the dynamic healthcare one.

**Step 4: Commit**

```bash
git add layouts/_default/baseof.html
git commit -m "feat(rss): add RSS autodiscovery links to <head>"
```

---

### Task 4: Visible RSS links on taxonomy term pages

**Files:**
- Create: `layouts/_default/terms.html` (if it doesn't exist — check first with `ls layouts/_default/`)

**Context:** Hugo renders taxonomy term list pages (e.g. `/domains/healthcare/`) using `layouts/_default/terms.html` or the theme default. We need to add a visible RSS icon/link on these pages so users can discover and copy the feed URL. Check if a custom `terms.html` already exists before creating one.

**Step 1: Check existing term list template**

```bash
ls layouts/_default/terms.html layouts/taxonomy/ 2>/dev/null || echo "no custom term list template"
```

**Step 2a: If no template exists — create `layouts/_default/terms.html`**

```html
{{ define "main" }}
<section class="taxonomy-term">
  <header class="page-header">
    <h1>{{ .Title }}</h1>
    <a class="rss-link" href="{{ .Permalink }}index.xml" title="Subscribe to RSS feed for {{ .Title }} catalogue entries" aria-label="RSS feed">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
        <path d="M6.18 15.64a2.18 2.18 0 0 1 2.18 2.18C8.36 19.01 7.38 20 6.18 20C4.98 20 4 19.01 4 17.82a2.18 2.18 0 0 1 2.18-2.18M4 4.44A15.56 15.56 0 0 1 19.56 20h-2.83A12.73 12.73 0 0 0 4 7.27V4.44m0 5.66a9.9 9.9 0 0 1 9.9 9.9h-2.83A7.07 7.07 0 0 0 4 12.93V10.1z"/>
      </svg>
      RSS
    </a>
  </header>
  {{ .Content }}
  <ul class="entry-list">
    {{ range .Pages }}
    <li><a href="{{ .RelPermalink }}">{{ .Title }}</a></li>
    {{ end }}
  </ul>
</section>
{{ end }}
```

**Step 2b: If a template already exists** — add only the RSS link anchor after the `<h1>` tag, following the same pattern as above.

**Step 3: Add minimal CSS for the RSS link in `assets/css/main.css`**

Find an appropriate place (e.g. near other `.page-header` rules) and add:

```css
.rss-link {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.8rem;
  color: #f26522;
  text-decoration: none;
  margin-top: 0.25rem;
}
.rss-link:hover {
  text-decoration: underline;
}
```

**Step 4: Rebuild and visually verify**

```bash
hugo --buildDrafts && open public/domains/healthcare/index.html
```

Expected: page shows an orange RSS icon/link below the title.

**Step 5: Commit**

```bash
git add layouts/_default/terms.html assets/css/main.css
git commit -m "feat(rss): add visible RSS subscription link on taxonomy term pages"
```
