/* CollabAtlas — Find Your Method Wizard */

(function () {
  'use strict';

  function readWizardData() {
    var dataElement = document.getElementById('wizard-data');
    if (!dataElement) {
      return { catalogue: [], questions: [] };
    }

    try {
      var payload = JSON.parse(dataElement.textContent);
      if (typeof payload === 'string') {
        payload = JSON.parse(payload);
      }

      return payload;
    } catch (error) {
      console.error('Unable to parse wizard data.', error);
      return { catalogue: [], questions: [] };
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

  var wizardData = readWizardData();
  var CATALOGUE = Array.isArray(wizardData.catalogue) ? wizardData.catalogue : [];
  var QUESTIONS = Array.isArray(wizardData.questions) ? wizardData.questions : [];
  var QUESTION_INDEX = QUESTIONS.reduce(function (acc, question) {
    acc[question.id] = question;
    return acc;
  }, {});

  var currentStep = 0;
  var answers = {};

  function getQuestionById(questionId) {
    return QUESTION_INDEX[questionId] || null;
  }

  function getAnswerOption(question, answerId) {
    if (!question || !Array.isArray(question.options)) {
      return null;
    }

    return question.options.find(function (option) {
      return option.id === answerId;
    }) || null;
  }

  function buildAnswerSummary() {
    return QUESTIONS.map(function (question) {
      var answerId = answers[question.id];
      var option = getAnswerOption(question, answerId);
      if (!option) {
        return null;
      }

      return {
        question: question.question,
        label: option.label,
        id: question.id,
        value: option.id
      };
    }).filter(Boolean);
  }

  function getSelectedTags() {
    var tags = [];

    QUESTIONS.forEach(function (question) {
      var option = getAnswerOption(question, answers[question.id]);
      if (!option || !Array.isArray(option.tags)) {
        return;
      }

      option.tags.forEach(function (tag) {
        if (tags.indexOf(tag) === -1) {
          tags.push(tag);
        }
      });
    });

    return tags;
  }

  function getQuestionWeight(question) {
    var weight = Number(question && question.weight);
    return Number.isFinite(weight) && weight > 0 ? weight : 1;
  }

  function getEntryFieldValues(entry, fieldName) {
    if (!entry || !fieldName) {
      return [];
    }

    if (fieldName === 'type') {
      return entry.type ? [entry.type] : [];
    }

    var value = entry[fieldName];
    if (Array.isArray(value)) {
      return value;
    }

    return value ? [value] : [];
  }

  function buildReasonLabel(questionId, matchedTags) {
    var tags = matchedTags.slice(0, 3).join(', ');

    if (questionId === 'goal') {
      return 'Supports your goal through: ' + tags;
    }

    if (questionId === 'domain') {
      return 'Relevant to your domain: ' + tags;
    }

    if (questionId === 'modality') {
      return 'Works for your collaboration mode: ' + tags;
    }

    if (questionId === 'scale') {
      return 'Fits your collaboration scale: ' + tags;
    }

    return 'Matches your context on: ' + tags;
  }

  function scoreEntry(entry) {
    var totalWeight = 0;
    var score = 0;
    var matchedTags = [];
    var reasons = [];

    QUESTIONS.forEach(function (question) {
      var option = getAnswerOption(question, answers[question.id]);
      if (!option) {
        return;
      }

      var weight = getQuestionWeight(question);
      var entryValues = getEntryFieldValues(entry, question.match_field || 'tags');
      var localMatches = (option.tags || []).filter(function (tag) {
        return entryValues.indexOf(tag) !== -1;
      });

      totalWeight += weight;

      if (!localMatches.length) {
        return;
      }

      var localCoverage = localMatches.length / Math.max((option.tags || []).length, 1);
      score += weight * localCoverage;

      localMatches.forEach(function (tag) {
        if (matchedTags.indexOf(tag) === -1) {
          matchedTags.push(tag);
        }
      });

      reasons.push(buildReasonLabel(question.id, localMatches));
    });

    return {
      entry: entry,
      score: score,
      matchedTags: matchedTags,
      reasons: reasons,
      coverage: totalWeight ? Math.round((score / totalWeight) * 100) : 0
    };
  }

  function getShareUrl() {
    var url = new URL(window.location.href);

    QUESTIONS.forEach(function (question) {
      var value = answers[question.id];
      var paramName = 'wizard_' + question.id;
      if (value) {
        url.searchParams.set(paramName, value);
      } else {
        url.searchParams.delete(paramName);
      }
    });

    return url;
  }

  function syncUrl() {
    var nextUrl = getShareUrl();
    window.history.replaceState({}, '', nextUrl.toString());
  }

  function loadAnswersFromUrl() {
    var url = new URL(window.location.href);
    var restored = {};

    QUESTIONS.forEach(function (question) {
      var value = url.searchParams.get('wizard_' + question.id);
      var option = getAnswerOption(question, value);
      if (option) {
        restored[question.id] = option.id;
      }
    });

    return restored;
  }

  function findNextIncompleteStep() {
    for (var index = 0; index < QUESTIONS.length; index++) {
      if (!answers[QUESTIONS[index].id]) {
        return index;
      }
    }

    return QUESTIONS.length - 1;
  }

  function renderSelectedContext() {
    var summaryList = document.getElementById('wizard-selected-context');
    if (!summaryList) {
      return;
    }

    var selections = buildAnswerSummary();
    if (!selections.length) {
      summaryList.innerHTML = '';
      return;
    }

    summaryList.innerHTML = selections.map(function (selection) {
      return '<li><strong>' + escapeHtml(selection.question) + ':</strong> ' + escapeHtml(selection.label) + '</li>';
    }).join('');
  }

  function showShareFeedback(message) {
    var feedback = document.getElementById('wizard-share-feedback');
    if (!feedback) {
      return;
    }

    feedback.textContent = message;
  }

  function copyShareLink() {
    var shareUrl = getShareUrl().toString();

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(shareUrl)
        .then(function () {
          showShareFeedback('Shareable link copied.');
        })
        .catch(function () {
          showShareFeedback('Unable to copy automatically. You can copy the URL from the address bar.');
        });
      return;
    }

    showShareFeedback('Clipboard access is unavailable. You can copy the URL from the address bar.');
  }

  function wizardStart() {
    if (!QUESTIONS.length || !CATALOGUE.length) {
      document.getElementById('wizard-intro').innerHTML =
        '<h2>Find Your Collaborative Method</h2>' +
        '<p>The wizard data is currently unavailable. Please browse the catalogue directly for now.</p>' +
        '<a class="btn btn-secondary" href="/catalogue/">Browse the Catalogue</a>';
      return;
    }

    document.getElementById('wizard-intro').hidden = true;
    document.getElementById('wizard-questions').hidden = false;
    document.getElementById('wizard-results').hidden = true;
    currentStep = 0;
    answers = {};
    syncUrl();
    renderQuestion();
  }

  function wizardResume() {
    if (!QUESTIONS.length || !CATALOGUE.length) {
      return;
    }

    document.getElementById('wizard-intro').hidden = true;
    document.getElementById('wizard-results').hidden = true;
    document.getElementById('wizard-questions').hidden = false;
    currentStep = findNextIncompleteStep();
    renderQuestion();
  }

  function wizardEditAnswers() {
    if (!QUESTIONS.length || !CATALOGUE.length) {
      return;
    }

    document.getElementById('wizard-intro').hidden = true;
    document.getElementById('wizard-results').hidden = true;
    document.getElementById('wizard-questions').hidden = false;
    currentStep = 0;
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

    area.innerHTML = '<h2 class="wizard-question">' + escapeHtml(q.question) + '</h2>' +
      '<div class="wizard-options" role="radiogroup" aria-label="' + escapeHtml(q.question) + '">' +
      q.options.map(function (opt) {
        var checked = answers[q.id] === opt.id;
        return '<label class="wizard-option' + (checked ? ' selected' : '') + '">' +
          '<input type="radio" name="wizard-q" value="' + opt.id + '"' + (checked ? ' checked' : '') + '>' +
          '<span>' + escapeHtml(opt.label) + '</span>' +
          '</label>';
      }).join('') +
      '</div>';

    area.querySelectorAll('input[type="radio"]').forEach(function (radio) {
      radio.addEventListener('change', function () {
        answers[q.id] = this.value;
        syncUrl();
        area.querySelectorAll('.wizard-option').forEach(function (el) {
          el.classList.remove('selected');
        });
        this.closest('.wizard-option').classList.add('selected');
        nextBtn.disabled = false;
      });
    });

    backBtn.hidden = currentStep === 0;
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
    document.getElementById('wizard-questions').hidden = true;
    document.getElementById('wizard-results').hidden = false;
    syncUrl();

    var answerSummary = buildAnswerSummary();
    var scored = CATALOGUE.map(scoreEntry);

    scored.sort(function (a, b) {
      if (b.score !== a.score) {
        return b.score - a.score;
      }

      return (a.entry.title || '').localeCompare(b.entry.title || '');
    });
    var top = scored.filter(function (s) { return s.score > 0; }).slice(0, 6);

    var summary = document.getElementById('wizard-results-summary');
    var list = document.getElementById('wizard-results-list');
    var hint = document.getElementById('wizard-results-hint');

    if (top.length === 0) {
      summary.textContent = 'No specific matches found. Browse the full catalogue to explore all entries.';
      if (hint) {
        hint.textContent = '';
      }
      list.innerHTML = '';
      renderSelectedContext();
      return;
    }

    summary.textContent = 'Based on your answers, here are the most relevant approaches from the current catalogue:';
    if (hint) {
      hint.textContent = answerSummary.length
        ? 'The ranking weighs your goal, domain, modality, and scale, then explains why each entry fits your context.'
        : '';
    }
    renderSelectedContext();
    list.innerHTML = top.map(function (s) {
      var matchedSummary = s.matchedTags.length
        ? '<p class="tagline">Matched on: ' + escapeHtml(s.matchedTags.slice(0, 4).join(', ')) + '</p>'
        : '';
      var whyThisResult = s.reasons.length
        ? '<div class="wizard-why"><p class="wizard-why-title">Why this result</p><ul class="wizard-why-list">' + s.reasons.slice(0, 4).map(function (reason) {
          return '<li>' + escapeHtml(reason) + '</li>';
        }).join('') + '</ul></div>'
        : '';
      var entryType = s.entry.type ? '<span class="badge ' + escapeHtml(s.entry.type) + '">' + escapeHtml(s.entry.type) + '</span>' : '';
      var maturity = s.entry.maturity ? '<span class="badge maturity-' + escapeHtml(s.entry.maturity) + '">' + escapeHtml(s.entry.maturity) + '</span>' : '';
      var tagline = s.entry.tagline ? '<p class="tagline">' + escapeHtml(s.entry.tagline) + '</p>' : '';
      var scoreBadge = '<span class="badge wizard-match-score">' + escapeHtml(String(s.coverage)) + '% match</span>';

      return '<article class="entry-card">' +
        '<h3><a href="' + escapeHtml(s.entry.url) + '">' + escapeHtml(s.entry.title) + '</a></h3>' +
        tagline +
        matchedSummary +
        whyThisResult +
        '<div class="card-meta">' +
        scoreBadge +
        entryType +
        maturity +
        '</div>' +
        '</article>';
    }).join('');
  }

  function wizardReset() {
    document.getElementById('wizard-results').hidden = true;
    document.getElementById('wizard-questions').hidden = true;
    document.getElementById('wizard-intro').hidden = false;
    currentStep = 0;
    answers = {};
    syncUrl();
    renderSelectedContext();
    showShareFeedback('');
  }

  function initializeWizardState() {
    answers = loadAnswersFromUrl();

    if (!Object.keys(answers).length) {
      return;
    }

    if (Object.keys(answers).length === QUESTIONS.length) {
      document.getElementById('wizard-intro').hidden = true;
      showResults();
      return;
    }

    wizardResume();
  }

  // Expose to global scope for onclick handlers in the template
  window.wizardStart = wizardStart;
  window.wizardNext = wizardNext;
  window.wizardBack = wizardBack;
  window.wizardReset = wizardReset;
  window.wizardEditAnswers = wizardEditAnswers;
  window.copyWizardShareLink = copyShareLink;

  initializeWizardState();
})();
