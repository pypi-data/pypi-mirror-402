"""Example usage of the Cognite Function Apps framework with composed apps.

This example demonstrates:
- Sync route handlers (get_item, create_item)
- Async route handlers (process_batch)
- Logger dependency injection
- Tracer dependency injection with OTLP export
- TracingApp decorator for automatic root spans with OpenTelemetry
- MCP tool integration
- Introspection endpoints
- Composable app architecture

Note: Interactive documentation (/docs, /redoc) is automatically available
when using the development server (devserver.create_asgi_app).

To test with Honeycomb tracing:
1. Go to https://ui.honeycomb.io/ -> Manage Data -> Send Data to find you API key.
2. `export TRACING_API_KEY=your-api-key`

To test with Jaeger tracing locally:
1. Start Jaeger: docker run -d -p 4317:4317 -p 16686:16686 jaegertracing/all-in-one:latest
2. Update tracing config below to use Jaeger

Then start the app and observe:
3. Run: `fun serve examples/handler.py`
4. Send a request to the endpoint: `curl -s http://localhost:8000/__routes__ | jq`
5. View traces at https://ui.honeycomb.io/ or http://localhost:16686
"""

import asyncio
import logging
from typing import Any

from cognite.client import CogniteClient
from pydantic import BaseModel, Field

from cognite_function_apps import (
    FunctionApp,
    FunctionService,
    FunctionTracer,
    create_function_service,
    create_introspection_app,
    create_mcp_app,
    create_tracing_app,
)

# Create individual apps using the composed architecture
app = FunctionApp(title="Asset Management API", version="1.0.0")
mcp = create_mcp_app("asset-management-tools")

# Tracing with backend presets:
# - Production: backend="honeycomb" or "lightstep" (requires tracing-api-key secret)
tracing = create_tracing_app(backend="honeycomb")  # Free tier available at https://ui.honeycomb.io/

# - Local dev: Use TracingConfig for Jaeger (no auth)
# from cognite_function_apps import TracingConfig
# tracing = create_tracing_app(backend=TracingConfig(endpoint="http://localhost:4317"))

introspection = create_introspection_app()


class Item(BaseModel):
    name: str
    description: str | None = Field(default=None)
    price: float = Field(gt=0)
    tax: float | None = Field(default=None, ge=0)


class ItemResponse(BaseModel):
    id: int
    item: Item
    total_price: float


@app.get("/items/{item_id}")
@mcp.tool(description="Retrieve an item by ID with optional tax calculation")
@tracing.trace()  # Automatic root span sent to OpenTelemetry collector
def get_item(
    client: CogniteClient, logger: logging.Logger, tracer: FunctionTracer, item_id: int, include_tax: bool = False
) -> ItemResponse:
    """Retrieve an item by ID.

    Root span automatically created by @tracing.trace() decorator and exported
    to the configured OTLP endpoint. Child spans are created for business logic.
    All spans include cognite.call_id for filtering/organization in the backend.
    """
    logger.info(f"Fetching item {item_id} (include_tax={include_tax})")

    logger.info("Creating fetch_item_data span...")
    with tracer.span("fetch_item_data"):
        logger.info("  Inside fetch_item_data span")
        item = Item(name=f"Item {item_id}", price=100.0, tax=10.0 if include_tax else None)
    logger.info("fetch_item_data span completed")

    logger.info("Creating calculate_total span...")
    with tracer.span("calculate_total"):
        logger.info("  Inside calculate_total span")
        total = item.price + (item.tax or 0)
    logger.info("calculate_total span completed")

    logger.debug(f"Item details: {item.model_dump()}")
    return ItemResponse(id=item_id, item=item, total_price=total)


@app.post("/items/")
@mcp.tool(description="Create a new item with validation and pricing calculation")
@tracing.trace()
def create_item(client: CogniteClient, logger: logging.Logger, tracer: FunctionTracer, item: Item) -> ItemResponse:
    """Create a new item."""
    logger.info(f"Creating new item: {item.name}")

    with tracer.span("validate_item"):
        # Validation logic
        pass

    with tracer.span("create_item"):
        new_id = 12345
        total = item.price + (item.tax or 0)

    logger.info(f"Item created with ID {new_id}")
    return ItemResponse(id=new_id, item=item, total_price=total)


@app.post("/process/batch")
@mcp.tool(description="Process multiple items concurrently with async operations")
@tracing.trace()
async def process_batch(
    client: CogniteClient, logger: logging.Logger, tracer: FunctionTracer, items: list[Item]
) -> dict[str, Any]:
    """Process multiple items in batch using async for concurrent operations.

    This demonstrates how async handlers can process items concurrently,
    which is useful when each item requires I/O operations like API calls.
    """
    logger.info(f"Starting batch processing of {len(items)} items")

    async def process_item(item: Item) -> dict[str, Any]:
        """Process a single item asynchronously."""
        with tracer.span("process_item"):
            # Simulate async processing (e.g., API call, database query)
            await asyncio.sleep(0.001)
            total = item.price + (item.tax or 0)
            logger.debug(f"Processed item: {item.name} -> total: {total}")
            return {"name": item.name, "total": total}

    # Process all items concurrently
    results = await asyncio.gather(*[process_item(item) for item in items])

    total_value = sum(result["total"] for result in results)
    logger.info(f"Batch processing complete. Total value: {total_value}")
    return {"processed_count": len(items), "total_value": total_value, "items": results}


# Routes without @tracing.trace() don't get automatic root spans
@app.get("/internal/health")
def health_check(client: CogniteClient) -> dict[str, str]:
    """Internal health check endpoint - no tracing decorator, no root span."""
    return {"status": "healthy", "service": "asset-management"}


# Compose apps with default dependencies (most common usage)
handle: FunctionService = create_function_service(tracing, mcp, introspection, app)


__all__ = ["handle"]
