from typing import Iterator, Mapping

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

class Slides:
    def __len__(self) -> int:
        ...

    def __getitem__(self, index: int) -> "Slide":
        ...

    def __iter__(self) -> Iterator["Slide"]:
        ...

class Slide:
    @property
    def index(self) -> int:
        ...

    @property
    def shapes(self) -> "Shapes":
        ...

    def replace_text(self, needle: str, replacement: str) -> int:
        ...

    def copy_to(self, presentation: Presentation) -> "Slide":
        ...

    def add_textbox(self, text: str, name: str | None = None) -> "Shape":
        ...

class Shapes:
    def __len__(self) -> int:
        ...

    def __getitem__(self, index: int) -> "Shape":
        ...

    def __iter__(self) -> Iterator["Shape"]:
        ...

    def find(self, *, type: str | None = None, name: str | None = None) -> list["Shape"]:
        ...

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

class TextFrame:
    @property
    def text(self) -> str:
        ...

    @text.setter
    def text(self, value: str) -> None:
        ...

    def replace(self, needle: str, replacement: str) -> int:
        ...

class Picture:
    @property
    def width(self) -> int:
        ...

    @property
    def height(self) -> int:
        ...

    def replace(self, data: bytes) -> None:
        ...

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

    def categories(self) -> list[str]:
        ...

    def series(self) -> list[str]:
        ...

    def set_data(self, data: "DataFrame | Mapping[str, list[float]]", *, x: str, series: list[str]) -> None:
        ...

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

class DataFrame:
    ...

__all__: list[str]
