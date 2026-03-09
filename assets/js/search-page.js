/* CollabAtlas — Dedicated search results page */

(function () {
  'use strict';

  function parseIndex() {
    var element = document.getElementById('site-search-index');
    if (!element) {
      return [];
    }

    try {
      var payload = JSON.parse(element.textContent);
      if (typeof payload === 'string') {
        payload = JSON.parse(payload);
      }

      return payload.map(function (item) {
        return {
          title: item.title || '',
          url: item.url || '#',
          type: item.type || 'page',
          summary: item.summary || '',
          text: (item.text || '').toLowerCase(),
          external: Boolean(item.external)
        };
      });
    } catch (error) {
      console.error('Unable to parse site search index.', error);
      return [];
    }
  }

  function escapeHtml(value) {
    return String(value || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function formatTypeLabel(type) {
    return String(type || 'page')
      .replace(/-/g, ' ')
      .replace(/\b\w/g, function (letter) { return letter.toUpperCase(); });
  }

  function scoreItem(item, query, terms) {
    var title = item.title.toLowerCase();
    var summary = item.summary.toLowerCase();
    var text = item.text;
    var score = 0;

    if (title === query) {
      score += 120;
    } else if (title.indexOf(query) === 0) {
      score += 80;
    } else if (title.indexOf(query) !== -1) {
      score += 45;
    }

    if (summary.indexOf(query) !== -1) {
      score += 20;
    }

    terms.forEach(function (term) {
      if (title.indexOf(term) !== -1) {
        score += 14;
      }
      if (summary.indexOf(term) !== -1) {
        score += 8;
      }
      if (text.indexOf(term) !== -1) {
        score += 5;
      }
    });

    return score;
  }

  function updateUrl(query) {
    var url = new URL(window.location.href);
    if (query) {
      url.searchParams.set('q', query);
    } else {
      url.searchParams.delete('q');
    }
    window.history.replaceState({}, '', url.toString());
  }

  function renderResults(container, matches) {
    container.innerHTML = matches.map(function (item) {
      var target = item.external ? ' target="_blank" rel="noopener"' : '';
      return '<article class="search-result-card">' +
        '<div class="search-result-header">' +
          '<span class="badge site-search-badge">' + escapeHtml(formatTypeLabel(item.type)) + '</span>' +
          '<h2 class="search-result-title"><a href="' + escapeHtml(item.url) + '"' + target + '>' + escapeHtml(item.title) + '</a></h2>' +
        '</div>' +
        (item.summary ? '<p class="search-result-summary">' + escapeHtml(item.summary) + '</p>' : '') +
        '<a class="search-result-link" href="' + escapeHtml(item.url) + '"' + target + '>' + escapeHtml(item.url) + (item.external ? ' ↗' : '') + '</a>' +
      '</article>';
    }).join('');
  }

  function init() {
    var input = document.getElementById('search-page-input');
    var count = document.getElementById('search-page-count');
    var results = document.getElementById('search-page-results');
    var empty = document.getElementById('search-page-empty');
    var hint = document.getElementById('search-page-hint');
    var reset = document.getElementById('search-page-reset');
    if (!input || !count || !results || !empty || !hint || !reset) {
      return;
    }

    var index = parseIndex();

    function applySearch() {
      var query = input.value.trim().toLowerCase();
      updateUrl(query);

      if (!query) {
        results.innerHTML = '';
        count.textContent = 'Enter a search term to begin.';
        empty.hidden = true;
        reset.hidden = true;
        hint.hidden = false;
        return;
      }

      reset.hidden = false;
      hint.hidden = true;

      var terms = query.split(/\s+/).filter(Boolean);
      var matches = index
        .map(function (item) {
          return { item: item, score: scoreItem(item, query, terms) };
        })
        .filter(function (entry) { return entry.score > 0; })
        .sort(function (a, b) {
          if (b.score !== a.score) {
            return b.score - a.score;
          }
          return a.item.title.localeCompare(b.item.title);
        })
        .map(function (entry) { return entry.item; });

      count.textContent = matches.length + ' result' + (matches.length !== 1 ? 's' : '');
      empty.hidden = matches.length !== 0;

      if (!matches.length) {
        results.innerHTML = '';
        return;
      }

      renderResults(results, matches);
    }

    input.addEventListener('input', applySearch);
    reset.addEventListener('click', function () {
      input.value = '';
      applySearch();
      input.focus();
    });

    var params = new URLSearchParams(window.location.search);
    var initialQuery = params.get('q');
    if (initialQuery) {
      input.value = initialQuery;
    }
    applySearch();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();