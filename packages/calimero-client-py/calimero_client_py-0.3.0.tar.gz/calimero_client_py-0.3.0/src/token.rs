//! Python wrapper for JwtToken

use calimero_client::JwtToken;
use pyo3::prelude::*;

/// Python wrapper for JwtToken
#[pyclass(name = "JwtToken")]
#[derive(Debug, Clone)]
pub struct PyJwtToken {
    access_token: String,
    refresh_token: Option<String>,
    expires_at: Option<i64>,
}

#[pymethods]
impl PyJwtToken {
    #[new]
    pub fn new(access_token: &str, refresh_token: Option<&str>, expires_at: Option<i64>) -> Self {
        Self {
            access_token: access_token.to_string(),
            refresh_token: refresh_token.map(|s| s.to_string()),
            expires_at,
        }
    }

    #[getter]
    pub fn access_token(&self) -> &str {
        &self.access_token
    }

    #[getter]
    pub fn refresh_token(&self) -> Option<&str> {
        self.refresh_token.as_deref()
    }

    #[getter]
    pub fn expires_at(&self) -> Option<i64> {
        self.expires_at
    }

    pub fn is_expired(&self) -> bool {
        if let Some(expires_at) = self.expires_at {
            let now = chrono::Utc::now().timestamp();
            now >= expires_at
        } else {
            false
        }
    }

    fn __str__(&self) -> String {
        format!(
            "JwtToken(access_token='{}...', expires_at={:?})",
            &self.access_token[..self.access_token.len().min(10)],
            self.expires_at
        )
    }
}

impl From<JwtToken> for PyJwtToken {
    fn from(token: JwtToken) -> Self {
        Self {
            access_token: token.access_token,
            refresh_token: token.refresh_token,
            expires_at: token.expires_at,
        }
    }
}
