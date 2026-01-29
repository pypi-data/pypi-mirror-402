"""Test configuration and fixtures for cognite-function-apps tests."""

import inspect
import os

# Mock the cognite_function_apps imports since we can't use relative imports in tests
import sys
from collections.abc import Callable, Mapping
from typing import Any, get_type_hints
from unittest.mock import Mock

import pytest
from cognite.client import CogniteClient
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from cognite_function_apps.app import FunctionApp
from cognite_function_apps.convert import convert_arguments_to_typed_params
from cognite_function_apps.dependency_registry import create_default_registry
from cognite_function_apps.introspection import create_introspection_app
from cognite_function_apps.mcp import MCPApp, create_mcp_app
from cognite_function_apps.models import FunctionCallInfo
from cognite_function_apps.tracer import setup_global_tracer_provider


def convert_with_di(
    client: CogniteClient,
    func: Callable[..., Any],
    arguments: dict[str, Any],
    secrets: dict[str, str] | None = None,
    function_call_info: FunctionCallInfo | None = None,
) -> Mapping[str, object]:
    """Helper function that combines DI and conversion for testing."""
    # Get dependency registry and resolve dependencies
    registry = create_default_registry()
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)
    dependency_context = {
        "client": client,
        "secrets": secrets,
        "function_call_info": function_call_info,
    }
    dependencies = registry.resolve(sig, dependency_context)

    # Convert user-provided arguments
    converted_params = convert_arguments_to_typed_params(
        arguments,
        dependency_names=registry.get_dependency_param_names(sig),
        signature=sig,
        type_hints=type_hints,
    )

    # Merge and return
    return {**dependencies, **converted_params}


@pytest.fixture(scope="class")
def mock_client():
    """Mock CogniteClient for testing."""
    return Mock(spec=CogniteClient)


@pytest.fixture
def test_app() -> FunctionApp:
    """Clean FunctionApp instance for testing."""
    return FunctionApp(title="Test App", version="1.0.0")


@pytest.fixture
def introspection_app() -> FunctionApp:
    """Introspection app instance for testing."""
    return create_introspection_app()


@pytest.fixture
def mcp_app() -> MCPApp:
    """MCP app instance for testing."""
    return create_mcp_app("test-server")


# Test models for use in various tests
class TestItem(BaseModel):
    """Test item model."""

    name: str
    description: str | None = Field(default=None)
    price: float = Field(gt=0)
    tax: float | None = Field(default=None, ge=0)


class TestItemResponse(BaseModel):
    """Test item response model."""

    id: int
    item: TestItem
    total_price: float


@pytest.fixture
def test_item():
    """Sample test item."""
    return TestItem(name="Test Item", price=100.0, tax=10.0)


@pytest.fixture
def test_item_response():
    """Sample test item response."""
    item = TestItem(name="Test Item", price=100.0, tax=10.0)
    return TestItemResponse(id=1, item=item, total_price=110.0)


@pytest.fixture(scope="session", autouse=True)
def setup_tracer_provider():
    """Set up the global TracerProvider once for the entire test session.

    This fixture runs once at the start of the test session and configures
    the OpenTelemetry TracerProvider. Individual tests can add their own
    span processors to collect spans.

    This prevents the "TracerProvider is already configured" warning that
    would occur if multiple tests tried to set it up.
    """
    try:
        # Set up once with a dummy exporter (tests will add their own processors)
        exporter = InMemorySpanExporter()
        setup_global_tracer_provider(
            service_name="test-service",
            service_version="1.0.0",
            exporter=exporter,
        )
    except ImportError:
        # OpenTelemetry not installed, skip setup
        pass


@pytest.fixture
def span_exporter():
    """Provide an isolated InMemorySpanExporter for each test.

    This fixture creates a new InMemorySpanExporter and adds it to the
    global TracerProvider via a SimpleSpanProcessor (synchronous export).
    After the test completes, it removes the processor to keep tests isolated.

    Returns:
        InMemorySpanExporter: Exporter for collecting spans in the test
    """
    try:
        from opentelemetry import trace  # noqa: PLC0415
        from opentelemetry.sdk.trace import TracerProvider  # noqa: PLC0415
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor  # noqa: PLC0415
        from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter  # noqa: PLC0415

        provider = trace.get_tracer_provider()
        if not isinstance(provider, TracerProvider):
            # Provider not set up (OpenTelemetry optional dependency)
            yield None
            return

        # Create exporter and processor for this test
        # Use SimpleSpanProcessor for synchronous export (better for tests)
        exporter = InMemorySpanExporter()
        processor = SimpleSpanProcessor(exporter)

        # Add to provider
        provider.add_span_processor(processor)

        yield exporter

        # Clean up: shutdown processor to flush any remaining spans
        processor.shutdown()

    except ImportError:
        # OpenTelemetry not installed
        yield None
