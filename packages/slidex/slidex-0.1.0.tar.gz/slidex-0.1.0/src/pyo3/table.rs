use ::pyo3::prelude::*;

use crate::pyo3::errors;

#[pyclass(name = "Table", unsendable)]
pub struct PyTable {}

#[pymethods]
impl PyTable {
    #[getter]
    pub fn rows(&self) -> PyResult<usize> {
        Err(errors::not_implemented("Table.rows"))
    }

    #[getter]
    pub fn cols(&self) -> PyResult<usize> {
        Err(errors::not_implemented("Table.cols"))
    }

    pub fn get(&self, _row: usize, _col: usize) -> PyResult<String> {
        Err(errors::not_implemented("Table.get"))
    }

    pub fn set(&self, _row: usize, _col: usize, _value: &str) -> PyResult<()> {
        Err(errors::not_implemented("Table.set"))
    }
}
