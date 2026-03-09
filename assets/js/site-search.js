/* CollabAtlas — Global site search */

(function () {
  'use strict';

  function parseIndex() {
    var element = document.getElementById('site-search-index');
    if (!element) {
      return [];
    }

    try {
      return JSON.parse(element.textContent).map(function (item) {
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

  function init() {
    var search = document.getElementById('site-search');
    var input = document.getElementById('site-search-input');
    var panel = document.getElementById('site-search-panel');
    var status = document.getElementById('site-search-status');
    var results = document.getElementById('site-search-results');
    var moreLink = document.getElementById('site-search-more');
    if (!search || !input || !panel || !status || !results) {
      return;
    }

    var index = parseIndex();
    var activeIndex = -1;
    var currentMatches = [];
    var searchPage = search.dataset.searchPage || '/search/';

    function buildSearchPageUrl(query) {
      var url = new URL(searchPage, window.location.origin);
      if (query) {
        url.searchParams.set('q', query);
      }
      return url.toString();
    }

    function closePanel() {
      panel.hidden = true;
      activeIndex = -1;
      currentMatches = [];
      results.innerHTML = '';
    }

    function openPanel() {
      panel.hidden = false;
    }

    function updateActiveResult() {
      var links = results.querySelectorAll('.site-search-link');
      links.forEach(function (link, index) {
        var selected = index === activeIndex;
        link.classList.toggle('is-active', selected);
        if (selected) {
          input.setAttribute('aria-activedescendant', link.id);
        }
      });

      if (activeIndex < 0) {
        input.removeAttribute('aria-activedescendant');
      }
    }

    function renderResults(matches, query) {
      if (!query) {
        status.textContent = 'Type at least 2 characters to search.';
        results.innerHTML = '';
        if (moreLink) {
          moreLink.href = buildSearchPageUrl('');
        }
        closePanel();
        return;
      }

      openPanel();
      if (moreLink) {
        moreLink.href = buildSearchPageUrl(query);
      }

      if (!matches.length) {
        status.textContent = 'No results found.';
        results.innerHTML = '';
        activeIndex = -1;
        input.removeAttribute('aria-activedescendant');
        return;
      }

      status.textContent = matches.length + ' result' + (matches.length !== 1 ? 's' : '') + ' found.';
      results.innerHTML = matches.map(function (item, index) {
        var typeLabel = formatTypeLabel(item.type);
        var target = item.external ? ' target="_blank" rel="noopener"' : '';
        return '<li class="site-search-item">' +
          '<a id="site-search-option-' + index + '" class="site-search-link" href="' + escapeHtml(item.url) + '" role="option"' + target + '>' +
            '<span class="badge site-search-badge">' + escapeHtml(typeLabel) + '</span>' +
            '<span class="site-search-title">' + escapeHtml(item.title) + '</span>' +
            (item.summary ? '<span class="site-search-summary">' + escapeHtml(item.summary) + '</span>' : '') +
          '</a>' +
        '</li>';
      }).join('');

      activeIndex = -1;
      input.removeAttribute('aria-activedescendant');

      results.querySelectorAll('.site-search-link').forEach(function (link, index) {
        link.addEventListener('mouseenter', function () {
          activeIndex = index;
          updateActiveResult();
        });
      });
    }

    function runSearch() {
      var query = input.value.trim().toLowerCase();
      if (query.length < 2) {
        renderResults([], '');
        return;
      }

      var terms = query.split(/\s+/).filter(Boolean);
      currentMatches = index
        .map(function (item) {
          return {
            item: item,
            score: scoreItem(item, query, terms)
          };
        })
        .filter(function (entry) { return entry.score > 0; })
        .sort(function (a, b) {
          if (b.score !== a.score) {
            return b.score - a.score;
          }

          return a.item.title.localeCompare(b.item.title);
        })
        .slice(0, 8)
        .map(function (entry) { return entry.item; });

      renderResults(currentMatches, query);
    }

    input.addEventListener('input', runSearch);
    input.addEventListener('focus', function () {
      if (input.value.trim().length >= 2) {
        runSearch();
      }
    });

    input.addEventListener('keydown', function (event) {
      if (panel.hidden || !currentMatches.length) {
        if (event.key === 'Escape') {
          closePanel();
        }
        return;
      }

      if (event.key === 'ArrowDown') {
        event.preventDefault();
        activeIndex = (activeIndex + 1) % currentMatches.length;
        updateActiveResult();
        return;
      }

      if (event.key === 'ArrowUp') {
        event.preventDefault();
        activeIndex = activeIndex <= 0 ? currentMatches.length - 1 : activeIndex - 1;
        updateActiveResult();
        return;
      }

      if (event.key === 'Enter') {
        if (activeIndex >= 0) {
          event.preventDefault();
          results.querySelectorAll('.site-search-link')[activeIndex].click();
        } else if (input.value.trim().length >= 2) {
          window.location.href = buildSearchPageUrl(input.value.trim().toLowerCase());
        }
        return;
      }

      if (event.key === 'Escape') {
        closePanel();
        input.blur();
      }
    });

    document.addEventListener('click', function (event) {
      if (!search.contains(event.target)) {
        closePanel();
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();