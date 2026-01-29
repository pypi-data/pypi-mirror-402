# Agent Instructions

This file provides guidance to AI agents (including Claude Code) when working with code in this repository.

## Project Overview

Enterprise-grade framework for building type-safe, composable Cognite Functions with automatic validation, built-in introspection, and AI integration. The framework provides FastAPI-style decorator syntax for Cognite Functions, making complex APIs maintainable with automatic type conversion, error handling, and OpenAPI schema generation.

**Critical**: This framework is used by customers to build Cognite Functions. Once deployed, we cannot update customer code - they must redeploy. Therefore:

- **Backward compatibility is paramount** - breaking changes require major version bump
- **Code must be robust** - thorough error handling, comprehensive validation
- **APIs must be simple** - favor clarity over cleverness
- **Documentation must be complete** - customers rely on docs for self-service

## Commit Message Guidelines

**IMPORTANT:** This project uses [Conventional Commits](https://www.conventionalcommits.org/) to enable automated releases via [release-please](https://github.com/googleapis/release-please).

### Commit Format

All commits must follow this format:

```text
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Commit Types

- **feat:** New feature (triggers minor version bump: 0.3.2 → 0.4.0)
- **fix:** Bug fix (triggers patch version bump: 0.3.2 → 0.3.3)
- **feat!:** or **BREAKING CHANGE:** Breaking change (triggers major version bump: 0.3.2 → 1.0.0)
- **docs:** Documentation changes (appears in changelog)
- **refactor:** Code refactoring (appears in changelog)
- **perf:** Performance improvements (appears in changelog)
- **test:** Test changes (hidden from changelog)
- **build:** Build system changes (hidden from changelog)
- **ci:** CI/CD changes (hidden from changelog)
- **chore:** Other changes (hidden from changelog)
- **revert:** Revert a previous commit (appears in changelog)

### Examples

```bash
# Feature (minor bump)
git commit -m "feat: add batch processing support for assets"

# Bug fix (patch bump)
git commit -m "fix: handle None values in type conversion"

# Breaking change (major bump)
git commit -m "feat!: change DependencyRegistry API

BREAKING CHANGE: register() now requires explicit target_type parameter"

# Documentation
git commit -m "docs: update API reference for FunctionApp"

# Refactoring
git commit -m "refactor: simplify route matching logic"

# Revert
git commit -m "revert: revert breaking changes to DependencyRegistry"
```

### Why This Matters

- release-please analyzes commit messages to determine version bumps
- Commit type determines semantic version increment
- Commit messages become the changelog
- Incorrect commit types will cause wrong version bumps or missing releases

**When making commits for this project, always use conventional commit format.**

## Environment

- This repository uses `uv` package manager
- To run Python: `uv run python`
- To run tests: `uv run pytest`
- To run type checker: `uv run pyright`
- To run pre-commit hooks: `pre-commit run --all-files`

## Development Commands

### Environment Setup

```bash
# Install dependencies
uv sync

# Install with dev dependencies
uv sync --dev

# Install pre-commit hooks
pre-commit install
```

### Testing

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_app.py

# Run with coverage
uv run pytest --cov=cognite_function_apps

# Run with coverage report (generates htmlcov/index.html)
uv run pytest --cov=cognite_function_apps --cov-report=html
```

### Type Checking

```bash
# Run pyright type checker (strict mode)
uv run pyright

# Check specific path
uv run pyright src/cognite_function_apps/
```

### Development Server

```bash
# Serve example functions locally with interactive API docs
uv run fun serve examples/

# Or manually
cd examples/
uv run uvicorn dev:app --reload
```

Visit `http://localhost:8000/docs` for interactive API documentation.

### Documentation

```bash
# Serve documentation locally
mkdocs serve

# Build documentation
mkdocs build
```

Visit `http://127.0.0.1:8000` to view documentation.

## Python Code Standards

### Type Annotations (Critical)

- **All code MUST be type-annotated** - No exceptions, pyright strict mode enforced
- Use builtin generic types: `list[T]`, `dict[K, V]`, `tuple[T, ...]` (not `List`, `Dict`, `Tuple` from typing)
- Use `Sequence[T]` instead of `list[T]` for immutable parameters (enables covariance)
- Use `Mapping[K, V]` instead of `dict[K, V]` for immutable parameters
- Annotate variables assigned empty lists/dicts: `items: list[Item] = []`
- Using `Any` or `# type: ignore` is a last resort
- All type ignores must be specific: `# type: ignore[return-value]` not `# type: ignore`
- Use `ParamSpec` for decorators to preserve function signatures

### Import Organization

- All imports at the top of the file
- No conditional imports or imports inside functions

### Code Structure Principles

- **File size limit**: Keep files under 500 lines
- **Function composition**: Prefer smaller, composable functions over large nested ones
- **OPEN/CLOSED principle**: Design for extension without modification
- **Avoid nested functions**: Use extraction and return-early patterns instead
- **Separation of concerns**: Don't mix error-handling with domain logic in the same function
- **No entropy dumps**: Avoid modules with unrelated utilities
- **Avoid premature abstractions**: Create abstractions when patterns emerge, not before

### Documentation

- Use Google-style docstrings
- Concise and professional language
- Include Args, Returns, Raises sections for public APIs

### Code Examples

```python
# GOOD - fully type-annotated, composable
def validate_item(item: Item) -> None:
    """Validate item data."""
    if not item.name:
        raise ValueError("Item name required")
    if item.price <= 0:
        raise ValueError("Price must be positive")

def save_item(client: CogniteClient, item: Item) -> int:
    """Save item to database."""
    validate_item(item)
    # Save logic here
    return item_id

# BAD - no types, nested, mixed concerns
def save_item(client, item):
    def validate():
        if not item.name:
            raise ValueError("Item name required")
    try:
        validate()
        # Save logic
    except Exception:
        raise
```

## Code Architecture

### Core Modules

The framework is organized into focused modules in `src/cognite_function_apps/`:

- **app.py** - Core `FunctionApp` class with FastAPI-style decorators (`@app.get()`, `@app.post()`, etc.) for route registration
- **service.py** - Function service layer implementing app composition via `create_function_service()`, enables left-to-right route matching across multiple apps
- **routing.py** - Route matching engine with path pattern support (e.g., `/items/{item_id}`), HTTP method matching, and query string parsing
- **models.py** - Pydantic models for core types (`Route`, `ErrorResponse`, `SuccessResponse`, `FunctionCallInfo`)
- **convert.py** - Recursive type conversion and validation system for nested structures, handles automatic coercion (str → int, bool, etc.)
- **schema.py** - OpenAPI 3.0 schema generator, converts routes and Pydantic models to OpenAPI spec with component schemas
- **dependency_registry.py** - Dependency injection system with type-based and name-based resolution, supports provider functions and custom dependencies
- **introspection.py** - Built-in endpoints for debugging: `/__schema__` (OpenAPI), `/__routes__` (route list), `/__health__`, `/__ping__`
- **logger.py** - Enterprise logging with isolated logger creation, stdout-only output, cloud provider compatible
- **tracer.py** - OpenTelemetry-based distributed tracing with span management and OTLP export
- **mcp.py** - Model Context Protocol integration exposing functions as AI tools via `/__mcp_tools__` and `/__mcp_call__/*`
- **client.py** - `FunctionClient` for consuming deployed functions with dynamic method discovery and type-safe calls
- **client_generation.py** - Runtime Pydantic model generation for client code
- **devserver/** - Local development server with ASGI adapter, CogniteClient authentication, and Swagger UI integration

### App Composition System

The framework uses a composition pattern where multiple `FunctionApp` instances can be combined:

1. **Left-to-right routing** - Apps are tried in order from left to right for route matching
2. **Last-app metadata** - The final app in the composition provides title and version for the service
3. **Registry sharing** - All composed apps share a single `DependencyRegistry`, enabling cross-app dependency injection
4. **Composition hook** - Apps can override `on_compose(next_app, shared_registry)` to access downstream apps and register dependencies

Example composition:

```python
handle = create_function_service(tracing_app, mcp_app, introspection_app, main_app)
# Routes: tracing → mcp → introspection → main
# Metadata: from main_app
# Registry: shared across all apps
```

### Request Processing Pipeline

1. Request arrives with `{path, method, body}`
2. Try each composed app in left-to-right order
3. Match route pattern and extract path parameters
4. Parse query parameters from URL
5. Create dependency context (`client`, `secrets`, `function_call_info`)
6. Resolve dependencies from registry (injected based on type annotations)
7. Validate and coerce parameters using recursive type conversion
8. Execute handler (async handlers awaited, sync handlers run on thread pool)
9. Format response as `SuccessResponse` or `ErrorResponse`
10. Return structured JSON response

### Dependency Injection

The framework uses type annotations for automatic dependency injection:

- **Built-in dependencies**: `CogniteClient`, `dict` (secrets), `FunctionCallInfo`
- **Custom dependencies**: Register via `registry.register(provider, target_type, param_name)`
- **Context-aware**: Providers receive execution context with client, secrets, and function call info
- **Shared registry**: All composed apps share dependencies for cross-app functionality

## Testing Guidelines

### Test Organization

- Test files in `tests/` directory
- Follow naming: `test_*.py` for files, `test_*` for functions
- Use descriptive test names: `test_validation_fails_for_negative_price()` not `test_price()`

### Coverage Expectations

- The project maintains high test coverage
- All new features require tests
- Test edge cases: empty inputs, invalid types, None values, boundary conditions

### Test Structure

```python
def test_custom_decorator():
    """Test custom decorator functionality."""
    app = FunctionApp("Test", "1.0.0")

    @app.custom("/test")
    def handler(client: CogniteClient) -> dict:
        return {"status": "ok"}

    result = call_handler(handler)
    assert result["status"] == "ok"
```

## Documentation Structure

Documentation lives in `docs/` and uses MkDocs Material theme:

- **index.md** - Landing page with quick start
- **architecture.md** - Framework design and internals (read this to understand system design)
- **app-composition.md** - Advanced: composing multiple apps together
- **type-safety.md** - Type conversion and validation details
- **dependency-injection.md** - Dependency system guide
- **async-support.md** - Async/await handler support
- **introspection.md** - Built-in debugging endpoints
- **mcp.md** - Model Context Protocol for AI integration
- **tracing.md** - OpenTelemetry distributed tracing
- **error-handling.md** - Structured error responses
- **logging.md** - Enterprise logging utilities
- **dev-server.md** - Local development server setup
- **function-client.md** - Client for consuming functions
- **contributing.md** - Development setup and guidelines
- **api-reference.md** - Hybrid manual + auto-generated API docs

### Documentation Updates

When changing code, update relevant docs:

- New features → corresponding guide
- API changes → api-reference.md and affected guides
- Always test docs locally with `mkdocs serve` before committing
- Use relative links: `[Error Handling](error-handling.md)` not absolute URLs

## Built-in Apps and Features

### IntrospectionApp

Provides debugging endpoints (always recommended for development):

- `/__schema__` - Unified OpenAPI schema across all composed apps
- `/__routes__` - List of all registered routes
- `/__health__` - Health check endpoint
- `/__ping__` - Connectivity check

### MCPApp

Exposes functions as AI tools via Model Context Protocol:

- `/__mcp_tools__` - List available tools with JSON schemas
- `/__mcp_call__/<tool_name>` - Execute specific tool

### TracingApp

Adds OpenTelemetry distributed tracing:

- Registers `FunctionTracer` dependency for all handlers
- Automatic span creation and context propagation
- OTLP export support

## Common Patterns

### Creating a Basic Function

```python
from cognite_function_apps import FunctionApp, create_function_service
from cognite.client import CogniteClient
from pydantic import BaseModel

app = FunctionApp(title="My API", version="1.0.0")

class Item(BaseModel):
    name: str
    price: float

@app.get("/items/{item_id}")
def get_item(client: CogniteClient, item_id: int) -> dict:
    """Retrieve an item by ID"""
    return {"id": item_id, "name": f"Item {item_id}"}

@app.post("/items/")
def create_item(client: CogniteClient, item: Item) -> dict:
    """Create a new item"""
    # item is automatically validated and instantiated from request body
    return {"id": 123, "item": item}

handle = create_function_service(app)
```

### Full-Featured Service with Composition

```python
from cognite_function_apps import (
    FunctionApp,
    create_function_service,
    create_tracing_app,
)
from cognite_function_apps.introspection import create_introspection_app
from cognite_function_apps.mcp import create_mcp_app

# Create system apps
tracing = create_tracing_app()
mcp = create_mcp_app()
introspection = create_introspection_app()

# Create business app
app = FunctionApp("Asset Management", "1.0.0")

@app.get("/assets/{asset_id}")
def get_asset(client: CogniteClient, tracer: FunctionTracer, asset_id: int) -> dict:
    """Get asset by ID with tracing"""
    with tracer.span("fetch_asset"):
        # Business logic
        return {"id": asset_id}

# Compose: tracing → AI tools → debugging → business logic
handle = create_function_service(tracing, mcp, introspection, app)
```

### Custom Dependency Registration

```python
from cognite_function_apps import create_default_registry
import redis

registry = create_default_registry()

# Register custom dependency
registry.register(
    provider=lambda ctx: redis.Redis.from_url(ctx["secrets"]["REDIS_URL"]),
    target_type=redis.Redis,
    param_name="cache",
    description="Redis cache connection"
)

# Use in handler
@app.get("/items/{item_id}")
def get_item(client: CogniteClient, cache: redis.Redis, item_id: int) -> dict:
    # cache is automatically injected
    cached = cache.get(f"item:{item_id}")
    return {"id": item_id, "cached": cached is not None}

handle = create_function_service(app, registry=registry)
```
