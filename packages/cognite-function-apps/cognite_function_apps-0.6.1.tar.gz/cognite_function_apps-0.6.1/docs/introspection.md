# Introspection

One of the key challenges with standard Cognite Functions is that they become "black boxes" after deployment. This framework solves that problem with built-in introspection endpoints.

## Why Introspection?

Introspection endpoints provide visibility into deployed functions:

- **No more redeployments** just to check function signatures
- **AI tools can discover** and generate code for your functions
- **Team members can easily** understand deployed functions
- **Documentation stays in sync** with implementation

## Available Endpoints

The framework provides five built-in introspection endpoints:

### `/__schema__`

Returns the complete OpenAPI 3.1 schema for all composed apps.

**Usage:**

```bash
curl "https://your-function-url" -d '{"path": "/__schema__", "method": "GET"}'
```

**Response:**

```json
{
  "status_code": 200,
  "data": {
    "openapi": "3.1.0",
    "info": {
      "title": "My API",
      "version": "1.0.0"
    },
    "paths": {
      "/items/{item_id}": {
        "get": {
          "summary": "Retrieve an item by ID",
          "parameters": [...],
          "responses": {...}
        }
      }
    }
  },
  "headers": {
    "content-type": "application/json"
  }
}
```

### `/__routes__`

Returns a summary of all available routes with descriptions.

**Usage:**

```bash
curl "https://your-function-url" -d '{"path": "/__routes__", "method": "GET"}'
```

**Response:**

```json
{
  "status_code": 200,
  "data": {
    "app_info": {
      "title": "My API",
      "version": "1.0.0",
      "total_apps": 2,
      "app_names": ["Introspection", "My API"]
    },
    "routes": {
      "/items/{item_id}": {
        "methods": ["GET"],
        "descriptions": {
          "GET": "Retrieve an item by ID"
        }
      },
      "/items/": {
        "methods": ["POST"],
        "descriptions": {
          "POST": "Create a new item"
        }
      }
    }
  },
  "headers": {
    "content-type": "application/json"
  }
}
```

### `/__health__`

Returns health status and comprehensive app information.

**Usage:**

```bash
curl "https://your-function-url" -d '{"path": "/__health__", "method": "GET"}'
```

**Response:**

```json
{
  "status_code": 200,
  "data": {
    "status": "healthy",
    "app": "My API",
    "version": "1.0.0",
    "composed_apps": [
      {"name": "Introspection", "routes": 5},
      {"name": "My API", "routes": 2}
    ],
    "statistics": {
      "total_routes": 7,
      "total_apps": 2,
      "routes_by_method": {
        "GET": 6,
        "POST": 1
      }
    }
  },
  "headers": {
    "content-type": "application/json"
  }
}
```

### `/__ping__`

Simple connectivity check for monitoring and pre-warming.

**Usage:**

```bash
curl "https://your-function-url" -d '{"path": "/__ping__", "method": "GET"}'
```

**Response:**

```json
{
  "status_code": 200,
  "data": {
    "status": "pong"
  },
  "headers": {
    "content-type": "application/json"
  }
}
```

### `/__client_methods__`

Returns complete metadata for client generation and dynamic calling.

**Usage:**

```bash
curl "https://your-function-url" -d '{"path": "/__client_methods__", "method": "GET"}'
```

**Response:**

```json
{
  "status_code": 200,
  "data": {
    "methods": [
      {
        "name": "get_items_by_item_id",
        "path": "/items/{item_id}",
        "http_method": "GET",
        "parameters": [
          {
            "name": "item_id",
            "type": "int",
            "required": true,
            "in": "path"
          },
          {
            "name": "include_tax",
            "type": "bool",
            "required": false,
            "default": "False",
            "in": "query"
          }
        ],
        "description": "Retrieve an item by ID",
        "return_type": "Item",
        "path_params": ["item_id"]
      }
    ],
    "models": [
      {
        "name": "Item",
        "source": "class Item(BaseModel):\n    name: str\n    price: float\n    ..."
      }
    ],
    "imports": [
      "from pydantic import BaseModel",
      "from typing import Any"
    ]
  },
  "headers": {
    "content-type": "application/json"
  }
}
```

This endpoint is used by [FunctionClient](function-client.md) to enable dynamic API discovery and client generation.

## Enabling Introspection

Introspection endpoints are provided by the `IntrospectionApp`. Include it in your app composition:

```python
from cognite_function_apps import (
    FunctionApp,
    create_function_service,
)
from cognite_function_apps.introspection import create_introspection_app

# Create your main app
app = FunctionApp(title="My API", version="1.0.0")

@app.get("/items/{item_id}")
def get_item(client: CogniteClient, item_id: int) -> dict[str, Any]:
    return {"id": item_id}

# Create introspection app
introspection = create_introspection_app()

# Compose apps - introspection endpoints are now available
handle = create_function_service(introspection, app)
```

## Cross-App Introspection

When composing multiple apps, introspection endpoints show routes from all apps:

```python
from cognite_function_apps import (
    FunctionApp,
    create_function_service,
)
from cognite_function_apps.introspection import create_introspection_app
from cognite_function_apps.mcp import create_mcp_app

# Create apps
mcp = create_mcp_app()
introspection = create_introspection_app()
main_app = FunctionApp(title="My API", version="1.0.0")

@main_app.get("/items/{item_id}")
def get_item(client: CogniteClient, item_id: int) -> dict[str, Any]:
    return {"id": item_id}

# Compose all apps
handle = create_function_service(mcp, introspection, main_app)
```

The `/__schema__` response will include:

- Routes from MCP app (`/__mcp_tools__`, `/__mcp_call__/...`)
- Routes from introspection app (`/__schema__`, `/__routes__`, etc.)
- Routes from your main business app (`/items/{item_id}`)

All routes are documented in a single unified OpenAPI schema.

## Using Introspection with FunctionClient

The [FunctionClient](function-client.md) uses introspection endpoints to discover your API:

```python
from cognite_function_apps import FunctionClient

# Connect to your function
client = FunctionClient(base_url="http://localhost:8000")

# Discover uses /__schema__ and /__client_methods__ internally
models = client.discover()
# ✓ Connected to My API v1.0.0
# Available methods: get_item, create_item, ...

# Call discovered methods
result = client.get_item(item_id=42)
```

See [Function Client](function-client.md) for complete documentation.

## Schema Structure

The OpenAPI schema includes complete information about your API:

```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "My API",
    "version": "1.0.0"
  },
  "paths": {
    "/items/{item_id}": {
      "get": {
        "summary": "Retrieve an item by ID",
        "parameters": [
          {
            "name": "item_id",
            "in": "path",
            "required": true,
            "schema": {"type": "integer"}
          },
          {
            "name": "include_tax",
            "in": "query",
            "required": false,
            "schema": {"type": "boolean", "default": false}
          }
        ],
        "responses": {
          "200": {
            "description": "Successful response",
            "content": {
              "application/json": {
                "schema": {"$ref": "#/components/schemas/ItemResponse"}
              }
            }
          }
        }
      }
    }
  },
  "components": {
    "schemas": {
      "Item": {
        "type": "object",
        "properties": {
          "name": {"type": "string"},
          "price": {"type": "number"}
        },
        "required": ["name", "price"]
      },
      "ItemResponse": {
        "type": "object",
        "properties": {
          "id": {"type": "integer"},
          "item": {"$ref": "#/components/schemas/Item"}
        }
      }
    }
  }
}
```

## Use Cases

### API Discovery

Teams can explore deployed functions without reading source code:

```bash
# What endpoints are available?
curl "https://function-url" -d '{"path": "/__routes__", "method": "GET"}'

# What's the complete API specification?
curl "https://function-url" -d '{"path": "/__schema__", "method": "GET"}'
```

### AI Tool Integration

AI assistants can use introspection to understand and call your functions:

```python
# AI discovers available endpoints
schema = get_schema_from_function()

# AI generates code to call the function
code = generate_code_from_schema(schema)
```

See [Model Context Protocol](mcp.md) for AI integration.

### Monitoring and Health Checks

Use `/__health__` and `/__ping__` for monitoring:

```bash
# Check if function is responding
curl "https://function-url" -d '{"path": "/__ping__", "method": "GET"}'

# Get detailed health information
curl "https://function-url" -d '{"path": "/__health__", "method": "GET"}'
```

### Documentation Generation

Generate documentation from the OpenAPI schema:

```bash
# Download schema
curl "https://function-url" -d '{"path": "/__schema__", "method": "GET"}' > schema.json

# Generate docs with tools like Redoc or Swagger UI
redoc-cli bundle schema.json -o docs.html
```

## Benefits

### No Documentation Drift

The schema is generated from your code, so it's always accurate:

- Routes match your decorators (`@app.get()`, etc.)
- Parameters match your function signatures
- Models match your Pydantic definitions
- Descriptions come from your docstrings

### Single Source of Truth

Instead of maintaining separate documentation files that can get out of sync, your code IS the documentation:

```python
@app.get("/items/{item_id}")
def get_item(client: CogniteClient, item_id: int, include_tax: bool = False) -> ItemResponse:
    """
    Retrieve an item by ID.

    This description appears in the OpenAPI schema automatically.
    """
    return ItemResponse(...)
```

### Team Collaboration

New team members can explore deployed functions without needing source code access or redeployment.

## Best Practices

### Write Good Docstrings

Docstrings appear in the generated schema:

```python
# **Good** - descriptive docstring
@app.get("/items/{item_id}")
def get_item(client: CogniteClient, item_id: int) -> ItemResponse:
    """
    Retrieve an item by ID.

    Returns complete item information including pricing and availability.
    """
    return ItemResponse(...)

# **Bad** - no docstring
@app.get("/items/{item_id}")
def get_item(client: CogniteClient, item_id: int) -> ItemResponse:
    return ItemResponse(...)
```

### Use Descriptive Parameter Names

Parameter names appear in the schema, so make them clear:

```python
# **Good** - clear parameter names
def search_items(
    client: CogniteClient,
    search_query: str,
    max_results: int = 10,
    include_archived: bool = False
) -> dict[str, Any]:
    pass

# **Bad** - ambiguous names
def search_items(client: CogniteClient, q: str, n: int = 10, a: bool = False) -> dict[str, Any]:
    pass
```

### Include Introspection in All Deployments

Always include the introspection app in production deployments:

```python
# **Good** - introspection in production
handle = create_function_service(introspection, main_app)

# **Bad** - no visibility into deployed function
handle = create_function_service(main_app)
```

## See Also

- [Function Client](function-client.md) - Using introspection for API discovery
- [Model Context Protocol](mcp.md) - AI tool integration using introspection
- [App Composition](app-composition.md) - How apps are composed together
- [API Reference](api-reference.md) - Complete API documentation
