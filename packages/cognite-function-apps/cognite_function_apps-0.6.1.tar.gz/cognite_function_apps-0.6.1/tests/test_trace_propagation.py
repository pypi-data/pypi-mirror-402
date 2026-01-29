"""Tests for W3C Trace Context propagation across function calls."""

from typing import Any
from unittest.mock import Mock, patch

import httpx
import pytest
from cognite.client import CogniteClient

from cognite_function_apps import FunctionApp, create_function_service
from cognite_function_apps.base_client import BaseFunctionClient
from cognite_function_apps.devserver.asgi import _run_cognite_asgi_app  # type: ignore[reportPrivateUsage]
from cognite_function_apps.models import HTTPMethod

# Skip all tests if OpenTelemetry not installed
pytest.importorskip("opentelemetry")

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter


@pytest.fixture
def span_exporter() -> InMemorySpanExporter:  # type: ignore[misc]
    """Provide in-memory span exporter for testing."""
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(exporter, max_export_batch_size=1))
    trace.set_tracer_provider(provider)
    yield exporter  # type: ignore[misc]
    exporter.clear()


@pytest.mark.asyncio
async def test_function_client_injects_traceparent_header_for_devserver(span_exporter: InMemorySpanExporter):
    """Test that FunctionClient injects W3C traceparent header when calling devserver with active span."""
    # ARRANGE: Create parent span with known trace ID
    tracer = trace.get_tracer("test-parent")

    with tracer.start_as_current_span("parent_operation") as parent_span:
        parent_trace_id = format(parent_span.get_span_context().trace_id, "032x")

        # ARRANGE: Mock httpx.request to capture headers
        captured_headers: dict[str, str] = {}

        def mock_request(method: str, url: str, headers: dict[str, str] | None = None, **kwargs: Any) -> Mock:
            if headers:
                captured_headers.update(headers)
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True, "data": {"result": "ok"}}
            return mock_response

        # ACT: Make devserver call with active trace context
        with patch.object(httpx, "request", side_effect=mock_request):
            client = BaseFunctionClient(base_url="http://localhost:8000")
            response = client._call_devserver(  # type: ignore[reportPrivateUsage]
                method=HTTPMethod.POST, path="/test", body={"data": "test"}, params=None
            )

        # ASSERT: Response succeeded
        assert response["success"] is True

        # ASSERT: traceparent header was injected with correct W3C format
        assert "traceparent" in captured_headers
        version, trace_id, span_id, flags = captured_headers["traceparent"].split("-")
        assert version == "00"
        assert trace_id == parent_trace_id
        assert len(span_id) == 16
        assert flags in ["00", "01"]


@pytest.mark.asyncio
async def test_devserver_extracts_and_normalizes_headers():
    """Test that _run_cognite_asgi_app extracts HTTP headers and normalizes names to lowercase.

    Exercises the header extraction logic in asgi.py (lines 272-275) which transforms
    ASGI HTTP headers [(b"TraceParent", b"value")] → {"traceparent": "value"}.

    The test uses capturing middleware to intercept the transformed Cognite ASGI scope
    since headers are not directly accessible from the HTTP response.
    """
    # Test data: Input headers (byte-encoded strings from ASGI) and expected normalized output.
    input_headers: list[tuple[bytes, bytes]] = [
        (b"TraceParent", b"00-trace-id-span-id-01"),
        (b"Content-Type", b"application/json"),
    ]
    expected_headers: dict[str, str] = {
        "traceparent": "00-trace-id-span-id-01",
        "content-type": "application/json",
    }

    # ARRANGE: Create application under test
    app = FunctionApp("TestApp", "1.0.0")

    @app.get("/test")
    def test_handler() -> dict[str, Any]:
        return {"status": "ok"}

    handle = create_function_service(app)

    # ARRANGE: Set up test infrastructure (capturing middleware)
    captured_headers: dict[str, str] = {}
    original_asgi_app = handle.asgi_app

    async def capturing_asgi_app(scope: Any, receive: Any, send: Any) -> None:
        """Intercept the Cognite ASGI scope to capture the transformed headers dict."""
        nonlocal captured_headers
        captured_headers = scope.get("headers", {})
        assert original_asgi_app is not None
        await original_asgi_app(scope, receive, send)

    handle.asgi_app = capturing_asgi_app

    # ARRANGE: Create HTTP request with test headers
    http_scope: dict[str, Any] = {
        "type": "http",
        "method": "GET",
        "path": "/test",
        "query_string": b"",
        "headers": input_headers,
    }

    async def receive() -> dict[str, Any]:
        return {"type": "http.request", "body": b""}

    async def send(message: dict[str, Any]) -> None:
        pass

    # ACT: Run the ASGI app which should extract and normalize headers
    await _run_cognite_asgi_app(handle, http_scope, receive, send, Mock(spec=CogniteClient))  # type: ignore[arg-type]

    # ASSERT: Verify headers were extracted and normalized to lowercase
    assert captured_headers == expected_headers
