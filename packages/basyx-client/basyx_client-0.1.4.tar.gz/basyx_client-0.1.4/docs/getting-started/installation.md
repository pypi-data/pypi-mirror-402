# Installation

## Requirements

- Python 3.10 or later
- pip or another Python package manager

## Basic Installation

Install the core SDK:

```bash
pip install basyx-client
```

## Installation with Extras

### CLI Support

To use the `basyx` command-line tool:

```bash
pip install basyx-client[cli]
```

This installs additional dependencies:

- **typer** - Modern CLI framework
- **rich** - Beautiful terminal output
- **pyyaml** - Configuration file support

### OAuth2 Support

For OAuth2 authentication (e.g., with Keycloak):

```bash
pip install basyx-client[oauth]
```

This installs:

- **authlib** - OAuth2 client credentials flow

### Documentation Tools

For building the documentation locally:

```bash
pip install basyx-client[docs]
```

### All Features

Install everything:

```bash
pip install basyx-client[all]
```

Or specify multiple extras:

```bash
pip install basyx-client[cli,oauth]
```

## Verify Installation

### Check SDK

```python
from basyx_client import AASClient, __version__
print(f"basyx-client {__version__}")
```

### Check CLI

```bash
basyx --version
basyx --help
```

## Development Installation

For contributing to basyx-client:

```bash
git clone https://github.com/hadijannat/basyx-client.git
cd basyx-client
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev,cli,oauth,docs]"
```

## Docker

You can run a BaSyx server for testing:

```bash
docker run -p 8081:8081 eclipsebasyx/aas-environment:2.0.0-milestone-03
```

Or use Docker Compose with the provided configuration:

```bash
docker compose up -d
```
