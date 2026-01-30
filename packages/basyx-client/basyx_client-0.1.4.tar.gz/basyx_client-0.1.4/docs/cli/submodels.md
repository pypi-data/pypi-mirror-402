# basyx submodels

Operations for Submodel resources.

## Commands

| Command | Description |
|---------|-------------|
| `list` | List all submodels |
| `get` | Get a specific submodel |
| `create` | Create a new submodel |
| `delete` | Delete a submodel |
| `value` | Get submodel $value |

## list

List all submodels on the server.

```bash
basyx submodels list [OPTIONS]
```

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--limit` | `-l` | 100 | Maximum results |
| `--cursor` | `-c` | | Pagination cursor |
| `--semantic-id` | `-s` | | Filter by semantic ID |
| `--all` | `-a` | | Fetch all pages |

**Examples:**

```bash
# List first 20 submodels
basyx submodels list --limit 20

# Filter by semantic ID
basyx submodels list --semantic-id "https://admin-shell.io/idta/nameplate/2/0"

# Fetch all as JSON
basyx submodels list --all --format json
```

## get

Get a specific submodel by identifier.

```bash
basyx submodels get SUBMODEL_ID [OPTIONS]
```

**Arguments:**

- `SUBMODEL_ID` - The submodel identifier

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--level` | deep | Content level (deep/core) |

**Examples:**

```bash
# Get full submodel
basyx submodels get "urn:example:submodel:nameplate"

# Get core only (no nested elements)
basyx submodels get "urn:example:submodel:nameplate" --level core
```

## create

Create a new submodel from a JSON file.

```bash
basyx submodels create FILE
```

**Arguments:**

- `FILE` - Path to JSON file containing submodel definition

**Example:**

```bash
basyx submodels create sensors-submodel.json
```

**Example JSON file:**

```json
{
  "id": "urn:example:submodel:sensors",
  "idShort": "Sensors",
  "semanticId": {
    "type": "ExternalReference",
    "keys": [{
      "type": "GlobalReference",
      "value": "https://example.com/semantics/sensors"
    }]
  },
  "submodelElements": [
    {
      "modelType": "Property",
      "idShort": "Temperature",
      "valueType": "xs:double",
      "value": "25.0"
    }
  ]
}
```

## delete

Delete a submodel.

```bash
basyx submodels delete SUBMODEL_ID [OPTIONS]
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--force` | `-f` | Skip confirmation |

**Examples:**

```bash
# Delete with confirmation
basyx submodels delete "urn:example:submodel:1"

# Force delete
basyx submodels delete "urn:example:submodel:1" --force
```

## value

Get the $value serialization of a submodel.

```bash
basyx submodels value SUBMODEL_ID
```

This returns a compact value-only representation useful for data exchange.

**Example:**

```bash
basyx submodels value "urn:example:submodel:sensors" --format json
```

**Output:**

```json
{
  "Temperature": 25.5,
  "Humidity": 60.2,
  "Pressure": 1013.25
}
```
