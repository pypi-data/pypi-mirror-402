# Development & Contributing

Guide for developers who want to contribute to the framework.

## Project Structure

```text
cognite-function-apps/
├── src/
│   └── cognite_function_apps/
│       ├── app.py              # Core FunctionApp class and decorators
│       ├── service.py          # Function service layer and app composition
│       ├── convert.py          # Type conversion and argument processing
│       ├── formatting.py       # Formatting utilities
│       ├── models.py           # Pydantic models and type definitions
│       ├── routing.py          # Route matching and management
│       ├── schema.py           # OpenAPI schema generation
│       ├── introspection.py    # Built-in introspection endpoints
│       ├── logger.py           # Enterprise logging utilities
│       ├── tracer.py           # Distributed tracing support
│       ├── mcp.py              # Model Context Protocol integration
│       ├── client.py           # FunctionClient for consuming functions
│       ├── base_client.py      # Base client functionality
│       ├── client_generation.py # Client code generation
│       ├── dependency_registry.py # Dependency injection system
│       └── devserver/          # Local development server
│           ├── __init__.py     # Module exports
│           ├── asgi.py         # ASGI adapter for uvicorn
│           ├── auth.py         # CogniteClient authentication
│           └── swagger.py      # Swagger UI integration
├── docs/                       # Documentation
├── examples/
│   ├── handler.py              # Complete example with MCP integration
│   └── dev.py                  # Local dev server example
├── tests/                      # Comprehensive test suite
├── pyproject.toml              # Project configuration and dependencies
└── README.md                   # Project overview
```

## Development Setup

### Prerequisites

- Python 3.10 or higher
- uv (recommended) or pip

### Clone Repository

```bash
git clone https://github.com/cognitedata/cognite-function-apps.git
cd cognite-function-apps
```

### Install Dependencies

```bash
# Install with uv (recommended)
uv sync

# Or with pip
pip install -e ".[dev]"
```

### Install Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Set up hooks
pre-commit install
```

## Running Tests

The project has a comprehensive test suite with high coverage.

### Run All Tests

```bash
# With uv
uv run pytest

# Without uv
pytest
```

### Run with Verbose Output

```bash
uv run pytest -v
```

### Run Specific Test File

```bash
uv run pytest tests/test_app.py
```

### Run with Coverage

```bash
uv run pytest --cov=cognite_function_apps
```

### Run with Coverage Report

```bash
uv run pytest --cov=cognite_function_apps --cov-report=html
# Open htmlcov/index.html in browser
```

## Code Style

The project follows strict code quality standards.

### Python Code Style

- **Python version**: 3.10+
- **Type annotations**: All code must be type-annotated
- **Type checker**: pyright (strict mode)
- **Imports**: All imports at the top of the file
- **Docstrings**: Google style docstrings

### Type Annotation Guidelines

```python
# **Good** - fully type-annotated
def process_items(
    client: CogniteClient,
    items: list[Item],
    limit: int = 10
) -> dict[str, Any]:
    """Process items with type safety."""
    results: list[dict[str, Any]] = []
    for item in items:
        results.append({"id": item.id})
    return {"results": results}

# **Bad** - no type annotations
def process_items(client, items, limit=10):
    results = []
    for item in items:
        results.append({"id": item.id})
    return {"results": results}
```

### Use Modern Python Types

```python
# **Good** - builtin generic types (Python 3.10+)
def process(items: list[Item]) -> dict[str, int]:
    pass

# **Bad** - importing from typing (unnecessary in 3.10+)
from typing import List, Dict
def process(items: List[Item]) -> Dict[str, int]:
    pass
```

### Avoid `Any` and `type: ignore`

- Using `Any` is a last resort
- All `# type: ignore` must be specific to the error code
- Document why the ignore is necessary

```python
# **Good** - specific ignore with explanation
result = unsafe_operation()  # type: ignore[return-value]  # External library lacks types

# **Bad** - generic ignore
result = unsafe_operation()  # type: ignore
```

### Code Organization

- Keep files under 500 lines
- Prefer smaller, composable functions
- Use extraction and return-early patterns
- Avoid nested functions when possible
- Separate error-handling from domain logic

```python
# **Good** - simple, composable
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

# **Bad** - complex, nested
def save_item(client: CogniteClient, item: Item) -> int:
    def validate():
        if not item.name:
            raise ValueError("Item name required")
        if item.price <= 0:
            raise ValueError("Price must be positive")

    try:
        validate()
        # Save logic mixed with validation
        return item_id
    except Exception:
        # Error handling mixed with logic
        raise
```

## Running Type Checks

```bash
# Run pyright
uv run pyright

# Or with specific path
uv run pyright src/cognite_function_apps/
```

## Running the Development Server

```bash
# With CLI
uv run fun serve examples/

# Or manually
cd examples/
uv run uvicorn dev:app --reload
```

Visit `http://localhost:8000/docs` for interactive API documentation.

## Building Documentation

```bash
# Install documentation dependencies (included in dev dependencies)
uv sync

# Serve documentation locally
mkdocs serve

# Build documentation
mkdocs build
```

Visit `http://127.0.0.1:8000` to view documentation.

## Documentation Guidelines

### When to Update Documentation

Update documentation when you:

- **Add new features** - Document the feature in the appropriate guide
- **Change APIs** - Update API reference and affected guides
- **Fix bugs** - Update examples if they were incorrect
- **Add examples** - Ensure examples are clear and runnable

### Documentation Structure

The documentation is modularized into focused pages:

```text
docs/
├── index.md                    # Landing page with overview and quick start
├── error-handling.md           # Error handling guide
├── logging.md                  # Logging guide
├── type-safety.md              # Type safety and validation
├── dependency-injection.md     # Dependency injection guide
├── async-support.md            # Async/await support
├── introspection.md            # Introspection endpoints
├── mcp.md                      # Model Context Protocol
├── tracing.md                  # Distributed tracing
├── dev-server.md               # Local development server
├── function-client.md          # Function client guide
├── app-composition.md          # App composition (advanced)
├── architecture.md             # Architecture overview
├── api-reference.md            # Hybrid: manual + auto-generated API docs
├── changelog.md                # Changelog
├── release-process.md          # Release process
└── contributing.md             # This file
```

### Cross-Referencing Documentation

Use relative links to reference other documentation pages:

```markdown
**Good** - relative links to other pages:
See [Error Handling](error-handling.md) for details.
See [Logging](logging.md#log-levels) for log levels.

**Good** - links to sections in the same page:
See [Documentation Structure](#documentation-structure) above.

**Bad** - absolute links:
See https://example.com/docs/error-handling.md

**Bad** - broken anchor links:
See [Error Handling](index.md#error-handling)  # This section doesn't exist in index.md
```

### Testing Documentation Changes

Always test documentation changes locally before committing:

```bash
# 1. Build documentation
mkdocs build

# 2. Check for warnings/errors in the output
# Look for:
#   - WARNING: broken links
#   - WARNING: missing anchors
#   - ERROR: build failures

# 3. Serve and manually review
mkdocs serve

# 4. Check the following:
#   - Navigation works correctly
#   - All internal links work
#   - Code examples are correct
#   - Images/diagrams load
#   - Table of contents is accurate
```

### Common Documentation Issues

**Broken Links:**

```bash
# MkDocs will warn about broken links:
INFO - Doc file 'dev-server.md' contains a link 'index.md#missing-section'
```

Fix by updating the link to the correct page:

```markdown
# Before (broken)
See [App Composition](index.md#app-composition)

# After (fixed)
See [App Composition](app-composition.md)
```

**Missing Anchors:**

Headers automatically create anchors. Use lowercase with hyphens:

```markdown
## Error Handling           → #error-handling
## Type Safety and Validation → #type-safety-and-validation
```

### Code Examples in Documentation

Ensure all code examples are:

- **Runnable** - Examples should work as written
- **Complete** - Include all necessary imports
- **Type-safe** - Use proper type annotations
- **Clear** - Include comments explaining non-obvious parts

```python
# **Good** - complete, runnable example
from cognite.client import CogniteClient
from cognite_function_apps import FunctionApp

app = FunctionApp(title="My API", version="1.0.0")

@app.get("/items/{item_id}")
def get_item(client: CogniteClient, item_id: int) -> dict[str, Any]:
    """Retrieve an item by ID"""
    return {"id": item_id, "name": f"Item {item_id}"}

# **Bad** - incomplete, won't run
@app.get("/items/{item_id}")
def get_item(client, item_id):
    return {"id": item_id}
```

### API Reference

The API reference uses a **hybrid approach**:

1. **Manual overview** - Quick reference with common patterns
2. **Auto-generated details** - Generated from source code docstrings using mkdocstrings

When updating public APIs:

```python
# Update docstrings in source code - they appear in API reference automatically
class FunctionApp:
    """Main application class for building Cognite Functions.

    Args:
        title: Application title (appears in OpenAPI schema)
        version: Application version (semantic versioning recommended)

    Example:
        ```python
        app = FunctionApp(title="My API", version="1.0.0")

        @app.get("/items/{item_id}")
        def get_item(client: CogniteClient, item_id: int) -> dict[str, Any]:
            return {"id": item_id}
        ```
    """
```

### Documentation Best Practices

1. **Write for users, not developers** - Explain what and why, not just how
2. **Use clear headers** - Descriptive section headers help navigation
3. **Include examples** - Show, don't just tell
4. **Keep it current** - Update docs when code changes
5. **Test all links** - Broken links frustrate users
6. **Use consistent terminology** - Stick to the framework's terms
7. **Format code properly** - Use syntax highlighting and proper indentation

## Contributing Workflow

### 1. Fork the Repository

Fork the repository on GitHub and clone your fork:

```bash
git clone https://github.com/YOUR-USERNAME/cognite-function-apps.git
cd cognite-function-apps
```

### 2. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

Use descriptive branch names:

- `feature/add-new-decorator`
- `fix/validation-error`
- `docs/improve-quickstart`

### 3. Make Your Changes

- Write clear, type-annotated code
- Add tests for new functionality
- Update documentation if needed
- Follow the code style guidelines

### 4. Run Tests and Checks

```bash
# Run tests
uv run pytest

# Run type checker
uv run pyright

# Run pre-commit hooks
pre-commit run --all-files
```

### 5. Commit Your Changes

Write clear commit messages:

```bash
git add .
git commit -m "Add support for custom decorators

- Implement @app.custom() decorator
- Add tests for custom decorator
- Update documentation with examples"
```

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Pull Request Guidelines

### PR Title

Use clear, descriptive titles:

- `Add support for custom route decorators`
- `Fix validation error for nested models`
- `Improve documentation for async handlers`

### PR Description

Include:

- **What**: What changes were made
- **Why**: Why the changes were necessary
- **How**: How the changes were implemented
- **Testing**: How the changes were tested

### Checklist

Before submitting:

- [ ] Tests pass locally
- [ ] Type checks pass (pyright)
- [ ] Code follows style guidelines
- [ ] Documentation updated if needed
- [ ] Commit messages are clear
- [ ] Pre-commit hooks pass

## Testing Guidelines

### Write Tests for New Features

Every new feature should have tests:

```python
def test_custom_decorator():
    """Test custom decorator functionality."""
    app = FunctionApp("Test", "1.0.0")

    @app.custom("/test")
    def handler(client: CogniteClient) -> dict[str, Any]:
        return {"status": "ok"}

    # Test the handler
    result = call_handler(handler)
    assert result["status"] == "ok"
```

### Test Edge Cases

Consider edge cases:

- Empty inputs
- Invalid types
- Null/None values
- Boundary conditions

### Use Descriptive Test Names

```python
# **Good** - descriptive
def test_validation_fails_for_negative_price():
    pass

# **Bad** - unclear
def test_price():
    pass
```

## Documentation Guidelines

### Write Clear Docstrings

Use Google-style docstrings:

```python
def process_items(
    client: CogniteClient,
    items: list[Item],
    limit: int = 10
) -> dict[str, Any]:
    """
    Process a list of items with specified limit.

    Args:
        client: Authenticated Cognite client
        items: List of items to process
        limit: Maximum number of items to process (default: 10)

    Returns:
        Dictionary with processing results including count and items

    Raises:
        ValueError: If items list is empty
        ProcessingError: If processing fails
    """
```

### Update Documentation

When adding features, update relevant documentation pages:

- User guides for new features
- API reference for new classes/functions
- Examples for common use cases

## Release Process

See [Release Process](release-process.md) for detailed release documentation.

### Summary

1. Create GitHub release with tag `vX.Y.Z`
2. GitHub Actions creates release branch
3. Create PR from release branch to main
4. Review and merge PR
5. GitHub Actions publishes to PyPI

## Getting Help

- **Issues**: Open an issue on GitHub for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: Check the [documentation](index.md) first

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

## Code of Conduct

Be respectful and constructive in all interactions. We're all here to build great software together.

## See Also

- [Architecture](architecture.md) - Framework architecture overview
- [Release Process](release-process.md) - How we release new versions
- [API Reference](api-reference.md) - Complete API documentation
