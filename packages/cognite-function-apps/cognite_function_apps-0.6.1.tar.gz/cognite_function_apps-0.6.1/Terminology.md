# Terminology

## Overview

The framework has a clear hierarchy:

```text
Service (the deployed Cognite Function)
  ├── App 1 (e.g., MCP - AI tool integration)
  │    ├── Endpoint: GET /__mcp_tools__
  │    └── Endpoint: POST /__mcp_call__/{tool_name}
  ├── App 2 (e.g., Introspection - system endpoints)
  │    ├── Endpoint: GET /__schema__
  │    ├── Endpoint: GET /__routes__
  │    └── Endpoint: GET /__health__
  └── App 3 (Main business logic)
       ├── Endpoint: GET /items/{item_id}
       ├── Endpoint: POST /items/
       └── Endpoint: POST /process/batch
```

- **Service**: The complete deployed Cognite Function (one per deployment)
- **App**: Composable middleware components (one or more per service)
- **Endpoint**: Individual endpoints (one or more per app)

Apps are composed **left-to-right** for endpoint routing, with the **last app** providing the service metadata (title, version).

## Function Application

A Function Application (`FunctionApp`) is the main class for creating Cognite Function
applications.

```python
app = FunctionApp("My Service", "1.0.0")
```

An app is a composable component that contains application endpoints. Apps can be:

- **Business logic apps**: Your main application logic (users create these directly)
- **System apps**: Middleware-like apps (MCP, introspection) that extend framework
  behavior. Customers may in a similar manner create advanced middleware by subclassing
  `FunctionApp` to extend the framework and add specialized behavior needed for their
  Function use cases.

All applications use the same `FunctionApp` base class and can be composed together.

**Extension Pattern:**

- **End users**: Create apps directly with `FunctionApp("My Service", "1.0.0")`
- **Middleware authors**: Subclass `FunctionApp` to add specialized behavior:
  - Override `set_context()` to access composition information
  - Add custom state and methods (e.g., `MCPApp` adds `tool()` decorator)
  - Examples: `MCPApp(FunctionApp)`, `IntrospectionApp(FunctionApp)`

```python
app = FunctionApp("Asset Management", "1.0.0")
mcp_app = create_mcp_app(...)
introspection_app = create_introspection_app()

# Compose apps (left-to-right routing)
handle = create_function_service(mcp_app, introspection_app, app)
```

## Application Endpoints

An endpoint is a single function endpoint that can be selected and executed by a
matching route, and is defined on an app using decorators:

- `@app.get(path)` - GET endpoint
- `@app.post(path)` - POST endpoint
- `@app.put(path)` - PUT endpoint
- `@app.delete(path)` - DELETE endpoint

```python
@app.get("/items/{item_id}")
def get_item(client: CogniteClient, item_id: int) -> dict:
    return {"id": item_id}
```

## Endpoint Routing

The framework uses a Router to match routes to endpoints. Each application endpoint is
registered with the Router, and routes are matched using the HTTP method and the path.

## Tools

A tool is an MCP tool that is defined on an application endpoint using the `@mcp.tool`
decorator:

```python
@mcp.tool(name="get_item", description="Get an item by ID")
def get_item(client: CogniteClient, item_id: int) -> dict:
    return {"id": item_id}
```

## Service

An application service is the complete deployed Cognite Function. It's composed of one
or more applications, and exposed through a handle function.

```python
# Compose apps into a service
handle = create_function_service(mcp_app, introspection_app, main_app)
```

The service handle is the entry point that the Cognite Functions platform invokes. It
has the signature:

```python
handle(client, data, secrets, function_call_info)
```

**Note:** The term "handle" is legacy terminology from when Cognite used OpenFaaS as a
platform. In the current framework, the handle represents the entry point to the
complete application service - all your composed apps packaged for deployment.
