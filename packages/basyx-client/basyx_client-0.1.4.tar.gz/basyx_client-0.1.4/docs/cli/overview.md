# CLI Overview

The `basyx` command-line interface provides full access to AAS Part 2 API operations.

## Installation

```bash
pip install basyx-client[cli]
```

## Basic Usage

```bash
basyx [OPTIONS] COMMAND [ARGS]...
```

## Global Options

| Option | Short | Description |
|--------|-------|-------------|
| `--url URL` | `-u` | Server URL (overrides profile) |
| `--profile NAME` | `-p` | Config profile to use |
| `--token TOKEN` | `-t` | Bearer token for auth |
| `--format FORMAT` | `-f` | Output format: json, yaml, table |
| `--verbose` | `-v` | Enable verbose output |
| `--version` | `-V` | Show version |
| `--help` | | Show help message |

## Command Groups

| Command | Description |
|---------|-------------|
| `basyx shells` | AAS shell operations |
| `basyx submodels` | Submodel operations |
| `basyx elements` | Submodel element operations |
| `basyx registry shells` | AAS registry operations |
| `basyx registry submodels` | Submodel registry operations |
| `basyx aasx` | AASX package operations |
| `basyx discovery` | Discovery service operations |
| `basyx concepts` | Concept description operations |
| `basyx config` | Configuration management |

## Output Formats

### Table (Default)

```bash
basyx shells list
```

```
┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┓
┃ ID                    ┃ ID Short   ┃ Global Asset ID       ┃
┡━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━┩
│ urn:example:aas:1     │ Motor001   │ urn:example:asset:1   │
│ urn:example:aas:2     │ Pump002    │ urn:example:asset:2   │
└───────────────────────┴────────────┴───────────────────────┘
```

### JSON

```bash
basyx shells list --format json
```

```json
[
  {
    "id": "urn:example:aas:1",
    "id_short": "Motor001"
  }
]
```

### YAML

```bash
basyx shells list --format yaml
```

```yaml
- id: urn:example:aas:1
  id_short: Motor001
```

## Pagination

Commands that list resources support pagination:

```bash
# Limit results
basyx shells list --limit 10

# Use cursor for next page
basyx shells list --cursor "abc123"

# Fetch all pages
basyx shells list --all
```

## Error Handling

Errors are displayed with helpful messages:

```bash
$ basyx shells get "nonexistent-id"
✗ Failed to get shell: Resource not found (404)
```

## Shell Completion

Generate shell completions:

```bash
# Bash
basyx --install-completion bash

# Zsh
basyx --install-completion zsh

# Fish
basyx --install-completion fish
```

## Scripting

The CLI works well in scripts:

```bash
#!/bin/bash

# List all shell IDs
basyx shells list --format json | jq -r '.[].id'

# Get specific value
TEMP=$(basyx elements get-value "urn:sm:1" "Temp" --format json | jq -r '.value')
echo "Temperature: $TEMP"
```

## Profiles

Use profiles for different environments:

```bash
# Use local profile (default)
basyx shells list

# Use production profile
basyx -p production shells list

# Override URL
basyx -u http://other:8081 shells list
```
