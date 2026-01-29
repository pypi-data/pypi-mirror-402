# Loco SDK

Official SDK for building Loco workflow plugins.

## Installation

### For Plugin Development

```bash
# Using pip
pip install loco-sdk

# Using uv (recommended)
uv pip install loco-sdk
```

### For SDK Development

```bash
# Clone repository
cd packages/loco-sdk

# Install with dev dependencies using uv
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv pip install -e ".[dev]"

# Or with pip
pip install -e ".[dev]"
```

## Quick Start

```python
from loco_sdk import NodePlugin

class MyNode(NodePlugin):
    """My custom node."""

    async def execute(self, inputs: dict, context: dict) -> dict:
        """
        Execute node logic.

        Args:
            inputs: Node input values
            context: Workflow execution context with auth, sys_vars, etc.

        Returns:
            Output values dictionary
        """
        # Get authentication if needed
        auth = context.get("auth")
        if auth:
            headers = auth.get_header()
            # Use headers for API calls

        # Process inputs
        result = do_something(inputs)

        # Return outputs
        return {"result": result}
```

## Authentication Helper

The SDK provides `AuthContext` to easily work with credentials:

```python
from loco_sdk import NodePlugin, AuthContext

class MyNode(NodePlugin):
    async def execute(self, inputs: dict, context: dict) -> dict:
        # Wrap auth dict with helper
        auth = AuthContext(context.get("auth"))

        # Get Authorization header
        headers = auth.get_header()
        # Returns: {"Authorization": "Bearer <token>"}

        # Check token expiry
        if auth.is_expired():
            raise AuthenticationError("Token expired")

        # Access properties
        provider = auth.provider  # e.g., "google"
        scopes = auth.scopes      # OAuth scopes

        # Use in API calls
        response = await client.get(url, headers=headers)
        return {"data": response.json()}
```

## Features

- **NodePlugin Base Class**: Simple interface for workflow nodes
- **AuthContext Helper**: Easy OAuth2/API key authentication
- **Type Safety**: Full Pydantic schema support (coming soon)
- **Manifest Loading**: Parse plugin.yaml files (coming soon)
- **Testing**: Comprehensive test suite with pytest

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed development guide including:

- Setting up development environment with uv
- Running tests with pytest
- Code formatting and linting
- Publishing to PyPI

### Quick Commands

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=loco_sdk --cov-report=html

# Format code
black src tests

# Lint code
ruff check src tests

# Type check
mypy src
```

## Documentation

See [docs/](docs/) for detailed guides (coming soon).

## Version

0.1.0
