# Quickstart

This guide will get you up and running with basyx-client in minutes.

## Prerequisites

- basyx-client installed (`pip install basyx-client[cli]`)
- A running AAS server (e.g., BaSyx or AASX Server)

## CLI Quickstart

### Configure Your Server

```bash
# Set the default server URL
basyx config set profiles.local.url http://localhost:8081

# Verify configuration
basyx config show
```

### List Resources

```bash
# List all AAS shells
basyx shells list

# List submodels
basyx submodels list

# List concept descriptions
basyx concepts list
```

### Get Specific Resources

```bash
# Get an AAS shell by ID
basyx shells get "urn:example:aas:motor-001"

# Get a submodel
basyx submodels get "urn:example:submodel:nameplate"

# Get a submodel element value
basyx elements get-value "urn:example:submodel:sensors" "Temperature"
```

### Output Formats

```bash
# Table format (default)
basyx shells list

# JSON format
basyx shells list --format json

# YAML format
basyx shells list --format yaml
```

## SDK Quickstart

### Basic Usage

```python
from basyx_client import AASClient

# Create a client
with AASClient("http://localhost:8081") as client:
    # List shells
    result = client.shells.list()
    for shell in result.result:
        print(f"ID: {shell.id}, idShort: {shell.id_short}")
```

### Get and Update Values

```python
from basyx_client import AASClient

with AASClient("http://localhost:8081") as client:
    # Get element value
    temp = client.submodels.elements.get_value(
        "urn:example:submodel:sensors",
        "Temperature"
    )
    print(f"Current temperature: {temp}")

    # Set element value
    client.submodels.elements.set_value(
        "urn:example:submodel:sensors",
        "Setpoint",
        25.0
    )
```

### Async Operations

```python
import asyncio
from basyx_client import AASClient

async def main():
    async with AASClient("http://localhost:8081") as client:
        # Fetch multiple submodels concurrently
        result = await client.submodels.list_async()

        tasks = [
            client.submodels.get_async(sm.id)
            for sm in result.result[:5]
        ]
        submodels = await asyncio.gather(*tasks)

        for sm in submodels:
            print(f"Submodel: {sm.id_short}")

asyncio.run(main())
```

### With Authentication

```python
from basyx_client import AASClient
from basyx_client.auth import BearerAuth

auth = BearerAuth("your-token-here")

with AASClient("http://localhost:8081", auth=auth) as client:
    result = client.shells.list()
```

## Next Steps

- [Configuration Guide](configuration.md) - Learn about profiles and authentication
- [CLI Reference](../cli/overview.md) - Explore all CLI commands
- [Library Guide](../library/client.md) - Deep dive into the SDK
- [Examples](../examples/basic-crud.md) - See more code examples
