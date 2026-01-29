use std::cell::RefCell;
use std::rc::Rc;

use crate::core::{chart::ChartRef, package::Package, picture::PictureRef, table::TableRef, text::TextRef};
use crate::core::xml::ShapeDescriptor;

#[derive(Clone, Debug)]
pub struct ShapeRef {
    id: u32,
    name: Option<String>,
    kind: ShapeKind,
    slide_path: String,
    package: Rc<RefCell<Package>>,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ShapeKind {
    Unknown,
    Text,
    Picture,
    Chart,
    Table,
}

impl ShapeRef {
    pub fn new(desc: ShapeDescriptor, slide_path: &str, package: Rc<RefCell<Package>>) -> Self {
        Self {
            id: desc.id,
            name: desc.name,
            kind: desc.kind,
            slide_path: slide_path.to_string(),
            package,
        }
    }

    pub fn id(&self) -> u32 {
        self.id
    }

    pub fn name(&self) -> Option<&str> {
        self.name.as_deref()
    }

    pub fn kind(&self) -> ShapeKind {
        self.kind
    }

    pub fn as_text(&self) -> Option<TextRef> {
        if self.kind == ShapeKind::Text {
            Some(TextRef::new(
                &self.slide_path,
                self.id,
                self.package.clone(),
            ))
        } else {
            None
        }
    }

    pub fn as_picture(&self) -> Option<PictureRef> {
        if self.kind == ShapeKind::Picture {
            Some(PictureRef::new(
                &self.slide_path,
                self.id,
                self.package.clone(),
            ))
        } else {
            None
        }
    }

    pub fn as_chart(&self) -> Option<ChartRef> {
        if self.kind == ShapeKind::Chart {
            Some(ChartRef { id: self.id })
        } else {
            None
        }
    }

    pub fn as_table(&self) -> Option<TableRef> {
        if self.kind == ShapeKind::Table {
            Some(TableRef { id: self.id })
        } else {
            None
        }
    }
}
