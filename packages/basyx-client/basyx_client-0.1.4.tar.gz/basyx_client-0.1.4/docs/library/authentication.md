# Authentication

basyx-client supports multiple authentication methods.

## Bearer Token

Simple token-based authentication:

```python
from basyx_client import AASClient
from basyx_client.auth import BearerAuth

auth = BearerAuth("your-token-here")

with AASClient("http://localhost:8081", auth=auth) as client:
    result = client.shells.list()
```

### From Environment Variable

```python
import os
from basyx_client.auth import BearerAuth

token = os.environ.get("BASYX_TOKEN")
auth = BearerAuth(token)
```

## Basic Authentication

Username and password authentication:

```python
from httpx import BasicAuth
from basyx_client import AASClient

auth = BasicAuth("username", "password")

with AASClient("http://localhost:8081", auth=auth) as client:
    result = client.shells.list()
```

## OAuth2 Client Credentials

For OAuth2/OpenID Connect (e.g., Keycloak):

```python
from basyx_client import AASClient
from basyx_client.auth import OAuth2ClientCredentials

auth = OAuth2ClientCredentials(
    token_url="https://keycloak.example.com/realms/aas/protocol/openid-connect/token",
    client_id="basyx-client",
    client_secret="your-client-secret",
    scope="openid profile",  # Optional
)

with AASClient("http://localhost:8081", auth=auth) as client:
    result = client.shells.list()
```

### Token Refresh

OAuth2 tokens are automatically refreshed before expiration:

```python
# Default: refresh 60 seconds before expiry
auth = OAuth2ClientCredentials(
    token_url="...",
    client_id="...",
    client_secret="...",
    token_refresh_buffer=120,  # Refresh 2 minutes early
)
```

### Installation

OAuth2 support requires the `oauth` extra:

```bash
pip install basyx-client[oauth]
```

## Certificate Authentication (mTLS)

For mutual TLS authentication:

```python
from basyx_client import AASClient
from basyx_client.auth import CertificateConfig

cert = CertificateConfig(
    cert_file="/path/to/client.crt",
    key_file="/path/to/client.key",
    ca_file="/path/to/ca.crt",  # Optional CA bundle
)

with AASClient("https://secure-server.com", cert=cert) as client:
    result = client.shells.list()
```

### Combined Certificate + Key File

```python
cert = CertificateConfig(
    cert_file="/path/to/combined.pem",  # Contains both cert and key
)
```

## Custom Authentication

Implement custom auth by subclassing `httpx.Auth`:

```python
import httpx
from basyx_client import AASClient

class CustomAuth(httpx.Auth):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def auth_flow(self, request):
        request.headers["X-API-Key"] = self.api_key
        yield request

auth = CustomAuth("my-api-key")

with AASClient("http://localhost:8081", auth=auth) as client:
    result = client.shells.list()
```

## SSL/TLS Configuration

### Disable SSL Verification (Not Recommended)

```python
# For development only!
with AASClient("https://self-signed.local", verify_ssl=False) as client:
    result = client.shells.list()
```

### Custom CA Bundle

```python
with AASClient(
    "https://internal-server.company.com",
    verify_ssl="/path/to/internal-ca.crt"
) as client:
    result = client.shells.list()
```

## Async Authentication

All authentication methods work with async operations:

```python
async with AASClient("http://localhost:8081", auth=auth) as client:
    result = await client.shells.list_async()
```
