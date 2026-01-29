# PPTX Fixtures

This folder holds golden PPTX fixtures used for regression and integration
coverage. The structure is designed for expansion; Phase 0.1 uses only a small
subset of these.

## Layout

```
tests/fixtures/
  generated/
    simple/
  simple/
  realworld/
    quarterly_report_sanitized.pptx
    marketing_update_sanitized.pptx
  weird/
    multiple_masters.pptx
    missing_notes.pptx
    no_sldIdLst.pptx
```

## Deck intents

- `generated/simple/title_and_content.pptx`: One title slide + one content slide
  with basic text placeholders. Use for text read/write and slide enumeration.
- `generated/simple/text_only.pptx`: Single slide with multiple text boxes and
  runs. Use for replace-text coverage and edge cases (multiple runs per
  paragraph).
- `generated/simple/picture_simple.pptx`: Single slide with one embedded PNG.
  Use for picture detection and binary replace workflows.
- `generated/simple/*`: Generated via `tools/fixture_gen/generate_fixtures.py`
  using `python-pptx` (dev-only). Use for baseline fixtures that are easy to
  regenerate.
- `simple/`: Reserved for manual fixtures that should not be regenerated.
- `realworld/quarterly_report_sanitized.pptx`: Sanitized report deck with charts
  and mixed layouts. Use for end-to-end regression once charts land.
- `realworld/marketing_update_sanitized.pptx`: Sanitized deck with imagery and
  text-heavy slides. Use for picture replacement and mixed shapes.
- `weird/multiple_masters.pptx`: Deck with multiple masters and layouts. Use for
  slide traversal and master resolution.
- `weird/missing_notes.pptx`: Deck with missing notes parts. Use for resilience
  and missing rels handling.
- `weird/no_sldIdLst.pptx`: Intentionally malformed deck missing `p:sldIdLst`.
  Use for error handling in slide enumeration.
