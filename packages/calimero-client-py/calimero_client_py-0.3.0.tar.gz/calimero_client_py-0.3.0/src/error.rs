//! Python wrapper for ClientError

use calimero_client::ClientError;
use pyo3::prelude::*;

/// Python wrapper for ClientError
#[pyclass(name = "ClientError")]
#[derive(Debug)]
pub struct PyClientError {
    error_type: String,
    message: String,
}

#[pymethods]
impl PyClientError {
    #[new]
    pub fn new(error_type: &str, message: &str) -> Self {
        Self {
            error_type: error_type.to_string(),
            message: message.to_string(),
        }
    }

    #[getter]
    pub fn error_type(&self) -> &str {
        &self.error_type
    }

    #[getter]
    pub fn message(&self) -> &str {
        &self.message
    }

    fn __str__(&self) -> String {
        format!("{}: {}", self.error_type, self.message)
    }

    fn __repr__(&self) -> String {
        format!(
            "ClientError(error_type='{}', message='{}')",
            self.error_type, self.message
        )
    }
}

impl From<ClientError> for PyClientError {
    fn from(err: ClientError) -> Self {
        match err {
            ClientError::Network { message } => Self {
                error_type: "Network".to_string(),
                message,
            },
            ClientError::Authentication { message } => Self {
                error_type: "Authentication".to_string(),
                message,
            },
            ClientError::Storage { message } => Self {
                error_type: "Storage".to_string(),
                message,
            },
            ClientError::Internal { message } => Self {
                error_type: "Internal".to_string(),
                message,
            },
        }
    }
}
