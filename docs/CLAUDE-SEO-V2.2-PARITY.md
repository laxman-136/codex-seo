# Claude SEO v2.2 → Codex SEO Parity Plan

**Branch:** `upgrade/claude-seo-v2.2-parity`  
**Target:** Codex-native functional parity with `AgriciDaniel/claude-seo` v2.2.x  
**Approach:** Adapt features to Codex skills, TOML agents, deterministic runners, and local/API execution. Do not copy Claude-only plugin behavior unchanged.

## Objectives

1. Preserve the existing Codex-first architecture.
2. Port all applicable Claude SEO v2.2 workflows and references.
3. Convert Claude subagents into Codex TOML agent profiles.
4. Keep deterministic scripts as the source of truth for repeatable output.
5. Maintain Windows, macOS, and Linux installer support.
6. Add tests and CI gates before merging into `main`.

## Parity Workstreams

### 1. Orchestrator and command surface

- [ ] Synchronize the main SEO orchestrator with Claude SEO v2.2 routing logic.
- [ ] Add `/seo content-brief <topic>` support.
- [ ] Reconcile workflow counts, command documentation, and discovery metadata.
- [ ] Preserve natural-language routing in Codex.
- [ ] Add explicit capability and setup-required fallbacks.

### 2. Rendering and extraction

- [ ] Port shared Playwright Chromium rendering behavior.
- [ ] Support `--render auto`, `--render always`, and `--render never`.
- [ ] Add SPA detection for React, Next.js, Vue, Nuxt, Astro, and hydration shells.
- [ ] Integrate boilerplate extraction and publication-date detection.
- [ ] Add visual cross-check guidance for scroll-bound or interaction-bound hydration.

### 3. Content quality and E-E-A-T

- [ ] Port QRG-aligned content quality gates.
- [ ] Add filler-pattern detection and humanization checks.
- [ ] Add claim-verification scanning.
- [ ] Add expired-domain heritage checks.
- [ ] Update primary-source Google guidance references.

### 4. Technical SEO and Core Web Vitals

- [ ] Add LCP subpart analysis: TTFB, load delay, load duration, render delay.
- [ ] Add Speculation Rules detection.
- [ ] Add bfcache diagnostics.
- [ ] Add IndexNow support and provider-specific submission handling.
- [ ] Integrate Unlighthouse for multi-page Lighthouse analysis.
- [ ] Keep INP, LCP, CLS, FCP, and TTFB terminology current.

### 5. Schema and structured data

- [ ] Port explicit generators for Reservation, OrderAction, DiscussionForumPosting, and ProfilePage.
- [ ] Add e-commerce schema validation for merchant return policy, shipping details, memberships, energy efficiency, and ProductGroup variants.
- [ ] Add dual validation support for Google Rich Results and Schema Markup Validator.
- [ ] Port current schema deprecation references and warnings.

### 6. GEO and AI-search readiness

- [ ] Align GEO guidance with Google's AI optimization documentation.
- [ ] Port passage-citability scoring and question-heading analysis.
- [ ] Port evidence-based treatment of `llms.txt`.
- [ ] Add entity-presence and attribution-density checks.
- [ ] Add AI-generated product image metadata checks where applicable.

### 7. Local, international, and privacy

- [ ] Add GBP deprecation linting.
- [ ] Add `.business.site` URL detection.
- [ ] Add multi-location doorway-page guardrails.
- [ ] Add Consent Mode v2 diagnostics.
- [ ] Add machine-translation QA checks.
- [ ] Preserve hreflang and international-content parity workflows.

### 8. MCP and external integrations

- [ ] Update DataForSEO integration parity.
- [ ] Update Firecrawl integration parity.
- [ ] Add or refresh Ahrefs MCP support.
- [ ] Add SE Ranking AI Share-of-Voice support.
- [ ] Add Profound citation-tracking support.
- [ ] Add Bing Webmaster and IndexNow support.
- [ ] Add Unlighthouse extension support.
- [ ] Keep every paid integration opt-in and credential-driven.

### 9. Security and reliability

- [ ] Port SSRF and DNS-rebinding protections.
- [ ] Add secret-scanning CI gate.
- [ ] Harden `.gitignore` for runtime credentials and generated artifacts.
- [ ] Validate redirects, alternate IP forms, and trailing-dot FQDN cases.
- [ ] Ensure credentials remain outside the repository.

### 10. Installers and runtime

- [ ] Update Unix installer.
- [ ] Update Windows PowerShell installer.
- [ ] Keep Python 3.10+ compatibility.
- [ ] Verify Python 3.14 bootstrap behavior.
- [ ] Verify Playwright browser installation and skip flags.
- [ ] Update uninstall scripts.

### 11. Tests and CI

- [ ] Add parity tests for each new workflow.
- [ ] Add manifest and command-count consistency tests.
- [ ] Add installer smoke tests.
- [ ] Add deterministic-runner tests.
- [ ] Add security regression tests.
- [ ] Require clean CI before merge.

### 12. Documentation and release

- [ ] Update README feature counts and architecture diagrams.
- [ ] Update command reference.
- [ ] Add migration notes from the existing Codex release.
- [ ] Add troubleshooting guidance.
- [ ] Add attribution for upstream Claude SEO changes.
- [ ] Prepare a Codex-specific release tag only after tests pass.

## Delivery Stages

### Stage A — Inventory and architecture mapping

Compare Claude v2.2 files against the current Codex port and classify each item as:

- direct reference/data port,
- Codex skill adaptation,
- TOML-agent conversion,
- deterministic runner change,
- installer/runtime change,
- unsupported Claude-only behavior requiring an alternative.

### Stage B — Core feature port

Implement rendering, content, technical, schema, GEO, and orchestrator updates first. These provide the highest audit value.

### Stage C — Integrations and security

Port MCP extensions, Google/Bing integrations, SSRF protection, secret scanning, and credential handling.

### Stage D — Validation and release readiness

Run unit tests, installer smoke tests, workflow smoke tests, documentation checks, and a sample full-site audit before merging.

## Merge Criteria

The branch should not be merged until:

1. Core workflows execute through Codex without Claude-specific runtime assumptions.
2. New capabilities have deterministic or explicitly setup-required outputs.
3. Windows and Unix installers pass smoke tests.
4. Security regression tests pass.
5. Documentation accurately distinguishes implemented features from optional integrations.
6. CI is green.

## Important Note

"Parity" means equivalent user-facing capability implemented natively for Codex. Claude Code plugin commands, agent APIs, and runtime-specific behavior will be translated rather than copied verbatim.
