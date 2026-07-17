#!/usr/bin/env python3
"""Generate deterministic, evidence-aware SEO content brief artifacts.

This runner intentionally does not fabricate SERP or keyword-volume data. It accepts
optional competitor/site-context JSON produced by a live provider or analyst and
creates a complete brief from the supplied evidence. Without evidence, it emits a
useful draft plus explicit research gaps.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

EXCLUDED_DOMAINS = {
    "wikipedia.org", "britannica.com", "investopedia.com", "dictionary.com",
    "merriam-webster.com", "webmd.com", "healthline.com", "mayoclinic.org",
    "facebook.com", "instagram.com", "twitter.com", "x.com", "linkedin.com",
    "pinterest.com", "tiktok.com", "youtube.com", "reddit.com", "quora.com",
    "threads.net", "medium.com", "substack.com", "blogger.com", "wordpress.com",
    "amazon.com", "amazon.co.uk", "amazon.com.au", "ebay.com", "etsy.com",
    "alibaba.com", "stackoverflow.com", "stackexchange.com", "bbc.com",
    "cnn.com", "theguardian.com", "forbes.com", "techcrunch.com", "statista.com",
    "similarweb.com", "tripadvisor.com", "yelp.com", "trustpilot.com",
    "semrush.com", "ahrefs.com", "moz.com", "backlinko.com",
    "searchengineland.com", "searchenginejournal.com", "chatgpt.com",
    "claude.ai", "perplexity.ai",
}

EXCLUDED_PATH_PARTS = {
    "/tag/", "/tags/", "/author/", "/category/", "/archive/", "/feed/",
    "/rss/", "/wp-json/", "/wp-admin/", "/login", "/signup", "/register",
    "/cart", "/checkout", "/terms", "/privacy", "/cookie-policy",
    "/disclaimer", "/sitemap", "/robots.txt",
}

PAGE_DEFAULTS = {
    "service": 1300,
    "blog": 1800,
    "case-study": 1200,
    "category": 1500,
    "landing": 1100,
    "faq": 1200,
    "location": 1300,
    "about": 1000,
    "homepage": 1200,
    "comparison": 2000,
    "product": 1000,
}

TEMPLATES: dict[str, list[tuple[str, str, str, float]]] = {
    "service": [
        ("What is {keyword}?", "Define the service and intended outcome.", "Answer-first definition box", 0.10),
        ("Who needs {keyword}?", "Qualify high-intent audiences and use cases.", "Scenario-based bullet list", 0.12),
        ("How {keyword} works", "Reduce friction by explaining delivery.", "Numbered process", 0.16),
        ("Costs, timelines and what affects them", "Answer commercial questions without unsupported promises.", "Range/table with assumptions", 0.14),
        ("Outcomes and proof", "Demonstrate value with first-party evidence.", "Case-study snippets and metrics", 0.17),
        ("Why choose the provider", "Differentiate with verifiable specifics.", "Comparison bullets", 0.13),
        ("Frequently asked questions", "Capture objections and long-tail questions.", "5-8 concise Q&As; FS targets", 0.12),
        ("Next step", "Move qualified visitors to one action.", "Low-friction CTA", 0.06),
    ],
    "blog": [
        ("Direct answer: {keyword}", "Answer the core query immediately.", "40-60 word answer; FS target", 0.07),
        ("Why this matters", "Establish context, stakes and audience relevance.", "Short explanatory section", 0.10),
        ("Core concepts and terminology", "Build the minimum knowledge needed.", "Definitions and examples", 0.15),
        ("Step-by-step approach", "Deliver the main practical value.", "Numbered process with examples", 0.25),
        ("Examples and decision criteria", "Help readers apply the guidance.", "Table, examples or checklist", 0.18),
        ("Common mistakes", "Add experience-led warnings.", "Numbered list", 0.12),
        ("Frequently asked questions", "Cover long-tail and PAA-style questions.", "5 concise Q&As", 0.08),
        ("Recommended next action", "Connect informational intent to a relevant next step.", "Contextual CTA/internal link", 0.05),
    ],
    "case-study": [
        ("Outcome summary", "Lead with a verifiable result.", "Metric-led summary", 0.10),
        ("Client situation", "Give relevant context without exposing confidential data.", "Narrative", 0.12),
        ("The challenge", "Explain the constraints and stakes.", "Problem framing", 0.15),
        ("The approach", "Show expertise and execution detail.", "Step-by-step narrative", 0.28),
        ("The result", "Report outcomes, timeframes and caveats.", "Before/after table", 0.22),
        ("Key takeaways", "Turn the project into reusable insight.", "3-5 bullets", 0.08),
        ("Related solution", "Link the proof to the relevant commercial page.", "Contextual CTA", 0.05),
    ],
    "category": [
        ("What {keyword} covers", "Define the category and its boundaries.", "Overview", 0.12),
        ("Available options", "Represent every relevant child page or offering.", "Linked card/list; one subsection per child", 0.36),
        ("How to choose", "Help readers self-select the correct option.", "Decision table", 0.18),
        ("Who this is for", "Qualify audience segments.", "Persona bullets", 0.10),
        ("Process overview", "Explain the journey after selection.", "Numbered steps", 0.10),
        ("Frequently asked questions", "Cover category-level objections.", "5-8 Q&As", 0.09),
        ("Next step", "Route users to a child page or consultation.", "CTA", 0.05),
    ],
    "landing": [
        ("Hero: outcome and offer", "State one clear promise and action.", "Headline, proof point, CTA", 0.10),
        ("Problem and urgency", "Show understanding of the user's situation.", "Short problem narrative", 0.12),
        ("Benefits and differentiators", "Translate features into outcomes.", "3-5 benefit blocks", 0.20),
        ("Proof", "Reduce perceived risk.", "Testimonials, metrics, credentials", 0.18),
        ("How it works", "Make the action feel easy.", "3-step process", 0.14),
        ("Offer details", "Clarify inclusions, exclusions and terms.", "Scannable table", 0.12),
        ("Objections and FAQ", "Remove final blockers.", "4-6 Q&As", 0.09),
        ("Final call to action", "Repeat one primary conversion action.", "CTA", 0.05),
    ],
    "faq": [
        ("Core questions about {keyword}", "Answer the highest-intent questions first.", "4-6 Q&As, 40-60 words each", 0.38),
        ("Decision and comparison questions", "Support evaluation intent.", "3-5 Q&As with tables where useful", 0.25),
        ("Process, cost and risk questions", "Remove practical objections.", "3-5 Q&As", 0.25),
        ("Next step", "Route readers to the relevant pillar or service page.", "Contextual CTA", 0.12),
    ],
    "location": [
        ("{keyword} in the local area", "Establish real local relevance.", "Overview with natural local entities", 0.14),
        ("Services available", "Describe only services actually delivered locally.", "Linked service list", 0.22),
        ("Areas served", "Clarify geographic coverage.", "Suburb/region list or map", 0.13),
        ("Local expertise and process", "Show experience with local constraints.", "Process and examples", 0.18),
        ("Local proof", "Build trust with location-specific evidence.", "Reviews, case studies, team", 0.16),
        ("Local frequently asked questions", "Cover local-intent variations.", "5 Q&As", 0.11),
        ("Contact the local team", "Give a location-relevant action.", "Phone/address/booking CTA", 0.06),
    ],
    "about": [
        ("Who we are", "State positioning and expertise.", "Concise narrative", 0.16),
        ("Our story", "Humanise the organisation.", "Timeline/narrative", 0.18),
        ("Leadership and team", "Demonstrate expertise.", "Credentialled bios", 0.24),
        ("How we work", "Set expectations and values in action.", "Principles with examples", 0.14),
        ("Proof and recognition", "Support authority claims.", "Awards, media, certifications", 0.16),
        ("Explore services or contact us", "Route readers to the next step.", "Internal links and CTA", 0.12),
    ],
    "homepage": [
        ("Hero: primary value proposition", "Explain who the business helps and how.", "Headline, subheadline, CTA", 0.10),
        ("Services or products", "Represent core commercial categories.", "Linked cards", 0.26),
        ("Why choose the brand", "Differentiate with evidence.", "Specific proof-led bullets", 0.16),
        ("How it works", "Explain the customer journey.", "3-5 steps", 0.12),
        ("Proof and trust", "Reduce uncertainty.", "Testimonials, outcomes, credentials", 0.17),
        ("Locations or service area", "Clarify availability.", "Map/list", 0.08),
        ("Frequently asked questions", "Answer broad business questions.", "4-6 Q&As", 0.07),
        ("Primary call to action", "Drive the main conversion.", "CTA", 0.04),
    ],
    "comparison": [
        ("Quick verdict", "Answer which option fits which user.", "Decision summary; FS target", 0.08),
        ("At-a-glance comparison", "Expose key differences immediately.", "Feature/criteria table", 0.16),
        ("Option A overview", "Explain strengths, limits and ideal use cases.", "Evidence-led review", 0.15),
        ("Option B overview", "Explain strengths, limits and ideal use cases.", "Evidence-led review", 0.15),
        ("Detailed criteria comparison", "Compare on the factors that drive the decision.", "Multiple criterion subsections", 0.26),
        ("Costs and total value", "Compare commercial implications fairly.", "Pricing/value table with dates", 0.10),
        ("Which should you choose?", "Map scenarios to recommendations.", "Decision matrix", 0.06),
        ("Frequently asked questions", "Capture long-tail comparison queries.", "4-6 Q&As", 0.04),
    ],
    "product": [
        ("Product overview", "State the use case and primary benefit.", "Concise answer-first copy", 0.12),
        ("Key features and benefits", "Connect capabilities to outcomes.", "Feature-benefit table", 0.22),
        ("Specifications and compatibility", "Answer technical qualification questions.", "Structured table", 0.18),
        ("How to use or implement", "Reduce adoption friction.", "Steps/video support", 0.15),
        ("Proof, reviews and comparisons", "Build confidence.", "Verified reviews and comparison points", 0.15),
        ("Price, delivery and returns", "Answer transactional questions.", "Offer details", 0.10),
        ("Frequently asked questions", "Remove purchase objections.", "4-6 Q&As", 0.05),
        ("Purchase call to action", "Drive the transaction.", "CTA", 0.03),
    ],
}


@dataclass(frozen=True)
class Competitor:
    url: str
    h2_sections: tuple[str, ...]
    word_count: int | None
    depth: int | None
    formatting: int | None
    seo: int | None
    ux: int | None
    main_gap: str

    @property
    def score(self) -> int | None:
        values = (self.depth, self.formatting, self.seo, self.ux)
        return sum(values) if all(isinstance(v, int) for v in values) else None


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_url(value: str) -> bool:
    parsed = urlparse(value.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def slugify(value: str, limit: int = 80) -> str:
    if is_url(value):
        parsed = urlparse(value)
        source = parsed.path.strip("/").split("/")[-1] or parsed.netloc
    else:
        source = value
    slug = re.sub(r"[^a-z0-9]+", "-", source.lower()).strip("-")
    return (slug[:limit].rstrip("-") or "content-brief")


def title_case_keyword(keyword: str) -> str:
    small = {"a", "an", "and", "as", "at", "by", "for", "from", "in", "of", "on", "or", "the", "to", "vs", "with"}
    acronyms = {"seo", "ai", "geo", "aeo", "scm", "hcm", "erp", "crm", "ga4", "gsc", "cwv", "api", "saas", "faq", "b2b", "b2c"}
    words = re.split(r"\s+", keyword.strip())
    rendered = []
    for i, word in enumerate(words):
        lower = word.lower()
        if lower in acronyms:
            rendered.append(lower.upper())
        elif i and lower in small:
            rendered.append(lower)
        else:
            rendered.append(word[:1].upper() + word[1:])
    return " ".join(rendered)


def extract_keyword(target: str) -> str:
    if not is_url(target):
        return re.sub(r"\s+", " ", target.strip())
    parsed = urlparse(target)
    last = parsed.path.rstrip("/").split("/")[-1]
    if not last:
        return parsed.netloc.split(":")[0].replace("www.", "").split(".")[0]
    return re.sub(r"[-_]+", " ", last).strip()


def classify_intent(keyword: str) -> str:
    k = keyword.lower()
    if any(term in k for term in ("login", "official", "website", "portal", "contact")):
        return "navigational"
    if any(term in k for term in ("buy", "book", "hire", "price", "pricing", "quote", "demo", "register", "enrol", "enroll", "download")):
        return "transactional"
    if any(term in k for term in ("best", "vs", "versus", "compare", "comparison", "review", "alternative", "top ")):
        return "commercial"
    return "informational"


def detect_page_type(keyword: str, target: str = "") -> str:
    k = f"{keyword} {target}".lower()
    if any(term in k for term in (" vs ", " versus ", "comparison", "alternatives", "best ")):
        return "comparison"
    if any(term in k for term in ("case study", "success story", "customer story")):
        return "case-study"
    if any(term in k for term in ("faq", "frequently asked", "questions")):
        return "faq"
    if any(term in k for term in ("about us", "our team", "who we are")):
        return "about"
    if any(term in k for term in ("homepage", "home page")) or (is_url(target) and urlparse(target).path in {"", "/"}):
        return "homepage"
    if any(term in k for term in ("landing page", "free demo", "download", "webinar", "lead magnet")):
        return "landing"
    if any(term in k for term in ("category", "types of", "solutions", "services overview", "courses")):
        return "category"
    if any(term in k for term in ("product", "model", "specifications", "buy ")):
        return "product"
    if re.search(r"\b(in|near)\s+[A-Z]?[a-z]+", keyword) or any(term in k for term in ("location page", "local ")):
        return "location"
    if any(term in k for term in ("service", "consulting", "training", "agency", "company", "provider", "management")):
        return "service"
    return "blog"


def clamp_score(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return max(1, min(10, number))


def excluded_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return True
    host = parsed.netloc.lower().split(":")[0].removeprefix("www.")
    if not host:
        return True
    if host.endswith((".gov", ".gov.au", ".gov.uk", ".gov.nz", ".gc.ca", ".edu", ".edu.au", ".ac.uk", ".ac.nz")):
        return True
    if any(host == domain or host.endswith(f".{domain}") for domain in EXCLUDED_DOMAINS):
        return True
    path = parsed.path.lower()
    return any(part in path for part in EXCLUDED_PATH_PARTS)


def load_json(path: str | None) -> Any:
    if not path:
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def parse_competitors(payload: Any) -> tuple[list[Competitor], list[str]]:
    if payload is None:
        return [], ["Live SERP competitor evidence was not supplied."]
    rows = payload.get("competitors", []) if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError("Competitor JSON must be a list or an object with a 'competitors' list.")
    competitors: list[Competitor] = []
    exclusions: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        url = str(row.get("url", "")).strip()
        if excluded_url(url):
            if url:
                exclusions.append(f"Excluded non-competitor: {url}")
            continue
        headings = row.get("h2_sections") or row.get("headings") or []
        if isinstance(headings, str):
            headings = [headings]
        try:
            wc = int(row["word_count"]) if row.get("word_count") is not None else None
        except (TypeError, ValueError):
            wc = None
        competitors.append(Competitor(
            url=url,
            h2_sections=tuple(str(x) for x in headings[:8]),
            word_count=wc if wc and wc > 0 else None,
            depth=clamp_score(row.get("depth")),
            formatting=clamp_score(row.get("formatting")),
            seo=clamp_score(row.get("seo")),
            ux=clamp_score(row.get("ux")),
            main_gap=str(row.get("main_gap") or "Requires analyst review"),
        ))
    return competitors[:5], exclusions


def competitor_average(competitors: Iterable[Competitor]) -> int | None:
    counts = [c.word_count for c in competitors if c.word_count]
    return round(sum(counts) / len(counts)) if counts else None


def round_to_50(value: int, minimum: int = 50) -> int:
    return max(minimum, int(round(value / 50.0) * 50))


def allocate_words(total: int, weights: list[float]) -> list[int]:
    raw = [round_to_50(max(50, round(total * weight))) for weight in weights]
    diff = total - sum(raw)
    raw[-1] = max(50, raw[-1] + diff)
    return raw


def secondary_terms(keyword: str) -> list[str]:
    base = keyword.lower().strip()
    candidates = [
        f"{base} guide", f"{base} process", f"{base} benefits", f"{base} cost",
        f"{base} examples", f"{base} best practices", f"{base} checklist",
        f"how to choose {base}",
    ]
    return list(dict.fromkeys(candidates))[:8]


def build_outline(keyword: str, page_type: str, target_words: int, site_context: Any = None) -> list[dict[str, Any]]:
    template = TEMPLATES.get(page_type, TEMPLATES["blog"])
    counts = allocate_words(target_words, [row[3] for row in template])
    terms = secondary_terms(keyword)
    outline: list[dict[str, Any]] = []
    for i, ((heading, purpose, fmt, _), words) in enumerate(zip(template, counts)):
        heading_text = heading.format(keyword=title_case_keyword(keyword))
        keyword_note = (
            f"Use the primary keyword naturally once in this section; use '{terms[i % len(terms)]}' only where accurate."
            if i in {0, 2} else
            f"Use a natural variation; avoid repeating the exact primary keyword solely for density."
        )
        outline.append({
            "level": "H2",
            "heading": heading_text,
            "word_count": words,
            "purpose": purpose,
            "format": fmt,
            "featured_snippet_target": "FS target" in fmt,
            "keyword_guidance": keyword_note,
            "writing_note": "Support claims with current primary sources or first-party evidence.",
        })

    pages = []
    if isinstance(site_context, dict):
        pages = site_context.get("pages") or site_context.get("urls") or []
    if page_type == "category" and pages:
        child_titles = []
        for page in pages[:20]:
            if isinstance(page, str):
                child_titles.append(extract_keyword(page))
            elif isinstance(page, dict):
                child_titles.append(str(page.get("title") or extract_keyword(str(page.get("url", "")))))
        outline[1]["subsections"] = [
            {"level": "H3", "heading": title_case_keyword(title), "internal_link_required": True}
            for title in child_titles if title
        ]
    return outline


def fit_title(keyword: str) -> str:
    suffix = " | [Brand]"
    base = f"{title_case_keyword(keyword)} Guide"
    if len(base) + len(suffix) < 50:
        base += ": Strategy, Examples and Tips"
    max_base = 60 - len(suffix)
    if len(base) > max_base:
        base = base[:max_base].rsplit(" ", 1)[0].rstrip(" -|:,.")
    title = base + suffix
    if len(title) < 50:
        room = 60 - len(title)
        addition = " for Results"[:room]
        title = base + addition + suffix
    return title


def fit_description(keyword: str) -> str:
    title_keyword = title_case_keyword(keyword)
    candidates = [
        f"Learn {keyword} with practical steps, examples, decision criteria and common mistakes. Use this checklist to create accurate content and choose the right next action.",
        f"Explore {keyword}: practical steps, examples, decision criteria and common mistakes. Use the checklist to create useful content and choose the next action.",
        f"{title_keyword}: practical steps, examples and evidence checks. Use this checklist to create accurate content, avoid common mistakes and choose the next action.",
        f"{title_keyword}: practical examples and evidence checks to create accurate content, avoid common mistakes and choose the next action.",
        f"{title_keyword}: practical examples and evidence checks to create accurate content and choose the next action with confidence.",
    ]
    for candidate in candidates:
        if 130 <= len(candidate) <= 150:
            return candidate
    short = candidates[-1]
    if len(short) > 150:
        short = f"{title_keyword}: practical evidence checks for accurate content, fewer mistakes and a clear next action."
    if len(short) > 150:
        short = short[:149].rsplit(" ", 1)[0].rstrip(" ,.;:") + "."
    while len(short) < 130:
        additions = [" Review the evidence before publishing.", " Apply the checklist before publishing.", " Start with verified evidence."]
        added = False
        for addition in additions:
            candidate = short.rstrip(".") + addition
            if len(candidate) <= 150:
                short = candidate
                added = True
                break
        if not added:
            break
    return short


def build_internal_links(site_context: Any, page_type: str) -> list[dict[str, str]]:
    pages = []
    if isinstance(site_context, dict):
        pages = site_context.get("pages") or site_context.get("urls") or []
    links: list[dict[str, str]] = []
    for page in pages[:5]:
        if isinstance(page, str):
            url = page
            title = title_case_keyword(extract_keyword(page))
        elif isinstance(page, dict):
            url = str(page.get("url", ""))
            title = str(page.get("title") or title_case_keyword(extract_keyword(url)))
        else:
            continue
        if url:
            links.append({"anchor": title, "target": url, "relationship": "hub-to-spoke" if page_type == "category" else "contextual"})
    while len(links) < 3:
        index = len(links) + 1
        links.append({
            "anchor": f"[Relevant internal anchor {index}]",
            "target": f"[Confirm real site URL {index}]",
            "relationship": "contextual",
        })
    return links[:5]


def build_gaps(competitors: list[Competitor]) -> list[dict[str, Any]]:
    if not competitors:
        return [
            {
                "type": "evidence gap",
                "opportunity": "Collect and review at least three genuine business competitors before finalising the outline.",
                "impact": 5,
                "competitive_advantage": 4,
                "effort": 2,
                "priority_score": 10.0,
            }
        ]
    gaps = []
    for competitor in competitors:
        gaps.append({
            "type": "quality gap",
            "opportunity": competitor.main_gap,
            "source": competitor.url,
            "impact": 4,
            "competitive_advantage": 3,
            "effort": 2,
            "priority_score": 6.0,
        })
    return gaps[:5]


def render_competitor_table(competitors: list[Competitor]) -> str:
    header = "| # | URL | Key H2 Sections | Est. Words | Score | Main Gap |\n|---|-----|-----------------|------------|-------|----------|"
    if not competitors:
        return header + "\n| — | Evidence not supplied | Run live SERP research | — | — | Do not finalise competitive claims yet |"
    rows = []
    for i, comp in enumerate(competitors, 1):
        headings = "; ".join(comp.h2_sections[:4]) or "Not supplied"
        score = f"{comp.score}/40" if comp.score is not None else "Not scored"
        rows.append(f"| {i} | {comp.url} | {headings} | {comp.word_count or '—'} | {score} | {comp.main_gap} |")
    return header + "\n" + "\n".join(rows)


def render_outline(outline: list[dict[str, Any]]) -> str:
    parts = []
    for section in outline:
        fs = " — **FS target**" if section.get("featured_snippet_target") else ""
        parts.append(
            f"## {section['heading']} — ~{section['word_count']} words{fs}\n"
            f"- **Purpose:** {section['purpose']}\n"
            f"- **Format:** {section['format']}\n"
            f"- **Keyword guidance:** {section['keyword_guidance']}\n"
            f"- **Writing note:** {section['writing_note']}"
        )
        for subsection in section.get("subsections", []):
            parts.append(f"### {subsection['heading']}\n- Add a verified internal link to the matching child page.")
    return "\n\n".join(parts)


def render_markdown(result: dict[str, Any], outline_only: bool = False) -> str:
    keyword = result["primary_keyword"]
    avg = result["competitor_average_words"]
    avg_text = f"~{avg} words" if avg else "not available; validate with live SERP evidence"
    if outline_only:
        return f"""# Content Outline: {title_case_keyword(keyword)}

- **Detected page type:** {result['page_type']}
- **H1:** {result['h1']}
- **URL slug:** /{result['url_slug']}
- **Target word count:** ~{result['target_word_count']} words (competitor average: {avg_text})

{render_outline(result['outline'])}
"""

    gaps = "\n".join(
        f"- **{gap['type'].title()}:** {gap['opportunity']} (priority: {gap['priority_score']})"
        for gap in result["content_gaps"]
    )
    eeat = "\n".join(f"- {item}" for item in result["eeat_requirements"])
    links = "\n".join(
        f"- **{item['anchor']}** → `{item['target']}` ({item['relationship']})"
        for item in result["internal_links"]
    )
    evidence = "\n".join(f"- {item}" for item in result["evidence_gaps"]) or "- None"
    return f"""# Content Brief: {title_case_keyword(keyword)}

## Search Intent

- **Intent:** {result['search_intent']}
- **Likely SERP format:** {result['serp_format']}
- **Target audience:** {result['target_audience']}
- **Mode:** {result['mode']}
- **Detected page type:** {result['page_type']}

## Competitor Analysis

{render_competitor_table(result['competitors_parsed'])}

## Content Gaps and Opportunities

{gaps}

## Winning Outline

- **H1:** {result['h1']}
- **URL slug:** /{result['url_slug']}
- **Target word count:** ~{result['target_word_count']} words (competitor average: {avg_text})
- **Primary keyword density guardrail:** 0.5%-2.0%; review above 2%; avoid exceeding 3%.
- **Required placements:** title, H1, slug, meta description, first 100 words, and one accurate image alt text.

{render_outline(result['outline'])}

## Recommended Meta Tags

- **Title ({len(result['meta']['title'])} chars):** {result['meta']['title']}
- **Meta description ({len(result['meta']['description'])} chars):** {result['meta']['description']}

## Unique Angle and Information Gain

{result['information_gain']}

## E-E-A-T Requirements

{eeat}

## Internal Linking Opportunities

{links}

## Evidence Gaps Before Publication

{evidence}
"""


def serialize_competitors(competitors: list[Competitor]) -> list[dict[str, Any]]:
    return [
        {
            "url": c.url,
            "h2_sections": list(c.h2_sections),
            "word_count": c.word_count,
            "depth": c.depth,
            "formatting": c.formatting,
            "seo": c.seo,
            "ux": c.ux,
            "score": c.score,
            "main_gap": c.main_gap,
        }
        for c in competitors
    ]


def generate_content_brief(
    target: str,
    *,
    page_type: str = "auto",
    mode: str = "auto",
    competitors_payload: Any = None,
    site_context: Any = None,
    target_word_count: int | None = None,
    outline_only: bool = False,
) -> dict[str, Any]:
    target = target.strip()
    if not target:
        raise ValueError("A URL, keyword, or topic is required.")
    keyword = extract_keyword(target)
    resolved_mode = ("improve" if is_url(target) else "new") if mode == "auto" else mode
    if resolved_mode not in {"new", "improve"}:
        raise ValueError("Mode must be auto, new, or improve.")
    resolved_type = detect_page_type(keyword, target) if page_type == "auto" else page_type
    if resolved_type not in PAGE_DEFAULTS:
        raise ValueError(f"Unsupported page type: {resolved_type}")

    competitors, exclusions = parse_competitors(competitors_payload)
    avg = competitor_average(competitors)
    baseline = target_word_count or (round_to_50(int(avg * 1.05), minimum=300) if avg else PAGE_DEFAULTS[resolved_type])
    outline = build_outline(keyword, resolved_type, baseline, site_context)
    intent = classify_intent(keyword)
    serp_format = {
        "informational": "answer-first guide, how-to, list or comparison table",
        "commercial": "comparison/review page with decision table",
        "transactional": "service, product or conversion landing page",
        "navigational": "clear brand/entity page",
    }[intent]
    evidence_gaps = list(exclusions)
    if not competitors:
        evidence_gaps.append("Run a live Google SERP review and score 3-5 real competitors before approving the brief.")
    if not site_context:
        evidence_gaps.append("Provide sitemap or site-page context before finalising internal links and category coverage.")
    if resolved_mode == "improve":
        evidence_gaps.append("Existing-page extraction was not supplied; classify each proposed section as keep, strengthen, or add after page review.")

    result: dict[str, Any] = {
        "cache_type": "content-brief",
        "generated_at": now_iso(),
        "status": "ready" if competitors and site_context else "research_required",
        "target": target,
        "mode": resolved_mode,
        "primary_keyword": keyword,
        "page_type": resolved_type,
        "search_intent": intent,
        "serp_format": serp_format,
        "target_audience": "Readers matching the query intent; refine with first-party customer and conversion data.",
        "h1": title_case_keyword(keyword),
        "url_slug": slugify(keyword),
        "target_word_count": baseline,
        "competitor_average_words": avg,
        "competitors": serialize_competitors(competitors),
        "competitors_parsed": competitors,
        "content_gaps": build_gaps(competitors),
        "outline": outline,
        "meta": {"title": fit_title(keyword), "description": fit_description(keyword)},
        "information_gain": (
            f"Add one first-party benchmark or anonymised case study for {keyword}, including the method, sample, date, "
            "measured outcome and limitations. Pair it with an expert explanation of why the result occurred; do not claim results until evidence is supplied."
        ),
        "eeat_requirements": [
            "Name an author or reviewer with credentials directly relevant to the topic.",
            "Cite current primary sources for factual, legal, financial, health, safety or technical claims.",
            "Include a last-reviewed date and a documented update owner.",
            "Use first-party examples, screenshots, process evidence or measured outcomes where available.",
            "Separate verified facts from estimates, opinion and promotional claims.",
        ],
        "internal_links": build_internal_links(site_context, resolved_type),
        "evidence_gaps": evidence_gaps,
        "recommendations": [
            "Validate search intent and page format against the current SERP before drafting.",
            "Replace every placeholder internal link with a real indexed URL.",
            "Review exact-match keyword usage after drafting; optimise placement, not repetition.",
        ],
        "outline_only": outline_only,
    }
    result["markdown"] = render_markdown(result, outline_only=outline_only)
    result.pop("competitors_parsed")
    return result


def write_artifacts(result: dict[str, Any], output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_name = "CONTENT-OUTLINE.md" if result.get("outline_only") else "CONTENT-BRIEF.md"
    report_path = output_dir / report_name
    summary_path = output_dir / "SUMMARY.json"
    report_path.write_text(result["markdown"], encoding="utf-8")
    json_payload = {key: value for key, value in result.items() if key != "markdown"}
    summary_path.write_text(json.dumps(json_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"report": str(report_path), "summary_json": str(summary_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate an evidence-aware SEO content brief")
    parser.add_argument("target", help="Existing page URL or target keyword/topic")
    parser.add_argument("--page-type", default="auto", choices=["auto", *PAGE_DEFAULTS.keys()])
    parser.add_argument("--mode", default="auto", choices=["auto", "new", "improve"])
    parser.add_argument("--competitors-json", help="Optional JSON list/object with live competitor evidence")
    parser.add_argument("--site-context-json", help="Optional JSON containing real site pages/URLs")
    parser.add_argument("--target-word-count", type=int)
    parser.add_argument("--outline-only", action="store_true")
    parser.add_argument("--output-dir", help="Artifact directory; defaults to output/content-brief-<slug>")
    parser.add_argument("--json", action="store_true", help="Print machine-readable result")
    args = parser.parse_args()
    try:
        result = generate_content_brief(
            args.target,
            page_type=args.page_type,
            mode=args.mode,
            competitors_payload=load_json(args.competitors_json),
            site_context=load_json(args.site_context_json),
            target_word_count=args.target_word_count,
            outline_only=args.outline_only,
        )
        output_dir = Path(args.output_dir) if args.output_dir else Path("output") / f"content-brief-{slugify(args.target)}"
        artifacts = write_artifacts(result, output_dir)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        payload = {"ok": False, "error": str(exc), "target": args.target}
        print(json.dumps(payload, indent=2) if args.json else f"Error: {exc}", file=sys.stderr)
        return 2
    payload = {"ok": True, "target": args.target, "status": result["status"], "artifacts": artifacts, "result": {k: v for k, v in result.items() if k != "markdown"}}
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"Content brief: {artifacts['report']}")
        print(f"Summary: {artifacts['summary_json']}")
        print(f"Status: {result['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
