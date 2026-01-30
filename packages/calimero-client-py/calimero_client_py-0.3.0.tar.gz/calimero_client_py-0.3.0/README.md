# Calimero Client Python Library

A comprehensive Python client library for Calimero Network APIs, built with PyO3 for high performance and native integration.

## Features

- **High Performance**: Built with Rust and PyO3 for optimal performance
- **Comprehensive API**: Full access to Calimero Network functionality  
- **Type Safety**: Strongly typed Python bindings
- **Async Support**: Built-in async/await support
- **Easy Installation**: Simple pip install

## Supported Protocols

- ✅ NEAR Protocol
- ✅ Ethereum  
- ✅ Internet Computer Protocol (ICP)
- ✅ Starknet
- ❌ Stellar (removed)

## Quick Start

```python
import asyncio
from calimero_client_py import create_connection, create_client, AuthMode

async def main():
    # Create a connection
    connection = create_connection(
        api_url="https://test.merod.dev.p2p.aws.calimero.network",
        node_name="test-dev-node"
    )
    
    # Create a client
    client = create_client(connection)
    
    # Use the client
    contexts = await client.list_contexts()
    print(f"Found {len(contexts)} contexts")

if __name__ == "__main__":
    asyncio.run(main())
```

## Installation

```bash
pip install calimero-client-py
```

## Development

### Building from Source

```bash
# Install dependencies
pip install maturin

# Build the package
maturin build --release

# Install in development mode
maturin develop
```

### Running Tests

```bash
python scripts/run_tests.py
```

## 🏗️ Project Structure

```
calimero-client-py/
├── README.md                    # This file
├── LICENSE                      # License file
├── pyproject.toml              # Python package configuration
├── Cargo.toml                  # Rust package configuration
├── Cargo.lock                  # Rust lock file
├── .github/
│   └── workflows/              # CI/CD workflows
├── src/                        # Rust source code
│   ├── lib.rs                  # PyO3 module registration
│   ├── error.rs                # PyClientError wrapper
│   ├── auth.rs                 # PyAuthMode wrapper
│   ├── token.rs                # PyJwtToken wrapper
│   ├── cache.rs                # Token cache path utilities
│   ├── storage.rs              # MeroboxFileStorage implementation
│   ├── connection.rs           # PyConnectionInfo + create_connection()
│   ├── client.rs               # PyClient + create_client()
│   └── utils.rs                # JSON to Python conversion helpers
├── calimero/                   # Python package
│   ├── __init__.py
│   └── cli.py
├── tests/                      # All tests
│   ├── test_integration.py
│   └── conftest.py
└── scripts/                    # Build and utility scripts
    ├── build.sh
    └── run_tests.py
```

## 🚀 Build Status

### Current Status: ✅ Ready to Build

The Python bindings for `calimero-client` are ready to build. Stellar support has been removed from the codebase.

### Environment Setup: ✅ Complete

- **Python Version**: 3.13.7
- **Virtual Environment**: ✅ Active and working
- **Maturin**: ✅ Installed (version 1.9.4)
- **PyO3**: ✅ Version 0.20.3 (compatible with Python 3.13 via ABI3)

### Current Working Components

- ✅ Python 3.13 virtual environment
- ✅ Maturin build system
- ✅ PyO3 configuration
- ✅ Basic project structure
- ✅ Rust toolchain
- ✅ All supported protocol dependencies

## 🔧 Building

### From the Repository Root (Recommended)

```bash
# From calimero-client-py root directory
./scripts/build.sh

# Or with options
./scripts/build.sh --install  # Build and install in development mode
```

### Manual Build

```bash
# Install maturin if you haven't already
pip install maturin

# Build the wheel
maturin build --release

# Install in development mode
maturin develop --release
```

### Standalone Build

This package can be built independently without requiring the full Calimero workspace.

#### Prerequisites

- Rust toolchain (1.70+)
- Python 3.8+
- maturin (will be installed automatically if missing)

#### Benefits of Standalone Build

✅ **Independent builds** - No need for full workspace  
✅ **Easier distribution** - Can be built anywhere  
✅ **CI/CD friendly** - Simpler build pipelines  
✅ **Version control** - Clear dependency management  
✅ **Faster builds** - Only builds what's needed

## 📦 Dependencies

The bindings depend on these crates (published to crates.io):
- `calimero-client` - Core client functionality
- `calimero-primitives` - Core data types

## 🧪 Testing

```bash
# Test Rust code
cargo test

# Test Python integration
python scripts/run_tests.py

# Test the environment
source venv/bin/activate.fish
python test-python.py
```

## 📤 Publishing to PyPI

This guide explains how to publish the `calimero-client-py` package to PyPI and other Python package repositories.

### Prerequisites

#### 1. PyPI Account
- Create an account on [PyPI](https://pypi.org/account/register/)
- Enable two-factor authentication (2FA) for security
- Create an API token for automated publishing

#### 2. Test PyPI Account (Recommended)
- Create an account on [Test PyPI](https://test.pypi.org/account/register/)
- Use this for testing before publishing to production

#### 3. Required Tools
```bash
# Install publishing tools
pip install twine build

# Install maturin for Rust bindings
pip install maturin
```

### Building the Package

#### 1. Clean Build Environment
```bash
# Remove previous builds
rm -rf target/wheels/
rm -rf dist/
rm -rf build/
rm -rf *.egg-info/
```

#### 2. Build with Maturin
```bash
# Build the Python wheel
maturin build --features python --release

# Verify the wheel was created
ls -la target/wheels/
```

#### 3. Build Source Distribution (Optional)
```bash
# Build source distribution
python -m build --sdist

# Verify source distribution
ls -la dist/
```

### Testing Before Publishing

#### 1. Test Installation
```bash
# Install from wheel
pip install target/wheels/calimero_client_py-*.whl

# Test import
python -c "import calimero_client_py; print('Import successful')"

# Test CLI
calimero-client-py --help
```

#### 2. Test on Test PyPI
```bash
# Upload to Test PyPI
twine upload --repository testpypi target/wheels/*.whl

# Install from Test PyPI
pip install --index-url https://test.pypi.org/simple/ calimero-client-py

# Test functionality
python -c "import calimero_client_py; print('Test PyPI install successful')"
```

### Publishing to PyPI

#### 1. Final Verification
```bash
# Check package metadata
twine check target/wheels/*.whl

# Verify package contents
pip show calimero-client-py
```

#### 2. Upload to PyPI
```bash
# Upload to production PyPI
twine upload target/wheels/*.whl

# Or upload both wheel and source
twine upload dist/*
```

#### 3. Verify Publication
```bash
# Wait a few minutes for PyPI to update
# Check on https://pypi.org/project/calimero-client-py/

# Test installation from PyPI
pip install calimero-client-py

# Verify it works
python -c "import calimero_client_py; print('PyPI install successful')"
```

### Automated Publishing with GitHub Actions

The package includes a GitHub Actions workflow that automatically publishes when you create a release tag.

#### 1. Create a Release
```bash
# Tag the release
git tag -a v0.1.0 -m "Release version 0.1.0"

# Push the tag
git push origin v0.1.0
```

#### 2. Set Up Secrets
In your GitHub repository settings, add these secrets:
- `PYPI_API_TOKEN`: Your PyPI API token
- `TEST_PYPI_API_TOKEN`: Your Test PyPI API token (optional)

#### 3. Monitor the Workflow
- Check the Actions tab in GitHub
- The workflow will automatically:
  - Build the package
  - Run tests
  - Publish to PyPI

### Common Issues and Solutions

#### 1. Build Failures
```bash
# Check Rust toolchain
rustup show

# Update dependencies
cargo update

# Clean and rebuild
cargo clean
maturin build --features python
```

#### 2. Import Errors
```bash
# Verify module structure
python -c "import sys; print(sys.path)"

# Check package installation
pip list | grep calimero
```

#### 3. PyPI Upload Errors
```bash
# Check authentication
twine check target/wheels/*.whl

# Verify API token
echo $PYPI_API_TOKEN

# Test with Test PyPI first
twine upload --repository testpypi target/wheels/*.whl
```

### Maintenance

#### 1. Version Management
```bash
# Update version in all files:
# - pyproject.toml
# - Cargo.toml
# - calimero_client_py/__init__.py
# - README.md (if version is mentioned)
```

#### 2. Dependency Updates
```bash
# Update Rust dependencies
cargo update

# Update Python dependencies
pip install --upgrade -r requirements-dev.txt

# Test with updated dependencies
pytest
```

#### 3. Security Updates
```bash
# Check for security vulnerabilities
safety check

# Update vulnerable packages
pip install --upgrade package-name
```

### Troubleshooting

- **Build fails**: Make sure `calimero-client` is published to crates.io
- **Import errors**: Verify the wheel was built for your Python version
- **Runtime errors**: Check that all dependencies are properly linked

### Additional Resources

- [PyPI Packaging Guide](https://packaging.python.org/tutorials/packaging-projects/)
- [Maturin Documentation](https://maturin.rs/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [Python Packaging Authority](https://www.pypa.io/)

## Token Persistence and Authentication

The client library includes automatic JWT token persistence for authenticated sessions. This feature enables:

- **Automatic token loading**: Tokens are loaded from disk when creating a connection
- **Automatic token refresh**: On 401 errors, the client automatically calls `/auth/refresh` and persists new tokens
- **Secure storage**: Tokens are stored with restrictive file permissions (0600 on Unix)

### Token Cache Location

Tokens are stored in `~/.merobox/auth_cache/` with filenames derived from the `node_name`:

```
~/.merobox/auth_cache/{sanitized_node_name}-{hash}.json
```

### The `node_name` Parameter

The `node_name` parameter is **critical for authenticated connections**:

```python
from calimero_client_py import create_connection, create_client

# For authenticated connections, node_name MUST be:
# 1. Provided (not None)
# 2. Stable across sessions (same value each time)
# 3. Unique per remote node you connect to

connection = create_connection(
    api_url="https://my-node.example.com:2428",
    node_name="my-production-node"  # Use a stable, descriptive name
)
```

**Important considerations:**

| Requirement | Why |
|------------|-----|
| **Stable** | The same `node_name` must be used across sessions to find cached tokens |
| **Unique** | Different nodes should have different names to avoid token collisions |
| **Descriptive** | Use meaningful names like `"prod-node-1"` or `"dev-local"` for clarity |

### Token Cache Utilities

Two helper functions are exposed for managing the token cache:

```python
from calimero_client_py import get_token_cache_path, get_token_cache_dir

# Get the full path to a node's token file
path = get_token_cache_path("my-node")
# Returns: ~/.merobox/auth_cache/my-node-<hash>.json

# Get the base cache directory
cache_dir = get_token_cache_dir()
# Returns: ~/.merobox/auth_cache/
```

### Authentication Flow

1. **Initial authentication** (handled by your application, e.g., merobox):
   - Call the auth endpoint to obtain JWT tokens
   - Write tokens to the path returned by `get_token_cache_path(node_name)`

2. **Subsequent connections**:
   - Create connection with the same `node_name`
   - Client automatically loads tokens from cache
   - Client attaches `Authorization: Bearer ...` header to requests

3. **Token refresh** (automatic):
   - On 401 response, client calls `/auth/refresh`
   - New tokens are automatically persisted to the same cache file

### Example: Complete Authentication Flow

```python
import json
from calimero_client_py import (
    create_connection,
    create_client,
    get_token_cache_path,
)

NODE_NAME = "my-remote-node"  # Keep this stable!

# Step 1: Write initial tokens (done once after authentication)
def save_initial_tokens(access_token, refresh_token, expires_at):
    token_data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": expires_at
    }
    cache_path = get_token_cache_path(NODE_NAME)
    
    # Ensure directory exists
    import os
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    
    with open(cache_path, 'w') as f:
        json.dump(token_data, f)

# Step 2: Create authenticated client (tokens loaded automatically)
connection = create_connection(
    api_url="https://my-node.example.com:2428",
    node_name=NODE_NAME
)
client = create_client(connection)

# Step 3: Use the client - Authorization header is set automatically
contexts = client.list_contexts()
```

## API Reference

### Core Classes

- `Client`: Main client for interacting with Calimero Network
- `ConnectionInfo`: Connection configuration
- `JwtToken`: JWT authentication token
- `ClientError`: Error handling
- `AuthMode`: Authentication modes

### Main Functions

- `create_connection()`: Create a new connection
- `create_client()`: Create a new client instance

### Client Methods

The `Client` class provides comprehensive access to Calimero Network functionality:

#### Connection Management
- `get_api_url()`: Get the API URL for this client
- `get_peers_count()`: Get the number of connected peers

#### Application Management
- `get_application(app_id: str)`: Get information about a specific application
- `list_applications()`: List all available applications
- `install_application(url: str, hash: Optional[str], metadata: Optional[bytes])`: Install application from URL
- `install_dev_application(path: str, metadata: Optional[bytes])`: Install development application from local path
- `uninstall_application(app_id: str)`: Uninstall an application

#### Context Management
- `get_context(context_id: str)`: Get information about a specific context
- `list_contexts()`: List all available contexts
- `create_context(application_id: str, protocol: str, params: Optional[str])`: Create a new context
- `delete_context(context_id: str)`: Delete a context
- `sync_context(context_id: str)`: Sync a specific context
- `sync_all_contexts()`: Sync all contexts

#### Context Operations
- `get_context_storage(context_id: str)`: Get context storage information
- `get_context_identities(context_id: str)`: Get identities associated with a context
- `get_context_client_keys(context_id: str)`: Get client keys for a context
- `invite_to_context(context_id: str, inviter_id: str, invitee_id: str)`: Invite someone to a context
- `join_context(context_id: str, invitee_id: str, invitation_payload: str)`: Join a context using invitation
- `update_context_application(context_id: str, application_id: str, executor_public_key: str)`: Update context application

#### Function Execution
- `execute_function(context_id: str, method: str, args: str, executor_public_key: str)`: Execute a function call via JSON-RPC

#### Permission Management
- `grant_permissions(context_id: str, permissions: str)`: Grant permissions to users in a context
- `revoke_permissions(context_id: str, permissions: str)`: Revoke permissions from users in a context

#### Proposal Management
- `get_proposal(context_id: str, proposal_id: str)`: Get proposal information
- `get_proposal_approvers(context_id: str, proposal_id: str)`: Get proposal approvers
- `list_proposals(context_id: str, args: Optional[str])`: List proposals in a context

#### Identity Management
- `generate_context_identity()`: Generate a new context identity

#### Blob Management
- `list_blobs()`: List all blobs
- `get_blob_info(blob_id: str)`: Get information about a specific blob
- `delete_blob(blob_id: str)`: Delete a blob

#### Alias Management
- `create_context_identity_alias(context_id: str, alias: str, public_key: str)`: Create context identity alias
- `create_context_alias(alias: str, context_id: str)`: Create context alias
- `create_application_alias(alias: str, application_id: str)`: Create application alias
- `delete_context_alias(alias: str)`: Delete context alias
- `delete_context_identity_alias(alias: str, context_id: str)`: Delete context identity alias

### Response Format

All client methods return Python objects (dictionaries, lists, etc.) containing the response data. The exact structure depends on the specific method called, but generally follows these patterns:

#### Success Response
```python
{
    "success": True,
    "data": { ... },  # Method-specific data
    "message": "Operation completed successfully"
}
```

#### Error Response
```python
{
    "success": False,
    "error": "Error description",
    "error_type": "Network|Authentication|Storage|Internal"
}
```

### Example Usage

```python
import asyncio
from calimero_client_py import create_connection, create_client, AuthMode

async def main():
    # Create connection
    connection = create_connection(
        api_url="https://test.merod.dev.p2p.aws.calimero.network",
        node_name="test-dev-node"
    )
    
    # Create client
    client = create_client(connection)
    
    # List applications
    apps = client.list_applications()
    print(f"Found {len(apps)} applications")
    
    # Create a context
    context = client.create_context(
        application_id="my-app-id",
        protocol="near",
        params='{"network": "testnet"}'
    )
    print(f"Created context: {context}")
    
    # Execute a function
    result = client.execute_function(
        context_id=context["context_id"],
        method="set_value",
        args='{"key": "test", "value": "hello"}',
        executor_public_key="your-public-key"
    )
    print(f"Function result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Support

If you encounter issues during publishing:

1. Check the [GitHub Issues](https://github.com/calimero-network/core/issues)
2. Review the [GitHub Actions logs](https://github.com/calimero-network/core/actions)
3. Contact the team at team@calimero.network

---

**Happy Publishing! 🎉**
