# AASClient

The `AASClient` is the main entry point for interacting with AAS servers.

## Basic Usage

```python
from basyx_client import AASClient

# Simple initialization
client = AASClient("http://localhost:8081")

# Use as context manager (recommended)
with AASClient("http://localhost:8081") as client:
    shells = client.shells.list()
```

## Initialization Options

```python
from basyx_client import AASClient
from basyx_client.auth import BearerAuth

client = AASClient(
    base_url="http://localhost:8081",
    auth=BearerAuth("token"),       # Optional authentication
    timeout=30.0,                   # Request timeout in seconds
    verify_ssl=True,                # SSL certificate verification
)
```

## Endpoints

The client provides namespaced access to all API endpoints:

| Attribute | Type | Description |
|-----------|------|-------------|
| `client.shells` | `AASRepositoryEndpoint` | AAS shell operations |
| `client.submodels` | `SubmodelRepositoryEndpoint` | Submodel operations |
| `client.submodels.elements` | `SubmodelElementsEndpoint` | Element operations |
| `client.aas_registry` | `AASRegistryEndpoint` | AAS registry |
| `client.submodel_registry` | `SubmodelRegistryEndpoint` | Submodel registry |
| `client.packages` | `AASXServerEndpoint` | AASX packages |
| `client.discovery` | `DiscoveryEndpoint` | Discovery service |
| `client.concept_descriptions` | `ConceptDescriptionEndpoint` | Concept descriptions |

## Context Manager

Always use the client as a context manager to ensure proper cleanup:

```python
# Synchronous
with AASClient("http://localhost:8081") as client:
    result = client.shells.list()

# Asynchronous
async with AASClient("http://localhost:8081") as client:
    result = await client.shells.list_async()
```

## Synchronous vs Asynchronous

Every method has both sync and async variants:

```python
# Synchronous
result = client.shells.list()
shell = client.shells.get("urn:example:aas:1")

# Asynchronous
result = await client.shells.list_async()
shell = await client.shells.get_async("urn:example:aas:1")
```

## Automatic Encoding

The client automatically handles identifier encoding:

```python
# These are equivalent - encoding handled automatically
shell = client.shells.get("urn:example:aas:motor-001")
# Internally: GET /shells/dXJuOmV4YW1wbGU6YWFzOm1vdG9yLTAwMQ

# idShortPath encoding also automatic
value = client.submodels.elements.get_value(
    "urn:sm:1",
    "Sensors[0].Temperature"  # Brackets encoded automatically
)
```

## Return Types

The client returns typed BaSyx model objects:

```python
from basyx.aas.model import AssetAdministrationShell, Submodel

result = client.shells.list()
for shell in result.result:
    assert isinstance(shell, AssetAdministrationShell)
    print(shell.id)
    print(shell.id_short)
```

Registry endpoints return dictionaries (descriptor format):

```python
result = client.aas_registry.list()
for descriptor in result.result:
    assert isinstance(descriptor, dict)
    print(descriptor["id"])
```

## Error Handling

```python
from basyx_client import (
    AASClient,
    ResourceNotFoundError,
    BadRequestError,
    UnauthorizedError,
)

with AASClient("http://localhost:8081") as client:
    try:
        shell = client.shells.get("nonexistent")
    except ResourceNotFoundError:
        print("Shell not found")
    except UnauthorizedError:
        print("Authentication required")
    except BadRequestError as e:
        print(f"Invalid request: {e}")
```

## Multiple Clients

You can create multiple clients for different servers:

```python
with AASClient("http://server1:8081") as client1, \
     AASClient("http://server2:8081") as client2:
    # Fetch from server1
    shells1 = client1.shells.list()

    # Fetch from server2
    shells2 = client2.shells.list()
```
