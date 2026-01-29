use std::collections::HashMap;
use std::io::Cursor;

use quick_xml::events::Event;
use quick_xml::Reader;

use crate::core::{CoreError, Result};
use crate::opc::constants::relationship_type;
use crate::core::xml::local_name;

pub fn parse_relationships(bytes: &[u8]) -> Result<HashMap<String, String>> {
    let mut reader = Reader::from_reader(Cursor::new(bytes));
    reader.config_mut().trim_text(true);
    let mut buf = Vec::new();
    let mut rels = HashMap::new();

    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(e)) | Ok(Event::Empty(e))
                if local_name(e.name().as_ref()) == b"Relationship" =>
            {
                let mut id = None;
                let mut target = None;
                for attr in e.attributes().flatten() {
                    match local_name(attr.key.as_ref()) {
                        b"Id" => id = Some(attr.unescape_value()?.to_string()),
                        b"Target" => target = Some(attr.unescape_value()?.to_string()),
                        _ => {}
                    }
                }
                if let (Some(id), Some(target)) = (id, target) {
                    rels.insert(id, target);
                }
            }
            Ok(Event::Eof) => break,
            Err(err) => return Err(CoreError::Xml(err.to_string())),
            _ => {}
        }
        buf.clear();
    }

    Ok(rels)
}

pub fn append_relationship(rels_xml: &[u8], rel_id: &str, target: &str) -> Result<Vec<u8>> {
    let xml_text = std::str::from_utf8(rels_xml)
        .map_err(|_| CoreError::InvalidPackage("rels not utf-8"))?;
    let marker = "</Relationships>";
    let insert = format!(
        "<Relationship Id=\"{rel_id}\" Type=\"{}\" Target=\"{target}\"/>",
        relationship_type::SLIDE
    );
    if let Some(pos) = xml_text.find(marker) {
        let mut out = String::with_capacity(xml_text.len() + insert.len());
        out.push_str(&xml_text[..pos]);
        out.push_str(&insert);
        out.push_str(&xml_text[pos..]);
        Ok(out.into_bytes())
    } else {
        Err(CoreError::InvalidPackage("rels missing Relationships root"))
    }
}

pub fn next_relationship_id(rels_xml: &[u8]) -> Result<String> {
    let rels = parse_relationships(rels_xml)?;
    let mut max_id = 0u32;
    for key in rels.keys() {
        if let Some(num) = key.strip_prefix("rId") {
            if let Ok(value) = num.parse::<u32>() {
                max_id = max_id.max(value);
            }
        }
    }
    Ok(format!("rId{}", max_id + 1))
}
