# CollabAtlas Governance

## Mission

CollabAtlas is an open, community-governed knowledge platform that catalogues, connects, and contextualizes collaborative solutions across domains, methods, tools, and research approaches. Our mission is to provide a reliable, long-lived reference for researchers and practitioners working on collaboration.

---

## Governance Model

CollabAtlas uses an **editorial board model**. Content quality is ensured through a combination of automated validation and human editorial review. Strategic decisions are made by consensus among core maintainers.

---

## Roles

### Core Maintainers

A small group (2-3 people) with full repository access.

**Responsibilities:**
- Set strategic direction for the project
- Merge pull requests (after domain editor approval)
- Manage releases and deployments
- Moderate community interactions
- Appoint and remove domain editors
- Resolve conflicts that cannot be settled at the editor level

### Domain Editors

One or more editors per major domain (e.g., healthcare, education, software engineering).

**Responsibilities:**
- Review and approve contributions in their domain
- Ensure accuracy, relevance, and quality of entries
- Triage monthly freshness reports for their domain
- Propose new taxonomy values relevant to their domain
- Mentor new contributors

### Contributors

Anyone who submits content following our [Contributing Guide](CONTRIBUTING.md).

**Responsibilities:**
- Follow the contribution guidelines and schemas
- Respond to review feedback
- Respect the Code of Conduct

---

## Decision Making

### Content Decisions

- **New entries and updates:** Require approval from the relevant domain editor + 1 core maintainer
- **Research articles:** Require approval from any domain editor whose domain is tagged

### Structural Decisions

- **New taxonomy values:** Proposed via an issue with the `taxonomy` label. Open for discussion for 2 weeks, then decided by consensus among core maintainers
- **Schema changes:** Proposed via PR with a rationale. Require approval from 2 core maintainers
- **New entry types:** RFC process — issue open for 4 weeks, decided by core maintainer consensus

### Policy Decisions

- **Governance changes:** Proposed via PR modifying this file. Open for review for 2 weeks. Require consensus among all core maintainers
- **Code of Conduct changes:** Same process as governance changes

---

## Becoming a Domain Editor

Domain editors are recognized for their expertise and sustained contributions.

**Path to becoming a domain editor:**

1. Make at least 5 quality contributions (entries, articles, or reviews) in the relevant domain
2. Be nominated by an existing domain editor or core maintainer
3. Nomination is approved by majority vote of core maintainers
4. A 1-week community comment period allows objections

**Domain editors may step down** at any time by notifying the core maintainers. Inactive editors (no activity for 6+ months) may be asked to confirm their continued involvement.

---

## Conflict Resolution

1. **Discussion:** Disagreements are first discussed in the relevant issue or PR
2. **Mediation:** If unresolved, a core maintainer mediates
3. **Vote:** If mediation fails, core maintainers vote (simple majority)
4. **Code of Conduct:** Behavioral issues are handled per the [Code of Conduct](CODE_OF_CONDUCT.md)

---

## Amendments

Changes to this governance document require:
- A pull request modifying this file
- A 2-week review period
- Consensus among all core maintainers
- No unresolved objections from domain editors
