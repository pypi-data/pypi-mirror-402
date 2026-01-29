"""Tracing support for Cognite Functions using dependency injection.

This module provides tracing capabilities through dependency injection,
making it available as a standard parameter like client, logger, etc.

Architecture:
- TracerProvider is configured once at application startup (not per-request)
- OTLPSpanExporter sends traces to OpenTelemetry collector (e.g., LightStep)
- BatchSpanProcessor handles async export without blocking requests
- No per-request setup/teardown to avoid resource leaks
- Spans include cognite.call_id attribute for filtering/organization in backend

Note:
    Tracing support requires the optional 'tracing' dependencies:
    pip install cognite-function-apps[tracing]
"""

import inspect
import logging
import os
import re
import threading
import warnings
from collections.abc import Callable, Coroutine, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from functools import wraps
from typing import TYPE_CHECKING, Any, Literal, ParamSpec, TypedDict, TypeVar, cast, get_type_hints

from cognite_function_apps._version import __version__
from cognite_function_apps.app import FunctionApp
from cognite_function_apps.dependency_registry import DependencyRegistry, resolve_dependencies
from cognite_function_apps.models import (
    ASGIReceiveCallable,
    ASGISendCallable,
    ASGITypedFunctionResponseMessage,
    ASGITypedFunctionScope,
    DataDict,
)

logger = logging.getLogger(__name__)

# Make sure this is short enough to avoid blocking the function execution, but long enough to ensure the spans are
# exported before the function instance is recycled.
FLUSH_TIMEOUT_MS = 500


@dataclass(kw_only=True)
class TracingConfig:
    """Configuration for OTLP tracing backend."""

    endpoint: str
    """OTLP endpoint URL (e.g., "https://api.honeycomb.io:443")"""
    header_name: str | None = None
    """Header name for API key authentication (e.g., "x-honeycomb-team")"""
    secret_key: str | None = None
    """CDF secret key for API key (e.g., "tracing-api-key")"""
    docs_url: str | None = None
    """Optional URL to documentation for obtaining the API key"""


# Backend presets for popular OTLP services
OTLP_BACKENDS: Mapping[str, TracingConfig] = {
    "honeycomb": TracingConfig(
        endpoint="https://api.honeycomb.io:443",
        header_name="x-honeycomb-team",
        secret_key="tracing-api-key",
        docs_url="https://docs.honeycomb.io/get-started/configure/environments/manage-api-keys/",
    ),
    "lightstep": TracingConfig(
        endpoint="https://ingest.lightstep.com:443",
        header_name="lightstep-access-token",
        secret_key="tracing-api-key",
        docs_url="https://docs.lightstep.com/docs/create-and-manage-access-tokens",
    ),
}

BackendType = Literal["honeycomb", "lightstep"]


def _resolve_secret(secret_key: str, secrets: Mapping[str, str] | None) -> str | None:
    """Resolve secret from CDF secrets or environment variables (with warning)."""
    # Try CDF secrets first (preferred)
    if secrets and (value := secrets.get(secret_key)):
        logger.info(f"Using {secret_key} from CDF secrets")
        return value

    # Fall back to environment variables (warn with actionable guidance)
    env_key = secret_key.upper().replace("-", "_")
    if value := os.getenv(env_key):
        logger.warning(
            f"Using {secret_key} from environment variable {env_key}. "
            f"For production, add as a CDF secret:\n"
            f"  Python SDK: client.functions.create(..., secrets={{'{secret_key}': 'your-key'}})\n"
            f"  Toolkit: Add to <function-name>.Function.yaml:\n"
            f"           secrets:\n"
            f"             {secret_key}: ${{YOUR_API_KEY_ENV_VAR}}"
        )
        return value

    return None


def _normalize_service_name(name: str) -> str:
    """Normalize service name to lowercase-with-hyphens for OpenTelemetry conventions."""
    return re.sub(r"[\s_]+", "-", name).strip("-").lower() or "cognite-function-apps"


# Try to import OpenTelemetry dependencies
_has_opentelemetry = True
try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.propagate import extract
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider as SdkTracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter
    from opentelemetry.trace import ProxyTracerProvider, Status, StatusCode
except ImportError:
    _has_opentelemetry = False
    if not TYPE_CHECKING:
        # Provide stubs for runtime when OpenTelemetry is not installed
        def extract(*args: Any, **kwargs: Any) -> None:  # type: ignore[misc]
            """No-op stub for extract when OpenTelemetry is not installed."""
            return None

        trace = None  # type: ignore[assignment]
        OTLPSpanExporter = Any  # type: ignore[assignment]
        Resource = Any  # type: ignore[assignment]
        SdkTracerProvider = Any  # type: ignore[assignment]
        BatchSpanProcessor = Any  # type: ignore[assignment]
        SpanExporter = Any  # type: ignore[assignment]
        ProxyTracerProvider = Any  # type: ignore[assignment]
        SpanKind = Any  # type: ignore[assignment]
        Status = Any  # type: ignore[assignment]
        StatusCode = Any  # type: ignore[assignment]

if TYPE_CHECKING:
    # Always import for type checking
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.propagate import extract
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider as SdkTracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter
    from opentelemetry.trace import ProxyTracerProvider, Status, StatusCode

_P = ParamSpec("_P")
_R = TypeVar("_R")


class _ResponseState(TypedDict):
    """Internal response state for tracing."""

    has_started: bool
    body: DataDict | None


class FunctionTracer:
    """Tracer for Cognite Functions with OpenTelemetry integration.

    Provides a simple interface for creating traced spans that are automatically
    exported to an OpenTelemetry collector (e.g., LightStep, Jaeger, etc.).
    """

    def __init__(self, tracer: "trace.Tracer") -> None:
        """Initialize the FunctionTracer."""
        if not _has_opentelemetry:
            raise ImportError(
                "Tracing support requires OpenTelemetry. Install it with: pip install cognite-function-apps[tracing]"
            )
        self.tracer = tracer

    @contextmanager
    def span(self, name: str):
        """Create a traced span context."""
        with self.tracer.start_as_current_span(name) as span:
            # Explicitly set operation name as an attribute for better visibility in backends
            span.set_attribute("operation.name", name)
            try:
                yield span
                span.set_status(Status(StatusCode.OK))
            except Exception:
                # Re-raise to allow the OpenTelemetry context manager to handle it.
                # It will set the status to ERROR and record the exception with a stack trace.
                raise


def setup_global_tracer_provider(
    *,
    service_name: str,
    service_version: str,
    exporter: "SpanExporter",
) -> "trace.TracerProvider":
    """Set up global TracerProvider with custom SpanExporter.

    This is called once at application startup to configure OpenTelemetry
    for the lifetime of the function worker.

    This function is idempotent - calling it multiple times is safe and will
    return the existing provider if already configured.

    Args:
        service_name: Service name for trace identification
        service_version: Service version
        exporter: SpanExporter instance (e.g., OTLPSpanExporter)

    Returns:
        The configured TracerProvider instance

    Raises:
        ImportError: If OpenTelemetry is not installed
    """
    if not _has_opentelemetry:
        raise ImportError(
            "Tracing support requires OpenTelemetry. Install it with: pip install cognite-function-apps[tracing]"
        )

    # Check if already configured
    existing_provider = trace.get_tracer_provider()
    if not isinstance(existing_provider, ProxyTracerProvider):
        # Already configured, log a warning and return existing provider.
        warnings.warn("TracerProvider is already configured. Subsequent configurations will be ignored.")
        return existing_provider  # type: ignore[return-value]

    # Create resource with service identification
    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": service_version,
        }
    )

    # Create and configure new provider with resource
    tracer_provider = SdkTracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)

    batch_processor = BatchSpanProcessor(exporter)
    tracer_provider.add_span_processor(batch_processor)

    return tracer_provider  # type: ignore[return-value]


class TracingApp(FunctionApp):
    """Tracing middleware that creates root spans for every request.

    Use create_tracing_app() instead of instantiating this class directly.
    """

    # Parameter name for tracer dependency injection
    # This must match the DI registration for consistent behavior
    # Can be overridden in subclasses for custom naming conventions
    tracer_param_name: str = "tracer"

    def __init__(
        self,
        *,
        _exporter_provider: Callable[..., "SpanExporter"],
        service_name: str | None = None,
        service_version: str | None = None,
    ) -> None:
        """Initialize TracingApp (internal - use create_tracing_app() instead).

        Args:
            _exporter_provider: Function returning SpanExporter. Can use DI for secrets.
            service_name: Service name. Defaults to main app title.
            service_version: Service version. Defaults to main app version.
        """
        if not _has_opentelemetry:
            raise ImportError(
                "Tracing support requires OpenTelemetry. Install it with: pip install cognite-function-apps[tracing]"
            )

        super().__init__(title="Tracing", version=__version__)

        # Store service name/version for later use
        # If None, will be pulled from main app during composition
        self._service_name_override = service_name
        self._service_version_override = service_version

        # Store for accessing main app metadata
        self.main_app: FunctionApp | None = None

        # Store exporter provider for lazy initialization on first request
        self._exporter_provider = _exporter_provider
        self._initialization_lock = threading.Lock()
        self._initialized = False

        # Get tracer for use in __call__
        self._tracer = trace.get_tracer(__name__)

    @property
    def _service_name(self) -> str:
        """Get the service name, falling back to main app title if not overridden.

        Service names are normalized to follow OpenTelemetry conventions:
        lowercase with hyphens instead of spaces/underscores.
        """
        match (self._service_name_override, self.main_app):
            # Explicit override provided - highest priority
            case (str(name), _):
                raw_name = name
            # No override, use main app's title from composition
            case (None, FunctionApp(title=title)):
                raw_name = title
            # Fallback to this tracing app's title (standalone mode)
            case _:
                raw_name = self.title
        return _normalize_service_name(raw_name)

    @property
    def _service_version(self) -> str:
        """Get the service version, falling back to main app version if not overridden."""
        if self._service_version_override is not None:
            return self._service_version_override
        if self.main_app is not None:
            return self.main_app.version
        # Fallback to TracingApp's own version when used standalone
        return self.version

    def on_compose(
        self,
        next_app: FunctionApp | None,
        shared_registry: DependencyRegistry,
    ) -> None:
        """Register FunctionTracer dependency and determine main app for metadata."""
        # Set registry first (call parent implementation)
        super().on_compose(next_app, shared_registry)

        # Determine main app (last app in composition) for metadata
        app_list = [self, *self.downstream_apps]
        self.main_app = app_list[-1] if app_list else self

        # Register the tracer dependency in the shared registry
        if self.registry is None:
            raise ValueError("Registry is not set")

        self.registry.register(
            provider=lambda ctx: FunctionTracer(trace.get_tracer(__name__)),
            target_type=FunctionTracer,
            param_name=self.tracer_param_name,
            description="OpenTelemetry function tracer with OTLP export",
        )

    def _set_span_status_from_response(
        self,
        root_span: Any,
        response_state: _ResponseState,
    ) -> None:
        """Set span status and attributes based on response state."""
        # No response sent - assume success
        if not response_state["has_started"]:
            root_span.set_attribute("http.status_code", 200)
            root_span.set_status(Status(StatusCode.OK))
            return

        response_body = response_state["body"]
        if not response_body:
            root_span.set_attribute("http.status_code", 200)
            root_span.set_status(Status(StatusCode.OK))
            return

        # Check if response indicates an error
        error_type = response_body.get("error_type")
        if not error_type:
            # Success response
            root_span.set_attribute("http.status_code", 200)
            root_span.set_status(Status(StatusCode.OK))
            return

        # Error response
        root_span.set_attribute("error", True)
        root_span.set_attribute("error.type", str(error_type))
        root_span.set_attribute("http.status_code", 500)
        error_message = response_body.get("message", "Error")
        root_span.set_status(Status(StatusCode.ERROR, str(error_message)))

    def _initialize_tracer_provider_if_needed(self, scope: ASGITypedFunctionScope) -> None:
        """Initialize tracer provider on first request (thread-safe)."""
        # Fast path: already initialized
        if self._initialized:
            return

        # Slow path: need to initialize
        with self._initialization_lock:
            # Double-check after acquiring lock
            if self._initialized:
                return

            # Ensure registry is available
            if self.registry is None:
                raise ValueError("Registry not initialized. App must be composed before use.")

            # Extract context for DI resolution
            client = scope["client"]
            secrets = scope.get("secrets")
            function_call_info = scope.get("function_call_info")

            # Resolve dependencies for exporter_provider
            dependencies = resolve_dependencies(
                self._exporter_provider,
                client,
                secrets,
                function_call_info,
                self.registry,
            )

            # Call exporter_provider to get the exporter
            exporter = self._exporter_provider(**dependencies)

            # Set up global tracer provider with the custom exporter
            setup_global_tracer_provider(
                service_name=self._service_name,
                service_version=self._service_version,
                exporter=exporter,
            )

            # Mark as initialized IMMEDIATELY after successful setup
            # This prevents retry attempts even if subsequent operations fail
            self._initialized = True

            # Update tracer reference (provider has changed)
            self._tracer = trace.get_tracer(__name__)

    def _force_flush_spans(self) -> None:
        """Force flush spans in background thread (fire-and-forget, best-effort)."""

        def _flush() -> None:
            try:
                tracer_provider = trace.get_tracer_provider()
                if isinstance(tracer_provider, SdkTracerProvider):
                    # Flush with short timeout to avoid blocking response
                    # 500ms is a reasonable compromise: long enough for most spans to export,
                    # short enough to avoid Azure Functions lifecycle issues
                    tracer_provider.force_flush(timeout_millis=FLUSH_TIMEOUT_MS)

            except Exception as e:
                error_msg = str(e).lower()
                is_auth_error = any(
                    word in error_msg for word in ("403", "401", "unauthorized", "forbidden", "unauthenticated")
                )
                logger.error(
                    f"Failed to flush trace spans: {e}"
                    + (
                        "\nInvalid 'tracing-api-key'? Check that your key is valid, not expired or revoked."
                        if is_auth_error
                        else ""
                    )
                )

        thread = threading.Thread(target=_flush, daemon=True)
        thread.start()

    async def __call__(
        self,
        scope: ASGITypedFunctionScope,
        receive: ASGIReceiveCallable,
        send: ASGISendCallable,
    ) -> None:
        """ASGI interface with automatic root span creation around request lifecycle."""
        from opentelemetry.trace import SpanKind  # noqa: PLC0415

        # Initialize tracer provider if using lazy initialization
        self._initialize_tracer_provider_if_needed(scope)

        # Extract request metadata from scope
        request = scope.get("request")
        function_call_info = scope.get("function_call_info")

        # Extract trace context from incoming headers (W3C Trace Context propagation)
        headers = scope.get("headers", {})
        parent_context = extract(headers) if headers else None

        # Determine span name from request
        if request:
            # Start with a low-cardinality name; will be updated with the route template later.
            span_name = request.method
        else:
            span_name = "cognite.function.request"

        # Create root span with SERVER kind for HTTP request handlers
        # If parent_context is provided, the span will be created as a child of that context
        with self._tracer.start_as_current_span(span_name, kind=SpanKind.SERVER, context=parent_context) as root_span:
            # Set HTTP and request attributes
            root_span.set_attribute("operation.name", span_name)
            if request:
                root_span.set_attribute("http.method", request.method)
                root_span.set_attribute("http.url", request.path)
                # Note: http.route will be set after routing completes by reading
                # from scope["state"]["matched_route_path"] (set by FunctionApp during dispatch)

            # Set Cognite-specific metadata if available (skip None values)
            if function_call_info:
                if function_id := function_call_info.get("function_id"):
                    root_span.set_attribute("cognite.function_id", function_id)
                if call_id := function_call_info.get("call_id"):
                    root_span.set_attribute("cognite.call_id", call_id)
                if schedule_id := function_call_info.get("schedule_id"):
                    root_span.set_attribute("cognite.schedule_id", schedule_id)
                if scheduled_time := function_call_info.get("scheduled_time"):
                    root_span.set_attribute("cognite.scheduled_time", scheduled_time)

            # Track response state - fail on multiple sends
            response_state: _ResponseState = {
                "has_started": False,
                "body": None,
            }

            # Wrap send to capture response
            async def wrapped_send(message: ASGITypedFunctionResponseMessage) -> None:
                body = message["body"]
                # Enforce single response rule
                if response_state["has_started"]:
                    raise RuntimeError(
                        "Response has already been sent. "
                        "Multiple response sends are not allowed in the middleware chain."
                    )
                response_state["has_started"] = True
                response_state["body"] = body

                await send(message)

            try:
                # Call parent which handles dispatch_request and next_app delegation
                await super().__call__(scope, receive, wrapped_send)

                # Update http.route with matched route template from scope state (if available)
                # This is set by FunctionApp after successful routing
                state = scope.get("state", {})
                if (matched_route_path := state.get("matched_route_path")) is not None:
                    root_span.set_attribute("http.route", matched_route_path)
                    if request:
                        root_span.update_name(f"{request.method} {matched_route_path}")

                # Set span status based on response
                self._set_span_status_from_response(root_span, response_state)

            except Exception:
                # Catch any unhandled exceptions (shouldn't happen with cognite_error_handler, but be defensive)
                # Re-raise to allow the OpenTelemetry context manager to handle it.
                # It will set the status to ERROR and record the exception with a stack trace.
                root_span.set_attribute("error", True)
                root_span.set_attribute("http.status_code", 500)
                raise
            finally:
                # Force flush traces after sending response to ensure spans are exported
                # before context is lost (especially important in serverless environments).
                # Uses short timeout to avoid blocking or impacting function lifecycle.
                self._force_flush_spans()

    def trace(self, span_name: str | None = None) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:
        """Decorator to create a child span with handler metadata (optional for granular tracing)."""

        def decorator(func: Callable[_P, _R]) -> Callable[_P, _R]:
            # Get route info from function metadata if set by @app.get/post decorators
            route_path = getattr(func, "_route_path", None)
            route_method = getattr(func, "_route_method", None)

            # Determine span name
            if span_name:
                effective_span_name = span_name
            else:
                effective_span_name = func.__name__

            # Check if function declares the tracer parameter
            # Uses strict name AND type matching to align with DI semantics
            sig = inspect.signature(func)
            param = sig.parameters.get(self.tracer_param_name)

            # Early exit if tracer parameter not declared with correct type
            # Use get_type_hints for PEP 563/649 compatibility (string/deferred annotations)
            if not param:
                return func
            try:
                hints = get_type_hints(func)
                resolved_type = hints.get(self.tracer_param_name)
            except (NameError, AttributeError):
                # Fallback to param.annotation if type hints can't be resolved
                resolved_type = param.annotation
            if resolved_type != FunctionTracer:
                return func

            def _update_root_span_with_route() -> None:
                """Update root span with route template for proper http.route semantics.

                Must be called before creating child span so get_current_span()
                returns the root span, not the child span.
                """
                if route_path and _has_opentelemetry:
                    root_span = trace.get_current_span()
                    if root_span and root_span.is_recording():
                        root_span.set_attribute("http.route", route_path)

            def _setup_span_attributes(child_span: Any) -> None:
                """Set up child span attributes with function-level metadata."""
                # Add operation name to child span
                child_span.set_attribute("operation.name", effective_span_name)

                # Add function metadata to child span
                child_span.set_attribute("function.name", func.__name__)

                # Add HTTP metadata to child span if available
                if route_path:
                    child_span.set_attribute("http.route", route_path)
                if route_method:
                    child_span.set_attribute("http.method", route_method)

            @wraps(func)
            def sync_wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                # Get tracer using configured parameter name
                tracer: FunctionTracer | None = cast(FunctionTracer | None, kwargs.get(self.tracer_param_name))

                if not tracer or not _has_opentelemetry:
                    # No tracer available or OpenTelemetry not installed, execute normally
                    return func(*args, **kwargs)

                # Update root span with route template before creating child span
                _update_root_span_with_route()

                # Create child span (inherits from root span created in __call__)
                with tracer.tracer.start_as_current_span(effective_span_name) as child_span:
                    _setup_span_attributes(child_span)
                    try:
                        result = func(*args, **kwargs)
                        child_span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception:
                        # Re-raise to allow the OpenTelemetry context manager to handle it.
                        # It will set the status to ERROR and record the exception with a stack trace.
                        child_span.set_attribute("error", True)
                        raise

            @wraps(func)
            async def async_wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                # Get tracer using configured parameter name
                tracer: FunctionTracer | None = cast(FunctionTracer | None, kwargs.get(self.tracer_param_name))
                _func = cast(Callable[..., Coroutine[Any, Any, _R]], func)

                if not tracer or not _has_opentelemetry:
                    # No tracer available or OpenTelemetry not installed, execute normally
                    return await _func(*args, **kwargs)

                # Update root span with route template before creating child span
                _update_root_span_with_route()

                # Create child span (inherits from root span created in __call__)
                with tracer.tracer.start_as_current_span(effective_span_name) as child_span:
                    _setup_span_attributes(child_span)
                    try:
                        result = await _func(*args, **kwargs)
                        child_span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception:
                        # Re-raise to allow the OpenTelemetry context manager to handle it.
                        # It will set the status to ERROR and record the exception with a stack trace.
                        child_span.set_attribute("error", True)
                        raise

            # Return appropriate wrapper based on function type
            if inspect.iscoroutinefunction(func):
                return async_wrapper  # type: ignore[return-value]
            else:
                return sync_wrapper  # type: ignore[return-value]

        return decorator


def create_tracing_app(
    backend: BackendType | TracingConfig,
) -> TracingApp:
    """Create a TracingApp with automatic backend configuration.

    Args:
        backend: Backend preset ("honeycomb", "lightstep") or custom TracingConfig.

    Examples:
        # Production with Honeycomb (reads tracing-api-key from CDF secrets)
        tracing = create_tracing_app(backend="honeycomb")

        # Local dev (reads TRACING_API_KEY env var with warning)
        tracing = create_tracing_app(backend="honeycomb")

        # Custom backend (e.g., Jaeger for local dev)
        tracing = create_tracing_app(
            backend=TracingConfig(
                endpoint="http://localhost:4317",
                header_name=None,
                secret_key=None,
                docs_url=None,
            )
        )
    """
    # Resolve backend config
    if isinstance(backend, str):
        config = OTLP_BACKENDS[backend]
        backend_name = backend
    else:
        config = backend
        backend_name = "custom"

    # Create exporter provider that resolves secrets automatically
    def _create_exporter(secrets: Mapping[str, str] | None = None) -> "SpanExporter":
        # Early return if no auth configuration
        if not (config.header_name and config.secret_key):
            return OTLPSpanExporter(endpoint=config.endpoint)

        secret_value = _resolve_secret(config.secret_key, secrets)
        if secret_value:
            headers = {config.header_name: secret_value}
            return OTLPSpanExporter(endpoint=config.endpoint, headers=headers)

        # Build dynamic error message for missing secret
        env_key = config.secret_key.upper().replace("-", "_")
        error_parts = [
            f"Secret '{config.secret_key}' not found in CDF secrets or environment variables.",
        ]

        # Add backend-specific docs URL if available
        if config.docs_url:
            error_parts.append(f"\nTo get your {backend_name.title()} API key:\n  See: {config.docs_url}")

        # Add local dev instructions
        error_parts.append(f"\nFor local development:\n  Create .env file: {config.secret_key}=your-api-key-here")

        # Add production deployment instructions
        error_parts.append(
            f"\nFor production deployment:\n"
            f"  Python SDK: client.functions.create(..., secrets={{'{config.secret_key}': 'your-key'}})\n"
            f"  Toolkit: Add to <function-name>.Function.yaml:\n"
            f"           secrets:\n"
            f"             {config.secret_key}: ${{{env_key}}}"
        )

        raise ValueError("".join(error_parts))

    return TracingApp(_exporter_provider=_create_exporter)
