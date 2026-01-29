# ADR: Response Customization

## Problem Statement

The current framework lacks flexibility in HTTP response handling:

1. **No content-type control** - All responses are `application/json`. Endpoints cannot specify alternative content types when needed.

2. **No status code control** - Success responses always return 200. Endpoints cannot return 201 (Created), 202 (Accepted), or other semantically correct status codes.

3. **Error status codes are guessed** - The devserver infers HTTP status from `error_type` field, which is fragile and imprecise.

4. **No caching headers** - No way to set `Cache-Control` or other caching directives, preventing proper HTTP caching.

5. **No content negotiation** - Cannot route requests based on `Accept` header to serve different representations of the same resource.

6. **No request header access** - Endpoints cannot read incoming HTTP headers (e.g., `Authorization`, custom headers).

7. **Redundant `success` field** - The response includes both `success: true/false` and implicitly conveys success via presence of `data` vs `error_type`, creating potential inconsistencies.

## How

We solve this through three complementary mechanisms:

1. **Decorator parameters** for static, per-endpoint configuration:
   - `content_type` - Response MIME type (default: `application/json`)
   - `accept` - Accept header matching for content negotiation
   - `status_code` - Default success status code (default: 200)
   - `cache_control` - Cache-Control header value
   - `extra_headers` - Additional custom headers

2. **`Response[T]` generic wrapper** for dynamic, per-request control:
   - Allows endpoints to override `status_code`, `cache_control`, `extra_headers` at runtime
   - Generic type parameter preserves return type information for OpenAPI schema generation
   - Framework detects `Response` instances and extracts the inner data

3. **`RequestHeaders` dependency injection** for accessing incoming headers:
   - Injected automatically when declared as a parameter
   - Provides read-only access to request headers

4. **Simplified wire format**:
   - Remove redundant `success` field
   - Add explicit `status_code` field
   - Add `headers` dict for response headers
   - Use `status_code < 400` to determine success

## Design

### Decorator Parameters (static per endpoint)

#### Content-Type

```python
# Return HTML instead of JSON
@app.get("/page", content_type="text/html")
def get_page(client: CogniteClient) -> str:
    return "<html><body>Hello World</body></html>"
```

#### Status Code

```python
# Return 201 Created for POST endpoints
@app.post("/items", status_code=201)
def create_item(client: CogniteClient, item: Item) -> Item:
    return item
```

#### Cache-Control

```python
# Enable caching for GET endpoints
@app.get("/items/{item_id}", cache_control="max-age=3600")
def get_item(client: CogniteClient, item_id: int) -> Item:
    return fetch_item(item_id)
```

#### Content Negotiation (Accept header routing)

```python
# Same path, different handlers based on Accept header
@app.get("/items/{item_id}", accept="application/json")
def get_item_json(client: CogniteClient, item_id: int) -> Item:
    return fetch_item(item_id)

@app.get("/items/{item_id}", accept="text/html", content_type="text/html")
def get_item_html(client: CogniteClient, item_id: int) -> str:
    item = fetch_item(item_id)
    return f"<html><body>{item.name}</body></html>"
```

#### Extra Headers

```python
# Add custom headers to response
@app.get("/items/{item_id}", extra_headers={"x-custom-header": "value"})
def get_item(client: CogniteClient, item_id: int) -> Item:
    return fetch_item(item_id)
```

#### Combined Example

```python
@app.get("/items/{item_id}",
    content_type="text/html",
    accept="text/html",
    status_code=200,
    cache_control="max-age=3600",
    extra_headers={"x-custom": "value"}
)
def get_item_html(client: CogniteClient, item_id: int) -> str:
    return "<html>...</html>"
```

### Response[T] Wrapper (dynamic per request)

```python
from cognite_function_apps import Response

@app.post("/jobs")
def create_job(client: CogniteClient, job: Job) -> Response[Job]:
    if async_mode:
        return Response(data=job, status_code=202, cache_control="no-store")
    return Response(data=job, status_code=201)
```

- Generic preserves type info for schema generation
- `status_code`, `cache_control`, `extra_headers` (NOT content_type - that's static per endpoint)
- Overrides decorator defaults when returned

#### Response[T] Model Definition

```python
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class Response(BaseModel, Generic[T]):
    """Generic response wrapper for dynamic status codes and headers.

    The type parameter T preserves return type information for schema generation.
    Schema generators should extract T from Response[T] for OpenAPI documentation.
    """

    data: T
    """The actual response data (typed for schema generation)"""

    status_code: int = 200
    """HTTP status code (overrides decorator default)"""

    cache_control: str | None = None
    """Cache-Control header value (overrides decorator default)"""

    extra_headers: dict[str, str] | None = None
    """Additional HTTP headers (merged with decorator defaults)"""
```

#### Usage Patterns

```python
# Simple - just override status code
return Response(data=item, status_code=201)

# With caching
return Response(data=item, cache_control="no-store")

# With custom headers
return Response(data=item, extra_headers={"x-request-id": request_id})

# Combined
return Response(
    data=job,
    status_code=202,
    cache_control="no-cache",
    extra_headers={"x-job-id": job.id}
)
```

### RequestHeaders DI (access request headers)

```python
@app.get("/items/{item_id}")
def get_item(client: CogniteClient, headers: RequestHeaders, item_id: int) -> Item:
    auth = headers.get("authorization")
    ...
```

#### RequestHeaders Type Definition

```python
from typing import NewType
from collections.abc import Mapping

# Simple type alias - immutable mapping of header name to value
# Header names are lowercase (HTTP/2 convention)
RequestHeaders = NewType("RequestHeaders", Mapping[str, str])
```

The `RequestHeaders` type is registered as a dependency and injected from the ASGI scope's headers.

## Wire Format

Success response:

```json
{
  "status_code": 200,
  "data": "...",
  "headers": {
    "content-type": "text/html",
    "cache-control": "max-age=3600"
  }
}
```

Error response:

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

**Decision**: The `success` field is removed. Use `status_code < 400` to determine success.

## Changes Required

### 1. Models ([`models.py`](../src/cognite_function_apps/models.py))

- Remove `success` field from `CogniteTypedResponse` and `CogniteTypedError`
- Add `ContentType` literal type
- Add `status_code` and `headers` to response message types
- Create `RequestHeaders` type for DI
- Create `Response[T]` generic class

### 2. RouteInfo ([`routing.py`](../src/cognite_function_apps/routing.py))

- Add fields: `content_type`, `accept`, `status_code`, `cache_control`, `extra_headers`
- Update route matching to consider `accept` header

### 3. Dependency Registry ([`dependency_registry.py`](../src/cognite_function_apps/dependency_registry.py))

- Register `RequestHeaders` as injectable dependency

### 4. Route Decorators ([`app.py`](../src/cognite_function_apps/app.py))

- Add new parameters to `register_route()` and decorators
- Update `execute_function_and_format_response()` to:
  - **Detect `Response` instances**: Check if returned value is `Response` type
  - **Extract data**: Use `response.data` as the actual response data
  - **Merge headers**: Combine decorator defaults with Response overrides
  - Include `status_code` and `headers` in wire format response
- Update route dispatch to handle `accept` header matching

### 5. Devserver ([`devserver/asgi.py`](../src/cognite_function_apps/devserver/asgi.py))

- Read `status_code` and `headers` from response
- Send raw content for `text/html` with correct HTTP headers
- Pass through request headers for DI

### 6. Schema Generation ([`schema.py`](../src/cognite_function_apps/schema.py))

- **Unwrap `Response[T]`**: When return type is `Response[T]`, extract `T` using `get_args()` for the actual response schema

  ```python
  from typing import get_origin, get_args

  def get_response_type(return_type: type) -> type:
      """Extract inner type from Response[T] if present."""
      if get_origin(return_type) is Response:
          args = get_args(return_type)
          return args[0] if args else Any
      return return_type
  ```

- Include `content_type` in response content types
- Document `accept` header parameter in OpenAPI spec

### 7. Introspection ([`introspection.py`](../src/cognite_function_apps/introspection.py))

- Include new route metadata in `/__routes__` (content_type, accept, status_code, cache_control)
- **Unwrap `Response[T]`** in `/__client_methods__` endpoint to expose actual return types

### 8. Tests

- Response[T] type extraction and handling
- Content negotiation (accept header routing)
- RequestHeaders injection
- Devserver content-type handling
- Schema generation with Response[T]

## Decisions

- **Default content-type**: `application/json` is the implicit default (no need to declare explicitly)
- **Accept header fallback** (following FastAPI pattern):
  - No Accept header or `*/*` → Use default (`application/json`)
  - Accept doesn't match any handler → Return **406 Not Acceptable**

## Limitations / Out of Scope

### Binary Data (bytes)

**Binary data (images, PDFs, etc.) is out of scope for this iteration.**

The framework is built on a JSON transport layer:

1. **`FunctionService`** returns `DataDict` (which is `Mapping[str, Json]`) — the wire format is fundamentally JSON
2. **Cognite Functions runtime** expects JSON responses — this is a platform constraint we cannot change
3. The **`Json` type** explicitly excludes `bytes`: `Mapping[str, Json] | Sequence[Json] | str | int | float | bool | None`

**Supported content types** are text-based formats where the payload is a string:

- `text/html` — HTML pages
- `text/plain` — Plain text
- `text/csv` — CSV data
- `application/xml` — XML documents
- Any content type where the data can be represented as a JSON-compatible string

**If binary data is needed**, users must handle encoding at the application level:

```python
import base64

@app.get("/images/{image_id}", content_type="application/json")
def get_image(client: CogniteClient, image_id: int) -> dict:
    image_bytes = fetch_image(image_id)
    return {
        "data": base64.b64encode(image_bytes).decode("ascii"),
        "content_type": "image/png",
        "encoding": "base64"
    }
```

A future iteration could explore:

- A `BinaryResponse` type with automatic base64 encoding
- Devserver support for decoding base64 to raw bytes for HTTP responses
- Convention-based detection (e.g., `{"_base64": "...", "_content_type": "..."}`)

This would require its own ADR to properly design the encoding conventions and wire format changes.

---

## Implementation Todo List

### Phase 1: Core Models and Types

- [ ] Add `Response[T]` generic class to `models.py`
- [ ] Add `RequestHeaders` NewType to `models.py`
- [ ] Add `ContentType` literal type to `models.py`
- [ ] Update `CogniteTypedResponse` - remove `success`, add `status_code`, `headers`
- [ ] Update `CogniteTypedError` - remove `success`, add `status_code`, `headers`
- [ ] Update `ASGITypedFunctionResponseMessage` with new fields

### Phase 2: Routing Infrastructure

- [ ] Add new fields to `RouteInfo` dataclass: `content_type`, `accept`, `status_code`, `cache_control`, `extra_headers`
- [ ] Update route matching to filter by `accept` header
- [ ] Implement 406 Not Acceptable response for unmatched Accept headers

### Phase 3: Decorator API

- [ ] Add parameters to `register_route()`: `content_type`, `accept`, `status_code`, `cache_control`, `extra_headers`
- [ ] Update `_create_route_decorator()` with new parameters
- [ ] Update `get()`, `post()`, `put()`, `delete()` decorators

### Phase 4: Response Handling

- [ ] Update `execute_function_and_format_response()` to detect `Response` instances
- [ ] Extract `data` from `Response` wrapper
- [ ] Merge decorator defaults with `Response` overrides
- [ ] Build wire format with `status_code` and `headers`

### Phase 5: Dependency Injection

- [ ] Register `RequestHeaders` as injectable dependency in `create_default_registry()`
- [ ] Pass request headers from ASGI scope to DI context

### Phase 6: Devserver Updates

- [ ] Read `status_code` from response and use for HTTP status
- [ ] Read `headers` from response and set HTTP headers
- [ ] For `text/html` content-type, send raw data (not JSON wrapped)
- [ ] Pass request headers through for DI

### Phase 7: Schema & Introspection

- [ ] Add `get_response_type()` helper to unwrap `Response[T]`
- [ ] Update `_generate_response_schema()` to use unwrapped type
- [ ] Include `content_type` in OpenAPI response content types
- [ ] Update `/__routes__` to include new route metadata
- [ ] Update `/__client_methods__` to unwrap `Response[T]` return types

### Phase 8: Tests

- [ ] Test `Response[T]` creation and field access
- [ ] Test Response type unwrapping in schema generation
- [ ] Test decorator parameters (content_type, accept, status_code, cache_control, extra_headers)
- [ ] Test Accept header content negotiation routing
- [ ] Test 406 Not Acceptable for unmatched Accept
- [ ] Test `RequestHeaders` dependency injection
- [ ] Test devserver sends correct HTTP status codes
- [ ] Test devserver sends correct Content-Type headers
- [ ] Test devserver sends raw HTML for text/html
- [ ] Test wire format structure (no `success` field)

### Phase 9: Documentation

- [ ] Update API reference docs
- [ ] Add content-type guide to docs
- [ ] Update error handling docs
- [ ] Add examples for `Response[T]` usage
