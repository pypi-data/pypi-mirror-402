pub mod core;
pub mod opc;

#[cfg(feature = "python")]
mod pyo3;

#[cfg(feature = "python")]
use ::pyo3::prelude::*;
#[cfg(feature = "python")]
use ::pyo3::types::PyModule;

#[cfg(feature = "python")]
#[pymodule]
fn _core(py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    pyo3::register(py, m)
}
