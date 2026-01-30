//! Python wrapper for Client

use std::str::FromStr;
use std::sync::Arc;

use calimero_client::client::Client;
use calimero_client::CliAuthenticator;
use calimero_context_config::types as context_types;
use calimero_primitives::alias::Alias;
use calimero_primitives::application::ApplicationId;
use calimero_primitives::blobs;
use calimero_primitives::context::{ContextId, ContextInvitationPayload};
use calimero_primitives::hash::Hash;
use calimero_primitives::identity;
use calimero_server_primitives::admin;
use calimero_server_primitives::jsonrpc;
use pyo3::prelude::*;
use tokio::runtime::Runtime;

use crate::connection::PyConnectionInfo;
use crate::storage::MeroboxFileStorage;
use crate::utils::json_to_python;

/// Python wrapper for Client
#[pyclass(name = "Client")]
pub struct PyClient {
    inner: Arc<Client<CliAuthenticator, MeroboxFileStorage>>,
    runtime: Arc<Runtime>,
}

#[pymethods]
impl PyClient {
    #[new]
    pub fn new(connection: &PyConnectionInfo) -> PyResult<Self> {
        let runtime = Arc::new(
            Runtime::new()
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?,
        );

        // Extract the inner connection from the Arc
        let connection_inner = connection.inner.as_ref().clone();
        let client = Client::new(connection_inner).map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                "Failed to create client: {}",
                e
            ))
        })?;

        Ok(Self {
            inner: Arc::new(client),
            runtime,
        })
    }

    /// Get API URL
    pub fn get_api_url(&self) -> String {
        self.inner.api_url().to_string()
    }

    /// Get application information
    pub fn get_application(&self, app_id: &str) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let app_id = app_id.parse::<ApplicationId>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid application ID '{}': {}",
                app_id, e
            ))
        })?;

        Python::with_gil(|py| {
            let result = self
                .runtime
                .block_on(async move { inner.get_application(&app_id).await });

            match result {
                Ok(data) => {
                    // Convert to JSON first, then to Python
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// List applications
    pub fn list_applications(&self) -> PyResult<PyObject> {
        let inner = self.inner.clone();

        Python::with_gil(|py| {
            let result = self
                .runtime
                .block_on(async move { inner.list_applications().await });

            match result {
                Ok(data) => {
                    // Convert to JSON first, then to Python
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Get context
    pub fn get_context(&self, context_id: &str) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let context_id = context_id.parse::<ContextId>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid context ID '{}': {}",
                context_id, e
            ))
        })?;

        Python::with_gil(|py| {
            let result = self
                .runtime
                .block_on(async move { inner.get_context(&context_id).await });

            match result {
                Ok(data) => {
                    // Convert to JSON first, then to Python
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// List contexts
    pub fn list_contexts(&self) -> PyResult<PyObject> {
        let inner = self.inner.clone();

        Python::with_gil(|py| {
            let result = self
                .runtime
                .block_on(async move { inner.list_contexts().await });

            match result {
                Ok(data) => {
                    // Convert to JSON first, then to Python
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Install application from URL
    pub fn install_application(
        &self,
        url: &str,
        hash: Option<&str>,
        metadata: Option<&[u8]>,
    ) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let url = url.to_string();
        let hash = hash.map(|h| h.to_string());
        let metadata = metadata.unwrap_or(b"{}").to_vec();

        Python::with_gil(|py| {
            let result = self.runtime.block_on(async move {
                let url = url::Url::parse(&url).map_err(|e| eyre::eyre!("Invalid URL: {}", e))?;

                let hash = if let Some(hash_str) = hash {
                    let hash_bytes =
                        hex::decode(hash_str).map_err(|e| eyre::eyre!("Invalid hash: {}", e))?;
                    let hash_array: [u8; 32] = hash_bytes
                        .try_into()
                        .map_err(|_| eyre::eyre!("Hash must be 32 bytes"))?;
                    Some(Hash::from(hash_array))
                } else {
                    None
                };

                let request =
                    admin::InstallApplicationRequest::new(url, hash, metadata, None, None);

                inner.install_application(request).await
            });

            match result {
                Ok(data) => {
                    // Convert to JSON first, then to Python
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Install development application from local path
    pub fn install_dev_application(
        &self,
        path: &str,
        metadata: Option<&[u8]>,
    ) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let path = path.to_string();
        let metadata = metadata.unwrap_or(b"{}").to_vec();

        Python::with_gil(|py| {
            let result = self.runtime.block_on(async move {
                let path = camino::Utf8PathBuf::from(path);
                let metadata = metadata;

                let request = admin::InstallDevApplicationRequest::new(path, metadata, None, None);

                inner.install_dev_application(request).await
            });

            match result {
                Ok(data) => {
                    // Convert to JSON first, then to Python
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Uninstall application
    pub fn uninstall_application(&self, app_id: &str) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let app_id = app_id.parse::<ApplicationId>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid application ID '{}': {}",
                app_id, e
            ))
        })?;

        Python::with_gil(|py| {
            let result = self
                .runtime
                .block_on(async move { inner.uninstall_application(&app_id).await });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Upload blob
    #[pyo3(signature = (data, context_id=None))]
    pub fn upload_blob(&self, data: &[u8], context_id: Option<&str>) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let data_vec = data.to_vec();
        let context_id_opt = context_id.map(|s| s.to_string());

        Python::with_gil(|py| {
            let result = self.runtime.block_on(async move {
                let context_id_parsed = if let Some(ctx_id) = context_id_opt {
                    Some(
                        ctx_id
                            .parse::<ContextId>()
                            .map_err(|e| eyre::eyre!("Invalid context ID '{}': {}", ctx_id, e))?,
                    )
                } else {
                    None
                };

                inner
                    .upload_blob(data_vec, context_id_parsed.as_ref())
                    .await
            });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Download blob
    #[pyo3(signature = (blob_id, context_id=None))]
    pub fn download_blob(&self, blob_id: &str, context_id: Option<&str>) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let blob_id = blob_id.parse::<blobs::BlobId>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid blob ID '{}': {}",
                blob_id, e
            ))
        })?;
        let context_id_opt = context_id.map(|s| s.to_string());

        Python::with_gil(|py| {
            let result = self.runtime.block_on(async move {
                let context_id_parsed = if let Some(ctx_id) = context_id_opt {
                    Some(
                        ctx_id
                            .parse::<ContextId>()
                            .map_err(|e| eyre::eyre!("Invalid context ID '{}': {}", ctx_id, e))?,
                    )
                } else {
                    None
                };

                inner
                    .download_blob(&blob_id, context_id_parsed.as_ref())
                    .await
            });

            match result {
                Ok(data) => {
                    // Return bytes directly as Python bytes object
                    Ok(pyo3::types::PyBytes::new_bound(py, &data).into_py(py))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// List blobs
    pub fn list_blobs(&self) -> PyResult<PyObject> {
        let inner = self.inner.clone();

        Python::with_gil(|py| {
            let result = self
                .runtime
                .block_on(async move { inner.list_blobs().await });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Get blob info
    pub fn get_blob_info(&self, blob_id: &str) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let blob_id = blob_id.parse::<blobs::BlobId>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid blob ID '{}': {}",
                blob_id, e
            ))
        })?;

        Python::with_gil(|py| {
            let result = self
                .runtime
                .block_on(async move { inner.get_blob_info(&blob_id).await });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Delete blob
    pub fn delete_blob(&self, blob_id: &str) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let blob_id = blob_id.parse::<blobs::BlobId>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid blob ID '{}': {}",
                blob_id, e
            ))
        })?;

        Python::with_gil(|py| {
            let result = self
                .runtime
                .block_on(async move { inner.delete_blob(&blob_id).await });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Generate context identity
    pub fn generate_context_identity(&self) -> PyResult<PyObject> {
        let inner = self.inner.clone();

        Python::with_gil(|py| {
            let result = self
                .runtime
                .block_on(async move { inner.generate_context_identity().await });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Get peers count
    pub fn get_peers_count(&self) -> PyResult<PyObject> {
        let inner = self.inner.clone();

        Python::with_gil(|py| {
            let result = self
                .runtime
                .block_on(async move { inner.get_peers_count().await });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Create context
    pub fn create_context(
        &self,
        application_id: &str,
        protocol: &str,
        params: Option<&str>,
    ) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let application_id = application_id.parse::<ApplicationId>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid application ID '{}': {}",
                application_id, e
            ))
        })?;

        let params = params.map(|p| p.as_bytes().to_vec()).unwrap_or_default();

        Python::with_gil(|py| {
            let result = self.runtime.block_on(async move {
                let request = admin::CreateContextRequest::new(
                    protocol.to_string(),
                    application_id,
                    None, // context_seed
                    params,
                );
                inner.create_context(request).await
            });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Delete context
    pub fn delete_context(&self, context_id: &str) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let context_id = context_id.parse::<ContextId>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid context ID '{}': {}",
                context_id, e
            ))
        })?;

        Python::with_gil(|py| {
            let result = self
                .runtime
                .block_on(async move { inner.delete_context(&context_id).await });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Get context storage
    pub fn get_context_storage(&self, context_id: &str) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let context_id = context_id.parse::<ContextId>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid context ID '{}': {}",
                context_id, e
            ))
        })?;

        Python::with_gil(|py| {
            let result = self
                .runtime
                .block_on(async move { inner.get_context_storage(&context_id).await });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Get context identities
    pub fn get_context_identities(&self, context_id: &str) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let context_id = context_id.parse::<ContextId>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid context ID '{}': {}",
                context_id, e
            ))
        })?;

        Python::with_gil(|py| {
            let result = self
                .runtime
                .block_on(async move { inner.get_context_identities(&context_id, false).await });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Get context client keys
    pub fn get_context_client_keys(&self, context_id: &str) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let context_id = context_id.parse::<ContextId>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid context ID '{}': {}",
                context_id, e
            ))
        })?;

        Python::with_gil(|py| {
            let result = self
                .runtime
                .block_on(async move { inner.get_context_client_keys(&context_id).await });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Sync context
    pub fn sync_context(&self, context_id: &str) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let context_id = context_id.parse::<ContextId>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid context ID '{}': {}",
                context_id, e
            ))
        })?;

        Python::with_gil(|py| {
            let result = self
                .runtime
                .block_on(async move { inner.sync_context(&context_id).await });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Invite to context
    pub fn invite_to_context(
        &self,
        context_id: &str,
        inviter_id: &str,
        invitee_id: &str,
    ) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let context_id = context_id.parse::<ContextId>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid context ID '{}': {}",
                context_id, e
            ))
        })?;
        let inviter_id = inviter_id.parse::<identity::PublicKey>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid inviter ID '{}': {}",
                inviter_id, e
            ))
        })?;
        let invitee_id = invitee_id.parse::<identity::PublicKey>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid invitee ID '{}': {}",
                invitee_id, e
            ))
        })?;

        Python::with_gil(|py| {
            let result = self.runtime.block_on(async move {
                let request =
                    admin::InviteToContextRequest::new(context_id, inviter_id, invitee_id);
                inner.invite_to_context(request).await
            });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Join context
    pub fn join_context(
        &self,
        context_id: &str,
        invitee_id: &str,
        invitation_payload: &str,
    ) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let _context_id = context_id.parse::<ContextId>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid context ID '{}': {}",
                context_id, e
            ))
        })?;
        let _invitee_id = invitee_id.parse::<identity::PublicKey>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid invitee ID '{}': {}",
                invitee_id, e
            ))
        })?;

        Python::with_gil(|py| {
            let result = self.runtime.block_on(async move {
                // For now, let's just try to join using the context_id and invitee_id
                // The invitation payload contains the necessary protocol/network/contract info
                // but we'll use the existing context for now
                let request = admin::JoinContextRequest::new(
                    ContextInvitationPayload::try_from(invitation_payload)
                        .map_err(|e| eyre::eyre!("Failed to parse invitation payload: {}", e))?,
                );
                inner.join_context(request).await
            });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Invite to context by open invitation
    pub fn invite_to_context_by_open_invitation(
        &self,
        context_id: &str,
        inviter_id: &str,
        valid_for_blocks: u64,
    ) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let context_id = context_id.parse::<ContextId>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid context ID '{}': {}",
                context_id, e
            ))
        })?;
        let inviter_id = inviter_id.parse::<identity::PublicKey>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid inviter ID '{}': {}",
                inviter_id, e
            ))
        })?;

        Python::with_gil(|py| {
            let result = self.runtime.block_on(async move {
                let request = admin::InviteToContextOpenInvitationRequest::new(
                    context_id,
                    inviter_id,
                    valid_for_blocks,
                );

                inner.invite_to_context_by_open_invitation(request).await
            });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Join context by open invitation
    pub fn join_context_by_open_invitation(
        &self,
        invitation_json: &str,
        new_member_public_key: &str,
    ) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let new_member_public_key = new_member_public_key
            .parse::<identity::PublicKey>()
            .map_err(|e| {
                PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                    "Invalid new member public key '{}': {}",
                    new_member_public_key, e
                ))
            })?;
        Python::with_gil(|py| {
            let result = self.runtime.block_on(async move {
                let invitation_value: serde_json::Value = serde_json::from_str(invitation_json)
                    .map_err(|e| eyre::eyre!("Invalid invitation JSON: {}", e))?;

                let invitation_data = if invitation_value.get("data").is_some() {
                    invitation_value.get("data").unwrap()
                } else {
                    &invitation_value
                };
                let invitation: context_types::SignedOpenInvitation =
                    serde_json::from_value(invitation_data.clone()).map_err(|e| {
                        eyre::eyre!(
                            "Failed to parse SignedOpenInvitation: {}. Data: {:?}",
                            e,
                            invitation_data
                        )
                    })?;

                let request = admin::JoinContextByOpenInvitationRequest::new(
                    invitation,
                    new_member_public_key,
                );

                inner.join_context_by_open_invitation(request).await
            });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Execute function call via JSON-RPC
    pub fn execute_function(
        &self,
        context_id: &str,
        method: &str,
        args: &str,
        executor_public_key: &str,
    ) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let context_id = context_id.parse::<ContextId>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid context ID '{}': {}",
                context_id, e
            ))
        })?;
        let executor_public_key =
            executor_public_key
                .parse::<identity::PublicKey>()
                .map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                        "Invalid executor public key '{}': {}",
                        executor_public_key, e
                    ))
                })?;

        Python::with_gil(|py| {
            let result = self.runtime.block_on(async move {
                // Parse args as JSON
                let args_value: serde_json::Value = serde_json::from_str(args)
                    .map_err(|e| eyre::eyre!("Invalid JSON args: {}", e))?;

                let execution_request = jsonrpc::ExecutionRequest::new(
                    context_id,
                    method.to_string(),
                    args_value,
                    executor_public_key,
                    vec![], // substitute aliases
                );

                let request = jsonrpc::Request::new(
                    jsonrpc::Version::TwoPointZero,
                    jsonrpc::RequestId::String("1".to_string()),
                    jsonrpc::RequestPayload::Execute(execution_request),
                );
                inner.execute_jsonrpc(request).await
            });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Grant permissions to users in a context
    pub fn grant_permissions(&self, context_id: &str, permissions: &str) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let context_id = context_id.parse::<ContextId>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid context ID '{}': {}",
                context_id, e
            ))
        })?;

        Python::with_gil(|py| {
            let result = self.runtime.block_on(async move {
                // Parse permissions as JSON array of [public_key, capability] pairs
                let permissions_value: Vec<(
                    identity::PublicKey,
                    calimero_context_config::types::Capability,
                )> = serde_json::from_str(permissions)
                    .map_err(|e| eyre::eyre!("Invalid JSON permissions: {}", e))?;

                inner
                    .grant_permissions(&context_id, permissions_value)
                    .await
            });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Revoke permissions from users in a context
    pub fn revoke_permissions(&self, context_id: &str, permissions: &str) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let context_id = context_id.parse::<ContextId>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid context ID '{}': {}",
                context_id, e
            ))
        })?;

        Python::with_gil(|py| {
            let result = self.runtime.block_on(async move {
                // Parse permissions as JSON array of [public_key, capability] pairs
                let permissions_value: Vec<(
                    identity::PublicKey,
                    calimero_context_config::types::Capability,
                )> = serde_json::from_str(permissions)
                    .map_err(|e| eyre::eyre!("Invalid JSON permissions: {}", e))?;

                inner
                    .revoke_permissions(&context_id, permissions_value)
                    .await
            });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Update context application
    pub fn update_context_application(
        &self,
        context_id: &str,
        application_id: &str,
        executor_public_key: &str,
    ) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let context_id = context_id.parse::<ContextId>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid context ID '{}': {}",
                context_id, e
            ))
        })?;
        let application_id = application_id.parse::<ApplicationId>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid application ID '{}': {}",
                application_id, e
            ))
        })?;
        let executor_public_key =
            executor_public_key
                .parse::<identity::PublicKey>()
                .map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                        "Invalid executor public key '{}': {}",
                        executor_public_key, e
                    ))
                })?;

        Python::with_gil(|py| {
            let result = self.runtime.block_on(async move {
                let request = admin::UpdateContextApplicationRequest::new(
                    application_id,
                    executor_public_key,
                );
                inner.update_context_application(&context_id, request).await
            });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Get proposal information
    pub fn get_proposal(&self, context_id: &str, proposal_id: &str) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let context_id = context_id.parse::<ContextId>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid context ID '{}': {}",
                context_id, e
            ))
        })?;
        let proposal_id = proposal_id.parse::<Hash>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid proposal ID '{}': {}",
                proposal_id, e
            ))
        })?;

        Python::with_gil(|py| {
            let result = self
                .runtime
                .block_on(async move { inner.get_proposal(&context_id, &proposal_id).await });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Get proposal approvers
    pub fn get_proposal_approvers(
        &self,
        context_id: &str,
        proposal_id: &str,
    ) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let context_id = context_id.parse::<ContextId>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid context ID '{}': {}",
                context_id, e
            ))
        })?;
        let proposal_id = proposal_id.parse::<Hash>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid proposal ID '{}': {}",
                proposal_id, e
            ))
        })?;

        Python::with_gil(|py| {
            let result = self.runtime.block_on(async move {
                inner
                    .get_proposal_approvers(&context_id, &proposal_id)
                    .await
            });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// List proposals in a context
    pub fn list_proposals(&self, context_id: &str, args: Option<&str>) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let context_id = context_id.parse::<ContextId>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid context ID '{}': {}",
                context_id, e
            ))
        })?;

        Python::with_gil(|py| {
            let result = self.runtime.block_on(async move {
                let args_value = if let Some(args_str) = args {
                    serde_json::from_str(args_str)
                        .map_err(|e| eyre::eyre!("Invalid JSON args: {}", e))?
                } else {
                    serde_json::Value::Null
                };

                inner.list_proposals(&context_id, args_value).await
            });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    pub fn create_and_approve_proposal(
        &self,
        context_id: &str,
        request_json: &str,
    ) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let context_id = context_id.parse::<ContextId>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid context ID '{}': {}",
                context_id, e
            ))
        })?;

        Python::with_gil(|py| {
            let result = self.runtime.block_on(async move {
                let request: admin::CreateAndApproveProposalRequest =
                    serde_json::from_str(request_json)
                        .map_err(|e| eyre::eyre!("Invalid request JSON: {}", e))?;

                inner
                    .create_and_approve_proposal(&context_id, request)
                    .await
            });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    pub fn approve_proposal(&self, context_id: &str, request_json: &str) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let context_id = context_id.parse::<ContextId>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid context ID '{}': {}",
                context_id, e
            ))
        })?;

        Python::with_gil(|py| {
            let result = self.runtime.block_on(async move {
                let request: admin::ApproveProposalRequest = serde_json::from_str(request_json)
                    .map_err(|e| eyre::eyre!("Invalid request JSON: {}", e))?;

                inner.approve_proposal(&context_id, request).await
            });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Sync all contexts
    pub fn sync_all_contexts(&self) -> PyResult<PyObject> {
        let inner = self.inner.clone();

        Python::with_gil(|py| {
            let result = self
                .runtime
                .block_on(async move { inner.sync_all_contexts().await });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Create context identity alias
    pub fn create_context_identity_alias(
        &self,
        context_id: &str,
        alias: &str,
        public_key: &str,
    ) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let context_id = context_id.parse::<ContextId>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid context ID '{}': {}",
                context_id, e
            ))
        })?;
        let public_key = public_key.parse::<identity::PublicKey>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid public key '{}': {}",
                public_key, e
            ))
        })?;

        Python::with_gil(|py| {
            let result = self.runtime.block_on(async move {
                let alias_obj = Alias::<identity::PublicKey>::from_str(alias)
                    .map_err(|e| eyre::eyre!("Invalid alias: {}", e))?;
                let request = admin::CreateAliasRequest {
                    alias: alias_obj,
                    value: admin::CreateContextIdentityAlias {
                        identity: public_key,
                    },
                };
                inner
                    .create_context_identity_alias(&context_id, request)
                    .await
            });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Create context alias
    pub fn create_context_alias(&self, alias: &str, context_id: &str) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let context_id = context_id.parse::<ContextId>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid context ID '{}': {}",
                context_id, e
            ))
        })?;

        Python::with_gil(|py| {
            let result = self.runtime.block_on(async move {
                let alias_obj = Alias::<ContextId>::from_str(alias)
                    .map_err(|e| eyre::eyre!("Invalid alias: {}", e))?;

                inner.create_alias(alias_obj, context_id, None).await
            });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Create application alias
    pub fn create_application_alias(
        &self,
        alias: &str,
        application_id: &str,
    ) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let application_id = application_id.parse::<ApplicationId>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid application ID '{}': {}",
                application_id, e
            ))
        })?;

        Python::with_gil(|py| {
            let result = self.runtime.block_on(async move {
                let alias_obj = Alias::<ApplicationId>::from_str(alias)
                    .map_err(|e| eyre::eyre!("Invalid alias: {}", e))?;

                inner.create_alias(alias_obj, application_id, None).await
            });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Delete context alias
    pub fn delete_context_alias(&self, alias: &str) -> PyResult<PyObject> {
        let inner = self.inner.clone();

        Python::with_gil(|py| {
            let result = self.runtime.block_on(async move {
                let alias_obj = Alias::<ContextId>::from_str(alias)
                    .map_err(|e| eyre::eyre!("Invalid alias: {}", e))?;

                inner.delete_alias(alias_obj, None).await
            });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Delete context identity alias
    pub fn delete_context_identity_alias(
        &self,
        alias: &str,
        context_id: &str,
    ) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let context_id = context_id.parse::<ContextId>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid context ID '{}': {}",
                context_id, e
            ))
        })?;

        Python::with_gil(|py| {
            let result = self.runtime.block_on(async move {
                let alias_obj = Alias::<identity::PublicKey>::from_str(alias)
                    .map_err(|e| eyre::eyre!("Invalid alias: {}", e))?;

                inner.delete_alias(alias_obj, Some(context_id)).await
            });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Delete application alias
    pub fn delete_application_alias(&self, alias: &str) -> PyResult<PyObject> {
        let inner = self.inner.clone();

        Python::with_gil(|py| {
            let result = self.runtime.block_on(async move {
                let alias_obj = Alias::<ApplicationId>::from_str(alias)
                    .map_err(|e| eyre::eyre!("Invalid alias: {}", e))?;

                inner.delete_alias(alias_obj, None).await
            });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// List context aliases
    pub fn list_context_aliases(&self) -> PyResult<PyObject> {
        let inner = self.inner.clone();

        Python::with_gil(|py| {
            let result = self
                .runtime
                .block_on(async move { inner.list_aliases::<ContextId>(None).await });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// List context identity aliases
    pub fn list_context_identity_aliases(&self, context_id: &str) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let context_id = context_id.parse::<ContextId>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid context ID '{}': {}",
                context_id, e
            ))
        })?;

        Python::with_gil(|py| {
            let result = self.runtime.block_on(async move {
                inner
                    .list_aliases::<identity::PublicKey>(Some(context_id))
                    .await
            });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// List application aliases
    pub fn list_application_aliases(&self) -> PyResult<PyObject> {
        let inner = self.inner.clone();

        Python::with_gil(|py| {
            let result = self
                .runtime
                .block_on(async move { inner.list_aliases::<ApplicationId>(None).await });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Lookup context alias
    pub fn lookup_context_alias(&self, alias: &str) -> PyResult<PyObject> {
        let inner = self.inner.clone();

        Python::with_gil(|py| {
            let result = self.runtime.block_on(async move {
                let alias_obj = Alias::<ContextId>::from_str(alias)
                    .map_err(|e| eyre::eyre!("Invalid alias: {}", e))?;

                inner.lookup_alias(alias_obj, None).await
            });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Lookup context identity alias
    pub fn lookup_context_identity_alias(
        &self,
        alias: &str,
        context_id: &str,
    ) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let context_id = context_id.parse::<ContextId>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid context ID '{}': {}",
                context_id, e
            ))
        })?;

        Python::with_gil(|py| {
            let result = self.runtime.block_on(async move {
                let alias_obj = Alias::<identity::PublicKey>::from_str(alias)
                    .map_err(|e| eyre::eyre!("Invalid alias: {}", e))?;

                inner.lookup_alias(alias_obj, Some(context_id)).await
            });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Lookup application alias
    pub fn lookup_application_alias(&self, alias: &str) -> PyResult<PyObject> {
        let inner = self.inner.clone();

        Python::with_gil(|py| {
            let result = self.runtime.block_on(async move {
                let alias_obj = Alias::<ApplicationId>::from_str(alias)
                    .map_err(|e| eyre::eyre!("Invalid alias: {}", e))?;

                inner.lookup_alias(alias_obj, None).await
            });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Resolve context alias
    pub fn resolve_context_alias(&self, alias: &str) -> PyResult<PyObject> {
        let inner = self.inner.clone();

        Python::with_gil(|py| {
            let result = self.runtime.block_on(async move {
                let alias_obj = Alias::<ContextId>::from_str(alias)
                    .map_err(|e| eyre::eyre!("Invalid alias: {}", e))?;

                inner.resolve_alias(alias_obj, None).await
            });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Resolve context identity alias
    pub fn resolve_context_identity_alias(
        &self,
        alias: &str,
        context_id: &str,
    ) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let context_id = context_id.parse::<ContextId>().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid context ID '{}': {}",
                context_id, e
            ))
        })?;

        Python::with_gil(|py| {
            let result = self.runtime.block_on(async move {
                let alias_obj = Alias::<identity::PublicKey>::from_str(alias)
                    .map_err(|e| eyre::eyre!("Invalid alias: {}", e))?;

                inner.resolve_alias(alias_obj, Some(context_id)).await
            });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Resolve application alias
    pub fn resolve_application_alias(&self, alias: &str) -> PyResult<PyObject> {
        let inner = self.inner.clone();

        Python::with_gil(|py| {
            let result = self.runtime.block_on(async move {
                let alias_obj = Alias::<ApplicationId>::from_str(alias)
                    .map_err(|e| eyre::eyre!("Invalid alias: {}", e))?;

                inner.resolve_alias(alias_obj, None).await
            });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }

    /// Create alias generic (Python wrapper for backward compatibility)
    pub fn create_alias_generic(
        &self,
        alias: &str,
        value: &str,
        scope: Option<&str>,
    ) -> PyResult<PyObject> {
        let inner = self.inner.clone();
        let alias_str = alias.to_string();
        let value_str = value.to_string();
        let _scope_str = scope.map(|s| s.to_string());

        Python::with_gil(|py| {
            let result = self.runtime.block_on(async move {
                // This is a simplified wrapper - in practice, you'd need to know the type T
                // For now, we'll use ContextId as a default type
                let alias_obj = Alias::<ContextId>::from_str(&alias_str)
                    .map_err(|e| eyre::eyre!("Invalid alias: {}", e))?;

                // Parse the value as ContextId
                let value_obj = value_str
                    .parse::<ContextId>()
                    .map_err(|e| eyre::eyre!("Invalid value: {}", e))?;

                // Create the alias
                inner.create_alias(alias_obj, value_obj, None).await
            });

            match result {
                Ok(data) => {
                    let json_data = serde_json::to_value(data).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                            "Failed to serialize response: {}",
                            e
                        ))
                    })?;
                    Ok(json_to_python(py, &json_data))
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Client error: {}",
                    e
                ))),
            }
        })
    }
}

/// Create a new client
#[pyfunction]
pub fn create_client(connection: &PyConnectionInfo) -> PyResult<PyClient> {
    PyClient::new(connection)
}
