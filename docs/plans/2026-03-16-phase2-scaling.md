# Phase 2: Scaling to 500+ Entries — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make CollabAtlas performant and usable at 500+ catalogue entries by replacing custom search with Pagefind, lazy-loading heavy data payloads, and improving pagination UX.

**Architecture:** Three independent scaling tracks: (1) Replace custom O(N) client-side search with Pagefind static search — eliminates search index from HTML, provides instant search with zero client-side scoring; (2) Extract inline JSON payloads (compare-data, visualization-data) into separate Hugo output files loaded on demand via fetch(); (3) Improve pagination with page number links and increased items-per-page. Each track is independent and can be committed/reverted separately.

**Tech Stack:** Hugo, Pagefind (npm), vanilla JavaScript (fetch API), Hugo custom output formats

---

## Task 1: Integrate Pagefind static search

**Context:** Current search loads a full `/index.json` (~47KB, grows to ~630KB at 500 entries) into memory and scores every entry via O(N×M) string matching on each keystroke. Pagefind is a post-build static search library that indexes the Hugo output and provides instant search with a tiny client (~6KB) and a pre-built WASM index. It replaces `site-search.js`, `search-page.js`, and `layouts/home.json` entirely.

**Files:**
- Create: `package.json` (for Pagefind dependency)
- Modify: `layouts/_default/baseof.html` — remove custom search JS, add Pagefind CSS/JS
- Create: `assets/js/pagefind-ui-bridge.js` — bridge between Pagefind API and our search UI
- Modify: `layouts/search/list.html` — use Pagefind for full-page search
- Delete (or keep for reference): `assets/js/site-search.js`, `assets/js/search-page.js`
- Modify: `.github/workflows/deploy.yml` — add Pagefind indexing step after Hugo build
- Remove: `layouts/home.json` (search index no longer needed)

**Step 1: Install Pagefind**

```bash
npm init -y
npm install --save-dev pagefind
```

This creates `package.json` and `package-lock.json`.

**Step 2: Add Pagefind data attributes to entry pages**

Pagefind indexes HTML pages by looking for `data-pagefind-body` on content sections and `data-pagefind-meta` for structured metadata. Modify `layouts/catalogue/single.html` to add:

```html
<article data-pagefind-body>
  ...existing content...
</article>
```

And ensure the page metadata is indexed:

```html
<meta data-pagefind-meta="type:{{ .Params.type }}" />
<meta data-pagefind-meta="maturity:{{ .Params.maturity }}" />
<meta data-pagefind-filter="type:{{ .Params.type }}" />
<meta data-pagefind-filter="domain[]:{{ delimit .Params.domains "," }}" />
```

Also add `data-pagefind-body` to blog and research article pages.

**Step 3: Run Pagefind indexing after Hugo build**

```bash
hugo --minify
npx pagefind --site public --output-subdir pagefind
```

This generates `public/pagefind/` with the search index, UI assets, and WASM engine.

**Step 4: Create the Pagefind UI bridge**

Create `assets/js/pagefind-ui-bridge.js` that:
- Initializes Pagefind by importing `/pagefind/pagefind.js`
- Hooks into the existing `#site-search-input` element
- Adds debouncing (200ms)
- Renders results in `#site-search-results` (max 8 in header dropdown)
- Supports the "View all results" link to the search page

```javascript
/* CollabAtlas — Pagefind search bridge */
(function () {
  'use strict';

  var pagefind = null;
  var debounceTimer = null;
  var DEBOUNCE_MS = 200;
  var MAX_HEADER_RESULTS = 8;

  async function ensurePagefind() {
    if (pagefind) return pagefind;
    pagefind = await import('/pagefind/pagefind.js');
    await pagefind.init();
    return pagefind;
  }

  function init() {
    var searchContainer = document.getElementById('site-search');
    var input = document.getElementById('site-search-input');
    var panel = document.getElementById('site-search-panel');
    var status = document.getElementById('site-search-status');
    var resultsList = document.getElementById('site-search-results');
    var moreLink = document.getElementById('site-search-more');

    if (!input || !panel || !resultsList) return;

    var searchPage = searchContainer ? searchContainer.dataset.searchPage : '/search/';

    function showPanel() { panel.hidden = false; }
    function hidePanel() { panel.hidden = true; }

    async function performSearch(query) {
      if (query.length < 2) {
        status.textContent = 'Type at least 2 characters to search.';
        status.hidden = false;
        resultsList.innerHTML = '';
        moreLink.hidden = true;
        return;
      }

      var pf = await ensurePagefind();
      var search = await pf.search(query);
      var results = await Promise.all(
        search.results.slice(0, MAX_HEADER_RESULTS).map(function (r) { return r.data(); })
      );

      status.hidden = true;
      resultsList.innerHTML = results.map(function (r) {
        return '<li><a href="' + r.url + '">' +
          '<strong>' + r.meta.title + '</strong>' +
          '<span class="site-search-excerpt">' + (r.excerpt || '') + '</span>' +
          '</a></li>';
      }).join('');

      if (search.results.length > MAX_HEADER_RESULTS) {
        moreLink.href = searchPage + '?q=' + encodeURIComponent(query);
        moreLink.hidden = false;
      } else {
        moreLink.hidden = true;
      }

      if (!results.length) {
        status.textContent = 'No results for "' + query + '".';
        status.hidden = false;
      }
    }

    input.addEventListener('input', function () {
      clearTimeout(debounceTimer);
      var query = input.value.trim();
      debounceTimer = setTimeout(function () { performSearch(query); }, DEBOUNCE_MS);
      showPanel();
    });

    input.addEventListener('focus', function () {
      if (input.value.trim().length >= 2) showPanel();
    });

    document.addEventListener('click', function (e) {
      if (!searchContainer.contains(e.target)) hidePanel();
    });

    input.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { hidePanel(); input.blur(); }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
```

**Step 5: Create the search page Pagefind integration**

Modify `layouts/search/list.html` to use Pagefind's built-in UI or custom rendering. The simplest approach is using Pagefind's `PagefindUI` component:

```html
<link href="/pagefind/pagefind-ui.css" rel="stylesheet">
<div id="search-results"></div>
<script src="/pagefind/pagefind-ui.js"></script>
<script>
  new PagefindUI({
    element: "#search-results",
    showSubResults: true,
    showImages: false
  });
  // Sync URL query param
  var params = new URLSearchParams(window.location.search);
  var q = params.get('q');
  if (q) {
    var input = document.querySelector('.pagefind-ui__search-input');
    if (input) { input.value = q; input.dispatchEvent(new Event('input')); }
  }
</script>
```

**Step 6: Update baseof.html**

Remove:
- `<script>window.SEARCH_INDEX_URL = ...</script>`
- The `site-search.js` script tag
- The `search-page.js` script tag
- `<link rel="search" href="/index.json" ...>`

Add:
- `<link rel="stylesheet" href="/pagefind/pagefind-ui.css">` (only if using PagefindUI on search page)
- The new `pagefind-ui-bridge.js` script tag

**Step 7: Update deploy.yml**

Add Node.js setup and Pagefind indexing after Hugo build:

```yaml
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install npm dependencies
        run: npm ci

      - name: Build site
        run: hugo --minify

      - name: Index site with Pagefind
        run: npx pagefind --site public --output-subdir pagefind

      - name: Monitor build size
        run: python scripts/monitor_build_size.py
```

**Step 8: Test locally**

```bash
hugo --minify && npx pagefind --site public --output-subdir pagefind
# Serve and test
hugo server
# Or use python -m http.server in public/
```

Verify:
- Header search works with instant results
- Search page shows full results with excerpts
- Results link to correct pages
- Performance is instant even with all entries

**Step 9: Clean up old search files**

Delete or move to an archive:
- `assets/js/site-search.js`
- `assets/js/search-page.js`
- `layouts/home.json`

Update `baseof.html` to remove references.

**Step 10: Update monitor_build_size.py**

Remove the `public/index.json` threshold (no longer generated). Add Pagefind directory check:

```python
THRESHOLDS = {
    # "public/index.json": 2 * 1024 * 1024,  # Removed — Pagefind replaces this
    "public/js/site-search.js": 50 * 1024,    # Kept for now
    "public/css/main.css": 150 * 1024,
    "public/index.html": 150 * 1024,
}

SCAN_DIRS = [
    "public/js",
    "public/css",
    "public/catalogue",
    "public/pagefind",  # NEW — monitor Pagefind index size
]
```

**Step 11: Commit**

```bash
git add package.json package-lock.json assets/js/pagefind-ui-bridge.js \
  layouts/_default/baseof.html layouts/search/list.html \
  layouts/catalogue/single.html .github/workflows/deploy.yml \
  scripts/monitor_build_size.py
git rm assets/js/site-search.js assets/js/search-page.js layouts/home.json
git commit -m "feat(search): replace custom search with Pagefind static search

Pagefind provides instant search with pre-built WASM index.
Eliminates O(N) client-side scoring and large JSON index.
Adds debounced header search + full PagefindUI on search page.
Removes site-search.js, search-page.js, and home.json."
```

---

## Task 2: Lazy-load compare data

**Context:** `compare-data.html` partial embeds ALL catalogue entries as JSON in a `<script>` tag on **every page** via `baseof.html`. At 500 entries this is ~200KB of JSON on every page load. The compare feature only needs this data on catalogue pages (for the compare dock) and the compare page itself.

**Files:**
- Create: `layouts/compare/compare-data.json` — Hugo output format generating compare JSON
- Modify: `layouts/_default/baseof.html` — remove inline compare-data partial, add compare data URL
- Modify: `assets/js/entry-compare.js` — fetch JSON on demand instead of parsing inline script
- Delete: `layouts/partials/compare-data.html`
- Modify: `hugo.toml` — add JSON output for compare section

**Step 1: Create the compare JSON output**

Create `layouts/compare/list.json`:

```
{{ $entries := slice }}
{{ range where site.RegularPages "Section" "catalogue" }}
  {{ $entry := dict
    "id" (.Params.data_id | default .File.ContentBaseName)
    "title" .Title
    "url" .RelPermalink
    "tagline" .Params.tagline
    "type" (path.Base (path.Dir .File.Path))
    "maturity" .Params.maturity
    "description" .Params.description
    "domains" (.Params.domains | default slice)
    "collaborationTypes" (index .Params "collaboration-types" | default slice)
    "modalities" (.Params.modalities | default slice)
    "scales" (.Params.scales | default slice)
    "researchMethods" (.Params.research_methods | default slice)
    "whenToUse" .Params.when_to_use
    "limitations" .Params.limitations
  }}
  {{ $entries = $entries | append $entry }}
{{ end }}
{{ $entries | jsonify }}
```

**Step 2: Add JSON output to hugo.toml**

```toml
[outputs]
  home = ["HTML", "RSS"]
  section = ["HTML"]

[outputs.compare]
  # Nope — need to use custom output format approach
```

Actually, the simplest approach: create a dedicated Hugo page with JSON output. Add to `hugo.toml`:

```toml
[outputFormats.CompareJSON]
  baseName = "compare-data"
  mediaType = "application/json"
  isPlainText = true

[outputs]
  home = ["HTML", "RSS"]
```

And in `content/compare/_index.md` set `outputs: ["HTML", "CompareJSON"]`.

Alternative simpler approach: generate a static JSON file using Hugo's `resource.FromString` in a partial, or simply create a `static/api/compare-data.json` generated at build time by a script.

**Simplest approach:** Use Hugo's existing JSON output format on the compare section.

In `content/compare/_index.md` frontmatter, add:
```yaml
outputs:
  - HTML
  - JSON
```

Create `layouts/compare/list.json` with the template above. This generates `/compare/index.json`.

**Step 3: Update entry-compare.js to fetch on demand**

Replace the `parseCompareData()` function:

```javascript
var COMPARE_DATA_URL = '/compare/index.json';
var compareDataCache = null;

async function fetchCompareData() {
  if (compareDataCache) return compareDataCache;
  try {
    var resp = await fetch(COMPARE_DATA_URL);
    var data = await resp.json();
    compareDataCache = Array.isArray(data) ? data : [];
    return compareDataCache;
  } catch (err) {
    console.error('Failed to load compare data.', err);
    return [];
  }
}
```

Update `init()` to be async:

```javascript
async function init() {
  var compareEntries = await fetchCompareData();
  // ...rest of init unchanged
}
```

**Step 4: Remove inline compare-data from baseof.html**

Remove line: `{{ partial "compare-data.html" . }}`

**Step 5: Test**

- Compare dock still shows on catalogue pages
- Compare page still renders comparison table
- Verify `/compare/index.json` is generated and accessible
- Non-catalogue pages no longer include compare data payload

**Step 6: Commit**

```bash
git add layouts/compare/list.json content/compare/_index.md \
  assets/js/entry-compare.js layouts/_default/baseof.html hugo.toml
git rm layouts/partials/compare-data.html
git commit -m "perf: lazy-load compare data via external JSON endpoint

Move compare data from inline script on every page to /compare/index.json.
entry-compare.js now fetches on demand. Saves ~8KB per page (200KB at 500 entries)."
```

---

## Task 3: Lazy-load visualization data

**Context:** `visualize.html` embeds all entries + taxonomies as inline `<script>` setting `window.CATALOGUE_DATA`. At 500 entries this becomes ~50-100KB inline in the HTML. Move to external JSON fetched on page load.

**Files:**
- Create: `layouts/catalogue/visualize.json` — Hugo template generating visualization data as JSON
- Modify: `layouts/catalogue/visualize.html` — remove inline script, add fetch()
- Modify: `assets/js/catalogue-visualize.js` — accept data via fetch instead of global
- Modify: `content/catalogue/visualize/_index.md` — add JSON output

**Step 1: Create visualization JSON output**

Create `layouts/catalogue/visualize.json`:

```
{{ $domains := site.Data.taxonomies.domains | default (slice) }}
{{ $collaborationTypes := index site.Data.taxonomies "collaboration_types" | default (slice) }}
{{ $modalities := site.Data.taxonomies.modalities | default (slice) }}
{{ $scales := site.Data.taxonomies.scales | default (slice) }}
{{ $researchMethods := index site.Data.taxonomies "research_methods" | default (slice) }}
{{ $maturityLevels := index site.Data.taxonomies "maturity_levels" | default (slice) }}

{{ $entries := slice }}
{{ range where site.RegularPages "Section" "catalogue" }}
  {{ $entry := dict
    "title" .Title
    "permalink" .RelPermalink
    "domains" (.Params.domains | default (slice))
    "collaborationTypes" (index .Params "collaboration-types" | default (slice))
    "scales" (.Params.scales | default (slice))
    "modalities" (.Params.modalities | default (slice))
    "researchMethods" (.Params.research_methods | default (slice))
    "maturity" (.Params.maturity | default "")
  }}
  {{ $entries = $entries | append $entry }}
{{ end }}

{{ dict "entries" $entries "taxonomies" (dict
  "domains" $domains
  "collaborationTypes" $collaborationTypes
  "modalities" $modalities
  "scales" $scales
  "researchMethods" $researchMethods
  "maturity" $maturityLevels
) | jsonify }}
```

**Step 2: Update content/catalogue/visualize/_index.md**

Add to frontmatter:
```yaml
outputs:
  - HTML
  - JSON
```

**Step 3: Update visualize.html**

Remove the inline `<script>` that sets `window.CATALOGUE_DATA` (lines 87-101). Replace with:

```html
<script>
  window.CATALOGUE_DATA_URL = '{{ "catalogue/visualize/index.json" | relURL }}';
</script>
```

**Step 4: Update catalogue-visualize.js**

Add async data loading at the top:

```javascript
async function loadCatalogueData() {
  if (window.CATALOGUE_DATA) return window.CATALOGUE_DATA;
  var url = window.CATALOGUE_DATA_URL || '/catalogue/visualize/index.json';
  var resp = await fetch(url);
  window.CATALOGUE_DATA = await resp.json();
  return window.CATALOGUE_DATA;
}
```

Update the initialization to use it:

```javascript
async function init() {
  var data = await loadCatalogueData();
  // ...use data.entries and data.taxonomies
}
```

**Step 5: Test**

- Visualization matrix still renders
- Distribution charts work
- Modal popups show correct entries
- Page loads faster (no inline data)

**Step 6: Commit**

```bash
git add layouts/catalogue/visualize.json content/catalogue/visualize/_index.md \
  layouts/catalogue/visualize.html assets/js/catalogue-visualize.js
git commit -m "perf: lazy-load visualization data via external JSON endpoint

Move CATALOGUE_DATA from inline script to /catalogue/visualize/index.json.
catalogue-visualize.js now fetches on demand."
```

---

## Task 4: Improve pagination for large catalogues

**Context:** Current pagination shows 12 items/page with simple Prev/Next buttons. At 500 entries this means 42 pages with no way to jump to a specific page. Increase items per page, add page number links, and add a "showing X of Y" counter.

**Files:**
- Modify: `layouts/catalogue/section.html` — increase paginator count
- Modify: `layouts/partials/pagination.html` — add page number links and entry count
- Modify: `assets/css/main.css` — style new pagination elements

**Step 1: Increase items per page**

In `layouts/catalogue/section.html`, change:
```
{{ $paginator := .Paginate .RegularPages 12 }}
```
to:
```
{{ $paginator := .Paginate .RegularPages 24 }}
```

This reduces 42 pages to 21 at 500 entries — still manageable.

**Step 2: Enhance pagination partial**

Replace `layouts/partials/pagination.html` with a version that shows page numbers:

```html
{{ $paginator := .Paginator }}
{{ if gt $paginator.TotalPages 1 }}
<nav class="pagination" aria-label="Pagination">
  <p class="pagination-info">
    Showing {{ add (mul (sub $paginator.PageNumber 1) $paginator.PageSize) 1 }}–{{ if eq $paginator.PageNumber $paginator.TotalPages }}{{ $paginator.TotalNumberOfElements }}{{ else }}{{ mul $paginator.PageNumber $paginator.PageSize }}{{ end }} of {{ $paginator.TotalNumberOfElements }} entries
  </p>
  <div class="pagination-controls">
    {{ if $paginator.HasPrev }}
    <a href="{{ $paginator.Prev.URL }}" class="pagination-btn" aria-label="Previous page">&larr; Previous</a>
    {{ else }}
    <span class="pagination-btn pagination-btn--disabled" aria-disabled="true">&larr; Previous</span>
    {{ end }}

    <span class="pagination-pages">
      {{ range $paginator.Pagers }}
        {{ if eq . $paginator }}
          <span class="pagination-page pagination-page--current" aria-current="page">{{ .PageNumber }}</span>
        {{ else }}
          <a href="{{ .URL }}" class="pagination-page">{{ .PageNumber }}</a>
        {{ end }}
      {{ end }}
    </span>

    {{ if $paginator.HasNext }}
    <a href="{{ $paginator.Next.URL }}" class="pagination-btn" aria-label="Next page">Next &rarr;</a>
    {{ else }}
    <span class="pagination-btn pagination-btn--disabled" aria-disabled="true">Next &rarr;</span>
    {{ end }}
  </div>
</nav>
{{ end }}
```

**Step 3: Add CSS for page numbers**

Add to `assets/css/main.css`:

```css
.pagination-info {
  text-align: center;
  color: var(--color-muted);
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
}

.pagination-pages {
  display: flex;
  gap: 0.25rem;
  align-items: center;
}

.pagination-page {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2rem;
  height: 2rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  text-decoration: none;
  color: var(--color-text);
}

.pagination-page:hover {
  background: var(--color-surface-hover);
}

.pagination-page--current {
  background: var(--color-primary);
  color: white;
  font-weight: 600;
}
```

**Step 4: Test**

- Pagination shows page numbers
- Current page is highlighted
- "Showing X-Y of Z entries" is accurate
- Navigation works correctly at page boundaries

**Step 5: Commit**

```bash
git add layouts/catalogue/section.html layouts/partials/pagination.html assets/css/main.css
git commit -m "feat(pagination): add page numbers and entry count for large catalogues

Increase items per page from 12 to 24. Add page number links
and 'Showing X-Y of Z entries' counter to pagination."
```

---

## Task 5: Add .gitignore entries and final cleanup

**Context:** Pagefind generates files in `public/pagefind/`, npm creates `node_modules/`. These should not be committed.

**Files:**
- Modify: `.gitignore`

**Step 1: Update .gitignore**

Add:
```
node_modules/
public/
```

**Step 2: Final validation**

```bash
python scripts/validate.py --check-refs
cd scripts && python -m pytest -v
hugo --minify && npx pagefind --site public --output-subdir pagefind
python scripts/monitor_build_size.py
```

**Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore: add node_modules and public to gitignore"
```

---

## Summary

| Task | What | Impact |
|------|------|--------|
| 1 | Pagefind static search | Eliminates O(N) search, ~630KB JSON index at 500 entries → ~6KB WASM client |
| 2 | Lazy-load compare data | Removes ~200KB inline JSON from every page at 500 entries |
| 3 | Lazy-load visualization data | Removes ~50-100KB inline JSON from viz page |
| 4 | Better pagination | Usable navigation at 42+ pages |
| 5 | Gitignore + cleanup | Repo hygiene for npm/Pagefind artifacts |

**Execution order:** Tasks are independent. Recommended: 1 → 2 → 3 → 4 → 5 (search is highest impact).
