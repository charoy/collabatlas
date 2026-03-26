/**
 * CollabAtlas — Force-directed graph visualization using D3.js
 *
 * Builds a graph from catalogue entries where:
 * - Nodes = catalogue entries (colored by type)
 * - Explicit links = related_entries (thick solid lines)
 * - Taxonomy links = shared taxonomy values (thin dashed lines)
 */

(function () {
  'use strict';

  /* ------------------------------------------------------------------ */
  /* Constants                                                           */
  /* ------------------------------------------------------------------ */

  const TYPE_COLORS = {
    tools: '#4a90d9',
    methods: '#2da44e',
    frameworks: '#8957e5',
    'case-studies': '#d97706',
    datasets: '#0ea5e9',
    resources: '#e5534b',
  };

  // Singular forms used in YAML "type" field → plural section key
  const TYPE_TO_SECTION = {
    tool: 'tools',
    method: 'methods',
    framework: 'frameworks',
    'case-study': 'case-studies',
    dataset: 'datasets',
    resource: 'resources',
  };

  const TAXONOMY_LINK_THRESHOLD = 2; // min shared taxonomy values to create a link
  const D3_CDN = 'https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js';

  /* ------------------------------------------------------------------ */
  /* Tab switching                                                       */
  /* ------------------------------------------------------------------ */

  document.querySelectorAll('.visualize-tab').forEach(function (tab) {
    tab.addEventListener('click', function () {
      document.querySelectorAll('.visualize-tab').forEach(function (t) {
        t.classList.remove('active');
        t.setAttribute('aria-selected', 'false');
      });
      document.querySelectorAll('.visualize-tab-panel').forEach(function (p) {
        p.classList.remove('active');
        p.hidden = true;
      });
      tab.classList.add('active');
      tab.setAttribute('aria-selected', 'true');
      var panel = document.getElementById('tab-' + tab.dataset.tab);
      if (panel) {
        panel.classList.add('active');
        panel.hidden = false;
      }
    });
  });

  /* ------------------------------------------------------------------ */
  /* Load D3.js dynamically                                              */
  /* ------------------------------------------------------------------ */

  function loadD3(callback) {
    if (window.d3) return callback();
    var script = document.createElement('script');
    script.src = D3_CDN;
    script.onload = callback;
    document.head.appendChild(script);
  }

  /* ------------------------------------------------------------------ */
  /* Build graph data (nodes + links) from catalogue entries             */
  /* ------------------------------------------------------------------ */

  function buildGraph(entries) {
    var nodeMap = {};
    var nodes = [];
    var links = [];

    // Build nodes
    entries.forEach(function (entry) {
      var section = TYPE_TO_SECTION[entry.type] || entry.type;
      var node = {
        id: entry.id,
        title: entry.title,
        type: section,
        tagline: entry.tagline || '',
        permalink: entry.permalink,
        domains: entry.domains || [],
        collaborationTypes: entry.collaborationTypes || [],
        scales: entry.scales || [],
        modalities: entry.modalities || [],
        relatedEntries: entry.relatedEntries || [],
        tags: entry.tags || [],
        linkCount: 0,
      };
      nodeMap[entry.id] = node;
      nodes.push(node);
    });

    var linkSet = new Set();

    // Explicit links (related_entries)
    nodes.forEach(function (node) {
      (node.relatedEntries || []).forEach(function (relId) {
        if (!nodeMap[relId]) return;
        var key = [node.id, relId].sort().join('--');
        if (linkSet.has(key)) return;
        linkSet.add(key);
        links.push({
          source: node.id,
          target: relId,
          type: 'explicit',
          strength: 1,
        });
        node.linkCount++;
        nodeMap[relId].linkCount++;
      });
    });

    // Taxonomy links (shared values)
    for (var i = 0; i < nodes.length; i++) {
      for (var j = i + 1; j < nodes.length; j++) {
        var a = nodes[i];
        var b = nodes[j];
        var key = [a.id, b.id].sort().join('--');
        if (linkSet.has(key)) continue;

        var shared = 0;
        shared += countShared(a.domains, b.domains);
        shared += countShared(a.collaborationTypes, b.collaborationTypes);
        shared += countShared(a.scales, b.scales);
        shared += countShared(a.modalities, b.modalities);

        if (shared >= TAXONOMY_LINK_THRESHOLD) {
          linkSet.add(key);
          links.push({
            source: a.id,
            target: b.id,
            type: 'taxonomy',
            strength: Math.min(shared / 6, 1),
          });
          a.linkCount++;
          b.linkCount++;
        }
      }
    }

    return { nodes: nodes, links: links };
  }

  function countShared(a, b) {
    if (!a || !b) return 0;
    var setB = new Set(b);
    var count = 0;
    a.forEach(function (v) { if (setB.has(v)) count++; });
    return count;
  }

  /* ------------------------------------------------------------------ */
  /* State                                                               */
  /* ------------------------------------------------------------------ */

  var allData = null;     // raw catalogue entries
  var taxonomies = null;  // taxonomy lists
  var simulation = null;
  var svg = null;
  var activeTypes = new Set(Object.keys(TYPE_COLORS));
  var activeFilters = { domain: '', collab: '', scale: '', modality: '' };

  /* ------------------------------------------------------------------ */
  /* Filtering                                                           */
  /* ------------------------------------------------------------------ */

  function getFilteredEntries() {
    return allData.filter(function (e) {
      var section = TYPE_TO_SECTION[e.type] || e.type;
      if (!activeTypes.has(section)) return false;
      if (activeFilters.domain && (e.domains || []).indexOf(activeFilters.domain) === -1) return false;
      if (activeFilters.collab && (e.collaborationTypes || []).indexOf(activeFilters.collab) === -1) return false;
      if (activeFilters.scale && (e.scales || []).indexOf(activeFilters.scale) === -1) return false;
      if (activeFilters.modality && (e.modalities || []).indexOf(activeFilters.modality) === -1) return false;
      return true;
    });
  }

  /* ------------------------------------------------------------------ */
  /* Render graph                                                        */
  /* ------------------------------------------------------------------ */

  function renderGraph() {
    var container = document.getElementById('graph-container');
    container.innerHTML = '';

    var filtered = getFilteredEntries();
    var graph = buildGraph(filtered);

    // Update stats
    document.getElementById('graph-node-count').textContent = graph.nodes.length;
    document.getElementById('graph-link-count').textContent = graph.links.length;

    if (graph.nodes.length === 0) {
      container.innerHTML = '<p class="visualize-loading">No entries match the current filters.</p>';
      return;
    }

    var width = container.clientWidth || 900;
    var height = Math.max(500, window.innerHeight - 300);

    svg = d3.select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', [0, 0, width, height]);

    // Zoom
    var g = svg.append('g');
    var zoom = d3.zoom()
      .scaleExtent([0.2, 5])
      .on('zoom', function (event) { g.attr('transform', event.transform); });
    svg.call(zoom);

    // Links
    var link = g.append('g')
      .attr('class', 'graph-links')
      .selectAll('line')
      .data(graph.links)
      .join('line')
      .attr('class', function (d) { return 'graph-link graph-link-' + d.type; })
      .attr('stroke-width', function (d) { return d.type === 'explicit' ? 2 : 0.5; })
      .attr('stroke', function (d) { return d.type === 'explicit' ? '#666' : '#ccc'; })
      .attr('stroke-dasharray', function (d) { return d.type === 'taxonomy' ? '3,3' : null; })
      .attr('stroke-opacity', function (d) { return d.type === 'explicit' ? 0.7 : 0.3; });

    // Nodes
    var node = g.append('g')
      .attr('class', 'graph-nodes')
      .selectAll('g')
      .data(graph.nodes)
      .join('g')
      .attr('class', 'graph-node')
      .call(d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended));

    node.append('circle')
      .attr('r', function (d) { return Math.max(5, Math.min(18, 4 + d.linkCount * 0.8)); })
      .attr('fill', function (d) { return TYPE_COLORS[d.type] || '#999'; })
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5);

    node.append('text')
      .text(function (d) { return d.title; })
      .attr('dx', function (d) { return Math.max(5, 4 + d.linkCount * 0.8) + 4; })
      .attr('dy', '0.35em')
      .attr('class', 'graph-label')
      .style('font-size', '11px')
      .style('fill', '#333')
      .style('pointer-events', 'none');

    // Hover highlight
    node.on('mouseover', function (event, d) {
      var neighbors = new Set();
      neighbors.add(d.id);
      graph.links.forEach(function (l) {
        var sid = typeof l.source === 'object' ? l.source.id : l.source;
        var tid = typeof l.target === 'object' ? l.target.id : l.target;
        if (sid === d.id) neighbors.add(tid);
        if (tid === d.id) neighbors.add(sid);
      });

      node.style('opacity', function (n) { return neighbors.has(n.id) ? 1 : 0.15; });
      link.style('opacity', function (l) {
        var sid = typeof l.source === 'object' ? l.source.id : l.source;
        var tid = typeof l.target === 'object' ? l.target.id : l.target;
        return (sid === d.id || tid === d.id) ? 1 : 0.05;
      });
    });

    node.on('mouseout', function () {
      node.style('opacity', 1);
      link.style('opacity', function (d) { return d.type === 'explicit' ? 0.7 : 0.3; });
    });

    // Click → detail panel
    node.on('click', function (event, d) {
      event.stopPropagation();
      showDetail(d);
    });

    svg.on('click', function () { hideDetail(); });

    // Simulation
    simulation = d3.forceSimulation(graph.nodes)
      .force('link', d3.forceLink(graph.links).id(function (d) { return d.id; }).distance(80).strength(function (d) { return d.type === 'explicit' ? 0.5 : 0.1; }))
      .force('charge', d3.forceManyBody().strength(-120))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(20))
      .on('tick', function () {
        link
          .attr('x1', function (d) { return d.source.x; })
          .attr('y1', function (d) { return d.source.y; })
          .attr('x2', function (d) { return d.target.x; })
          .attr('y2', function (d) { return d.target.y; });
        node.attr('transform', function (d) { return 'translate(' + d.x + ',' + d.y + ')'; });
      });

    function dragstarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }
  }

  /* ------------------------------------------------------------------ */
  /* Detail panel                                                        */
  /* ------------------------------------------------------------------ */

  function showDetail(d) {
    var panel = document.getElementById('graph-detail');
    document.getElementById('graph-detail-title').textContent = d.title;
    document.getElementById('graph-detail-tagline').textContent = d.tagline;
    document.getElementById('graph-detail-link').href = d.permalink;

    var meta = document.getElementById('graph-detail-meta');
    var badges = '';
    badges += '<span class="badge" style="background:' + (TYPE_COLORS[d.type] || '#999') + ';color:#fff">' + d.type + '</span> ';
    (d.domains || []).forEach(function (v) { badges += '<span class="badge domain">' + v + '</span> '; });
    meta.innerHTML = badges;

    panel.hidden = false;
  }

  function hideDetail() {
    document.getElementById('graph-detail').hidden = true;
  }

  document.getElementById('graph-detail-close').addEventListener('click', hideDetail);

  /* ------------------------------------------------------------------ */
  /* Populate filter dropdowns                                           */
  /* ------------------------------------------------------------------ */

  function populateFilters() {
    var domainSel = document.getElementById('graph-filter-domain');
    var collabSel = document.getElementById('graph-filter-collab');
    var scaleSel = document.getElementById('graph-filter-scale');
    var modalitySel = document.getElementById('graph-filter-modality');

    if (taxonomies) {
      fillSelect(domainSel, taxonomies.domains, 'All domains');
      fillSelect(collabSel, taxonomies.collaborationTypes, 'All collaboration types');
      fillSelect(scaleSel, taxonomies.scales, 'All scales');
      fillSelect(modalitySel, taxonomies.modalities, 'All modalities');
    }
  }

  function fillSelect(sel, items, defaultLabel) {
    sel.innerHTML = '<option value="">' + defaultLabel + '</option>';
    if (!items) return;
    // items can be array of strings or array of objects with id/title
    items.forEach(function (item) {
      var val = typeof item === 'string' ? item : (item.id || item);
      var label = typeof item === 'string' ? item : (item.title || item.id || item);
      var opt = document.createElement('option');
      opt.value = val;
      opt.textContent = label;
      sel.appendChild(opt);
    });
  }

  /* ------------------------------------------------------------------ */
  /* Event listeners                                                     */
  /* ------------------------------------------------------------------ */

  function setupListeners() {
    // Type toggles
    document.querySelectorAll('.type-toggle').forEach(function (btn) {
      // Set initial color
      btn.style.setProperty('--toggle-color', TYPE_COLORS[btn.dataset.type] || '#999');
      btn.addEventListener('click', function () {
        btn.classList.toggle('active');
        var t = btn.dataset.type;
        if (activeTypes.has(t)) activeTypes.delete(t);
        else activeTypes.add(t);
        renderGraph();
      });
    });

    // Filter dropdowns
    document.getElementById('graph-filter-domain').addEventListener('change', function (e) {
      activeFilters.domain = e.target.value;
      renderGraph();
    });
    document.getElementById('graph-filter-collab').addEventListener('change', function (e) {
      activeFilters.collab = e.target.value;
      renderGraph();
    });
    document.getElementById('graph-filter-scale').addEventListener('change', function (e) {
      activeFilters.scale = e.target.value;
      renderGraph();
    });
    document.getElementById('graph-filter-modality').addEventListener('change', function (e) {
      activeFilters.modality = e.target.value;
      renderGraph();
    });
  }

  /* ------------------------------------------------------------------ */
  /* Init                                                                */
  /* ------------------------------------------------------------------ */

  function init() {
    var url = window.CATALOGUE_DATA_URL;
    if (!url) return;

    fetch(url)
      .then(function (r) { return r.json(); })
      .then(function (data) {
        allData = data.entries || [];
        taxonomies = data.taxonomies || {};
        populateFilters();
        setupListeners();
        loadD3(renderGraph);
      })
      .catch(function (err) {
        console.error('Failed to load graph data:', err);
        document.getElementById('graph-container').innerHTML =
          '<p class="visualize-loading">Failed to load data.</p>';
      });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
