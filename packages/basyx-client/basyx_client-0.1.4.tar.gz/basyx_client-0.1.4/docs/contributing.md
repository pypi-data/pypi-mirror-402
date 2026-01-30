# Contributing

See the full [CONTRIBUTING.md](https://github.com/hadijannat/basyx-client/blob/main/CONTRIBUTING.md) on GitHub.

## Quick Start

```bash
# Clone
git clone https://github.com/hadijannat/basyx-client.git
cd basyx-client

# Setup
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,cli,oauth,docs]"

# Verify
basyx --help
pytest tests/unit -v
```

## Running Tests

```bash
# Unit tests
pytest tests/unit -v

# With coverage
pytest tests/unit --cov=basyx_client

# Integration tests (requires Docker)
docker compose up -d
pytest tests/integration -v
```

## Code Quality

```bash
# Lint
ruff check src tests

# Format
ruff format src tests

# Type check
mypy src
```

## Documentation

```bash
# Serve locally
mkdocs serve

# Build
mkdocs build
```

## Pull Request Process

1. Fork and create a branch
2. Write tests for new functionality
3. Ensure all checks pass
4. Update CHANGELOG.md
5. Submit PR with clear description
