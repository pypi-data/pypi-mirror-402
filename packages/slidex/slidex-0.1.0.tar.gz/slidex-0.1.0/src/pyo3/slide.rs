use ::pyo3::prelude::*;
use ::pyo3::types::PyList;

use crate::core::slide::SlideRef;
use crate::pyo3::{errors, shape::PyShapes};

#[pyclass(name = "Slides", unsendable)]
pub struct PySlides {
    items: Vec<SlideRef>,
}

impl PySlides {
    pub fn new(items: Vec<SlideRef>) -> Self {
        Self { items }
    }
}

#[pymethods]
impl PySlides {
    pub fn __len__(&self) -> PyResult<usize> {
        Ok(self.items.len())
    }

    pub fn __getitem__(&self, index: isize) -> PyResult<PySlide> {
        let len = self.items.len() as isize;
        let idx = if index < 0 { len + index } else { index };
        if idx < 0 || idx >= len {
            return Err(errors::not_implemented("Slides.__getitem__ out of range"));
        }
        let slide = self.items[idx as usize].clone();
        Ok(PySlide::new(slide))
    }

    pub fn __iter__(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        let mut out = Vec::with_capacity(self.items.len());
        for slide in &self.items {
            let py_slide = Py::new(py, PySlide::new(slide.clone()))?;
            out.push(py_slide.into_any());
        }
        let list = PyList::new(py, &out)?;
        Ok(list.into_any().unbind())
    }
}

#[pyclass(name = "Slide", unsendable)]
pub struct PySlide {
    slide: SlideRef,
}

impl PySlide {
    pub fn new(slide: SlideRef) -> Self {
        Self { slide }
    }
}

#[pymethods]
impl PySlide {
    #[getter]
    pub fn index(&self) -> PyResult<usize> {
        Ok(self.slide.index())
    }

    #[getter]
    pub fn shapes(&self) -> PyResult<PyShapes> {
        let shapes = self.slide.shapes().map_err(errors::to_py_err)?;
        Ok(PyShapes::new(shapes))
    }

    pub fn replace_text(&self, needle: &str, replacement: &str) -> PyResult<usize> {
        self.slide
            .replace_text(needle, replacement)
            .map_err(errors::to_py_err)
    }

    pub fn copy_to(&self, _presentation: &Bound<'_, PyAny>) -> PyResult<PySlide> {
        Err(errors::not_implemented("Slide.copy_to"))
    }

    #[pyo3(signature = (text, name=None))]
    pub fn add_textbox(
        &self,
        text: &str,
        name: Option<&str>,
    ) -> PyResult<crate::pyo3::shape::PyShape> {
        let shape = self
            .slide
            .add_textbox(text, name)
            .map_err(errors::to_py_err)?;
        Ok(crate::pyo3::shape::PyShape::new(shape))
    }
}
