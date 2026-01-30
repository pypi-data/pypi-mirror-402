# Examples

Runnable example scripts demonstrating basyx-client usage.

## Prerequisites

1. Install basyx-client with CLI:
   ```bash
   pip install basyx-client[cli]
   ```

2. Start a BaSyx server:
   ```bash
   docker run -p 8081:8081 eclipsebasyx/aas-environment:2.0.0-milestone-03
   ```

## Running Examples

```bash
# Basic CRUD operations
python examples/basic_crud.py

# Async concurrent operations
python examples/async_concurrent.py

# OAuth2 with Keycloak
KEYCLOAK_TOKEN_URL=... KEYCLOAK_CLIENT_ID=... KEYCLOAK_CLIENT_SECRET=... \
python examples/oauth2_keycloak.py

# CLI scripting
bash examples/cli_scripting.sh
```

## Example Files

| File | Description |
|------|-------------|
| `basic_crud.py` | Create, read, update, delete operations |
| `async_concurrent.py` | Concurrent async requests |
| `oauth2_keycloak.py` | OAuth2 authentication with Keycloak |
| `pagination_large_dataset.py` | Handling large datasets with pagination |
| `cli_scripting.sh` | Shell scripting with the CLI |
