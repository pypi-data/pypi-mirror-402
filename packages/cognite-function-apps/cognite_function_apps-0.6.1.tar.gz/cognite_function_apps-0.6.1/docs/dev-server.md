# Local Development Server

This guide shows how to run Function Apps locally for development and testing using uvicorn.

## Overview

The dev server allows you to test your Cognite Functions locally before deploying them. It provides:

- **Fast iteration**: Test changes instantly with auto-reload
- **Real CDF access**: Connect to your actual Cognite project
- **Standard HTTP tools**: Test with curl, Postman, or your browser
- **Optimal performance**: Automatically uses async implementation when available

## Quick Start

### 1. Install CLI Support

Install cognite-function-apps with CLI support to get the `fun` command and uvicorn:

```bash
pip install cognite-function-apps[cli]
# or with uv
uv add cognite-function-apps --extra cli
```

This installs both the framework and uvicorn (the development server).

### 2. Set Environment Variables

The dev server needs authentication credentials to connect to Cognite Data Fusion:

```bash
export COGNITE_CLIENT_ID="your-client-id"
export COGNITE_CLIENT_SECRET="your-client-secret"
export COGNITE_TENANT_ID="your-tenant-id"
export COGNITE_PROJECT="your-project"

# Optional (with defaults shown)
export COGNITE_BASE_URL="https://api.cognitedata.com"
export COGNITE_CLIENT_NAME="typed-functions"
```

**Getting credentials:**

- Client ID and Secret: Create an OAuth application in your Microsoft Entra ID (Azure AD)
- Tenant ID: Your Azure AD tenant ID
- Project: Your Cognite project name (e.g., "my-project")

### 3. Run the Development Server

#### Option A: Using the CLI (Recommended)

Simply point the `fun serve` command to your handler directory:

```bash
fun serve .
# or with uv
uv run fun serve .
```

The CLI automatically finds `handler.py`, loads the `handle` object, and starts the server on `http://localhost:8000`.

**Interactive API Documentation:**

The development server includes interactive API documentation:

- **Swagger UI** at <http://localhost:8000/docs> - Test your endpoints directly in the browser

Swagger UI automatically loads your OpenAPI schema from `/__schema__` and provides:

- Full API documentation with request/response schemas
- Interactive "Try it out" functionality
- Parameter validation and examples
- Authentication support

**CLI Options:**

```bash
# Change port
fun serve . --port 3000

# Bind to all interfaces
fun serve . --host 0.0.0.0

# Disable auto-reload
fun serve . --no-reload

# Adjust log level
fun serve . --log-level debug

# Combine options
fun serve . --port 3000 --log-level debug
```

#### Option B: Manual Setup

If you prefer more control, create a `dev.py` file next to your handler:

```python
from cognite_function_apps.devserver import create_asgi_app
from handler import handle

app = create_asgi_app(handle)
```

Then run with uvicorn:

```bash
uv run uvicorn dev:app --reload
# or without uv
uvicorn dev:app --reload
```

The server will start on `http://localhost:8000` by default.

## Interactive API Documentation

The development server includes built-in interactive documentation powered by Swagger UI.

### Accessing Documentation

Once your server is running, open your browser and navigate to:

**Swagger UI** - <http://localhost:8000/docs>

- Interactive interface for testing endpoints
- Click "Try it out" to execute requests directly from the browser
- See request/response examples and schemas
- Test authentication and parameters

### Benefits

- **No manual API documentation needed** - automatically generated from your code
- **Test endpoints interactively** - no need for curl or Postman during development
- **Validate requests** - see parameter requirements and constraints
- **Explore your API** - discover all available endpoints and their schemas

### Example Workflow

1. Start the server: `fun serve examples/`
2. Open <http://localhost:8000/docs> in your browser
3. Explore available endpoints in the Swagger UI
4. Click "Try it out" on any endpoint
5. Fill in parameters and click "Execute"
6. See the response immediately

### How Documentation Works

The documentation endpoints are **automatically provided** by the development server. You don't need to add any special app to your composition:

```python
from cognite_function_apps import (
    FunctionApp,
    create_function_service,
    create_introspection_app,
)

# Create your apps
introspection = create_introspection_app()  # Provides /__schema__
app = FunctionApp("My API", "1.0.0")

# Compose apps - docs are automatically added by the dev server
handle = create_function_service(introspection, app)

# When you run this with create_asgi_app(), the dev server automatically adds:
# - /docs (Swagger UI)
# - /openapi.json (raw schema for the docs tools)
```

The development server:

- Automatically serves `/docs` and `/openapi.json` routes
- Fetches the OpenAPI schema from your app's `/__schema__` introspection endpoint
- Only exists in local development (not deployed to production)
- Requires the `IntrospectionApp` to be included in your composition

This design ensures documentation is **development-only** and doesn't add overhead to your deployed functions.

## Testing Your Endpoints

### Using Interactive Docs (Recommended)

Visit <http://localhost:8000/docs> and use the built-in "Try it out" feature for each endpoint.

### Using curl

### GET Request

```bash
curl http://localhost:8000/items/123?include_tax=true
```

### POST Request

```bash
curl -X POST http://localhost:8000/items/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Widget",
    "price": 29.99,
    "tax": 2.50
  }'
```

### Using Python requests

```python
import requests

# GET request
response = requests.get(
    "http://localhost:8000/items/123",
    params={"include_tax": True}
)
print(response.json())

# POST request
response = requests.post(
    "http://localhost:8000/items/",
    json={
        "name": "Widget",
        "price": 29.99,
        "tax": 2.50
    }
)
print(response.json())
```

## Advanced Configuration

### Using the CLI

```bash
# Custom port and host
fun serve . --host 0.0.0.0 --port 3000

# Adjust log level
fun serve . --log-level debug

# Disable auto-reload for production-like testing
fun serve . --no-reload
```

### Using uvicorn directly

If you're using the manual setup with `dev.py`:

```bash
# Custom port and host
uvicorn dev:app --reload --host 0.0.0.0 --port 3000

# Log level
uvicorn dev:app --reload --log-level debug

# Multiple workers (production-like, disables --reload)
uvicorn dev:app --workers 4
```

## Architecture

### How It Works

The dev server bridges between ASGI (used by uvicorn) and the Cognite Functions interface:

1. **ASGI Request** → HTTP request from uvicorn
2. **Parse** → Convert to Cognite handle format (`{path, method, body}`)
3. **Execute** → Call your function handlers with a real CogniteClient
4. **Format** → Convert response back to HTTP
5. **ASGI Response** → Send back to uvicorn

### Performance Optimization

The dev server automatically detects and uses the internal async implementation for optimal performance:

- **With FunctionApp**: Uses `_async_handle` directly (zero overhead)
- **With generic functions**: Falls back to thread pool execution
- **Both sync and async endpoints**: Work seamlessly

This means your async endpoints run natively without blocking, and sync endpoints run on a thread pool to avoid blocking the event loop.

## Troubleshooting

### Missing Environment Variables

**Error:**

```text
ValueError: Missing required environment variables: COGNITE_CLIENT_ID, COGNITE_CLIENT_SECRET
```

**Solution:** Make sure all required environment variables are set. Check with:

```bash
echo $COGNITE_CLIENT_ID
echo $COGNITE_CLIENT_SECRET
echo $COGNITE_TENANT_ID
echo $COGNITE_PROJECT
```

### Authentication Failed

**Error:**

```text
Failed to create Cognite client: ...
```

**Solution:**

- Verify your Client ID and Secret are correct
- Ensure your OAuth app has the required scopes (`{base_url}/.default`)
- Check that your tenant ID is correct
- Verify your Entra ID app registration is properly configured

### Port Already in Use

**Error:**

```text
Error: [Errno 48] Address already in use
```

**Solution:** Use a different port:

```bash
uvicorn dev:app --reload --port 3000
```

### Module Not Found

**Error:**

```text
ModuleNotFoundError: No module named 'handler'
```

**Solution (CLI):**

- Make sure you're pointing to the directory containing `handler.py`
- Use absolute or relative paths: `fun serve /path/to/handler-dir` or `fun serve ./my-function`

**Solution (Manual Setup):**

- Make sure you're running from the correct directory
- Check that your handler file is named correctly
- Verify the import path in your `dev.py` matches your project structure

### Connection Refused

**Error:**

```text
Connection refused when calling CDF
```

**Solution:**

- Check your `COGNITE_BASE_URL` is correct
- Verify you have network access to Cognite
- Try accessing the base URL in your browser to check connectivity

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `COGNITE_CLIENT_ID` | **Yes** | - | OAuth client ID from Entra ID |
| `COGNITE_CLIENT_SECRET` | **Yes** | - | OAuth client secret from Entra ID |
| `COGNITE_TENANT_ID` | **Yes** | - | Microsoft Entra ID tenant ID |
| `COGNITE_PROJECT` | **Yes** | - | Cognite project name |
| `COGNITE_BASE_URL` | No | `https://api.cognitedata.com` | Base URL for Cognite API |
| `COGNITE_CLIENT_NAME` | No | `typed-functions` | Client name for tracking |

## Best Practices

### 1. Use .env Files

Create a `.env` file in your project (add to `.gitignore`!):

```bash
COGNITE_CLIENT_ID=your-client-id
COGNITE_CLIENT_SECRET=your-client-secret
COGNITE_TENANT_ID=your-tenant-id
COGNITE_PROJECT=your-project
```

The CLI and devserver will automatically use these environment variables.

If using manual setup with `dev.py`, you can use `python-dotenv`:

```python
from dotenv import load_dotenv
load_dotenv()

from cognite_function_apps.devserver import create_asgi_app
from handler import handle

app = create_asgi_app(handle)
```

### 2. Separate Dev and Production

Keep your development setup separate from your production handler:

**With CLI (Recommended):**

```text
my-function/
├── handler.py          # Production handler (deployed)
├── .env                # Local credentials (not committed, not deployed)
└── .gitignore          # Ignore .env
```

Then run: `fun serve my-function/`

**With Manual Setup:**

```text
my-project/
├── handler.py          # Production handler
├── dev.py              # Dev server (not deployed)
├── .env                # Local credentials (not committed, not deployed)
└── .gitignore          # Ignore .env and dev.py
```

### 3. Use Auto-Reload During Development

The CLI enables auto-reload by default. For manual setup, always use `--reload` during development:

```bash
# CLI (auto-reload enabled by default)
fun serve .

# Manual setup
uvicorn dev:app --reload
```

### 4. Test with Real Data

Since you're connecting to real CDF, you can test with actual data:

- Query real assets, time series, etc.
- Verify your data transformations
- Test edge cases with production data

### 5. Log Everything

Use the injected logger in your handlers:

```python
@app.get("/items/{item_id}")
def get_item(client: CogniteClient, logger: logging.Logger, item_id: int):
    logger.info(f"Fetching item {item_id}")
    # Your logic here
    logger.debug(f"Item details: {details}")
    return result
```

Then run with debug logging:

```bash
uvicorn dev:app --reload --log-level debug
```

## Next Steps

- Learn about [app composition](app-composition.md) for modular functions
- Explore [MCP integration](mcp.md) for AI tool integration
- Review [type safety](type-safety.md) best practices

## Need Help?

If you encounter issues not covered here, please:

1. Check the main [documentation home](index.md) for general documentation
2. Open an issue on GitHub with details about your problem
