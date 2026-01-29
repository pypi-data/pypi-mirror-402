# Modulo SDK

Python SDK for Modulo API.

## Quick Start

```python
from modulo import ModuloClient

client = ModuloClient(
    api_key="your-api-key",
    project_id="project-123",
)

# List integrations
integrations = client.integrations.list()

# List kits
kits = client.kits.list()

# Execute an action
result = client.actions.execute(
    kit_id="kit-123",
    action_id="action-456",
    arguments={"param": "value"},
)
```

## Async Client

```python
from modulo import AsyncModuloClient

async with AsyncModuloClient(api_key="...", project_id="...") as client:
    kits = await client.kits.list()
```

## Configuration

| Variable | Description |
|----------|-------------|
| `MODULO_API_KEY` | API key |
| `MODULO_BASE_URL` | Base URL override |

### Environments

```python
# Production (default)
client = ModuloClient(environment="production", ...)

# Staging
client = ModuloClient(environment="staging", ...)

# Development
client = ModuloClient(environment="development", ...)
```

## Available Resources

- `client.integrations` - List and retrieve integrations
- `client.kits` - List, retrieve, and delete integration kits
- `client.actions` - List, retrieve, and execute actions
