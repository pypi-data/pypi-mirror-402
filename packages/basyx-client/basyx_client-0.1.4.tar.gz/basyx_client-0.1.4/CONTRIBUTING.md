# Contributing to basyx-client

Thank you for your interest in contributing to basyx-client! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Docker and Docker Compose (for integration tests)
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/hadijannat/basyx-client.git
   cd basyx-client
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install in development mode with all extras:
   ```bash
   pip install -e ".[dev,cli,oauth,docs]"
   ```

4. Verify CLI installation:
   ```bash
   basyx --help
   ```

## Running Tests

### Unit Tests

Unit tests run without external dependencies:

```bash
pytest tests/unit -v
```

### Integration Tests

Integration tests require BaSyx servers running via Docker:

```bash
# Start BaSyx services
docker compose up -d

# Wait for services to be ready (about 30-45 seconds)
sleep 45

# Run integration tests
pytest tests/integration -v

# Stop services when done
docker compose down
```

### All Tests

```bash
pytest tests -v
```

## Code Style

We use [Ruff](https://github.com/astral-sh/ruff) for linting and formatting.

### Linting

```bash
ruff check src tests
```

### Auto-fix Issues

```bash
ruff check --fix src tests
```

### Format Code

```bash
ruff format src tests
```

### Check Formatting

```bash
ruff format --check src tests
```

## Type Checking

We use [mypy](https://mypy.readthedocs.io/) for static type checking:

```bash
mypy src
```

Note: The basyx-python-sdk doesn't have type stubs, so some type errors from that package are suppressed.

## Pull Request Process

1. **Fork the repository** and create your branch from `main`.

2. **Write tests** for any new functionality or bug fixes.

3. **Ensure all checks pass**:
   ```bash
   ruff check src tests
   ruff format --check src tests
   mypy src
   pytest tests/unit -v
   ```

4. **Update documentation** if you've changed APIs or added features.

5. **Update CHANGELOG.md** with your changes under the `[Unreleased]` section.

6. **Submit a pull request** with a clear description of your changes.

### PR Guidelines

- Keep PRs focused on a single feature or fix
- Write clear commit messages
- Add tests for new functionality
- Update documentation as needed
- Follow existing code style and patterns

## Project Structure

```
basyx-client/
├── src/basyx_client/
│   ├── __init__.py          # Public API exports
│   ├── client.py            # AASClient main class
│   ├── auth.py              # Authentication handlers
│   ├── encoding.py          # Base64url and path encoding
│   ├── exceptions.py        # Exception hierarchy
│   ├── pagination.py        # Pagination utilities
│   ├── serialization.py     # BaSyx model serialization
│   ├── endpoints/           # API endpoint implementations
│   │   ├── aas_repository.py
│   │   ├── submodel_repository.py
│   │   └── ...
│   └── cli/                 # Command-line interface
│       ├── main.py          # CLI entry point
│       ├── config.py        # Configuration management
│       ├── output.py        # Output formatters
│       └── commands/        # Command implementations
│           ├── shells.py
│           ├── submodels.py
│           └── ...
├── docs/                    # MkDocs documentation
├── examples/                # Runnable example scripts
├── tests/
│   ├── unit/                # Unit tests (no external deps)
│   └── integration/         # Integration tests (require Docker)
└── docker-compose.yml       # BaSyx server setup for testing
```

## Adding CLI Commands

When adding new CLI commands:

1. Create a command file in `src/basyx_client/cli/commands/`
2. Follow existing patterns for argument handling
3. Use output formatters from `output.py` for consistent output
4. Add error handling with `print_error()` and `typer.Exit(1)`
5. Write tests in `tests/unit/test_cli.py`
6. Document in `docs/cli/`

Example command structure:
```python
@app.command("list")
def list_items(
    ctx: typer.Context,
    limit: int = typer.Option(100, "--limit", "-l", help="Max results"),
) -> None:
    """List all items."""
    with get_client_from_context(ctx) as client:
        try:
            result = client.endpoint.list(limit=limit)
            format_output(result.result, title="Items")
        except Exception as e:
            print_error(f"Failed: {e}")
            raise typer.Exit(1)
```

## Reporting Issues

- Use GitHub Issues for bug reports and feature requests
- Include Python version, OS, and relevant error messages
- Provide a minimal reproducible example when possible

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
