use ::pyo3::exceptions::PyException;
use ::pyo3::prelude::*;
use ::pyo3::types::{PyModule, PyModuleMethods};

use crate::core::CoreError;

::pyo3::create_exception!(slidex, SlidexError, PyException);
::pyo3::create_exception!(slidex, InvalidPresentationError, SlidexError);
::pyo3::create_exception!(slidex, ShapeNotFoundError, SlidexError);
::pyo3::create_exception!(slidex, ChartTypeUnsupportedError, SlidexError);
::pyo3::create_exception!(slidex, TableDimensionsError, SlidexError);
::pyo3::create_exception!(slidex, OpenXmlError, SlidexError);
::pyo3::create_exception!(slidex, SerializationError, SlidexError);

pub fn register(py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("SlidexError", py.get_type::<SlidexError>())?;
    m.add("InvalidPresentationError", py.get_type::<InvalidPresentationError>())?;
    m.add("ShapeNotFoundError", py.get_type::<ShapeNotFoundError>())?;
    m.add("ChartTypeUnsupportedError", py.get_type::<ChartTypeUnsupportedError>())?;
    m.add("TableDimensionsError", py.get_type::<TableDimensionsError>())?;
    m.add("OpenXmlError", py.get_type::<OpenXmlError>())?;
    m.add("SerializationError", py.get_type::<SerializationError>())?;
    Ok(())
}

pub fn to_py_err(err: CoreError) -> PyErr {
    PyErr::new::<SlidexError, _>(err.to_string())
}

pub fn not_implemented(name: &str) -> PyErr {
    PyErr::new::<SlidexError, _>(format!("Not implemented: {name}"))
}
