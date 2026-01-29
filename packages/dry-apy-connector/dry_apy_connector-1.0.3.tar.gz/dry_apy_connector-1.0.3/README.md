# dry-apy-connector

Python client for Navigo3 API.

## Features

- 🔐 **Authentication** - credentials or token-based login
- 🔄 **Automatic logout** - automatic logout when context exits or program ends
- 🧵 **Thread-safe** - safe for concurrent API calls
- ⚡ **Batch execution** - execute multiple requests in a single call

## Installation

```bash
pip install dry_apy_connector
```

### Using uv

```bash
# From PyPI
uv add dry-apy-connector
```

## Quick Start

```python
from dry_apy_connector.ApiConnector import ApiConnector

# Using context manager (recommended) - logout is automatic
with ApiConnector("https://instance.navigo3.com/API") as connector:
    # Login with credentials
    connector.login_with_credentials("username", "password")

    # Execute API call
    project = connector.execute("project/get", {"id": 88})
    print(project)
    # Logout happens automatically when exiting the context
```

### Token Authentication

```python
with ApiConnector("https://instance.navigo3.com/API") as connector:
    connector.login_with_token("your-api-token")
    result = connector.execute("project/get", {"id": 88})
    # Logout happens automatically
```

## Usage

### Batch Execution (Same Endpoint)

Execute multiple calls to the same endpoint efficiently:

```python
from dry_apy_connector.ApiConnector import ApiConnector

with ApiConnector("https://instance.navigo3.com/API") as connector:
    connector.login_with_credentials("user", "password")

    # Multiple inputs for the same endpoint
    inputs = [{"id": 1}, {"id": 2}, {"id": 3}]
    projects = connector.execute_endpoint_batch("project/get", inputs)

    for project in projects:
        print(project)
```

### Batch Execution (Mixed Endpoints)

Execute multiple different API calls in a single HTTP request:

```python
from dry_apy_connector.ApiConnector import ApiConnector
from uuid import uuid1

with ApiConnector("https://instance.navigo3.com/API") as connector:
    connector.login_with_credentials("user", "password")

    # Create batch with different endpoints
    batch = [
        ApiConnector.create_request(
            str(uuid1()), "project/get", "EXECUTE", {"id": 1}
        ),
        ApiConnector.create_request(
            str(uuid1()), "user/list", "EXECUTE", {}
        ),
    ]

    responses = connector.call(batch)
```

### Validation

Validate input data before execution:

```python
with ApiConnector("https://instance.navigo3.com/API") as connector:
    connector.login_with_credentials("user", "password")

    validation = connector.validate("project/create", {"name": "Test"})
    if validation.get("valid"):
        result = connector.execute("project/create", {"name": "Test"})
```

### Custom Logger

```python
from loguru import logger

connector = ApiConnector("https://instance.navigo3.com/API", logger=logger)
```

## API Reference

### ApiConnector

```python
ApiConnector(base_address: str, logger: Optional[LoggerInterface] = None)
```

#### Authentication

| Method                                              | Description                                       |
| --------------------------------------------------- | ------------------------------------------------- |
| `login_with_credentials(login: str, password: str)` | Login with username and password                  |
| `login_with_token(token: str)`                      | Login with API token                              |
| `logout()`                                          | Logout and close session (automatic with context) |
| `is_logged_in() -> bool`                            | Check if authenticated                            |

#### Execution

| Method                                                                                       | Description                             |
| -------------------------------------------------------------------------------------------- | --------------------------------------- |
| `execute(method: str, input_data: dict \| list) -> dict \| list`                             | Execute single API call                 |
| `execute_endpoint_batch(method: str, requests_input_data: List[dict \| list]) -> List[dict]` | Execute multiple calls to same endpoint |
| `validate(method: str, input_data: dict) -> dict`                                            | Validate input without execution        |
| `call(requests_list: List[Dict]) -> List[dict]`                                              | Execute batch of mixed requests         |

#### Utility

| Method                                                                                                     | Description                               |
| ---------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| `create_request(request_uuid: str, method: str, request_type: str, input_data: dict \| list, ...) -> dict` | Create request object for batch execution |
| `close()`                                                                                                  | Close HTTP session (automatic on exit)    |

## Best Practices

1. **Use context manager** for automatic logout and cleanup:

```python
with ApiConnector(url) as connector:
    connector.login_with_credentials("user", "pass")
    # Your API calls
    # Logout happens automatically
```

2. **Reuse connector** - don't create new instances for each call

3. **Use batch execution** for multiple requests:

```python
# ✓ Good - single HTTP request
projects = connector.execute_endpoint_batch("project/get", inputs)

# ✗ Avoid - multiple HTTP requests
for item in items:
    connector.execute("project/get", item)
```

4. **Thread safety** - API calls are thread-safe after login, but don't call `login()` from multiple threads

5. **Manual logout** - only needed if not using context manager:

```python
connector = ApiConnector(url)
connector.login_with_credentials("user", "pass")
# Your API calls
connector.logout()  # Explicit logout
# Or let it happen automatically at program exit


## License

Proprietary - Navigo Solutions

## Support

For issues or questions, contact us at **vyvoj@navigo3.com**
```
