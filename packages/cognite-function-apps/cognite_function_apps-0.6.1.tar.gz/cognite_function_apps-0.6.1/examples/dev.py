"""Development server for local testing.

This example shows how to run the Function Apps handler locally
using uvicorn for development and testing.

Usage:
    1. Set required environment variables:
       export COGNITE_CLIENT_ID="your-client-id"
       export COGNITE_CLIENT_SECRET="your-client-secret"
       export COGNITE_TENANT_ID="your-tenant-id"
       export COGNITE_PROJECT="your-project"

    2. Run with uvicorn:
       uv run uvicorn examples.dev:app --reload

    3. View interactive API documentation:
       - Swagger UI: http://localhost:8000/docs

    4. Test the endpoints:
       curl http://localhost:8000/items/123?include_tax=true
       curl -X POST http://localhost:8000/items/ \
         -H "Content-Type: application/json" \
         -d '{"name": "Widget", "price": 29.99, "tax": 2.50}'

The dev server will automatically reload when you make changes to your handler code.
"""

from cognite_function_apps.devserver import create_asgi_app
from examples.handler import handle

# Create the ASGI app from the Cognite Functions handle
app = create_asgi_app(handle)
