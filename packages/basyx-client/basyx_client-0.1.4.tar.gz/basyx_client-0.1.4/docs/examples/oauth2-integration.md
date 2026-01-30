# OAuth2 Integration

Integrate basyx-client with OAuth2/OpenID Connect providers.

## Prerequisites

Install OAuth2 support:

```bash
pip install basyx-client[oauth]
```

## Keycloak Integration

### Basic Setup

```python
from basyx_client import AASClient
from basyx_client.auth import OAuth2ClientCredentials

auth = OAuth2ClientCredentials(
    token_url="https://keycloak.example.com/realms/aas/protocol/openid-connect/token",
    client_id="basyx-client",
    client_secret="your-client-secret",
)

with AASClient("http://localhost:8081", auth=auth) as client:
    result = client.shells.list()
    print(f"Found {len(result.result)} shells")
```

### With Scopes

```python
auth = OAuth2ClientCredentials(
    token_url="https://keycloak.example.com/realms/aas/protocol/openid-connect/token",
    client_id="basyx-client",
    client_secret="your-client-secret",
    scope="openid profile aas:read aas:write",
)
```

### Environment Variables

Store secrets securely:

```python
import os

auth = OAuth2ClientCredentials(
    token_url=os.environ["OAUTH_TOKEN_URL"],
    client_id=os.environ["OAUTH_CLIENT_ID"],
    client_secret=os.environ["OAUTH_CLIENT_SECRET"],
)
```

## Token Refresh

Tokens are automatically refreshed before expiration:

```python
auth = OAuth2ClientCredentials(
    token_url="https://auth.example.com/token",
    client_id="basyx-client",
    client_secret="secret",
    token_refresh_buffer=120,  # Refresh 2 minutes before expiry
)

# Long-running application
with AASClient("http://localhost:8081", auth=auth) as client:
    while True:
        # Token automatically refreshed as needed
        result = client.shells.list()
        process(result)
        time.sleep(60)
```

## Azure AD

```python
auth = OAuth2ClientCredentials(
    token_url="https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
    client_id="your-client-id",
    client_secret="your-client-secret",
    scope="api://your-api-id/.default",
)
```

## Auth0

```python
auth = OAuth2ClientCredentials(
    token_url="https://your-domain.auth0.com/oauth/token",
    client_id="your-client-id",
    client_secret="your-client-secret",
    scope="read:aas write:aas",
)
```

## Async OAuth2

```python
import asyncio
from basyx_client import AASClient
from basyx_client.auth import OAuth2ClientCredentials

async def main():
    auth = OAuth2ClientCredentials(
        token_url="https://auth.example.com/token",
        client_id="basyx-client",
        client_secret="secret",
    )

    async with AASClient("http://localhost:8081", auth=auth) as client:
        result = await client.shells.list_async()
        print(f"Found {len(result.result)} shells")

asyncio.run(main())
```

## CLI with OAuth2

Configure OAuth2 in `~/.basyx/config.yaml`:

```yaml
profiles:
  production:
    url: https://aas.company.com
    auth:
      type: oauth2
      token_url: https://auth.company.com/token
      client_id: basyx-cli
      client_secret_env: BASYX_CLIENT_SECRET
      scope: aas:read aas:write
```

Then use the CLI:

```bash
export BASYX_CLIENT_SECRET="your-secret"
basyx -p production shells list
```

## Complete Example

```python
"""OAuth2 integration example with Keycloak."""

import os
from basyx_client import AASClient
from basyx_client.auth import OAuth2ClientCredentials

def main():
    # Configuration from environment
    auth = OAuth2ClientCredentials(
        token_url=os.environ["KEYCLOAK_TOKEN_URL"],
        client_id=os.environ["KEYCLOAK_CLIENT_ID"],
        client_secret=os.environ["KEYCLOAK_CLIENT_SECRET"],
        scope="openid",
    )

    base_url = os.environ.get("BASYX_URL", "http://localhost:8081")

    with AASClient(base_url, auth=auth) as client:
        # List shells
        result = client.shells.list()
        print(f"Authenticated! Found {len(result.result)} shells:")

        for shell in result.result:
            print(f"  - {shell.id_short}: {shell.id}")

if __name__ == "__main__":
    main()
```

Run with:

```bash
export KEYCLOAK_TOKEN_URL="https://keycloak.example.com/realms/aas/protocol/openid-connect/token"
export KEYCLOAK_CLIENT_ID="basyx-client"
export KEYCLOAK_CLIENT_SECRET="your-secret"
python oauth2_example.py
```
