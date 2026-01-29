from __future__ import annotations

import io
import zipfile

import slidex


def build_minimal_pptx() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "[Content_Types].xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Override PartName="/ppt/presentation.xml"
            ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slides/slide1.xml"
            ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
  <Override PartName="/ppt/_rels/presentation.xml.rels"
            ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
</Types>
""",
        )
        zf.writestr(
            "ppt/presentation.xml",
            """<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
                xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <p:sldIdLst>
    <p:sldId id="256" r:id="rId1"/>
  </p:sldIdLst>
</p:presentation>
""",
        )
        zf.writestr(
            "ppt/_rels/presentation.xml.rels",
            """<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
                Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide"
                Target="slides/slide1.xml"/>
</Relationships>
""",
        )
        zf.writestr(
            "ppt/slides/slide1.xml",
            """<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:cSld>
    <p:spTree>
      <p:sp>
        <p:nvSpPr>
          <p:cNvPr id="42" name="Title 1"/>
        </p:nvSpPr>
        <p:txBody>
          <a:p>
            <a:r><a:t>Hello {{name}}</a:t></a:r>
          </a:p>
        </p:txBody>
      </p:sp>
    </p:spTree>
  </p:cSld>
</p:sld>
""",
        )
    return buf.getvalue()


def test_open_from_bytes_and_enumerate():
    pres = slidex.Presentation.from_bytes(build_minimal_pptx())
    assert len(pres.slides) == 1
    slide = pres.slides[0]
    assert slide.index == 0
    shapes = slide.shapes
    assert len(shapes) == 1
    shape = shapes[0]
    assert shape.id == 42
    assert shape.type == "text"


def test_textframe_read_write_and_replace():
    pres = slidex.Presentation.from_bytes(build_minimal_pptx())
    shape = pres.slides[0].shapes[0]
    text = shape.as_text()
    assert text.text == "Hello {{name}}"
    text.text = "Hello World"
    assert text.text == "Hello World"
    count = text.replace("World", "Ada")
    assert count == 1
    assert text.text == "Hello Ada"


def test_presentation_replace_text():
    pres = slidex.Presentation.from_bytes(build_minimal_pptx())
    count = pres.replace_text("{{name}}", "Ada")
    assert count == 1
    assert pres.slides[0].shapes[0].as_text().text == "Hello Ada"
