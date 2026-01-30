# Error Handling

basyx-client provides a rich exception hierarchy for precise error handling.

## Exception Hierarchy

```
AASClientError
├── ResourceNotFoundError (404)
├── BadRequestError (400)
├── ConflictError (409)
├── UnauthorizedError (401)
├── ForbiddenError (403)
├── ServerError (5xx)
├── ConnectionError
└── TimeoutError
```

## Basic Error Handling

```python
from basyx_client import (
    AASClient,
    AASClientError,
    ResourceNotFoundError,
)

with AASClient("http://localhost:8081") as client:
    try:
        shell = client.shells.get("nonexistent-id")
    except ResourceNotFoundError:
        print("Shell not found")
    except AASClientError as e:
        print(f"API error: {e}")
```

## Specific Exception Types

### ResourceNotFoundError (404)

Raised when a requested resource doesn't exist:

```python
from basyx_client import ResourceNotFoundError

try:
    shell = client.shells.get("urn:nonexistent")
except ResourceNotFoundError as e:
    print(f"Not found: {e}")
    # Create the resource or handle gracefully
```

### BadRequestError (400)

Raised for invalid requests (malformed data, validation errors):

```python
from basyx_client import BadRequestError

try:
    client.shells.create({"invalid": "data"})
except BadRequestError as e:
    print(f"Invalid request: {e}")
```

### ConflictError (409)

Raised when a resource already exists:

```python
from basyx_client import ConflictError

try:
    client.shells.create(existing_shell)
except ConflictError:
    print("Shell already exists")
    # Maybe update instead of create
```

### UnauthorizedError (401)

Raised when authentication is required or invalid:

```python
from basyx_client import UnauthorizedError

try:
    result = client.shells.list()
except UnauthorizedError:
    print("Authentication required")
    # Prompt for credentials or refresh token
```

### ForbiddenError (403)

Raised when authenticated but lacking permissions:

```python
from basyx_client import ForbiddenError

try:
    client.shells.delete("urn:protected:aas")
except ForbiddenError:
    print("Permission denied")
```

### ServerError (5xx)

Raised for server-side errors:

```python
from basyx_client import ServerError

try:
    result = client.shells.list()
except ServerError as e:
    print(f"Server error: {e}")
    # Retry or alert operations team
```

### ConnectionError

Raised when the server is unreachable:

```python
from basyx_client import ConnectionError

try:
    result = client.shells.list()
except ConnectionError:
    print("Cannot connect to server")
    # Check network or server status
```

### TimeoutError

Raised when a request times out:

```python
from basyx_client import TimeoutError

try:
    result = client.shells.list()
except TimeoutError:
    print("Request timed out")
    # Retry with longer timeout
```

## Comprehensive Error Handling

```python
from basyx_client import (
    AASClient,
    ResourceNotFoundError,
    BadRequestError,
    ConflictError,
    UnauthorizedError,
    ForbiddenError,
    ServerError,
    ConnectionError,
    TimeoutError,
    AASClientError,
)

def safe_get_shell(client, aas_id):
    try:
        return client.shells.get(aas_id)
    except ResourceNotFoundError:
        return None
    except UnauthorizedError:
        raise RuntimeError("Invalid credentials")
    except ForbiddenError:
        raise RuntimeError("Access denied")
    except (ConnectionError, TimeoutError):
        raise RuntimeError("Server unavailable")
    except ServerError:
        raise RuntimeError("Server error - try again later")
    except AASClientError as e:
        raise RuntimeError(f"Unexpected error: {e}")
```

## Retry Pattern

```python
import time
from basyx_client import ServerError, TimeoutError, ConnectionError

def with_retry(func, max_attempts=3, delay=1.0):
    for attempt in range(max_attempts):
        try:
            return func()
        except (ServerError, TimeoutError, ConnectionError) as e:
            if attempt == max_attempts - 1:
                raise
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(delay * (attempt + 1))

# Usage
result = with_retry(lambda: client.shells.list())
```

## Async Error Handling

Same patterns work with async code:

```python
import asyncio
from basyx_client import ResourceNotFoundError

async def safe_get(client, aas_id):
    try:
        return await client.shells.get_async(aas_id)
    except ResourceNotFoundError:
        return None

async def main():
    async with AASClient("http://localhost:8081") as client:
        shell = await safe_get(client, "urn:example:aas:1")
```

## Logging Errors

```python
import logging
from basyx_client import AASClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    result = client.shells.list()
except AASClientError as e:
    logger.error(f"AAS API error: {e}", exc_info=True)
    raise
```
