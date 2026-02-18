---
title: "Find Your Method"
description: "An interactive decision wizard to help you choose the right collaborative approach for your context."
---

<div id="wizard" class="wizard">
  <div id="wizard-intro" class="wizard-step active">
    <h2>Find Your Collaborative Method</h2>
    <p>Answer a few questions about your context and goals, and we'll suggest the most relevant collaborative approaches from the CollabAtlas catalogue.</p>
    <button class="btn btn-primary" onclick="wizardStart()">Get Started</button>
  </div>

  <div id="wizard-questions" class="wizard-step" style="display:none">
    <div id="wizard-progress" class="wizard-progress"></div>
    <div id="wizard-question-area"></div>
    <div class="wizard-nav">
      <button class="btn btn-secondary" id="wizard-back" onclick="wizardBack()" style="display:none">← Back</button>
      <button class="btn btn-primary" id="wizard-next" onclick="wizardNext()" disabled>Next →</button>
    </div>
  </div>

  <div id="wizard-results" class="wizard-step" style="display:none">
    <h2>Recommended Approaches</h2>
    <p id="wizard-results-summary"></p>
    <div id="wizard-results-list" class="entry-grid"></div>
    <div style="margin-top:2rem">
      <button class="btn btn-secondary" onclick="wizardReset()">Start Over</button>
      <a href="/catalogue/" class="btn btn-secondary">Browse Full Catalogue</a>
    </div>
  </div>
</div>

<script src="/js/wizard.js"></script>
