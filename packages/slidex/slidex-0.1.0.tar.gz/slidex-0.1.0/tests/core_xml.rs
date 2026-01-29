use slidex::core::xml;

const PRESENTATION_XML: &str = r#"
<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
                xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <p:sldIdLst>
    <p:sldId id="256" r:id="rId1"/>
  </p:sldIdLst>
</p:presentation>
"#;

const RELS_XML: &str = r#"
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
                Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide"
                Target="slides/slide1.xml"/>
</Relationships>
"#;

const SLIDE_XML: &str = r#"
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
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
"#;

const SLIDE_PICTURE_XML: &str = r#"
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <p:cSld>
    <p:spTree>
      <p:pic>
        <p:nvPicPr>
          <p:cNvPr id="7" name="Picture 1"/>
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
"#;

#[test]
fn parse_slide_paths_from_xml() {
    let paths = xml::parse_slide_paths(PRESENTATION_XML.as_bytes(), RELS_XML.as_bytes()).unwrap();
    assert_eq!(paths, vec!["ppt/slides/slide1.xml".to_string()]);
}

#[test]
fn parse_shapes_finds_text_shape() {
    let shapes = xml::parse_shapes(SLIDE_XML.as_bytes()).unwrap();
    assert_eq!(shapes.len(), 1);
    let shape = &shapes[0];
    assert_eq!(shape.id, 42);
    assert_eq!(shape.name.as_deref(), Some("Title 1"));
}

#[test]
fn shape_text_read_write_replace() {
    let text = xml::shape_text(SLIDE_XML.as_bytes(), 42).unwrap();
    assert_eq!(text, "Hello {{name}}");

    let updated = xml::set_shape_text(SLIDE_XML.as_bytes(), 42, "Hello World").unwrap();
    let text = xml::shape_text(&updated, 42).unwrap();
    assert_eq!(text, "Hello World");

    let (updated, count) =
        xml::replace_text_all(SLIDE_XML.as_bytes(), "{{name}}", "Ada").unwrap();
    assert_eq!(count, 1);
    let text = xml::shape_text(&updated, 42).unwrap();
    assert_eq!(text, "Hello Ada");
}

#[test]
fn parse_shapes_finds_picture_shape() {
    let shapes = xml::parse_shapes(SLIDE_PICTURE_XML.as_bytes()).unwrap();
    assert_eq!(shapes.len(), 1);
    let shape = &shapes[0];
    assert_eq!(shape.id, 7);
    assert_eq!(shape.name.as_deref(), Some("Picture 1"));
    assert_eq!(shape.kind, slidex::core::shape::ShapeKind::Picture);
}

#[test]
fn picture_info_reads_embed_and_dimensions() {
    let info = xml::picture_info(SLIDE_PICTURE_XML.as_bytes(), 7).unwrap();
    assert_eq!(info.rel_id.as_deref(), Some("rId2"));
    assert_eq!(info.width, Some(123456));
    assert_eq!(info.height, Some(654321));
}
