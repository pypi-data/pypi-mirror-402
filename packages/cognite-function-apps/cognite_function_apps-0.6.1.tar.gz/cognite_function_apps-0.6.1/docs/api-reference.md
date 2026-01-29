# API Reference

Complete API documentation for the Function Apps framework.

## Quick Reference

### Basic Usage Pattern

```python
from cognite_function_apps import FunctionApp, create_function_service
from cognite.client import CogniteClient
from pydantic import BaseModel

# Create app
app = FunctionApp(title="My API", version="1.0.0")

# Define models
class Item(BaseModel):
    name: str
    price: float

# Define endpoints
@app.get("/items/{item_id}")
def get_item(client: CogniteClient, item_id: int) -> dict[str, Any]:
    """Retrieve an item by ID"""
    return {"id": item_id}

@app.post("/items/", status_code=201)
def create_item(client: CogniteClient, item: Item) -> dict[str, Any]:
    """Create a new item"""
    return {"id": 123, "item": item.model_dump()}

# Create service
handle = create_function_service(app)
```

### Common Patterns

#### Route Decorators

```python
@app.get(path)      # Retrieve data
@app.post(path)     # Create or process data
@app.put(path)      # Update resources
@app.delete(path)   # Delete resources
```

All route decorators support these parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `str` | (required) | Route path pattern (e.g., "/items/{item_id}") |
| `content_type` | `str` | `"application/json"` | Response MIME type |
| `accept` | `str \| None` | `None` | Accept header for content negotiation |
| `status_code` | `int` | `200` | Default success status code |
| `cache_control` | `str \| None` | `None` | Cache-Control header value |
| `extra_headers` | `Mapping[str, str] \| None` | `None` | Additional response headers |

#### Handler Parameters

```python
@app.post("/categories/{category_id}/items")
def create_item(
    client: CogniteClient,              # Framework dependency (required)
    logger: logging.Logger,             # Framework dependency (optional)
    headers: RequestHeaders,            # Request headers (optional)
    category_id: int,                   # Path parameter
    item: Item,                         # Request body
    notify: bool = False                # Query parameter
) -> dict[str, Any]:
    return {"category_id": category_id, "item": item.model_dump()}
```

#### Service Creation

```python
# Single app
handle = create_function_service(app)

# Multiple apps (composition)
handle = create_function_service(introspection, main_app)

# With custom dependencies
handle = create_function_service(app, registry=custom_registry)
```

### Request/Response Format

**Request:**

```json
{
    "path": "/items/123?include_tax=true",
    "method": "GET",
    "body": {},
    "headers": {"accept": "application/json"}
}
```

**Success Response:**

```json
{
    "status_code": 200,
    "data": {...},
    "headers": {
        "content-type": "application/json"
    }
}
```

**Error Response:**

```json
{
    "status_code": 400,
    "error_type": "ValidationError",
    "message": "Input validation failed",
    "details": {...},
    "headers": {
        "content-type": "application/json"
    }
}
```

Use `status_code < 400` to determine if a response is successful or an error.

See [Error Handling](error-handling.md) for complete error documentation.

## Detailed API Reference

The following sections provide complete API documentation auto-generated from the source code.

### Core Classes

#### FunctionApp

::: cognite_function_apps.FunctionApp
    options:
      show_root_heading: true
      show_source: false
      members_order: source
      show_signature_annotations: true

### Response Wrapper

#### Response[T]

Generic response wrapper for dynamic status codes and headers at runtime.

```python
from cognite_function_apps import Response

@app.post("/items")
def create_item(client: CogniteClient, item: Item) -> Response[Item]:
    """Create item with dynamic status code"""
    if async_mode:
        return Response(data=item, status_code=202, cache_control="no-store")
    return Response(data=item, status_code=201)
```

**Fields:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `data` | `T` | (required) | The actual response data |
| `status_code` | `int` | `200` | HTTP status code |
| `cache_control` | `str \| None` | `None` | Cache-Control header |
| `extra_headers` | `dict[str, str] \| None` | `None` | Additional headers |

The type parameter `T` preserves return type information for OpenAPI schema generation.

See [Response Customization](response-customization.md) for complete documentation.

### Service Creation

#### create_function_service

::: cognite_function_apps.create_function_service
    options:
      show_root_heading: true
      show_source: false
      show_signature_annotations: true

### Dependency Injection

#### DependencyRegistry

::: cognite_function_apps.dependency_registry.DependencyRegistry
    options:
      show_root_heading: true
      show_source: false
      members_order: source

#### create_default_registry

::: cognite_function_apps.create_default_registry
    options:
      show_root_heading: true
      show_source: false

### Introspection

#### create_introspection_app

::: cognite_function_apps.introspection.create_introspection_app
    options:
      show_root_heading: true
      show_source: false

### Model Context Protocol

#### create_mcp_app

::: cognite_function_apps.mcp.create_mcp_app
    options:
      show_root_heading: true
      show_source: false

#### MCPApp

::: cognite_function_apps.mcp.MCPApp
    options:
      show_root_heading: true
      show_source: false
      members:
        - tool

### Distributed Tracing

#### create_tracing_app

::: cognite_function_apps.tracer.create_tracing_app
    options:
      show_root_heading: true
      show_source: false

#### FunctionTracer

::: cognite_function_apps.tracer.FunctionTracer
    options:
      show_root_heading: true
      show_source: false
      members:
        - span

### Function Client

#### FunctionClient

::: cognite_function_apps.FunctionClient
    options:
      show_root_heading: true
      show_source: false
      members_order: source
      members:
        - discover
        - describe
        - materialize

### Development Server

#### create_asgi_app

::: cognite_function_apps.devserver.create_asgi_app
    options:
      show_root_heading: true
      show_source: false

### Models and Types

#### FunctionCallInfo

Type alias for function execution metadata:

```python
from cognite_function_apps.models import FunctionCallInfo

# FunctionCallInfo is dict[str, Any] with these keys:
{
    "function_id": int,           # Function ID in CDF
    "call_id": int,               # Unique call identifier
    "schedule_id": int | None,    # Schedule ID if scheduled execution
    "scheduled_time": str | None  # Scheduled execution time
}
```

#### RequestHeaders

Type alias for accessing incoming HTTP headers:

```python
from cognite_function_apps.models import RequestHeaders

# RequestHeaders is Mapping[str, str] with header names in lowercase
@app.get("/items/{item_id}")
def get_item(client: CogniteClient, headers: RequestHeaders, item_id: int) -> dict[str, Any]:
    auth = headers.get("authorization")
    accept = headers.get("accept")
    return {"id": item_id}
```

See [Dependency Injection](dependency-injection.md) for usage details.

#### Handler

Type alias for the service handler function:

```python
from cognite_function_apps.models import Handler

# Handler signature:
def handle(
    client: CogniteClient,
    data: dict,
    secrets: dict[str, str] | None = None,
    function_call_info: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Compatible with Cognite Functions platform.

    Args:
        client: Authenticated CogniteClient
        data: Request data (path, method, body, headers)
        secrets: Function secrets
        function_call_info: Execution metadata

    Returns:
        Structured response dict with status_code, data/error, and headers
    """
```

## See Also

- [Response Customization](response-customization.md) - Status codes, headers, and content types
- [Type Safety](type-safety.md) - Type validation and conversion
- [Error Handling](error-handling.md) - Structured error responses
- [Dependency Injection](dependency-injection.md) - Custom dependencies
- [App Composition](app-composition.md) - Composing multiple apps
- [Introspection](introspection.md) - Built-in introspection endpoints
- [Model Context Protocol](mcp.md) - MCP integration
