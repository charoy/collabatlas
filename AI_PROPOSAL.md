## AI Integration Proposal for CollabAtlas

### Objectives

AI can add value in two distinct use cases:

1. **Editorial production assistance**
	- propose summaries for articles, tools, or resources;
	- suggest likely taxonomies;
	- detect missing fields or inconsistencies;
	- help generate a first draft entry before human review;
	- suggest links between related entries.

2. **Assistance for site users**
	- answer questions such as “which tool or method fits my context?”;
	- explain differences between several entries;
	- guide users toward relevant pages, taxonomies, or comparisons;
	- rewrite site content in more accessible language.

These two use cases should not be designed as a single feature. It is better to separate:

- an internal **editorial assistant**;
- a **user-facing assistant** reserved for authorized users.

---

## Recommended General Principle

### Recommendation

Adopt a **hybrid** architecture:

- the public CollabAtlas site remains a **static Hugo site**;
- AI features are exposed through a **separate application service**;
- that service calls one or more external or internal models;
- access is controlled through authentication and roles.

This separation is recommended for four reasons:

1. **security**: no AI API keys in the public frontend;
2. **access control**: AI features limited to selected accounts;
3. **abuse prevention**: quotas, logging, moderation, emergency shutdown;
4. **scalability**: the static site remains simple while the AI layer can evolve independently.

---

## Proposed Target Architecture

### 1. Public static frontend remains unchanged

The Hugo site continues to serve:

- the catalogue;
- search;
- visualizations;
- editorial pages.

An AI interface appears only if the user is authorized.

### 2. Separate AI service

Create a small backend service, for example:

- **Python/FastAPI** if the goal is to stay close to the existing scripts;
- or **Node.js/TypeScript** if the priority is modern frontend/API integration.

This service handles:

- authentication and authorization;
- model calls;
- rate limiting;
- logging;
- prompt filtering;
- optional caching;
- connection to CollabAtlas data.

### 3. Data layer for AI

Two levels should be distinguished:

#### Level A — simple and quick to launch

The service reads directly from:

- YAML files in `data/entries/`;
- `data/research_articles.yaml`;
- optionally a JSON export generated at build time.

This is enough for a first assistant based on:

- search + content retrieval;
- constrained generation;
- suggestions derived from site metadata.

#### Level B — more robust in the medium term

Create a dedicated **AI index** generated at build time, for example a normalized JSON record per entry containing:

- title;
- type;
- summary;
- taxonomies;
- relations;
- URL;
- useful text for semantic search.

Then feed:

- either a simple hybrid engine;
- or a lightweight vector store;
- or a local index based on embeddings + metadata.

---

## Recommended AI Use Cases

### A. Internal editorial assistant

#### Priority features

1. **Entry pre-fill**
	- from a DOI, GitHub URL, Zenodo record, Zotero source, etc.;
	- propose a structured draft;
	- propose likely taxonomies with confidence levels.

2. **Editorial quality control**
	- missing fields;
	- consistency between type, taxonomies, and description;
	- related entry suggestions;
	- probable duplicate detection.

3. **Normalization assistance**
	- more consistent summaries;
	- tagline rewriting;
	- harmonization of tone and length.

#### Recommended governance

- AI never publishes on its own;
- every AI output is marked as a **suggestion**;
- human validation is required before integration.

### B. Restricted user assistant

#### Priority features

1. **Catalogue question answering**
	- “Which tools support hybrid collaboration in a small team?”
	- “Which methods are close to participatory design?”

2. **Guided orientation**
	- propose relevant entries;
	- point users to comparison views;
	- explain the taxonomies.

3. **Assisted comparison**
	- summarize 2 to 4 entries;
	- explain differences based on the user’s context.

#### Recommended limits

- answers should be strictly grounded in CollabAtlas content and metadata;
- always cite the entries or pages used;
- do not provide an “outside the knowledge base” answer without explicitly stating the limit.

---

## Access Control and Abuse Prevention

### Why access should be restricted

The need is legitimate:

- cost control;
- reduced spam and scraping;
- protection against abusive prompts;
- better quality of use.

### Recommended mechanisms

1. **Authentication**
	- editor or member accounts;
	- or SSO through GitHub / Microsoft / institutional identity.

2. **Roles**
	- `admin`;
	- `editor-ai`;
	- `member-ai`;
	- optionally `beta-user`.

3. **Quotas**
	- daily / weekly / monthly limits;
	- limits by action type (chat, enrichment, generation).

4. **Rate limiting**
	- per user;
	- per IP as an additional safeguard.

5. **Logging**
	- prompt;
	- response;
	- timestamp;
	- estimated cost;
	- resource consulted.

6. **Emergency shutdown mode**
	- fast deactivation of the AI service without affecting the public site.

---

## Hosting Impact

### Short answer

**Yes, probably.**

If the AI becomes interactive and reserved for authenticated users, simple static hosting will no longer be sufficient for that part.

### What can stay unchanged

- the public Hugo site;
- the main static deployment;
- the majority of pages and content.

### What will require additional hosting

- secure API;
- authentication;
- quota management;
- model calls;
- logs and possibly session storage.

### Recommended hosting setup

#### Option 1 — the most pragmatic

- main site on static hosting;
- AI backend on a small managed cloud service.

Examples:

- Azure App Service;
- Azure Container Apps;
- Railway / Render / Fly.io;
- a small VPS if strong control is required.

#### Option 2 — if the Azure ecosystem is preferred

- static site;
- FastAPI backend on Azure App Service or Container Apps;
- authentication through Microsoft Entra ID / GitHub OAuth;
- secrets in Azure Key Vault;
- optionally Azure OpenAI for the models.

This option is coherent if the project wants:

- more formal governance;
- restricted access;
- better traceability;
- clear separation between publishing and AI.

---

## Proposed 3-Phase Rollout

### Phase 1 — private editorial assistant

**Goal:** create value quickly without exposing AI to the public.

Scope:

- simple interface reserved for editors;
- generation of draft entries;
- taxonomy suggestions;
- quality control and missing-field detection.

Benefits:

- low abuse risk;
- controlled cost;
- direct value for enriching the site.

### Phase 2 — closed user assistant

**Goal:** open usage to a small group of authorized members.

Scope:

- catalogue-assisted chat;
- help with selection and comparison;
- quotas and logging.

Benefits:

- allows real usage patterns to be tested;
- refines safeguards before wider opening.

### Phase 3 — more advanced AI if value is confirmed

**Goal:** industrialize only the features that have demonstrated value.

Possible scope:

- semantic search;
- vector index;
- enriched automatic recommendations;
- AI dashboards for editors.

---

## Operational Recommendation

### Most reasonable proposal today

1. **Do not integrate AI directly into the public static site.**
2. **Create a separate backend service.**
3. **Start with a private editorial assistant.**
4. **Open the user assistant only to a restricted group.**
5. **Provide a dedicated AI data index instead of letting the model read raw files directly.**

### Why this is the best option

It:

- protects the public site;
- limits costs;
- reduces abuse;
- enables clear editorial governance;
- remains compatible with the current architecture.

---

## Decisions to Make Later

Before implementation, the following will need to be decided:

1. the types of authorized accounts;
2. the identity provider;
3. the model provider;
4. the acceptable level of logging;
5. how open the editorial assistant and user assistant should be;
6. the acceptable monthly budget.

---

## Summary

The right trajectory is not “add a chatbot to the site,” but rather:

- keep CollabAtlas as a **robust static foundation**;
- add a **separate, controlled, and progressive AI layer**;
- start with **internal editorial use**;
- later open a **restricted user assistant** if usage justifies it.

This approach will very likely require **additional hosting** for the AI layer, but not a full redesign of the main site.
