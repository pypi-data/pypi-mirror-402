# basyx-client

**Python CLI & SDK for the AAS Part 2 API**

basyx-client provides a high-level HTTP client for interacting with Asset Administration Shell (AAS) servers implementing the [AAS Part 2 API specification](https://industrialdigitaltwin.org/content-hub/downloads).

## Features

- **Complete CLI** - First-class command-line interface for all operations
- **BaSyx-native** - Returns basyx-python-sdk model objects, not raw dicts
- **Automatic encoding** - Handles base64url identifier encoding transparently
- **Full async support** - Both synchronous and asynchronous operations
- **Multiple auth schemes** - Bearer, Basic, OAuth2, and certificate auth
- **Type-safe** - Full type hints throughout

## Quick Start

=== "CLI"

    ```bash
    # Install with CLI support
    pip install basyx-client[cli]

    # Configure server URL
    basyx config set profiles.local.url http://localhost:8081

    # List AAS shells
    basyx shells list

    # Get a specific submodel
    basyx submodels get "urn:example:submodel:1"
    ```

=== "Python SDK"

    ```python
    from basyx_client import AASClient

    with AASClient("http://localhost:8081") as client:
        # List all shells
        result = client.shells.list()
        for shell in result.result:
            print(f"AAS: {shell.id}")

        # Get element value
        temp = client.submodels.elements.get_value(
            "urn:example:submodel:1",
            "Sensors.Temperature"
        )
        print(f"Temperature: {temp}")
    ```

## Installation

```bash
# Basic installation (SDK only)
pip install basyx-client

# With CLI support
pip install basyx-client[cli]

# With OAuth2 support
pip install basyx-client[cli,oauth]

# All features
pip install basyx-client[all]
```

## Supported Endpoints

| Endpoint | CLI Command | SDK Attribute |
|----------|-------------|---------------|
| AAS Repository | `basyx shells` | `client.shells` |
| Submodel Repository | `basyx submodels` | `client.submodels` |
| Submodel Elements | `basyx elements` | `client.submodels.elements` |
| AAS Registry | `basyx registry shells` | `client.aas_registry` |
| Submodel Registry | `basyx registry submodels` | `client.submodel_registry` |
| AASX Server | `basyx aasx` | `client.packages` |
| Discovery | `basyx discovery` | `client.discovery` |
| Concept Descriptions | `basyx concepts` | `client.concept_descriptions` |

## Compatibility

- **Python**: 3.10+
- **AAS Part 2 API**: v3.x
- **BaSyx Server**: v2.x
- **AASX Server**: v3.x

## Links

- [GitHub Repository](https://github.com/hadijannat/basyx-client)
- [PyPI Package](https://pypi.org/project/basyx-client/)
- [Eclipse BaSyx](https://www.eclipse.org/basyx/)
- [AAS Specifications](https://industrialdigitaltwin.org/)
