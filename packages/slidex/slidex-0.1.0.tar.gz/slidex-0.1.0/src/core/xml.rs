use std::io::Cursor;

use quick_xml::events::{BytesText, Event};
use quick_xml::{Reader, Writer};

use crate::core::{package::Package, CoreError, Result};
use crate::core::relationships;

#[derive(Clone, Debug)]
pub struct ShapeDescriptor {
    pub id: u32,
    pub name: Option<String>,
    pub kind: crate::core::shape::ShapeKind,
}

#[derive(Clone, Debug)]
pub struct PictureInfo {
    pub rel_id: Option<String>,
    pub width: Option<u32>,
    pub height: Option<u32>,
}

pub fn local_name(name: &[u8]) -> &[u8] {
    if let Some(pos) = name.iter().rposition(|b| *b == b':') {
        &name[pos + 1..]
    } else {
        name
    }
}

fn is_element<N: AsRef<[u8]>>(name: N, expected: &[u8]) -> bool {
    local_name(name.as_ref()) == expected
}

pub fn slide_paths_from_package(package: &Package) -> Result<Vec<String>> {
    let pres = package
        .get_part("ppt/presentation.xml")
        .ok_or(CoreError::MissingPart("ppt/presentation.xml"))?;
    let rels = package
        .get_part("ppt/_rels/presentation.xml.rels")
        .ok_or(CoreError::MissingPart(
            "ppt/_rels/presentation.xml.rels",
        ))?;
    parse_slide_paths(&pres.data, &rels.data)
}

pub fn parse_slide_paths(presentation_xml: &[u8], rels_xml: &[u8]) -> Result<Vec<String>> {
    let relationships = relationships::parse_relationships(rels_xml)?;
    let mut reader = Reader::from_reader(Cursor::new(presentation_xml));
    reader.config_mut().trim_text(true);
    let mut buf = Vec::new();
    let mut slide_ids = Vec::new();

    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(e)) | Ok(Event::Empty(e))
                if is_element(e.name().as_ref(), b"sldId") =>
            {
                for attr in e.attributes().flatten() {
                    let value = attr.unescape_value()?.to_string();
                    if value.starts_with("rId") {
                        slide_ids.push(value);
                    }
                }
            }
            Ok(Event::Eof) => break,
            Err(err) => return Err(CoreError::Xml(err.to_string())),
            _ => {}
        }
        buf.clear();
    }

    if slide_ids.is_empty() {
        if let Ok(xml_text) = std::str::from_utf8(presentation_xml) {
            slide_ids = fallback_slide_ids(xml_text);
        }
    }

    if slide_ids.is_empty() {
        return Err(CoreError::InvalidPackage("missing p:sldIdLst"));
    }

    let mut slide_paths = Vec::new();
    for rel_id in slide_ids {
        let target = relationships
            .get(&rel_id)
            .ok_or(CoreError::InvalidPackage("missing slide rel"))?;
        let normalized = target.trim_start_matches('/');
        slide_paths.push(format!("ppt/{normalized}"));
    }

    Ok(slide_paths)
}

fn fallback_slide_ids(xml_text: &str) -> Vec<String> {
    let mut ids = Vec::new();
    for chunk in xml_text.split('<') {
        if !(chunk.starts_with("p:sldId") || chunk.starts_with("sldId")) {
            continue;
        }
        if let Some(val) = extract_attr_value(chunk, "r:id")
            .or_else(|| extract_attr_value(chunk, ":id"))
        {
            if val.starts_with("rId") {
                ids.push(val);
            }
        }
    }
    ids
}

fn extract_attr_value(input: &str, key: &str) -> Option<String> {
    let needle = format!("{key}=\"");
    let start = input.find(&needle)? + needle.len();
    let rest = &input[start..];
    let end = rest.find('"')?;
    Some(rest[..end].to_string())
}

pub fn append_slide_id(presentation_xml: &[u8], rel_id: &str, slide_id: u32) -> Result<Vec<u8>> {
    let xml_text = std::str::from_utf8(presentation_xml)
        .map_err(|_| CoreError::InvalidPackage("presentation not utf-8"))?;
    let marker = "</p:sldIdLst>";
    let insert = format!("<p:sldId id=\"{slide_id}\" r:id=\"{rel_id}\"/>");
    if let Some(pos) = xml_text.find(marker) {
        let mut out = String::with_capacity(xml_text.len() + insert.len());
        out.push_str(&xml_text[..pos]);
        out.push_str(&insert);
        out.push_str(&xml_text[pos..]);
        Ok(out.into_bytes())
    } else {
        Err(CoreError::InvalidPackage("missing p:sldIdLst"))
    }
}

pub fn max_slide_id(presentation_xml: &[u8]) -> Result<u32> {
    let mut reader = Reader::from_reader(Cursor::new(presentation_xml));
    reader.config_mut().trim_text(true);
    let mut buf = Vec::new();
    let mut max_id = 0u32;

    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(e)) | Ok(Event::Empty(e)) if is_element(e.name().as_ref(), b"sldId") => {
                for attr in e.attributes().flatten() {
                    if local_name(attr.key.as_ref()) == b"id" {
                        if let Ok(id) = attr.unescape_value()?.parse::<u32>() {
                            max_id = max_id.max(id);
                        }
                    }
                }
            }
            Ok(Event::Eof) => break,
            Err(err) => return Err(CoreError::Xml(err.to_string())),
            _ => {}
        }
        buf.clear();
    }

    Ok(max_id)
}

pub fn append_content_type_override(
    content_types_xml: &[u8],
    part_name: &str,
    content_type: &str,
) -> Result<Vec<u8>> {
    let xml_text = std::str::from_utf8(content_types_xml)
        .map_err(|_| CoreError::InvalidPackage("content types not utf-8"))?;
    let marker = "</Types>";
    let insert = format!(
        "<Override PartName=\"{part_name}\" ContentType=\"{content_type}\"/>"
    );
    if let Some(pos) = xml_text.find(marker) {
        let mut out = String::with_capacity(xml_text.len() + insert.len());
        out.push_str(&xml_text[..pos]);
        out.push_str(&insert);
        out.push_str(&xml_text[pos..]);
        Ok(out.into_bytes())
    } else {
        Err(CoreError::InvalidPackage("content types missing Types root"))
    }
}

pub fn max_shape_id(slide_xml: &[u8]) -> Result<u32> {
    let mut reader = Reader::from_reader(Cursor::new(slide_xml));
    reader.config_mut().trim_text(true);
    let mut buf = Vec::new();
    let mut max_id = 0u32;

    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(e)) | Ok(Event::Empty(e)) if is_element(e.name().as_ref(), b"cNvPr") => {
                for attr in e.attributes().flatten() {
                    if local_name(attr.key.as_ref()) == b"id" {
                        if let Ok(id) = attr.unescape_value()?.parse::<u32>() {
                            max_id = max_id.max(id);
                        }
                    }
                }
            }
            Ok(Event::Eof) => break,
            Err(err) => return Err(CoreError::Xml(err.to_string())),
            _ => {}
        }
        buf.clear();
    }

    Ok(max_id)
}

pub fn append_text_shape(slide_xml: &[u8], shape_id: u32, name: &str, text: &str) -> Result<Vec<u8>> {
    let xml_text = std::str::from_utf8(slide_xml)
        .map_err(|_| CoreError::InvalidPackage("slide not utf-8"))?;
    let marker = "</p:spTree>";
    let safe_text = escape_xml(text);
    let safe_name = escape_xml(name);
    let insert = format!(
        "<p:sp>\
<p:nvSpPr>\
<p:cNvPr id=\"{shape_id}\" name=\"{safe_name}\"/>\
<p:cNvSpPr txBox=\"1\"/>\
<p:nvPr/>\
</p:nvSpPr>\
<p:spPr>\
<a:xfrm><a:off x=\"1000000\" y=\"1000000\"/><a:ext cx=\"1000000\" cy=\"1000000\"/></a:xfrm>\
<a:prstGeom prst=\"rect\"><a:avLst/></a:prstGeom>\
<a:noFill/>\
</p:spPr>\
<p:txBody>\
<a:bodyPr wrap=\"none\"><a:spAutoFit/></a:bodyPr>\
<a:lstStyle/>\
<a:p><a:r><a:t>{safe_text}</a:t></a:r></a:p>\
</p:txBody>\
</p:sp>"
    );
    if let Some(pos) = xml_text.find(marker) {
        let mut out = String::with_capacity(xml_text.len() + insert.len());
        out.push_str(&xml_text[..pos]);
        out.push_str(&insert);
        out.push_str(&xml_text[pos..]);
        Ok(out.into_bytes())
    } else {
        Err(CoreError::InvalidPackage("missing p:spTree"))
    }
}

fn escape_xml(value: &str) -> String {
    value
        .replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('\"', "&quot;")
        .replace('\'', "&apos;")
}

pub fn parse_shapes(slide_xml: &[u8]) -> Result<Vec<ShapeDescriptor>> {
    let mut reader = Reader::from_reader(Cursor::new(slide_xml));
    reader.config_mut().trim_text(true);
    let mut buf = Vec::new();
    let mut shapes = Vec::new();
    let mut in_sp_tree = false;
    let mut depth = 0usize;

    #[derive(Default)]
    struct ShapeState {
        kind: Option<crate::core::shape::ShapeKind>,
        id: Option<u32>,
        name: Option<String>,
        has_tx_body: bool,
        graphic_uri: Option<String>,
        depth: usize,
    }

    let mut current: Option<ShapeState> = None;

    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(e)) => {
                depth += 1;
                let name = e.name().as_ref().to_vec();
                if is_element(&name, b"spTree") {
                    in_sp_tree = true;
                } else if in_sp_tree && is_element(&name, b"sp") {
                    current = Some(ShapeState {
                        kind: Some(crate::core::shape::ShapeKind::Unknown),
                        depth,
                        ..Default::default()
                    });
                } else if in_sp_tree && is_element(&name, b"pic") {
                    current = Some(ShapeState {
                        kind: Some(crate::core::shape::ShapeKind::Picture),
                        depth,
                        ..Default::default()
                    });
                } else if in_sp_tree && is_element(&name, b"graphicFrame") {
                    current = Some(ShapeState {
                        kind: Some(crate::core::shape::ShapeKind::Unknown),
                        depth,
                        ..Default::default()
                    });
                }

                if let Some(state) = current.as_mut() {
                    if is_element(&name, b"cNvPr") {
                        for attr in e.attributes().flatten() {
                            match local_name(attr.key.as_ref()) {
                                b"id" => {
                                    if let Ok(id) = attr.unescape_value()?.parse::<u32>() {
                                        state.id = Some(id);
                                    }
                                }
                                b"name" => state.name = Some(attr.unescape_value()?.to_string()),
                                _ => {}
                            }
                        }
                    } else if is_element(&name, b"txBody") {
                        state.has_tx_body = true;
                    } else if is_element(&name, b"graphicData") {
                        for attr in e.attributes().flatten() {
                            if local_name(attr.key.as_ref()) == b"uri" {
                                state.graphic_uri = Some(attr.unescape_value()?.to_string());
                            }
                        }
                    }
                }
            }
            Ok(Event::Empty(e)) => {
                let name = e.name().as_ref().to_vec();
                if let Some(state) = current.as_mut() {
                    if is_element(&name, b"cNvPr") {
                        for attr in e.attributes().flatten() {
                            match local_name(attr.key.as_ref()) {
                                b"id" => {
                                    if let Ok(id) = attr.unescape_value()?.parse::<u32>() {
                                        state.id = Some(id);
                                    }
                                }
                                b"name" => state.name = Some(attr.unescape_value()?.to_string()),
                                _ => {}
                            }
                        }
                    } else if is_element(&name, b"graphicData") {
                        for attr in e.attributes().flatten() {
                            if local_name(attr.key.as_ref()) == b"uri" {
                                state.graphic_uri = Some(attr.unescape_value()?.to_string());
                            }
                        }
                    }
                }
            }
            Ok(Event::End(e)) => {
                let name = e.name().as_ref().to_vec();
                if is_element(&name, b"spTree") {
                    in_sp_tree = false;
                }
                if let Some(state) = current.as_ref() {
                    if state.depth == depth
                        && (is_element(&name, b"sp")
                            || is_element(&name, b"pic")
                            || is_element(&name, b"graphicFrame"))
                    {
                        let mut kind = state.kind.unwrap_or(crate::core::shape::ShapeKind::Unknown);
                        if is_element(&name, b"sp") && state.has_tx_body {
                            kind = crate::core::shape::ShapeKind::Text;
                        }
                        if is_element(&name, b"graphicFrame") {
                            if let Some(uri) = &state.graphic_uri {
                                if uri.contains("chart") {
                                    kind = crate::core::shape::ShapeKind::Chart;
                                } else if uri.contains("table") {
                                    kind = crate::core::shape::ShapeKind::Table;
                                }
                            }
                        }
                        if let Some(id) = state.id {
                            shapes.push(ShapeDescriptor {
                                id,
                                name: state.name.clone(),
                                kind,
                            });
                        }
                        current = None;
                    }
                }
                if depth > 0 {
                    depth -= 1;
                }
            }
            Ok(Event::Eof) => break,
            Err(err) => return Err(CoreError::Xml(err.to_string())),
            _ => {}
        }
        buf.clear();
    }

    Ok(shapes)
}

pub fn shape_text(slide_xml: &[u8], shape_id: u32) -> Result<String> {
    let mut reader = Reader::from_reader(Cursor::new(slide_xml));
    reader.config_mut().trim_text(false);
    let mut buf = Vec::new();
    let mut text = String::new();
    let mut in_target_shape = false;
    let mut in_text = false;
    let mut shape_depth = None;
    let mut depth = 0usize;

    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(e)) => {
                depth += 1;
                let name = e.name().as_ref().to_vec();
                if is_element(&name, b"sp") || is_element(&name, b"pic") || is_element(&name, b"graphicFrame") {
                    shape_depth = Some(depth);
                    in_target_shape = false;
                }
                if shape_depth.is_some() && is_element(&name, b"cNvPr") {
                    for attr in e.attributes().flatten() {
                        if local_name(attr.key.as_ref()) == b"id" {
                            if let Ok(id) = attr.unescape_value()?.parse::<u32>() {
                                if id == shape_id {
                                    in_target_shape = true;
                                }
                            }
                        }
                    }
                }
                if in_target_shape && is_element(&name, b"t") {
                    in_text = true;
                }
            }
            Ok(Event::Empty(e)) => {
                let name = e.name().as_ref().to_vec();
                if shape_depth.is_some() && is_element(&name, b"cNvPr") {
                    for attr in e.attributes().flatten() {
                        if local_name(attr.key.as_ref()) == b"id" {
                            if let Ok(id) = attr.unescape_value()?.parse::<u32>() {
                                if id == shape_id {
                                    in_target_shape = true;
                                }
                            }
                        }
                    }
                }
            }
            Ok(Event::End(e)) => {
                let name = e.name().as_ref().to_vec();
                if in_target_shape && is_element(&name, b"t") {
                    in_text = false;
                }
                if let Some(current_depth) = shape_depth {
                    if current_depth == depth
                        && (is_element(&name, b"sp")
                            || is_element(&name, b"pic")
                            || is_element(&name, b"graphicFrame"))
                    {
                        shape_depth = None;
                        in_target_shape = false;
                    }
                }
                if depth > 0 {
                    depth -= 1;
                }
            }
            Ok(Event::Text(e)) if in_target_shape && in_text => {
                text.push_str(&e.unescape()?.to_string());
            }
            Ok(Event::Eof) => break,
            Err(err) => return Err(CoreError::Xml(err.to_string())),
            _ => {}
        }
        buf.clear();
    }

    Ok(text)
}

pub fn picture_info(slide_xml: &[u8], shape_id: u32) -> Result<PictureInfo> {
    let mut reader = Reader::from_reader(Cursor::new(slide_xml));
    reader.config_mut().trim_text(true);
    let mut buf = Vec::new();
    let mut depth = 0usize;
    let mut pic_depth = None;
    let mut xfrm_depth = None;
    let mut in_pic = false;
    let mut in_target = false;
    let mut in_xfrm = false;
    let mut rel_id = None;
    let mut width = None;
    let mut height = None;

    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(e)) => {
                depth += 1;
                let name = e.name().as_ref().to_vec();
                if is_element(&name, b"pic") {
                    in_pic = true;
                    in_target = false;
                    pic_depth = Some(depth);
                }
                if in_pic && is_element(&name, b"cNvPr") {
                    for attr in e.attributes().flatten() {
                        if local_name(attr.key.as_ref()) == b"id" {
                            if let Ok(id) = attr.unescape_value()?.parse::<u32>() {
                                if id == shape_id {
                                    in_target = true;
                                }
                            }
                        }
                    }
                }
                if in_target && is_element(&name, b"blip") {
                    for attr in e.attributes().flatten() {
                        if local_name(attr.key.as_ref()) == b"embed" {
                            rel_id = Some(attr.unescape_value()?.to_string());
                        }
                    }
                }
                if in_target && is_element(&name, b"xfrm") {
                    in_xfrm = true;
                    xfrm_depth = Some(depth);
                }
                if in_target && in_xfrm && is_element(&name, b"ext") {
                    for attr in e.attributes().flatten() {
                        match local_name(attr.key.as_ref()) {
                            b"cx" => {
                                if let Ok(value) = attr.unescape_value()?.parse::<u32>() {
                                    width = Some(value);
                                }
                            }
                            b"cy" => {
                                if let Ok(value) = attr.unescape_value()?.parse::<u32>() {
                                    height = Some(value);
                                }
                            }
                            _ => {}
                        }
                    }
                }
            }
            Ok(Event::Empty(e)) => {
                let name = e.name().as_ref().to_vec();
                if in_pic && is_element(&name, b"cNvPr") {
                    for attr in e.attributes().flatten() {
                        if local_name(attr.key.as_ref()) == b"id" {
                            if let Ok(id) = attr.unescape_value()?.parse::<u32>() {
                                if id == shape_id {
                                    in_target = true;
                                }
                            }
                        }
                    }
                }
                if in_target && is_element(&name, b"blip") {
                    for attr in e.attributes().flatten() {
                        if local_name(attr.key.as_ref()) == b"embed" {
                            rel_id = Some(attr.unescape_value()?.to_string());
                        }
                    }
                }
                if in_target && in_xfrm && is_element(&name, b"ext") {
                    for attr in e.attributes().flatten() {
                        match local_name(attr.key.as_ref()) {
                            b"cx" => {
                                if let Ok(value) = attr.unescape_value()?.parse::<u32>() {
                                    width = Some(value);
                                }
                            }
                            b"cy" => {
                                if let Ok(value) = attr.unescape_value()?.parse::<u32>() {
                                    height = Some(value);
                                }
                            }
                            _ => {}
                        }
                    }
                }
            }
            Ok(Event::End(e)) => {
                let name = e.name().as_ref().to_vec();
                if in_xfrm && is_element(&name, b"xfrm") {
                    if xfrm_depth == Some(depth) {
                        in_xfrm = false;
                        xfrm_depth = None;
                    }
                }
                if in_pic && is_element(&name, b"pic") {
                    if pic_depth == Some(depth) {
                        in_pic = false;
                        in_target = false;
                        pic_depth = None;
                    }
                }
                if depth > 0 {
                    depth -= 1;
                }
            }
            Ok(Event::Eof) => break,
            Err(err) => return Err(CoreError::Xml(err.to_string())),
            _ => {}
        }
        buf.clear();
    }

    Ok(PictureInfo {
        rel_id,
        width,
        height,
    })
}

pub fn set_shape_text(slide_xml: &[u8], shape_id: u32, value: &str) -> Result<Vec<u8>> {
    let mut reader = Reader::from_reader(Cursor::new(slide_xml));
    reader.config_mut().trim_text(false);
    let mut writer = Writer::new(Cursor::new(Vec::new()));
    let mut buf = Vec::new();
    let mut in_target_shape = false;
    let mut in_text = false;
    let mut shape_depth = None;
    let mut depth = 0usize;
    let mut replaced_any = false;

    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(e)) => {
                depth += 1;
                let name = e.name().as_ref().to_vec();
                if is_element(&name, b"sp") || is_element(&name, b"pic") || is_element(&name, b"graphicFrame") {
                    shape_depth = Some(depth);
                    in_target_shape = false;
                }
                if shape_depth.is_some() && is_element(&name, b"cNvPr") {
                    for attr in e.attributes().flatten() {
                        if local_name(attr.key.as_ref()) == b"id" {
                            if let Ok(id) = attr.unescape_value()?.parse::<u32>() {
                                if id == shape_id {
                                    in_target_shape = true;
                                }
                            }
                        }
                    }
                }
                if in_target_shape && is_element(&name, b"t") {
                    in_text = true;
                }
                writer
                    .write_event(Event::Start(e))
                    .map_err(|err| CoreError::Xml(err.to_string()))?;
            }
            Ok(Event::Empty(e)) => {
                let name = e.name().as_ref().to_vec();
                if shape_depth.is_some() && is_element(&name, b"cNvPr") {
                    for attr in e.attributes().flatten() {
                        if local_name(attr.key.as_ref()) == b"id" {
                            if let Ok(id) = attr.unescape_value()?.parse::<u32>() {
                                if id == shape_id {
                                    in_target_shape = true;
                                }
                            }
                        }
                    }
                }
                writer
                    .write_event(Event::Empty(e))
                    .map_err(|err| CoreError::Xml(err.to_string()))?;
            }
            Ok(Event::End(e)) => {
                let name = e.name().as_ref().to_vec();
                if in_target_shape && is_element(&name, b"t") {
                    in_text = false;
                }
                if let Some(current_depth) = shape_depth {
                    if current_depth == depth
                        && (is_element(&name, b"sp")
                            || is_element(&name, b"pic")
                            || is_element(&name, b"graphicFrame"))
                    {
                        shape_depth = None;
                        in_target_shape = false;
                    }
                }
                writer
                    .write_event(Event::End(e))
                    .map_err(|err| CoreError::Xml(err.to_string()))?;
                if depth > 0 {
                    depth -= 1;
                }
            }
            Ok(Event::Text(e)) => {
                if in_target_shape && in_text {
                    if !replaced_any {
                        replaced_any = true;
                        let text = BytesText::new(value);
                        writer
                            .write_event(Event::Text(text))
                            .map_err(|err| CoreError::Xml(err.to_string()))?;
                    } else {
                        let text = BytesText::new("");
                        writer
                            .write_event(Event::Text(text))
                            .map_err(|err| CoreError::Xml(err.to_string()))?;
                    }
                } else {
                    writer
                        .write_event(Event::Text(e))
                        .map_err(|err| CoreError::Xml(err.to_string()))?;
                }
            }
            Ok(Event::Eof) => break,
            Ok(event) => {
                writer
                    .write_event(event)
                    .map_err(|err| CoreError::Xml(err.to_string()))?;
            }
            Err(err) => return Err(CoreError::Xml(err.to_string())),
        }
        buf.clear();
    }

    Ok(writer.into_inner().into_inner())
}

pub fn replace_text_in_shape(
    slide_xml: &[u8],
    shape_id: u32,
    needle: &str,
    replacement: &str,
) -> Result<(Vec<u8>, usize)> {
    replace_text_with_scope(slide_xml, Some(shape_id), needle, replacement)
}

pub fn replace_text_all(
    slide_xml: &[u8],
    needle: &str,
    replacement: &str,
) -> Result<(Vec<u8>, usize)> {
    replace_text_with_scope(slide_xml, None, needle, replacement)
}

fn replace_text_with_scope(
    slide_xml: &[u8],
    shape_id: Option<u32>,
    needle: &str,
    replacement: &str,
) -> Result<(Vec<u8>, usize)> {
    let mut reader = Reader::from_reader(Cursor::new(slide_xml));
    reader.config_mut().trim_text(false);
    let mut writer = Writer::new(Cursor::new(Vec::new()));
    let mut buf = Vec::new();
    let mut in_target_shape = shape_id.is_none();
    let mut in_text = false;
    let mut shape_depth = None;
    let mut depth = 0usize;
    let mut replacements = 0usize;

    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(e)) => {
                depth += 1;
                let name = e.name().as_ref().to_vec();
                if is_element(&name, b"sp")
                    || is_element(&name, b"pic")
                    || is_element(&name, b"graphicFrame")
                {
                    shape_depth = Some(depth);
                    in_target_shape = shape_id.is_none();
                }
                if let (Some(target_id), Some(_)) = (shape_id, shape_depth) {
                    if is_element(&name, b"cNvPr") {
                        for attr in e.attributes().flatten() {
                            if local_name(attr.key.as_ref()) == b"id" {
                                if let Ok(id) = attr.unescape_value()?.parse::<u32>() {
                                    if id == target_id {
                                        in_target_shape = true;
                                    }
                                }
                            }
                        }
                    }
                }
                if in_target_shape && is_element(&name, b"t") {
                    in_text = true;
                }
                writer
                    .write_event(Event::Start(e))
                    .map_err(|err| CoreError::Xml(err.to_string()))?;
            }
            Ok(Event::Empty(e)) => {
                let name = e.name().as_ref().to_vec();
                if let (Some(target_id), Some(_)) = (shape_id, shape_depth) {
                    if is_element(&name, b"cNvPr") {
                        for attr in e.attributes().flatten() {
                            if local_name(attr.key.as_ref()) == b"id" {
                                if let Ok(id) = attr.unescape_value()?.parse::<u32>() {
                                    if id == target_id {
                                        in_target_shape = true;
                                    }
                                }
                            }
                        }
                    }
                }
                writer
                    .write_event(Event::Empty(e))
                    .map_err(|err| CoreError::Xml(err.to_string()))?;
            }
            Ok(Event::End(e)) => {
                let name = e.name().as_ref().to_vec();
                if in_target_shape && is_element(&name, b"t") {
                    in_text = false;
                }
                if let Some(current_depth) = shape_depth {
                    if current_depth == depth
                        && (is_element(&name, b"sp")
                            || is_element(&name, b"pic")
                            || is_element(&name, b"graphicFrame"))
                    {
                        shape_depth = None;
                        in_target_shape = shape_id.is_none();
                    }
                }
                writer
                    .write_event(Event::End(e))
                    .map_err(|err| CoreError::Xml(err.to_string()))?;
                if depth > 0 {
                    depth -= 1;
                }
            }
            Ok(Event::Text(e)) => {
                if in_target_shape && in_text {
                    let original = e.unescape()?.to_string();
                    let count = original.matches(needle).count();
                    if count > 0 {
                        let replaced = original.replace(needle, replacement);
                        replacements += count;
                        let text = BytesText::new(&replaced);
                        writer
                            .write_event(Event::Text(text))
                            .map_err(|err| CoreError::Xml(err.to_string()))?;
                    } else {
                        writer
                            .write_event(Event::Text(e))
                            .map_err(|err| CoreError::Xml(err.to_string()))?;
                    }
                } else {
                    writer
                        .write_event(Event::Text(e))
                        .map_err(|err| CoreError::Xml(err.to_string()))?;
                }
            }
            Ok(Event::Eof) => break,
            Ok(event) => {
                writer
                    .write_event(event)
                    .map_err(|err| CoreError::Xml(err.to_string()))?;
            }
            Err(err) => return Err(CoreError::Xml(err.to_string())),
        }
        buf.clear();
    }

    Ok((writer.into_inner().into_inner(), replacements))
}
