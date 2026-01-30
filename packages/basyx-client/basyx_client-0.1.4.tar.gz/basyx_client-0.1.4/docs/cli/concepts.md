# basyx concepts

Operations for Concept Descriptions.

Concept Descriptions provide semantic definitions for submodel elements, enabling interoperability through shared understanding of data semantics.

## Commands

| Command | Description |
|---------|-------------|
| `list` | List all concept descriptions |
| `get` | Get a specific concept |
| `create` | Create a new concept |
| `delete` | Delete a concept |

## list

List all concept descriptions on the server.

```bash
basyx concepts list [OPTIONS]
```

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--limit` | `-l` | 100 | Maximum results |
| `--cursor` | `-c` | | Pagination cursor |
| `--id-short` | | | Filter by idShort |
| `--all` | `-a` | | Fetch all pages |

**Examples:**

```bash
# List all concepts
basyx concepts list

# Filter by idShort
basyx concepts list --id-short "Temperature"

# Output as JSON
basyx concepts list --format json
```

**Output:**

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┓
┃ ID                            ┃ ID Short     ┃ Preferred Name   ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━┩
│ 0173-1#02-AAO677#002          │ Temperature  │ Temperature      │
│ 0173-1#02-AAH880#003          │ SerialNumber │ Serial Number    │
└───────────────────────────────┴──────────────┴──────────────────┘
```

## get

Get a specific concept description by identifier.

```bash
basyx concepts get CONCEPT_ID
```

**Example:**

```bash
basyx concepts get "0173-1#02-AAO677#002"
```

## create

Create a new concept description from a JSON file.

```bash
basyx concepts create FILE
```

**Example:**

```bash
basyx concepts create temperature-concept.json
```

**Example JSON file:**

```json
{
  "id": "urn:example:concept:temperature",
  "idShort": "Temperature",
  "embeddedDataSpecifications": [
    {
      "dataSpecification": {
        "type": "ExternalReference",
        "keys": [
          {
            "type": "GlobalReference",
            "value": "https://admin-shell.io/DataSpecificationTemplates/DataSpecificationIEC61360/3/0"
          }
        ]
      },
      "dataSpecificationContent": {
        "modelType": "DataSpecificationIec61360",
        "preferredName": [
          {
            "language": "en",
            "text": "Temperature"
          },
          {
            "language": "de",
            "text": "Temperatur"
          }
        ],
        "shortName": [
          {
            "language": "en",
            "text": "Temp"
          }
        ],
        "unit": "°C",
        "dataType": "REAL_MEASURE"
      }
    }
  ]
}
```

## delete

Delete a concept description.

```bash
basyx concepts delete CONCEPT_ID [OPTIONS]
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--force` | `-f` | Skip confirmation |

**Example:**

```bash
basyx concepts delete "urn:example:concept:old" --force
```

## Working with ECLASS and IEC CDD

Concept Descriptions often reference standardized concept dictionaries:

### ECLASS

```bash
# Get ECLASS concept
basyx concepts get "0173-1#02-AAO677#002"
```

### IEC Common Data Dictionary

```bash
# Get IEC CDD concept
basyx concepts get "0112/2///61360_4#AAA123#001"
```

## Use Cases

### Semantic Interoperability

Concept descriptions enable different systems to understand each other:

```bash
# Export all concepts
basyx concepts list --all --format json > concepts.json

# Import to another server
for file in concepts/*.json; do
    basyx -u http://other:8081 concepts create "$file"
done
```
