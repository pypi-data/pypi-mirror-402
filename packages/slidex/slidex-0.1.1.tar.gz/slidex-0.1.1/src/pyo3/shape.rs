use ::pyo3::prelude::*;
use ::pyo3::types::PyList;

use crate::core::shape::{ShapeKind, ShapeRef};
use crate::core::picture::PictureRef;
use crate::pyo3::{chart::PyChart, errors, table::PyTable, text::PyTextFrame};

#[pyclass(name = "Shapes", unsendable)]
pub struct PyShapes {
    items: Vec<ShapeRef>,
}

impl PyShapes {
    pub fn new(items: Vec<ShapeRef>) -> Self {
        Self { items }
    }
}

#[pymethods]
impl PyShapes {
    pub fn __len__(&self) -> PyResult<usize> {
        Ok(self.items.len())
    }

    pub fn __getitem__(&self, index: isize) -> PyResult<PyShape> {
        let len = self.items.len() as isize;
        let idx = if index < 0 { len + index } else { index };
        if idx < 0 || idx >= len {
            return Err(errors::not_implemented("Shapes.__getitem__ out of range"));
        }
        let shape = self.items[idx as usize].clone();
        Ok(PyShape::new(shape))
    }

    pub fn __iter__(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        let mut out = Vec::with_capacity(self.items.len());
        for shape in &self.items {
            let py_shape = Py::new(py, PyShape::new(shape.clone()))?;
            out.push(py_shape.into_any());
        }
        let list = PyList::new(py, &out)?;
        Ok(list.into_any().unbind())
    }

    #[pyo3(signature = (r#type=None, name=None))]
    pub fn find(&self, r#type: Option<&str>, name: Option<&str>) -> PyResult<Vec<PyShape>> {
        let mut out = Vec::new();
        for shape in &self.items {
            if let Some(target_name) = name {
                if shape.name().unwrap_or("") != target_name {
                    continue;
                }
            }
            if let Some(target_type) = r#type {
                if shape_type_string(shape.kind()) != target_type {
                    continue;
                }
            }
            out.push(PyShape::new(shape.clone()));
        }
        Ok(out)
    }
}

#[pyclass(name = "Shape", unsendable)]
pub struct PyShape {
    shape: ShapeRef,
}

impl PyShape {
    pub fn new(shape: ShapeRef) -> Self {
        Self { shape }
    }
}

#[pymethods]
impl PyShape {
    #[getter]
    pub fn id(&self) -> PyResult<u32> {
        Ok(self.shape.id())
    }

    #[getter]
    pub fn name(&self) -> PyResult<String> {
        Ok(self.shape.name().unwrap_or("").to_string())
    }

    #[getter]
    pub fn r#type(&self) -> PyResult<String> {
        Ok(shape_type_string(self.shape.kind()).to_string())
    }

    pub fn as_text(&self) -> PyResult<PyTextFrame> {
        let text = self
            .shape
            .as_text()
            .ok_or_else(|| errors::not_implemented("Shape.as_text"))?;
        Ok(PyTextFrame::new(text))
    }

    pub fn as_picture(&self) -> PyResult<PyPicture> {
        let picture = self
            .shape
            .as_picture()
            .ok_or_else(|| errors::not_implemented("Shape.as_picture"))?;
        Ok(PyPicture::new(picture))
    }

    pub fn as_chart(&self) -> PyResult<PyChart> {
        Err(errors::not_implemented("Shape.as_chart"))
    }

    pub fn as_table(&self) -> PyResult<PyTable> {
        Err(errors::not_implemented("Shape.as_table"))
    }
}

#[pyclass(name = "Picture", unsendable)]
pub struct PyPicture {
    picture: PictureRef,
}

impl PyPicture {
    pub fn new(picture: PictureRef) -> Self {
        Self { picture }
    }
}

#[pymethods]
impl PyPicture {
    #[getter]
    pub fn width(&self) -> PyResult<u32> {
        let (width, _) = self.picture.dimensions().map_err(errors::to_py_err)?;
        Ok(width.unwrap_or(0))
    }

    #[getter]
    pub fn height(&self) -> PyResult<u32> {
        let (_, height) = self.picture.dimensions().map_err(errors::to_py_err)?;
        Ok(height.unwrap_or(0))
    }

    pub fn replace(&self, _data: &Bound<'_, PyAny>) -> PyResult<()> {
        let bytes: Vec<u8> = _data.extract()?;
        self.picture.replace(&bytes).map_err(errors::to_py_err)
    }
}

fn shape_type_string(kind: ShapeKind) -> &'static str {
    match kind {
        ShapeKind::Text => "text",
        ShapeKind::Picture => "picture",
        ShapeKind::Chart => "chart",
        ShapeKind::Table => "table",
        ShapeKind::Unknown => "unknown",
    }
}
