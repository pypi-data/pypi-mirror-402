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

3. Install in development mode with dev dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

4. (Optional) Install OAuth support:
   ```bash
   pip install -e ".[dev,oauth]"
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
│   └── endpoints/           # API endpoint implementations
│       ├── aas_repository.py
│       ├── submodel_repository.py
│       ├── submodel_elements.py
│       └── ...
├── tests/
│   ├── unit/                # Unit tests (no external deps)
│   └── integration/         # Integration tests (require Docker)
└── docker-compose.yml       # BaSyx server setup for testing
```

## Reporting Issues

- Use GitHub Issues for bug reports and feature requests
- Include Python version, OS, and relevant error messages
- Provide a minimal reproducible example when possible

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
