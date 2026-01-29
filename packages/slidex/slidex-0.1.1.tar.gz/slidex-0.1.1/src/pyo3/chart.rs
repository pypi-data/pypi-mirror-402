use ::pyo3::prelude::*;

use crate::pyo3::errors;

#[pyclass(name = "Chart", unsendable)]
pub struct PyChart {}

#[pymethods]
impl PyChart {
    #[getter]
    pub fn title(&self) -> PyResult<Option<String>> {
        Err(errors::not_implemented("Chart.title"))
    }

    #[setter]
    pub fn set_title(&mut self, _value: Option<String>) -> PyResult<()> {
        Err(errors::not_implemented("Chart.title"))
    }

    #[getter]
    pub fn chart_type(&self) -> PyResult<String> {
        Err(errors::not_implemented("Chart.chart_type"))
    }

    pub fn categories(&self) -> PyResult<Vec<String>> {
        Err(errors::not_implemented("Chart.categories"))
    }

    pub fn series(&self) -> PyResult<Vec<String>> {
        Err(errors::not_implemented("Chart.series"))
    }

    pub fn set_data(&self, _data: &Bound<'_, PyAny>, _x: &str, _series: Vec<String>) -> PyResult<()> {
        Err(errors::not_implemented("Chart.set_data"))
    }
}
