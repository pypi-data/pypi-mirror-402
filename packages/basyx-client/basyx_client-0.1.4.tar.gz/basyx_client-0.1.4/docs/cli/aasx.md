# basyx aasx

Operations for AASX packages.

## Commands

| Command | Description |
|---------|-------------|
| `list` | List all AASX packages |
| `get` | Get package information |
| `download` | Download a package |
| `upload` | Upload a package |
| `delete` | Delete a package |

## list

List all AASX packages on the server.

```bash
basyx aasx list [OPTIONS]
```

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--limit` | `-l` | 100 | Maximum results |
| `--cursor` | `-c` | | Pagination cursor |
| `--aas-id` | | | Filter by AAS ID |
| `--all` | `-a` | | Fetch all pages |

**Examples:**

```bash
# List all packages
basyx aasx list

# Filter by AAS
basyx aasx list --aas-id "urn:example:aas:1"
```

## get

Get information about a specific package.

```bash
basyx aasx get PACKAGE_ID
```

**Example:**

```bash
basyx aasx get "pkg-001"
```

## download

Download an AASX package file.

```bash
basyx aasx download PACKAGE_ID [OPTIONS]
```

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--output` | `-o` | `{id}.aasx` | Output file path |

**Examples:**

```bash
# Download with default name
basyx aasx download "pkg-001"

# Specify output path
basyx aasx download "pkg-001" --output motor-data.aasx
```

## upload

Upload an AASX package file.

```bash
basyx aasx upload FILE [OPTIONS]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--aas-id` | Associate with specific AAS |

**Examples:**

```bash
# Simple upload
basyx aasx upload motor-data.aasx

# Associate with AAS
basyx aasx upload motor-data.aasx --aas-id "urn:example:aas:motor"
```

## delete

Delete an AASX package.

```bash
basyx aasx delete PACKAGE_ID [OPTIONS]
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--force` | `-f` | Skip confirmation |

**Example:**

```bash
basyx aasx delete "pkg-001" --force
```

## Working with AASX Files

### Export and Import Workflow

```bash
# Download all packages
for pkg in $(basyx aasx list --format json | jq -r '.[].package_id'); do
    basyx aasx download "$pkg" -o "backup-$pkg.aasx"
done

# Upload to new server
basyx -u http://new-server:8081 aasx upload backup-pkg-001.aasx
```

### Integration with AASX Package Explorer

AASX files downloaded with this CLI are compatible with:

- [AASX Package Explorer](https://github.com/admin-shell-io/aasx-package-explorer)
- Other AAS tools supporting the AASX format
