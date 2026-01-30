# CLI Workflows

Practical workflows using the basyx CLI.

## Data Export

### Export All Shells

```bash
#!/bin/bash
# export-shells.sh

OUTPUT_DIR="./export"
mkdir -p "$OUTPUT_DIR"

basyx shells list --all --format json > "$OUTPUT_DIR/shells.json"
echo "Exported shells to $OUTPUT_DIR/shells.json"
```

### Export Submodel Values

```bash
#!/bin/bash
# export-values.sh

SUBMODEL_ID="urn:example:submodel:sensors"

basyx submodels value "$SUBMODEL_ID" --format json > values.json
echo "Exported values to values.json"
```

## Data Import

### Batch Import from Directory

```bash
#!/bin/bash
# import-shells.sh

for file in shells/*.json; do
    echo "Importing $file..."
    basyx shells create "$file" || echo "Failed: $file"
done
```

## Monitoring

### Watch Element Value

```bash
#!/bin/bash
# watch-temp.sh

SUBMODEL_ID="urn:example:submodel:sensors"
ELEMENT="Temperature"

while true; do
    VALUE=$(basyx elements get-value "$SUBMODEL_ID" "$ELEMENT" --format json | jq -r '.value')
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    echo "$TIMESTAMP | Temperature: $VALUE"
    sleep 5
done
```

### Health Check

```bash
#!/bin/bash
# health-check.sh

if basyx shells list --limit 1 > /dev/null 2>&1; then
    echo "OK: AAS server is responding"
    exit 0
else
    echo "FAIL: AAS server not responding"
    exit 1
fi
```

## Discovery Workflows

### Register New Asset

```bash
#!/bin/bash
# register-asset.sh

AAS_ID="urn:example:aas:motor-001"
ASSET_ID="urn:example:asset:motor-001"
SERIAL="SN-12345678"

# Create AAS
basyx shells create motor-aas.json

# Register in discovery service
basyx discovery link "$AAS_ID" globalAssetId "$ASSET_ID"
basyx discovery link "$AAS_ID" serialNumber "$SERIAL"

echo "Registered $AAS_ID with asset IDs"
```

### Find by Serial Number

```bash
#!/bin/bash
# find-by-serial.sh

SERIAL="$1"

if [ -z "$SERIAL" ]; then
    echo "Usage: $0 <serial-number>"
    exit 1
fi

AAS_ID=$(basyx discovery lookup serialNumber "$SERIAL" --format json | jq -r '.[0].aas_id')

if [ "$AAS_ID" != "null" ] && [ -n "$AAS_ID" ]; then
    echo "Found AAS: $AAS_ID"
    basyx shells get "$AAS_ID"
else
    echo "No AAS found for serial: $SERIAL"
    exit 1
fi
```

## Server Migration

### Copy Between Servers

```bash
#!/bin/bash
# migrate.sh

SOURCE_URL="http://old-server:8081"
TARGET_URL="http://new-server:8081"

# Export from source
basyx --url "$SOURCE_URL" shells list --all --format json > shells.json
basyx --url "$SOURCE_URL" submodels list --all --format json > submodels.json

# Import to target
for id in $(jq -r '.[].id' shells.json); do
    basyx --url "$SOURCE_URL" shells get "$id" --format json > "tmp_shell.json"
    basyx --url "$TARGET_URL" shells create tmp_shell.json || echo "Shell exists: $id"
done

rm tmp_shell.json
echo "Migration complete"
```

## Multi-Profile Usage

### Compare Environments

```bash
#!/bin/bash
# compare-envs.sh

echo "=== Local ==="
basyx -p local shells list --limit 5

echo ""
echo "=== Staging ==="
basyx -p staging shells list --limit 5

echo ""
echo "=== Production ==="
basyx -p production shells list --limit 5
```

## CI/CD Integration

### Validate AAS Structure

```bash
#!/bin/bash
# validate-aas.sh

set -e

echo "Checking AAS structure..."

# Verify shells exist
SHELL_COUNT=$(basyx shells list --format json | jq 'length')
if [ "$SHELL_COUNT" -eq 0 ]; then
    echo "FAIL: No shells found"
    exit 1
fi
echo "OK: Found $SHELL_COUNT shells"

# Verify critical submodel exists
if basyx submodels get "urn:critical:submodel" > /dev/null 2>&1; then
    echo "OK: Critical submodel exists"
else
    echo "FAIL: Critical submodel missing"
    exit 1
fi

echo "All validations passed!"
```

### Deploy AASX Package

```bash
#!/bin/bash
# deploy-aasx.sh

PACKAGE_FILE="$1"
SERVER_URL="${2:-http://localhost:8081}"

if [ ! -f "$PACKAGE_FILE" ]; then
    echo "Error: Package file not found: $PACKAGE_FILE"
    exit 1
fi

echo "Deploying $PACKAGE_FILE to $SERVER_URL..."
basyx --url "$SERVER_URL" aasx upload "$PACKAGE_FILE"

echo "Deployment complete!"
```

## Tips

### Use JSON + jq for Scripting

```bash
# Get specific fields
basyx shells list --format json | jq '.[].idShort'

# Filter results
basyx submodels list --format json | jq '.[] | select(.idShort | contains("Sensor"))'

# Count resources
basyx shells list --all --format json | jq 'length'
```

### Error Handling

```bash
#!/bin/bash
set -e  # Exit on error

# Or handle manually
if ! basyx shells get "$ID" > /dev/null 2>&1; then
    echo "Shell not found, creating..."
    basyx shells create shell.json
fi
```
