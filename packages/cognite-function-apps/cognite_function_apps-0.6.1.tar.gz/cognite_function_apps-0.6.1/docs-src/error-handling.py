# %%
from typing import Any

# %% [markdown]
"""
# Error Handling

The framework provides structured error handling with detailed information for debugging.

## Error Types

The framework defines several error types for different failure scenarios:

- **RouteNotFound** - No matching route found for the request
- **ValidationError** - Input validation failed (Pydantic validation errors)
- **TypeConversionError** - Parameter type conversion failed
- **ExecutionError** - Function execution failed (unhandled exceptions)

## Response Format

All responses follow a consistent structure.
Use `status_code < 400` to determine if a response is successful or an error.

### Success Response
"""

# %%
# Example success response structure
success_response: dict[str, Any] = {
    "status_code": 200,
    "data": {},  # Your actual response data
    "headers": {"content-type": "application/json"},
}

# %% [markdown]
"""
### Error Response
"""

# %%
# Example error response structure
error_response: dict[str, Any] = {
    "status_code": 400,
    "error_type": "ValidationError",
    "message": "Input validation failed: 1 error(s)",
    "details": {"errors": []},
    "headers": {"content-type": "application/json"},
}

# %% [markdown]
"""
## Error Examples

### Validation Error

When input data fails Pydantic validation:
"""

# %%
from typing import Any

# Request example
request = {
    "path": "/items/",
    "method": "POST",
    "body": {"name": "Widget", "price": "not-a-number"},  # Invalid price
}

# Response example
response: dict[str, Any] = {
    "status_code": 400,
    "error_type": "ValidationError",
    "message": "Input validation failed: 1 error(s)",
    "details": {
        "errors": [
            {
                "loc": ["price"],
                "msg": "value is not a valid float",
                "type": "type_error.float",
            }
        ]
    },
    "headers": {"content-type": "application/json"},
}

# %% [markdown]
"""
### Route Not Found

When no route matches the request:
"""

# %%
from typing import Any

# Request example
request = {"path": "/nonexistent", "method": "GET"}

# Response example
response: dict[str, Any] = {
    "status_code": 404,
    "error_type": "RouteNotFound",
    "message": "No route found for GET /nonexistent",
    "details": {},
    "headers": {"content-type": "application/json"},
}

# %% [markdown]
"""
### Type Conversion Error

When a path or query parameter cannot be converted to the expected type:
"""

# %%
# Request example
request = {
    "path": "/items/not-a-number",  # item_id should be int
    "method": "GET",
}

# Response example
response = {
    "status_code": 400,
    "error_type": "TypeConversionError",
    "message": "Failed to convert parameter 'item_id' to type <class 'int'>",
    "details": {"parameter": "item_id", "expected_type": "int", "value": "not-a-number"},
    "headers": {"content-type": "application/json"},
}

# %% [markdown]
"""
### Execution Error

When an unhandled exception occurs during handler execution:
"""

# %%
# Response example
response: dict[str, Any] = {
    "status_code": 500,
    "error_type": "ExecutionError",
    "message": "Function execution failed: division by zero",
    "details": {"exception_type": "ZeroDivisionError", "traceback": "..."},
    "headers": {"content-type": "application/json"},
}

# %% [markdown]
"""
## Error Handling in Handlers

You can raise exceptions in your handlers, and the framework will catch them and return structured error responses:
"""

# %%
from cognite.client import CogniteClient

from cognite_function_apps import FunctionApp

app = FunctionApp(title="My API", version="1.0.0")


@app.get("/items/{item_id}")
def get_item(client: CogniteClient, item_id: int) -> dict[str, Any]:
    """Retrieve an item by ID."""
    # Validation errors are handled automatically
    if item_id < 0:
        raise ValueError("Item ID must be positive")

    # The framework catches exceptions and returns structured errors
    # item = fetch_item(item_id)  # May raise exception

    return {"id": item_id, "data": {}}


# %% [markdown]
"""
## Custom Error Handling

For more control over error responses, catch exceptions and re-raise them to let the framework
produce a proper structured error response:
"""

# %%
from pydantic import BaseModel


class Item(BaseModel):
    name: str
    price: float


class DatabaseError(Exception):
    """Example database error."""


@app.post("/items/")
def create_item(client: CogniteClient, item: Item) -> dict[str, Any]:
    """Create a new item."""
    try:
        # result = create_in_database(item)
        return {"id": 123, "item": item.model_dump()}
    except DatabaseError as e:
        # Re-raise an exception to let the framework handle it.
        # This will produce a structured error response with a 500 status code.
        raise RuntimeError("Database operation failed") from e


# %% [markdown]
"""
## HTTP Status Codes

The framework uses appropriate HTTP status codes for different scenarios:

| Status Code | Error Type | Description |
|-------------|------------|-------------|
| 200 | - | Successful response (default) |
| 201 | - | Created (use with `status_code=201` decorator parameter) |
| 400 | ValidationError, TypeConversionError | Bad request / invalid input |
| 404 | RouteNotFound | Route not found |
| 406 | NotAcceptable | Accept header doesn't match any route |
| 500 | ExecutionError | Internal server error |

You can customize success status codes using decorator parameters or the `Response[T]` wrapper.
See [Response Customization](response-customization.md) for details.

## Best Practices

1. **Use Pydantic models** - Let the framework handle input validation automatically
2. **Raise descriptive exceptions** - Error messages are included in the response
3. **Log errors** - Use the [injected logger](logging.md) to log errors for debugging
4. **Don't catch everything** - Let the framework handle unexpected errors with proper structure
5. **Return structured data** - Even for success cases, return consistent data structures
6. **Use appropriate status codes** - Use decorator parameters for static codes, `Response[T]` for dynamic codes

## See Also

- [Response Customization](response-customization.md) - Customize status codes, headers, and content types
- [Type Safety](type-safety.md) - Understanding type validation and conversion
- [Logging](logging.md) - Logging errors for debugging
- [API Reference](api-reference.md) - Complete API documentation
"""
