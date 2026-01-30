//! Disk-backed storage implementation for JWT tokens.
//!
//! Stores tokens in `~/.merobox/auth_cache/` with atomic writes and secure permissions.
//!
//! ## Features
//! - Atomic writes using temp file + rename pattern
//! - Secure permissions (0700 for directory, 0600 for files on Unix)
//! - Human-readable + collision-resistant filenames
//! - Proper error handling with context

use std::fs;
use std::fs::OpenOptions;
use std::io::Write;
use std::path::PathBuf;

#[cfg(unix)]
use std::os::unix::fs::OpenOptionsExt;

use calimero_client::traits::ClientStorage;
use calimero_client::JwtToken;
use eyre::WrapErr;

use crate::cache::{get_cache_base_dir, get_token_cache_path_internal};

/// Guard that ensures a temp file is cleaned up if the operation fails.
/// The file is only removed if `commit()` is not called before drop.
struct TempFileGuard {
    path: PathBuf,
    committed: bool,
}

impl TempFileGuard {
    fn new(path: PathBuf) -> Self {
        Self {
            path,
            committed: false,
        }
    }

    /// Mark the temp file as successfully committed (renamed to final path).
    /// After calling this, the guard will not remove the file on drop.
    fn commit(mut self) {
        self.committed = true;
        // self is moved, so drop won't be called
    }
}

impl Drop for TempFileGuard {
    fn drop(&mut self) {
        if !self.committed && self.path.exists() {
            // Best effort cleanup - ignore errors since we're in drop
            let _ = fs::remove_file(&self.path);
        }
    }
}

/// Disk-backed storage implementation for JWT tokens.
#[derive(Clone)]
pub struct MeroboxFileStorage;

impl MeroboxFileStorage {
    pub fn new() -> Self {
        Self
    }

    /// Ensure the cache directory exists with secure permissions (0700 on Unix).
    ///
    /// Uses `DirBuilderExt::mode` on Unix to create with correct permissions atomically,
    /// avoiding a TOCTOU race between create and set_permissions.
    fn ensure_cache_dir_exists(&self) -> eyre::Result<()> {
        let cache_dir = get_cache_base_dir();
        if !cache_dir.exists() {
            Self::create_cache_dir(&cache_dir)?;
        }
        Ok(())
    }

    #[cfg(unix)]
    fn create_cache_dir(cache_dir: &std::path::Path) -> eyre::Result<()> {
        use std::os::unix::fs::DirBuilderExt;
        fs::DirBuilder::new()
            .mode(0o700)
            .recursive(true)
            .create(cache_dir)
            .wrap_err_with(|| format!("Failed to create cache directory: {:?}", cache_dir))
    }

    #[cfg(not(unix))]
    fn create_cache_dir(cache_dir: &std::path::Path) -> eyre::Result<()> {
        fs::create_dir_all(cache_dir)
            .wrap_err_with(|| format!("Failed to create cache directory: {:?}", cache_dir))
    }
}

impl Default for MeroboxFileStorage {
    fn default() -> Self {
        Self::new()
    }
}

#[async_trait::async_trait]
impl ClientStorage for MeroboxFileStorage {
    /// Save JWT tokens to disk with atomic write and secure permissions.
    ///
    /// This method:
    /// 1. Ensures the cache directory exists (creating with 0700 permissions if needed)
    /// 2. Creates a temp file with 0600 permissions (Unix) via OpenOptionsExt::mode to avoid TOCTOU
    /// 3. Writes tokens and syncs
    /// 4. Atomically renames temp file to final path
    async fn save_tokens(&self, node_name: &str, tokens: &JwtToken) -> eyre::Result<()> {
        // Ensure directory exists with proper permissions
        self.ensure_cache_dir_exists()?;

        let cache_path = get_token_cache_path_internal(node_name);
        let temp_path = cache_path.with_extension("json.tmp");

        // Create guard to ensure temp file is cleaned up on error
        let _guard = TempFileGuard::new(temp_path.clone());

        // Serialize tokens to JSON
        let json = serde_json::to_string_pretty(tokens)
            .wrap_err("Failed to serialize JWT tokens to JSON")?;

        // Create temp file with correct permissions atomically (avoids TOCTOU).
        // On Unix, use OpenOptionsExt::mode(0o600); on other platforms, use default create.
        {
            #[allow(unused_mut)] // mut needed on Unix for mode() call
            let mut opts = OpenOptions::new();
            opts.write(true).create(true).truncate(true);
            #[cfg(unix)]
            {
                opts.mode(0o600);
            }
            let mut file = opts
                .open(&temp_path)
                .wrap_err_with(|| format!("Failed to create temp file: {:?}", temp_path))?;
            file.write_all(json.as_bytes())
                .wrap_err_with(|| format!("Failed to write to temp file: {:?}", temp_path))?;
            file.sync_all()
                .wrap_err_with(|| format!("Failed to sync temp file: {:?}", temp_path))?;
        }

        // Rename temp file to final path (atomic on most filesystems)
        fs::rename(&temp_path, &cache_path).wrap_err_with(|| {
            format!(
                "Failed to rename temp file {:?} to {:?}",
                temp_path, cache_path
            )
        })?;

        // Successfully committed - prevent cleanup on drop
        _guard.commit();

        Ok(())
    }

    /// Load JWT tokens from disk.
    ///
    /// Returns:
    /// - `Ok(Some(tokens))` if file exists and is valid JSON
    /// - `Ok(None)` if file does not exist
    /// - `Err(...)` if file exists but cannot be read or parsed
    async fn load_tokens(&self, node_name: &str) -> eyre::Result<Option<JwtToken>> {
        let cache_path = get_token_cache_path_internal(node_name);

        // If file doesn't exist, return None (not an error)
        if !cache_path.exists() {
            return Ok(None);
        }

        // Read and deserialize
        let json = fs::read_to_string(&cache_path).wrap_err_with(|| {
            format!(
                "Failed to read token file: {:?} for node: {}",
                cache_path, node_name
            )
        })?;

        let tokens: JwtToken = serde_json::from_str(&json).wrap_err_with(|| {
            format!(
                "Failed to parse token JSON from file: {:?} for node: {}",
                cache_path, node_name
            )
        })?;

        Ok(Some(tokens))
    }

    /// Remove the token file for a given node.
    ///
    /// This overrides the default trait implementation which would save an "empty token".
    /// Instead, we delete the file entirely.
    async fn remove_tokens(&self, node_name: &str) -> eyre::Result<()> {
        let cache_path = get_token_cache_path_internal(node_name);

        // Only try to remove if file exists
        if cache_path.exists() {
            fs::remove_file(&cache_path).wrap_err_with(|| {
                format!(
                    "Failed to remove token file: {:?} for node: {}",
                    cache_path, node_name
                )
            })?;
        }

        Ok(())
    }
}
