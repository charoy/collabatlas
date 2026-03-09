/* CollabAtlas — Research client-side filtering */

(function () {
  'use strict';

  function escapeHtml(value) {
    return String(value || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function updateUrl(filters) {
    var url = new URL(window.location.href);

    if (filters.domain) {
      url.searchParams.set('domain', filters.domain);
    } else {
      url.searchParams.delete('domain');
    }

    if (filters.access) {
      url.searchParams.set('access', filters.access);
    } else {
      url.searchParams.delete('access');
    }

    if (filters.search) {
      url.searchParams.set('search', filters.search);
    } else {
      url.searchParams.delete('search');
    }

    window.history.replaceState({}, '', url.toString());
  }

  function renderChips(container, filters, onRemove) {
    if (!container) {
      return;
    }

    var active = [];
    if (filters.domain) {
      active.push({ key: 'domain', label: 'Domain', value: filters.domain });
    }
    if (filters.access) {
      active.push({ key: 'access', label: 'Access', value: filters.access });
    }
    if (filters.search) {
      active.push({ key: 'search', label: 'Search', value: filters.search });
    }

    if (!active.length) {
      container.hidden = true;
      container.innerHTML = '';
      return;
    }

    container.hidden = false;
    container.innerHTML = active.map(function (item) {
      return '<button type="button" class="filter-chip" data-key="' + item.key + '">' +
        '<span class="filter-chip-label">' + escapeHtml(item.label) + ':</span> ' +
        '<span class="filter-chip-value">' + escapeHtml(item.value) + '</span>' +
        '<span class="filter-chip-remove" aria-hidden="true">×</span>' +
      '</button>';
    }).join('');

    container.querySelectorAll('.filter-chip').forEach(function (button) {
      button.addEventListener('click', function () {
        onRemove(button.dataset.key);
      });
    });
  }

  function splitValues(raw) {
    return raw ? raw.split('|').filter(Boolean) : [];
  }

  function init() {
    var list = document.getElementById('research-list');
    var empty = document.getElementById('research-empty');
    var count = document.getElementById('research-count');
    var fDomain = document.getElementById('filter-domain');
    var fAccess = document.getElementById('filter-access');
    var fSearch = document.getElementById('filter-search');
    var reset = document.getElementById('research-reset');
    var chips = document.getElementById('research-filter-chips');
    if (!list || !empty || !count || !fDomain || !fAccess || !fSearch || !reset) {
      return;
    }

    var cards = Array.prototype.slice.call(list.querySelectorAll('.research-card')).map(function (card) {
      return {
        element: card,
        domains: splitValues(card.dataset.domains),
        access: card.dataset.access || '',
        text: (card.dataset.text || '').toLowerCase()
      };
    });

    function getFilters() {
      return {
        domain: fDomain.value,
        access: fAccess.value,
        search: fSearch.value.trim().toLowerCase()
      };
    }

    function applyFilters() {
      var filters = getFilters();
      var hasFilter = filters.domain || filters.access || filters.search;
      var visible = 0;

      cards.forEach(function (card) {
        var matchDomain = !filters.domain || card.domains.indexOf(filters.domain) !== -1;
        var matchAccess = !filters.access || card.access === filters.access;
        var matchSearch = !filters.search || card.text.indexOf(filters.search) !== -1;
        var show = matchDomain && matchAccess && matchSearch;
        card.element.hidden = !show;
        if (show) {
          visible++;
        }
      });

      count.textContent = visible + ' article' + (visible !== 1 ? 's' : '');
      empty.hidden = visible !== 0;
      reset.hidden = !hasFilter;
      renderChips(chips, filters, function (key) {
        if (key === 'domain') fDomain.value = '';
        if (key === 'access') fAccess.value = '';
        if (key === 'search') fSearch.value = '';
        applyFilters();
      });
      updateUrl(filters);
    }

    function restoreFromUrl() {
      var params = new URLSearchParams(window.location.search);
      var domain = params.get('domain');
      var access = params.get('access');
      var search = params.get('search');

      if (domain) {
        fDomain.value = domain;
      }
      if (access) {
        fAccess.value = access;
      }
      if (search) {
        fSearch.value = search;
      }
    }

    fDomain.addEventListener('change', applyFilters);
    fAccess.addEventListener('change', applyFilters);
    fSearch.addEventListener('input', applyFilters);
    reset.addEventListener('click', function () {
      fDomain.value = '';
      fAccess.value = '';
      fSearch.value = '';
      applyFilters();
    });

    restoreFromUrl();
    applyFilters();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();