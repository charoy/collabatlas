/* CollabAtlas — Entry comparison */

(function () {
  'use strict';

  var STORAGE_KEY = 'collabatlas-compare-selection';
  var MAX_ITEMS = 4;
  var COMPARE_DATA_URL = (window.__BASE_URL__ || '/') + 'compare/index.json';
  var compareDataCache = null;

  async function fetchCompareData() {
    if (compareDataCache) return compareDataCache;
    // Fallback: try inline data first (for backwards compat)
    var element = document.getElementById('compare-data');
    if (element) {
      try {
        var payload = JSON.parse(element.textContent);
        if (typeof payload === 'string') payload = JSON.parse(payload);
        compareDataCache = Array.isArray(payload) ? payload : [];
        return compareDataCache;
      } catch (e) {}
    }
    // Fetch from external JSON
    try {
      var resp = await fetch(COMPARE_DATA_URL);
      if (!resp.ok) throw new Error('HTTP ' + resp.status);
      var data = await resp.json();
      compareDataCache = Array.isArray(data) ? data : [];
    } catch (err) {
      console.error('Failed to load compare data.', err);
      compareDataCache = [];
    }
    return compareDataCache;
  }

  function escapeHtml(value) {
    return String(value || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function capitalize(value) {
    return String(value || '')
      .replace(/-/g, ' ')
      .replace(/\b\w/g, function (letter) { return letter.toUpperCase(); });
  }

  function readStoredSelection() {
    try {
      var raw = window.localStorage.getItem(STORAGE_KEY);
      if (!raw) {
        return [];
      }
      var parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch (error) {
      return [];
    }
  }

  function writeStoredSelection(selection) {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(selection));
    } catch (error) {
      console.warn('Unable to persist comparison selection.', error);
    }
  }

  function dedupeSelection(selection, validIds) {
    var unique = [];
    selection.forEach(function (id) {
      if (unique.indexOf(id) === -1 && validIds.indexOf(id) !== -1) {
        unique.push(id);
      }
    });
    return unique.slice(0, MAX_ITEMS);
  }

  function buildCompareUrl(basePath, selection) {
    var url = new URL(basePath, window.location.origin);
    if (selection.length) {
      url.searchParams.set('items', selection.join(','));
    }
    return url.toString();
  }

  function parseSelectionFromUrl(validIds) {
    var params = new URLSearchParams(window.location.search);
    var raw = params.get('items');
    if (!raw) {
      return [];
    }
    return dedupeSelection(raw.split(','), validIds);
  }

  async function init() {
    var compareEntries = await fetchCompareData();
    if (!compareEntries.length) {
      return;
    }

    var compareMap = compareEntries.reduce(function (acc, entry) {
      acc[entry.id] = entry;
      return acc;
    }, {});
    var validIds = compareEntries.map(function (entry) { return entry.id; });

    var dock = document.getElementById('compare-dock');
    var dockSummary = document.getElementById('compare-dock-summary');
    var dockFeedback = document.getElementById('compare-dock-feedback');
    var dockOpen = document.getElementById('compare-dock-open');
    var dockClear = document.getElementById('compare-dock-clear');
    var comparePath = dock ? (dock.dataset.comparePage || '/compare/') : '/compare/';

    var compareButtons = Array.prototype.slice.call(document.querySelectorAll('.compare-toggle'));
    var comparePage = document.getElementById('compare-table');
    var compareCount = document.getElementById('compare-page-count');
    var compareEmpty = document.getElementById('compare-empty');
    var compareWrap = document.getElementById('compare-table-wrap');
    var compareHead = document.getElementById('compare-table-head');
    var compareBody = document.getElementById('compare-table-body');
    var compareClear = document.getElementById('compare-page-clear');
    var compareCopy = document.getElementById('compare-page-copy');
    var compareFeedback = document.getElementById('compare-share-feedback');
    var canUseDockOnPage = compareButtons.length > 0;

    if (dock && !canUseDockOnPage) {
      dock.hidden = true;
    }

    var selection = dedupeSelection(readStoredSelection(), validIds);
    var selectionFromUrl = parseSelectionFromUrl(validIds);
    if (selectionFromUrl.length) {
      selection = selectionFromUrl;
      writeStoredSelection(selection);
    }

    function setFeedback(message) {
      if (dockFeedback) {
        dockFeedback.textContent = message || '';
      }
      if (compareFeedback) {
        compareFeedback.textContent = message || '';
      }
    }

    function getSelectionEntries() {
      return selection.map(function (id) { return compareMap[id]; }).filter(Boolean);
    }

    function syncCardButtons() {
      compareButtons.forEach(function (button) {
        var isSelected = selection.indexOf(button.dataset.compareId) !== -1;
        button.setAttribute('aria-pressed', isSelected ? 'true' : 'false');
        button.classList.toggle('is-selected', isSelected);
        button.textContent = isSelected ? 'Remove from compare' : 'Add to compare';
      });
    }

    function syncDock() {
      if (!dock || !dockSummary || !dockOpen) {
        return;
      }

      if (!canUseDockOnPage) {
        dock.hidden = true;
        return;
      }

      var entries = getSelectionEntries();
      dock.hidden = entries.length === 0;

      if (!entries.length) {
        dockSummary.textContent = 'No entries selected.';
        dockOpen.setAttribute('aria-disabled', 'true');
        dockOpen.href = comparePath;
        return;
      }

      dockSummary.textContent = entries.length + ' entr' + (entries.length === 1 ? 'y' : 'ies') + ' selected: ' + entries.map(function (entry) {
        return entry.title;
      }).join(', ');

      dockOpen.removeAttribute('aria-disabled');
      dockOpen.href = buildCompareUrl(comparePath, selection);
    }

    function renderComparePage() {
      if (!comparePage || !compareCount || !compareEmpty || !compareWrap || !compareHead || !compareBody) {
        return;
      }

      var entries = getSelectionEntries();
      var params = new URLSearchParams(window.location.search);
      if (entries.length) {
        params.set('items', selection.join(','));
      } else {
        params.delete('items');
      }
      window.history.replaceState({}, '', window.location.pathname + (params.toString() ? '?' + params.toString() : ''));

      compareCount.textContent = entries.length
        ? entries.length + ' entr' + (entries.length === 1 ? 'y' : 'ies') + ' selected'
        : 'No entries selected.';

      if (compareClear) {
        compareClear.hidden = entries.length === 0;
      }
      if (compareCopy) {
        compareCopy.hidden = entries.length < 2;
      }

      if (entries.length < 2) {
        compareEmpty.hidden = false;
        compareWrap.hidden = true;
        compareHead.innerHTML = '';
        compareBody.innerHTML = '';
        return;
      }

      compareEmpty.hidden = true;
      compareWrap.hidden = false;

      compareHead.innerHTML = '<tr><th scope="col">Criteria</th>' + entries.map(function (entry) {
        return '<th scope="col"><div class="compare-head-card">' +
          '<button type="button" class="compare-remove" data-remove-id="' + escapeHtml(entry.id) + '">Remove</button>' +
          '<a href="' + escapeHtml(entry.url) + '" class="compare-head-link">' + escapeHtml(entry.title) + '</a>' +
          '<p class="compare-head-tagline">' + escapeHtml(entry.tagline || '') + '</p>' +
        '</div></th>';
      }).join('') + '</tr>';

      var rows = [
        { label: 'Type', key: 'type', format: function (value) { return capitalize(value); } },
        { label: 'Maturity', key: 'maturity', format: function (value) { return value ? capitalize(value) : '—'; } },
        { label: 'Domains', key: 'domains', list: true },
        { label: 'Collaboration', key: 'collaborationTypes', list: true },
        { label: 'Modalities', key: 'modalities', list: true },
        { label: 'Scales', key: 'scales', list: true },
        { label: 'When to use', key: 'whenToUse' },
        { label: 'Limitations', key: 'limitations' }
      ];

      compareBody.innerHTML = rows.map(function (row) {
        return '<tr><th scope="row">' + escapeHtml(row.label) + '</th>' + entries.map(function (entry) {
          var value = entry[row.key];
          var content = '—';

          if (row.list) {
            content = Array.isArray(value) && value.length
              ? '<ul class="compare-list">' + value.map(function (item) { return '<li>' + escapeHtml(capitalize(item)) + '</li>'; }).join('') + '</ul>'
              : '—';
          } else if (typeof row.format === 'function') {
            content = escapeHtml(row.format(value));
          } else if (value) {
            content = escapeHtml(value);
          }

          return '<td>' + content + '</td>';
        }).join('') + '</tr>';
      }).join('');

      Array.prototype.slice.call(compareHead.querySelectorAll('.compare-remove')).forEach(function (button) {
        button.addEventListener('click', function () {
          removeFromSelection(button.dataset.removeId);
        });
      });
    }

    function syncAll() {
      writeStoredSelection(selection);
      syncCardButtons();
      syncDock();
      renderComparePage();
    }

    function addToSelection(id) {
      if (selection.indexOf(id) !== -1) {
        return;
      }

      if (selection.length >= MAX_ITEMS) {
        setFeedback('You can compare up to ' + MAX_ITEMS + ' entries at a time.');
        return;
      }

      selection.push(id);
      setFeedback('Added to comparison.');
      syncAll();
    }

    function removeFromSelection(id) {
      selection = selection.filter(function (entryId) {
        return entryId !== id;
      });
      setFeedback('Removed from comparison.');
      syncAll();
    }

    function clearSelection() {
      selection = [];
      setFeedback('Comparison cleared.');
      syncAll();
    }

    compareButtons.forEach(function (button) {
      button.addEventListener('click', function () {
        var id = button.dataset.compareId;
        if (selection.indexOf(id) !== -1) {
          removeFromSelection(id);
        } else {
          addToSelection(id);
        }
      });
    });

    if (dockClear) {
      dockClear.addEventListener('click', clearSelection);
    }

    if (compareClear) {
      compareClear.addEventListener('click', clearSelection);
    }

    if (compareCopy) {
      compareCopy.addEventListener('click', function () {
        var shareUrl = buildCompareUrl(comparePath, selection);
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(shareUrl)
            .then(function () { setFeedback('Comparison link copied.'); })
            .catch(function () { setFeedback('Unable to copy automatically.'); });
          return;
        }
        setFeedback('Clipboard access is unavailable.');
      });
    }

    syncAll();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();