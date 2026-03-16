/* CollabAtlas — Dedicated search results page */

(function () {
  'use strict';

  var searchIndex = [];
  var isLoaded = false;
  var isLoading = false;

  function loadIndex() {
    if (isLoaded) return Promise.resolve(searchIndex);
    if (isLoading) return new Promise(function(resolve) {
      var check = setInterval(function() {
        if (isLoaded) {
          clearInterval(check);
          resolve(searchIndex);
        }
      }, 100);
    });

    isLoading = true;
    var url = window.SEARCH_INDEX_URL || '/index.json';
    return fetch(url)
      .then(function(response) {
        if (!response.ok) throw new Error(response.statusText);
        return response.json();
      })
      .then(function(data) {
        searchIndex = data.map(function (item) {
          return {
            title: item.title || '',
            url: item.url || '#',
            type: item.type || 'page',
            summary: item.summary || '',
            text: (item.text || '').toLowerCase(),
            external: Boolean(item.external)
          };
        });
        isLoaded = true;
        isLoading = false;
        return searchIndex;
      })
      .catch(function(error) {
        console.error('Unable to load search index:', error);
        isLoading = false;
        return [];
      });
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
    // Check for elements matching layouts/search/list.html
    var input = document.getElementById('search-page-input');
    var resultsContainer = document.getElementById('search-page-results');
    var countDisplay = document.getElementById('search-page-count');
    var emptyMessage = document.getElementById('search-page-empty');
    var resetButton = document.getElementById('search-page-reset');
    var hintMessage = document.getElementById('search-page-hint');

    if (!input || !resultsContainer) {
      return;
    }

    function renderResults(matches, query) {
        resultsContainer.innerHTML = '';
        
        if (!query) {
            countDisplay.textContent = '';
            emptyMessage.hidden = true;
            if (hintMessage) hintMessage.hidden = false;
            if (resetButton) resetButton.hidden = true;
            return;
        }

        if (hintMessage) hintMessage.hidden = true;
        if (resetButton) resetButton.hidden = false;

        if (matches.length === 0) {
            countDisplay.textContent = '0 results'; // Or hidden
            emptyMessage.hidden = false;
            return;
        }

        emptyMessage.hidden = true;
        countDisplay.textContent = matches.length + ' result' + (matches.length !== 1 ? 's' : '');

        var html = matches.map(function(item) {
             var typeLabel = formatTypeLabel(item.type);
             var target = item.external ? ' target="_blank" rel="noopener"' : '';
             return '<article class="search-result-card">' +
                '<header class="search-result-header">' +
                '<span class="badge search-result-badge">' + escapeHtml(typeLabel) + '</span>' +
                '<h2 class="search-result-title"><a href="' + escapeHtml(item.url) + '"' + target + '>' + escapeHtml(item.title) + '</a></h2>' +
                '</header>' +
                (item.summary ? '<p class="search-result-summary">' + escapeHtml(item.summary) + '</p>' : '') +
            '</article>';
        }).join('');
        
        resultsContainer.innerHTML = html;
    }

    function performSearch(query) {
       if (!query) {
          renderResults([], '');
          // Update URL to remove query
          var url = new URL(window.location);
          url.searchParams.delete('q');
          window.history.replaceState({}, '', url);
          return;
       }

       // Update URL
       var url = new URL(window.location);
       url.searchParams.set('q', query);
       window.history.replaceState({}, '', url);

       loadIndex().then(function(index) {
          var terms = query.toLowerCase().split(/\s+/).filter(Boolean);
          var matches = index
            .map(function (item) {
                return {
                item: item,
                score: scoreItem(item, query.toLowerCase(), terms)
                };
            })
            .filter(function (entry) { return entry.score > 0; })
            .sort(function (a, b) {
                if (b.score !== a.score) {
                return b.score - a.score;
                }
                return a.item.title.localeCompare(b.item.title);
            })
            .map(function (entry) { return entry.item; });
          
          renderResults(matches, query);
       });
    }

    // Event Listeners
    input.addEventListener('input', function() {
        performSearch(input.value.trim());
    });
    
    if (resetButton) {
        resetButton.addEventListener('click', function() {
            input.value = '';
            performSearch('');
            input.focus();
        });
    }

    // Initial Load from URL
    var params = new URLSearchParams(window.location.search);
    var initialQuery = (params.get('q') || '').trim();
    if (initialQuery) {
        input.value = initialQuery;
        // Trigger search immediately
        performSearch(initialQuery);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
