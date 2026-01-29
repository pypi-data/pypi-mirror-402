"""Service layer for bridging Cognite Functions runtime with ASGI.

This module provides the FunctionService class that adapts between the
Cognite Functions runtime signature and the internal ASGI middleware
chain. It enables type-safe function execution with both synchronous and
asynchronous interfaces, facilitating optimal performance in development
server environments.

The service layer handles request parsing, ASGI scope construction, and
response capture while maintaining compatibility with the Cognite
Functions Handle protocol.
"""

import asyncio
from collections.abc import Awaitable, Callable, Coroutine, Mapping
from functools import wraps
from typing import Any, ParamSpec, TypeVar, cast

from cognite.client import CogniteClient
from pydantic import ValidationError as PydanticValidationError

from cognite_function_apps.app import FunctionApp
from cognite_function_apps.dependency_registry import DependencyRegistry, create_default_registry

from .models import (
    ASGIApp,
    ASGITypedFunctionRequestMessage,
    ASGITypedFunctionScope,
    CogniteFunctionError,
    DataDict,
    FunctionCallInfo,
    Json,
    RequestData,
    SecretsMapping,
)

P = ParamSpec("P")
T = TypeVar("T")


def handle_unhandled_exceptions(
    func: Callable[P, Coroutine[Any, Any, DataDict]],
) -> Callable[P, Coroutine[Any, Any, DataDict]]:
    """Decorator that catches unhandled exceptions and converts them to error responses.

    This provides a safety net for truly unexpected exceptions that escape
    the normal error handling flow. Expected/recoverable errors should be
    handled explicitly within the wrapped function.

    Args:
        func: Async function to wrap

    Returns:
        Wrapped function that returns CogniteFunctionError on unhandled exceptions
    """

    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> DataDict:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            return CogniteFunctionError(
                error_type="ExecutionError",
                message=f"Function execution failed with an unhandled exception: {e!s}",
                details={"exception_type": type(e).__name__},
            ).model_dump()

    return wrapper


class FunctionService:
    """Type-safe wrapper for Cognite Function services with ASGI support.

    This class provides both synchronous and asynchronous handle functions
    for Cognite Functions, enabling type-safe access to the async implementation
    for devserver optimization. It adapts between the Cognite Function signature
    and internal ASGI middleware architecture.

    The instance is callable and implements the Handle protocol for compatibility
    with the Cognite Functions runtime.

    Attributes:
        asgi_app: The internal ASGI app (middleware chain)
        async_handle: The async implementation for optimal devserver performance
    """

    def __init__(
        self,
        asgi_app: ASGIApp,
    ):
        """Initialize the FunctionService.

        Args:
            asgi_app: ASGI app (middleware chain)
        """
        self.asgi_app = asgi_app

    def _collect_all_routes(self) -> list[str]:
        """Collect all routes from all apps in the composition chain.

        Returns:
            List of all route paths across all composed apps
        """
        if not isinstance(self.asgi_app, FunctionApp):
            return []

        # Get all routes from current app and all downstream apps
        return list(self.asgi_app.all_routes.keys())

    @handle_unhandled_exceptions
    async def _run_asgi(
        self,
        client: CogniteClient,
        data: DataDict,
        secrets: SecretsMapping | None,
        function_call_info: FunctionCallInfo | None,
    ) -> DataDict:
        """Run ASGI app and capture response.

        Args:
            client: The Cognite client instance
            data: Request data containing path, method, and body
            secrets: Optional secrets mapping
            function_call_info: Optional function call metadata

        Returns:
            Response data dict
        """
        # Parse request (validation errors here won't be traced, but that's ok - see ASGI_ARCHITECTURE.md)
        # We need the cast here since Pydantic is doing the validation
        try:
            request = RequestData(**cast(dict[str, Any], data))
        except PydanticValidationError as e:
            # Basic request structure validation failed - return error
            return CogniteFunctionError(
                error_type="ValidationError",
                message=f"Invalid request structure: {e.error_count()} error(s)",
                details={"errors": e.errors()},
            ).model_dump()

        # Build ASGI scope
        # The state dict is shared by reference across all middleware layers
        state: dict[str, Any] = {}
        scope: ASGITypedFunctionScope = {
            "type": "cognite.function",
            "asgi": {"version": "3.0"},
            "client": client,
            "secrets": secrets,
            "function_call_info": function_call_info,
            "request": request,
            "state": state,
            "headers": request.headers,  # Headers from request data (e.g., for trace propagation)
        }

        # Response capture
        response_data: DataDict | None = None

        async def receive() -> ASGITypedFunctionRequestMessage:
            return {
                "type": "cognite.function.request",
                "body": request,
            }

        async def send(message: Mapping[str, Any]) -> None:
            nonlocal response_data
            if message.get("type") == "cognite.function.response":
                response_data = message.get("body")  # type: ignore[assignment]

        # Run ASGI app
        if self.asgi_app is None:
            return CogniteFunctionError(
                error_type="ConfigurationError",
                message="ASGI app not configured",
            ).model_dump()

        await self.asgi_app(scope, receive, send)

        if response_data is None:
            # Check if we have any FunctionApp in the chain
            if not isinstance(self.asgi_app, FunctionApp):
                return CogniteFunctionError(
                    error_type="ConfigurationError",
                    message="No FunctionApp configured in the middleware chain",
                    details={"hint": "Use create_function_service() with at least one FunctionApp"},
                ).model_dump()

            # No app in the chain handled the request - generate 404 with all available routes
            all_routes = self._collect_all_routes()
            return CogniteFunctionError(
                error_type="RouteNotFound",
                message=f"No route found for {request.method} {request.clean_path}",
                details={"available_routes": all_routes},
            ).model_dump()

        return response_data  # pyright: ignore[reportUnreachable]

    @property
    def async_handle(self) -> Callable[..., Awaitable[DataDict]]:
        """Get the async handle function.

        Returns:
            Async handle compatible with devserver
        """

        # New ASGI architecture - create handle that runs ASGI
        async def _handle(
            *,
            client: CogniteClient,
            data: DataDict,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
        ) -> DataDict:
            return await self._run_asgi(client, data, secrets, function_call_info)

        return _handle

    def __call__(
        self,
        *,
        client: CogniteClient,
        data: DataDict,
        secrets: SecretsMapping | None = None,
        function_call_info: FunctionCallInfo | None = None,
    ) -> Json:
        """Call the synchronous handle (Handle protocol implementation).

        This makes FunctionService callable and compatible with the Cognite
        Functions runtime expectations.

        Args:
            client: The Cognite client instance
            data: Request data containing path, method, and body
            secrets: Optional secrets mapping
            function_call_info: Optional function call metadata

        Returns:
            Response data dict
        """
        return asyncio.run(self._run_asgi(client, data, secrets, function_call_info))


def create_function_service(
    app: FunctionApp, *apps: FunctionApp, registry: DependencyRegistry | None = None
) -> FunctionService:
    """Create function service from single app or composed apps using ASGI middleware pattern.

    Apps are composed as middleware chains where each app can wrap the next app,
    providing natural before/after hooks. Apps are composed left-to-right, with
    the leftmost app being the outermost middleware (first to process requests).

    Args:
        app: The first FunctionApp in the composition chain (required).
        apps: Additional FunctionApp instances to compose (optional).
              For composed apps, endpoint routing flows through the middleware
              chain left-to-right, with each app able to intercept, handle, or
              delegate to the next app.
        registry: Optional shared dependency registry. If None, creates a default registry
                  with standard framework dependencies (client, secrets, logger, etc.).
                  All apps will share this registry for dependency injection.

    Returns:
        FunctionService handle instance compatible with Cognite Functions. May also be
        used asynchronously with the devserver.

    Example:
        # Simple usage with default dependencies
        handle = create_function_service(main_app)

        # Composed apps with default dependencies (middleware pattern)
        # Request flow: tracing → mcp → main_app
        handle = create_function_service(tracing_app, mcp_app, main_app)

        # Custom dependencies
        registry = create_default_registry()
        registry.register(lambda ctx: MyService(), target_type=MyService)
        handle = create_function_service(main_app, registry=registry)

    Note:
        Uses ASGI middleware architecture internally. Error handling happens
        in individual middleware (e.g., TracingApp wraps validation errors).
    """
    # Normalize to list - first app is mandatory, rest are optional
    app_list = [app, *apps]

    # Create or use provided registry
    shared_registry = registry if registry is not None else create_default_registry()

    # Provide composition context to apps (including shared registry and next_app chaining)
    _compose(app_list, shared_registry)

    # The first app in the list is the outermost middleware (entry point)
    outermost_app = app_list[0]

    # Return FunctionService with ASGI app
    return FunctionService(asgi_app=outermost_app)


def _compose(app_list: list[FunctionApp], shared_registry: DependencyRegistry) -> None:
    """Provide composition context to all apps in the composition.

    Following layered architecture principles, each app only sees downstream apps
    (lower priority apps to their right) through the next_app chain. Apps can use
    the downstream_apps and downstream_routes properties to walk the chain.

    Args:
        app_list: List of apps in composition order
        shared_registry: Shared dependency registry for all apps
    """
    # Iterate backwards so each app's downstream context is fully configured
    # when we call on_compose on it
    for i in range(len(app_list) - 1, -1, -1):
        app = app_list[i]
        next_app = app_list[i + 1] if i < len(app_list) - 1 else None
        app.on_compose(next_app, shared_registry)
