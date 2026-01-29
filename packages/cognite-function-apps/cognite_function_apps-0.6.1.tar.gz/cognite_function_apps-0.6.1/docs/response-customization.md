# Response Customization

The framework provides flexible control over HTTP responses through decorator parameters for static configuration and the `Response[T]` wrapper for dynamic control.

## Overview

Response customization allows you to:

- **Set HTTP status codes** - Return 201 (Created), 202 (Accepted), 204 (No Content), etc.
- **Control content types** - Return HTML, plain text, CSV, or other text-based formats
- **Add response headers** - Set Cache-Control, custom headers, and more
- **Content negotiation** - Route requests based on Accept header

## Decorator Parameters (Static Configuration)

For responses that always use the same status code, content type, or headers, use decorator parameters:

### Status Code

```python
from cognite_function_apps import FunctionApp
from cognite.client import CogniteClient
from pydantic import BaseModel

app = FunctionApp(title="My API", version="1.0.0")

class Item(BaseModel):
    name: str
    price: float

# Return 201 Created for POST endpoints
@app.post("/items", status_code=201)
def create_item(client: CogniteClient, item: Item) -> Item:
    """Create a new item - returns 201 Created"""
    return item

# Return 204 No Content for DELETE endpoints
@app.delete("/items/{item_id}", status_code=204)
def delete_item(client: CogniteClient, item_id: int) -> dict[str, Any]:
    """Delete an item - returns 204 No Content"""
    return {}
```

### Content Type

```python
# Return HTML instead of JSON
@app.get("/page", content_type="text/html")
def get_page(client: CogniteClient) -> str:
    """Return an HTML page"""
    return "<html><body><h1>Hello World</h1></body></html>"

# Return plain text
@app.get("/health", content_type="text/plain")
def health_check(client: CogniteClient) -> str:
    """Simple health check returning plain text"""
    return "OK"

# Return CSV data
@app.get("/export", content_type="text/csv")
def export_data(client: CogniteClient) -> str:
    """Export data as CSV"""
    return "name,price\nWidget,29.99\nGadget,49.99"
```

### Cache-Control

```python
# Enable caching for GET endpoints
@app.get("/items/{item_id}", cache_control="max-age=3600")
def get_item(client: CogniteClient, item_id: int) -> Item:
    """Cached for 1 hour"""
    return Item(name=f"Item {item_id}", price=29.99)

# Disable caching for sensitive data
@app.get("/user/profile", cache_control="no-store, no-cache, must-revalidate")
def get_profile(client: CogniteClient) -> dict[str, Any]:
    """Never cached"""
    return {"username": "alice"}
```

### Extra Headers

```python
# Add custom headers to response
@app.get("/items/{item_id}", extra_headers={"x-api-version": "2.0"})
def get_item(client: CogniteClient, item_id: int) -> Item:
    """Response includes custom API version header"""
    return Item(name=f"Item {item_id}", price=29.99)
```

### Content Negotiation (Accept Header Routing)

The same path can have multiple handlers based on the Accept header:

```python
# JSON handler (default)
@app.get("/items/{item_id}", accept="application/json")
def get_item_json(client: CogniteClient, item_id: int) -> Item:
    """Return item as JSON"""
    return Item(name=f"Item {item_id}", price=29.99)

# HTML handler
@app.get("/items/{item_id}", accept="text/html", content_type="text/html")
def get_item_html(client: CogniteClient, item_id: int) -> str:
    """Return item as HTML page"""
    return f"<html><body><h1>Item {item_id}</h1><p>Price: $29.99</p></body></html>"

# Plain text handler
@app.get("/items/{item_id}", accept="text/plain", content_type="text/plain")
def get_item_text(client: CogniteClient, item_id: int) -> str:
    """Return item as plain text"""
    return f"Item {item_id}: $29.99"
```

**Accept Header Matching:**

- `accept=None` (default) - Matches any request (fallback handler)
- Specific accept value - Must match request's Accept header
- Request with `*/*` - Matches any handler
- Media range wildcards - `text/*` matches `text/html`, `text/plain`, etc.
- If no match found - Returns 406 Not Acceptable

### Combined Example

```python
@app.get(
    "/items/{item_id}",
    content_type="application/json",
    accept="application/json",
    status_code=200,
    cache_control="max-age=3600",
    extra_headers={"x-api-version": "2.0", "x-request-id": "static-id"}
)
def get_item(client: CogniteClient, item_id: int) -> Item:
    """Get item with full response customization"""
    return Item(name=f"Item {item_id}", price=29.99)
```

## Response[T] Wrapper (Dynamic Configuration)

When you need to determine status codes or headers at runtime, use the `Response[T]` wrapper:

```python
from cognite_function_apps import FunctionApp, Response
from cognite.client import CogniteClient
from pydantic import BaseModel

app = FunctionApp(title="My API", version="1.0.0")

class Job(BaseModel):
    id: str
    status: str

@app.post("/jobs")
def create_job(client: CogniteClient, job: Job) -> Response[Job]:
    """Create a job - status code depends on processing mode"""
    if job.status == "queued":
        # Async processing - return 202 Accepted
        return Response(data=job, status_code=202, cache_control="no-store")
    else:
        # Sync processing - return 201 Created
        return Response(data=job, status_code=201)
```

### Response[T] Fields

| Field | Type | Description |
|-------|------|-------------|
| `data` | `T` | The actual response data (required) |
| `status_code` | `int` | HTTP status code (default: 200) |
| `cache_control` | `str \| None` | Cache-Control header value |
| `extra_headers` | `dict[str, str] \| None` | Additional HTTP headers |

### Usage Patterns

```python
# Simple - just override status code
return Response(data=item, status_code=201)

# With caching disabled
return Response(data=item, cache_control="no-store")

# With custom headers
return Response(data=item, extra_headers={"x-request-id": request_id})

# Combined - all options
return Response(
    data=job,
    status_code=202,
    cache_control="no-cache",
    extra_headers={"x-job-id": job.id, "x-estimated-time": "30s"}
)
```

### Priority: Response[T] Overrides Decorator Defaults

When both decorator parameters and `Response[T]` are used, `Response[T]` values take priority:

```python
@app.post("/items", status_code=201, cache_control="max-age=300")
def create_item(client: CogniteClient, item: Item) -> Response[Item]:
    if item.price > 1000:
        # High-value items: override to 202 and disable caching
        return Response(data=item, status_code=202, cache_control="no-store")
    else:
        # Regular items: use decorator defaults (201, max-age=300)
        return Response(data=item)
```

### Type Safety with Response[T]

The generic type parameter `T` preserves return type information for OpenAPI schema generation:

```python
# OpenAPI schema shows Item as the response type, not Response
@app.get("/items/{item_id}")
def get_item(client: CogniteClient, item_id: int) -> Response[Item]:
    return Response(data=Item(name="Widget", price=29.99))

# Works with any type
@app.get("/items")
def list_items(client: CogniteClient) -> Response[list[Item]]:
    items = [Item(name="Widget", price=29.99)]
    return Response(data=items, cache_control="max-age=60")
```

## Accessing Request Headers

Use the `RequestHeaders` type to access incoming HTTP headers:

```python
from cognite_function_apps import FunctionApp
from cognite_function_apps.models import RequestHeaders
from cognite.client import CogniteClient

app = FunctionApp(title="My API", version="1.0.0")

@app.get("/items/{item_id}")
def get_item(
    client: CogniteClient,
    headers: RequestHeaders,
    item_id: int
) -> dict[str, Any]:
    """Access request headers for custom logic"""
    # Headers are lowercase (HTTP/2 convention)
    auth = headers.get("authorization")
    user_agent = headers.get("user-agent")
    custom_header = headers.get("x-custom-header")

    return {
        "id": item_id,
        "has_auth": auth is not None,
        "user_agent": user_agent
    }
```

`RequestHeaders` is a `Mapping[str, str]` with header names in lowercase.

## Wire Format

### Success Response

```json
{
    "status_code": 200,
    "data": {"name": "Widget", "price": 29.99},
    "headers": {
        "content-type": "application/json",
        "cache-control": "max-age=3600"
    }
}
```

### With Custom Status Code (201 Created)

```json
{
    "status_code": 201,
    "data": {"id": 123, "name": "Widget"},
    "headers": {
        "content-type": "application/json"
    }
}
```

### HTML Response

```json
{
    "status_code": 200,
    "data": "<html><body>Hello</body></html>",
    "headers": {
        "content-type": "text/html"
    }
}
```

### Error Response

```json
{
    "status_code": 404,
    "error_type": "NotFound",
    "message": "Item not found",
    "headers": {
        "content-type": "application/json"
    }
}
```

**Note:** Use `status_code < 400` to determine if a response is successful or an error.

## Supported Content Types

The framework supports text-based content types where the payload can be represented as a JSON-compatible string:

| Content Type | Description | Example Use Case |
|--------------|-------------|------------------|
| `application/json` | JSON (default) | API responses |
| `text/html` | HTML pages | Web pages, reports |
| `text/plain` | Plain text | Simple responses |
| `text/csv` | CSV data | Data exports |
| `application/xml` | XML documents | Legacy integrations |

### Binary Data Limitations

Binary data (images, PDFs, etc.) is **not directly supported** because the Cognite Functions runtime uses JSON as the transport format. For binary data, use base64 encoding:

```python
import base64

@app.get("/images/{image_id}")
def get_image(client: CogniteClient, image_id: int) -> dict[str, Any]:
    """Return base64-encoded image"""
    image_bytes = fetch_image(image_id)
    return {
        "data": base64.b64encode(image_bytes).decode("ascii"),
        "content_type": "image/png",
        "encoding": "base64"
    }
```

## Complete Example

```python
from cognite_function_apps import FunctionApp, Response, create_function_service
from cognite_function_apps.models import RequestHeaders
from cognite_function_apps.introspection import create_introspection_app
from cognite.client import CogniteClient
from pydantic import BaseModel

app = FunctionApp(title="Item API", version="1.0.0")

class Item(BaseModel):
    id: int
    name: str
    price: float

# JSON response (default)
@app.get("/items/{item_id}", cache_control="max-age=300")
def get_item(client: CogniteClient, item_id: int) -> Item:
    """Get item as JSON with caching"""
    return Item(id=item_id, name="Widget", price=29.99)

# HTML response
@app.get("/items/{item_id}", accept="text/html", content_type="text/html")
def get_item_html(client: CogniteClient, item_id: int) -> str:
    """Get item as HTML page"""
    return f"<html><body><h1>Item {item_id}</h1></body></html>"

# Dynamic status code with Response[T]
@app.post("/items", status_code=201)
def create_item(
    client: CogniteClient,
    headers: RequestHeaders,
    item: Item
) -> Response[Item]:
    """Create item with dynamic status code"""
    # Check for async processing request
    prefer = headers.get("prefer", "")
    if "respond-async" in prefer:
        # Queue for async processing
        return Response(data=item, status_code=202, cache_control="no-store")
    else:
        # Sync creation
        return Response(data=item, status_code=201)

# Create service with introspection
introspection = create_introspection_app()
handle = create_function_service(introspection, app)
```

## Best Practices

1. **Use decorator parameters for static configuration** - When the status code or headers are always the same
2. **Use Response[T] for dynamic configuration** - When the response varies based on runtime conditions
3. **Set appropriate status codes** - Use 201 for creation, 202 for async processing, 204 for no content
4. **Use cache-control headers** - Enable caching for read-only endpoints, disable for sensitive data
5. **Keep content negotiation simple** - Most APIs only need JSON; add HTML for user-facing pages
6. **Header names in lowercase** - Follow HTTP/2 convention for request headers

## See Also

- [Error Handling](error-handling.md) - Structured error responses
- [Dependency Injection](dependency-injection.md) - Using RequestHeaders dependency
- [Type Safety](type-safety.md) - Type validation and conversion
- [API Reference](api-reference.md) - Complete API documentation
