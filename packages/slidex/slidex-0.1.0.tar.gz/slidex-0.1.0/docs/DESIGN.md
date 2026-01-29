# `slidex` — Design Document (Draft v0.1)

*Last updated: TBD*

See `docs/PHASES.md` for the implementation checklist and current status.

---

## 1. Mission & Vision

`slidex` is a high-performance Python library for **reading, modifying, and generating PowerPoint (`.pptx`) files**, backed by a **Rust core** for speed and correctness.

Key priorities:

* **Fast** — Rust-powered manipulation of large, complex decks
* **Practical** — Designed for *real-world business reporting workflows*
* **Pythonic** — Feels natural to Python users (pandas, notebooks, automation)
* **Robust** — Works without PowerPoint installed; pure Open XML stack
* **Composable** — Suitable for CLIs, automation, CI pipelines, and notebooks
* **Readable** — API mirrors PowerPoint’s conceptual model (Slides/Shapes/Charts)

The long-term vision:

> “The Ruff-of-PowerPoint” — a batteries-included PPTX storytelling toolchain for Python.

---

## 2. Inspiration & Prior Art

`slidex` draws from:

* **ShapeCrawler (.NET)** — strong shape-centric model on top of Open XML
* **python-pptx** — existing Python PPTX binding, but slower & lower-level
* **Astral Tooling (Ruff / uv)** — excellence in Rust-backed Python ergonomics
* **OpenXML SDK** — canonical Open XML reference
* **Pandas / DataFrames** — foundational for chart/table interop
* **LaTeX/Beamer & Reveal.js** — inspiration for template-driven slides

---

## 3. User Personas & Workflows

`slidex` is optimized for:

### 3.1 Data → Deck Pipelines

Automated reporting and dashboards:

* Financial reporting
* Business reviews
* KPI dashboards
* Board/Investor decks
* Monthly/quarterly operations reviews

### 3.2 Template-driven content

Use pre-designed PPTX templates with tokens:

```
{{quarter}}
{{revenue}}
{{lead_region}}
```

Fill via Python + DataFrame.

### 3.3 Read/Modify/Write Existing Decks

Common tasks:

* Update charts
* Update tables
* Replace images
* Fix tokens/placeholders
* Reorder / copy / merge slides

### 3.4 CI/CD & Batch processing

Running in pipelines:

```bash
slidex replace --from "{{date}}" --to "2026-01-17" deck.pptx
```

---

## 4. High-Level Architecture

`slidex` is a **two-layer system**:

```
+----------------------------------+
| Python API (pythonic)            |
|  • Presentation / Slide / Shape  |
|  • Chart / Table / Picture       |
|  • Deck & templating helpers     |
|  • Pandas integration            |
|  • CLI tools                     |
+---------------+------------------+
                |
                | PyO3 bindings
                v
+----------------------------------+
| Rust Core                        |
|  • Open XML parsing              |
|  • Slides / Shapes / Charts      |
|  • Data modification             |
|  • Embedded Excel manipulation   |
|  • ZIP packaging & serialization |
+----------------------------------+
```

### 4.1 Rust Responsibilities

* Open PPTX (ZIP)
* Parse Open XML parts
* Maintain document graph (rels, parts, masters)
* Text & token replacement
* Chart data manipulation
* Slide copy/move/merge
* Write PPTX

### 4.2 Python Responsibilities

* Surface ergonomic API
* Bind pandas for chart/table input
* Template helpers
* CLI wrapper
* Integration into notebooks & workflows

---

## 5. Core Domain Model

`slidex` mirrors PowerPoint’s conceptual objects.

### 5.1 Presentation

* Open/save PPTX
* Access `slides`
* Global text replace
* Metadata access
* Cross-presentation copy/merge

### 5.2 Slide

* Has index, layout, section
* Holds `shapes`
* Has notes
* Supports slide-level replace

### 5.3 Shape

* Strongly typed:

  * Text
  * Picture
  * Chart
  * Table
  * (Future: Media, SmartArt, Groups)

### 5.4 TextFrame

* `.text` read/write
* `.replace()`
* Later: paragraphs/runs

### 5.5 Picture

* Read metadata
* Replace image data
* Preserve bounds & relationships

### 5.6 Chart

* Title
* Type
* Categories
* Series
* Editable in PowerPoint
* Data integration from pandas

### 5.7 Table

* Cell read/write
* Add row/column (later)

---

## 6. Python API Design (Public)

Python API is designed to feel simple & discoverable:

```python
from slidex import Presentation

pres = Presentation.open("deck.pptx")

pres.replace_text("{{quarter}}", "Q1 2026")

slide = pres.slides[0]
chart = slide.shapes.find(type="chart")[0].chart

chart.title = "Revenue by Region"
chart.set_data(df, x="quarter", series=["APAC", "EMEA", "Americas"])

pres.save("updated.pptx")
```

### 6.1 Optional High-level “Deck” helpers

Above the core API, offer “storytelling helpers”:

```python
deck = slidex.Deck.from_template("corp_template.pptx")
deck.title_slide("Q1 Results", "Internal")
deck.chart_slide(...df...)

deck.save("board.pptx")
```

These are pure Python, no Rust changes required.

---

## 7. CLI Tooling (Optional but Recommended)

Command: `slidex` (similar to `ruff` / `uv`)

Examples:

```bash
slidex list deck.pptx
slidex replace deck.pptx --from "{{month}}" --to "Jan 2026"
slidex export-text deck.pptx --json
slidex render template.pptx data.yaml
```

CLI reuses Rust core for speed.

---

## 8. Rust Core Design

### 8.1 Crate Layout

```
src/
  lib.rs             # PyO3 module
  core/
    presentation.rs
    slide.rs
    shape.rs
    chart.rs
    table.rs
    text.rs
    relationships.rs
    zip.rs
    excel.rs         # for chart data
```

### 8.2 Performance Principles

* Zero-copy where possible
* Batch operations (avoid Python loops)
* Minimize Python↔Rust crossings
* Ownership managed via indices or IDs

---

## 9. Data Interop (Python + Pandas)

`chart.set_data(df, x, series=...)`

Runtime rule:

* Convert pandas → Python lists → Rust
* Rust operates on primitives (`Vec<String>`, `Vec<f64>`)

No pandas logic in Rust.

---

## 10. Error Handling & Diagnostics

### 10.1 Exception Taxonomy (Python)

* `InvalidPresentationError`
* `ShapeNotFoundError`
* `ChartTypeUnsupportedError`
* `TableDimensionsError`
* `OpenXmlError`
* `SerializationError`

### 10.2 Contextual errors

Errors should state:

* Slide index
* Shape name/type
* Chart type (if relevant)
* Operation attempted

---

## 11. MVP Scope (v0.1)

Minimum viable release:

* Open/save PPTX
* Enumerate slides/shapes
* Text read/write
* Replace text (slide/presentation)
* Picture detection + replace
* Chart read + basic data update (single series)
* Tests on:

  * Windows PowerPoint
  * Mac PowerPoint
  * Google Slides (via import)
  * LibreOffice (optional)

---

## 12. Roadmap

| Phase | Features             |
| ----- | -------------------- |
| 0.1   | core model + text    |
| 0.2   | pictures + tables v1 |
| 0.3   | charts v1            |
| 0.4   | template engine      |
| 0.5   | slide copy/merge     |
| 0.6   | CLI tooling          |
| 0.7   | docs + examples      |
| 1.0   | stable release       |

Future ideas:

* SmartArt support
* Layout inference
* “Slide recipes”
* Notebook visualization
* Export PDF (LibreOffice / Office365 bridge)
* Cloud rendering (optional)

---

## 13. Testing Strategy

Test against:

* Real corporate decks
* Multiple Office versions
* Multiple masters/layouts
* Non-English decks
* Large data charts
* Weird edge cases (e.g., missing rels)

Testing tiers:

* Rust unit tests
* Python integration tests
* Fuzz testing for XML parsing
* “Golden deck” tests (before/after comparison)

---

## 14. Principles (Cultural / Design)

* **Python-first UX**
* **Rust correctness & speed**
* **Batteries included**
* **Zero PowerPoint runtime**
* **Performance predictable**
* **Errors informative**
* **Open XML compliant**
* **Power-user escape hatches**
* **Stable core surface**

---

## 15. Open Questions (to evolve)

* Do we support in-memory streaming (BytesIO)?
* Which chart types for MVP?
* How deep do we go on formatting?
* Template engine syntax: Jinja? Tokens? YAML?
* Slide merging policy (resolve masters/layouts?)

---

# End of document
