# App Composition

> **Note:** This is an advanced feature for framework extensibility. Most developers won't need to use app composition directly - it's primarily used internally for features like MCP integration and introspection endpoints. For typical use cases, simply create one `FunctionApp` and add your routes.

The framework supports composing multiple apps together to create modular services.

## What is App Composition?

App composition allows you to combine multiple `FunctionApp` instances into a single service. This enables:

- **Modular architecture** - Separate system utilities from business logic
- **Reusable components** - Share common functionality across services
- **Extension pattern** - Add framework features without modifying core apps
- **Clean separation** - Keep concerns isolated and maintainable

## Basic Composition

Compose multiple apps using `create_function_service()`:

```python
from cognite_function_apps import FunctionApp, create_function_service
from cognite_function_apps.introspection import create_introspection_app

# Create individual apps
introspection_app = create_introspection_app()
main_app = FunctionApp("Asset Management API", "2.1.0")

@main_app.get("/assets/{asset_id}")
def get_asset(client: CogniteClient, asset_id: int) -> dict[str, Any]:
    return {"id": asset_id, "name": f"Asset {asset_id}"}

# Compose apps
handle = create_function_service(introspection_app, main_app)
```

## Composition Rules

The framework uses specific rules for composing apps:

### 1. Routing Order (Left-to-Right)

Apps are tried **left-to-right** for route matching:

```python
# Routing order: app1 → app2 → app3
handle = create_function_service(app1, app2, app3)
```

When a request arrives:

1. Try app1's routes first
2. If no match, try app2's routes
3. If no match, try app3's routes
4. If no match, return RouteNotFound error

### 2. Metadata Source (Last App)

The **last app** provides title and version for the service:

```python
app1 = FunctionApp("App 1", "1.0.0")
app2 = FunctionApp("App 2", "2.0.0")
app3 = FunctionApp("Main API", "3.0.0")  # This title/version is used

handle = create_function_service(app1, app2, app3)
# Service title: "Main API"
# Service version: "3.0.0"
```

### 3. Registry Sharing

All composed apps share a single dependency registry:

```python
from cognite_function_apps import create_tracing_app

# TracingApp registers FunctionTracer in the shared registry
tracing_app = create_tracing_app()
main_app = FunctionApp("My API", "1.0.0")

# Both apps can use FunctionTracer
@main_app.get("/items/{item_id}")
def get_item(client: CogniteClient, tracer: FunctionTracer, item_id: int) -> dict[str, Any]:
    # FunctionTracer is available from tracing_app's registry!
    with tracer.span("fetch_item"):
        return {"id": item_id}

handle = create_function_service(tracing_app, main_app)
```

See [Dependency Injection](dependency-injection.md) for more information.

## Composition Patterns

### System + Business Pattern

Separate system utilities from business logic:

```python
from cognite_function_apps import FunctionApp, create_function_service
from cognite_function_apps.introspection import create_introspection_app

# System app provides introspection endpoints
introspection = create_introspection_app()

# Business app provides domain logic
business_app = FunctionApp("Business API", "1.0.0")

@business_app.get("/orders/{order_id}")
def get_order(client: CogniteClient, order_id: int) -> dict[str, Any]:
    return {"order_id": order_id}

# System endpoints first, then business logic
handle = create_function_service(introspection, business_app)
```

### Full Stack Pattern

Complete composition with all framework features:

```python
from cognite_function_apps import (
    FunctionApp,
    create_function_service,
    create_tracing_app,
)
from cognite_function_apps.introspection import create_introspection_app
from cognite_function_apps.mcp import create_mcp_app

# Create all apps
tracing = create_tracing_app()
mcp = create_mcp_app()
introspection = create_introspection_app()
main_app = FunctionApp("My API", "1.0.0")

@main_app.get("/items/{item_id}")
def get_item(client: CogniteClient, item_id: int) -> dict[str, Any]:
    return {"id": item_id}

# Complete composition: tracing + AI tools + debugging + business logic
handle = create_function_service(tracing, mcp, introspection, main_app)
```

### Development Pattern

Add debugging capabilities to existing services:

```python
from cognite_function_apps.introspection import create_introspection_app

# Your existing service
existing_app = FunctionApp("Production API", "1.0.0")

# Add introspection for debugging
introspection = create_introspection_app()
debug_handle = create_function_service(introspection, existing_app)
```

## Cross-App Introspection

When apps are composed, introspection endpoints show routes from all apps:

```python
from cognite_function_apps import FunctionApp, create_function_service
from cognite_function_apps.introspection import create_introspection_app
from cognite_function_apps.mcp import create_mcp_app

mcp = create_mcp_app()
introspection = create_introspection_app()
main_app = FunctionApp("My API", "1.0.0")

@main_app.get("/items/{item_id}")
def get_item(client: CogniteClient, item_id: int) -> dict[str, Any]:
    return {"id": item_id}

handle = create_function_service(mcp, introspection, main_app)
```

The `/__schema__` endpoint returns a unified OpenAPI schema including:

```json
{
  "info": {
    "title": "My API",
    "version": "1.0.0"
  },
  "paths": {
    "/__mcp_tools__": {...},        // From MCP app
    "/__schema__": {...},            // From introspection app
    "/__routes__": {...},            // From introspection app
    "/__health__": {...},            // From introspection app
    "/items/{item_id}": {...}        // From main business app
  }
}
```

## Custom Registry

Pass a custom registry to share dependencies across composed apps:

```python
from cognite_function_apps import (
    FunctionApp,
    create_function_service,
    create_default_registry,
)
import redis

# Create custom registry
registry = create_default_registry()
registry.register(
    provider=lambda ctx: redis.Redis.from_url(ctx["secrets"]["REDIS_URL"]),
    target_type=redis.Redis,
    param_name="cache",
    description="Redis cache"
)

# Create apps
app1 = FunctionApp("App 1", "1.0.0")
app2 = FunctionApp("App 2", "1.0.0")

@app1.get("/endpoint1")
def endpoint1(client: CogniteClient, cache: redis.Redis) -> dict[str, Any]:
    # Uses shared cache dependency
    return {"cached": True}

@app2.get("/endpoint2")
def endpoint2(client: CogniteClient, cache: redis.Redis) -> dict[str, Any]:
    # Uses same shared cache dependency
    return {"cached": True}

# Pass registry to service
handle = create_function_service(app1, app2, registry=registry)
```

See [Dependency Injection](dependency-injection.md) for complete registry documentation.

## Creating Custom Apps

Advanced users can extend `FunctionApp` to create custom middleware:

```python
from cognite_function_apps import FunctionApp

class CustomMiddlewareApp(FunctionApp):
    """Custom app with specialized behavior"""

    def __init__(self, title: str, version: str):
        super().__init__(title, version)
        self.custom_state = {}

    def on_compose(
        self,
        next_app: FunctionApp | None,
        shared_registry: "DependencyRegistry",
    ) -> None:
        """Called when app is composed into a service"""
        # Call parent to set up next_app and registry
        super().on_compose(next_app, shared_registry)
        # Access other apps' routes
        all_routes = self.downstream_routes
        # Register custom dependencies
        shared_registry.register(
            provider=lambda ctx: self.create_custom_dependency(ctx),
            target_type=MyCustomType,
            param_name="custom_dep"
        )

    def create_custom_dependency(self, ctx: dict):
        """Create custom dependency from context"""
        return MyCustomType(
            client=ctx["client"],
            secrets=ctx["secrets"]
        )

# Use custom app
custom_app = CustomMiddlewareApp("Custom", "1.0.0")
main_app = FunctionApp("Main", "1.0.0")

handle = create_function_service(custom_app, main_app)
```

## Composition Benefits

### Clean Separation of Concerns

```python
# System concerns (tracing, introspection)
system_app = create_introspection_app()

# Business concerns (domain logic)
business_app = FunctionApp("Orders API", "1.0.0")

# Clear separation
handle = create_function_service(system_app, business_app)
```

### Reusable Components

```python
# Create reusable monitoring app
monitoring_app = create_monitoring_app()

# Use in multiple services
service1 = create_function_service(monitoring_app, app1)
service2 = create_function_service(monitoring_app, app2)
service3 = create_function_service(monitoring_app, app3)
```

### Progressive Enhancement

```python
# Start simple
handle = create_function_service(app)

# Add introspection
handle = create_function_service(introspection, app)

# Add tracing
handle = create_function_service(tracing, introspection, app)

# Add AI integration
handle = create_function_service(mcp, tracing, introspection, app)
```

## Best Practices

### Order Apps by Priority

Put system apps before business apps:

```python
# **Good** - system apps first
handle = create_function_service(
    tracing_app,         # System
    introspection_app,   # System
    mcp_app,             # System
    main_app             # Business (provides metadata)
)

# **Bad** - business app first
handle = create_function_service(
    main_app,            # Business
    introspection_app    # System (won't provide metadata)
)
```

### Use Main App Last

The last app should be your main business app:

```python
# **Good** - main business app provides metadata
handle = create_function_service(system_apps..., main_business_app)

# **Bad** - utility app provides metadata
handle = create_function_service(main_business_app, introspection_app)
```

### Keep Apps Focused

Each app should have a single responsibility:

```python
# **Good** - focused apps
monitoring_app = create_monitoring_app()
auth_app = create_auth_app()
business_app = create_business_app()

handle = create_function_service(monitoring_app, auth_app, business_app)

# **Bad** - one app doing everything
god_app = FunctionApp("Everything", "1.0.0")
# Don't put monitoring, auth, and business logic in one app
```

## When NOT to Use Composition

For most applications, you don't need composition:

```python
# **Good** - simple single app (most common case)
app = FunctionApp("My API", "1.0.0")

@app.get("/items/{item_id}")
def get_item(client: CogniteClient, item_id: int) -> dict[str, Any]:
    return {"id": item_id}

handle = create_function_service(app)
```

Only use composition when you need:

- Framework extensions (introspection, MCP, tracing)
- Reusable middleware components
- Clear separation between system and business concerns

## See Also

- [Dependency Injection](dependency-injection.md) - Sharing dependencies across apps
- [Introspection](introspection.md) - Cross-app introspection
- [Model Context Protocol](mcp.md) - MCP integration via composition
- [Distributed Tracing](tracing.md) - Tracing via composition
- [Architecture](architecture.md) - Framework architecture overview
