use std::collections::HashMap;
use std::io::{Cursor, Read, Write};

use quick_xml::events::Event;
use quick_xml::Reader;
use zip::write::FileOptions;
use zip::ZipArchive;
use zip::ZipWriter;

use crate::core::{CoreError, Result};

#[derive(Debug, Clone)]
pub struct Part {
    pub path: String,
    pub content_type: Option<String>,
    pub data: Vec<u8>,
}

#[derive(Debug, Default)]
struct ContentTypes {
    overrides: HashMap<String, String>,
    defaults: HashMap<String, String>,
}

impl ContentTypes {
    fn content_type_for(&self, path: &str) -> Option<String> {
        if let Some(value) = self.overrides.get(path) {
            return Some(value.clone());
        }
        let ext = path.rsplit('.').next()?;
        self.defaults.get(ext).cloned()
    }

    fn from_xml(bytes: &[u8]) -> Result<Self> {
        let mut reader = Reader::from_reader(Cursor::new(bytes));
        reader.config_mut().trim_text(true);
        let mut buf = Vec::new();
        let mut content_types = ContentTypes::default();

        loop {
            match reader.read_event_into(&mut buf) {
                Ok(Event::Start(e)) if e.name().as_ref().ends_with(b"Override") => {
                    let mut part_name = None;
                    let mut content_type = None;
                    for attr in e.attributes().flatten() {
                        match attr.key.as_ref() {
                            b"PartName" => part_name = Some(attr.unescape_value()?.to_string()),
                            b"ContentType" => {
                                content_type = Some(attr.unescape_value()?.to_string())
                            }
                            _ => {}
                        }
                    }
                    if let (Some(name), Some(ctype)) = (part_name, content_type) {
                        let normalized = name.trim_start_matches('/').to_string();
                        content_types.overrides.insert(normalized, ctype);
                    }
                }
                Ok(Event::Start(e)) if e.name().as_ref().ends_with(b"Default") => {
                    let mut extension = None;
                    let mut content_type = None;
                    for attr in e.attributes().flatten() {
                        match attr.key.as_ref() {
                            b"Extension" => extension = Some(attr.unescape_value()?.to_string()),
                            b"ContentType" => {
                                content_type = Some(attr.unescape_value()?.to_string())
                            }
                            _ => {}
                        }
                    }
                    if let (Some(ext), Some(ctype)) = (extension, content_type) {
                        content_types.defaults.insert(ext, ctype);
                    }
                }
                Ok(Event::Eof) => break,
                Err(err) => return Err(CoreError::Xml(err.to_string())),
                _ => {}
            }
            buf.clear();
        }

        Ok(content_types)
    }
}

#[derive(Debug, Default)]
pub struct Package {
    parts: HashMap<String, Part>,
}

impl Package {
    pub fn new(parts: HashMap<String, Part>) -> Self {
        Self { parts }
    }

    pub fn open(path: &str) -> Result<Self> {
        let bytes = std::fs::read(path)?;
        Self::from_bytes(&bytes)
    }

    pub fn from_bytes(bytes: &[u8]) -> Result<Self> {
        let cursor = Cursor::new(bytes);
        let mut archive = ZipArchive::new(cursor)?;

        let mut types_bytes = Vec::new();
        {
            let mut types_file = archive
                .by_name("[Content_Types].xml")
                .map_err(|_| CoreError::MissingPart("[Content_Types].xml"))?;
            types_file.read_to_end(&mut types_bytes)?;
        }
        let content_types = ContentTypes::from_xml(&types_bytes)?;

        let mut parts = HashMap::new();
        for i in 0..archive.len() {
            let mut file = archive.by_index(i)?;
            if file.is_dir() {
                continue;
            }
            let mut data = Vec::new();
            file.read_to_end(&mut data)?;
            let path = file.name().to_string();
            let content_type = content_types.content_type_for(&path);
            parts.insert(
                path.clone(),
                Part {
                    path,
                    content_type,
                    data,
                },
            );
        }

        Ok(Self { parts })
    }

    pub fn get_part(&self, path: &str) -> Option<&Part> {
        self.parts.get(path)
    }

    pub fn get_part_mut(&mut self, path: &str) -> Option<&mut Part> {
        self.parts.get_mut(path)
    }

    pub fn insert_part(&mut self, part: Part) {
        self.parts.insert(part.path.clone(), part);
    }

    pub fn parts(&self) -> impl Iterator<Item = &Part> {
        self.parts.values()
    }

    pub fn save(&self, path: &str) -> Result<()> {
        let bytes = self.to_bytes()?;
        std::fs::write(path, bytes)?;
        Ok(())
    }

    pub fn to_bytes(&self) -> Result<Vec<u8>> {
        let mut cursor = Cursor::new(Vec::new());
        let mut writer = ZipWriter::new(&mut cursor);
        let options = FileOptions::<()>::default();

        for part in self.parts.values() {
            writer.start_file(&part.path, options)?;
            writer.write_all(&part.data)?;
        }

        writer.finish()?;
        Ok(cursor.into_inner())
    }
}
