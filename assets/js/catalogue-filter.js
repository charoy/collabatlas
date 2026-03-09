/* CollabAtlas — Catalogue client-side filtering */

(function () {
  'use strict';

  const FILTER_FIELDS = [
    { key: 'search', param: 'search', label: 'Search' },
    { key: 'type', param: 'type', label: 'Type' },
    { key: 'domain', param: 'domain', label: 'Domain' },
    { key: 'collabType', param: 'collaboration_type', label: 'Collaboration' },
    { key: 'scale', param: 'scale', label: 'Scale' },
    { key: 'modality', param: 'modality', label: 'Modality' }
  ];

  function splitValues(raw) {
    return raw ? raw.split('|').filter(Boolean) : [];
  }

  function updateUrl(filters) {
    const url = new URL(window.location.href);

    FILTER_FIELDS.forEach(field => {
      const value = filters[field.key];
      if (value) {
        url.searchParams.set(field.param, value);
      } else {
        url.searchParams.delete(field.param);
      }
    });

    window.history.replaceState({}, '', url.toString());
  }

  function renderChips(container, filters, onRemove) {
    const activeFilters = FILTER_FIELDS.filter(field => filters[field.key]);
    if (!container) {
      return;
    }

    if (!activeFilters.length) {
      container.hidden = true;
      container.innerHTML = '';
      return;
    }

    container.hidden = false;
    container.innerHTML = activeFilters.map(field => {
      const value = filters[field.key];
      return '<button type="button" class="filter-chip" data-filter-key="' + field.key + '">' +
        '<span class="filter-chip-label">' + field.label + ':</span> ' +
        '<span class="filter-chip-value">' + escapeHtml(String(value)) + '</span>' +
        '<span class="filter-chip-remove" aria-hidden="true">×</span>' +
      '</button>';
    }).join('');

    container.querySelectorAll('.filter-chip').forEach(button => {
      button.addEventListener('click', () => onRemove(button.dataset.filterKey));
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

  function init() {
    const filterBar = document.querySelector('.filters');
    if (!filterBar) return;

    const cards = Array.from(document.querySelectorAll('.entry-card'));
    if (!cards.length) return;
    const sections = Array.from(document.querySelectorAll('.type-section'));

    let emptyMessage = document.querySelector('.filter-empty');
    if (!emptyMessage) {
      emptyMessage = document.createElement('p');
      emptyMessage.className = 'filter-empty';
      emptyMessage.hidden = true;
      emptyMessage.textContent = 'No entries match your filters. Try clearing one or more filters.';
      filterBar.insertAdjacentElement('afterend', emptyMessage);
    }

    const cardIndex = cards.map(card => ({
      element: card,
      type: card.dataset.type || '',
      text: card.dataset.searchText || card.textContent.toLowerCase(),
      domains: splitValues(card.dataset.domains),
      collaborationTypes: splitValues(card.dataset.collaborationTypes),
      scales: splitValues(card.dataset.scales),
      modalities: splitValues(card.dataset.modalities)
    }));

    // Collect unique values from cards
    const domains = new Set();
    const types = new Set();
    const collabTypes = new Set();
    const modalities = new Set();
    const scales = new Set();

    cardIndex.forEach(card => {
      const type = card.type;
      if (type) types.add(type);

      card.domains.forEach(value => domains.add(value));
      card.collaborationTypes.forEach(value => collabTypes.add(value));
      card.modalities.forEach(value => modalities.add(value));
      card.scales.forEach(value => scales.add(value));
    });

    // Build filter controls
    filterBar.innerHTML = `
      <label class="filter-label">
        <span>Search</span>
        <input type="search" id="filter-search" placeholder="Filter by title or keyword…" aria-label="Search entries">
      </label>
      ${types.size > 1 ? `
      <label class="filter-label">
        <span>Type</span>
        <select id="filter-type" aria-label="Filter by type">
          <option value="">All types</option>
          ${[...types].sort().map(t => `<option value="${t}">${capitalize(t)}</option>`).join('')}
        </select>
      </label>` : ''}
      ${domains.size ? `
      <label class="filter-label">
        <span>Domain</span>
        <select id="filter-domain" aria-label="Filter by domain">
          <option value="">All domains</option>
          ${[...domains].sort().map(d => `<option value="${d}">${d}</option>`).join('')}
        </select>
      </label>` : ''}
      ${collabTypes.size ? `
      <label class="filter-label">
        <span>Collaboration</span>
        <select id="filter-collaboration-type" aria-label="Filter by collaboration type">
          <option value="">All collaboration types</option>
          ${[...collabTypes].sort().map(c => `<option value="${c}">${capitalize(c)}</option>`).join('')}
        </select>
      </label>` : ''}
      ${scales.size ? `
      <label class="filter-label">
        <span>Scale</span>
        <select id="filter-scale" aria-label="Filter by scale">
          <option value="">All scales</option>
          ${[...scales].sort().map(s => `<option value="${s}">${capitalize(s)}</option>`).join('')}
        </select>
      </label>` : ''}
      ${modalities.size ? `
      <label class="filter-label">
        <span>Modality</span>
        <select id="filter-modality" aria-label="Filter by modality">
          <option value="">All modalities</option>
          ${[...modalities].sort().map(m => `<option value="${m}">${capitalize(m)}</option>`).join('')}
        </select>
      </label>` : ''}
      <div class="filter-actions">
        <button id="filter-reset" type="button" class="btn btn-secondary filter-reset" hidden>Clear filters</button>
        <span id="filter-count" class="filter-count" aria-live="polite"></span>
      </div>
      <div id="filter-chips" class="filter-chips" hidden aria-live="polite"></div>
    `;

    const searchInput = document.getElementById('filter-search');
    const typeSelect = document.getElementById('filter-type');
    const domainSelect = document.getElementById('filter-domain');
    const collabTypeSelect = document.getElementById('filter-collaboration-type');
    const scaleSelect = document.getElementById('filter-scale');
    const modalitySelect = document.getElementById('filter-modality');
    const resetBtn = document.getElementById('filter-reset');
    const countSpan = document.getElementById('filter-count');
    const chips = document.getElementById('filter-chips');

    const controls = {
      search: searchInput,
      type: typeSelect,
      domain: domainSelect,
      collabType: collabTypeSelect,
      scale: scaleSelect,
      modality: modalitySelect
    };

    function getFilters() {
      return {
        search: searchInput ? searchInput.value.trim().toLowerCase() : '',
        type: typeSelect ? typeSelect.value : '',
        domain: domainSelect ? domainSelect.value : '',
        collabType: collabTypeSelect ? collabTypeSelect.value : '',
        scale: scaleSelect ? scaleSelect.value : '',
        modality: modalitySelect ? modalitySelect.value : '',
      };
    }

    function setFilterValue(key, value) {
      const control = controls[key];
      if (!control) return;
      control.value = value;
    }

    function applyFilters() {
      const f = getFilters();
      const hasFilter = f.search || f.type || f.domain || f.collabType || f.scale || f.modality;
      resetBtn.hidden = !hasFilter;

      let visible = 0;
      cardIndex.forEach(card => {
        let show = true;

        if (f.search) {
          if (!card.text.includes(f.search)) show = false;
        }
        if (f.type && card.type !== f.type) show = false;
        if (f.domain && !card.domains.includes(f.domain)) show = false;
        if (f.collabType && !card.collaborationTypes.includes(f.collabType)) show = false;
        if (f.scale && !card.scales.includes(f.scale)) show = false;
        if (f.modality && !card.modalities.includes(f.modality)) show = false;

        card.element.hidden = !show;
        if (show) visible++;
      });

      sections.forEach(section => {
        const visibleCards = section.querySelectorAll('.entry-card:not([hidden])');
        section.hidden = visibleCards.length === 0;
      });

      countSpan.textContent = hasFilter
        ? `${visible} result${visible !== 1 ? 's' : ''}`
        : `${visible} entr${visible !== 1 ? 'ies' : 'y'}`;
      emptyMessage.hidden = visible !== 0;

      renderChips(chips, f, key => {
        setFilterValue(key, '');
        applyFilters();
      });
      updateUrl(f);
    }

    if (searchInput) searchInput.addEventListener('input', applyFilters);
    [typeSelect, domainSelect, collabTypeSelect, scaleSelect, modalitySelect].forEach(el => {
      if (el) el.addEventListener('change', applyFilters);
    });

    resetBtn.addEventListener('click', () => {
      if (searchInput) searchInput.value = '';
      if (typeSelect) typeSelect.value = '';
      if (domainSelect) domainSelect.value = '';
      if (collabTypeSelect) collabTypeSelect.value = '';
      if (scaleSelect) scaleSelect.value = '';
      if (modalitySelect) modalitySelect.value = '';
      applyFilters();
    });

    // Pre-select filters from URL query parameters
    const params = new URLSearchParams(window.location.search);

    function preselectFilter(selectEl, paramName) {
      const val = params.get(paramName);
      if (!val || !selectEl) return false;
      for (let i = 0; i < selectEl.options.length; i++) {
        if (selectEl.options[i].value === val) {
          selectEl.value = selectEl.options[i].value;
          return true;
        }
      }
      return false;
    }

    let hasUrlFilter = false;
    if (searchInput && params.get('search')) {
      searchInput.value = params.get('search');
      hasUrlFilter = true;
    }
    hasUrlFilter = preselectFilter(domainSelect, 'domain') || hasUrlFilter;
    hasUrlFilter = preselectFilter(collabTypeSelect, 'collaboration_type') || hasUrlFilter;
    hasUrlFilter = preselectFilter(scaleSelect, 'scale') || hasUrlFilter;
    hasUrlFilter = preselectFilter(modalitySelect, 'modality') || hasUrlFilter;
    hasUrlFilter = preselectFilter(typeSelect, 'type') || hasUrlFilter;

    applyFilters();
  }

  function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1).replace(/-/g, ' ');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
