use std::cell::RefCell;
use std::rc::Rc;

use crate::core::{package::Package, relationships, xml, CoreError, Result};

#[derive(Clone, Debug)]
pub struct PictureRef {
    id: u32,
    slide_path: String,
    package: Rc<RefCell<Package>>,
}

impl PictureRef {
    pub fn new(slide_path: &str, id: u32, package: Rc<RefCell<Package>>) -> Self {
        Self {
            id,
            slide_path: slide_path.to_string(),
            package,
        }
    }

    pub fn dimensions(&self) -> Result<(Option<u32>, Option<u32>)> {
        let package = self.package.borrow();
        let slide = package
            .get_part(&self.slide_path)
            .ok_or(CoreError::MissingPart("slide xml"))?;
        let info = xml::picture_info(&slide.data, self.id)?;
        Ok((info.width, info.height))
    }

    pub fn replace(&self, data: &[u8]) -> Result<()> {
        let mut package = self.package.borrow_mut();
        let slide = package
            .get_part(&self.slide_path)
            .ok_or(CoreError::MissingPart("slide xml"))?;
        let info = xml::picture_info(&slide.data, self.id)?;
        let rel_id = info
            .rel_id
            .ok_or(CoreError::InvalidPackage("missing picture relationship"))?;

        let rels_path = self
            .slide_path
            .replace("ppt/slides/", "ppt/slides/_rels/")
            .replace(".xml", ".xml.rels");
        let rels_part = package
            .get_part(&rels_path)
            .ok_or(CoreError::MissingPart("slide rels"))?;
        let rels = relationships::parse_relationships(&rels_part.data)?;
        let target = rels
            .get(&rel_id)
            .ok_or(CoreError::InvalidPackage("missing picture rel target"))?;
        let resolved = resolve_target(&self.slide_path, target);
        let part = package
            .get_part_mut(&resolved)
            .ok_or(CoreError::MissingPart("picture part"))?;
        part.data = data.to_vec();
        Ok(())
    }
}

fn resolve_target(slide_path: &str, target: &str) -> String {
    if let Some(rest) = target.strip_prefix('/') {
        return rest.to_string();
    }
    if let Some(rest) = target.strip_prefix("../") {
        return format!("ppt/{rest}");
    }
    if let Some(pos) = slide_path.rfind('/') {
        let base = &slide_path[..pos];
        return format!("{base}/{target}");
    }
    target.to_string()
}
