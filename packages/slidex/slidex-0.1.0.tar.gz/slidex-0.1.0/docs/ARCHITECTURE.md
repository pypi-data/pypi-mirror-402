# `slidex` — Architecture (Rust + PyO3 Internals)

*Last updated: TBD*

---

## 1. Scope

This document describes the internal Rust core and its PyO3 bridge. It excludes
public API design, CLI UX, or product roadmap details.

---

## 2. Crate Structure

```
src/
  lib.rs
  pyo3/
    errors.rs
    presentation.rs
    slide.rs
    shape.rs
    chart.rs
    table.rs
    text.rs
  core/
    presentation.rs
    slide.rs
    shape.rs
    chart.rs
    table.rs
    text.rs
    relationships.rs
    zip.rs
    excel.rs
    xml.rs
```

### 2.1 Layers

* `core/` contains all PPTX/Open XML logic with no Python dependency.
* `pyo3/` exposes Python classes and translates arguments, errors, and results.
* `lib.rs` wires the module, types, and exceptions.

---

## 3. Data Model (Rust)

### 3.1 Presentation

* Owns the ZIP container and the in-memory XML parts.
* Maintains a parts graph (rels + part IDs + content types).
* Provides slide ordering, master/layout discovery, and part resolution.

### 3.2 Slide

* Holds a reference to slide XML and related part IDs.
* Exposes shape traversal and slide-level operations (text replace, copy).

### 3.3 Shape

* Parsed into a typed enum with a stable `shape_id`.
* Variants: `Text`, `Picture`, `Chart`, `Table`.
* Each variant stores references to its relevant XML nodes/parts.

### 3.4 Chart + Embedded Excel

* Chart XML part (`chartX.xml`) is bound to an embedded workbook.
* `excel.rs` edits the embedded worksheet data for category/series values.
* On update, both chart XML caches and workbook data are refreshed.

---

## 4. XML + Parts Management

### 4.1 Parsing Strategy

* Read all XML parts via `zip.rs` into a `HashMap<PartId, XmlDoc>`.
* `xml.rs` provides lightweight utilities to find/replace nodes and attributes.
* Keep stable element paths for common operations (text runs, chart series).

### 4.2 Relationships Graph

* `relationships.rs` maps each part to its relationship targets.
* Resolves `rId` links from slides to images, charts, and layouts.

### 4.3 Serialization

* Writes modified XML back into the ZIP container.
* Preserves unmodified parts verbatim to avoid churn.

---

## 5. PyO3 Bridge

### 5.1 Module Layout

* `lib.rs` defines the Python module and registers exceptions.
* Each Python-facing class is a thin wrapper around a `core` handle.

### 5.2 Lifetime + Ownership Model

* `Presentation` owns the Rust core object and is the root of the graph.
* `Slide` and `Shape` wrappers hold indices or IDs into `Presentation`.
* Avoid storing direct references in PyO3 wrappers to reduce borrow issues.

### 5.3 Crossing the FFI Boundary

* Batch operations stay in Rust (e.g., replace all text across slides).
* Use simple types across the boundary: `String`, `Vec<String>`, `Vec<f64>`.
* Convert pandas data in Python before calling Rust.

### 5.4 Error Mapping

* Rust errors implement a core error enum.
* `pyo3/errors.rs` maps to Python exceptions with context (slide index, shape).

---

## 6. Concurrency + Performance

* Prefer immutable reads with interior mutability where needed.
* Use indices/IDs for stable references to shapes and parts.
* Avoid repeated XML parsing by caching DOMs per part.
* Minimize Python calls in hot paths by exposing batch operations.

---

## 7. Internal APIs (Rust)

### 7.1 Presentation API (core)

* `open(path) -> Presentation`
* `save(path)`
* `slides() -> Vec<SlideRef>`
* `replace_text(from, to)`

### 7.2 Slide API (core)

* `shapes() -> Vec<ShapeRef>`
* `replace_text(from, to)`
* `copy_to(pres)`

### 7.3 Shape API (core)

* `as_text() / as_picture() / as_chart() / as_table()`
* `shape_id()`

---

## 8. Rust <-> Python Type Mapping

| Rust                        | Python                |
| --------------------------- | --------------------- |
| `Presentation`              | `slidex.Presentation` |
| `SlideRef` + `Presentation` | `slidex.Slide`         |
| `ShapeRef` + `Presentation` | `slidex.Shape`         |
| `Vec<String>`               | `list[str]`           |
| `Vec<f64>`                  | `list[float]`         |

---

## 9. Error Surfaces

* `OpenXmlError` for malformed XML/relationships.
* `ShapeNotFoundError` for invalid IDs or mismatched types.
* `SerializationError` for ZIP or write failures.

All errors should provide enough context to locate the failing slide/shape.

---

## 10. Future Extensions (Internal)

* Add shape groups and SmartArt by expanding the shape enum.
* Centralize XML selectors for format stability across PowerPoint versions.
* Optional streaming mode for large decks (requires part paging).

---

# End of document
