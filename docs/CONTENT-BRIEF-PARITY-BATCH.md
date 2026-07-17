# Claude SEO v2.2 parity batch: content briefs

This batch adds a Codex-native `seo-content-brief` workflow to the existing Codex
SEO v1.9.6 port.

## Added

- `skills/seo-content-brief/SKILL.md`
- Page-type, keyword-placement, and competitor-filter references
- `agents/seo-content-brief.toml`
- `scripts/generate_content_brief.py`
- Deterministic runner routing and smoke-suite registration
- Installer and uninstaller registration
- Plugin, README, command, orchestrator, and count updates
- Unit tests for deterministic generation and evidence handling

## Evidence policy

The runner does not call a live SERP provider by itself and does not fabricate live
metrics. Pass verified competitor and site-context JSON to receive a validated brief.
Without those inputs, the output remains useful but is explicitly marked
`research_required`.

## Example

```bash
python scripts/generate_content_brief.py "oracle fusion scm training" \
  --page-type service \
  --competitors-json competitors.json \
  --site-context-json site-context.json \
  --json
```

## Validation

```bash
python -m pytest tests/test_content_brief.py
python -m compileall -q scripts
python scripts/run_skill_workflow.py --skill seo-content-brief "target keyword" --json
```
