use std::cell::RefCell;
use std::rc::Rc;

use crate::core::{package::Package, slide::SlideRef, Result};
use crate::core::xml;
use crate::core::relationships;

#[derive(Debug)]
pub struct Presentation {
    package: Rc<RefCell<Package>>,
    slide_paths: Vec<String>,
}

impl Presentation {
    pub fn open(_path: &str) -> Result<Self> {
        let package = Package::open(_path)?;
        Self::from_package(package)
    }

    pub fn from_bytes(_data: &[u8]) -> Result<Self> {
        let package = Package::from_bytes(_data)?;
        Self::from_package(package)
    }

    pub fn new() -> Result<Self> {
        let candidates = [
            "assets/blank.pptx",
            "tests/fixtures/generated/simple/title_and_content.pptx",
        ];
        for candidate in candidates {
            if std::path::Path::new(candidate).exists() {
                let package = Package::open(candidate)?;
                return Self::from_package(package);
            }
        }
        Err(crate::core::CoreError::InvalidPackage(
            "missing template PPTX for Presentation::new; run fixture generator",
        ))
    }

    pub fn save(&self, _path: &str) -> Result<()> {
        self.package.borrow().save(_path)
    }

    pub fn to_bytes(&self) -> Result<Vec<u8>> {
        self.package.borrow().to_bytes()
    }

    pub fn slides(&self) -> Result<Vec<SlideRef>> {
        Ok(self
            .slide_paths
            .iter()
            .enumerate()
            .map(|(index, path)| SlideRef::new(index, path, self.package.clone()))
            .collect())
    }

    pub fn replace_text(&mut self, _needle: &str, _replacement: &str) -> Result<usize> {
        let mut replaced = 0;
        let mut package = self.package.borrow_mut();
        for path in &self.slide_paths {
            if let Some(part) = package.get_part_mut(path) {
                let (updated, count) = xml::replace_text_all(&part.data, _needle, _replacement)?;
                part.data = updated;
                replaced += count;
            }
        }
        Ok(replaced)
    }

    pub fn add_slide(&mut self) -> Result<SlideRef> {
        let index = self.slide_paths.len() + 1;
        let slide_path = format!("ppt/slides/slide{index}.xml");
        let rel_target = format!("slides/slide{index}.xml");

        let mut package = self.package.borrow_mut();
        let template_slide = self
            .slide_paths
            .last()
            .cloned()
            .ok_or(crate::core::CoreError::InvalidPackage(
                "no template slide available",
            ))?;
        let template_rels = template_slide
            .replace("ppt/slides/", "ppt/slides/_rels/")
            .replace(".xml", ".xml.rels");

        let mut rel_id = None;
        if let Some(rels) = package.get_part_mut("ppt/_rels/presentation.xml.rels") {
            let next_id = relationships::next_relationship_id(&rels.data)?;
            rel_id = Some(next_id.clone());
            rels.data = relationships::append_relationship(&rels.data, &next_id, &rel_target)?;
        }
        if let Some(pres) = package.get_part_mut("ppt/presentation.xml") {
            let next_slide_id = xml::max_slide_id(&pres.data)?.saturating_add(1);
            let rel_id = rel_id.as_deref().unwrap_or("rId1");
            pres.data = xml::append_slide_id(&pres.data, rel_id, next_slide_id)?;
        }
        if let Some(types) = package.get_part_mut("[Content_Types].xml") {
            types.data = xml::append_content_type_override(
                &types.data,
                &format!("/ppt/slides/slide{index}.xml"),
                "application/vnd.openxmlformats-officedocument.presentationml.slide+xml",
            )?;
        }

        if let Some(template_part) = package.get_part(&template_slide) {
            let data = template_part.data.clone();
            package.insert_part(crate::core::package::Part {
                path: slide_path.clone(),
                content_type: None,
                data,
            });
        } else {
            return Err(crate::core::CoreError::MissingPart("template slide"));
        }

        if let Some(template_rels_part) = package.get_part(&template_rels) {
            let rels_data = template_rels_part.data.clone();
            let rels_path = slide_path
                .replace("ppt/slides/", "ppt/slides/_rels/")
                .replace(".xml", ".xml.rels");
            package.insert_part(crate::core::package::Part {
                path: rels_path,
                content_type: None,
                data: rels_data,
            });
        }

        self.slide_paths.push(slide_path.clone());
        Ok(SlideRef::new(index - 1, &slide_path, self.package.clone()))
    }
}

impl Presentation {
    fn from_package(package: Package) -> Result<Self> {
        let slide_paths = xml::slide_paths_from_package(&package)?;
        Ok(Self {
            package: Rc::new(RefCell::new(package)),
            slide_paths,
        })
    }
}
