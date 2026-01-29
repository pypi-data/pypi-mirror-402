# Distributed Tracing

The Function Apps framework provides built-in distributed tracing support through OpenTelemetry, making it easy to understand execution flow, identify performance bottlenecks, and debug issues in production. Traces are sent to an OpenTelemetry collector like LightStep, Jaeger, or any OTLP-compatible backend.

## Why Use Tracing?

Tracing helps you:

- **Understand execution flow** - See how requests flow through your functions
- **Identify performance bottlenecks** - Find slow operations in your function
- **Debug production issues** - Trace exactly what happened during a specific execution
- **Monitor system behavior** - Analyze patterns across function executions
- **Track dependencies** - See how different services interact
- **Understand a Cognite Workflow** - Connect the trace of a workflow by passing along the trace ID.

Unlike logging, which gives you discrete events, tracing provides a hierarchical view of operations with timing information, making it perfect for understanding complex workflows.

## Quick Start

### 1. Configure Tracing Backend

**Local Development (Jaeger)**
For local development we recommend Jaeger as a lightweight satellite:

```bash
# Start Jaeger (OTLP on 4317, UI on 16686)
docker run -d -p 4317:4317 -p 16686:16686 jaegertracing/all-in-one:latest
```

**Production (Honeycomb/LightStep)**

For functions running in CDF, we recommend Honeycomb or LightStep.

**Get your API key:**

- [Honeycomb](https://ui.honeycomb.io/account) - Free tier available
- [LightStep](https://docs.lightstep.com/docs/create-and-manage-access-tokens)

**Store API key locally:**

```bash
echo "TRACING_API_KEY=your-honeycomb-api-key" > .env
```

**Deploy function with tracing:**

```python
# deploy.py
import os
from dotenv import load_dotenv
from cognite.client import CogniteClient

load_dotenv()
client = CogniteClient()

function = client.functions.create(
    name="my-traced-function",
    external_id="my-traced-function",
    folder_path="./example/",
    secrets={"tracing-api-key": os.getenv("TRACING_API_KEY")}
)
```

**Deploy with Toolkit:**

For use with Cognite Toolkit, add to `my_function.Function.yaml`:

```yaml
secrets:
  tracing-api-key: ${TRACING_API_KEY}
```

### 2. Create Your Function

```python
from cognite_function_apps import (
    FunctionApp,
    FunctionTracer,
    TracingConfig,
    create_function_service,
    create_tracing_app,
)
from cognite.client import CogniteClient

app = FunctionApp(title="my-traced-function", version="1.0.0")

# Production: Use backend preset "honeycomb" or "lightstep"
tracing = create_tracing_app(backend="honeycomb")

# Local: Use Jaeger (no authentication)
# tracing = create_tracing_app(backend=TracingConfig(endpoint="http://localhost:4317"))

@app.get("/items/{item_id}")
@tracing.trace()  # Automatic root span with metadata
def get_item(client: CogniteClient, tracer: FunctionTracer, item_id: int) -> dict[str, Any]:
    # Root span already created by decorator!

    with tracer.span("fetch_item"):
        item = client.assets.retrieve(id=item_id)

    with tracer.span("process"):
        result = {"id": item_id, "name": item.name if item else "Not found"}

    return result

handle = create_function_service(tracing, app)
```

### 3. Test Your Setup

```bash
# Serve the example app
fun serve examples/
```

**Test interactively with Swagger UI:**

1. Visit <http://localhost:8000/docs>
2. Click on `GET /items/{item_id}`
3. Click "Try it out", enter `123` for item_id, and click "Execute"

**Or test with curl:**

```bash
curl -X POST http://localhost:8000/items/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Item","price":100.0}'
```

Then view traces at <http://localhost:16686> or on Honeycomb or Lightstep

## Core Usage

### Set spans and nested spans

Nest `tracer.span()` calls to create true parent-child relationships. These are helpful to break down the performance of a processing step to understand if you are IO or CPU bound:

```python
@app.post("/analyze")
@tracing.trace()
def analyze_data(client: CogniteClient, tracer: FunctionTracer, asset_ids: list[int]) -> dict[str, Any]:
    # Root span: "POST /analyze"
    # └─ fetch_and_process (parent)
    #    ├─ fetch_assets - I/O (child 1)
    #    └─ calculate_metrics -  (child 2)
    #       with asset_count as attribute.

    with tracer.span("fetch_and_process"):
        with tracer.span("fetch_assets"):
            assets = client.assets.retrieve_multiple(ids=asset_ids)
        with tracer.span("calculate_metrics") as calc_span:
            calc_span.set_attribute("asset_count", len(assets))
            total = sum(a.metadata.get("value", 0) for a in assets)

    return {"total": total, "count": len(assets)}
```

### Exception Recording

Exceptions are automatically recorded with `exception.type` and `exception.message`, enabling you to **filter traces by errors** in Honeycomb/Lightstep/Jaeger:

```python
@app.post("/process")
@tracing.trace()
def process_data(client: CogniteClient, tracer: FunctionTracer, data: list[dict[str, Any]]) -> dict[str, Any]:
    with tracer.span("validate"):
        if not data:
            raise ValueError("Data required")  # Recorded in span automatically

    with tracer.span("save"):
        client.events.create(data)  # CogniteAPIError recorded if this fails

    return {"processed": len(data)}
```

**In your tracing UI:** Filter by `error=true` or `exception.type="ValueError"` to find all failed requests.

### Custom Attributes

Add metadata to spans for filtering and debugging:

```python
with tracer.span("process_batch") as span:
    span.set_attribute("batch_size", len(items))
    span.set_attribute("region", "europe-west1")
    # ... processing ...
    span.set_attribute("items_processed", count)
```

**Filter examples:** `batch_size > 100`, `region="europe-west1"`, `items_processed < batch_size` (partial failures)

## Automatic Metadata

Root spans created by `@tracing.trace()` automatically include:

**HTTP Context:**

- `http.method` - POST, GET, etc.
- `http.route` - `/items/{item_id}`
- `http.url` - Full request path
- `http.status_code` - 200, 500, etc.

**Cognite Context:**

- `cognite.call_id` - Unique ID for this function invocation
- `cognite.function_id` - Function identifier (or `local-dev-server`)
- `cognite.schedule_id` - Schedule ID if triggered by schedule

**Error Details:**

- `error.type` - `ValidationError`, `ExecutionError`, `CogniteAPIError`, etc.
- `status_message` - Full error message (e.g., "Input validation failed: ...")

**Service Info:**

- `service.name` - From `FunctionApp(title=...)`
- `service.version` - From `FunctionApp(version=...)`
- `duration_ms` - Span duration in milliseconds

**OpenTelemetry Standard:**

- `trace.trace_id` - Distributed trace ID
- `trace.span_id` - This span's unique ID
- `span.kind` - Always `server` for root spans
- `span.num_events` - Event count (see below)
- `span.num_links` - Link count (see below)

### Span Events

**Events** record point-in-time occurrences within a span without creating child spans. Use for cache hits, retries, warnings, or decision points:

```python
with tracer.span("process_data") as span:
    span.add_event("cache_miss", {"key": f"asset_{asset_id}"})
    data = fetch_from_api(asset_id)
    span.add_event("data_fetched", {"size_bytes": len(data)})
```

## Advanced: Filtering Traces for one Cognite Workflow Run

For Cognite Workflows, generate a human-readable correlation ID and pass it through the workflow spec to link related traces. (This might become automatic in the future).

This example shows an orchestrator pattern where a dispatcher discovers work and spawns parallel workers.

**Workflow definition** (pass trace ID through dynamic task body):

```json
[
  {
    "externalId": "dispatcher",
    "type": "function",
    "parameters": {
      "function": {
        "externalId": "my-function",
        "data": {"path": "/dispatch", "method": "POST"}
      }
    }
  },
  {
    "externalId": "workers",
    "type": "dynamic",
    "dependsOn": [{"externalId": "dispatcher"}],
    "parameters": {
      "dynamic": {
        "tasks": "${dispatcher.output.response.data.tasks}",
        "function": {
          "externalId": "my-function",
          "data": {
            "path": "/worker",
            "method": "POST",
            "body": {
              "item_id": "${dynamic.input.item_id}",
              "workflow_run_id": "${dispatcher.output.response.data.workflow_run_id}"
            }
          }
        }
      }
    }
  },
]
```

```python
from datetime import datetime, timezone
from opentelemetry import trace

# Step 1: Dispatcher generates a workflow run ID
@app.post("/dispatch")
@tracing.trace()
def dispatch_workers(client: CogniteClient, tracer: FunctionTracer, input_data: dict[str, Any]) -> dict[str, Any]:
    # Generate human-readable workflow run ID
    workflow_run_id = f"workflow-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

    # Discover work and split into tasks
    tasks = [{"item_id": i, "data": {...}} for i in range(20)]

    return {
        "workflow_run_id": workflow_run_id,  # Pass to workers
        "tasks": tasks,
    }

# Step 2: Workers receive workflow run ID and set it as attribute
@app.post("/worker")
@tracing.trace()
def process_item(client: CogniteClient, tracer: FunctionTracer,
                 item_id: int, workflow_run_id: str) -> dict[str, Any]:
    # Set workflow run ID on root span for querying
    root_span = trace.get_current_span()
    root_span.set_attribute("workflow.run_id", workflow_run_id)
    root_span.set_attribute("item_id", item_id)

    with tracer.span("process"):
        result = process(item_id)

    return {"item_id": item_id, "result": result}
```

**In your tracing UI:** Filter by `workflow.run_id="workflow-20241114-153000"` to see all traces (dispatcher + 20 workers) from a single workflow execution.

## Custom Backend

For other OTLP backends, use TracingConfig:

```python
from cognite_function_apps import TracingConfig

tracing = create_tracing_app(
    backend=TracingConfig(
        endpoint="https://your-collector:4317",
        header_name="authorization",
        secret_key="my-custom-key",  # Name of secret in CDF
        docs_url="https://your-docs.com",
    )
)
```

## Best Practices

**Span Naming:**

- ✅ Descriptive: `fetch_user_profile`, `validate_order`, `calculate_shipping`
- ❌ Vague: `step1`, `do_stuff`, `process`

**Span Granularity:**

- ✅ Separate I/O operations (API calls, CDF queries) from processing (computation, transformation)
- ✅ This shows if you're I/O bound (slow network) or CPU bound (slow processing)
- ❌ Don't create spans for trivial operations (assignments, logging)

**Attribute Values:**

- ✅ Scalar values: `equipment_id`, `count`
- ❌ Large objects (use summaries instead)

**Privacy & Security:**

- ✅ Use IDs and counts: `asset_id=123`, `batch_size=50`
- ❌ Never include customer data: names, emails, external_ids, sensor values, equipment metadata
- ❌ Traces are sent to third-party backends (Honeycomb/Lightstep) - treat them as insecure
- 💡 If unsure, don't include it - spans are for debugging flow, not data inspection

**Performance:**

- Reasonable span count: 10-100 spans per request
- Spans have minimal overhead (~microseconds)
- Async export via BatchSpanProcessor (non-blocking)

## Troubleshooting

### Traces not appearing

Check the function log for any of the following errors:

**Error: `Tracing support requires OpenTelemetry. Install it with: pip install cognite-function-apps[tracing]`**

Add the tracing extra to your dependencies:

```txt
# requirements.txt
cognite-function-apps[tracing]
```

Or with `uv`:

```bash
uv add 'cognite-function-apps[tracing]'
```

**Error: `Secret 'tracing-api-key' not found in CDF secrets or environment variables`**

The tracing API key is missing. See the [Quick Start](#quick-start) section above for how to configure secrets for deployment (SDK or Toolkit) and local development.

**Error: `Failed to flush trace spans: ... 401/403/unauthorized`**

Your tracing API key is invalid, expired, or revoked. Get a new key:

- [Honeycomb](https://ui.honeycomb.io/account) → Environment Settings → API Keys
- [LightStep](https://docs.lightstep.com/docs/create-and-manage-access-tokens)

**Traces still not appearing:**

1. **Check collector is running** (for local Jaeger):

   ```bash
   docker ps | grep jaeger
   curl http://localhost:16686/
   ```

2. **Ensure TracingApp is composed**:

   ```python
   handle = create_function_service(tracing, app)  # Include tracing
   ```

### Missing metadata

Use `@tracing.trace()` decorator for automatic HTTP/Cognite metadata:

```python
@app.get("/items/{id}")
@tracing.trace()  # Adds automatic metadata
def handler(client: CogniteClient, tracer: FunctionTracer, id: int): ...
```

## Next Steps

- [Dependency Injection](dependency-injection.md) - How tracer is injected
- [MCP Integration](mcp.md) - AI tools with tracing
- [Dev Server](dev-server.md) - Local testing with secrets
