/* CollabAtlas — Pagefind search bridge for header dropdown */

(function () {
  'use strict';

  var pagefind = null;
  var debounceTimer = null;

  function getBaseUrl() {
    // Injected by Hugo in baseof.html as window.__BASE_URL__
    return window.__BASE_URL__ || '/';
  }

  async function loadPagefind() {
    if (pagefind) return pagefind;
    try {
      var baseUrl = getBaseUrl();
      pagefind = await import(baseUrl + 'pagefind/pagefind.js');
      await pagefind.init();
      return pagefind;
    } catch (e) {
      console.error('Failed to load Pagefind:', e);
      return null;
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

    var activeIndex = -1;
    var currentCount = 0;
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
      currentCount = 0;
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

    function renderResults(items, query) {
      if (!query) {
        status.textContent = 'Type at least 2 characters to search.';
        results.innerHTML = '';
        if (moreLink) moreLink.href = buildSearchPageUrl('');
        closePanel();
        return;
      }

      openPanel();
      if (moreLink) moreLink.href = buildSearchPageUrl(query);

      if (!items.length) {
        status.textContent = 'No results found.';
        results.innerHTML = '';
        activeIndex = -1;
        input.removeAttribute('aria-activedescendant');
        return;
      }

      status.textContent = items.length + ' result' + (items.length !== 1 ? 's' : '') + ' found.';
      currentCount = items.length;

      results.innerHTML = items.map(function (item, index) {
        var typeLabel = (item.meta.type || 'page').replace(/-/g, ' ').replace(/\b\w/g, function (l) { return l.toUpperCase(); });
        return '<li class="site-search-item">' +
          '<a id="site-search-option-' + index + '" class="site-search-link" href="' + escapeHtml(item.meta.url || item.url) + '" role="option">' +
            '<span class="badge site-search-badge">' + escapeHtml(typeLabel) + '</span>' +
            '<span class="site-search-title">' + escapeHtml(item.meta.title) + '</span>' +
            (item.excerpt ? '<span class="site-search-summary">' + item.excerpt.replace(/<(?!\/?mark\b)[^>]*>/g, '') + '</span>' : '') +
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

    async function performSearch(query) {
      if (query.length < 2) {
        renderResults([], '');
        return;
      }

      var pf = await loadPagefind();
      if (!pf) {
        status.textContent = 'Search unavailable.';
        openPanel();
        return;
      }

      var search = await pf.search(query);
      var topResults = search.results.slice(0, 8);
      var items = await Promise.all(topResults.map(function (r) { return r.data(); }));
      renderResults(items, query);
    }

    function runSearch() {
      var query = input.value.trim();
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(function () {
        performSearch(query);
      }, 200);
    }

    // Lazy load on interaction
    function lazyLoad() {
      loadPagefind();
    }

    input.addEventListener('input', runSearch);
    input.addEventListener('focus', lazyLoad);

    input.addEventListener('keydown', function (event) {
      if (panel.hidden || !currentCount) {
        if (event.key === 'Escape') closePanel();
        return;
      }

      if (event.key === 'ArrowDown') {
        event.preventDefault();
        activeIndex = (activeIndex + 1) % currentCount;
        updateActiveResult();
        return;
      }

      if (event.key === 'ArrowUp') {
        event.preventDefault();
        activeIndex = activeIndex <= 0 ? currentCount - 1 : activeIndex - 1;
        updateActiveResult();
        return;
      }

      if (event.key === 'Enter') {
        if (activeIndex >= 0) {
          event.preventDefault();
          results.querySelectorAll('.site-search-link')[activeIndex].click();
        } else if (input.value.trim().length >= 2) {
          window.location.href = buildSearchPageUrl(input.value.trim());
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
