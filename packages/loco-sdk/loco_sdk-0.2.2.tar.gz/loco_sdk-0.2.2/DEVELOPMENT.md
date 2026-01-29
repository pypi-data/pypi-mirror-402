# Development Guide

## Setup Development Environment

### Prerequisites

- Python 3.11+
- uv (recommended) or pip

### Install with uv (Recommended)

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Navigate to SDK directory
cd packages/loco-plugin-sdk

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows

# Install package with dev dependencies
uv pip install -e ".[dev]"
```

### Install with pip

```bash
cd packages/loco-plugin-sdk

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate  # Windows

# Install package with dev dependencies
pip install -e ".[dev]"
```

## Running Tests

### Run all tests

```bash
# With pytest
pytest

# With coverage
pytest --cov=loco_plugin_sdk --cov-report=html

# Verbose output
pytest -v
```

### Run specific tests

```bash
# Test specific file
pytest tests/test_auth_context.py

# Test specific function
pytest tests/test_auth_context.py::test_auth_context_oauth2_get_header

# Test with keyword
pytest -k "oauth"
```

### Watch mode (requires pytest-watch)

```bash
pip install pytest-watch
ptw
```

## Code Quality

### Format code

```bash
# Format with black
black src tests

# Check formatting
black --check src tests
```

### Lint code

```bash
# Run ruff
ruff check src tests

# Auto-fix issues
ruff check --fix src tests
```

### Type checking

```bash
# Run mypy
mypy src
```

### All checks

```bash
# Format, lint, and test
black src tests && ruff check src tests && pytest
```

## Project Structure

```
packages/loco-plugin-sdk/
├── src/
│   └── loco_plugin_sdk/
│       ├── __init__.py       # Public API
│       ├── version.py        # Version info
│       ├── core/             # Base classes
│       │   ├── base.py       # NodePlugin
│       │   ├── exceptions.py # Exception hierarchy
│       │   └── __init__.py
│       ├── auth/             # Auth helpers
│       │   ├── context.py    # AuthContext
│       │   └── __init__.py
│       ├── schemas/          # Future: Pydantic models
│       └── utils/            # Future: Utilities
├── tests/
│   ├── conftest.py           # Pytest fixtures
│   ├── test_auth_context.py # AuthContext tests
│   ├── test_node_plugin.py  # NodePlugin tests
│   └── test_exceptions.py   # Exception tests
├── pyproject.toml            # Package config
├── README.md                 # User documentation
└── DEVELOPMENT.md            # This file
```

## Adding New Features

### 1. Create the feature

```python
# src/loco_plugin_sdk/myfeature.py
def my_function():
    """My new feature."""
    pass
```

### 2. Export in **init**.py

```python
# src/loco_plugin_sdk/__init__.py
from loco_plugin_sdk.myfeature import my_function

__all__ = [
    # ... existing
    "my_function",
]
```

### 3. Add tests

```python
# tests/test_myfeature.py
def test_my_function():
    """Test my new feature."""
    result = my_function()
    assert result is not None
```

### 4. Update documentation

Update README.md with usage examples.

## Publishing

### Build package

```bash
# Install build tools
pip install build twine

# Build distributions
python -m build

# Check build
twine check dist/*
```

### Publish to PyPI

```bash
# Test PyPI (recommended first)
twine upload --repository testpypi dist/*

# Production PyPI
twine upload dist/*
```

### Version bumping

```bash
# Update version in src/loco_plugin_sdk/version.py
__version__ = "0.2.0"

# Update version in pyproject.toml
version = "0.2.0"

# Commit and tag
git commit -am "Bump version to 0.2.0"
git tag v0.2.0
git push && git push --tags
```

## Continuous Integration

### GitHub Actions (example)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Run tests
        run: |
          pytest --cov=loco_plugin_sdk --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Best Practices

### Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for public APIs
- Keep functions small and focused

### Testing

- Write tests for new features
- Maintain >80% code coverage
- Use descriptive test names
- Test edge cases and errors

### Documentation

- Update README for user-facing changes
- Add inline comments for complex logic
- Keep CHANGELOG.md updated

### Version Control

- Use feature branches
- Write clear commit messages
- Squash commits before merging
- Tag releases

## Troubleshooting

### Import errors

```bash
# Reinstall in editable mode
pip install -e .
```

### Test failures

```bash
# Run with verbose output
pytest -vv

# Show print statements
pytest -s
```

### Coverage not working

```bash
# Ensure coverage installed
pip install pytest-cov

# Clear cache
pytest --cache-clear
```
