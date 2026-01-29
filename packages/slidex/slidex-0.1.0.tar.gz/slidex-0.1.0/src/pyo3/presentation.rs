use ::pyo3::prelude::*;
use ::pyo3::types::{PyBytes, PyType};

use crate::core;
use crate::pyo3::{errors, slide::PySlides};

#[pyclass(name = "Presentation", unsendable)]
pub struct PyPresentation {
    core: core::presentation::Presentation,
}

#[pymethods]
impl PyPresentation {
    #[classmethod]
    pub fn open(_cls: &Bound<'_, PyType>, path: &str) -> PyResult<Self> {
        let core = core::presentation::Presentation::open(path).map_err(errors::to_py_err)?;
        Ok(Self { core })
    }

    #[classmethod]
    pub fn from_bytes(_cls: &Bound<'_, PyType>, data: &Bound<'_, PyBytes>) -> PyResult<Self> {
        let core = core::presentation::Presentation::from_bytes(data.as_bytes())
            .map_err(errors::to_py_err)?;
        Ok(Self { core })
    }

    #[classmethod]
    pub fn new(_cls: &Bound<'_, PyType>) -> PyResult<Self> {
        let core = core::presentation::Presentation::new().map_err(errors::to_py_err)?;
        Ok(Self { core })
    }

    pub fn save(&self, path: &str) -> PyResult<()> {
        self.core.save(path).map_err(errors::to_py_err)
    }

    pub fn to_bytes<'py>(&self, py: Python<'py>) -> PyResult<Py<PyBytes>> {
        let bytes = self.core.to_bytes().map_err(errors::to_py_err)?;
        Ok(PyBytes::new(py, &bytes).into())
    }

    #[getter]
    pub fn slides(&self) -> PyResult<PySlides> {
        let slides = self.core.slides().map_err(errors::to_py_err)?;
        Ok(PySlides::new(slides))
    }

    pub fn replace_text(&mut self, needle: &str, replacement: &str) -> PyResult<usize> {
        self.core
            .replace_text(needle, replacement)
            .map_err(errors::to_py_err)
    }

    pub fn add_slide(&mut self) -> PyResult<crate::pyo3::slide::PySlide> {
        let slide = self.core.add_slide().map_err(errors::to_py_err)?;
        Ok(crate::pyo3::slide::PySlide::new(slide))
    }
}
