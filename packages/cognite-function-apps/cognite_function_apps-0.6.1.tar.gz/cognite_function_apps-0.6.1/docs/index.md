# Function Apps

Enterprise-grade framework for building type-safe, composable Cognite Functions with automatic validation, built-in introspection, and AI integration.

## Why Function Apps?

Standard [Cognite Functions](https://docs.cognite.com/cdf/functions/) require a simple `handle(client, data)` function, which becomes unwieldy for complex APIs. This framework provides composable architecture, automatic validation, and built-in introspection.

**Standard Cognite Function:**

```python
def handle(client, data):
    try:
        asset_no = int(data["assetNo"])  # Manual validation
        include_tax = data.get("includeTax", "false").lower() == "true"  # Manual parsing
        # Handle routing manually based on data
        if data.get("action") == "get_item":
            # Implementation here
        elif data.get("action") == "create_item":
            # Different implementation
    except Exception as e:
        return {"error": str(e)}  # Basic error handling
```

**With Function Apps:**

```python
@app.get("/items/{item_id}")
def get_item(client: CogniteClient, item_id: int, include_tax: bool = False) -> ItemResponse:
    """Retrieve an item by ID"""
    # Type validation and coercion handled automatically
    # Clear function signature with proper types
    # Automatic error handling and response formatting
```

## Key Features

- **[Type-safe routing](type-safety.md)** - Decorator-based syntax with automatic validation
- **[Response customization](response-customization.md)** - Control status codes, headers, and content types
- **[Async/await support](async-support.md)** - Write both sync and async handlers for concurrent operations
- **[Error handling](error-handling.md)** - Comprehensive error handling with structured responses
- **[Logging](logging.md)** - Enterprise logging with dependency injection across all cloud providers
- **[Distributed tracing](tracing.md)** - OpenTelemetry-based tracing with automatic span creation
- **[Dependency injection](dependency-injection.md)** - Inject custom dependencies into your handlers
- **[Introspection](introspection.md)** - Built-in endpoints for schema, routes, health checks
- **[Model Context Protocol (MCP)](mcp.md)** - Native AI tool exposure for LLM integration
- **[Local development server](dev-server.md)** - Test your functions locally with interactive API docs
- **[Function client](function-client.md)** - Notebook-first client for exploring and consuming functions

## Installation

**Requirements:**

- Python 3.10 or higher
- uv (recommended) or pip

```bash
# Install the package (when published)
pip install cognite-function-apps

# Optional: Install with CLI support for dev server
pip install cognite-function-apps[cli]

# Optional: Install with tracing support
pip install cognite-function-apps[tracing]
```

## Quick Start

### Basic Example

```python
from cognite.client import CogniteClient
from pydantic import BaseModel

from cognite_function_apps import FunctionApp, create_function_service

# Create your app
app = FunctionApp(title="My API", version="1.0.0")

# Define your models
class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

class ItemResponse(BaseModel):
    id: int
    item: Item
    total_price: float

# Define your endpoints
@app.get("/items/{item_id}")
def get_item(
    client: CogniteClient,
    item_id: int,
    include_tax: bool = False
) -> ItemResponse:
    """Retrieve an item by ID"""
    item = Item(
        name=f"Item {item_id}",
        price=100.0,
        tax=10.0 if include_tax else None
    )
    total = item.price + (item.tax or 0)
    return ItemResponse(id=item_id, item=item, total_price=total)

@app.post("/items/")
def create_item(client: CogniteClient, item: Item) -> ItemResponse:
    """Create a new item"""
    new_id = 12345  # Your creation logic here
    total = item.price + (item.tax or 0)
    return ItemResponse(id=new_id, item=item, total_price=total)

# Export the handler for Cognite Functions
handle = create_function_service(app)
```

### Test Locally

Install with CLI support and run the development server:

```bash
pip install cognite-function-apps[cli]
fun serve examples/
```

Visit `http://localhost:8000/docs` for interactive API documentation.

See the [Local Development Server](dev-server.md) guide for detailed setup instructions.

## Documentation Structure

### Getting Started

- **[Quick Start](#quick-start)** - Get up and running in minutes
- **[Installation](#installation)** - Install the framework and optional dependencies

### Core Features

- **[Error Handling](error-handling.md)** - Structured error responses with detailed information
- **[Response Customization](response-customization.md)** - Control status codes, headers, and content types
- **[Logging](logging.md)** - Enterprise-grade logging for all cloud providers
- **[Type Safety](type-safety.md)** - Automatic type validation and conversion
- **[Dependency Injection](dependency-injection.md)** - Inject custom dependencies into handlers
- **[Async Support](async-support.md)** - Build concurrent handlers with async/await
- **[Introspection](introspection.md)** - Built-in endpoints for schema, routes, and health
- **[Model Context Protocol](mcp.md)** - Expose your functions as AI tools
- **[Distributed Tracing](tracing.md)** - OpenTelemetry integration for observability

### Development Tools

- **[Local Dev Server](dev-server.md)** - Test functions locally with auto-reload
- **[Function Client](function-client.md)** - Notebook-first client for exploring functions

### Advanced Topics

- **[App Composition](app-composition.md)** - Build modular services from reusable apps
- **[Architecture](architecture.md)** - Understand the framework's design

### Reference

- **[API Reference](api-reference.md)** - Complete API documentation
- **[Changelog](changelog.md)** - Release notes and version history
- **[Release Process](release-process.md)** - How we release new versions
- **[Contributing](contributing.md)** - Development setup and contribution guide

## Examples

The framework includes a complete example in `examples/handler.py` demonstrating:

- Type-safe routing with decorator syntax
- MCP integration for AI tool exposure
- Built-in introspection endpoints
- Async handler support
- Composable app architecture

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## Acknowledgments

- Built specifically for [Cognite Data Fusion](https://www.cognite.com/) [Functions](https://docs.cognite.com/cdf/functions/) platform
- Decorator routing syntax inspired by [FastAPI](https://fastapi.tiangolo.com/)
- Data validation powered by [Pydantic](https://pydantic-docs.helpmanual.io/)
