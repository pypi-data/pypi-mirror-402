//! Python wrapper for AuthMode

use calimero_client::connection::AuthMode;
use pyo3::prelude::*;

/// Python wrapper for AuthMode
#[pyclass(name = "AuthMode")]
#[derive(Debug, Clone, Copy)]
pub struct PyAuthMode {
    pub(crate) mode: AuthMode,
}

#[pymethods]
impl PyAuthMode {
    #[new]
    pub fn new(mode: &str) -> PyResult<Self> {
        let mode = match mode.to_lowercase().as_str() {
            "required" => AuthMode::Required,
            "none" => AuthMode::None,
            _ => {
                return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                    "AuthMode must be 'required' or 'none'",
                ))
            }
        };
        Ok(Self { mode })
    }

    #[getter]
    pub fn value(&self) -> &str {
        match self.mode {
            AuthMode::Required => "required",
            AuthMode::None => "none",
        }
    }

    fn __str__(&self) -> &str {
        self.value()
    }

    fn __repr__(&self) -> String {
        format!("AuthMode('{}')", self.value())
    }
}
