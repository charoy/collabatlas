/* CollabAtlas — Local favorites */

(function () {
  'use strict';

  var STORAGE_KEY = 'collabatlas-favorites';

  function readFavorites() {
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

  function writeFavorites(favorites) {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(favorites));
    } catch (error) {
      console.warn('Unable to persist favorites.', error);
    }
  }

  function dedupeFavorites(favorites) {
    var seen = [];
    favorites.forEach(function (item) {
      if (!item || !item.id || seen.some(function (entry) { return entry.id === item.id; })) {
        return;
      }
      seen.push({
        id: item.id,
        title: item.title || item.id,
        url: item.url || ''
      });
    });
    return seen;
  }

  function findFavorite(favorites, id) {
    return favorites.find(function (item) { return item.id === id; }) || null;
  }

  function emitFavoritesChanged(favorites) {
    document.dispatchEvent(new CustomEvent('collabatlas:favorites-changed', {
      detail: { favorites: favorites.slice() }
    }));
  }

  function syncButtons(favorites) {
    var favoriteIds = favorites.map(function (item) { return item.id; });
    Array.prototype.slice.call(document.querySelectorAll('.favorite-toggle')).forEach(function (button) {
      var id = button.dataset.favoriteId;
      var isFavorite = favoriteIds.indexOf(id) !== -1;
      var icon = button.querySelector('.favorite-toggle-icon');
      var label = button.querySelector('.favorite-toggle-label');
      var article = button.closest('[data-entry-id]');

      button.setAttribute('aria-pressed', isFavorite ? 'true' : 'false');
      button.classList.toggle('is-selected', isFavorite);
      button.title = isFavorite ? 'Remove from favorites' : 'Save to favorites';

      if (icon) {
        icon.textContent = isFavorite ? '★' : '☆';
      }
      if (label) {
        label.textContent = isFavorite ? 'Saved' : (button.closest('.entry-card') ? 'Save' : 'Save to favorites');
      }
      if (article) {
        article.classList.toggle('is-favorite', isFavorite);
      }
    });
  }

  function init() {
    var buttons = Array.prototype.slice.call(document.querySelectorAll('.favorite-toggle'));
    if (!buttons.length) {
      emitFavoritesChanged(dedupeFavorites(readFavorites()));
      return;
    }

    var favorites = dedupeFavorites(readFavorites());

    function updateFavorites(nextFavorites) {
      favorites = dedupeFavorites(nextFavorites);
      writeFavorites(favorites);
      syncButtons(favorites);
      emitFavoritesChanged(favorites);
    }

    function toggleFavorite(button) {
      var id = button.dataset.favoriteId;
      var existing = findFavorite(favorites, id);

      if (existing) {
        updateFavorites(favorites.filter(function (item) { return item.id !== id; }));
        return;
      }

      updateFavorites(favorites.concat({
        id: id,
        title: button.dataset.favoriteTitle || id,
        url: button.dataset.favoriteUrl || ''
      }));
    }

    buttons.forEach(function (button) {
      button.addEventListener('click', function () {
        toggleFavorite(button);
      });
    });

    window.addEventListener('storage', function (event) {
      if (event.key === STORAGE_KEY) {
        favorites = dedupeFavorites(readFavorites());
        syncButtons(favorites);
        emitFavoritesChanged(favorites);
      }
    });

    syncButtons(favorites);
    emitFavoritesChanged(favorites);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
