from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from generate_content_brief import (  # noqa: E402
    excluded_url,
    generate_content_brief,
    write_artifacts,
)


def test_keyword_mode_is_research_required_without_live_evidence() -> None:
    result = generate_content_brief("oracle fusion scm training")
    assert result["mode"] == "new"
    assert result["page_type"] == "service"
    assert result["status"] == "research_required"
    assert result["primary_keyword"] == "oracle fusion scm training"
    assert sum(section["word_count"] for section in result["outline"]) == result["target_word_count"]
    assert 50 <= len(result["meta"]["title"]) <= 60
    assert 130 <= len(result["meta"]["description"]) <= 150
    assert "Live SERP" in " ".join(result["evidence_gaps"])


def test_url_mode_is_improve_and_does_not_fetch_or_guess() -> None:
    result = generate_content_brief("https://example.com/services/technical-seo")
    assert result["mode"] == "improve"
    assert result["primary_keyword"] == "technical seo"
    assert any("Existing-page extraction" in item for item in result["evidence_gaps"])


def test_competitor_filter_and_average() -> None:
    payload = {
        "competitors": [
            {"url": "https://wikipedia.org/wiki/SEO", "word_count": 5000, "depth": 10},
            {
                "url": "https://agency.example/seo-guide",
                "word_count": 1600,
                "depth": 8,
                "formatting": 7,
                "seo": 8,
                "ux": 7,
                "h2_sections": ["Process", "Cost"],
                "main_gap": "No first-party examples",
            },
            {
                "url": "https://consulting.example/seo-playbook",
                "word_count": 1800,
                "depth": 7,
                "formatting": 8,
                "seo": 7,
                "ux": 8,
                "main_gap": "Outdated evidence",
            },
        ]
    }
    result = generate_content_brief(
        "enterprise seo consulting",
        competitors_payload=payload,
        site_context={"pages": ["https://brand.example/services", "https://brand.example/case-studies"]},
    )
    assert len(result["competitors"]) == 2
    assert result["competitor_average_words"] == 1700
    assert result["target_word_count"] == 1800
    assert result["status"] == "ready"
    assert all("wikipedia" not in item["url"] for item in result["competitors"])


def test_excluded_url_rules() -> None:
    assert excluded_url("https://reddit.com/r/seo")
    assert excluded_url("https://example.gov/guide")
    assert excluded_url("https://business.example/tag/seo")
    assert not excluded_url("https://agency.example/services/seo")


def test_artifacts_are_written_without_markdown_in_summary(tmp_path: Path) -> None:
    result = generate_content_brief("content strategy")
    artifacts = write_artifacts(result, tmp_path)
    report = Path(artifacts["report"])
    summary = Path(artifacts["summary_json"])
    assert report.exists()
    assert summary.exists()
    payload = json.loads(summary.read_text(encoding="utf-8"))
    assert "markdown" not in payload
    assert "Content Brief" in report.read_text(encoding="utf-8")
