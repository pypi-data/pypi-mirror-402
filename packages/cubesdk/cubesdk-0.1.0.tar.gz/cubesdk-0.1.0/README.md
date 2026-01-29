# CubeSDK

Python SDK for Cube secret management with built-in caching, environment switching, and automatic error handling.

## Features

- 🔐 **Secure Secret Management** - Retrieve secrets from Cube with service token authentication
- ⚡ **Built-in Caching** - TTL-based caching to reduce API calls and improve performance
- 🌍 **Environment Support** - Switch between environments (development, staging, production) seamlessly
- 🔄 **Auto-refresh** - Automatic cache invalidation and refresh capabilities
- 🛡️ **Error Handling** - Comprehensive exception handling for authentication, authorization, and API errors
- 📦 **Simple API** - Clean and intuitive interface for secret management

## Installation

Install CubeSDK using pip:

```bash
pip install cubesdk
```

## Quick Start

```python
from cubesdk import CubeSDK

# Initialize client with a service token and default environment
client = CubeSDK(
    service_token="st_prod_xxx",
    default_env="production",
    cache_ttl=120,  # Cache secrets for 2 minutes
)

# Get a single secret
db_password = client.get_secret("DB_PASSWORD")

# Get all secrets
secrets = client.get_secrets()

# Switch environment
client.switch_env("staging")
api_key = client.get_secret("API_KEY")

# Force refresh cache
client.refresh()
```

## Configuration

The `CubeSDK` client accepts the following parameters:

- `service_token` (str, required): Your Cube service token for authentication
- `api_version` (str, optional): API version to use (defaults to environment variable or configured value)
- `default_env` (str, optional): Default environment name (default: `"development"`)
- `base_url` (str, optional): Base URL for the Cube API (defaults to environment variable or configured value)
- `timeout` (int, optional): Request timeout in seconds (default: `5`)
- `cache_ttl` (int, optional): Cache time-to-live in seconds (default: `60`)

## API Reference

### `get_secret(key: str) -> str`

Retrieve a single secret by key. The secret is cached based on the current environment and cache TTL.

```python
password = client.get_secret("DB_PASSWORD")
```

### `get_secrets() -> Dict[str, str]`

Retrieve all secrets for the current environment. All secrets are cached automatically.

```python
all_secrets = client.get_secrets()
# Returns: {"DB_PASSWORD": "secret123", "API_KEY": "key456", ...}
```

### `switch_env(environment: str)`

Switch to a different environment. This clears the cache to ensure fresh secrets are fetched.

```python
client.switch_env("staging")
```

### `refresh()`

Force refresh all cached secrets by clearing the cache.

```python
client.refresh()
```

## Error Handling

The SDK provides specific exception types for different error scenarios:

```python
from cubesdk import CubeSDK
from app.exceptions import (
    AuthenticationError,
    AuthorizationError,
    SecretNotFoundError,
    APIError,
)

try:
    secret = client.get_secret("MY_SECRET")
except AuthenticationError:
    print("Invalid or expired service token")
except AuthorizationError:
    print("Access denied for this environment")
except SecretNotFoundError:
    print("Secret not found in the current environment")
except APIError as e:
    print(f"API error: {e}")
```

## Examples

### Basic Usage

```python
from cubesdk import CubeSDK

client = CubeSDK(
    service_token="st_dev_xxx",
    default_env="development",
    cache_ttl=300,  # 5 minutes
)

# Get secrets
db_host = client.get_secret("DB_HOST")
db_password = client.get_secret("DB_PASSWORD")
api_key = client.get_secret("API_KEY")
```

### Environment Switching

```python
# Start with production
client = CubeSDK(
    service_token="st_prod_xxx",
    default_env="production",
)

prod_secret = client.get_secret("SECRET_KEY")

# Switch to staging
client.switch_env("staging")
staging_secret = client.get_secret("SECRET_KEY")
```

### Batch Secret Retrieval

```python
# Get all secrets at once (more efficient for multiple secrets)
secrets = client.get_secrets()
db_config = {
    "host": secrets["DB_HOST"],
    "port": secrets["DB_PORT"],
    "password": secrets["DB_PASSWORD"],
}
```

### Custom Configuration

```python
client = CubeSDK(
    service_token="st_prod_xxx",
    default_env="production",
    base_url="https://api.cube.example.com",
    timeout=10,
    cache_ttl=600,  # 10 minutes
    api_version="v1",
)
```

## Requirements

- Python 3.9+
- `requests>=2.31.0`

## License

MIT
