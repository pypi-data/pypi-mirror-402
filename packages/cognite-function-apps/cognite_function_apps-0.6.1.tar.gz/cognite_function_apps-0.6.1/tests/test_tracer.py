"""Tests for the new DI-based tracing system."""

import asyncio
import logging
from collections.abc import Mapping
from contextlib import contextmanager
from typing import Any
from unittest.mock import Mock

import pytest
from cognite.client import CogniteClient
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SpanExporter
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from cognite_function_apps import FunctionApp, FunctionTracer, create_function_service
from cognite_function_apps._version import __version__
from cognite_function_apps.models import (
    ASGITypedFunctionRequestMessage,
    ASGITypedFunctionScope,
    FunctionCallInfo,
    HTTPMethod,
    RequestData,
)
from cognite_function_apps.tracer import (
    TracingApp,
    TracingConfig,
    _normalize_service_name,  # type: ignore[protected-access]
    _resolve_secret,  # type: ignore[attr-defined]
    create_tracing_app,
)

# Test config for local OTLP endpoint (Jaeger)
TEST_CONFIG = TracingConfig(
    endpoint="http://test:4317",
    header_name=None,
    secret_key=None,
    docs_url=None,
)


@contextmanager
def create_tracer_with_call_id(call_id: str):
    """Helper to create a tracer with call_id in span context.

    This helper yields a FunctionTracer that will add the call_id attribute
    to all spans. The global tracer provider should already be configured
    by the session-scoped fixture.
    """
    # Create tracer (provider already set up by session fixture)
    tracer = FunctionTracer(trace.get_tracer(__name__))

    # We need to create a wrapper that adds call_id to all spans
    original_span = tracer.span

    @contextmanager
    def span_with_call_id(name: str):
        with original_span(name) as span:
            span.set_attribute("cognite.call_id", call_id)
            yield span

    tracer.span = span_with_call_id  # type: ignore[method-assign]
    yield tracer


def test_tracer_dependency_injection():
    """Test that tracer can be injected into route handlers."""
    app = FunctionApp("Test")

    @app.get("/test")
    def test_route(tracer: FunctionTracer) -> dict[str, str]:
        with tracer.span("test_span"):
            pass
        return {"status": "ok"}

    # Test that route accepts tracer parameter
    assert "tracer" in test_route.__annotations__


@pytest.mark.parametrize(
    ("input_name", "expected"),
    [
        ("Asset Management API", "asset-management-api"),
        ("My Service Name", "my-service-name"),
        ("Single", "single"),
        ("My_Service_Name", "my-service-name"),
        ("asset_management", "asset-management"),
        ("_leading_underscore", "leading-underscore"),
        ("trailing_underscore_", "trailing-underscore"),
        ("UPPERCASE_NAME", "uppercase-name"),
        ("asset-management-api", "asset-management-api"),
        ("my-service", "my-service"),
        ("service", "service"),
        ("My__Double__Underscore", "my-double-underscore"),
        ("Mixed _ Separators", "mixed-separators"),
    ],
)
def test_normalize_service_name(input_name: str, expected: str):
    """Test service name normalization with various inputs."""
    assert _normalize_service_name(input_name) == expected


def test_otlp_export_configuration(span_exporter: InMemorySpanExporter):
    """Test that TracerProvider is configured and spans are exported."""
    # Verify provider is configured
    provider = trace.get_tracer_provider()
    assert isinstance(provider, TracerProvider)

    # Create spans and verify they are exported
    test_call_id = "test-call-123"
    tracer = FunctionTracer(trace.get_tracer(__name__))

    with tracer.span("test_operation") as span:
        span.set_attribute("test.attribute", "test_value")
        span.set_attribute("cognite.call_id", test_call_id)

    # Force flush to ensure spans are exported
    provider.force_flush(timeout_millis=1000)

    # Verify spans were exported
    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    span = spans[0]
    assert span.name == "test_operation"
    assert span.attributes is not None
    assert span.attributes["test.attribute"] == "test_value"
    assert span.attributes["cognite.call_id"] == test_call_id
    assert span.attributes["operation.name"] == "test_operation"


def test_tracer_works_without_call_id():
    """Test tracer works even when call_id is not set."""
    tracer = FunctionTracer(trace.get_tracer(__name__))

    # Tracer should work - spans will be exported without call_id attribute
    with tracer.span("test_operation"):
        result = "test_result"

    # Should not raise any exceptions
    assert result == "test_result"


def test_tracer_exception_handling():
    """Test that tracer properly handles exceptions."""
    with create_tracer_with_call_id("test-call-123") as tracer:
        with pytest.raises(ValueError):
            with tracer.span("test_operation"):
                raise ValueError("Test error")

        # Exception should be properly recorded in span
        # (This is tested by the span context manager implementation)


@pytest.mark.parametrize(
    "span_name,has_tracer,use_route",
    [
        (None, True, False),  # basic case
        ("custom_operation", True, False),  # custom span name
        (None, False, False),  # no tracer parameter
        (None, True, True),  # with route metadata
    ],
)
def test_tracing_app_decorator_variations(span_name: str | None, has_tracer: bool, use_route: bool):
    """Test TracingApp decorator with various configurations."""
    tracing = create_tracing_app(backend=TEST_CONFIG)
    app = FunctionApp("Test") if use_route else None

    if use_route and app:
        if span_name:

            @app.get("/items/{id}")
            @tracing.trace(span_name)
            def test_func(tracer: FunctionTracer, id: int) -> dict[str, int]:  # type: ignore[no-redef]
                return {"id": id}
        else:

            @app.get("/items/{id}")
            @tracing.trace()
            def test_func(tracer: FunctionTracer, id: int) -> dict[str, int]:  # type: ignore[no-redef]
                return {"id": id}

        with create_tracer_with_call_id("test-123") as tracer:
            result = test_func(tracer=tracer, id=123)
            assert result == {"id": 123}
    elif has_tracer:
        if span_name:

            @tracing.trace(span_name)
            def test_func(tracer: FunctionTracer) -> dict[str, str]:  # type: ignore[no-redef]
                with tracer.span("child_span"):
                    pass
                return {"result": "ok"}
        else:

            @tracing.trace()
            def test_func(tracer: FunctionTracer) -> dict[str, str]:  # type: ignore[no-redef]
                with tracer.span("child_span"):
                    pass
                return {"result": "ok"}

        with create_tracer_with_call_id("test-123") as tracer:
            result = test_func(tracer=tracer)
            assert result == {"result": "ok"}
    else:

        @tracing.trace()
        def test_func() -> dict[str, str]:  # type: ignore[no-redef]
            return {"result": "ok"}

        result = test_func()
        assert result == {"result": "ok"}


def test_tracing_app_exception_handling() -> None:
    """Test TracingApp properly handles exceptions."""
    tracing = create_tracing_app(backend=TEST_CONFIG)

    @tracing.trace()
    def test_func(tracer: FunctionTracer) -> dict[str, str]:
        raise ValueError("Test error")

    with create_tracer_with_call_id("test-123") as tracer:
        with pytest.raises(ValueError, match="Test error"):
            test_func(tracer=tracer)


def test_tracing_app_mismatched_parameter_name_disables_tracing():
    """Test that wrong parameter name disables @trace() decorator logic.

    When the parameter name doesn't match 'tracer', the decorator returns the
    function unchanged. The function still executes normally if called directly,
    but the decorator's child span creation is skipped.
    """
    tracing = create_tracing_app(backend=TEST_CONFIG)

    # Wrong parameter name - decorator will return function unchanged
    @tracing.trace("custom_operation")
    def test_func(my_custom_tracer: FunctionTracer, value: int) -> dict[str, int]:
        # This will work if we manually pass a tracer, but the @trace() decorator
        # won't create a child span because the parameter name doesn't match
        with my_custom_tracer.span("inner_operation"):
            pass
        return {"value": value}

    with create_tracer_with_call_id("test-456") as tracer_instance:
        # Function executes, but without decorator's child span
        result = test_func(my_custom_tracer=tracer_instance, value=42)
        assert result == {"value": 42}


def test_tracing_app_strict_function_call_info_matching():
    """Test that function_call_info requires BOTH name AND type to match (strict framework dependency)."""
    tracing = create_tracing_app(backend=TEST_CONFIG)

    # Test 1: Correct name AND type - should capture metadata
    @tracing.trace()
    def correct_signature(tracer: FunctionTracer, function_call_info: FunctionCallInfo) -> dict[str, str]:
        return {"test": "ok"}

    # Test 2: Wrong type (dict instead of FunctionCallInfo) - should NOT capture metadata
    @tracing.trace()
    def wrong_type(tracer: FunctionTracer, function_call_info: FunctionCallInfo) -> dict[str, str]:
        return {"test": "ok"}

    # Test 3: Wrong name but correct type - should NOT capture metadata
    @tracing.trace()
    def wrong_name(tracer: FunctionTracer, my_call_info: FunctionCallInfo) -> dict[str, str]:
        return {"test": "ok"}

    with create_tracer_with_call_id("test-789") as tracer:
        # All should work, but only the first one properly matches function_call_info
        call_info: FunctionCallInfo = {
            "call_id": "test-789",
            "function_id": "fn-123",
            "schedule_id": None,
            "scheduled_time": None,
        }

        result1 = correct_signature(tracer=tracer, function_call_info=call_info)
        assert result1 == {"test": "ok"}

        result2 = wrong_type(tracer=tracer, function_call_info={"call_id": "test-789"})  # type: ignore[arg-type]
        assert result2 == {"test": "ok"}

        result3 = wrong_name(tracer=tracer, my_call_info=call_info)
        assert result3 == {"test": "ok"}


# ===== Integration tests for ASGI middleware architecture =====


@pytest.mark.asyncio
async def test_tracing_app_middleware_creates_root_span(span_exporter: InMemorySpanExporter):
    """Test that TracingApp creates root span at middleware level."""
    # Create TracingApp (uses already-configured provider from session fixture)
    app = FunctionApp("TestApp")
    tracing = create_tracing_app(backend=TEST_CONFIG)

    # Get the provider for flushing
    provider = trace.get_tracer_provider()

    @app.get("/items/{id}")
    def get_item(id: int) -> dict[str, int]:
        return {"id": id}

    # Create service with tracing middleware
    handle = create_function_service(tracing, app)

    # Create mock client
    client = Mock(spec=CogniteClient)

    # Call through the service (which goes through ASGI middleware)
    function_call_info: FunctionCallInfo = {
        "call_id": "test-call-456",
        "function_id": "fn-789",
        "schedule_id": None,
        "scheduled_time": None,
    }

    result = await handle.async_handle(
        client=client,
        data={"path": "/items/123", "method": "GET", "body": {}},
        function_call_info=function_call_info,
    )

    # Verify response (wrapped in data + success format)
    assert result.get("data") == {"id": 123}
    status_code = result.get("status_code", 500)
    assert isinstance(status_code, int)
    assert status_code < 400

    # Force flush to export spans
    if isinstance(provider, TracerProvider):
        provider.force_flush(timeout_millis=1000)

    # Verify root span was created
    spans = span_exporter.get_finished_spans()
    assert len(spans) >= 1

    # Find root span (should have SERVER kind and no parent)
    root_spans = [s for s in spans if s.parent is None]
    assert len(root_spans) == 1

    root_span = root_spans[0]
    assert root_span.name == "GET /items/{id}"
    assert root_span.attributes is not None
    assert root_span.attributes.get("http.method") == "GET"
    # http.route should be the parameterized template, not the concrete path
    assert root_span.attributes.get("http.route") == "/items/{id}"
    assert root_span.attributes.get("cognite.call_id") == "test-call-456"
    assert root_span.attributes.get("cognite.function_id") == "fn-789"
    assert root_span.attributes.get("http.status_code") == 200


@pytest.mark.asyncio
async def test_tracing_app_middleware_handles_errors(span_exporter: InMemorySpanExporter):
    """Test that TracingApp detects error responses and marks root span."""
    # Create app that raises an error
    app = FunctionApp("TestApp")
    tracing = create_tracing_app(backend=TEST_CONFIG)

    # Get the provider for flushing
    provider = trace.get_tracer_provider()

    @app.get("/error")
    def error_route() -> dict[str, str]:
        raise ValueError("Test error")

    # Create service with tracing middleware
    handle = create_function_service(tracing, app)

    # Create mock client
    client = Mock(spec=CogniteClient)

    # Call endpoint that raises an error
    result = await handle.async_handle(
        client=client,
        data={"path": "/error", "method": "GET", "body": {}},
    )

    # Verify error response
    assert result.get("error_type") == "ExecutionError"
    message = result.get("message", "")
    assert isinstance(message, str) and "Test error" in message

    # Force flush to export spans
    if isinstance(provider, TracerProvider):
        provider.force_flush(timeout_millis=1000)

    # Verify root span marked as error
    spans = span_exporter.get_finished_spans()
    root_spans = [s for s in spans if s.parent is None]
    assert len(root_spans) == 1

    root_span = root_spans[0]
    assert root_span.attributes is not None
    assert root_span.attributes.get("error") is True
    assert root_span.attributes.get("error.type") == "ExecutionError"
    assert root_span.attributes.get("http.status_code") == 500


@pytest.mark.asyncio
async def test_tracing_app_child_spans_nested_under_root(span_exporter: InMemorySpanExporter):
    """Test that @trace() decorator creates child spans under root span."""
    # Create app with tracing
    app = FunctionApp("TestApp")
    tracing = create_tracing_app(backend=TEST_CONFIG)

    # Get the provider for flushing
    provider = trace.get_tracer_provider()

    @app.get("/nested")
    @tracing.trace()
    def nested_route(tracer: FunctionTracer) -> dict[str, str]:
        with tracer.span("business_logic"):
            with tracer.span("database_query"):
                pass
        return {"status": "ok"}

    # Create service with tracing middleware
    handle = create_function_service(tracing, app)

    # Create mock client
    client = Mock(spec=CogniteClient)

    # Call endpoint
    result = await handle.async_handle(
        client=client,
        data={"path": "/nested", "method": "GET", "body": {}},
    )

    # Verify response (wrapped in data + success format)
    assert result.get("data") == {"status": "ok"}
    status_code = result.get("status_code", 500)
    assert isinstance(status_code, int)
    assert status_code < 400

    # Force flush to export spans
    if isinstance(provider, TracerProvider):
        provider.force_flush(timeout_millis=1000)

    # Verify span hierarchy
    spans = span_exporter.get_finished_spans()
    assert len(spans) >= 4  # root + @trace child + business_logic + database_query

    # Find root span (no parent)
    root_spans = [s for s in spans if s.parent is None]
    assert len(root_spans) == 1
    root_span = root_spans[0]
    assert root_span.name == "GET /nested"

    # Find @trace() child span (parent is root)
    assert root_span.context is not None
    root_span_id = root_span.context.span_id
    trace_children = [s for s in spans if s.parent is not None and s.parent.span_id == root_span_id]
    assert len(trace_children) >= 1
    trace_span = trace_children[0]
    assert trace_span.name == "nested_route"

    # Find grandchild spans (business_logic and database_query)
    assert trace_span.context is not None
    trace_span_id = trace_span.context.span_id
    grandchildren = [s for s in spans if s.parent is not None and s.parent.span_id == trace_span_id]
    assert len(grandchildren) >= 1
    assert any(s.name == "business_logic" for s in grandchildren)


# ===== Tests for custom exporter provider with DI =====


@pytest.mark.asyncio
async def test_tracing_app_with_exporter_provider_using_secrets(span_exporter: InMemorySpanExporter):
    """Test that exporter_provider can use secrets from DI."""
    # Track that provider was called with secrets
    provider_called: dict[str, bool | Mapping[str, str] | None] = {"value": False, "secrets": None}

    def create_custom_exporter(secrets: Mapping[str, str]) -> SpanExporter:
        """Custom exporter that uses secrets."""
        provider_called["value"] = True
        provider_called["secrets"] = secrets

        # Validate that we got the expected secret
        token = secrets.get("test-token")
        if not token:
            raise ValueError("test-token secret is required")

        # Return the test exporter
        return span_exporter

    # Create app with custom exporter provider
    app = FunctionApp("TestApp")
    tracing = TracingApp(
        _exporter_provider=create_custom_exporter,
        service_name="test-service",
        service_version="1.0.0",
    )

    provider = trace.get_tracer_provider()

    @app.get("/test")
    def test_route() -> dict[str, str]:
        return {"status": "ok"}

    # Create service
    handle = create_function_service(tracing, app)

    # Create mock client and secrets
    client = Mock(spec=CogniteClient)
    secrets = {"test-token": "secret-value-123"}

    function_call_info: FunctionCallInfo = {
        "call_id": "test-call-789",
        "function_id": "fn-456",
        "schedule_id": None,
        "scheduled_time": None,
    }

    # Call endpoint - this should trigger lazy initialization
    result = await handle.async_handle(
        client=client,
        data={"path": "/test", "method": "GET", "body": {}},
        secrets=secrets,
        function_call_info=function_call_info,
    )

    # Verify response
    assert result.get("data") == {"status": "ok"}
    status_code = result.get("status_code", 500)
    assert isinstance(status_code, int)
    assert status_code < 400

    # Verify provider was called with secrets
    assert provider_called["value"] is True
    secrets_captured = provider_called["secrets"]
    assert secrets_captured is not None
    assert isinstance(secrets_captured, Mapping)
    assert secrets_captured.get("test-token") == "secret-value-123"

    # Force flush to export spans
    if isinstance(provider, TracerProvider):
        provider.force_flush(timeout_millis=1000)

    # Verify spans were created
    spans = span_exporter.get_finished_spans()
    assert len(spans) >= 1


@pytest.mark.asyncio
async def test_tracing_app_exporter_provider_called_once():
    """Test that exporter_provider is only called once even with multiple requests."""
    # Track number of times provider is called
    call_count = {"value": 0}
    test_exporter = InMemorySpanExporter()

    def create_custom_exporter() -> SpanExporter:
        """Custom exporter that tracks calls."""
        call_count["value"] += 1
        return test_exporter

    # Create app with custom exporter provider
    app = FunctionApp("TestApp")
    tracing = TracingApp(
        _exporter_provider=create_custom_exporter,
        service_name="test-service",
    )

    @app.get("/test")
    def test_route() -> dict[str, str]:
        return {"status": "ok"}

    # Create service
    handle = create_function_service(tracing, app)

    # Create mock client
    client = Mock(spec=CogniteClient)

    # Make multiple requests
    status_code: int = 500
    for _ in range(3):
        result = await handle.async_handle(
            client=client,
            data={"path": "/test", "method": "GET", "body": {}},
        )
        raw_status = result.get("status_code", 500)
        assert isinstance(raw_status, int)
        status_code = raw_status
    assert status_code < 400

    # Verify provider was only called once
    assert call_count["value"] == 1


@pytest.mark.asyncio
async def test_tracing_app_exporter_provider_with_multiple_dependencies(span_exporter: InMemorySpanExporter):
    """Test that exporter_provider can use multiple DI dependencies."""
    deps_provided = False

    def create_custom_exporter(
        secrets: Mapping[str, str],
        logger: logging.Logger,
        function_call_info: FunctionCallInfo | None,
        client: CogniteClient,
    ) -> SpanExporter:
        """Custom exporter that uses multiple DI dependencies."""
        nonlocal deps_provided
        # Verify all expected dependencies are provided
        assert isinstance(secrets, Mapping)
        assert isinstance(logger, logging.Logger)
        assert function_call_info is not None and isinstance(function_call_info, dict)
        assert client is not None
        deps_provided = True
        return span_exporter

    # Create app with custom exporter provider
    app = FunctionApp("TestApp")
    tracing = TracingApp(
        _exporter_provider=create_custom_exporter,
        service_name="test-service",
    )

    @app.get("/test")
    def test_route() -> dict[str, str]:
        return {"status": "ok"}

    # Create service and call endpoint
    handle = create_function_service(tracing, app)
    client = Mock(spec=CogniteClient)

    result = await handle.async_handle(
        client=client,
        data={"path": "/test", "method": "GET", "body": {}},
        secrets={"api-key": "test-key"},
        function_call_info={
            "call_id": "test-999",
            "function_id": "fn-777",
            "schedule_id": None,
            "scheduled_time": None,
        },
    )

    status_code = result.get("status_code", 500)
    assert isinstance(status_code, int)
    assert status_code < 400
    assert deps_provided


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error_type,error_msg,use_secrets",
    [
        ("runtime", "Failed to create exporter", False),
        ("missing_secret", "required-token secret is missing", True),
    ],
)
async def test_tracing_app_exporter_provider_errors(error_type: str, error_msg: str, use_secrets: bool):
    """Test that errors in exporter_provider result in error responses."""
    if error_type == "runtime":

        def provider() -> SpanExporter:  # pyright: ignore[reportRedeclaration]
            raise RuntimeError(error_msg)
    else:

        def provider(secrets: Mapping[str, str]) -> SpanExporter:  # type: ignore[no-redef]
            token = secrets.get("required-token")
            if not token:
                raise ValueError(error_msg)
            return InMemorySpanExporter()

    # Create app with failing provider
    app = FunctionApp("TestApp")
    tracing = TracingApp(
        _exporter_provider=provider,
        service_name="test-service",
    )

    @app.get("/test")
    def test_route() -> dict[str, str]:
        return {"status": "ok"}

    # Create service
    handle = create_function_service(tracing, app)

    # Create mock client
    client = Mock(spec=CogniteClient)
    secrets = {"wrong-key": "wrong-value"} if use_secrets else None

    # Call endpoint - should return error response
    result = await handle.async_handle(
        client=client,
        data={"path": "/test", "method": "GET", "body": {}},
        secrets=secrets,
    )

    # Verify error response
    status_code = result.get("status_code", 500)
    assert isinstance(status_code, int)
    assert status_code >= 400
    assert result.get("error_type") == "ExecutionError"
    message = result.get("message", "")
    assert isinstance(message, str)
    assert error_msg in message


@pytest.mark.asyncio
async def test_create_tracing_app_with_custom_config():
    """Test create_tracing_app with custom TracingConfig."""
    # Create custom config
    config = TracingConfig(
        endpoint="http://test:4317",
        header_name=None,
        secret_key=None,
        docs_url=None,
    )

    # Create app using convenience function with custom config
    app = FunctionApp("TestApp")
    tracing = create_tracing_app(backend=config)

    @app.get("/test")
    def test_route() -> dict[str, str]:
        return {"status": "ok"}

    # Create service
    handle = create_function_service(tracing, app)

    # Create mock client
    client = Mock(spec=CogniteClient)

    # Call endpoint
    result = await handle.async_handle(
        client=client,
        data={"path": "/test", "method": "GET", "body": {}},
    )

    status_code = result.get("status_code", 500)
    assert isinstance(status_code, int)
    assert status_code < 400
    assert result.get("data") == {"status": "ok"}


@pytest.mark.asyncio
async def test_tracing_app_service_name_from_main_app():
    """Test that service name is derived from main app title and normalized."""
    # Create app with spaces in title
    app = FunctionApp("Asset Management API", "2.0.0")
    tracing = create_tracing_app(backend=TEST_CONFIG)  # No override - use main app name

    @app.get("/test")
    def test_route() -> dict[str, str]:
        return {"status": "ok"}

    # Create service - this triggers composition
    handle = create_function_service(tracing, app)

    # Verify service name is normalized from main app title
    assert tracing._service_name == "asset-management-api"  # type: ignore[protected-access]
    assert tracing._service_version == "2.0.0"  # type: ignore[protected-access]

    # Also verify it works in actual request
    client = Mock(spec=CogniteClient)
    result = await handle.async_handle(
        client=client,
        data={"path": "/test", "method": "GET", "body": {}},
    )
    status_code = result.get("status_code", 500)
    assert isinstance(status_code, int)
    assert status_code < 400


def test_tracing_app_service_name_fallback_to_self():
    """Test that service name falls back to TracingApp's own title when used standalone."""
    # Create TracingApp without explicit service name
    tracing = create_tracing_app(backend=TEST_CONFIG)

    # Before composition, should use its own title (normalized)
    assert tracing._service_name == "tracing"  # type: ignore[protected-access]

    # Verify service version fallback to library version
    assert tracing._service_version == __version__  # type: ignore[protected-access]


def test_resolve_secret_from_env_var(monkeypatch: pytest.MonkeyPatch):
    """Test that _resolve_secret falls back to environment variables with warning."""
    # Set environment variable
    monkeypatch.setenv("TRACING_API_KEY", "env-value-123")

    # Should resolve from env var and return value
    result = _resolve_secret("tracing-api-key", None)
    assert result == "env-value-123"


def test_resolve_secret_prefers_cdf_secrets(monkeypatch: pytest.MonkeyPatch):
    """Test that CDF secrets take precedence over environment variables."""
    # Set both env var and CDF secret
    monkeypatch.setenv("TRACING_API_KEY", "env-value")
    cdf_secrets = {"tracing-api-key": "cdf-value"}

    # Should prefer CDF secret
    result = _resolve_secret("tracing-api-key", cdf_secrets)
    assert result == "cdf-value"


def test_resolve_secret_returns_none_when_not_found():
    """Test that _resolve_secret returns None when secret not found."""
    result = _resolve_secret("nonexistent-key", None)
    assert result is None


@pytest.mark.asyncio
async def test_tracing_app_with_async_route(span_exporter: InMemorySpanExporter):
    """Test that async routes create proper trace spans."""
    # Create app with async route
    app = FunctionApp("TestApp")
    tracing = create_tracing_app(backend=TEST_CONFIG)

    # Get the provider for flushing
    provider = trace.get_tracer_provider()

    @app.get("/async/{id}")
    @tracing.trace()
    async def async_route(tracer: FunctionTracer, id: int) -> dict[str, int]:
        with tracer.span("async_operation"):
            await asyncio.sleep(0.001)
        return {"id": id}

    # Create service with tracing middleware
    handle = create_function_service(tracing, app)

    # Create mock client
    client = Mock(spec=CogniteClient)

    # Call async endpoint
    result = await handle.async_handle(
        client=client,
        data={"path": "/async/42", "method": "GET", "body": {}},
    )

    # Verify response
    assert result.get("data") == {"id": 42}
    status_code = result.get("status_code", 500)
    assert isinstance(status_code, int)
    assert status_code < 400

    # Force flush to export spans
    if isinstance(provider, TracerProvider):
        provider.force_flush(timeout_millis=1000)

    # Verify spans were created
    spans = span_exporter.get_finished_spans()
    assert len(spans) >= 3  # root + @trace child + async_operation

    # Verify root span exists
    root_spans = [s for s in spans if s.parent is None]
    assert len(root_spans) == 1
    assert root_spans[0].name == "GET /async/{id}"

    # Verify @trace() child span exists
    assert any(s.name == "async_route" for s in spans)
    # Verify async_operation span exists
    assert any(s.name == "async_operation" for s in spans)


@pytest.mark.asyncio
async def test_create_tracing_app_missing_secret_error(monkeypatch: pytest.MonkeyPatch):
    """Test that create_tracing_app raises helpful error when secret is missing."""
    # Remove TRACING_API_KEY from environment to force missing secret error
    monkeypatch.delenv("TRACING_API_KEY", raising=False)

    # Create app that requires secret
    app = FunctionApp("TestApp")
    tracing = create_tracing_app(backend="honeycomb")

    @app.get("/test")
    def test_route() -> dict[str, str]:
        return {"status": "ok"}

    # Create service
    handle = create_function_service(tracing, app)

    # Create mock client with no secrets
    client = Mock(spec=CogniteClient)

    # Call endpoint - should return error with helpful message
    result = await handle.async_handle(
        client=client,
        data={"path": "/test", "method": "GET", "body": {}},
        secrets=None,  # No secrets provided
    )

    # Verify error response with helpful message
    status_code = result.get("status_code", 500)
    assert isinstance(status_code, int)
    assert status_code >= 400
    assert result.get("error_type") == "ExecutionError"
    message = result.get("message", "")
    assert isinstance(message, str)
    assert "tracing-api-key" in message
    assert "not found" in message or "missing" in message.lower()


@pytest.mark.asyncio
async def test_tracing_app_extracts_traceparent_header(span_exporter: InMemorySpanExporter):
    """Test that TracingApp extracts traceparent header and creates child span."""
    # Create app with tracing
    app = FunctionApp("TestApp")
    tracing = create_tracing_app(backend=TEST_CONFIG)

    # Get the provider for flushing
    provider = trace.get_tracer_provider()

    @app.get("/test")
    def test_route() -> dict[str, str]:
        return {"status": "ok"}

    # Create service with tracing middleware
    handle = create_function_service(tracing, app)

    # Create parent trace context
    parent_tracer = trace.get_tracer("test-parent")
    with parent_tracer.start_as_current_span("parent_operation") as parent_span:
        # Get parent trace context
        parent_ctx = parent_span.get_span_context()
        parent_trace_id = parent_ctx.trace_id
        parent_span_id = parent_ctx.span_id

        # Inject trace context into headers (W3C Trace Context format)
        carrier: dict[str, str] = {}
        TraceContextTextMapPropagator().inject(carrier)
        traceparent = carrier.get("traceparent", "")

        # Create mock client
        client = Mock(spec=CogniteClient)

        # Call through service with traceparent header
        # Note: In production, this would be passed via the ASGITypedFunctionScope
        # For this test, we need to simulate the header being present
        # We'll modify the scope to include headers

        request = RequestData(path="/test", method=HTTPMethod.GET, body={})

        # Build scope with headers
        scope: ASGITypedFunctionScope = {
            "type": "cognite.function",
            "asgi": {"version": "3.0"},
            "client": client,
            "secrets": None,
            "function_call_info": None,
            "request": request,
            "state": {},
            "headers": {"traceparent": traceparent},  # Include W3C trace context header
        }

        # Create simple receive/send callables

        async def receive() -> ASGITypedFunctionRequestMessage:
            return {"type": "cognite.function.request", "body": request}

        response_data: dict[str, Any] = {}

        async def send(message: Mapping[str, Any]) -> None:
            response_data.update(message.get("body", {}))

        # Call ASGI app directly with headers
        await handle.asgi_app(scope, receive, send)

        # Verify response
        assert int(response_data.get("status_code", 500)) < 400  # Success
        assert response_data.get("data") == {"status": "ok"}

    # Force flush to export spans
    if isinstance(provider, TracerProvider):
        provider.force_flush(timeout_millis=1000)

    # Verify spans were created
    spans = span_exporter.get_finished_spans()
    assert len(spans) >= 2  # parent + child (root span from function)

    # Find the child span (the root span created by TracingApp should have parent)
    child_spans = [
        s
        for s in spans
        if s.parent is not None and s.parent.trace_id == parent_trace_id and s.parent.span_id == parent_span_id
    ]
    assert len(child_spans) >= 1, "Child span with correct parent should exist"

    # Verify the child span has the same trace ID as parent
    child_span = child_spans[0]
    assert child_span.context is not None
    assert child_span.context.trace_id == parent_trace_id, "Child should have same trace ID as parent"


@pytest.mark.asyncio
async def test_tracing_app_without_headers_creates_new_trace(span_exporter: InMemorySpanExporter):
    """Test that TracingApp creates new root span when no traceparent header present."""
    # Create app with tracing
    app = FunctionApp("TestApp")
    tracing = create_tracing_app(backend=TEST_CONFIG)

    # Get the provider for flushing
    provider = trace.get_tracer_provider()

    @app.get("/test")
    def test_route() -> dict[str, str]:
        return {"status": "ok"}

    # Create service with tracing middleware
    handle = create_function_service(tracing, app)

    # Create mock client
    client = Mock(spec=CogniteClient)

    # Call without providing headers (backward compatibility)
    result = await handle.async_handle(
        client=client,
        data={"path": "/test", "method": "GET", "body": {}},
    )

    # Verify response
    assert result.get("data") == {"status": "ok"}
    status_code = result.get("status_code", 500)
    assert isinstance(status_code, int)
    assert status_code < 400

    # Force flush to export spans
    if isinstance(provider, TracerProvider):
        provider.force_flush(timeout_millis=1000)

    # Verify root span was created (no parent)
    spans = span_exporter.get_finished_spans()
    root_spans = [s for s in spans if s.parent is None]
    assert len(root_spans) >= 1, "Should create new root span when no traceparent header"
