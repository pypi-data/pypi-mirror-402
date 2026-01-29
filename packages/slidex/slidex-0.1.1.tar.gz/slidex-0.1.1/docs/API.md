# `slidex` — Python API (Public)

*Last updated: TBD*

---

## 1. Overview

This document lists the public Python classes and method signatures exposed by
`slidex`. Behavior details live in the design document; this focuses on
interfaces only.

---

## 2. Module: `slidex`

Legend:
- **Implemented (0.1)**: Wired to Rust core and working.
- **Stub (0.1)**: Present but not implemented yet.

### 2.1 Presentation

```python
class Presentation:
    @classmethod
    def open(cls, path: str) -> "Presentation":
        ...

    @classmethod
    def from_bytes(cls, data: bytes) -> "Presentation":
        ...

    @classmethod
    def new(cls) -> "Presentation":
        ...

    def save(self, path: str) -> None:
        ...

    def to_bytes(self) -> bytes:
        ...

    @property
    def slides(self) -> "Slides":
        ...

    def replace_text(self, needle: str, replacement: str) -> int:
        ...

    def add_slide(self) -> "Slide":
        ...
```

Status:
- **Implemented (0.1)**: `open`, `from_bytes`, `new`, `save`, `to_bytes`, `slides`, `replace_text`, `add_slide`

### 2.2 Slides

```python
class Slides:
    def __len__(self) -> int:
        ...

    def __getitem__(self, index: int) -> "Slide":
        ...

    def __iter__(self) -> "Iterator[Slide]":
        ...
```

Status:
- **Implemented (0.1)**: `__len__`, `__getitem__`, `__iter__`

### 2.3 Slide

```python
class Slide:
    @property
    def index(self) -> int:
        ...

    @property
    def shapes(self) -> "Shapes":
        ...

    def replace_text(self, needle: str, replacement: str) -> int:
        ...

    def copy_to(self, presentation: "Presentation") -> "Slide":
        ...

    def add_textbox(self, text: str, name: str | None = None) -> "Shape":
        ...
```

Status:
- **Implemented (0.1)**: `index`, `shapes`, `replace_text`, `add_textbox`
- **Stub (0.1)**: `copy_to`

### 2.4 Shapes

```python
class Shapes:
    def __len__(self) -> int:
        ...

    def __getitem__(self, index: int) -> "Shape":
        ...

    def __iter__(self) -> "Iterator[Shape]":
        ...

    def find(self, *, type: str | None = None, name: str | None = None) -> "list[Shape]":
        ...
```

Status:
- **Implemented (0.1)**: `__len__`, `__getitem__`, `__iter__`, `find`

### 2.5 Shape

```python
class Shape:
    @property
    def id(self) -> int:
        ...

    @property
    def name(self) -> str:
        ...

    @property
    def type(self) -> str:
        ...

    def as_text(self) -> "TextFrame":
        ...

    def as_picture(self) -> "Picture":
        ...

    def as_chart(self) -> "Chart":
        ...

    def as_table(self) -> "Table":
        ...
```

Status:
- **Implemented (0.1)**: `id`, `name`, `type`, `as_text`, `as_picture`
- **Stub (0.1)**: `as_chart`, `as_table`

---

## 3. Text

### 3.1 TextFrame

```python
class TextFrame:
    @property
    def text(self) -> str:
        ...

    @text.setter
    def text(self, value: str) -> None:
        ...

    def replace(self, needle: str, replacement: str) -> int:
        ...
```

Status:
- **Implemented (0.1)**: `text` (get/set), `replace`

---

## 4. Picture

### 4.1 Picture

```python
class Picture:
    @property
    def width(self) -> int:
        ...

    @property
    def height(self) -> int:
        ...

    def replace(self, data: bytes) -> None:
        ...
```

Status:
- **Implemented (0.1)**: `width`, `height` (EMU units), `replace`

---

## 5. Chart

### 5.1 Chart

```python
class Chart:
    @property
    def title(self) -> str | None:
        ...

    @title.setter
    def title(self, value: str | None) -> None:
        ...

    @property
    def chart_type(self) -> str:
        ...

    def categories(self) -> "list[str]":
        ...

    def series(self) -> "list[str]":
        ...

    def set_data(
        self,
        data: "DataFrame | Mapping[str, list[float]]",
        *,
        x: str,
        series: "list[str]",
    ) -> None:
        ...
```

Status:
- **Stub (0.1)**: all methods/properties

---

## 6. Table

### 6.1 Table

```python
class Table:
    @property
    def rows(self) -> int:
        ...

    @property
    def cols(self) -> int:
        ...

    def get(self, row: int, col: int) -> str:
        ...

    def set(self, row: int, col: int, value: str) -> None:
        ...
```

Status:
- **Stub (0.1)**: all methods/properties

---

## 7. Exceptions

```python
class SlidexError(Exception):
    ...

class InvalidPresentationError(SlidexError):
    ...

class ShapeNotFoundError(SlidexError):
    ...

class ChartTypeUnsupportedError(SlidexError):
    ...

class TableDimensionsError(SlidexError):
    ...

class OpenXmlError(SlidexError):
    ...

class SerializationError(SlidexError):
    ...
```

Status:
- **Implemented (0.1)**: exception classes are exposed; error mapping is currently generic.

---

# End of document
