# `slidex` Phases Checklist

## Phase 0.1 (Core text + minimal authoring)

**Done**
- [x] Open/save PPTX (`Presentation.open`, `Presentation.save`)
- [x] Enumerate slides/shapes (`Presentation.slides`, `Slide.shapes`)
- [x] TextFrame read/write (`TextFrame.text`, `Shape.text_frame`)
- [x] Global text replace (`Presentation.replace_text`)
- [x] Slide/shape text replace (`Slide.replace_text`, `Shape.replace_text`)
- [x] Picture detection + replace (`src/core/shape.rs`, `src/core/relationships.rs`, `src/core/presentation.rs`, `src/pyo3/shape.rs`)
- [x] Basic Python API surface aligned to `docs/API.md`
- [x] Minimal creation flow (`Presentation.new`, `Presentation.add_slide`, `Slide.add_textbox`)
- [x] Core ZIP/package + XML parsing (`Package`, relationships, content types)
- [x] Fixtures tooling + baseline comparison script
- [x] Unit tests + Python tests scaffolded/passing

**Remaining**
- [ ] Chart read + basic data update (`src/core/chart.rs`, `src/core/xml.rs`, `src/core/excel.rs`, `src/pyo3/chart.rs`)
- [ ] Table cell read/write (`src/core/table.rs`, `src/core/xml.rs`, `src/pyo3/table.rs`)
- [ ] Error taxonomy coverage + contextual errors (`src/core/error.rs`, `src/pyo3/errors.rs`)
- [ ] 3–4 simple golden decks + golden tests (`tests/fixtures`, `tools/fixture_gen`, `tools/fixture_compare`)
- [ ] Compatibility sanity checks (PowerPoint Mac/Win; optional: Google Slides, LibreOffice)

## Phase 0.2 (Pictures + tables v1)

**Planned**
- [ ] Picture metadata expansion (crop, offset, rotation) in `src/core/xml.rs`
- [ ] Picture dimension helpers in `src/core/picture.rs`
- [ ] Table read/write: cell access in `src/core/table.rs`
- [ ] PyO3 bridge: `src/pyo3/shape.rs`, `src/pyo3/table.rs`, `src/pyo3/picture.rs`
- [ ] Tests + fixtures: add picture/table decks and golden comparisons

## Phase 0.3 (Charts v1)

**Planned**
- [ ] Core shape parsing: chart detection in `src/core/shape.rs`
- [ ] Core XML ops: chart nodes/series in `src/core/xml.rs`
- [ ] Chart model: read/write in `src/core/chart.rs`
- [ ] Embedded workbook: update data in `src/core/excel.rs`
- [ ] Relationships: resolve chart + workbook parts in `src/core/relationships.rs`
- [ ] PyO3 bridge: `src/pyo3/chart.rs` and shape metadata updates
- [ ] Tests + fixtures: add chart decks and golden comparisons
