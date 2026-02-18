/* CollabAtlas — Catalogue client-side filtering */

(function () {
  'use strict';

  function init() {
    const filterBar = document.querySelector('.filters');
    if (!filterBar) return;

    const cards = Array.from(document.querySelectorAll('.entry-card'));
    if (!cards.length) return;

    // Collect unique values from cards
    const domains = new Set();
    const types = new Set();
    const modalities = new Set();
    const scales = new Set();

    cards.forEach(card => {
      const type = card.dataset.type;
      if (type) types.add(type);

      card.querySelectorAll('.badge.domain').forEach(b => domains.add(b.textContent.trim()));
      card.querySelectorAll('.badge.modality').forEach(b => modalities.add(b.textContent.trim()));
      card.querySelectorAll('.badge.scale').forEach(b => scales.add(b.textContent.trim()));
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
      ${modalities.size ? `
      <label class="filter-label">
        <span>Modality</span>
        <select id="filter-modality" aria-label="Filter by modality">
          <option value="">All modalities</option>
          ${[...modalities].sort().map(m => `<option value="${m}">${capitalize(m)}</option>`).join('')}
        </select>
      </label>` : ''}
      <button id="filter-reset" class="btn btn-secondary filter-reset" style="display:none">Clear filters</button>
      <span id="filter-count" class="filter-count" aria-live="polite"></span>
    `;

    const searchInput = document.getElementById('filter-search');
    const typeSelect = document.getElementById('filter-type');
    const domainSelect = document.getElementById('filter-domain');
    const modalitySelect = document.getElementById('filter-modality');
    const resetBtn = document.getElementById('filter-reset');
    const countSpan = document.getElementById('filter-count');

    function getFilters() {
      return {
        search: searchInput ? searchInput.value.trim().toLowerCase() : '',
        type: typeSelect ? typeSelect.value : '',
        domain: domainSelect ? domainSelect.value : '',
        modality: modalitySelect ? modalitySelect.value : '',
      };
    }

    function applyFilters() {
      const f = getFilters();
      const hasFilter = f.search || f.type || f.domain || f.modality;
      resetBtn.style.display = hasFilter ? '' : 'none';

      let visible = 0;
      cards.forEach(card => {
        let show = true;

        if (f.search) {
          const text = card.textContent.toLowerCase();
          if (!text.includes(f.search)) show = false;
        }
        if (f.type && card.dataset.type !== f.type) show = false;
        if (f.domain) {
          const cardDomains = [...card.querySelectorAll('.badge.domain')].map(b => b.textContent.trim());
          if (!cardDomains.includes(f.domain)) show = false;
        }
        if (f.modality) {
          const cardModalities = [...card.querySelectorAll('.badge.modality')].map(b => b.textContent.trim());
          if (!cardModalities.includes(f.modality)) show = false;
        }

        card.style.display = show ? '' : 'none';
        if (show) visible++;
      });

      // Show/hide empty-section messages
      document.querySelectorAll('.type-section').forEach(section => {
        const visibleCards = section.querySelectorAll('.entry-card:not([style*="display: none"])');
        section.style.display = visibleCards.length === 0 ? 'none' : '';
      });

      countSpan.textContent = hasFilter ? `${visible} result${visible !== 1 ? 's' : ''}` : '';
    }

    [searchInput, typeSelect, domainSelect, modalitySelect].forEach(el => {
      if (el) el.addEventListener('input', applyFilters);
    });

    resetBtn.addEventListener('click', () => {
      if (searchInput) searchInput.value = '';
      if (typeSelect) typeSelect.value = '';
      if (domainSelect) domainSelect.value = '';
      if (modalitySelect) modalitySelect.value = '';
      applyFilters();
    });
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
