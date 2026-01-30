# basyx discovery

Operations for the AAS Discovery Service.

The Discovery Service maps asset identifiers to AAS identifiers, enabling lookup of digital twins by physical asset IDs.

## Commands

| Command | Description |
|---------|-------------|
| `lookup` | Find AAS IDs by asset ID |
| `link` | Link asset ID to AAS |
| `unlink` | Unlink asset ID from AAS |
| `list-links` | List all asset IDs for an AAS |

## lookup

Find AAS identifiers by asset identifier.

```bash
basyx discovery lookup ASSET_ID_TYPE ASSET_ID_VALUE [OPTIONS]
```

**Arguments:**

- `ASSET_ID_TYPE` - Type of asset ID (e.g., `globalAssetId`, `serialNumber`)
- `ASSET_ID_VALUE` - The asset ID value

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--limit` | `-l` | 100 | Maximum results |
| `--cursor` | `-c` | | Pagination cursor |

**Examples:**

```bash
# Lookup by global asset ID
basyx discovery lookup globalAssetId "urn:example:asset:motor-001"

# Lookup by serial number
basyx discovery lookup serialNumber "SN-12345678"

# Lookup by manufacturer part ID
basyx discovery lookup manufacturerPartId "MPD-ABC-123"
```

**Output:**

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ AAS ID                              ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ urn:example:aas:motor-001           │
│ urn:example:aas:motor-001-backup    │
└─────────────────────────────────────┘
```

## link

Create a link between an asset ID and an AAS.

```bash
basyx discovery link AAS_ID ASSET_ID_TYPE ASSET_ID_VALUE
```

**Examples:**

```bash
# Link global asset ID
basyx discovery link "urn:example:aas:motor-001" globalAssetId "urn:example:asset:motor-001"

# Link serial number
basyx discovery link "urn:example:aas:motor-001" serialNumber "SN-12345678"
```

## unlink

Remove a link between an asset ID and an AAS.

```bash
basyx discovery unlink AAS_ID ASSET_ID_TYPE ASSET_ID_VALUE [OPTIONS]
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--force` | `-f` | Skip confirmation |

**Example:**

```bash
basyx discovery unlink "urn:example:aas:motor-001" serialNumber "SN-OLD" --force
```

## list-links

List all asset IDs linked to a specific AAS.

```bash
basyx discovery list-links AAS_ID
```

**Example:**

```bash
basyx discovery list-links "urn:example:aas:motor-001"
```

**Output:**

```
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Asset ID Type      ┃ Asset ID Value             ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ globalAssetId      │ urn:example:asset:motor-001│
│ serialNumber       │ SN-12345678                │
│ manufacturerPartId │ MPD-ABC-123                │
└────────────────────┴────────────────────────────┘
```

## Use Cases

### Register a New Physical Asset

```bash
# Create the AAS
basyx shells create motor-aas.json

# Register in discovery service
basyx discovery link "urn:example:aas:motor-001" globalAssetId "urn:example:asset:motor-001"
basyx discovery link "urn:example:aas:motor-001" serialNumber "SN-12345678"
```

### Find Digital Twin by Nameplate Data

```bash
# Scan serial number from physical asset
SERIAL="SN-12345678"

# Look up the digital twin
AAS_ID=$(basyx discovery lookup serialNumber "$SERIAL" --format json | jq -r '.[0].aas_id')

# Get the digital twin data
basyx shells get "$AAS_ID"
```
