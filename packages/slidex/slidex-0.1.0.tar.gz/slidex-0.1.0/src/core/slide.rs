use std::cell::RefCell;
use std::rc::Rc;

use crate::core::{package::Package, shape::ShapeRef, CoreError, Result};
use crate::core::xml;

#[derive(Clone, Debug)]
pub struct SlideRef {
    index: usize,
    path: String,
    package: Rc<RefCell<Package>>,
}

impl SlideRef {
    pub fn new(index: usize, path: &str, package: Rc<RefCell<Package>>) -> Self {
        Self {
            index,
            path: path.to_string(),
            package,
        }
    }

    pub fn index(&self) -> usize {
        self.index
    }

    pub fn replace_text(&self, _needle: &str, _replacement: &str) -> Result<usize> {
        let mut package = self.package.borrow_mut();
        let part = package
            .get_part_mut(&self.path)
            .ok_or(CoreError::MissingPart("slide xml"))?;
        let (updated, count) = xml::replace_text_all(&part.data, _needle, _replacement)?;
        part.data = updated;
        Ok(count)
    }

    pub fn shapes(&self) -> Result<Vec<ShapeRef>> {
        let package = self.package.borrow();
        let part = package
            .get_part(&self.path)
            .ok_or(CoreError::MissingPart("slide xml"))?;
        let shapes = xml::parse_shapes(&part.data)?;
        Ok(shapes
            .into_iter()
            .map(|shape| ShapeRef::new(shape, &self.path, self.package.clone()))
            .collect())
    }

    pub fn path(&self) -> &str {
        &self.path
    }

    pub fn add_textbox(&self, text: &str, name: Option<&str>) -> Result<ShapeRef> {
        let mut package = self.package.borrow_mut();
        let part = package
            .get_part_mut(&self.path)
            .ok_or(CoreError::MissingPart("slide xml"))?;
        let next_id = xml::max_shape_id(&part.data)?.saturating_add(1);
        let shape_name = name.unwrap_or("TextBox");
        let updated = xml::append_text_shape(&part.data, next_id, shape_name, text)?;
        part.data = updated;
        let shapes = xml::parse_shapes(&part.data)?;
        let last = shapes
            .into_iter()
            .find(|shape| shape.id == next_id)
            .ok_or(CoreError::InvalidPackage("shape append failed"))?;
        Ok(ShapeRef::new(last, &self.path, self.package.clone()))
    }
}
