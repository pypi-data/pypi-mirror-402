use ::pyo3::prelude::*;

use crate::core::text::TextRef;
use crate::pyo3::errors;

#[pyclass(name = "TextFrame", unsendable)]
pub struct PyTextFrame {
    text: TextRef,
}

impl PyTextFrame {
    pub fn new(text: TextRef) -> Self {
        Self { text }
    }
}

#[pymethods]
impl PyTextFrame {
    #[getter]
    pub fn text(&self) -> PyResult<String> {
        self.text.text().map_err(errors::to_py_err)
    }

    #[setter]
    pub fn set_text(&mut self, value: String) -> PyResult<()> {
        self.text.set_text(&value).map_err(errors::to_py_err)
    }

    pub fn replace(&self, needle: &str, replacement: &str) -> PyResult<usize> {
        self.text
            .replace(needle, replacement)
            .map_err(errors::to_py_err)
    }
}
