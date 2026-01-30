//! Python wrapper for ConnectionInfo

use std::sync::Arc;

use calimero_client::connection::ConnectionInfo;
use calimero_client::CliAuthenticator;
use pyo3::prelude::*;
use tokio::runtime::Runtime;
use url::Url;

use crate::auth::PyAuthMode;
use crate::storage::MeroboxFileStorage;
use crate::utils::json_to_python;

/// Python wrapper for ConnectionInfo
#[pyclass(name = "ConnectionInfo")]
pub struct PyConnectionInfo {
    pub(crate) inner: Arc<ConnectionInfo<CliAuthenticator, MeroboxFileStorage>>,
    pub(crate) runtime: Arc<Runtime>,
}

#[pymethods]
impl PyConnectionInfo {
    #[new]
    pub fn new(api_url: &str, node_name: Option<&str>) -> PyResult<Self> {
        let runtime = Arc::new(
            Runtime::new()
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?,
        );

        let url = Url::parse(api_url).map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Invalid URL: {}", e))
        })?;

        let authenticator = CliAuthenticator::new();
        let storage = MeroboxFileStorage::new();

        let connection = ConnectionInfo::new(
            url,
            node_name.map(|s| s.to_string()),
            authenticator,
            storage,
        );

        Ok(Self {
            inner: Arc::new(connection),
            runtime,
        })
    }

    #[getter]
    pub fn api_url(&self) -> String {
        self.inner.api_url.to_string()
    }

    #[getter]
    pub fn node_name(&self) -> Option<String> {
        self.inner.node_name.clone()
    }

    /// Make a GET request
    pub fn get(&self, path: &str) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let path = path.to_string();

        Python::with_gil(|py| {
            let result = self
                .runtime
                .block_on(async move { inner.get::<serde_json::Value>(&path).await });

            match result {
                Ok(data) => Ok(json_to_python(py, &data)),
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Check if authentication is required
    pub fn detect_auth_mode(&self) -> PyResult<PyAuthMode> {
        let inner = self.inner.clone();

        let result = self
            .runtime
            .block_on(async move { inner.detect_auth_mode().await });

        match result {
            Ok(mode) => Ok(PyAuthMode { mode }),
            Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                "Client error: {}",
                e
            ))),
        }
    }
}

/// Create a new connection
#[pyfunction]
#[pyo3(signature = (api_url, node_name=None))]
pub fn create_connection(api_url: &str, node_name: Option<&str>) -> PyResult<PyConnectionInfo> {
    PyConnectionInfo::new(api_url, node_name)
}
