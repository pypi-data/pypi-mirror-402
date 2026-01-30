//! Python bindings for Calimero client using PyO3
//!
//! This crate provides Python bindings that can be built independently
//! without requiring the full Calimero workspace.
//!
//! ## Module Structure
//!
//! - `error` - PyClientError wrapper
//! - `auth` - PyAuthMode wrapper
//! - `token` - PyJwtToken wrapper
//! - `cache` - Token cache path utilities
//! - `storage` - MeroboxFileStorage implementation
//! - `connection` - PyConnectionInfo and create_connection()
//! - `client` - PyClient and create_client()
//! - `utils` - JSON to Python conversion helpers

pub mod auth;
pub mod cache;
pub mod client;
pub mod connection;
pub mod error;
pub mod storage;
pub mod token;
pub mod utils;

use pyo3::prelude::*;

/// Python module for Calimero client
#[pymodule]
fn calimero_client_py(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Register classes
    m.add_class::<connection::PyConnectionInfo>()?;
    m.add_class::<client::PyClient>()?;
    m.add_class::<token::PyJwtToken>()?;
    m.add_class::<error::PyClientError>()?;
    m.add_class::<auth::PyAuthMode>()?;

    // Register functions
    m.add_function(wrap_pyfunction!(connection::create_connection, m)?)?;
    m.add_function(wrap_pyfunction!(client::create_client, m)?)?;
    m.add_function(wrap_pyfunction!(cache::get_token_cache_path, m)?)?;
    m.add_function(wrap_pyfunction!(cache::get_token_cache_dir, m)?)?;

    // Add constants
    m.add("VERSION", env!("CARGO_PKG_VERSION"))?;

    Ok(())
}
