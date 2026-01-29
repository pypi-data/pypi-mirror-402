# FunctionClient Design

## Overview

FunctionClient is a notebook-first developer tool for exploring and consuming Cognite Functions. It provides a progressive enhancement path from quick exploration to production-ready typed clients.

## Design Philosophy

**Notebook-First**: Optimized for interactive exploration in Jupyter notebooks and Python REPLs, with an easy path to production.

**Three-Tier Workflow**:

1. **Quick Exploration** - Use dynamic client with dicts (no validation, fast iteration)
2. **Interactive Validation** - Use `discover()` to get runtime Pydantic models for validation
3. **Production** - Use `materialize()` to generate fully typed client for production code

## Key Design Decisions

- **Safe Constructor**: No I/O in `__init__` - constructor never fails, connection is lazy
- **Two-Tier Model Approach**:
  - `discover()`: Uses OpenAPI schemas for simplified runtime models (fast exploration)
  - `materialize()`: Uses source extraction for complete models (full validation, production-ready)
- **Runtime Model Loading**: Creates Pydantic models dynamically from JSON schemas on-demand
- **Progressive Enhancement**: Same API patterns from exploration to production
- **Language Agnostic**: OpenAPI enables multi-language client generation for exploration

## Architecture

### Two Approaches for Different Use Cases

The FunctionClient uses two complementary approaches for model handling:

#### 1. OpenAPI Schemas (for `discover()`)

The server automatically generates OpenAPI schemas through FastAPI. The `discover()` method fetches these schemas from the `/openapi.json` endpoint and uses them to:

1. **Display method signatures** - Show available methods, parameters, and return types
2. **Create runtime models** - Dynamically generate simplified Pydantic models from JSON schemas
3. **Enable validation** - Models provide basic structure validation for exploration

**Benefits**:

- Fast and lightweight for interactive exploration
- No server-side changes needed
- Standard format enables multi-language support
- Industry-standard tooling ecosystem

**Limitations**:

- Creates simplified models (structure only, no Field constraints or validators)
- Cannot represent Python-specific features (custom validators, computed fields, etc.)
- Suitable for exploration, not production use

#### 2. Source Code Extraction (for `materialize()`)

The `materialize()` method uses `inspect.getsource()` to extract the actual Pydantic model source code and generates a complete, production-ready client that includes:

1. **Complete model definitions** - Full Pydantic models with all validators and constraints
2. **Custom validation logic** - @validator, @field_validator, and computed fields preserved
3. **Field constraints** - Field(gt=0), Field(max_length=100), etc. included
4. **Type-safe client** - Fully typed methods with proper imports

**Benefits**:

- Users get their actual models with all functionality intact
- No loss of validation logic or constraints
- Production-ready code with full type safety
- Self-contained client (no manual imports needed)

**Trade-offs**:

- Requires models to be defined in source files (not dynamically generated)
- Python-specific approach (though OpenAPI enables other language clients)
- This is acceptable for production use cases where models are properly defined

**Why Both Approaches?**

- **Exploration (discover)**: Fast, simple models from OpenAPI are perfect for notebooks
- **Production (materialize)**: Complete models with all features are essential for deployed code
- Server-side validation handles all constraints anyway, so simplified discovery models are sufficient

### Model Creation from JSON Schema (for `discover()`)

The `discover()` method dynamically creates simplified Pydantic models from OpenAPI JSON schemas:

```python
# JSON Schema from OpenAPI
{
  "Item": {
    "type": "object",
    "properties": {
      "name": {"type": "string"},
      "price": {"type": "number"},
      "description": {"anyOf": [{"type": "string"}, {"type": "null"}]}
    },
    "required": ["name", "price"]
  }
}

# Becomes runtime Pydantic model (simplified - structure only)
class Item(BaseModel):
    name: str
    price: float
    description: str | None = None
```

**Key Implementation Details**:

- **Dependency Resolution**: Topological sort ensures models are created in correct order
- **Type Mapping**: JSON Schema types (string, integer, number, etc.) → Python types
- **Reference Handling**: `$ref` pointers resolved to other models
- **Optional Types**: `anyOf` with null converted to `Type | None`
- **Nested Models**: Full support for models referencing other models

**Note**: These are simplified models for exploration. For production, use `materialize()` to get the complete models with all validators and constraints.

### Lazy Connection

The constructor is I/O-free and never fails. Connection happens lazily when:

- You call `discover()` explicitly
- You call `describe(method_name)`
- You access a method dynamically (via `__getattr__`)
- You call `materialize()`

This design prevents network errors from breaking notebook cell execution.

## API Reference

### Constructor

```python
# For local devserver
client = FunctionClient(base_url="http://localhost:8000")

# For deployed Cognite Functions
from cognite.client import CogniteClient

cognite_client = CogniteClient(...)
client = FunctionClient(
    cognite_client=cognite_client,
    function_external_id="my-function"
)
# Function is retrieved lazily on first discover() or method call
```

**Parameters**:

- `base_url`: Direct URL to devserver (e.g., "<http://localhost:8000>")
- `cognite_client`: CogniteClient instance for deployed functions
- `function_external_id`: External ID of deployed function (retrieved lazily)
- `function_id`: ID of deployed function (retrieved lazily)

**Behavior**: No I/O, safe constructor - never throws network errors. For deployed functions, the function is retrieved lazily on first `discover()` or method call.

### `discover() -> SimpleNamespace`

Single entry point for interactive exploration. Connects to the server, displays available methods, and returns runtime Pydantic models.

```python
models = client.discover()
# ✓ Connected to Asset Management API v1.0.0
#
# Available methods:
#   - get_item(item_id: int, include_tax: bool) -> ItemResponse
#   - create_item(item: Item) -> ItemResponse
#   - process_batch(items: list[Item]) -> BatchResponse
#
# Models: Item, ItemResponse, BatchResponse
#
# Use help(client.method_name) or client.describe('method_name') for details
```

**Returns**: `SimpleNamespace` with Pydantic model classes as attributes

**Usage**:

```python
# Create validated request
item = models.Item(name="Widget", price=99.99)

# Call with validation
result = client.create_item(item=item)

# Parse response (optional)
typed_result = models.ItemResponse.model_validate(result)
```

**Implementation Notes**:

- No caching - each call fetches fresh data (function may have been redeployed)
- Lazy connection - connects on first call
- Displays formatted info to stdout
- Creates simplified models (structure only, server validates constraints)

### `describe(method_name: str) -> None`

Display detailed information about a specific method. Alternative to Python's `help()` with richer formatting.

```python
client.describe("create_item")
# create_item(item: Item) -> ItemResponse
#     Create a new item.
#
#     Parameters:
#       item: Item (required)
#         Field: name (str, required)
#         Field: description (str | None, optional)
#         Field: price (float, required)
#         Field: tax (float | None, optional)
#
#     Returns: ItemResponse
#         Field: id (int)
#         Field: item (Item)
#         Field: total_price (float)
#
#     HTTP: POST /items/
```

**Raises**: `ValueError` if method doesn't exist

### `materialize(output_path: str | Path | None = None) -> str | None`

Generate a fully typed Python client with all models and methods for production use.

```python
# Generate to file
client.materialize("clients/asset_management.py")

# Or print to stdout
print(client.materialize())

# Use the generated client
from clients.asset_management import AssetManagementClient, Item

typed_client = AssetManagementClient("http://localhost:8000")
item = Item(name="Widget", price=99.99)
result = typed_client.create_item(item)
```

**Returns**: Client content as string if `output_path` is None, otherwise None

**Generated Client Features**:

- Self-contained (includes all models)
- Fully type-safe
- No manual imports needed
- Uses httpx for HTTP communication
- Handles Cognite Functions response format

### Dynamic Method Calling

Methods are callable directly without `discover()`:

```python
client = FunctionClient("http://localhost:8000")

# Call with dicts (lazy loads metadata on first call)
result = client.get_item(item_id=42, include_tax=True)

# Or with models after discover()
models = client.discover()
item = models.Item(name="Widget", price=99.99)
result = client.create_item(item=item)
```

**Flexible Input**: Methods accept both dicts and Pydantic models (automatically serialized).

## Usage Patterns

### Pattern 1: Quick Exploration (Tier 1)

Fast iteration with no validation overhead:

```python
from cognite_function_apps import FunctionClient

# Create client (no connection yet)
client = FunctionClient("http://localhost:8000")

# Call methods with dicts
result = client.get_item(item_id=42)
print(result)

result = client.create_item(item={"name": "Widget", "price": 99.99})
print(result)
```

**Use When**: Exploring APIs, quick prototyping, don't need validation

### Pattern 2: Interactive Validation (Tier 2)

Get runtime models for validation during development:

```python
from cognite_function_apps import FunctionClient

# Create client
client = FunctionClient("http://localhost:8000")

# Discover and get models
models = client.discover()
# ✓ Connected to Asset Management API v1.0.0
# Available methods: ...

# Create with validation
item = models.Item(name="Widget", price=99.99)  # Validated!
result = client.create_item(item=item)

# Explore methods interactively
client.describe("create_item")

# Or use Python's help
help(client.create_item)

# Parse responses for typed access
typed_result = models.ItemResponse.model_validate(result)
print(f"Created item with ID: {typed_result.id}")
```

**Use When**: Need validation, exploring complex models, notebook workflows

### Pattern 3: Production (Tier 3)

Generate fully typed client for production code:

```python
# In notebook - generate client once
from cognite_function_apps import FunctionClient

client = FunctionClient("http://localhost:8000")
client.materialize("clients/asset_management.py")

# In production code - use generated client
from clients.asset_management import AssetManagementClient, Item

client = AssetManagementClient("http://localhost:8000")
item = Item(name="Widget", price=99.99)
result = client.create_item(item)  # Fully typed!
```

**Use When**: Production code, need full type safety, IDE autocomplete critical

### Pattern 4: Mixed Workflow

Combine patterns as needed:

```python
from cognite_function_apps import FunctionClient

client = FunctionClient("http://localhost:8000")

# Quick exploration first
client.discover()  # See what's available

# Explore specific method
client.describe("create_item")

# Try with dicts
result = client.create_item(item={"name": "Test", "price": 10.0})

# Get models for complex requests
models = client.discover()
batch = models.BatchRequest(
    items=[
        models.Item(name="Widget", price=99.99),
        models.Item(name="Gadget", price=49.99),
    ]
)
results = client.process_batch(batch=batch)

# Generate typed client when ready for production
client.materialize("clients/asset_management.py")
```

## Implementation Details

### JSON Schema to Python Type Conversion

The client converts JSON Schema types to Python type annotations:

| JSON Schema | Python Type |
|-------------|-------------|
| `{"type": "string"}` | `str` |
| `{"type": "integer"}` | `int` |
| `{"type": "number"}` | `float` |
| `{"type": "boolean"}` | `bool` |
| `{"type": "null"}` | `type(None)` |
| `{"type": "object"}` | `dict[str, Any]` |
| `{"type": "array", "items": T}` | `list[T]` |
| `{"$ref": "#/components/schemas/Item"}` | `Item` (resolved model) |
| `{"anyOf": [{"type": "string"}, {"type": "null"}]}` | `str \| None` |

### Dependency Resolution

Models often reference other models. The client uses topological sorting to create models in the correct order:

```python
# ItemResponse depends on Item
schemas = {
    "Item": {
        "type": "object",
        "properties": {"name": {"type": "string"}}
    },
    "ItemResponse": {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "item": {"$ref": "#/components/schemas/Item"}
        }
    }
}

# Client creates Item first, then ItemResponse
# Uses Kahn's algorithm for topological sort
```

**Handles**:

- Simple dependencies (A → B)
- Complex dependencies (D → B, C; B → A; C → A)
- Detects circular dependencies (raises `RuntimeError`)

### Simplified Models (from `discover()`)

Runtime models created by `discover()` are structural only (no Field constraints):

✓ **Included**:

- Field names and types
- Required vs optional
- Nested models
- Lists and dicts

✗ **Not Included** (server validates anyway):

- Field constraints (gt=0, ge=0, etc.)
- Custom validators
- Serialization customization
- Computed fields

This keeps model creation simple and fast while maintaining validation where it matters (server-side).

For production use with complete models including all validators and constraints, use `materialize()` instead.

### Error Handling

The client provides detailed error messages:

**Model Creation Failure**:

```python
RuntimeError: Failed to create model 'ItemResponse' from schema.
Schema: {...}. Error: ...
```

**Method Not Found**:

```python
ValueError: Method 'invalid_method' not found.
Available methods: ['get_item', 'create_item', ...]
```

**Connection Failure**:

```python
AttributeError: Failed to fetch methods from http://localhost:8000.
Is the server running?
```

## Design Evolution

### Previous Design (Stub Files - Removed)

- Generated `.pyi` stub files for IDE support
- Created disconnect between dynamic client (dicts) and type hints (models)
- Confusing developer experience with inconsistent APIs

### Current Design (Two-Tier Approach)

**For Exploration (`discover()`):**

- Uses OpenAPI/JSON Schema (standard format)
- Runtime model creation from schemas (simplified, structural only)
- Fast and lightweight for interactive notebooks
- Language-agnostic (enables TypeScript, Go, Rust clients)

**For Production (`materialize()`):**

- Uses `inspect.getsource()` to extract actual Pydantic models
- Preserves all validators, Field constraints, and custom logic
- Generates complete, self-contained Python clients
- Production-ready with full type safety

**Why Both?**

- OpenAPI cannot represent Python-specific features (validators, computed fields)
- Users need their complete models with all functionality for production
- Simplified models are sufficient for exploration (server validates anyway)
- Best of both worlds: fast exploration + complete production code

## Future: Multi-Language Support

Since we use OpenAPI for discovery, generating exploration clients for other languages is straightforward:

**TypeScript**:

```bash
openapi-generator-cli generate -i http://localhost:8000/openapi.json -g typescript-axios
```

**Go**:

```bash
oapi-codegen -generate types,client http://localhost:8000/openapi.json
```

**Rust**:

```bash
openapi-generator-cli generate -i http://localhost:8000/openapi.json -g rust
```

**Note**: These would be exploration clients (structure only). For production clients in other languages, custom code generation would be needed to preserve language-specific validation features.

This makes the framework valuable for diverse ecosystems beyond Python!

## Benefits

1. **Notebook-First**: Optimized for interactive exploration and iteration
2. **Safe Constructor**: Never fails on instantiation, lazy connection
3. **Progressive Enhancement**: Easy path from exploration → validation → production
4. **Flexible Input**: Accept both dicts and models seamlessly
5. **Standard Format**: OpenAPI enables tooling ecosystem and multi-language support
6. **Single Source of Truth**: No schema drift - schemas come from the server
7. **Zero Server Changes**: Uses existing OpenAPI endpoint
8. **Runtime Validation**: Get models on-demand for validation
9. **Full Type Safety**: Materialize typed clients for production

## Demo Workflow

```python
# Complete workflow demonstrating all three tiers

from cognite_function_apps import FunctionClient

# Create client (no connection, no I/O)
client = FunctionClient("http://localhost:8000")

# ========== TIER 1: Quick Exploration ==========

# Call with dicts - fast, no validation
result = client.get_item(item_id=42)
print(result)

# ========== TIER 2: Interactive Validation ==========

# Discover what's available
models = client.discover()
# ✓ Connected to Asset Management API v1.0.0
# Available methods:
#   - get_item(item_id: int, include_tax: bool) -> ItemResponse
#   - create_item(item: Item) -> ItemResponse
# Models: Item, ItemResponse

# Explore a specific method
client.describe("create_item")

# Use models for validation
item = models.Item(name="Widget", price=99.99, description="A nice widget")
result = client.create_item(item=item)

# Parse response with validation
typed_result = models.ItemResponse.model_validate(result)
print(f"Created: {typed_result.id} - ${typed_result.total_price}")

# ========== TIER 3: Production ==========

# Generate typed client
client.materialize("clients/asset_management.py")
# ✓ Generated typed client: clients/asset_management.py

# Use in production code (new file/module)
from clients.asset_management import AssetManagementClient, Item

prod_client = AssetManagementClient("http://localhost:8000")
item = Item(name="Production Widget", price=199.99)
result = prod_client.create_item(item)  # Full type safety!
```

## Using Deployed Cognite Functions

The FunctionClient supports connecting to deployed Cognite Functions in addition to local devservers. This enables notebook users to explore and interact with production functions.

### Prerequisites

Deployed function support requires:

1. `cognite-sdk` installed: `pip install cognite-sdk`
2. A CogniteClient with appropriate authentication
3. The deployed function must expose introspection endpoints (`/__client_methods__`, `/openapi.json`)

### Authentication

Users typically have a CogniteClient ready for other purposes in their notebooks:

```python
from cognite.client import ClientConfig, CogniteClient
from cognite.client.credentials import Token, OAuthClientCredentials

# Option 1: Interactive authentication with MSAL
from msal import PublicClientApplication

def authenticate_azure() -> dict[str, str]:
    authority_host_uri = "https://login.microsoftonline.com"
    tenant = "your-tenant-id"
    client_id = "your-client-id"
    authority_uri = authority_host_uri + "/" + tenant
    scopes = ["https://your-cluster.cognitedata.com/.default"]

    app = PublicClientApplication(client_id=client_id, authority=authority_uri)
    # Interactive login - make sure you have http://localhost:port in Redirect URI
    port = 53000
    creds: dict[str, str] = app.acquire_token_interactive(scopes=scopes, port=port)
    return creds

creds = authenticate_azure()

cognite_client = CogniteClient(
    config=ClientConfig(
        client_name="notebook-client",
        project="your-project",
        base_url="https://your-cluster.cognitedata.com",
        credentials=Token(creds["access_token"]),
    )
)

# Option 2: Client credentials (service accounts)
cognite_client = CogniteClient(
    config=ClientConfig(
        client_name="service-client",
        project="your-project",
        base_url="https://your-cluster.cognitedata.com",
        credentials=OAuthClientCredentials(
            token_url=f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
            client_id="your-client-id",
            client_secret="your-client-secret",
            scopes=[f"https://your-cluster.cognitedata.com/.default"],
        ),
    )
)
```

### Connecting to Deployed Functions

Once you have a CogniteClient, retrieve the function and create a FunctionClient:

```python
from cognite_function_apps import FunctionClient

# Create FunctionClient - function retrieved lazily
client = FunctionClient(
    cognite_client=cognite_client,
    function_external_id="my-deployed-function"
)
# or with function ID:
# client = FunctionClient(cognite_client=cognite_client, function_id=5199938255797384)

# Use the same API as local devserver
models = client.discover()
# ✓ Connected to My API v1.0.0
# Available methods: ...

# Call methods
result = client.get_item(item_id=42)
```

### How It Works

For deployed functions, the FunctionClient uses the Cognite SDK's `func.call()` method internally:

1. **Introspection calls**: `/__client_methods__` and `/openapi.json` are routed through `func.call()` with special `__path__` markers
2. **Method calls**: Regular API calls are also routed through `func.call()` with path and parameter data
3. **Response handling**: Same response unwrapping and model parsing as local devserver

This means:

- ✓ No need to manage function URLs or tokens directly
- ✓ Authentication handled by CogniteClient
- ✓ Same developer experience for local and deployed functions
- ✓ Function execution tracked in Cognite Functions API (calls, logs, etc.)

### Complete Workflow Example

```python
# 1. Set up authentication
from cognite.client import ClientConfig, CogniteClient
from cognite.client.credentials import Token
from cognite_function_apps import FunctionClient

cognite_client = CogniteClient(...)  # See authentication examples above

# 2. Create FunctionClient - function retrieved lazily
client = FunctionClient(
    cognite_client=cognite_client,
    function_external_id="asset-enrichment-api"
)

# 4. Discover and explore
models = client.discover()
# ✓ Connected to Asset Enrichment API v2.1.0
# Available methods:
#   - enrich_asset(asset_id: int, include_hierarchy: bool) -> EnrichedAsset
#   - batch_enrich(asset_ids: list[int]) -> list[EnrichedAsset]

# 5. Explore specific method
client.describe("enrich_asset")

# 6. Call with validation
enriched = client.enrich_asset(asset_id=123456, include_hierarchy=True)
print(enriched)

# Or use models for complex requests
batch_result = client.batch_enrich(asset_ids=[123, 456, 789])
for asset in batch_result:
    print(f"{asset.name}: {asset.enrichment_score}")

# 7. Generate typed client for production (optional)
client.materialize("clients/asset_enrichment_client.py")
```

### Limitations and Notes

1. **Function Requirements**: The deployed function must expose introspection endpoints. Functions built with `cognite-function-apps` framework automatically include these.

2. **Execution Time**: Calls to deployed functions go through the Cognite Functions API, which means:
   - Longer latency than direct HTTP calls
   - Calls are queued and executed asynchronously
   - The FunctionClient waits for completion using `call.wait()`

3. **Debugging**: For deployed functions, check logs in the Cognite Functions UI or via:

   ```python
   # If you need to debug a specific call
   call = client.get_item(item_id=42)
   # Access the underlying SDK call object for logs
   ```

4. **Local vs Deployed**: For development, use local devserver for faster iteration. For production workflows in notebooks, use deployed functions with proper authentication.

## Testing

The FunctionClient includes comprehensive tests for:

- I/O-free constructor
- JSON Schema to Python type conversion (primitives, arrays, Optional)
- Dependency graph building
- Topological sorting (simple and complex dependencies)
- Model creation from schemas with validation
- Reference extraction from nested schemas
- Dynamic method calling with both dicts and models
- Deployed function parameter validation

See `tests/test_client_generation.py` for the complete test suite.
