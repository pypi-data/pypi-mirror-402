# basyx shells

Operations for Asset Administration Shell (AAS) resources.

## Commands

| Command | Description |
|---------|-------------|
| `list` | List all AAS shells |
| `get` | Get a specific shell |
| `create` | Create a new shell |
| `delete` | Delete a shell |
| `refs` | Get submodel references |
| `asset-info` | Get asset information |

## list

List all AAS shells on the server.

```bash
basyx shells list [OPTIONS]
```

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--limit` | `-l` | 100 | Maximum results |
| `--cursor` | `-c` | | Pagination cursor |
| `--all` | `-a` | | Fetch all pages |

**Examples:**

```bash
# List first 10 shells
basyx shells list --limit 10

# List all shells
basyx shells list --all

# Output as JSON
basyx shells list --format json
```

## get

Get a specific AAS shell by identifier.

```bash
basyx shells get AAS_ID
```

**Arguments:**

- `AAS_ID` - The AAS identifier (URL-encoded automatically)

**Examples:**

```bash
# Get by URN identifier
basyx shells get "urn:example:aas:motor-001"

# Get by IRI identifier
basyx shells get "https://example.com/aas/001"

# Output as YAML
basyx shells get "urn:example:aas:1" --format yaml
```

## create

Create a new AAS shell from a JSON file.

```bash
basyx shells create FILE
```

**Arguments:**

- `FILE` - Path to JSON file containing AAS definition

**Example:**

```bash
# Create from file
basyx shells create motor-aas.json
```

**Example JSON file:**

```json
{
  "id": "urn:example:aas:motor-001",
  "idShort": "Motor001",
  "assetInformation": {
    "assetKind": "Instance",
    "globalAssetId": "urn:example:asset:motor-001"
  }
}
```

## delete

Delete an AAS shell.

```bash
basyx shells delete AAS_ID [OPTIONS]
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--force` | `-f` | Skip confirmation |

**Examples:**

```bash
# Delete with confirmation
basyx shells delete "urn:example:aas:1"

# Force delete
basyx shells delete "urn:example:aas:1" --force
```

## refs

Get submodel references for an AAS shell.

```bash
basyx shells refs AAS_ID
```

**Example:**

```bash
basyx shells refs "urn:example:aas:motor-001"
```

**Output:**

```
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Type     ┃ Value                        ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Submodel │ urn:example:submodel:namepl… │
│ Submodel │ urn:example:submodel:sensors │
└──────────┴──────────────────────────────┘
```

## asset-info

Get asset information for an AAS shell.

```bash
basyx shells asset-info AAS_ID
```

**Example:**

```bash
basyx shells asset-info "urn:example:aas:motor-001"
```
