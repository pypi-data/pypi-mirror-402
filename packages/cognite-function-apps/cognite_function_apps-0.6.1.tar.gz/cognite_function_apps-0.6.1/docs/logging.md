# Logging

The framework provides an enterprise-grade logging solution that works across all cloud providers through dependency injection.

## Why Use the Framework Logger?

According to the [Cognite Functions documentation](https://docs.cognite.com/cdf/functions/), the standard Python `logging` module is not recommended because it can interfere with the cloud provider's logging infrastructure. This framework provides an **isolated logger** that:

- Uses Python's standard `logging` module with familiar API
- Writes directly to stdout (captured by all cloud providers)
- Is completely isolated from other loggers
- Supports standard log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Can be dependency-injected like `client` and `secrets`
- Works with both sync and async handlers

## Logger Usage

Add `logger: logging.Logger` to your function signature to have it automatically injected:

```python
import logging
from cognite.client import CogniteClient
from cognite_function_apps import FunctionApp

app = FunctionApp(title="My API", version="1.0.0")

@app.get("/items/{item_id}")
def get_item(client: CogniteClient, logger: logging.Logger, item_id: int) -> dict[str, Any]:
    """Retrieve an item with logging"""
    logger.info(f"Fetching item {item_id}")
    item = fetch_item(item_id)
    logger.debug(f"Item details: {item}")
    return {"id": item_id, "name": item.name}
```

## Log Levels

The framework supports all standard Python log levels:

```python
@app.post("/process/data")
def process_data(client: CogniteClient, logger: logging.Logger, data: dict[str, Any]) -> dict[str, Any]:
    logger.debug("Detailed debug information")      # DEBUG: Detailed diagnostic info
    logger.info("Processing started")               # INFO: General informational messages
    logger.warning("Unexpected value encountered")  # WARNING: Warning messages
    logger.error("Processing failed")               # ERROR: Error messages
    logger.critical("System failure")               # CRITICAL: Critical errors
    return {"status": "processed"}
```

By default, the logger is configured at **INFO** level, meaning DEBUG messages are not shown unless you change the log level.

## Async Handlers

The logger works seamlessly with async handlers:

```python
import asyncio

@app.post("/process/batch")
async def process_batch(
    client: CogniteClient,
    logger: logging.Logger,
    items: list[Item]
) -> dict[str, Any]:
    logger.info(f"Starting batch processing of {len(items)} items")

    async def process_item(item: Item) -> dict[str, Any]:
        logger.debug(f"Processing item: {item.name}")
        result = await process_async(item)
        return result

    results = await asyncio.gather(*[process_item(item) for item in items])
    logger.info(f"Batch processing complete. Processed {len(results)} items")
    return {"processed_count": len(results), "results": results}
```

## Logging with Error Handling

Combine logging with error handling for better debugging:

```python
@app.post("/items/")
def create_item(
    client: CogniteClient,
    logger: logging.Logger,
    item: Item
) -> ItemResponse:
    """Create a new item with logging"""
    logger.info(f"Creating item: {item.name}")

    try:
        # Your creation logic
        new_id = save_to_database(item)
        logger.info(f"Successfully created item {new_id}")

        total = item.price + (item.tax or 0)
        return ItemResponse(id=new_id, item=item, total_price=total)

    except Exception as e:
        logger.error(f"Failed to create item: {e}", exc_info=True)
        raise
```

## Structured Logging

For structured logging, include relevant context in your log messages:

```python
@app.get("/assets/{asset_id}")
def get_asset(
    client: CogniteClient,
    logger: logging.Logger,
    asset_id: int,
    include_metadata: bool = False
) -> dict[str, Any]:
    """Retrieve asset with structured logging"""
    logger.info(
        f"Fetching asset",
        extra={
            "asset_id": asset_id,
            "include_metadata": include_metadata,
            "user_action": "get_asset"
        }
    )

    asset = client.assets.retrieve(id=asset_id)

    if not asset:
        logger.warning(f"Asset {asset_id} not found")
        return {"error": "Asset not found"}

    logger.debug(f"Asset data: {asset.dump()}")
    return asset.dump()
```

## Logging Best Practices

### Use Appropriate Log Levels

- **DEBUG**: Detailed diagnostic information (variable values, state dumps)
- **INFO**: General informational messages (operation started, completed)
- **WARNING**: Unexpected situations that don't prevent execution
- **ERROR**: Errors that prevent a specific operation from completing
- **CRITICAL**: Severe errors that may cause the entire function to fail

### Don't Log Sensitive Information

Avoid logging credentials, tokens, API keys, or personal data:

```python
# **Bad** - logs sensitive data
logger.info(f"Using API key: {api_key}")

# **Good** - logs that key exists without revealing it
logger.info("API key configured")
```

### Use Structured Logging

Include relevant context in your log messages:

```python
# BAD: Less useful
logger.info("Processing started")

# **Yes** Better - includes context
logger.info(f"Processing batch of {len(items)} items for user {user_id}")
```

### Log at Key Points

Log at important execution points:

- Entry points (function start)
- Success paths (operation completed)
- Error conditions (operation failed)
- Important state changes
- External API calls

```python
@app.post("/process/workflow")
def process_workflow(
    client: CogniteClient,
    logger: logging.Logger,
    workflow_id: int
) -> dict[str, Any]:
    logger.info(f"Starting workflow {workflow_id}")

    # Log external calls
    logger.debug("Fetching workflow data from CDF")
    workflow = client.workflows.retrieve(id=workflow_id)

    # Log state changes
    logger.info(f"Workflow status: {workflow.status}")

    # Log completion
    logger.info(f"Workflow {workflow_id} processed successfully")
    return {"status": "complete"}
```

### Use Exception Information

When logging exceptions, include the traceback:

```python
try:
    risky_operation()
except Exception as e:
    # **Good** - includes full traceback
    logger.error("Operation failed", exc_info=True)
    raise
```

## Testing Locally

When running the [local development server](dev-server.md), logs appear in the console:

```bash
fun serve examples/
# Logs will appear in the console output
```

You can adjust the log level using the `--log-level` option:

```bash
fun serve examples/ --log-level debug
```

## See Also

- [Error Handling](error-handling.md) - Structured error responses
- [Async Support](async-support.md) - Using logger with async handlers
- [Dependency Injection](dependency-injection.md) - How dependencies are injected
- [Local Dev Server](dev-server.md) - Testing functions locally with logging
