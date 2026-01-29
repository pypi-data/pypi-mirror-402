pub mod chart;
pub mod excel;
pub mod package;
pub mod picture;
pub mod presentation;
pub mod relationships;
pub mod shape;
pub mod slide;
pub mod table;
pub mod text;
pub mod xml;
pub mod zip;

mod error;

pub use error::{CoreError, Result};
