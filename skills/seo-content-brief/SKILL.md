---
name: seo-content-brief
description: >
  Generate evidence-aware SEO content briefs with search-intent classification,
  competitor scoring, content-gap prioritisation, per-section word counts,
  keyword-placement guardrails, page-type templates, information-gain requirements,
  E-E-A-T checks, and internal-link recommendations. Supports new-page and
  improve-existing-page modes. Trigger on content brief, writing brief, content
  outline, blog brief, service-page brief, content plan, or outline for.
user-invocable: true
argument-hint: "[url-or-keyword] [page-type]"
license: MIT
metadata:
  author: puneetindersingh
  original_author: puneetindersingh
  codex_port: laxman-136/codex-seo
  version: "1.0.0-codex.1"
  category: seo
---

# SEO Content Brief Generator

Create a practical brief that a writer can execute and an SEO lead can verify. Do
not fabricate rankings, search volume, competitor word counts, page content, or
business capabilities. Clearly separate supplied evidence, observed evidence,
inference, and work still requiring research.

## Deterministic runner

Use the plugin-root script:

```bash
python scripts/generate_content_brief.py "target keyword" --json
python scripts/generate_content_brief.py "https://example.com/existing-page" --mode improve --json
python scripts/generate_content_brief.py "target keyword" \
  --page-type service \
  --competitors-json competitors.json \
  --site-context-json site-context.json \
  --json
```

The runner writes `CONTENT-BRIEF.md` and `SUMMARY.json`. Without competitor or site
context, it returns `research_required` rather than inventing evidence.

## 1. Determine brief mode

### Improve mode

Use when the target is an existing page URL.

- Review the current page before recommending changes.
- Mark proposed sections as **keep**, **strengthen**, or **add**.
- Preserve strong, accurate content.
- Prefer targeted improvements over an unnecessary full rewrite.
- Report an unreachable page instead of guessing what it contains.

### New-page mode

Use when the target is a keyword or topic.

- Establish the target site's real products, services, audiences, and locations.
- Build a new page only within that credible scope.
- Use the sitemap or verified page inventory for internal links and hub coverage.

## 2. Gather evidence

Collect, when available:

- Target page or homepage context
- XML sitemap or verified page inventory
- Top organic results for the target query
- Current keyword and intent data from configured providers
- First-party customer, conversion, sales, and subject-matter evidence

Optional live-data sources include DataForSEO, Ahrefs, Google Search Console, and
manual SERP review. Never imply these sources were used when they were not.

## 3. Filter and score competitors

Use real business competitors. Exclude encyclopedias, social platforms,
marketplaces, directories, job boards, generic news sites, SEO-tool articles,
government/academic domains, login/cart pages, tags, archives, and other
non-comparable results. See `references/excluded-domains.md`.

Score each retained competitor from 1-10 on:

- Depth
- Formatting
- SEO execution
- UX

Identify:

- **Topic gaps:** important subtopics absent from ranking pages
- **Depth gaps:** relevant topics treated superficially
- **Quality gaps:** weak evidence, outdated claims, poor formatting, or no expert view

Prioritise gaps with:

```text
Priority = Impact × Competitive Advantage ÷ Effort
```

## 4. Classify intent and page type

Intent must be one of:

- Informational
- Commercial
- Transactional
- Navigational

State the page format currently rewarded by the SERP, such as guide, list,
comparison, service page, landing page, FAQ, video, or local result set.

Select a template from `references/page-type-templates.md`, then adapt it to the
verified business and competitive evidence.

## 5. Critical rules

### Website relevance

Every suggested heading, offer, FAQ, proof point, location, and internal link must
be something the target business can credibly support. Remove competitor sections
that describe products or services the target site does not offer.

### Site-structure coverage

For category, hub, overview, or “types of” pages:

- Represent every relevant verified child page.
- Give each child category its own section and internal-link recommendation.
- Do not invent or omit categories.

For single-service and blog pages, recommend only contextually relevant links.

### Output language

- Write for a content writer or business stakeholder.
- Do not mention internal framework names or research-tool brands in the final brief.
- Do not present generic “more detail” as information gain.

## 6. Keyword guidance

Follow `references/keyword-density.md`.

- Primary exact-match density guardrail: 0.5%-2.0%.
- Review above 2%; avoid exceeding 3%.
- Require natural placement in title, H1, slug, meta description, first 100 words,
  and one accurate image alt attribute.
- Do not force the exact keyword into every heading or paragraph.
- Use 5-8 closely related terms and broader semantic coverage where relevant.
- Give section-level placement guidance.

## 7. Meta requirements

- Title tag: 50-60 characters, primary topic near the front, brand last.
- Meta description: 130-150 characters, active voice, specific value, clear action.
- Treat generated tags as drafts until brand pattern and SERP evidence are verified.

## 8. Information gain and E-E-A-T

Every full brief must define one specific new contribution, such as:

- First-party benchmark with method, sample, date, result, and limitations
- Anonymised case study with measurable outcome
- Expert commentary based on direct experience
- Original comparison or synthesis using cited primary evidence

Specify exact trust requirements: qualified author/reviewer, current primary
sources, update date, claim ownership, first-party proof, and YMYL review where
applicable.

## 9. Internal links

Recommend 3-5 real links with:

- Suggested anchor text
- Exact destination URL
- Hub-to-spoke, spoke-to-pillar, or contextual relationship

Use placeholders only when site evidence was not supplied, and label them clearly.

## Required full-brief structure

```markdown
# Content Brief: [Primary Keyword]

## Search Intent
## Competitor Analysis
## Content Gaps and Opportunities
## Winning Outline
## Recommended Meta Tags
## Unique Angle and Information Gain
## E-E-A-T Requirements
## Internal Linking Opportunities
## Evidence Gaps Before Publication
```

The outline must include H1, slug, total target word count, competitor average when
available, H2/H3 structure, section word counts, content formats, Featured Snippet
targets, keyword guidance, and writing notes.

## Outline-only mode

When the user asks only for an outline, omit competitor tables, gap analysis,
information gain, and E-E-A-T sections. Keep H1, slug, target words, full H2/H3
structure, section counts, format notes, snippet targets, keyword guidance, and
brief writing notes.

## Error handling

| Scenario | Required action |
|---|---|
| Target page unreachable | Report the failure; do not infer page content. |
| No genuine competitors remain | Broaden carefully and disclose the thin landscape. |
| No sitemap/site inventory | Continue, but flag internal links as incomplete. |
| Page type omitted | Auto-detect and state the detected type. |
| No competitor word-count evidence | Use a page-type planning baseline and label it as provisional. |
| Live provider unavailable | Produce a research-required brief; do not fabricate live metrics. |

## Shared Cache

Write the deterministic content-brief summary to:

- `.seo-cache/content-brief.json`

Use this cache for later content planning, page analysis, internal-link recommendations, and related SEO workflows. Treat cached competitor or keyword evidence as stale when the user explicitly requests a fresh analysis.
