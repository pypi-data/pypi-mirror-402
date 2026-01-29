# Architecture

Understanding the framework's design and internal structure.

## Overview

The framework is organized into several modules, each with a specific responsibility:

```text
cognite-function-apps/
├── src/cognite_function_apps/
│   ├── app.py                  # Core FunctionApp class and decorators
│   ├── service.py              # Function service layer and app composition
│   ├── routing.py              # Route matching and management
│   ├── models.py               # Pydantic models and type definitions
│   ├── convert.py              # Type conversion and argument processing
│   ├── schema.py               # OpenAPI schema generation
│   ├── formatting.py           # Formatting utilities
│   ├── introspection.py        # Built-in introspection endpoints
│   ├── logger.py               # Enterprise logging utilities
│   ├── tracer.py               # Distributed tracing support
│   ├── mcp.py                  # Model Context Protocol integration
│   ├── client.py               # FunctionClient for consuming functions
│   ├── dependency_registry.py  # Dependency injection system
│   └── devserver/              # Local development server
│       ├── asgi.py             # ASGI adapter for uvicorn
│       └── auth.py             # CogniteClient authentication
```

## Key Components

### 1. FunctionApp

Main application class with FastAPI-style decorators.

**Responsibilities:**

- Route registration via decorators (`@app.get()`, `@app.post()`, etc.)
- Route storage and management
- App metadata (title, version)
- Dependency registry management

**Example:**

```python
app = FunctionApp(title="My API", version="1.0.0")

@app.get("/items/{item_id}")
def get_item(client: CogniteClient, item_id: int) -> dict[str, Any]:
    return {"id": item_id}
```

### 2. create_function_service()

Creates composed handler from multiple apps with optional custom registry.

**Responsibilities:**

- App composition with left-to-right routing
- Metadata extraction from last app
- Registry sharing across apps
- Handler creation compatible with Cognite Functions

**Example:**

```python
handle = create_function_service(introspection, main_app, registry=custom_registry)
```

### 3. App Composition System

**Composition Hook:**

Apps can override `on_compose()` to access the next app in the chain and the shared registry.

```python
class CustomApp(FunctionApp):
    def on_compose(
        self,
        next_app: FunctionApp | None,
        shared_registry: DependencyRegistry,
    ) -> None:
        # Call parent to set up next_app and registry
        super().on_compose(next_app, shared_registry)

        # Access downstream apps and their routes
        downstream_routes = self.downstream_routes

        # Register custom dependencies
        shared_registry.register(...)
```

**Registry Sharing:**

All composed apps share a single dependency registry, enabling cross-app dependency injection.

**Left-to-Right Routing:**

Earlier apps in composition handle routes first.

**Last-App Metadata:**

The final app provides title/version for schemas.

### 4. SchemaGenerator

Generates unified OpenAPI documentation across all apps.

**Responsibilities:**

- Convert routes to OpenAPI paths
- Generate component schemas from Pydantic models
- Handle nested model references
- Produce OpenAPI 3.0 compliant schemas

### 5. Built-in Apps

**IntrospectionApp:**

Provides `/__schema__`, `/__routes__`, `/__health__`, `/__ping__` endpoints.

**MCPApp:**

Provides `/__mcp_tools__`, `/__mcp_call__/*` endpoints for AI integration.

**TracingApp:**

Provides distributed tracing support via OpenTelemetry.

### 6. Request Processing Pipeline

```text
1. Request arrives: {path, method, body, headers}
   ↓
2. Try each composed app in order (left-to-right)
   ↓
3. Find matching route in current app (with content negotiation)
   ↓
4. Extract path parameters from URL
   ↓
5. Parse query parameters from URL
   ↓
6. Create dependency context (client, secrets, function_call_info, headers)
   ↓
7. Resolve dependencies from registry
   ↓
8. Validate and coerce parameters (recursive type conversion)
   ↓
9. Execute handler function with resolved dependencies
   ↓
10. Detect Response[T] wrapper and extract data with custom status/headers
   ↓
11. Format response ({status_code, data, headers} or {status_code, error_type, ...})
   ↓
12. Return structured response
```

## Module Details

### app.py

**Core FunctionApp class:**

- Route decorators (`get`, `post`, `put`, `delete`)
- Route storage and retrieval
- App composition support via `on_compose()`
- Dependency registry management

### service.py

**Function service layer:**

- `create_function_service()` for app composition
- Handler creation from composed apps
- Request routing across multiple apps
- Response formatting

### routing.py

**Route matching:**

- Path pattern matching (e.g., `/items/{item_id}`)
- HTTP method matching
- Route parameter extraction
- Query string parsing
- Content negotiation via Accept header matching
- Route metadata: content_type, accept, status_code, cache_control, extra_headers

### models.py

**Pydantic models and types:**

- `Route` - Route definition with handler
- `CogniteFunctionError` - Structured error format with status_code and headers
- `CogniteFunctionResponse` - Structured success format with status_code and headers
- `Response[T]` - Generic wrapper for dynamic status codes and headers
- `FunctionCallInfo` - Execution metadata type
- `RequestHeaders` - Type alias for incoming HTTP headers

### convert.py

**Type conversion and validation:**

- Recursive type conversion for nested structures
- Pydantic model instantiation from dicts
- Parameter type coercion (str → int, float, bool)
- Detailed error messages for conversion failures

### schema.py

**OpenAPI schema generation:**

- Route to OpenAPI path conversion
- Pydantic model to JSON Schema conversion
- Reference resolution (`$ref` handling)
- Component schema generation

### dependency_registry.py

**Dependency injection:**

- Dependency registration
- Provider functions
- Type-based and name-based matching
- Context-aware dependency creation

### introspection.py

**Built-in introspection endpoints:**

- `/__schema__` - OpenAPI schema
- `/__routes__` - Route list
- `/__health__` - Health check
- `/__ping__` - Connectivity check

### logger.py

**Enterprise logging:**

- Isolated logger creation
- Stdout-only output
- Standard log levels
- Cloud provider compatibility

### tracer.py

**Distributed tracing:**

- OpenTelemetry integration
- Span creation and management
- OTLP export
- Trace context propagation

### mcp.py

**Model Context Protocol:**

- Tool registration
- Tool discovery endpoint
- Tool execution endpoint
- JSON schema generation for tools

### client.py

**FunctionClient for consuming functions:**

- Dynamic method discovery
- Runtime Pydantic model generation
- Type-safe method calls
- Client code generation

### devserver/

**Local development server:**

- ASGI adapter for uvicorn
- Request/response conversion
- CogniteClient authentication
- Interactive API documentation (Swagger UI)

## Design Principles

### 1. Composability

Apps are composable building blocks that can be combined:

```python
# Compose any combination of apps
handle = create_function_service(tracing, mcp, introspection, main_app)
```

### 2. Type Safety

Everything is type-safe with automatic validation:

- Input validation via Pydantic
- Output validation via return type hints
- Dependency injection with type annotations

### 3. Zero Configuration

Sensible defaults for common use cases:

- Automatic schema generation
- Built-in error handling
- Standard response format

### 4. Extensibility

Easy to extend with custom apps and dependencies:

- Subclass `FunctionApp` for custom middleware
- Register custom dependencies
- Override composition behavior

### 5. Developer Experience

Optimized for productivity:

- FastAPI-style decorators
- Local development server
- Interactive API documentation
- FunctionClient for exploration

## Request Flow Example

```python
# 1. Request arrives
{
    "path": "/items/123?include_tax=true",
    "method": "GET"
}

# 2. Router matches path pattern
route = Router.match("GET", "/items/123")
# Matched: GET /items/{item_id}
# Parameters: {"item_id": "123"}

# 3. Query string parsed
query_params = {"include_tax": "true"}

# 4. Parameters converted
converted_params = {
    "item_id": 123,           # str → int
    "include_tax": True       # str → bool
}

# 5. Dependencies resolved
dependencies = {
    "client": CogniteClient(...),
    "logger": Logger(...),
    "tracer": FunctionTracer(...)
}

# 6. Handler executed
result = get_item(
    client=dependencies["client"],
    logger=dependencies["logger"],
    tracer=dependencies["tracer"],
    item_id=123,
    include_tax=True
)

# 7. Response formatted
{
    "status_code": 200,
    "data": result,
    "headers": {"content-type": "application/json"}
}
```

## Performance Considerations

### Async Support

- Async handlers (`async def`) are awaited directly
- Sync handlers (`def`) run on thread pool
- No blocking in event loop

### Type Conversion

- Conversion is cached per request
- Recursive conversion handles nested structures
- Pydantic provides fast validation

### Dependency Injection

- Dependencies created once per request
- Provider functions are lightweight
- Context is shared across all handlers

### Schema Generation

- Schemas generated once at startup (introspection)
- Cached and reused for all introspection requests
- No runtime overhead for business logic

## See Also

- [Response Customization](response-customization.md) - Status codes, headers, and content types
- [App Composition](app-composition.md) - How apps are composed
- [Dependency Injection](dependency-injection.md) - Dependency system details
- [Type Safety](type-safety.md) - Type conversion and validation
- [Contributing](contributing.md) - Development and contribution guide
