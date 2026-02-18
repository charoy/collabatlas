---
title: "Mining Open-Source Collaboration Patterns with GH Archive and the CSCW Corpus"
summary: "A methodological walkthrough for combining the GH Archive event dataset with the ACM CSCW proceedings corpus to study how open-source collaboration norms have evolved."
date: 2025-12-03
author: "CollabAtlas Editorial"
category: "Research Spotlight"
related_entries:
  - github-archive
  - cscw-proceedings-corpus
  - linux-kernel-development
  - jupyter
tags:
  - datasets
  - open-source
  - mixed-methods
---

Two of the richest publicly available resources for studying computer-supported cooperative work sit largely unconnected: the **GH Archive** — a continuous record of every public GitHub event since 2011 — and the **ACM CSCW Proceedings Corpus** — three decades of peer-reviewed research on collaborative systems. Combining them opens up compelling mixed-methods research designs.

## The datasets at a glance

The [GH Archive](/catalogue/datasets/github-archive/) captures structured event data: push events, pull request reviews, issue comments, fork actions. At scale it reveals the rhythms of distributed collaboration — who reviews whom, how quickly patches are merged, how contributor networks evolve over time.

The [ACM CSCW Proceedings Corpus](/catalogue/datasets/cscw-proceedings-corpus/) provides the conceptual vocabulary: what researchers have *said* about collaboration, which constructs have gained traction, and how the field's attention has shifted from synchronous groupware to asynchronous platforms.

## A combined research design

### Step 1 — Select a phenomenon
Choose a collaboration pattern visible in both datasets. For example: **code review norms in large open-source projects**. The [Linux Kernel Development](/catalogue/case-studies/linux-kernel-development/) case study is a natural anchor — it is both extensively documented in CSCW literature and richly represented in GH Archive data.

### Step 2 — Quantitative layer (GH Archive)
Use BigQuery to extract pull request review events for a set of target repositories over a defined time window. Key metrics:
- Review turnaround time
- Reviewer diversity (number of unique reviewers per contributor)
- Comment-to-merge ratio

[Jupyter Notebook](/catalogue/tools/jupyter/) is the ideal environment for this analysis — BigQuery integrates via `google-cloud-bigquery`, and the results can be visualised inline with `matplotlib` or `altair`.

### Step 3 — Qualitative layer (CSCW Corpus)
Run a topic model (LDA or BERTopic) over CSCW abstracts filtered to papers about code review or patch submission. Map the evolution of dominant topics across conference years to contextualise the quantitative trends.

### Step 4 — Triangulation
Overlay the quantitative timeline with the qualitative topic shifts. Did changes in review behaviour precede or follow changes in how researchers framed the phenomenon?

## Reproducibility considerations

- Pin your BigQuery SQL queries and export schemas in the notebook
- Archive the CSCW corpus snapshot used (the corpus is updated annually)
- Use `papermill` to parameterise the notebook for different repository sets

## External resources

The GH Archive data is accessible at [gharchive.org](https://www.gharchive.org/) and mirrored on Google BigQuery as `githubarchive.day.*`. The CSCW corpus is available through the ACM Digital Library; institutional access is required for full-text.
