from __future__ import annotations

import base64
import io
import zipfile

import slidex

PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMB/axh3qkAAAAASUVORK5CYII="
)


def build_picture_pptx() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "[Content_Types].xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="png" ContentType="image/png"/>
  <Override PartName="/ppt/presentation.xml"
            ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slides/slide1.xml"
            ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
  <Override PartName="/ppt/_rels/presentation.xml.rels"
            ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Override PartName="/ppt/slides/_rels/slide1.xml.rels"
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
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <p:cSld>
    <p:spTree>
      <p:pic>
        <p:nvPicPr>
          <p:cNvPr id="7" name="Picture 1"/>
          <p:cNvPicPr/>
          <p:nvPr/>
        </p:nvPicPr>
        <p:blipFill>
          <a:blip r:embed="rId2"/>
        </p:blipFill>
        <p:spPr>
          <a:xfrm>
            <a:ext cx="123456" cy="654321"/>
          </a:xfrm>
        </p:spPr>
      </p:pic>
    </p:spTree>
  </p:cSld>
</p:sld>
""",
        )
        zf.writestr(
            "ppt/slides/_rels/slide1.xml.rels",
            """<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId2"
                Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
                Target="../media/image1.png"/>
</Relationships>
""",
        )
        zf.writestr("ppt/media/image1.png", PNG_1X1)
    return buf.getvalue()


def test_picture_replace_updates_media_part():
    pres = slidex.Presentation.from_bytes(build_picture_pptx())
    shape = pres.slides[0].shapes[0]
    assert shape.type == "picture"
    picture = shape.as_picture()
    assert picture.width == 123456
    assert picture.height == 654321

    new_bytes = b"new-image-bytes"
    picture.replace(new_bytes)

    out = pres.to_bytes()
    with zipfile.ZipFile(io.BytesIO(out), "r") as zf:
        assert zf.read("ppt/media/image1.png") == new_bytes
