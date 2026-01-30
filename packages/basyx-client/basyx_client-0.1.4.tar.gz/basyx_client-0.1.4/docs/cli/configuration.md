# basyx config

Manage CLI configuration profiles and settings.

## Commands

| Command | Description |
|---------|-------------|
| `show` | Show configuration |
| `set` | Set a configuration value |
| `get` | Get a configuration value |
| `profiles` | List all profiles |
| `init` | Initialize config file |

## show

Display current configuration or a specific profile.

```bash
basyx config show [PROFILE]
```

**Examples:**

```bash
# Show full configuration
basyx config show

# Show specific profile
basyx config show production
```

**Output:**

```yaml
default_profile: local
profiles:
  local:
    url: http://localhost:8081
    timeout: 30
  production:
    url: https://aas.company.com
    auth:
      type: oauth2
      token_url: https://auth.company.com/token
      client_id: basyx-client
```

## set

Set a configuration value using dot notation.

```bash
basyx config set KEY VALUE
```

**Examples:**

```bash
# Set URL for local profile
basyx config set profiles.local.url http://localhost:8082

# Set default profile
basyx config set default_profile production

# Set timeout
basyx config set profiles.production.timeout 60

# Set OAuth2 configuration
basyx config set profiles.production.auth.type oauth2
basyx config set profiles.production.auth.token_url https://auth.company.com/token
basyx config set profiles.production.auth.client_id basyx-client
basyx config set profiles.production.auth.client_secret_env BASYX_SECRET
```

## get

Get a specific configuration value.

```bash
basyx config get KEY
```

**Examples:**

```bash
# Get URL
basyx config get profiles.local.url
# Output: http://localhost:8081

# Get auth type
basyx config get profiles.production.auth.type
# Output: oauth2
```

## profiles

List all configured profiles.

```bash
basyx config profiles
```

**Output:**

```
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━┓
┃ Name        ┃ URL                     ┃ Auth   ┃ Default ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━┩
│ local       │ http://localhost:8081   │ -      │ ✓       │
│ staging     │ https://staging.co.com  │ bearer │         │
│ production  │ https://aas.company.com │ oauth2 │         │
└─────────────┴─────────────────────────┴────────┴─────────┘
```

## init

Initialize the configuration file with defaults.

```bash
basyx config init [OPTIONS]
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--force` | `-f` | Overwrite existing config |

**Examples:**

```bash
# Create default config
basyx config init

# Overwrite existing
basyx config init --force
```

## Configuration File

Located at `~/.basyx/config.yaml`:

```yaml
default_profile: local

profiles:
  local:
    url: http://localhost:8081
    timeout: 30

  staging:
    url: https://staging.company.com
    timeout: 30
    auth:
      type: bearer
      token_env: BASYX_STAGING_TOKEN

  production:
    url: https://aas.company.com
    timeout: 60
    auth:
      type: oauth2
      token_url: https://auth.company.com/token
      client_id: basyx-client
      client_secret_env: BASYX_CLIENT_SECRET
      scope: aas:read aas:write
```

## Authentication Types

### Bearer Token

```yaml
auth:
  type: bearer
  token_env: BASYX_TOKEN  # Environment variable name
```

### OAuth2 Client Credentials

```yaml
auth:
  type: oauth2
  token_url: https://auth.company.com/token
  client_id: basyx-client
  client_secret_env: BASYX_SECRET  # From environment
  scope: aas:read aas:write  # Optional
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `BASYX_URL` | Override server URL |
| `BASYX_TOKEN` | Bearer token |
| `BASYX_PROFILE` | Default profile name |

Custom environment variables can be referenced in config using `*_env` keys.
