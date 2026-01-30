# basyx elements

Operations for Submodel Elements within submodels.

## Commands

| Command | Description |
|---------|-------------|
| `list` | List elements in a submodel |
| `get` | Get a specific element |
| `get-value` | Get element value |
| `set-value` | Set element value |
| `create` | Create a new element |
| `delete` | Delete an element |
| `invoke` | Invoke an operation |

## idShort Path

Many commands require an `idShortPath` to identify nested elements:

- Simple: `Temperature`
- Nested: `Sensors.Temperature`
- Collection: `SensorArray[0]`
- Deep: `Equipment.Motor.Parameters.Speed`

## list

List all elements in a submodel.

```bash
basyx elements list SUBMODEL_ID [OPTIONS]
```

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--limit` | `-l` | 100 | Maximum results |
| `--cursor` | `-c` | | Pagination cursor |
| `--all` | `-a` | | Fetch all pages |

**Example:**

```bash
basyx elements list "urn:example:submodel:sensors"
```

**Output:**

```
┏━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━┓
┃ ID Short     ┃ Type     ┃ Value ┃ Value Type  ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━┩
│ Temperature  │ Property │ 25.5  │ double      │
│ Humidity     │ Property │ 60.2  │ double      │
│ Status       │ Property │ OK    │ string      │
└──────────────┴──────────┴───────┴─────────────┘
```

## get

Get a specific submodel element.

```bash
basyx elements get SUBMODEL_ID ID_SHORT_PATH
```

**Example:**

```bash
basyx elements get "urn:example:submodel:sensors" "Temperature"
```

## get-value

Get just the value of an element.

```bash
basyx elements get-value SUBMODEL_ID ID_SHORT_PATH
```

**Examples:**

```bash
# Get simple property value
basyx elements get-value "urn:example:submodel:1" "Temperature"

# Get nested element value
basyx elements get-value "urn:example:submodel:1" "Sensors.Temperature"

# Get collection element
basyx elements get-value "urn:example:submodel:1" "DataPoints[0]"
```

## set-value

Set the value of an element.

```bash
basyx elements set-value SUBMODEL_ID ID_SHORT_PATH VALUE
```

**Arguments:**

- `VALUE` - New value (JSON or primitive string)

**Examples:**

```bash
# Set numeric value
basyx elements set-value "urn:sm:1" "Temperature" "25.5"

# Set string value
basyx elements set-value "urn:sm:1" "Status" "Running"

# Set complex value (JSON)
basyx elements set-value "urn:sm:1" "Config" '{"enabled": true, "interval": 60}'
```

## create

Create a new element in a submodel.

```bash
basyx elements create SUBMODEL_ID FILE [OPTIONS]
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--parent` | `-p` | Parent idShortPath for nested creation |

**Examples:**

```bash
# Create at root level
basyx elements create "urn:sm:1" new-property.json

# Create nested element
basyx elements create "urn:sm:1" temp-prop.json --parent "Sensors"
```

**Example JSON file:**

```json
{
  "modelType": "Property",
  "idShort": "NewSensor",
  "valueType": "xs:double",
  "value": "0.0"
}
```

## delete

Delete a submodel element.

```bash
basyx elements delete SUBMODEL_ID ID_SHORT_PATH [OPTIONS]
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--force` | `-f` | Skip confirmation |

**Example:**

```bash
basyx elements delete "urn:sm:1" "OldSensor" --force
```

## invoke

Invoke an Operation element.

```bash
basyx elements invoke SUBMODEL_ID ID_SHORT_PATH [OPTIONS]
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--input` | `-i` | JSON file with input arguments |
| `--async` | | Invoke asynchronously |
| `--timeout` | `-t` | Operation timeout (seconds) |

**Examples:**

```bash
# Invoke with no arguments
basyx elements invoke "urn:sm:1" "Reset"

# Invoke with input file
basyx elements invoke "urn:sm:1" "Calculate" --input args.json

# Async invocation
basyx elements invoke "urn:sm:1" "LongOperation" --async
```

**Example input file:**

```json
{
  "inputArguments": [
    {
      "value": {
        "modelType": "Property",
        "idShort": "multiplier",
        "valueType": "xs:int",
        "value": "2"
      }
    }
  ]
}
```
