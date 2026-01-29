# slidex

Rust-backed Python library for reading, modifying, and generating PowerPoint
(`.pptx`) files.

## Status

Early development. APIs may change.

## What it does (today)

- Open and save PPTX files
- Enumerate slides and shapes
- Read/write text frames
- Replace text across a slide or presentation

## Install (from source)

slidex is not published yet. Install from source with:

```bash
uv venv
uv pip install maturin
uv run maturin develop
```

## Usage

Basic read/modify/write flow:

```python
from slidex import Presentation

pres = Presentation.open("deck.pptx")
pres.replace_text("{{quarter}}", "Q1 2026")

slide = pres.slides[0]
shape = slide.shapes[0]
text = shape.as_text()
text.text = "Hello from slidex"

pres.save("updated.pptx")
```

Create a new deck from scratch:

```python
from slidex import Presentation

pres = Presentation.new()
slide = pres.add_slide()
slide.add_textbox("Hello from slidex")
pres.save("new_deck.pptx")
```

## Documentation

- `docs/DESIGN.md`
- `docs/ARCHITECTURE.md`
- `docs/API.md`

## Contributing

See `CONTRIBUTING.md` for developer setup, tests, and fixture tooling.
