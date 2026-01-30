# Configuration

basyx-client supports multiple configuration methods for both CLI and SDK usage.

## CLI Configuration

### Configuration File

The CLI stores configuration in `~/.basyx/config.yaml`:

```yaml
default_profile: local

profiles:
  local:
    url: http://localhost:8081
    timeout: 30

  production:
    url: https://aas.company.com
    timeout: 60
    auth:
      type: oauth2
      token_url: https://auth.company.com/token
      client_id: basyx-client
      client_secret_env: BASYX_CLIENT_SECRET
```

### Initialize Configuration

```bash
# Create default config file
basyx config init

# Overwrite existing config
basyx config init --force
```

### View Configuration

```bash
# Show full configuration
basyx config show

# Show specific profile
basyx config show production

# List all profiles
basyx config profiles

# Get a specific value
basyx config get profiles.local.url
```

### Set Configuration Values

```bash
# Set URL for a profile
basyx config set profiles.production.url https://aas.company.com

# Set default profile
basyx config set default_profile production

# Set timeout
basyx config set profiles.local.timeout 60
```

## Profiles

Profiles allow you to manage multiple server configurations:

### Using Profiles

```bash
# Use default profile
basyx shells list

# Use specific profile
basyx --profile production shells list
basyx -p production shells list
```

### Authentication in Profiles

#### Bearer Token

```yaml
profiles:
  staging:
    url: https://staging.company.com
    auth:
      type: bearer
      token_env: BASYX_STAGING_TOKEN
```

#### OAuth2 Client Credentials

```yaml
profiles:
  production:
    url: https://aas.company.com
    auth:
      type: oauth2
      token_url: https://auth.company.com/token
      client_id: basyx-client
      client_secret_env: BASYX_CLIENT_SECRET
      scope: aas:read aas:write
```

## Environment Variables

Environment variables override configuration file settings:

| Variable | Description |
|----------|-------------|
| `BASYX_URL` | Server URL |
| `BASYX_TOKEN` | Bearer token |
| `BASYX_PROFILE` | Default profile name |

### Usage

```bash
# Override URL
BASYX_URL=http://other-server:8081 basyx shells list

# Use token from environment
export BASYX_TOKEN="your-token"
basyx shells list
```

## Command-Line Overrides

CLI flags have highest priority:

```bash
# Override URL
basyx --url http://other-server:8081 shells list

# Override with token
basyx --token "your-token" shells list

# Combine overrides
basyx --url http://server:8081 --token "token" shells list
```

## SDK Configuration

### Basic Configuration

```python
from basyx_client import AASClient

# Simple URL
client = AASClient("http://localhost:8081")

# With timeout
client = AASClient("http://localhost:8081", timeout=60.0)
```

### Authentication

```python
from basyx_client import AASClient
from basyx_client.auth import BearerAuth, OAuth2ClientCredentials

# Bearer token
client = AASClient(
    "http://localhost:8081",
    auth=BearerAuth("your-token")
)

# OAuth2
auth = OAuth2ClientCredentials(
    token_url="https://auth.company.com/token",
    client_id="basyx-client",
    client_secret="secret"
)
client = AASClient("http://localhost:8081", auth=auth)
```

### Certificate Authentication

```python
from basyx_client import AASClient
from basyx_client.auth import CertificateConfig

cert = CertificateConfig(
    cert_file="/path/to/client.crt",
    key_file="/path/to/client.key",
    ca_file="/path/to/ca.crt"  # Optional
)

client = AASClient("https://secure-server.com", cert=cert)
```

## Priority Order

Configuration is resolved in this order (highest to lowest):

1. CLI flags (`--url`, `--token`)
2. Environment variables (`BASYX_URL`, `BASYX_TOKEN`)
3. Profile configuration (`~/.basyx/config.yaml`)
4. Default values
