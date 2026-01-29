# Async Support

The framework supports both synchronous and asynchronous route handlers, enabling efficient concurrent code when needed.

## Why Use Async?

Async handlers are particularly useful for:

- **Concurrent API calls** - Fetch data from multiple sources simultaneously
- **I/O-bound operations** - Database queries, file operations, network requests
- **Parallel processing** - Process multiple items concurrently
- **External service integration** - Call multiple external APIs in parallel

## Basic Async Usage

Simply declare your route handler as `async def` instead of `def`:

```python
import asyncio
from cognite_function_apps import FunctionApp

app = FunctionApp(title="Async API", version="1.0.0")

# Synchronous handler (traditional)
@app.get("/items/{item_id}")
def get_item(client: CogniteClient, item_id: int) -> ItemResponse:
    """Synchronous data retrieval"""
    # Your sync logic here
    return ItemResponse(...)

# Asynchronous handler (new!)
@app.get("/items/{item_id}/async")
async def get_item_async(client: CogniteClient, item_id: int) -> ItemResponse:
    """Asynchronous data retrieval with concurrent operations"""
    # Use await for async operations
    result = await fetch_data_async(item_id)
    return ItemResponse(...)
```

## Concurrent Operations Example

The real power of async comes from running multiple operations concurrently:

```python
@app.get("/items/{item_id}/details")
async def get_item_with_details(client: CogniteClient, item_id: int) -> dict[str, Any]:
    """Fetch item data from multiple sources concurrently"""

    # Define async operations
    async def fetch_item_info():
        # Simulate API call
        await asyncio.sleep(0.1)
        return {"name": f"Item {item_id}", "price": 100.0}

    async def fetch_inventory():
        # Simulate another API call
        await asyncio.sleep(0.1)
        return {"stock": 50, "warehouse": "A"}

    async def fetch_reviews():
        # Simulate yet another API call
        await asyncio.sleep(0.1)
        return {"rating": 4.5, "count": 120}

    # Execute all operations concurrently (not sequentially!)
    item_info, inventory, reviews = await asyncio.gather(
        fetch_item_info(),
        fetch_inventory(),
        fetch_reviews()
    )

    return {
        "item": item_info,
        "inventory": inventory,
        "reviews": reviews
    }
```

In this example, all three operations run concurrently, completing in ~0.1 seconds instead of ~0.3 seconds if run sequentially.

## Batch Processing with Async

Process multiple items concurrently for better performance:

```python
@app.post("/process/batch/async")
async def process_batch_async(client: CogniteClient, items: list[Item]) -> dict[str, Any]:
    """Process multiple items concurrently"""

    async def process_item(item: Item) -> dict[str, Any]:
        """Process a single item asynchronously"""
        # Simulate async processing (e.g., API call, database query)
        await asyncio.sleep(0.01)
        total = item.price + (item.tax or 0)
        return {"name": item.name, "total": total}

    # Process all items concurrently
    results = await asyncio.gather(*[process_item(item) for item in items])

    total_value = sum(result["total"] for result in results)
    return {
        "processed_count": len(items),
        "total_value": total_value,
        "items": results
    }
```

## How It Works

The framework automatically detects whether your handler is sync or async:

- **Async handlers** (`async def`) are awaited directly for native async execution
- **Sync handlers** (`def`) are run on a thread pool to avoid blocking the event loop
- **MCP tools** support both sync and async handlers seamlessly
- **App composition** works with any mix of sync and async handlers

```python
# Framework detects and handles both
@app.get("/sync-endpoint")
def sync_handler(client: CogniteClient) -> dict[str, Any]:
    # Runs on thread pool
    return {"type": "sync"}

@app.get("/async-endpoint")
async def async_handler(client: CogniteClient) -> dict[str, Any]:
    # Awaited directly
    return {"type": "async"}
```

## Performance Considerations

### When async helps

- Multiple I/O operations that can run in parallel
- External API calls that can be concurrent
- Database queries that can be batched

**Example - Performance Gain:**

```python
# BAD: Synchronous - takes ~3 seconds total
@app.get("/slow-sync")
def slow_sync(client: CogniteClient) -> dict[str, Any]:
    data1 = fetch_api_1()  # 1 second
    data2 = fetch_api_2()  # 1 second
    data3 = fetch_api_3()  # 1 second
    return {"data": [data1, data2, data3]}

# **Yes** Asynchronous - takes ~1 second total
@app.get("/fast-async")
async def fast_async(client: CogniteClient) -> dict[str, Any]:
    # All three run concurrently!
    data1, data2, data3 = await asyncio.gather(
        fetch_api_1_async(),
        fetch_api_2_async(),
        fetch_api_3_async()
    )
    return {"data": [data1, data2, data3]}
```

### When sync is fine

- Simple CPU-bound calculations
- Single database/API call
- Straightforward data transformations

**Note:** Since Cognite Functions don't handle concurrent requests within the same process (each function call gets its own compute instance), async is primarily beneficial for **concurrent operations within a single request**, not for handling multiple requests simultaneously.

## Mixing Sync and Async

You can freely mix sync and async handlers in the same app:

```python
app = FunctionApp(title="Mixed API", version="1.0.0")

@app.get("/simple")
def simple_endpoint(client: CogniteClient) -> dict[str, Any]:
    """Simple sync endpoint"""
    return {"status": "ok"}

@app.get("/complex")
async def complex_endpoint(client: CogniteClient) -> dict[str, Any]:
    """Complex async endpoint with concurrent operations"""
    results = await asyncio.gather(
        fetch_data_1(),
        fetch_data_2(),
        fetch_data_3()
    )
    return {"results": results}

# Both work seamlessly in the same app!
handle = create_function_service(app)
```

## Async with Dependencies

Dependency injection works seamlessly with async handlers:

```python
import logging

@app.get("/items/{item_id}")
async def get_item_async(
    client: CogniteClient,
    logger: logging.Logger,
    item_id: int
) -> dict[str, Any]:
    """Async handler with dependency injection"""
    logger.info(f"Fetching item {item_id} asynchronously")

    # Concurrent operations
    item_data, metadata = await asyncio.gather(
        fetch_item_data(item_id),
        fetch_item_metadata(item_id)
    )

    logger.info(f"Successfully fetched item {item_id}")
    return {"item": item_data, "metadata": metadata}
```

## Async with Tracing

Tracing works perfectly with async handlers:

```python
from cognite_function_apps import FunctionTracer

@app.get("/items/{item_id}")
async def get_item_async(
    client: CogniteClient,
    tracer: FunctionTracer,
    item_id: int
) -> dict[str, Any]:
    """Async handler with distributed tracing"""

    async def fetch_details():
        with tracer.span("fetch_details"):
            await asyncio.sleep(0.1)
            return {"extra": "data"}

    async def fetch_reviews():
        with tracer.span("fetch_reviews"):
            await asyncio.sleep(0.1)
            return {"reviews": []}

    # Concurrent operations are traced
    details, reviews = await asyncio.gather(
        fetch_details(),
        fetch_reviews()
    )

    return {"item_id": item_id, "details": details, "reviews": reviews}
```

See [Distributed Tracing](tracing.md) for more information on tracing.

## Error Handling in Async

Error handling works the same way as sync handlers:

```python
@app.post("/process/async")
async def process_async(
    client: CogniteClient,
    logger: logging.Logger,
    data: dict[str, Any]
) -> dict[str, Any]:
    """Async handler with error handling"""
    try:
        result = await process_data_async(data)
        return {"status": "success", "result": result}
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        raise
```

## Best Practices

### Do Use Async For

**Yes** Multiple concurrent I/O operations
**Yes** External API calls that can run in parallel
**Yes** Database queries that can be batched
**Yes** Long-running I/O-bound tasks

### Don't Use Async For

**Avoid:** Simple CPU-bound calculations
**Avoid:** Single sequential operations
**Avoid:** Code that doesn't have awaitable operations

### Example - When to Choose

```python
# **Good** use of async - concurrent operations
@app.get("/dashboard")
async def get_dashboard(client: CogniteClient) -> dict[str, Any]:
    assets, timeseries, events = await asyncio.gather(
        fetch_assets(),
        fetch_timeseries(),
        fetch_events()
    )
    return {"assets": assets, "timeseries": timeseries, "events": events}

# **Good** use of sync - simple operation
@app.get("/health")
def health_check(client: CogniteClient) -> dict[str, Any]:
    return {"status": "healthy"}
```

### Avoid Blocking Operations in Async

Don't use blocking operations in async handlers:

```python
# **Bad** - blocking operations in async handler
@app.get("/bad-async")
async def bad_async(client: CogniteClient) -> dict[str, Any]:
    time.sleep(1)  # Blocks the event loop!
    result = blocking_io_operation()  # Also blocks!
    return {"result": result}

# **Good** - use async operations
@app.get("/good-async")
async def good_async(client: CogniteClient) -> dict[str, Any]:
    await asyncio.sleep(1)  # Non-blocking
    result = await async_io_operation()  # Non-blocking
    return {"result": result}
```

## See Also

- [Type Safety](type-safety.md) - Type validation works with async handlers
- [Dependency Injection](dependency-injection.md) - Inject dependencies into async handlers
- [Distributed Tracing](tracing.md) - Trace async operations
- [Logging](logging.md) - Log from async handlers
- [Error Handling](error-handling.md) - Handle errors in async handlers
