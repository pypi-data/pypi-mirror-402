# Dependency Injection

The framework uses dependency injection to provide framework dependencies (`client`, `secrets`, `logger`, `function_call_info`, `headers`) to your handlers. You can also **register your own custom dependencies** for services like database connections, tracing, caching, or any other resources your application needs.

## Dependency Matching Semantics

The framework uses **AND semantics** for dependency matching, providing clear and predictable behavior:

**Framework Dependencies (Strict Matching):**

- `client` - Requires **both** `param_name="client"` AND `target_type=CogniteClient`
- `secrets` - Requires **both** `param_name="secrets"` AND `target_type=Mapping` (accepts `dict`, `Mapping`, `dict[str, str]`, `Mapping[str, str]`, etc.)
- `logger` - Requires **both** `param_name="logger"` AND `target_type=logging.Logger`
- `function_call_info` - Requires **both** `param_name="function_call_info"` AND `target_type=FunctionCallInfo`
- `headers` - Requires **both** `param_name="headers"` AND `target_type=RequestHeaders`

**Custom Dependencies (Flexible Matching):**

Note: `target_type` is **always required** - this is a type-safe framework.

- Register with `target_type` only for flexible parameter naming (works with any parameter name)
- Register with **both** `param_name` and `target_type` to require BOTH (strict matching with AND logic)

## Built-in Dependencies

The framework provides these dependencies by default:

### CogniteClient

The authenticated Cognite client for accessing CDF APIs:

```python
from cognite.client import CogniteClient

@app.get("/assets/{asset_id}")
def get_asset(client: CogniteClient, asset_id: int) -> dict[str, Any]:
    """Retrieve an asset from CDF"""
    asset = client.assets.retrieve(id=asset_id)
    return asset.dump()
```

**Important:** You **must** use the parameter name `client` with type annotation `CogniteClient`.

### Secrets

Access to function secrets (credentials, API keys, etc.):

```python
from collections.abc import Mapping

@app.post("/sync-data")
def sync_data(
    client: CogniteClient,
    secrets: Mapping[str, str],
    data: dict[str, Any]
) -> dict[str, Any]:
    """Sync data using external API credentials"""
    api_key = secrets.get("EXTERNAL_API_KEY")
    api_url = secrets.get("EXTERNAL_API_URL")

    # Use credentials
    external_client = create_external_client(api_key, api_url)
    result = external_client.sync(data)

    return {"synced": True, "records": result}
```

**Important:** You **must** use the parameter name `secrets` with a Mapping-compatible type annotation (`dict`, `Mapping`, `dict[str, str]`, `Mapping[str, str]`, etc.).

### Logger

Isolated logger for enterprise-grade logging:

```python
import logging

@app.get("/items/{item_id}")
def get_item(
    client: CogniteClient,
    logger: logging.Logger,
    item_id: int
) -> dict[str, Any]:
    """Retrieve item with logging"""
    logger.info(f"Fetching item {item_id}")
    item = fetch_item(item_id)
    logger.debug(f"Item details: {item}")
    return {"id": item_id, "data": item}
```

**Important:** You **must** use the parameter name `logger` with type annotation `logging.Logger`.

See [Logging](logging.md) for detailed usage information.

### FunctionCallInfo

Metadata about the current function execution:

```python
from cognite_function_apps.models import FunctionCallInfo

@app.get("/meta")
def get_execution_info(
    client: CogniteClient,
    function_call_info: FunctionCallInfo
) -> dict[str, Any]:
    """Get information about current execution"""
    return {
        "function_id": function_call_info.get("function_id"),
        "call_id": function_call_info.get("call_id"),
        "schedule_id": function_call_info.get("schedule_id"),
        "scheduled_time": function_call_info.get("scheduled_time")
    }
```

**Important:** You **must** use the parameter name `function_call_info` with type annotation `FunctionCallInfo`.

### RequestHeaders

Access to incoming HTTP request headers:

```python
from cognite_function_apps.models import RequestHeaders

@app.get("/items/{item_id}")
def get_item(
    client: CogniteClient,
    headers: RequestHeaders,
    item_id: int
) -> dict[str, Any]:
    """Access request headers for custom logic"""
    # Header names are lowercase (HTTP/2 convention)
    auth = headers.get("authorization")
    accept = headers.get("accept")
    user_agent = headers.get("user-agent")
    custom = headers.get("x-custom-header")

    return {
        "id": item_id,
        "has_auth": auth is not None
    }
```

`RequestHeaders` is a `Mapping[str, str]` with header names in lowercase.

**Important:** You **must** use the parameter name `headers` with type annotation `RequestHeaders`.

See [Response Customization](response-customization.md) for more examples of using request headers.

## Registering Custom Dependencies

To use custom dependencies, create a registry with your dependencies and pass it to `create_function_service()`:

```python
from cognite_function_apps import (
    FunctionApp,
    create_function_service,
    create_default_registry,
)
import redis
import httpx

# Create a custom registry with your dependencies
registry = create_default_registry()

# Register with name+type matching (both required for consistent naming)
registry.register(
    provider=lambda ctx: redis.Redis.from_url(ctx.get("secrets", {}).get("REDIS_URL")),
    target_type=redis.Redis,
    param_name="cache",
    description="Redis cache connection"
)

registry.register(
    provider=lambda ctx: httpx.Client(base_url="https://api.example.com"),
    target_type=httpx.Client,
    param_name="http",
    description="HTTP client for external API"
)

# Create your app
app = FunctionApp(title="My API", version="1.0.0")

# Now use them in your handlers with the registered parameter names
@app.get("/items/{item_id}")
def get_item(
    client: CogniteClient,        # Framework: requires name="client" + type
    cache: redis.Redis,            # Custom: requires name="cache" + type
    http: httpx.Client,            # Custom: requires name="http" + type
    item_id: int
) -> dict[str, Any]:
    # Try cache first
    cached = cache.get(f"item:{item_id}")
    if cached:
        return json.loads(cached)

    # Fetch from external API
    response = http.get(f"/items/{item_id}")
    item_data = response.json()

    # Cache and return
    cache.set(f"item:{item_id}", json.dumps(item_data), ex=3600)
    return item_data

# All endpoints must use the same parameter names consistently
@app.get("/users/{user_id}")
def get_user(
    client: CogniteClient,
    cache: redis.Redis,            # Must use "cache", not "redis_conn"
    http: httpx.Client,            # Must use "http", not "api_client"
    user_id: int
) -> dict[str, Any]:
    # Same dependencies with consistent parameter names across all endpoints
    return {"user_id": user_id}

# Pass the registry to create_function_service
handle = create_function_service(app, registry=registry)
```

## Context-Aware Dependencies

Provider functions receive a context dictionary with `client`, `secrets`, and `function_call_info`:

```python
from cognite_function_apps import (
    FunctionApp,
    create_function_service,
    create_default_registry,
)

class MyAPIClient:
    def __init__(self, api_key: str, environment: str):
        self.api_key = api_key
        self.environment = environment

    def fetch_data(self):
        # Implementation here
        pass

# Create registry and register with name+type matching (both required)
registry = create_default_registry()
registry.register(
    provider=lambda ctx: MyAPIClient(
        api_key=ctx.get("secrets", {}).get("API_KEY"),
        environment=ctx.get("secrets", {}).get("ENV", "production")
    ),
    target_type=MyAPIClient,
    param_name="api_client",
    description="External API client with credentials"
)

app = FunctionApp(title="My API", version="1.0.0")

@app.post("/sync-data")
def sync_data(
    client: CogniteClient,      # Framework dependency
    api_client: MyAPIClient,    # Custom dependency (must use param_name="api_client")
    data: dict[str, Any]
) -> dict[str, Any]:
    # api_client is initialized with secrets from context
    external_data = api_client.fetch_data()
    # Process and return
    return {"synced": True}

# Pass the registry to create_function_service
handle = create_function_service(app, registry=registry)
```

## Registry Sharing in Composed Apps

When composing multiple apps, **all apps share a single dependency registry**. Built-in framework apps like `TracingApp` automatically register their dependencies (like `FunctionTracer`) into the shared registry:

```python
from cognite_function_apps import (
    FunctionApp,
    create_function_service,
    create_tracing_app,
    FunctionTracer,
)
from cognite_function_apps.mcp import create_mcp_app
from cognite_function_apps.introspection import create_introspection_app

# Create your main app
app = FunctionApp(title="My API", version="1.0.0")

@app.get("/items/{item_id}")
def get_item(client: CogniteClient, tracer: FunctionTracer, item_id: int) -> dict[str, Any]:
    """Main business endpoint with tracer"""
    with tracer.span("fetch_item_details"):
        return client.assets.retrieve(id=item_id).dump()

# Create extension apps
tracing_app = create_tracing_app()  # Provides FunctionTracer dependency
mcp_app = create_mcp_app()
introspection_app = create_introspection_app()

# Compose apps - FunctionTracer is now available to all apps!
handle = create_function_service(tracing_app, introspection_app, mcp_app, app)

# Now MCP tools can also use 'tracer' with the same parameter name
@mcp_app.tool("Get item with tracing")
def get_item_tool(client: CogniteClient, tracer: FunctionTracer, item_id: int) -> dict[str, Any]:
    with tracer.span("mcp_get_item"):
        # FunctionTracer from TracingApp is available here!
        return client.assets.retrieve(id=item_id).dump()
```

**Note:** `TracingApp` also provides a `@tracing.trace()` decorator for automatic root span creation. See the [Distributed Tracing](tracing.md) guide for complete examples.

**If you don't pass a custom registry**, `create_function_service()` creates a default registry with the built-in framework dependencies (`client`, `secrets`, `logger`, `function_call_info`). This is sufficient for most use cases.

## Dependency Lifecycle

Dependencies are created once per request:

1. Request arrives at the function
2. Framework creates dependency context (`client`, `secrets`, `function_call_info`)
3. Custom dependency providers are called with the context
4. Dependencies are injected into handler parameters
5. Handler executes with all dependencies available

## Best Practices

### Use Type Annotations

Always use proper type annotations for dependencies:

```python
# **Good** - clear type annotation
def handler(client: CogniteClient, cache: redis.Redis) -> dict[str, Any]:
    pass

# **Bad** - no type annotation
def handler(client, cache) -> dict[str, Any]:  # type: ignore[no-untyped-def]
    pass
```

### Consistent Parameter Names

When registering custom dependencies with `param_name`, use the same parameter name across all handlers:

```python
# **Good** - consistent naming
@app.get("/endpoint1")
def handler1(cache: redis.Redis): pass

@app.get("/endpoint2")
def handler2(cache: redis.Redis): pass

# **Bad** - inconsistent naming
@app.get("/endpoint1")
def handler1(cache: redis.Redis): pass

@app.get("/endpoint2")
def handler2(redis_conn: redis.Redis): pass  # Different name!
```

### Don't Create Heavy Dependencies

Keep dependency creation lightweight:

```python
# **Good** - lightweight connection
registry.register(
    provider=lambda ctx: redis.Redis.from_url(ctx["secrets"]["REDIS_URL"]),
    target_type=redis.Redis,
    param_name="cache"
)

# **Bad** - heavy initialization
registry.register(
    provider=lambda ctx: train_ml_model(),  # Don't do expensive work here!
    target_type=MLModel,
    param_name="model"
)
```

### Use Secrets for Configuration

Pass configuration through secrets, not hardcoded values:

```python
# **Good** - configuration from secrets
registry.register(
    provider=lambda ctx: MyClient(
        api_key=ctx["secrets"]["API_KEY"],
        endpoint=ctx["secrets"]["API_ENDPOINT"]
    ),
    target_type=MyClient,
    param_name="my_client"
)

# **Bad** - hardcoded configuration
registry.register(
    provider=lambda ctx: MyClient(
        api_key="hardcoded-key",  # Don't hardcode credentials!
        endpoint="https://api.example.com"
    ),
    target_type=MyClient,
    param_name="my_client"
)
```

## See Also

- [Response Customization](response-customization.md) - Using RequestHeaders for custom logic
- [Logging](logging.md) - Using the injected logger
- [Distributed Tracing](tracing.md) - Using the injected tracer
- [App Composition](app-composition.md) - How apps share dependencies
- [API Reference](api-reference.md) - Complete API documentation
