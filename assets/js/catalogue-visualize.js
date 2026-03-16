// catalogue-visualize.js

(function () {
  'use strict';

  // State to hold current view data for interaction
  let currentMatrix = {};
  let currentXItems = [];
  let currentYItems = [];
  let data = null; // Global data reference

  function init() {
    console.log('Catalogue Visualize Init');
    data = window.CATALOGUE_DATA;
    
    const chart = document.getElementById('visualize-chart');
    if (!data) {
      console.error('No catalogue data found');
      if (chart) chart.innerHTML = '<p class="error">Data error: window.CATALOGUE_DATA is missing.</p>';
      return;
    }

    if (!chart) {
      console.error('Chart container not found');
      return;
    }

    const xSelect = document.getElementById('x-axis-select');
    const ySelect = document.getElementById('y-axis-select');
    
    // Modal Elements
    const modal = document.getElementById('visualize-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalList = document.getElementById('modal-list'); // Use .visualize-modal-content if list not there
    const modalClose = document.getElementById('modal-close');

    if (!xSelect || !ySelect) {
      console.error('Controls not found');
      return;
    }

    // --- Interaction Handlers ---

    // Modal Close
    if (modal) {
        if (modalClose) {
            modalClose.addEventListener('click', () => modal.close());
        }
        modal.addEventListener('click', (event) => {
            if (event.target === modal) {
            modal.close();
            }
        });
    }

    // Chart Click (Delegation)
    chart.addEventListener('click', (e) => {
      const td = e.target.closest('td');
      if (!td) return;
      
      const count = parseInt(td.dataset.count, 10);
      if (!count || count === 0) return;

      const xId = td.dataset.xId;
      const yId = td.dataset.yId;

      if (xId && yId && currentMatrix[yId] && currentMatrix[yId][xId]) {
        const entries = currentMatrix[yId][xId];
        openModal(xId, yId, entries);
      }
    });

    function openModal(xId, yId, entries) {
      if (!modal) return;
      
      // Find labels
      const xObj = currentXItems.find(i => i.id === xId);
      const yObj = currentYItems.find(i => i.id === yId);
      const xLabel = xObj ? xObj.label : xId;
      const yLabel = yObj ? yObj.label : yId;

      if (modalTitle) modalTitle.textContent = `${yLabel} ∩ ${xLabel} (${entries.length})`;
      
      const contentContainer = document.querySelector('.visualize-modal-content');
      if (contentContainer) {
          contentContainer.innerHTML = `<ul class="modal-entry-list">` + entries.map(entry => `
            <li class="modal-entry-item">
            <a href="${entry.permalink}" class="modal-entry-title" target="_blank">${entry.title}</a>
            ${entry.description ? `<p class="modal-entry-tagline">${entry.description}</p>` : ''}
            </li>
        `).join('') + `</ul>`;
      }
      
      modal.showModal();
    }


    // --- Data Helpers ---

    function getItemsForAxis(axisKey) {
      // Key normalization for taxonomy map
      // Hugo keys might be different? safeJS output keys are what we see in template.
      // domains, collaborationTypes, modalities, scales, researchMethods, maturity
      const items = data.taxonomies[axisKey];
      if (Array.isArray(items)) {
        return items;
      }
      return [];
    }
    
    function getEntryValues(entry, axisKey) {
       // Only return values that are actually ID strings or objects with IDs?
       // The previous code assumed params were array of something that matched taxonomy IDs.
       const val = entry[axisKey];
       if (val === undefined || val === null) return [];
       
       let values = Array.isArray(val) ? val : [val];
       // Filter out empty strings
       return values.filter(v => v !== "");
    }

    // --- Render Logic ---

    function renderMatrix() {
      const xKey = xSelect.value;
      const yKey = ySelect.value;
      
      currentXItems = getItemsForAxis(xKey);
      currentYItems = getItemsForAxis(yKey);

      if (currentXItems.length === 0 || currentYItems.length === 0) {
        chart.innerHTML = '<p class="visualize-empty">No taxonomy data available for selected axes.</p>';
        return;
      }

      // Initialize matrix structure: matrix[yId][xId] = []
      const matrix = {};
      currentYItems.forEach(y => {
        matrix[y.id] = {};
        currentXItems.forEach(x => {
          matrix[y.id][x.id] = [];
        });
      });

      // Fill matrix
      // Iterate entries and place them in appropriate cells
      // Note: O(N * M * K) complexity roughly
      
      // Helper: Map entry value to taxonomy ID?
      // Usually Hugo frontmatter values are the IDs (or titles that match IDs?).
      // Assuming exact match for now.
      
      const xMap = new Set(currentXItems.map(i => i.id));
      const yMap = new Set(currentYItems.map(i => i.id));

      data.entries.forEach(entry => {
        const xValues = getEntryValues(entry, xKey);
        const yValues = getEntryValues(entry, yKey);

        xValues.forEach(xv => {
          if (!xMap.has(xv)) return; // Skip if value not in current taxonomy axis
          
          yValues.forEach(yv => {
            if (!yMap.has(yv)) return; // Skip if value not in current taxonomy axis
            
            if (matrix[yv] && matrix[yv][xv]) {
              matrix[yv][xv].push(entry);
            }
          });
        });
      });
      
      currentMatrix = matrix;

      // Build HTML
      let html = '<div class="table-responsive"><table class="visual-matrix"><thead><tr><th></th>';
      
      // Header
      currentXItems.forEach(x => {
        html += `<th scope="col" title="${x.label}">${x.label}</th>`;
      });
      html += '</tr></thead><tbody>';

      // Rows
      currentYItems.forEach(y => {
        html += `<tr><th scope="row" title="${y.label}">${y.label}</th>`;
        currentXItems.forEach(x => {
          const matchedEntries = matrix[y.id][x.id] || [];
          const count = matchedEntries.length;
          
          let styleAttr = '';
          let classList = 'matrix-cell';
          let title = '0 entries';
          
          if (count > 0) {
            // Calculate opacity: base 0.2, max at 1.0 (for ~8 entries)
            const opacity = Math.min(0.2 + (count / 8) * 0.8, 1).toFixed(2);
            styleAttr = `style="background-color: rgba(0, 123, 255, ${opacity}); cursor: pointer;"`; 
            classList += ' cell-filled interactive-cell';
            
            // Tooltip preview
            const names = matchedEntries.slice(0, 5).map(e => `• ${e.title}`).join('\n');
            title = `${count} entries:\n${names}${count > 5 ? '\n...' : ''}`;
          } else {
            classList += ' cell-empty';
          }
          
          html += `<td class="${classList}" ${styleAttr} 
                      title="${title}" 
                      data-x-id="${x.id}" 
                      data-y-id="${y.id}" 
                      data-count="${count}"
                      tabindex="${count > 0 ? 0 : -1}">
                      ${count > 0 ? count : ''}
                   </td>`;
        });
        html += '</tr>';
      });
      html += '</tbody></table></div>';

      chart.innerHTML = html;

      // Update distributions
      renderDistributions(xKey, 'x-distribution', 'x-dist-title');
      renderDistributions(yKey, 'y-distribution', 'y-dist-title');
    }

    function renderDistributions(axisKey, containerId, titleId) {
      const container = document.getElementById(containerId);
      const titleEl = document.getElementById(titleId);
      if (!container) return;

      const items = getItemsForAxis(axisKey);
      if (!items.length) {
        container.innerHTML = '<p>No data available.</p>';
        return;
      }
      
      // Update title with label
      const select = axisKey === xSelect.value ? xSelect : ySelect;
      if (titleEl && select) {
        titleEl.textContent = `Distribution by ${select.options[select.selectedIndex].text}`;
      }

      // Count occurrences
      const counts = {};
      let maxCount = 0;
      
      // Initialize counts
      items.forEach(item => { counts[item.id] = 0; });

      data.entries.forEach(entry => {
        const values = getEntryValues(entry, axisKey);
        values.forEach(val => {
          if (counts[val] !== undefined) {
            counts[val]++;
          }
        });
      });

      // Find max for scaling
      Object.values(counts).forEach(c => {
        if (c > maxCount) maxCount = c;
      });

      // Sort items by count desc
      const sortedItems = [...items].sort((a, b) => counts[b.id] - counts[a.id]);

      // Render bars
      container.innerHTML = sortedItems.map(item => {
        const count = counts[item.id];
        const percentage = maxCount > 0 ? (count / maxCount) * 100 : 0;
        // Don't hide 0 counts, showing them can be informative (gaps)
        // Adjust opacity if 0?
        const barStyle = `width: ${percentage}%; opacity: ${count > 0 ? 1 : 0.3};`;
        
        return `
          <div class="chart-row">
            <span class="chart-label" title="${item.label}">${item.label}</span>
            <div class="chart-bar-group">
              <div class="chart-bar" style="${barStyle}"></div>
              <span class="chart-value">${count}</span>
            </div>
          </div>
        `;
      }).join('');
    }

    xSelect.addEventListener('change', renderMatrix);
    ySelect.addEventListener('change', renderMatrix);
    
    try {
      renderMatrix();
    } catch (e) {
      console.error('Error rendering matrix:', e);
      chart.innerHTML = `<p class="error">Error rendering visualization: ${e.message}</p>`;
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
