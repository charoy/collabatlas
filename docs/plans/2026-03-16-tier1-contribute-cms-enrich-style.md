# Tier 1: Contribute Flow, Decap CMS, Entry Enrichment & Homepage Refresh

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make CollabAtlas contributor-friendly with visible contribute buttons, a headless CMS for trusted editors, richer entry content, and a polished homepage.

**Architecture:** Four independent features layered on the existing Hugo static site. Contribute buttons are static links to GitHub Issue templates (pipeline already built). Sveltia CMS provides a web admin UI authenticating via GitHub OAuth — zero backend. Entry enrichment is a Python script generating markdown body content for all 119 entries. Homepage refresh is CSS + template work.

**Tech Stack:** Hugo, Sveltia CMS (Decap-compatible), Python 3.12, CSS

---

### Task 1: Create feature branch

**Files:**
- None (git operation only)

**Step 1: Create and switch to feature branch**

```bash
cd C:/Users/charo/dev/research/portfolio
git checkout -b feat/tier1-contribute-cms-style main
```

**Step 2: Verify branch**

```bash
git branch --show-current
```

Expected: `feat/tier1-contribute-cms-style`

---

### Task 2: Add "Suggest an entry" contribute links to catalogue section pages

**Files:**
- Modify: `layouts/catalogue/section.html:1-6`

**Step 1: Add contribute link to section header**

In `layouts/catalogue/section.html`, replace the header block (lines 1-6) with a version that includes a "Suggest" link pointing to the correct GitHub Issue template based on the section name:

```html
{{ define "main" }}
<section class="catalogue">
  <header class="page-header">
    <div class="page-header-row">
      <h1>{{ .Title }}</h1>
      {{ $repo := .Site.Params.github_repo }}
      {{ $typeMap := dict
        "Tools" "new-tool"
        "Methods" "new-method"
        "Frameworks" "new-framework"
        "Case Studies" "new-case-study"
        "Datasets" "new-dataset"
        "Resources" "new-resource"
      }}
      {{ $template := index $typeMap .Title }}
      {{ with $template }}
      <a href="{{ $repo }}/issues/new?template={{ . }}.yml" target="_blank" rel="noopener" class="btn btn-outline btn-sm">+ Suggest a {{ $.Title | singularize }}</a>
      {{ end }}
    </div>
    {{ with .Params.description }}<p class="page-description">{{ . }}</p>{{ end }}
  </header>
```

Note: Hugo's `singularize` function handles "Tools"→"Tool", "Methods"→"Method", etc. For "Case Studies" it produces "Case Study" which is fine.

**Step 2: Add CSS for the header row layout**

In `assets/css/main.css`, after the existing `.page-header` styles (around line 430), add:

```css
.page-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.btn-outline {
  background: transparent;
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
  padding: 0.4rem 1rem;
  border-radius: var(--radius-sm);
  font-size: 0.8rem;
  font-weight: 600;
  text-decoration: none;
  white-space: nowrap;
  transition: background 0.15s, color 0.15s;
}

.btn-outline:hover {
  background: var(--color-primary);
  color: white;
  text-decoration: none;
}

.btn-sm {
  padding: 0.35rem 0.875rem;
  font-size: 0.775rem;
}
```

**Step 3: Build and verify**

```bash
hugo --gc --minify 2>&1 | tail -5
```

Expected: Build succeeds with no errors.

**Step 4: Commit**

```bash
git add layouts/catalogue/section.html assets/css/main.css
git commit -m "feat: add 'Suggest' contribute links to catalogue section pages"
```

---

### Task 3: Add contribute CTA section to homepage

**Files:**
- Modify: `layouts/index.html` (add section between taxonomy grids and "Explore the Catalogue")
- Modify: `assets/css/main.css` (add contribute section styles)

**Step 1: Add contribute section to homepage template**

In `layouts/index.html`, insert this new section just before the "Explore the Catalogue" section (before line 250 `<section class="home-section">`... `Explore the Catalogue`):

```html
<section class="home-contribute">
  <div class="home-contribute-inner">
    <h2 class="home-contribute-title">Help grow the atlas</h2>
    <p class="home-contribute-lead">CollabAtlas is community-driven. Suggest a new entry through our guided forms — no GitHub experience needed.</p>
    <div class="contribute-grid">
      {{ $repo := .Site.Params.github_repo }}
      {{ $types := slice
        (dict "name" "Tool"         "template" "new-tool"         "icon" "wrench"    "emoji" "🔧")
        (dict "name" "Method"       "template" "new-method"       "icon" "method"    "emoji" "📐")
        (dict "name" "Framework"    "template" "new-framework"    "icon" "framework" "emoji" "🏗")
        (dict "name" "Case Study"   "template" "new-case-study"   "icon" "case"      "emoji" "📋")
        (dict "name" "Dataset"      "template" "new-dataset"      "icon" "dataset"   "emoji" "📊")
        (dict "name" "Resource"     "template" "new-resource"     "icon" "resource"  "emoji" "📚")
      }}
      {{ range $types }}
      <a href="{{ $repo }}/issues/new?template={{ .template }}.yml" target="_blank" rel="noopener" class="contribute-card">
        <span class="contribute-card-icon">{{ .emoji }}</span>
        <span class="contribute-card-name">Suggest a {{ .name }}</span>
      </a>
      {{ end }}
    </div>
    <p class="home-contribute-or">or <a href="{{ $repo }}/issues/new?template=suggest-article.yml" target="_blank" rel="noopener">suggest a research article</a> · <a href="{{ $repo }}/issues/new?template=update-entry.yml" target="_blank" rel="noopener">update an existing entry</a></p>
  </div>
</section>
```

**Step 2: Add contribute section CSS**

Append to the homepage section in `assets/css/main.css` (after the `.home-features` styles, around line 1575):

```css
/* ─── Contribute CTA (homepage) ────────────────────────────────── */

.home-contribute {
  background: linear-gradient(135deg, #eef2ff 0%, #e0f2fe 50%, #d1fae5 100%);
  border-top: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
  padding: 3rem 2rem;
  text-align: center;
}

.home-contribute-inner {
  max-width: 56rem;
  margin: 0 auto;
}

.home-contribute-title {
  font-family: var(--font-display);
  font-size: 1.75rem;
  font-weight: 400;
  margin: 0 0 0.5rem;
}

.home-contribute-lead {
  font-size: 1rem;
  color: var(--color-text-muted);
  margin: 0 0 1.75rem;
  max-width: 48ch;
  margin-left: auto;
  margin-right: auto;
  line-height: 1.6;
}

.contribute-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(9rem, 1fr));
  gap: 0.75rem;
  max-width: 42rem;
  margin: 0 auto 1.25rem;
}

.contribute-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.4rem;
  padding: 1rem 0.75rem;
  background: rgba(255,255,255,0.8);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  text-decoration: none;
  color: var(--color-text);
  font-size: 0.825rem;
  font-weight: 600;
  transition: transform 0.15s, box-shadow 0.15s, background 0.15s;
}

.contribute-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  background: white;
  text-decoration: none;
  color: var(--color-primary);
}

.contribute-card-icon {
  font-size: 1.5rem;
}

.contribute-card-name {
  text-align: center;
  line-height: 1.3;
}

.home-contribute-or {
  font-size: 0.825rem;
  color: var(--color-text-muted);
  margin: 0;
}

.home-contribute-or a {
  color: var(--color-primary);
  text-decoration: underline;
}
```

**Step 3: Build and verify**

```bash
hugo --gc --minify 2>&1 | tail -5
```

**Step 4: Commit**

```bash
git add layouts/index.html assets/css/main.css
git commit -m "feat: add contribute CTA section to homepage with entry type cards"
```

---

### Task 4: Add hero contribute button

**Files:**
- Modify: `layouts/index.html:30-34` (hero-actions div)

**Step 1: Add third hero button**

In `layouts/index.html`, modify the `.hero-actions` div to add a contribute button:

```html
    <div class="hero-actions">
      <a href="{{ $cataloguePage.RelPermalink }}" class="btn btn-primary">Browse the Catalogue</a>
      <a href="{{ $wizardPage.RelPermalink }}" class="btn btn-secondary">Find Your Method</a>
      <a href="#contribute" class="btn btn-outline">Contribute →</a>
    </div>
```

The `#contribute` anchor links to the contribute section. Add the matching `id` to the contribute section:

In the contribute section added in Task 3, change:
```html
<section class="home-contribute">
```
to:
```html
<section class="home-contribute" id="contribute">
```

**Step 2: Build and verify**

```bash
hugo --gc --minify 2>&1 | tail -5
```

**Step 3: Commit**

```bash
git add layouts/index.html
git commit -m "feat: add contribute button to homepage hero linking to contribute section"
```

---

### Task 5: Set up Sveltia CMS (Decap-compatible headless CMS)

**Files:**
- Create: `static/admin/index.html`
- Create: `static/admin/config.yml`

**Step 1: Create admin index.html**

Create `static/admin/index.html`:

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="robots" content="noindex">
  <title>CollabAtlas Admin</title>
</head>
<body>
  <script src="https://unpkg.com/@sveltia/cms/dist/sveltia-cms.js"></script>
</body>
</html>
```

**Step 2: Create admin config.yml**

Create `static/admin/config.yml`. This maps all 6 content types to form fields matching the existing frontmatter schema:

```yaml
backend:
  name: github
  repo: charoy/collabatlas
  branch: main

media_folder: static/images
public_folder: /images

slug:
  encoding: ascii
  clean_accents: true

collections:
  - name: tools
    label: Tools
    folder: content/catalogue/tools
    create: true
    slug: "{{slug}}"
    extension: md
    fields:
      - { name: title, label: Title, widget: string }
      - { name: tagline, label: Tagline, widget: string, hint: "One-sentence summary (max 200 chars)" }
      - { name: data_id, label: Data ID, widget: string, hint: "Unique kebab-case identifier" }
      - name: domains
        label: Domains
        widget: select
        multiple: true
        options:
          - { label: Healthcare, value: healthcare }
          - { label: Education, value: education }
          - { label: Urban Planning, value: urban-planning }
          - { label: Software Engineering, value: software-engineering }
          - { label: Design, value: design }
          - { label: Environmental Science, value: environmental-science }
          - { label: Social Sciences, value: social-sciences }
          - { label: Public Policy, value: public-policy }
          - { label: Business, value: business }
          - { label: "Arts & Culture", value: arts-culture }
          - { label: Disaster Response, value: disaster-response }
          - { label: Citizen Science, value: citizen-science }
          - { label: Manufacturing, value: manufacturing }
          - { label: Agriculture, value: agriculture }
          - { label: Publishing, value: publishing }
      - name: collaboration-types
        label: Collaboration Types
        widget: select
        multiple: true
        options:
          - { label: Co-Design, value: co-design }
          - { label: Co-Creation, value: co-creation }
          - { label: Co-Production, value: co-production }
          - { label: Participatory, value: participatory }
          - { label: Distributed, value: distributed }
          - { label: Crowdsourcing, value: crowdsourcing }
          - { label: Open Source, value: open-source }
          - { label: Interdisciplinary, value: interdisciplinary }
          - { label: Transdisciplinary, value: transdisciplinary }
          - { label: Community-Based, value: community-based }
      - name: scales
        label: Scales
        widget: select
        multiple: true
        options:
          - { label: Pair, value: pair }
          - { label: "Small Team", value: small-team }
          - { label: Organization, value: organization }
          - { label: "Multi-Org", value: multi-org }
          - { label: Community, value: community }
      - name: modalities
        label: Modalities
        widget: select
        multiple: true
        options:
          - { label: In-Person, value: in-person }
          - { label: Remote, value: remote }
          - { label: Hybrid, value: hybrid }
      - name: maturity
        label: Maturity
        widget: select
        options:
          - { label: Emerging, value: emerging }
          - { label: Established, value: established }
          - { label: Well-Documented, value: well-documented }
      - { name: status, label: Status, widget: select, default: published, options: [draft, published] }
      - { name: body, label: Description, widget: markdown, required: false }

  - name: methods
    label: Methods
    folder: content/catalogue/methods
    create: true
    slug: "{{slug}}"
    extension: md
    fields:
      - { name: title, label: Title, widget: string }
      - { name: tagline, label: Tagline, widget: string }
      - { name: data_id, label: Data ID, widget: string }
      - name: domains
        label: Domains
        widget: select
        multiple: true
        options:
          - { label: Healthcare, value: healthcare }
          - { label: Education, value: education }
          - { label: Urban Planning, value: urban-planning }
          - { label: Software Engineering, value: software-engineering }
          - { label: Design, value: design }
          - { label: Environmental Science, value: environmental-science }
          - { label: Social Sciences, value: social-sciences }
          - { label: Public Policy, value: public-policy }
          - { label: Business, value: business }
          - { label: "Arts & Culture", value: arts-culture }
          - { label: Disaster Response, value: disaster-response }
          - { label: Citizen Science, value: citizen-science }
          - { label: Manufacturing, value: manufacturing }
          - { label: Agriculture, value: agriculture }
          - { label: Publishing, value: publishing }
      - name: collaboration-types
        label: Collaboration Types
        widget: select
        multiple: true
        options:
          - { label: Co-Design, value: co-design }
          - { label: Co-Creation, value: co-creation }
          - { label: Co-Production, value: co-production }
          - { label: Participatory, value: participatory }
          - { label: Distributed, value: distributed }
          - { label: Crowdsourcing, value: crowdsourcing }
          - { label: Open Source, value: open-source }
          - { label: Interdisciplinary, value: interdisciplinary }
          - { label: Transdisciplinary, value: transdisciplinary }
          - { label: Community-Based, value: community-based }
      - name: scales
        label: Scales
        widget: select
        multiple: true
        options:
          - { label: Pair, value: pair }
          - { label: "Small Team", value: small-team }
          - { label: Organization, value: organization }
          - { label: "Multi-Org", value: multi-org }
          - { label: Community, value: community }
      - name: modalities
        label: Modalities
        widget: select
        multiple: true
        options:
          - { label: In-Person, value: in-person }
          - { label: Remote, value: remote }
          - { label: Hybrid, value: hybrid }
      - name: maturity
        label: Maturity
        widget: select
        options:
          - { label: Emerging, value: emerging }
          - { label: Established, value: established }
          - { label: Well-Documented, value: well-documented }
      - { name: status, label: Status, widget: select, default: published, options: [draft, published] }
      - { name: body, label: Description, widget: markdown, required: false }

  - name: frameworks
    label: Frameworks
    folder: content/catalogue/frameworks
    create: true
    slug: "{{slug}}"
    extension: md
    fields:
      - { name: title, label: Title, widget: string }
      - { name: tagline, label: Tagline, widget: string }
      - { name: data_id, label: Data ID, widget: string }
      - name: domains
        label: Domains
        widget: select
        multiple: true
        options:
          - { label: Healthcare, value: healthcare }
          - { label: Education, value: education }
          - { label: Urban Planning, value: urban-planning }
          - { label: Software Engineering, value: software-engineering }
          - { label: Design, value: design }
          - { label: Environmental Science, value: environmental-science }
          - { label: Social Sciences, value: social-sciences }
          - { label: Public Policy, value: public-policy }
          - { label: Business, value: business }
          - { label: "Arts & Culture", value: arts-culture }
          - { label: Disaster Response, value: disaster-response }
          - { label: Citizen Science, value: citizen-science }
          - { label: Manufacturing, value: manufacturing }
          - { label: Agriculture, value: agriculture }
          - { label: Publishing, value: publishing }
      - name: collaboration-types
        label: Collaboration Types
        widget: select
        multiple: true
        options:
          - { label: Co-Design, value: co-design }
          - { label: Co-Creation, value: co-creation }
          - { label: Co-Production, value: co-production }
          - { label: Participatory, value: participatory }
          - { label: Distributed, value: distributed }
          - { label: Crowdsourcing, value: crowdsourcing }
          - { label: Open Source, value: open-source }
          - { label: Interdisciplinary, value: interdisciplinary }
          - { label: Transdisciplinary, value: transdisciplinary }
          - { label: Community-Based, value: community-based }
      - name: scales
        label: Scales
        widget: select
        multiple: true
        options:
          - { label: Pair, value: pair }
          - { label: "Small Team", value: small-team }
          - { label: Organization, value: organization }
          - { label: "Multi-Org", value: multi-org }
          - { label: Community, value: community }
      - name: modalities
        label: Modalities
        widget: select
        multiple: true
        options:
          - { label: In-Person, value: in-person }
          - { label: Remote, value: remote }
          - { label: Hybrid, value: hybrid }
      - name: maturity
        label: Maturity
        widget: select
        options:
          - { label: Emerging, value: emerging }
          - { label: Established, value: established }
          - { label: Well-Documented, value: well-documented }
      - { name: status, label: Status, widget: select, default: published, options: [draft, published] }
      - { name: body, label: Description, widget: markdown, required: false }

  - name: case-studies
    label: Case Studies
    folder: content/catalogue/case-studies
    create: true
    slug: "{{slug}}"
    extension: md
    fields:
      - { name: title, label: Title, widget: string }
      - { name: tagline, label: Tagline, widget: string }
      - { name: data_id, label: Data ID, widget: string }
      - name: domains
        label: Domains
        widget: select
        multiple: true
        options:
          - { label: Healthcare, value: healthcare }
          - { label: Education, value: education }
          - { label: Urban Planning, value: urban-planning }
          - { label: Software Engineering, value: software-engineering }
          - { label: Design, value: design }
          - { label: Environmental Science, value: environmental-science }
          - { label: Social Sciences, value: social-sciences }
          - { label: Public Policy, value: public-policy }
          - { label: Business, value: business }
          - { label: "Arts & Culture", value: arts-culture }
          - { label: Disaster Response, value: disaster-response }
          - { label: Citizen Science, value: citizen-science }
          - { label: Manufacturing, value: manufacturing }
          - { label: Agriculture, value: agriculture }
          - { label: Publishing, value: publishing }
      - name: collaboration-types
        label: Collaboration Types
        widget: select
        multiple: true
        options:
          - { label: Co-Design, value: co-design }
          - { label: Co-Creation, value: co-creation }
          - { label: Co-Production, value: co-production }
          - { label: Participatory, value: participatory }
          - { label: Distributed, value: distributed }
          - { label: Crowdsourcing, value: crowdsourcing }
          - { label: Open Source, value: open-source }
          - { label: Interdisciplinary, value: interdisciplinary }
          - { label: Transdisciplinary, value: transdisciplinary }
          - { label: Community-Based, value: community-based }
      - name: scales
        label: Scales
        widget: select
        multiple: true
        options:
          - { label: Pair, value: pair }
          - { label: "Small Team", value: small-team }
          - { label: Organization, value: organization }
          - { label: "Multi-Org", value: multi-org }
          - { label: Community, value: community }
      - name: modalities
        label: Modalities
        widget: select
        multiple: true
        options:
          - { label: In-Person, value: in-person }
          - { label: Remote, value: remote }
          - { label: Hybrid, value: hybrid }
      - name: maturity
        label: Maturity
        widget: select
        options:
          - { label: Emerging, value: emerging }
          - { label: Established, value: established }
          - { label: Well-Documented, value: well-documented }
      - { name: status, label: Status, widget: select, default: published, options: [draft, published] }
      - { name: body, label: Description, widget: markdown, required: false }

  - name: datasets
    label: Datasets
    folder: content/catalogue/datasets
    create: true
    slug: "{{slug}}"
    extension: md
    fields:
      - { name: title, label: Title, widget: string }
      - { name: tagline, label: Tagline, widget: string }
      - { name: data_id, label: Data ID, widget: string }
      - name: domains
        label: Domains
        widget: select
        multiple: true
        options:
          - { label: Healthcare, value: healthcare }
          - { label: Education, value: education }
          - { label: Urban Planning, value: urban-planning }
          - { label: Software Engineering, value: software-engineering }
          - { label: Design, value: design }
          - { label: Environmental Science, value: environmental-science }
          - { label: Social Sciences, value: social-sciences }
          - { label: Public Policy, value: public-policy }
          - { label: Business, value: business }
          - { label: "Arts & Culture", value: arts-culture }
          - { label: Disaster Response, value: disaster-response }
          - { label: Citizen Science, value: citizen-science }
          - { label: Manufacturing, value: manufacturing }
          - { label: Agriculture, value: agriculture }
          - { label: Publishing, value: publishing }
      - name: collaboration-types
        label: Collaboration Types
        widget: select
        multiple: true
        options:
          - { label: Co-Design, value: co-design }
          - { label: Co-Creation, value: co-creation }
          - { label: Co-Production, value: co-production }
          - { label: Participatory, value: participatory }
          - { label: Distributed, value: distributed }
          - { label: Crowdsourcing, value: crowdsourcing }
          - { label: Open Source, value: open-source }
          - { label: Interdisciplinary, value: interdisciplinary }
          - { label: Transdisciplinary, value: transdisciplinary }
          - { label: Community-Based, value: community-based }
      - name: scales
        label: Scales
        widget: select
        multiple: true
        options:
          - { label: Pair, value: pair }
          - { label: "Small Team", value: small-team }
          - { label: Organization, value: organization }
          - { label: "Multi-Org", value: multi-org }
          - { label: Community, value: community }
      - name: modalities
        label: Modalities
        widget: select
        multiple: true
        options:
          - { label: In-Person, value: in-person }
          - { label: Remote, value: remote }
          - { label: Hybrid, value: hybrid }
      - name: maturity
        label: Maturity
        widget: select
        options:
          - { label: Emerging, value: emerging }
          - { label: Established, value: established }
          - { label: Well-Documented, value: well-documented }
      - name: platform
        label: Hosting Platform
        widget: select
        required: false
        options:
          - { label: Zenodo, value: zenodo }
          - { label: Kaggle, value: kaggle }
          - { label: Figshare, value: figshare }
          - { label: Dataverse, value: dataverse }
          - { label: Dryad, value: dryad }
          - { label: OSF, value: osf }
          - { label: HuggingFace, value: huggingface }
          - { label: "Google BigQuery", value: google-bigquery }
          - { label: "ACM DL", value: acm-dl }
          - { label: Other, value: other }
      - { name: status, label: Status, widget: select, default: published, options: [draft, published] }
      - { name: body, label: Description, widget: markdown, required: false }

  - name: resources
    label: Resources
    folder: content/catalogue/resources
    create: true
    slug: "{{slug}}"
    extension: md
    fields:
      - { name: title, label: Title, widget: string }
      - { name: tagline, label: Tagline, widget: string }
      - { name: data_id, label: Data ID, widget: string }
      - name: domains
        label: Domains
        widget: select
        multiple: true
        options:
          - { label: Healthcare, value: healthcare }
          - { label: Education, value: education }
          - { label: Urban Planning, value: urban-planning }
          - { label: Software Engineering, value: software-engineering }
          - { label: Design, value: design }
          - { label: Environmental Science, value: environmental-science }
          - { label: Social Sciences, value: social-sciences }
          - { label: Public Policy, value: public-policy }
          - { label: Business, value: business }
          - { label: "Arts & Culture", value: arts-culture }
          - { label: Disaster Response, value: disaster-response }
          - { label: Citizen Science, value: citizen-science }
          - { label: Manufacturing, value: manufacturing }
          - { label: Agriculture, value: agriculture }
          - { label: Publishing, value: publishing }
      - name: collaboration-types
        label: Collaboration Types
        widget: select
        multiple: true
        options:
          - { label: Co-Design, value: co-design }
          - { label: Co-Creation, value: co-creation }
          - { label: Co-Production, value: co-production }
          - { label: Participatory, value: participatory }
          - { label: Distributed, value: distributed }
          - { label: Crowdsourcing, value: crowdsourcing }
          - { label: Open Source, value: open-source }
          - { label: Interdisciplinary, value: interdisciplinary }
          - { label: Transdisciplinary, value: transdisciplinary }
          - { label: Community-Based, value: community-based }
      - name: scales
        label: Scales
        widget: select
        multiple: true
        options:
          - { label: Pair, value: pair }
          - { label: "Small Team", value: small-team }
          - { label: Organization, value: organization }
          - { label: "Multi-Org", value: multi-org }
          - { label: Community, value: community }
      - name: modalities
        label: Modalities
        widget: select
        multiple: true
        options:
          - { label: In-Person, value: in-person }
          - { label: Remote, value: remote }
          - { label: Hybrid, value: hybrid }
      - name: maturity
        label: Maturity
        widget: select
        options:
          - { label: Emerging, value: emerging }
          - { label: Established, value: established }
          - { label: Well-Documented, value: well-documented }
      - { name: status, label: Status, widget: select, default: published, options: [draft, published] }
      - { name: body, label: Description, widget: markdown, required: false }
```

**Step 3: Build and verify admin page is served**

```bash
hugo --gc --minify 2>&1 | tail -5
ls public/admin/
```

Expected: `index.html` and `config.yml` in `public/admin/`.

**Step 4: Commit**

```bash
git add static/admin/index.html static/admin/config.yml
git commit -m "feat: add Sveltia CMS admin panel for trusted editors"
```

---

### Task 6: Enrich catalogue entries with body content

**Files:**
- Create: `scripts/enrich_entries.py`

**Step 1: Create the enrichment script**

Create `scripts/enrich_entries.py` — a Python script that reads each `.md` file in `content/catalogue/`, checks if it has body content below the frontmatter, and if not, generates meaningful markdown body based on the entry's title, tagline, type, and taxonomy values.

The script should:
1. Walk all `.md` files in `content/catalogue/` subdirectories
2. Parse YAML frontmatter (between `---` delimiters)
3. Skip files that already have body content (non-whitespace after closing `---`)
4. Generate 2-4 paragraphs of descriptive content based on:
   - Entry type (tool, method, framework, case-study, dataset, resource)
   - Title and tagline
   - Domain, collaboration-type, scale, modality values
5. Write back the file with frontmatter + generated body
6. Report: `Enriched: {path}` or `Skipped (has content): {path}`

Template patterns per type:
- **Tools**: What it does, key features for collaboration, who uses it, how it fits in the landscape
- **Methods**: How the method works, when to apply it, typical steps, what distinguishes it
- **Frameworks**: Core concepts, theoretical foundations, how practitioners use it
- **Case Studies**: Context, what was done, outcomes, lessons learned
- **Datasets**: What data is included, collection methodology, research applications
- **Resources**: What it covers, target audience, how to use it

**Step 2: Run the script**

```bash
cd C:/Users/charo/dev/research/portfolio
python scripts/enrich_entries.py
```

Expected: ~100+ entries enriched, ~10-15 skipped (ones that already have content).

**Step 3: Build and verify**

```bash
hugo --gc --minify 2>&1 | tail -5
```

Expected: Build succeeds, entry count unchanged.

**Step 4: Commit**

```bash
git add scripts/enrich_entries.py content/catalogue/
git commit -m "feat: enrich 100+ catalogue entries with descriptive body content"
```

---

### Task 7: Homepage style refresh — hero and stats

**Files:**
- Modify: `assets/css/main.css:690-835` (hero + stats styles)
- Modify: `layouts/index.html:24-44` (hero + stats HTML)

**Step 1: Update hero styles**

Replace the `.home-hero` CSS block (lines 690-770) with an updated version featuring:
- Animated mesh gradient background
- Larger, more prominent metric counter
- Search input integrated in hero
- More padding and breathing room

Key CSS changes:
```css
.home-hero {
  background:
    radial-gradient(ellipse at 20% 80%, rgba(8,145,178,0.06) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 20%, rgba(79,70,229,0.08) 0%, transparent 50%),
    radial-gradient(ellipse at 50% 50%, rgba(5,150,105,0.04) 0%, transparent 60%),
    linear-gradient(135deg, #f8faff 0%, #eef2ff 40%, #e0f2fe 70%, #f0fdf4 100%);
  border-bottom: 1px solid var(--color-border);
  padding: 4.5rem 2rem 3.5rem;
}
```

Update the metric to be a pill-shaped badge:
```css
.home-hero-metric {
  display: inline-block;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-primary);
  background: rgba(79,70,229,0.08);
  border: 1px solid rgba(79,70,229,0.15);
  border-radius: 9999px;
  padding: 0.35rem 1.25rem;
  margin: 0 auto 2rem;
  letter-spacing: 0.02em;
}
```

**Step 2: Update stats bar**

Update `.home-stats` to have more padding and subtle stat icons:
```css
.home-stats {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 0;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg);
}

.home-stats .stat {
  text-align: center;
  padding: 1.5rem 1rem;
  border-right: 1px solid var(--color-border);
  transition: background 0.15s;
}

.home-stats .stat:hover {
  background: var(--color-bg-alt);
}

.home-stats .stat-number {
  font-family: var(--font-display);
  font-size: 2.25rem;
  color: var(--color-text);
  display: block;
  line-height: 1;
  margin-bottom: 0.35rem;
}

.home-stats .stat-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted);
}
```

**Step 3: Build and verify**

```bash
hugo --gc --minify 2>&1 | tail -5
```

**Step 4: Commit**

```bash
git add assets/css/main.css layouts/index.html
git commit -m "style: refresh homepage hero and stats bar with more polish"
```

---

### Task 8: Homepage style refresh — sections, tiles, and features

**Files:**
- Modify: `assets/css/main.css` (section dividers, domain tiles, catalogue tiles, feature cards)

**Step 1: Update section dividers**

Replace hard `border-bottom` dividers between `.home-section` with gradient fades:
```css
.home-section {
  padding: 3.5rem 2rem;
  max-width: var(--max-width);
  margin: 0 auto;
  position: relative;
}

.home-section + .home-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 10%;
  right: 10%;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--color-border) 30%, var(--color-border) 70%, transparent);
}
```

**Step 2: Update domain tiles**

Add gradient hover effect and softer shadows:
```css
.domain-tile {
  padding: 1.25rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-bg);
  text-decoration: none;
  color: var(--color-text);
  transition: all 0.2s ease;
  box-shadow: var(--shadow-sm);
}

.domain-tile:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
  border-color: var(--color-primary);
  text-decoration: none;
}
```

**Step 3: Update catalogue tiles**

Make them larger with a subtle gradient accent at left:
```css
.catalogue-tile {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1.5rem;
  border: 1px solid var(--color-border);
  border-left: 4px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-bg);
  box-shadow: var(--shadow-sm);
  text-decoration: none;
  color: var(--color-text);
  transition: all 0.2s ease;
}

.catalogue-tile:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-3px);
  text-decoration: none;
  color: var(--color-text);
}

.catalogue-tile-icon {
  font-size: 1.75rem;
  line-height: 1;
  flex-shrink: 0;
  margin-top: 0.1rem;
}
```

**Step 4: Update feature cards**

Add gradient background, larger icons, more spacing:
```css
.home-features {
  background: var(--color-bg-alt);
  border-radius: var(--radius);
  padding: 3rem 2rem;
}

.feature-card {
  padding: 2rem 1.5rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-bg);
  box-shadow: var(--shadow-sm);
  transition: all 0.2s ease;
}

.feature-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.feature-icon {
  font-size: 2rem;
  margin-bottom: 0.75rem;
  display: block;
}
```

**Step 5: Build and verify**

```bash
hugo --gc --minify 2>&1 | tail -5
```

**Step 6: Commit**

```bash
git add assets/css/main.css
git commit -m "style: polish homepage sections, tiles, and feature cards"
```

---

### Task 9: Mobile responsive fixes for new styles

**Files:**
- Modify: `assets/css/main.css` (mobile media query section around line 2570+)

**Step 1: Add mobile overrides for new components**

Add to the existing `@media (max-width: 48rem)` block:

```css
  .home-stats {
    grid-template-columns: repeat(3, 1fr);
  }

  .home-stats .stat:nth-child(3) {
    border-right: none;
  }

  .contribute-grid {
    grid-template-columns: repeat(3, 1fr);
  }

  .page-header-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .home-contribute { padding: 2rem 1.25rem; }
  .home-contribute-title { font-size: 1.5rem; }
```

**Step 2: Build and verify**

```bash
hugo --gc --minify 2>&1 | tail -5
```

**Step 3: Commit**

```bash
git add assets/css/main.css
git commit -m "style: add mobile responsive fixes for new homepage components"
```

---

### Task 10: Build verification and final commit

**Step 1: Full build**

```bash
cd C:/Users/charo/dev/research/portfolio
hugo --gc --minify
```

Expected: Clean build, no errors.

**Step 2: Run Hugo server for manual check**

```bash
hugo server --navigateToChanged
```

Verify:
- Homepage hero shows 3 buttons (Browse, Find Your Method, Contribute)
- Stats bar shows 6 categories with counts
- Contribute section shows 6 entry type cards
- Catalogue section pages show "Suggest a [type]" button
- `/admin/` loads Sveltia CMS login page
- Entry pages show body content
- Mobile layout looks correct

**Step 3: Stop server and verify git log**

```bash
git log --oneline feat/tier1-contribute-cms-style --not main
```

Expected: ~8-9 commits covering all features.
