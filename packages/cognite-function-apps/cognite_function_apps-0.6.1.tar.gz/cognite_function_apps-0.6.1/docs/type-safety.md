# Type Safety and Validation

The framework provides comprehensive type safety with automatic validation and conversion.

## Overview

The framework uses Pydantic for robust type validation and automatic type conversions:

- **Input validation** - Pydantic models validate request data
- **Output validation** - Response models ensure consistent output format
- **Type coercion** - Automatic conversion of string parameters to correct types
- **Detailed error messages** - Validation errors include precise paths for debugging

## Basic Type Conversions

The framework automatically converts string parameters to the expected types:

### Primitive Types

```python
from cognite_function_apps import FunctionApp

app = FunctionApp(title="Type Demo", version="1.0.0")

@app.get("/convert")
def convert_types(
    client: CogniteClient,
    string_val: str,          # No conversion needed
    int_val: int,             # "123" → 123
    float_val: float,         # "3.14" → 3.14
    bool_val: bool,           # "true", "1", "yes", "on" → True
    optional_val: str | None = None  # None if not provided
) -> dict[str, Any]:
    """Demonstrates automatic type conversion"""
    return {
        "string": string_val,
        "int": int_val,
        "float": float_val,
        "bool": bool_val,
        "optional": optional_val
    }
```

**Boolean Conversion:**

The framework accepts multiple formats for boolean values:

- `True`: "true", "1", "yes", "on" (case-insensitive)
- `False`: "false", "0", "no", "off" (case-insensitive)

### Pydantic Models

Dictionaries are automatically converted to Pydantic model instances:

```python
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float
    description: str | None = None

@app.post("/items/")
def create_item(client: CogniteClient, item: Item) -> dict[str, Any]:
    """
    Request body:
    {
        "name": "Widget",
        "price": 29.99,
        "description": "A useful widget"
    }

    Automatically converted to Item instance with validation
    """
    return {"id": 123, "item": item.model_dump()}
```

### Lists of Models

Lists of dictionaries are converted to lists of model instances:

```python
@app.post("/process/batch")
def process_batch(client: CogniteClient, items: list[Item]) -> dict[str, Any]:
    """
    Request body:
    {
        "items": [
            {"name": "Widget", "price": 29.99},
            {"name": "Gadget", "price": 49.99}
        ]
    }

    Each dict is converted to an Item instance
    """
    total_value = sum(item.price for item in items)
    return {"processed_count": len(items), "total_value": total_value}
```

## Recursive Type Conversions

The framework handles arbitrarily nested combinations of types:

### Supported Nested Types

```python
# Complex nested types supported
dict[str, BaseModel]                    # Dict with model values
Optional[BaseModel]                     # Optional models
Union[BaseModel, str]                   # Union types with fallback
list[dict[str, BaseModel]]              # List of dicts of models
dict[str, list[BaseModel]]              # Dict containing lists of models
```

### Real-World Example

```python
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int

class Team(BaseModel):
    name: str
    leader: User                        # Nested model
    members: list[User]                 # List of models

@app.post("/teams")
def create_team(client: CogniteClient, team: Team) -> dict[str, Any]:
    """
    Input automatically converted:
    {
      "name": "Engineering",
      "leader": {"name": "Alice", "age": 30},      # → User instance
      "members": [                                 # → list[User]
        {"name": "Bob", "age": 25},                # → User instance
        {"name": "Carol", "age": 28}               # → User instance
      ]
    }
    """
    return {
        "team_name": team.name,
        "leader_name": team.leader.name,
        "members_count": len(team.members)
    }
```

## Type Annotation Compatibility

The framework supports both legacy and modern Python type annotation syntaxes:

### Union Types

```python
from typing import Union

# Both work identically
def process_legacy(client: CogniteClient, data: Union[User, str]) -> Response:
    pass

def process_modern(client: CogniteClient, data: User | str) -> Response:
    pass
```

### Optional Types

```python
from typing import Optional

# Both work identically
def get_user_legacy(client: CogniteClient, user: Optional[User]) -> Response:
    pass

def get_user_modern(client: CogniteClient, user: User | None) -> Response:
    pass
```

### Collection Types

```python
from typing import List, Dict

# Both work identically
def process_items_legacy(client: CogniteClient, items: List[Item]) -> Dict[str, int]:
    pass

def process_items_modern(client: CogniteClient, items: list[Item]) -> dict[str, int]:
    pass
```

**Recommendation:** Use modern syntax (builtin types) for Python 3.10+ projects.

## Validation Errors

When validation fails, the framework returns detailed error information:

```python
# Request with invalid data
{
    "path": "/items/",
    "method": "POST",
    "body": {
        "name": "Widget",
        "price": "not-a-number"  # Invalid!
    }
}

# Response with validation error
{
    "status_code": 400,
    "error_type": "ValidationError",
    "message": "Input validation failed: 1 error(s)",
    "details": {
        "errors": [
            {
                "loc": ["price"],
                "msg": "value is not a valid float",
                "type": "type_error.float"
            }
        ]
    },
    "headers": {
        "content-type": "application/json"
    }
}
```

## Pydantic Model Features

You can use all Pydantic features in your models:

### Field Validation

```python
from pydantic import BaseModel, Field

class Item(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0, description="Price must be positive")
    quantity: int = Field(1, ge=1, le=1000)
    tags: list[str] = Field(default_factory=list)

@app.post("/items/")
def create_item(client: CogniteClient, item: Item) -> dict[str, Any]:
    # Pydantic validates all field constraints automatically
    return {"item": item.model_dump()}
```

### Custom Validators

```python
from pydantic import BaseModel, field_validator

class User(BaseModel):
    email: str
    age: int

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if '@' not in v:
            raise ValueError('Invalid email address')
        return v.lower()

    @field_validator('age')
    @classmethod
    def validate_age(cls, v: int) -> int:
        if v < 0 or v > 150:
            raise ValueError('Age must be between 0 and 150')
        return v

@app.post("/users/")
def create_user(client: CogniteClient, user: User) -> dict[str, Any]:
    # Custom validators are executed automatically
    return {"user": user.model_dump()}
```

### Computed Fields

```python
from pydantic import BaseModel, computed_field

class Item(BaseModel):
    name: str
    price: float
    tax_rate: float = 0.1

    @computed_field
    @property
    def total_price(self) -> float:
        return self.price * (1 + self.tax_rate)

@app.post("/items/")
def create_item(client: CogniteClient, item: Item) -> dict[str, Any]:
    # total_price is computed automatically
    return {"item": item.model_dump()}
```

## Type Conversion Errors

When a parameter cannot be converted to the expected type:

```python
# Request
{
    "path": "/items/not-a-number",
    "method": "GET"
}

# Response
{
    "status_code": 400,
    "error_type": "TypeConversionError",
    "message": "Failed to convert parameter 'item_id' to type <class 'int'>",
    "details": {
        "parameter": "item_id",
        "expected_type": "int",
        "value": "not-a-number"
    },
    "headers": {
        "content-type": "application/json"
    }
}
```

## Best Practices

### Use Pydantic Models for Complex Data

**Yes** **Good - Structured with validation:**

```python
class CreateItemRequest(BaseModel):
    name: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)
    tags: list[str] = Field(default_factory=list)

@app.post("/items/")
def create_item(client: CogniteClient, request: CreateItemRequest) -> dict[str, Any]:
    # Automatic validation
    return {"item": request.model_dump()}
```

**Avoid:** **Bad - Raw dict without validation:**

```python
@app.post("/items/")
def create_item(client: CogniteClient, data: dict[str, Any]) -> dict[str, Any]:
    # No validation, no type safety
    name = data.get("name")  # Could be None or wrong type
    price = data.get("price")  # Could be None or wrong type
    return {"item": data}
```

### Validate All Inputs

Use Pydantic's field constraints to validate inputs:

```python
from pydantic import BaseModel, Field

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    limit: int = Field(10, ge=1, le=100)
    offset: int = Field(0, ge=0)

@app.post("/search")
def search(client: CogniteClient, request: SearchRequest) -> dict[str, Any]:
    # All inputs are validated before reaching this code
    return {"results": []}
```

### Use Type Hints Everywhere

Always use type hints for better IDE support and runtime validation:

```python
# **Good** - full type hints
@app.get("/items/{item_id}")
def get_item(
    client: CogniteClient,
    item_id: int,
    include_tax: bool = False
) -> dict[str, Any]:
    return {"id": item_id}

# **Bad** - no type hints
@app.get("/items/{item_id}")
def get_item(client, item_id, include_tax=False):  # type: ignore[no-untyped-def]
    return {"id": item_id}
```

### Handle Optional Parameters Properly

```python
# **Good** - clear optional with default
@app.get("/items/{item_id}")
def get_item(
    client: CogniteClient,
    item_id: int,
    include_details: bool = False,
    format: str | None = None
) -> dict[str, Any]:
    return {"id": item_id}

# **Bad** - ambiguous None default
@app.get("/items/{item_id}")
def get_item(client: CogniteClient, item_id: int, format: str | None = None) -> dict[str, Any]:
    return {"id": item_id}
```

## See Also

- [Response Customization](response-customization.md) - Status codes, headers, and content types
- [Error Handling](error-handling.md) - Understanding validation errors
- [Async Support](async-support.md) - Type safety with async handlers
- [API Reference](api-reference.md) - Complete API documentation
