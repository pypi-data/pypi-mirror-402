# basyx-client

[![PyPI version](https://img.shields.io/pypi/v/basyx-client)](https://pypi.org/project/basyx-client/)
[![Python versions](https://img.shields.io/pypi/pyversions/basyx-client)](https://pypi.org/project/basyx-client/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)
[![CI](https://github.com/hadijannat/basyx-client/actions/workflows/ci.yml/badge.svg)](https://github.com/hadijannat/basyx-client/actions)

A high-level, BaSyx-model-native HTTP client for the AAS Part 2 API v3.x.

## Why basyx-client?

Working with the AAS Part 2 API directly is painful:

1. **Identifier encoding** - Every identifier must be base64url encoded (without padding!)
2. **idShortPath encoding** - Brackets in paths like `Sensors[0]` must be URL-encoded as `%5B0%5D`
3. **No typed responses** - You get raw dictionaries, not BaSyx model objects
4. **Manual error handling** - Status codes must be checked and mapped to meaningful errors

basyx-client eliminates all of this friction:

```python
from basyx_client import AASClient

# All encoding happens automatically
with AASClient("http://localhost:8081") as client:
    # Get an AAS - returns basyx.aas.model.AssetAdministrationShell, not dict
    aas = client.shells.get("https://acme.org/ids/aas/55")
    print(aas.id_short)  # Type-safe attribute access

    # Access submodel elements with array indices - brackets encoded automatically
    temp = client.submodels.elements.get_value(
        "https://acme.org/ids/sm/sensors",
        "Measurements[0].Temperature"  # [0] becomes %5B0%5D automatically
    )
```

## Installation

```bash
pip install basyx-client
```

## Docker (GHCR)

The GitHub Actions workflow publishes a Docker image on release:

```bash
docker pull ghcr.io/hadijannat/basyx-client:<version>
```

The image contains Python with `basyx-client` installed and defaults to `python`.

## Features

- **Automatic encoding** - Base64url for identifiers, URL-encoding for idShortPath
- **Typed responses** - Returns `basyx.aas.model.*` objects, not dictionaries
- **Sync + async** - Both synchronous and asynchronous operation support
- **Full auth suite** - Bearer, Basic, OAuth2 client credentials, mTLS certificates
- **Proper exceptions** - `ResourceNotFoundError`, `ConflictError`, etc. instead of generic errors
- **Pagination helpers** - Easy iteration through paginated results

## Quick Start

### Basic Usage

Note: the BaSyx Docker images in `docker-compose.yml` expose the API at the root
(`http://localhost:8081`, no `/api/v3.0`). Some deployments mount the API at
`/api/v3.0` — set `base_url` accordingly.

```python
from basyx_client import AASClient

with AASClient("http://localhost:8081") as client:
    # List all AAS
    result = client.shells.list()
    for aas in result.items:
        print(f"{aas.id_short}: {aas.id}")

    # Get a specific AAS
    aas = client.shells.get("urn:example:aas:machine-001")

    # Get a submodel
    sm = client.submodels.get("urn:example:sm:operational-data")

    # Get/set element values
    temp = client.submodels.elements.get_value(
        "urn:example:sm:operational-data",
        "Sensors.Temperature"
    )
    client.submodels.elements.set_value(
        "urn:example:sm:operational-data",
        "Sensors.Temperature",
        25.5
    )
```

### Async Usage

```python
import asyncio
from basyx_client import AASClient

async def main():
    async with AASClient("http://localhost:8081") as client:
        # Concurrent fetches
        aas1, aas2 = await asyncio.gather(
            client.shells.get_async("urn:example:aas:1"),
            client.shells.get_async("urn:example:aas:2"),
        )
        print(aas1.id_short, aas2.id_short)

asyncio.run(main())
```

### Authentication

```python
from basyx_client import AASClient
from basyx_client.auth import BearerAuth, OAuth2ClientCredentials

# Bearer token
client = AASClient("http://localhost:8081", auth=BearerAuth("my-token"))

# Basic auth (shorthand)
client = AASClient("http://localhost:8081", auth=("username", "password"))

# OAuth2 client credentials
client = AASClient("http://localhost:8081", auth=OAuth2ClientCredentials(
    token_url="https://auth.example.com/oauth/token",
    client_id="my-client",
    client_secret="my-secret",
    scope="aas:read aas:write",
))

# mTLS
client = AASClient(
    "https://secure.example.com",
    cert=("/path/to/cert.pem", "/path/to/key.pem"),
)
```

### Error Handling

```python
from basyx_client import AASClient
from basyx_client.exceptions import ResourceNotFoundError, ConflictError

with AASClient("http://localhost:8081") as client:
    try:
        aas = client.shells.get("urn:nonexistent:aas")
    except ResourceNotFoundError as e:
        print(f"AAS not found: {e.message}")
        print(f"URL: {e.url}")

    try:
        client.shells.create(my_aas)
    except ConflictError:
        print("AAS already exists")
```

### Pagination

```python
from basyx_client import AASClient
from basyx_client.pagination import iterate_pages

with AASClient("http://localhost:8081/api/v3.0") as client:
    # Manual pagination
    result = client.shells.list(limit=10)
    while result.has_more:
        for aas in result.items:
            process(aas)
        result = client.shells.list(limit=10, cursor=result.cursor)

    # Automatic pagination
    for aas in iterate_pages(lambda limit, cursor: client.shells.list(limit, cursor)):
        process(aas)
```

## API Coverage

| Endpoint | Status |
|----------|--------|
| AAS Repository (`/shells`) | ✅ Full |
| Submodel Repository (`/submodels`) | ✅ Full |
| Submodel Elements (`/submodels/{id}/submodel-elements/{path}`) | ✅ Full |
| Concept Descriptions (`/concept-descriptions`) | ✅ Full |
| AAS Registry (`/shell-descriptors`) | ✅ Full |
| Submodel Registry (`/submodel-descriptors`) | ✅ Full |
| AASX Server (`/packages`) | ✅ Full |
| Discovery (`/lookup/shells`) | ✅ Full |

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/unit -v

# Run linter
ruff check src tests

# Type checking
mypy src

# Integration tests (requires Docker)
docker compose up -d
pytest tests/integration -v
docker compose down
```

## License

Apache License 2.0
