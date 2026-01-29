use std::cell::RefCell;
use std::rc::Rc;

use crate::core::{package::Package, Result};
use crate::core::xml;

#[derive(Clone, Debug)]
pub struct TextRef {
    slide_path: String,
    shape_id: u32,
    package: Rc<RefCell<Package>>,
}

impl TextRef {
    pub fn new(slide_path: &str, shape_id: u32, package: Rc<RefCell<Package>>) -> Self {
        Self {
            slide_path: slide_path.to_string(),
            shape_id,
            package,
        }
    }

    pub fn text(&self) -> Result<String> {
        let package = self.package.borrow();
        let part = package
            .get_part(&self.slide_path)
            .ok_or(crate::core::CoreError::MissingPart("slide xml"))?;
        xml::shape_text(&part.data, self.shape_id)
    }

    pub fn set_text(&self, value: &str) -> Result<()> {
        let mut package = self.package.borrow_mut();
        let part = package
            .get_part_mut(&self.slide_path)
            .ok_or(crate::core::CoreError::MissingPart("slide xml"))?;
        let updated = xml::set_shape_text(&part.data, self.shape_id, value)?;
        part.data = updated;
        Ok(())
    }

    pub fn replace(&self, needle: &str, replacement: &str) -> Result<usize> {
        let mut package = self.package.borrow_mut();
        let part = package
            .get_part_mut(&self.slide_path)
            .ok_or(crate::core::CoreError::MissingPart("slide xml"))?;
        let (updated, count) =
            xml::replace_text_in_shape(&part.data, self.shape_id, needle, replacement)?;
        part.data = updated;
        Ok(count)
    }
}
