"""
Calimero Client Python Library

A comprehensive Python client library for Calimero Network APIs,
built with PyO3 for high performance and native integration.
"""

__version__ = "0.3.0"
__author__ = "Calimero Network"
__email__ = "team@calimero.network"

# Import main functions and classes from the Rust bindings
from calimero_client_py import (
    create_connection,
    create_client,
    ConnectionInfo,
    Client,
    JwtToken,
    ClientError,
    AuthMode,
    get_token_cache_path,
    get_token_cache_dir,
)

# Re-export main types
__all__ = [
    "create_connection",
    "create_client",
    "ConnectionInfo",
    "Client",
    "JwtToken",
    "ClientError",
    "AuthMode",
    "get_token_cache_path",
    "get_token_cache_dir",
]
