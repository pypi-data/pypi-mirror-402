# basyx registry

Operations for AAS and Submodel registries.

## Command Groups

| Command | Description |
|---------|-------------|
| `basyx registry shells` | AAS registry operations |
| `basyx registry submodels` | Submodel registry operations |

---

## basyx registry shells

Manage AAS descriptors in the registry.

### Commands

| Command | Description |
|---------|-------------|
| `list` | List all AAS descriptors |
| `get` | Get a specific descriptor |
| `create` | Register a new AAS |
| `delete` | Delete a registration |

### list

```bash
basyx registry shells list [OPTIONS]
```

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--limit` | `-l` | 100 | Maximum results |
| `--cursor` | `-c` | | Pagination cursor |
| `--all` | `-a` | | Fetch all pages |

**Example:**

```bash
basyx registry shells list --format json
```

### get

```bash
basyx registry shells get AAS_ID
```

**Example:**

```bash
basyx registry shells get "urn:example:aas:1"
```

### create

```bash
basyx registry shells create FILE
```

**Example descriptor file:**

```json
{
  "id": "urn:example:aas:motor-001",
  "idShort": "Motor001",
  "endpoints": [
    {
      "interface": "AAS-3.0",
      "protocolInformation": {
        "href": "http://localhost:8081/shells/dXJuOmV4YW1wbGU6YWFzOm1vdG9yLTAwMQ"
      }
    }
  ]
}
```

### delete

```bash
basyx registry shells delete AAS_ID [--force]
```

---

## basyx registry submodels

Manage Submodel descriptors in the registry.

### Commands

| Command | Description |
|---------|-------------|
| `list` | List all submodel descriptors |
| `get` | Get a specific descriptor |
| `create` | Register a new submodel |
| `delete` | Delete a registration |

### list

```bash
basyx registry submodels list [OPTIONS]
```

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--limit` | `-l` | 100 | Maximum results |
| `--cursor` | `-c` | | Pagination cursor |
| `--all` | `-a` | | Fetch all pages |

### get

```bash
basyx registry submodels get SUBMODEL_ID
```

### create

```bash
basyx registry submodels create FILE
```

**Example descriptor file:**

```json
{
  "id": "urn:example:submodel:sensors",
  "idShort": "Sensors",
  "semanticId": {
    "type": "ExternalReference",
    "keys": [
      {
        "type": "GlobalReference",
        "value": "https://example.com/semantics/sensors"
      }
    ]
  },
  "endpoints": [
    {
      "interface": "SUBMODEL-3.0",
      "protocolInformation": {
        "href": "http://localhost:8081/submodels/dXJuOmV4YW1wbGU6c3VibW9kZWw6c2Vuc29ycw"
      }
    }
  ]
}
```

### delete

```bash
basyx registry submodels delete SUBMODEL_ID [--force]
```

---

## Use Cases

### Register an AAS with Multiple Submodels

```bash
# Register the AAS
basyx registry shells create aas-descriptor.json

# Register associated submodels
basyx registry submodels create nameplate-descriptor.json
basyx registry submodels create sensors-descriptor.json
```

### List All Registered Services

```bash
# Get all AAS registrations as JSON
basyx registry shells list --all --format json > aas-registry.json

# Get all submodel registrations
basyx registry submodels list --all --format json > sm-registry.json
```
