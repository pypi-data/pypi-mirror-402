use ::pyo3::prelude::*;
use ::pyo3::types::{PyModule, PyModuleMethods};

pub mod chart;
pub mod errors;
pub mod presentation;
pub mod shape;
pub mod slide;
pub mod table;
pub mod text;

pub fn register(py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<presentation::PyPresentation>()?;
    m.add_class::<slide::PySlides>()?;
    m.add_class::<slide::PySlide>()?;
    m.add_class::<shape::PyShapes>()?;
    m.add_class::<shape::PyShape>()?;
    m.add_class::<text::PyTextFrame>()?;
    m.add_class::<shape::PyPicture>()?;
    m.add_class::<chart::PyChart>()?;
    m.add_class::<table::PyTable>()?;
    errors::register(py, m)?;
    Ok(())
}
