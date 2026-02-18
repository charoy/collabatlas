/* CollabAtlas — Find Your Method Wizard */

(function () {
  'use strict';

  // Catalogue entries embedded at build time via Hugo template
  // This file is loaded only on the wizard page; catalogue data is injected
  // via a Hugo shortcode or inline script in the page template.
  // For now, we use a static catalogue snapshot that mirrors the YAML entries.

  var CATALOGUE = [
    {
      id: 'participatory-design',
      title: 'Participatory Design',
      tagline: 'A design approach that actively involves all stakeholders in the design process.',
      url: '/catalogue/methods/participatory-design/',
      type: 'method',
      tags: ['co-design', 'participatory', 'community-based', 'in-person', 'hybrid',
             'small-team', 'organization', 'community', 'design', 'urban-planning',
             'healthcare', 'education', 'software-engineering', 'design-science', 'action-research'],
      maturity: 'well-documented'
    },
    {
      id: 'delphi-method',
      title: 'Delphi Method',
      tagline: 'Structured expert consultation technique using iterative questionnaire rounds.',
      url: '/catalogue/methods/delphi-method/',
      type: 'method',
      tags: ['interdisciplinary', 'distributed', 'remote', 'hybrid',
             'small-team', 'organization', 'multi-org', 'public-policy',
             'healthcare', 'education', 'business', 'survey'],
      maturity: 'well-documented'
    },
    {
      id: 'design-sprint',
      title: 'Design Sprint',
      tagline: 'A five-day process for answering critical questions through design and testing.',
      url: '/catalogue/methods/design-sprint/',
      type: 'method',
      tags: ['co-design', 'co-creation', 'in-person', 'hybrid', 'remote',
             'small-team', 'software-engineering', 'design', 'business',
             'design-science', 'experimental'],
      maturity: 'established'
    },
    {
      id: 'miro',
      title: 'Miro',
      tagline: 'Online collaborative whiteboard platform for visual teamwork.',
      url: '/catalogue/tools/miro/',
      type: 'tool',
      tags: ['co-design', 'co-creation', 'distributed', 'remote', 'hybrid',
             'small-team', 'organization', 'multi-org', 'software-engineering',
             'design', 'education', 'business'],
      maturity: 'well-documented'
    },
    {
      id: 'zotero',
      title: 'Zotero',
      tagline: 'Free, open-source reference manager for collaborative research.',
      url: '/catalogue/tools/zotero/',
      type: 'tool',
      tags: ['interdisciplinary', 'co-production', 'distributed', 'remote', 'hybrid',
             'in-person', 'pair', 'small-team', 'organization', 'education',
             'social-sciences', 'healthcare', 'environmental-science'],
      maturity: 'well-documented'
    },
    {
      id: 'jupyter',
      title: 'Jupyter Notebook',
      tagline: 'Interactive computing environment for collaborative data science.',
      url: '/catalogue/tools/jupyter/',
      type: 'tool',
      tags: ['co-production', 'open-source', 'distributed', 'remote', 'hybrid',
             'in-person', 'pair', 'small-team', 'organization',
             'environmental-science', 'social-sciences', 'education',
             'citizen-science', 'software-engineering'],
      maturity: 'well-documented'
    },
    {
      id: 'slack',
      title: 'Slack',
      tagline: 'Channel-based messaging platform for team communication.',
      url: '/catalogue/tools/slack/',
      type: 'tool',
      tags: ['distributed', 'co-production', 'open-source', 'remote', 'hybrid',
             'small-team', 'organization', 'multi-org', 'software-engineering',
             'business', 'education', 'design'],
      maturity: 'well-documented'
    },
    {
      id: 'activity-theory',
      title: 'Activity Theory',
      tagline: 'Conceptual framework for analyzing socially situated, tool-mediated activities.',
      url: '/catalogue/frameworks/activity-theory/',
      type: 'framework',
      tags: ['co-production', 'interdisciplinary', 'community-based', 'in-person',
             'remote', 'hybrid', 'small-team', 'organization', 'community',
             'education', 'software-engineering', 'social-sciences', 'healthcare',
             'ethnography', 'action-research'],
      maturity: 'well-documented'
    },
    {
      id: 'cscw-framework',
      title: 'CSCW Framework',
      tagline: 'Research field examining how technology supports group work.',
      url: '/catalogue/frameworks/cscw-framework/',
      type: 'framework',
      tags: ['distributed', 'co-production', 'interdisciplinary', 'remote', 'hybrid',
             'in-person', 'pair', 'small-team', 'organization', 'multi-org',
             'software-engineering', 'healthcare', 'education', 'business',
             'ethnography', 'design-science'],
      maturity: 'well-documented'
    },
    {
      id: 'open-innovation',
      title: 'Open Innovation',
      tagline: 'Distributed innovation model using external and internal knowledge flows.',
      url: '/catalogue/frameworks/open-innovation/',
      type: 'framework',
      tags: ['open-source', 'crowdsourcing', 'co-creation', 'interdisciplinary',
             'remote', 'hybrid', 'in-person', 'organization', 'multi-org', 'community',
             'business', 'software-engineering', 'public-policy', 'manufacturing'],
      maturity: 'established'
    }
  ];

  var QUESTIONS = [
    {
      id: 'goal',
      question: 'What is your primary goal?',
      options: [
        { id: 'design-solution', label: 'Design a solution or product',
          tags: ['co-design', 'co-creation', 'design-science'] },
        { id: 'build-consensus', label: 'Build consensus or make a decision',
          tags: ['interdisciplinary', 'transdisciplinary', 'distributed'] },
        { id: 'produce-knowledge', label: 'Produce or synthesize knowledge',
          tags: ['co-production', 'action-research', 'systematic-review'] },
        { id: 'engage-community', label: 'Engage a community or stakeholders',
          tags: ['participatory', 'community-based', 'crowdsourcing'] }
      ]
    },
    {
      id: 'scale',
      question: 'How many people are involved?',
      options: [
        { id: 'pair', label: '2–5 people (pair or small group)', tags: ['pair', 'small-team'] },
        { id: 'team', label: '6–30 people (team or department)', tags: ['small-team', 'organization'] },
        { id: 'org', label: '30–500 people (organization)', tags: ['organization', 'multi-org'] },
        { id: 'community', label: '500+ people (large community)', tags: ['community', 'multi-org'] }
      ]
    },
    {
      id: 'modality',
      question: 'How will people collaborate?',
      options: [
        { id: 'in-person', label: 'In person', tags: ['in-person'] },
        { id: 'remote', label: 'Fully remote', tags: ['remote'] },
        { id: 'hybrid', label: 'Mix of in-person and remote', tags: ['hybrid'] }
      ]
    },
    {
      id: 'domain',
      question: 'Which domain best describes your context?',
      options: [
        { id: 'tech', label: 'Technology / Software', tags: ['software-engineering', 'design'] },
        { id: 'social', label: 'Social sciences / Policy', tags: ['social-sciences', 'public-policy', 'education'] },
        { id: 'health', label: 'Health / Environment', tags: ['healthcare', 'environmental-science'] },
        { id: 'community', label: 'Community / Urban', tags: ['urban-planning', 'citizen-science', 'arts-culture'] }
      ]
    }
  ];

  var currentStep = 0;
  var answers = {};
  var selectedOption = null;

  function wizardStart() {
    document.getElementById('wizard-intro').style.display = 'none';
    document.getElementById('wizard-questions').style.display = '';
    currentStep = 0;
    answers = {};
    renderQuestion();
  }

  function renderQuestion() {
    var q = QUESTIONS[currentStep];
    var progress = document.getElementById('wizard-progress');
    var area = document.getElementById('wizard-question-area');
    var backBtn = document.getElementById('wizard-back');
    var nextBtn = document.getElementById('wizard-next');

    progress.innerHTML = 'Question ' + (currentStep + 1) + ' of ' + QUESTIONS.length;
    progress.setAttribute('aria-label', 'Question ' + (currentStep + 1) + ' of ' + QUESTIONS.length);

    area.innerHTML = '<h2 class="wizard-question">' + q.question + '</h2>' +
      '<div class="wizard-options" role="radiogroup" aria-label="' + q.question + '">' +
      q.options.map(function (opt) {
        var checked = answers[q.id] === opt.id;
        return '<label class="wizard-option' + (checked ? ' selected' : '') + '">' +
          '<input type="radio" name="wizard-q" value="' + opt.id + '"' + (checked ? ' checked' : '') + '>' +
          '<span>' + opt.label + '</span>' +
          '</label>';
      }).join('') +
      '</div>';

    area.querySelectorAll('input[type="radio"]').forEach(function (radio) {
      radio.addEventListener('change', function () {
        answers[q.id] = this.value;
        area.querySelectorAll('.wizard-option').forEach(function (el) {
          el.classList.remove('selected');
        });
        this.closest('.wizard-option').classList.add('selected');
        nextBtn.disabled = false;
      });
    });

    backBtn.style.display = currentStep > 0 ? '' : 'none';
    nextBtn.disabled = !answers[q.id];
    nextBtn.textContent = currentStep < QUESTIONS.length - 1 ? 'Next →' : 'See Results';
  }

  function wizardNext() {
    var q = QUESTIONS[currentStep];
    if (!answers[q.id]) return;

    if (currentStep < QUESTIONS.length - 1) {
      currentStep++;
      renderQuestion();
    } else {
      showResults();
    }
  }

  function wizardBack() {
    if (currentStep > 0) {
      currentStep--;
      renderQuestion();
    }
  }

  function showResults() {
    document.getElementById('wizard-questions').style.display = 'none';
    document.getElementById('wizard-results').style.display = '';

    // Collect all selected tags
    var selectedTags = [];
    QUESTIONS.forEach(function (q) {
      var answerId = answers[q.id];
      if (!answerId) return;
      var opt = q.options.find(function (o) { return o.id === answerId; });
      if (opt) selectedTags = selectedTags.concat(opt.tags);
    });

    // Score each entry
    var scored = CATALOGUE.map(function (entry) {
      var score = 0;
      selectedTags.forEach(function (tag) {
        if (entry.tags.indexOf(tag) !== -1) score++;
      });
      return { entry: entry, score: score };
    });

    scored.sort(function (a, b) { return b.score - a.score; });
    var top = scored.filter(function (s) { return s.score > 0; }).slice(0, 6);

    var summary = document.getElementById('wizard-results-summary');
    var list = document.getElementById('wizard-results-list');

    if (top.length === 0) {
      summary.textContent = 'No specific matches found. Browse the full catalogue to explore all entries.';
      list.innerHTML = '';
      return;
    }

    summary.textContent = 'Based on your answers, here are the most relevant approaches:';
    list.innerHTML = top.map(function (s) {
      return '<article class="entry-card">' +
        '<h3><a href="' + s.entry.url + '">' + s.entry.title + '</a></h3>' +
        '<p class="tagline">' + s.entry.tagline + '</p>' +
        '<div class="card-meta">' +
        '<span class="badge ' + s.entry.type + '">' + s.entry.type + '</span>' +
        '<span class="badge maturity-' + s.entry.maturity + '">' + s.entry.maturity + '</span>' +
        '</div>' +
        '</article>';
    }).join('');
  }

  function wizardReset() {
    document.getElementById('wizard-results').style.display = 'none';
    document.getElementById('wizard-intro').style.display = '';
    currentStep = 0;
    answers = {};
  }

  // Expose to global scope for onclick handlers in the template
  window.wizardStart = wizardStart;
  window.wizardNext = wizardNext;
  window.wizardBack = wizardBack;
  window.wizardReset = wizardReset;
})();
