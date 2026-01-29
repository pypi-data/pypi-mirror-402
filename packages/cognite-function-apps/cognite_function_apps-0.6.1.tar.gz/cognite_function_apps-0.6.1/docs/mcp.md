# Model Context Protocol (MCP)

The framework includes built-in Model Context Protocol support, enabling AI assistants to discover and use your Cognite Functions as tools.

## What is MCP?

The Model Context Protocol (MCP) is a standard for exposing tools to AI assistants. By adding MCP support to your Cognite Functions, you enable:

- **AI discovery** - AI assistants can find and understand your tools
- **Automatic schema generation** - AI gets JSON schemas for all parameters
- **Built-in validation** - Input validation happens automatically
- **Selective exposure** - Choose which endpoints AI can access

## MCP Endpoints

The framework provides two MCP endpoints:

### `/__mcp_tools__`

List all available MCP tools with their schemas.

**Usage:**

```bash
curl "https://your-function-url" -d '{"path": "/__mcp_tools__", "method": "GET"}'
```

**Response:**

```json
{
  "success": true,
  "data": {
    "tools": [
      {
        "name": "get_item",
        "description": "Retrieve an item by ID",
        "inputSchema": {
          "type": "object",
          "properties": {
            "item_id": {"type": "integer"},
            "include_tax": {"type": "boolean"}
          },
          "required": ["item_id"]
        }
      }
    ]
  }
}
```

### `/__mcp_call__/{tool_name}`

Execute a specific MCP tool by name.

**Usage:**

```bash
curl "https://your-function-url" -d '{
  "path": "/__mcp_call__/get_item",
  "method": "POST",
  "body": {"item_id": 42, "include_tax": true}
}'
```

**Response:**

```json
{
  "success": true,
  "data": {
    "id": 42,
    "name": "Widget",
    "total_price": 110.0
  }
}
```

## Basic Usage

Create an MCP app and use the `@mcp.tool()` decorator to expose functions as AI tools:

```python
from cognite_function_apps import FunctionApp, create_function_service
from cognite_function_apps.mcp import create_mcp_app
from cognite_function_apps.introspection import create_introspection_app

# Create your main business app
app = FunctionApp(title="Asset Management API", version="1.0.0")

@app.get("/items/{item_id}")
def get_item(client: CogniteClient, item_id: int) -> dict[str, Any]:
    """Retrieve an item by ID"""
    return {"id": item_id, "name": f"Item {item_id}"}

# Create MCP app for AI tool exposure
mcp = create_mcp_app()

# Use @mcp.tool() decorator to expose specific functions to AI
@mcp.tool(description="Retrieve an item by ID for AI assistants")
def get_item_for_ai(client: CogniteClient, item_id: int) -> dict[str, Any]:
    """AI-accessible version of get_item"""
    return get_item(client, item_id)

# Create introspection app
introspection = create_introspection_app()

# Compose all apps
handle = create_function_service(mcp, introspection, app)
```

## Exposing Existing Endpoints

You can expose existing app endpoints as MCP tools by combining decorators:

```python
from cognite_function_apps import FunctionApp
from cognite_function_apps.mcp import create_mcp_app

app = FunctionApp(title="My API", version="1.0.0")
mcp = create_mcp_app()

# Define function once, expose both as HTTP endpoint and MCP tool
@mcp.tool(description="Get asset information")
@app.get("/assets/{asset_id}")
def get_asset(client: CogniteClient, asset_id: int, include_metadata: bool = False) -> dict[str, Any]:
    """
    Retrieve asset information from CDF.

    Available both as HTTP endpoint and as AI tool.
    """
    asset = client.assets.retrieve(id=asset_id)
    result = {"id": asset.id, "name": asset.name}

    if include_metadata and asset.metadata:
        result["metadata"] = asset.metadata

    return result

handle = create_function_service(mcp, app)
```

## Tool-Only Functions

You can also create functions that are only accessible as MCP tools (not HTTP endpoints):

```python
from cognite_function_apps.mcp import create_mcp_app

mcp = create_mcp_app()

@mcp.tool(description="Search assets by name (AI tool only)")
def search_assets(client: CogniteClient, query: str, limit: int = 10) -> list[dict]:
    """
    Search for assets by name.

    This function is only accessible via MCP, not as an HTTP endpoint.
    """
    assets = client.assets.list(name=query, limit=limit)
    return [{"id": a.id, "name": a.name} for a in assets]

handle = create_function_service(mcp)
```

## Custom Tool Names

By default, the tool name is the function name. You can customize it:

```python
@mcp.tool(
    name="asset_retrieval",  # Custom tool name for AI
    description="Retrieve detailed asset information"
)
def get_asset_details(client: CogniteClient, asset_id: int) -> dict[str, Any]:
    """Get asset with full details"""
    return client.assets.retrieve(id=asset_id).dump()
```

## MCP with Pydantic Models

MCP tools support complex Pydantic models:

```python
from pydantic import BaseModel

class AssetQuery(BaseModel):
    name_filter: str
    limit: int = 10
    include_metadata: bool = False

class AssetResult(BaseModel):
    id: int
    name: str
    metadata: dict | None = None

@mcp.tool(description="Search assets with filters")
def search_assets(client: CogniteClient, query: AssetQuery) -> list[AssetResult]:
    """
    MCP tool accepts complex Pydantic models.

    AI provides:
    {
      "query": {
        "name_filter": "pump",
        "limit": 5,
        "include_metadata": true
      }
    }
    """
    assets = client.assets.list(name=query.name_filter, limit=query.limit)

    results = []
    for asset in assets:
        result = AssetResult(id=asset.id, name=asset.name)
        if query.include_metadata and asset.metadata:
            result.metadata = asset.metadata
        results.append(result)

    return results
```

## MCP Capabilities

### Automatic Schema Generation

AI assistants get complete JSON schemas for your tools:

```json
{
  "name": "search_assets",
  "description": "Search assets with filters",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "object",
        "properties": {
          "name_filter": {"type": "string"},
          "limit": {"type": "integer", "default": 10},
          "include_metadata": {"type": "boolean", "default": false}
        },
        "required": ["name_filter"]
      }
    },
    "required": ["query"]
  }
}
```

### Built-in Validation

Input validation happens automatically using Pydantic:

```python
# AI provides invalid input
{
  "item_id": "not-a-number"  # Should be int
}

# Framework returns validation error
{
  "success": false,
  "error_type": "ValidationError",
  "message": "Input validation failed: 1 error(s)",
  "details": {...}
}
```

### Tool Discovery

AI can discover all available tools:

```python
# AI queries available tools
GET /__mcp_tools__

# AI receives list of all MCP-enabled tools with schemas
{
  "tools": [
    {"name": "get_item", "description": "...", "inputSchema": {...}},
    {"name": "search_assets", "description": "...", "inputSchema": {...}}
  ]
}
```

## MCP with Async Handlers

MCP tools work seamlessly with async functions:

```python
import asyncio

@mcp.tool(description="Fetch data from multiple sources concurrently")
async def get_comprehensive_data(
    client: CogniteClient,
    asset_id: int
) -> dict[str, Any]:
    """
    Async MCP tool that fetches data concurrently.
    """
    async def fetch_asset():
        return client.assets.retrieve(id=asset_id).dump()

    async def fetch_timeseries():
        # Simulate async operation
        await asyncio.sleep(0.1)
        return {"timeseries": []}

    async def fetch_events():
        # Simulate async operation
        await asyncio.sleep(0.1)
        return {"events": []}

    # Fetch all data concurrently
    asset, timeseries, events = await asyncio.gather(
        fetch_asset(),
        fetch_timeseries(),
        fetch_events()
    )

    return {
        "asset": asset,
        "timeseries": timeseries,
        "events": events
    }
```

See [Async Support](async-support.md) for more information on async handlers.

## MCP with Dependency Injection

MCP tools support all framework dependencies:

```python
import logging
from cognite_function_apps import FunctionTracer

@mcp.tool(description="Get asset with logging and tracing")
def get_asset_instrumented(
    client: CogniteClient,
    logger: logging.Logger,
    tracer: FunctionTracer,
    asset_id: int
) -> dict[str, Any]:
    """
    MCP tool with dependency injection.
    """
    logger.info(f"AI requested asset {asset_id}")

    with tracer.span("fetch_asset"):
        asset = client.assets.retrieve(id=asset_id)

    logger.info(f"Successfully retrieved asset {asset_id}")
    return asset.dump()
```

See [Dependency Injection](dependency-injection.md) for more information.

## Selective Exposure

Use the `@mcp.tool()` decorator to control which functions are accessible to AI:

```python
# **Yes** Exposed to AI - has @mcp.tool() decorator
@mcp.tool(description="Safe operation for AI")
def safe_operation(client: CogniteClient, asset_id: int) -> dict[str, Any]:
    return client.assets.retrieve(id=asset_id).dump()

# BAD: NOT exposed to AI - no @mcp.tool() decorator
@app.delete("/assets/{asset_id}")
def dangerous_operation(client: CogniteClient, asset_id: int) -> dict[str, Any]:
    """This is NOT accessible via MCP - too dangerous for AI"""
    client.assets.delete(id=asset_id)
    return {"deleted": asset_id}
```

This gives you fine-grained control over what AI assistants can do with your function.

## Real-World Example

Complete example with multiple MCP tools:

```python
from cognite_function_apps import FunctionApp, create_function_service
from cognite_function_apps.mcp import create_mcp_app
from cognite_function_apps.introspection import create_introspection_app
from pydantic import BaseModel

# Models
class AssetSearchRequest(BaseModel):
    query: str
    limit: int = 10

class AssetInfo(BaseModel):
    id: int
    name: str
    description: str | None = None

# Create apps
app = FunctionApp(title="Asset Management", version="1.0.0")
mcp = create_mcp_app()
introspection = create_introspection_app()

# MCP Tools
@mcp.tool(description="Search for assets by name")
def search_assets(client: CogniteClient, request: AssetSearchRequest) -> list[AssetInfo]:
    """Find assets matching the search query"""
    assets = client.assets.list(name=request.query, limit=request.limit)
    return [
        AssetInfo(id=a.id, name=a.name, description=a.description)
        for a in assets
    ]

@mcp.tool(description="Get detailed asset information")
def get_asset_details(client: CogniteClient, asset_id: int) -> AssetInfo:
    """Retrieve detailed information about a specific asset"""
    asset = client.assets.retrieve(id=asset_id)
    return AssetInfo(
        id=asset.id,
        name=asset.name,
        description=asset.description
    )

@mcp.tool(description="Get asset hierarchy")
def get_asset_hierarchy(client: CogniteClient, asset_id: int, depth: int = 2) -> dict[str, Any]:
    """Get asset with children up to specified depth"""
    asset = client.assets.retrieve(id=asset_id)
    # Build hierarchy
    return {
        "id": asset.id,
        "name": asset.name,
        "children": []  # Implement hierarchy logic
    }

# Compose
handle = create_function_service(mcp, introspection, app)
```

## Best Practices

### Write Clear Descriptions

Descriptions help AI understand when to use your tools:

```python
# **Good** - clear, actionable description
@mcp.tool(description="Retrieve asset information by ID from Cognite Data Fusion")
def get_asset(client: CogniteClient, asset_id: int) -> dict[str, Any]:
    pass

# **Bad** - vague description
@mcp.tool(description="Get stuff")
def get_asset(client: CogniteClient, asset_id: int) -> dict[str, Any]:
    pass
```

### Use Meaningful Tool Names

Tool names should be clear and descriptive:

```python
# **Good** - descriptive name
@mcp.tool(name="search_assets_by_name", description="...")
def search_assets(client: CogniteClient, query: str) -> list[dict[str, Any]]:
    pass

# **Bad** - generic name
@mcp.tool(name="search", description="...")
def search_assets(client: CogniteClient, query: str) -> list[dict[str, Any]]:
    pass
```

### Don't Expose Dangerous Operations

Be careful about what you expose to AI:

```python
# **Good** - read-only operation
@mcp.tool(description="Retrieve asset data")
def get_asset(client: CogniteClient, asset_id: int) -> dict[str, Any]:
    return client.assets.retrieve(id=asset_id).dump()

# BAD: Dangerous - write operation accessible to AI
@mcp.tool(description="Delete asset")  # Don't do this!
def delete_asset(client: CogniteClient, asset_id: int) -> dict[str, Any]:
    client.assets.delete(id=asset_id)
    return {"deleted": asset_id}
```

## See Also

- [Introspection](introspection.md) - Built-in introspection endpoints
- [Dependency Injection](dependency-injection.md) - Using dependencies in MCP tools
- [Async Support](async-support.md) - Creating async MCP tools
- [App Composition](app-composition.md) - Composing MCP with other apps
