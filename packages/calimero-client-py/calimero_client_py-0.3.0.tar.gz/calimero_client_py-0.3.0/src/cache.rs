//! Token cache path utilities
//!
//! Provides functions for deriving stable, collision-resistant cache file paths
//! for JWT tokens stored in ~/.merobox/auth_cache/

use std::path::PathBuf;

use pyo3::prelude::*;
use sha2::{Digest, Sha256};

// ============================================================================
// Constants
// ============================================================================

/// Default base directory for token cache: ~/.merobox/auth_cache/
pub const AUTH_CACHE_SUBDIR: &str = "auth_cache";
pub const MEROBOX_DIR: &str = ".merobox";

// ============================================================================
// Internal Functions
// ============================================================================

/// Get the base directory for token cache files.
/// Returns `~/.merobox/auth_cache/`
pub fn get_cache_base_dir() -> PathBuf {
    dirs::home_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join(MEROBOX_DIR)
        .join(AUTH_CACHE_SUBDIR)
}

/// Sanitize a node name to create a safe filesystem slug.
/// Only allows `[A-Za-z0-9._-]`, replacing other characters with `_`.
pub fn sanitize_node_name(node_name: &str) -> String {
    node_name
        .chars()
        .map(|c| {
            if c.is_ascii_alphanumeric() || c == '.' || c == '_' || c == '-' {
                c
            } else {
                '_'
            }
        })
        .collect()
}

/// Derive a stable, unique filename for a node's token cache.
/// Format: `{slug[:64]}-{sha256_hash[:12]}.json`
///
/// This ensures:
/// - Human-readable prefix (truncated slug)
/// - Collision-resistant suffix (SHA-256 hash prefix)
/// - Safe filesystem characters only
pub fn derive_token_filename(node_name: &str) -> String {
    // Create sanitized slug
    let slug = sanitize_node_name(node_name);
    let truncated_slug: String = slug.chars().take(64).collect();

    // Compute SHA-256 hash of the original node_name
    let mut hasher = Sha256::new();
    hasher.update(node_name.as_bytes());
    let hash_result = hasher.finalize();
    let hash_hex = hex::encode(hash_result);
    let hash_prefix = &hash_hex[..12];

    format!("{}-{}.json", truncated_slug, hash_prefix)
}

/// Get the full path to the token cache file for a given node name.
/// Returns the path as `~/.merobox/auth_cache/{slug}-{hash}.json`
pub fn get_token_cache_path_internal(node_name: &str) -> PathBuf {
    get_cache_base_dir().join(derive_token_filename(node_name))
}

// ============================================================================
// Python-exposed Functions
// ============================================================================

/// Python-exposed function to get the token cache path for a given node name.
/// This allows Python code (e.g., merobox) to write initial tokens to the correct location.
#[pyfunction]
pub fn get_token_cache_path(node_name: &str) -> PyResult<String> {
    let path = get_token_cache_path_internal(node_name);
    path.to_str().map(|s| s.to_string()).ok_or_else(|| {
        PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "Token cache path contains invalid UTF-8 characters",
        )
    })
}

/// Python-exposed function to get the base directory for token cache.
/// Returns `~/.merobox/auth_cache/`
#[pyfunction]
pub fn get_token_cache_dir() -> PyResult<String> {
    let path = get_cache_base_dir();
    path.to_str().map(|s| s.to_string()).ok_or_else(|| {
        PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "Token cache directory path contains invalid UTF-8 characters",
        )
    })
}

// ============================================================================
// Unit Tests
// ============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    /// Test that filename derivation is stable (same input → same output).
    #[test]
    fn test_filename_derivation_stability() {
        let node_name = "https://my-node.example.com:8080";

        let filename1 = derive_token_filename(node_name);
        let filename2 = derive_token_filename(node_name);
        let filename3 = derive_token_filename(node_name);

        assert_eq!(
            filename1, filename2,
            "Filename should be stable across calls"
        );
        assert_eq!(
            filename2, filename3,
            "Filename should be stable across calls"
        );
    }

    /// Test that different inputs produce different filenames.
    #[test]
    fn test_filename_derivation_uniqueness() {
        let filenames: Vec<String> = vec![
            "node-alpha",
            "node-beta",
            "node-gamma",
            "https://example.com",
            "test-dev-node",
        ]
        .into_iter()
        .map(derive_token_filename)
        .collect();

        // Check all filenames are unique
        let unique_count = filenames
            .iter()
            .collect::<std::collections::HashSet<_>>()
            .len();
        assert_eq!(
            unique_count,
            filenames.len(),
            "All node names should produce unique filenames"
        );
    }

    /// Test filename format is correct: {slug}-{hash}.json
    #[test]
    fn test_filename_format() {
        let filename = derive_token_filename("test-node");

        // Should end with .json
        assert!(
            filename.ends_with(".json"),
            "Filename should end with .json"
        );

        // Should contain a dash before the hash
        let name_without_ext = &filename[..filename.len() - 5];
        assert!(
            name_without_ext.contains('-'),
            "Filename should contain a dash separator"
        );

        // Hash should be 12 hex characters
        let parts: Vec<&str> = name_without_ext.rsplitn(2, '-').collect();
        assert_eq!(parts.len(), 2, "Filename should have slug-hash format");
        let hash_part = parts[0];
        assert_eq!(hash_part.len(), 12, "Hash should be 12 characters");
        assert!(
            hash_part.chars().all(|c| c.is_ascii_hexdigit()),
            "Hash should be hex"
        );
    }

    /// Test that long node names are truncated properly.
    #[test]
    fn test_long_node_name_truncation() {
        let long_name = "a".repeat(1000);
        let filename = derive_token_filename(&long_name);

        // slug (max 64) + dash (1) + hash (12) + .json (5) = max 82 chars
        assert!(
            filename.len() <= 82,
            "Filename should be truncated to reasonable length"
        );
        assert!(filename.ends_with(".json"));
    }

    /// Test sanitization of special characters.
    #[test]
    fn test_sanitize_node_name() {
        assert_eq!(sanitize_node_name("simple"), "simple");
        assert_eq!(sanitize_node_name("with-dashes"), "with-dashes");
        assert_eq!(sanitize_node_name("with_underscores"), "with_underscores");
        assert_eq!(sanitize_node_name("with.dots"), "with.dots");

        // Special characters should be replaced with underscore
        assert_eq!(sanitize_node_name("with spaces"), "with_spaces");
        assert_eq!(
            sanitize_node_name("https://example.com"),
            "https___example.com"
        );
        assert_eq!(sanitize_node_name("node:8080"), "node_8080");
        assert_eq!(sanitize_node_name("path/to/node"), "path_to_node");
    }

    /// Test cache path derivation.
    #[test]
    fn test_cache_path_derivation() {
        let path = get_token_cache_path_internal("test-node");

        // Should be under the cache directory
        let cache_dir = get_cache_base_dir();
        assert!(
            path.starts_with(&cache_dir),
            "Path should be under cache directory"
        );

        // Should end with .json
        assert!(
            path.to_str().unwrap().ends_with(".json"),
            "Path should end with .json"
        );
    }

    /// Test cache base directory format.
    #[test]
    fn test_cache_base_dir() {
        let cache_dir = get_cache_base_dir();
        let path_str = cache_dir.to_str().unwrap();

        // Should contain .merobox and auth_cache
        assert!(
            path_str.contains(".merobox"),
            "Cache dir should contain .merobox"
        );
        assert!(
            path_str.contains("auth_cache"),
            "Cache dir should contain auth_cache"
        );
    }

    /// Test that empty node name works (edge case).
    #[test]
    fn test_empty_node_name() {
        let filename = derive_token_filename("");
        assert!(filename.ends_with(".json"));
        assert!(filename.len() > 5); // At least "-{hash}.json"
    }

    /// Test that URL-like node names produce valid filenames.
    #[test]
    fn test_url_node_names() {
        let test_urls = vec![
            "https://api.example.com:8080/v1",
            "https://test.merod.dev.p2p.aws.calimero.network",
            "wss://node.example.com",
            "https://user:pass@host.com",
        ];

        for url in test_urls {
            let filename = derive_token_filename(url);
            assert!(
                filename.ends_with(".json"),
                "URL '{}' should produce .json file",
                url
            );

            // Verify no invalid filesystem characters
            let invalid_chars = ['<', '>', ':', '"', '|', '?', '*'];
            for ch in invalid_chars {
                assert!(
                    !filename.contains(ch),
                    "Filename for '{}' should not contain '{}'",
                    url,
                    ch
                );
            }
        }
    }
}
