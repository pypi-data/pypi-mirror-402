"""Core application framework with composable apps architecture.

Enterprise-grade framework for Cognite Functions with composable apps,
automatic validation, and built-in introspection capabilities.

This module provides the main FunctionApp class for building type-safe
Cognite Functions. It handles route registration, parameter validation,
automatic type conversion, and error handling. Multiple FunctionApp instances
can be composed together to create modular, reusable functionality.

Key Components:
    - FunctionApp: Main application class with route decorators (@app.get,
      @app.post, etc.)
    - Composable architecture: Multiple apps can be combined using
      create_function_service([app1, app2, app3])
    - Route handling: Automatic parameter extraction from URLs, query
      strings, and request bodies
    - Type safety: Automatic conversion and validation using Pydantic
      models and type hints
    - Error handling: Comprehensive error catching and formatting for
      Cognite Functions
    - Schema generation: OpenAPI-style documentation generation
    - Built-in extensions: MCP integration and introspection endpoints
    - Async support: Application endpoints can be sync or async functions

Example usage:
    ```python
    from cognite_function_apps import FunctionApp, create_function_service
    from cognite_function_apps.mcp import create_mcp_app
    from cognite_function_apps.introspection import create_introspection_app
    from pydantic import BaseModel

    # Main business logic app
    app = FunctionApp("My Function", "1.0.0")

    class ItemResponse(BaseModel):
        id: int
        name: str
        price: float

    @app.get("/items/{item_id}")
    def get_item(client, item_id: int) -> ItemResponse:
        # Function automatically gets typed parameters
        return ItemResponse(id=item_id, name="Widget", price=29.99)

    @app.get("/items/{item_id}/async")
    async def get_item_async(client, item_id: int) -> ItemResponse:
        # Async application endpoints are also supported
        result = await fetch_data_async(item_id)
        return ItemResponse(id=item_id, name=result.name, price=result.price)

    # Create composable extensions
    mcp_app = create_mcp_app("my-server")
    introspection_app = create_introspection_app()

    # Optionally expose routes via MCP
    @mcp_app.tool("Get item by ID")
    @app.get("/items/{item_id}")  # Can decorate the same function
    def get_item_mcp(client, item_id: int) -> ItemResponse:
        return get_item(client, item_id)

    # Compose all apps together (introspection first to see all apps)
    handle = create_function_service(introspection_app, mcp_app, app)
    ```

The framework supports:
- Path parameters: /items/{item_id}
- Query parameters: ?include_tax=true&category=electronics
- Request body parsing and validation
- Automatic type conversion based on function signatures
- Input/output model validation with Pydantic
- Composable apps architecture for modular functionality
- MCP (Model Context Protocol) integration
- Built-in introspection endpoints (/__health__, /__schema__, etc.)
- Pattern-based routing for advanced use cases
- Comprehensive error handling with structured responses
- Both sync and async application endpoints
"""

import asyncio
import inspect
from collections.abc import Callable, Coroutine, Mapping, Sequence
from functools import wraps
from typing import (
    Any,
    ParamSpec,
    TypeVar,
    cast,
    get_type_hints,
)

from cognite.client import CogniteClient
from pydantic import BaseModel, ValidationError

from ._version import __version__
from .convert import ConvertError, convert_arguments_to_typed_params
from .dependency_registry import DependencyRegistry, resolve_dependencies
from .models import (
    ASGIReceiveCallable,
    ASGISendCallable,
    ASGITypedFunctionScope,
    CogniteFunctionError,
    CogniteFunctionResponse,
    ConfigurationError,
    DataDict,
    FunctionCallInfo,
    HTTPMethod,
    NotAcceptableError,
    RequestData,
    Response,
    SecretsMapping,
    TypedResponse,
)
from .routing import PathParams, RouteInfo, Router

_P = ParamSpec("_P")  # , bound=RequestHandler, wait for Python 3.13)
_R = TypeVar("_R")


def cognite_error_handler(
    func: Callable[_P, Coroutine[Any, Any, DataDict | None]],
) -> Callable[_P, Coroutine[Any, Any, DataDict | None]]:
    """Decorator that handles common errors in async application endpoints.

    This decorator works with async functions and returns error dicts instead
    of raising exceptions. Both sync and async callers benefit from this
    centralized error handling.

    Supports functions that return DataDict | None (where None signals "no match").
    """

    @wraps(func)
    async def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> DataDict | None:
        try:
            return await func(*args, **kwargs)
        except NotAcceptableError as e:
            # Handle Accept header mismatch (406 Not Acceptable)
            return CogniteFunctionError(
                status_code=406,
                error_type="NotAcceptable",
                message=str(e),
                details={"available_content_types": list(e.available_types)},
            ).model_dump()
        except ValidationError as e:
            # Handle validation errors from Pydantic on the returned data
            return CogniteFunctionError(
                status_code=400,
                error_type="ValidationError",
                message=f"Input validation failed: {e.error_count()} error(s)",
                details={"errors": e.errors()},
            ).model_dump()
        except ConvertError as e:
            # Handle parameter conversion and validation errors on input data
            return CogniteFunctionError(
                status_code=400,
                error_type="ValidationError",
                message=f"Input validation failed: {e!s}",
                details={"exception_type": type(e).__name__},
            ).model_dump()
        except Exception as e:
            return CogniteFunctionError(
                status_code=500,
                error_type="ExecutionError",
                message=f"Function execution failed: {e!s}",
                details={"exception_type": type(e).__name__},
            ).model_dump()

    return wrapper


class FunctionApp:
    """Composable application for building Cognite Function services."""

    def __init__(
        self,
        title: str = "Function App",
        version: str = __version__,
    ):
        """Initialize the FunctionApp.

        Args:
            title: The title of the app.
            version: The version of the app.

        Note:
            The dependency registry is set by create_function_service() during
            composition. All apps in a composition share the same registry.
        """
        self.title = title
        self.version = version

        # Registry will be set by create_function_service()
        # Initialized to None to catch any attempts to use app before composition
        self.registry: DependencyRegistry | None = None

        # Next app in middleware chain (set by create_function_service during composition)
        self.next_app: FunctionApp | None = None

        self.router = Router()

    @property
    def downstream_apps(self) -> Sequence["FunctionApp"]:
        """Get all downstream apps by walking the next_app chain.

        Returns apps with lower priority (to the right in composition order).
        """
        apps: list[FunctionApp] = []
        current = self.next_app
        while current is not None:
            apps.append(current)
            current = current.next_app
        return apps

    @property
    def routes(self) -> dict[str, dict[HTTPMethod, list[RouteInfo]]]:
        """Get all routes registered with the app."""
        return self.router.routes

    @property
    def downstream_routes(self) -> dict[str, dict[HTTPMethod, list[RouteInfo]]]:
        """Get all routes from downstream apps by walking the next_app chain.

        Returns aggregated routes from apps with lower priority (to the right in composition order).
        """
        routes: dict[str, dict[HTTPMethod, list[RouteInfo]]] = {}
        for app in reversed(self.downstream_apps):
            for path, methods in app.routes.items():
                for method, route_infos in methods.items():
                    routes.setdefault(path, {}).setdefault(method, []).extend(route_infos)
        return routes

    @property
    def all_routes(self) -> Mapping[str, Mapping[HTTPMethod, Sequence[RouteInfo]]]:
        """Get all routes including current app and all downstream apps.

        Returns aggregated routes from this app and all downstream apps in the composition.
        Routes from downstream apps are included first, then routes from this app
        (allowing this app's routes to override downstream routes if needed).
        """
        # Merge downstream routes and own routes
        result: dict[str, dict[HTTPMethod, list[RouteInfo]]] = {}
        for path, methods in self.downstream_routes.items():
            for method, route_infos in methods.items():
                result.setdefault(path, {}).setdefault(method, []).extend(route_infos)
        for path, methods in self.routes.items():
            for method, route_infos in methods.items():
                result.setdefault(path, {}).setdefault(method, []).extend(route_infos)
        return result

    def on_compose(
        self,
        next_app: "FunctionApp | None",
        shared_registry: DependencyRegistry,
    ) -> None:
        """Called during app composition to configure the middleware chain.

        This method is called automatically during app composition and can be
        overridden by apps that need access to the next app in the chain.

        Args:
            next_app: Next app in the middleware chain (None if this is the last app)
            shared_registry: Shared dependency registry containing all dependencies
        """
        # Set the shared registry (apps can override to do additional setup)
        self.registry = shared_registry
        # Set the next app in the middleware chain
        self.next_app = next_app

    def extract_path_params(self, path: str) -> Sequence[str]:
        """Extract parameter names from path like /items/{item_id}."""
        return self.router.extract_path_params(path)

    def register_route(
        self,
        path: str,
        method: HTTPMethod,
        # We use Callable[..., Any] to support both sync and async application endpoints
        # The actual validation happens at runtime in execute_function_and_format_response
        func: Callable[..., Any],
        description: str = "",
        *,
        content_type: str = "application/json",
        accept: str | None = None,
        status_code: int = 200,
        cache_control: str | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> None:
        """Register a route with the app.

        Supports both sync and async application endpoints.

        Args:
            path: Route path pattern (e.g., "/items/{item_id}")
            method: HTTP method
            func: Handler function (sync or async)
            description: Human-readable description
            content_type: Response MIME type (default: application/json)
            accept: Accept header for content negotiation (None matches any)
            status_code: Default success status code (default: 200)
            cache_control: Cache-Control header value
            extra_headers: Additional custom response headers

        Note: Parameters are stored unfiltered in RouteInfo. Dependency filtering
        happens at execution time when the complete registry is available (after composition).
        """
        # Extract function signature for parameter inspection
        sig = inspect.signature(func)
        try:
            type_hints = get_type_hints(func)
        except (NameError, AttributeError):
            # Fallback for functions with type hints that can't be resolved
            # (e.g., adapter functions with JSONLike references)
            type_hints = {}

        # Dependency filtering is deferred to execution time when the complete
        # shared registry is available (after sub-apps have registered their dependencies)
        params = dict(sig.parameters)

        route_info = RouteInfo(
            path=path,
            method=method,
            endpoint=func,
            signature=sig,
            parameters=params,
            type_hints=type_hints,
            path_params=self.extract_path_params(path),
            description=description or func.__doc__ or f"{method} {path}",
            content_type=content_type,
            accept=accept,
            status_code=status_code,
            cache_control=cache_control,
            extra_headers=extra_headers,
        )

        self.router.register_route(path, method, route_info)

    @cognite_error_handler
    async def dispatch_request(
        self,
        request: RequestData,
        client: CogniteClient,
        scope: ASGITypedFunctionScope,
        secrets: SecretsMapping | None = None,
        function_call_info: FunctionCallInfo | None = None,
    ) -> DataDict | None:
        """Dispatch a request and return the response.

        This method enables flexible inter-app communication by allowing
        one app to dispatch requests to another app or to itself.

        Errors are automatically caught and converted to error response dicts
        by the cognite_error_handler decorator.

        Args:
            request: The request data containing path, method, body, and query parameters
            client: The Cognite client instance
            secrets: Optional secrets mapping (injected if the application endpoint declares it)
            function_call_info: Optional function call metadata (injected if the application endpoint declares it)
            scope: ASGI scope dict. Enriches scope["state"] with matched route info

        Returns:
            Response data dict (either success or error)
        """
        # Get request headers from scope for content negotiation and DI
        headers = scope.get("headers", {})
        accept_header = headers.get("accept")

        # Find matching route and extract path parameters (with content negotiation)
        route_match, path_params = self.router.find_matching_route(
            request.clean_path, request.method, accept=accept_header
        )

        if not route_match:
            # No route matched - return None to signal no match
            # (None is handled specially in __call__ for route chaining)
            return None

        # Enrich scope state with matched route path (write-once semantics)
        state = scope.get("state")
        if "matched_route_path" not in state:
            # Store the parameterized route template from the matched route
            state["matched_route_path"] = route_match.path

        # Prepare function arguments with validation and type coercion
        kwargs = self._prepare_function_arguments(
            client,
            route_match,
            request.body,
            request.query,
            path_params,
            secrets,
            function_call_info,
            headers=headers,
        )

        # Execute function and format response
        return await execute_function_and_format_response(route_match, kwargs)

    def _prepare_function_arguments(
        self,
        client: CogniteClient,
        route_match: RouteInfo,
        body: DataDict,
        query: Mapping[str, str | Sequence[str]],
        path_params: PathParams,
        secrets: SecretsMapping | None = None,
        function_call_info: FunctionCallInfo | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, object]:
        """Prepare and validate function arguments with type coercion and dependency injection.

        Uses cached signature and type hints from RouteInfo to avoid repeated introspection.

        Args:
            client: CogniteClient instance
            route_match: Matched route information
            body: Request body data
            query: Query parameters
            path_params: Extracted path parameters
            secrets: Optional secrets mapping
            function_call_info: Optional function call metadata
            headers: Optional request headers (for RequestHeaders dependency)

        Returns:
            Dictionary of arguments ready to pass to the function. We use object here
            since we cannot know the types of any injected dependencies.
        """
        # Ensure registry is set (should be set by create_function_service)
        if self.registry is None:
            raise ConfigurationError(
                "Registry not initialized. App must be composed with create_function_service() before use."
            )

        # Combine body, query, and path parameters
        all_params = {**body, **query, **path_params}

        func = route_match.endpoint

        # Resolve dependencies using the cached signature and type hints
        # Pass type_hints for PEP 563/649 compatibility (string/deferred annotations)
        dependencies = resolve_dependencies(
            func,
            client,
            secrets,
            function_call_info,
            self.registry,
            signature=route_match.signature,
            headers=headers,
            type_hints=route_match.type_hints,
        )

        # Convert user-provided arguments to typed parameters using cached signature and type hints
        converted_params = convert_arguments_to_typed_params(
            all_params,
            dependency_names=self.registry.get_dependency_param_names(route_match.signature),
            signature=route_match.signature,
            type_hints=route_match.type_hints,
        )

        # Merge dependencies and converted parameters
        return {**dependencies, **converted_params}

    def _create_route_decorator(
        self,
        method: HTTPMethod,
        path: str,
        *,
        content_type: str = "application/json",
        accept: str | None = None,
        status_code: int = 200,
        cache_control: str | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:
        """Create a route decorator for the specified HTTP method.

        Supports both sync and async application endpoints.

        Attaches _route_path and _route_method attributes to the function
        for tracing and observability purposes.
        """

        def decorator(
            func: Callable[_P, _R],
        ) -> Callable[_P, _R]:
            self.register_route(
                path,
                method,
                func,
                content_type=content_type,
                accept=accept,
                status_code=status_code,
                cache_control=cache_control,
                extra_headers=extra_headers,
            )
            # Attach route metadata to the function for tracing/observability
            setattr(func, "_route_path", path)
            setattr(func, "_route_method", method.value)
            return func

        return decorator

    def get(
        self,
        path: str,
        *,
        content_type: str = "application/json",
        accept: str | None = None,
        status_code: int = 200,
        cache_control: str | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:
        """Decorator for GET operations (data retrieval).

        Supports both sync and async endpoints.

        Args:
            path: Route path pattern (e.g., "/items/{item_id}")
            content_type: Response MIME type (default: application/json)
            accept: Accept header for content negotiation (None matches any)
            status_code: Default success status code (default: 200)
            cache_control: Cache-Control header value
            extra_headers: Additional custom response headers
        """
        return self._create_route_decorator(
            HTTPMethod.GET,
            path,
            content_type=content_type,
            accept=accept,
            status_code=status_code,
            cache_control=cache_control,
            extra_headers=extra_headers,
        )

    def post(
        self,
        path: str,
        *,
        content_type: str = "application/json",
        accept: str | None = None,
        status_code: int = 200,
        cache_control: str | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:
        """Decorator for POST operations (create/process).

        Supports both sync and async endpoints.

        Args:
            path: Route path pattern (e.g., "/items")
            content_type: Response MIME type (default: application/json)
            accept: Accept header for content negotiation (None matches any)
            status_code: Default success status code (default: 200, use 201 for Created)
            cache_control: Cache-Control header value
            extra_headers: Additional custom response headers
        """
        return self._create_route_decorator(
            HTTPMethod.POST,
            path,
            content_type=content_type,
            accept=accept,
            status_code=status_code,
            cache_control=cache_control,
            extra_headers=extra_headers,
        )

    def put(
        self,
        path: str,
        *,
        content_type: str = "application/json",
        accept: str | None = None,
        status_code: int = 200,
        cache_control: str | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:
        """Decorator for PUT operations (update/replace).

        Supports both sync and async endpoints.

        Args:
            path: Route path pattern (e.g., "/items/{item_id}")
            content_type: Response MIME type (default: application/json)
            accept: Accept header for content negotiation (None matches any)
            status_code: Default success status code (default: 200)
            cache_control: Cache-Control header value
            extra_headers: Additional custom response headers
        """
        return self._create_route_decorator(
            HTTPMethod.PUT,
            path,
            content_type=content_type,
            accept=accept,
            status_code=status_code,
            cache_control=cache_control,
            extra_headers=extra_headers,
        )

    def delete(
        self,
        path: str,
        *,
        content_type: str = "application/json",
        accept: str | None = None,
        status_code: int = 200,
        cache_control: str | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:
        """Decorator for DELETE operations.

        Supports both sync and async endpoints.

        Args:
            path: Route path pattern (e.g., "/items/{item_id}")
            content_type: Response MIME type (default: application/json)
            accept: Accept header for content negotiation (None matches any)
            status_code: Default success status code (default: 200, or 204 for No Content)
            cache_control: Cache-Control header value
            extra_headers: Additional custom response headers
        """
        return self._create_route_decorator(
            HTTPMethod.DELETE,
            path,
            content_type=content_type,
            accept=accept,
            status_code=status_code,
            cache_control=cache_control,
            extra_headers=extra_headers,
        )

    async def __call__(
        self,
        scope: ASGITypedFunctionScope,
        receive: ASGIReceiveCallable,
        send: ASGISendCallable,
    ) -> None:
        """ASGI interface for middleware composition.

        This enables apps to be composed as middleware chains where each app
        can wrap the next app in the chain, providing natural before/after hooks.

        Error handling is done by the @cognite_error_handler decorator on dispatch_request.

        Args:
            scope: ASGI scope containing request context (client, request, secrets, etc.).
                   Contains a 'state' dict that is shared by reference across all middleware layers.
            receive: ASGI receive callable (for future streaming support)
            send: ASGI send callable for sending the response

        Note:
            Apps should handle their routes and delegate to self.next_app if no route matches.
            The scope['state'] dict can be enriched with routing information for upstream middleware.
        """
        # Extract context from scope
        client = scope["client"]
        request = scope["request"]
        secrets = scope.get("secrets")
        function_call_info = scope.get("function_call_info")

        # Try to handle the request with this app's routes
        # dispatch_request is decorated with @cognite_error_handler, so it returns
        # error dicts instead of raising exceptions
        response = await self.dispatch_request(request, client, scope, secrets, function_call_info)

        if response is not None:
            # This app handled the request (or had an error)
            await send(
                {
                    "type": "cognite.function.response",
                    "body": response,
                }
            )
        elif self.next_app is not None:
            # Delegate to next app in chain
            await self.next_app(scope, receive, send)


async def call_endpoint(func: Callable[..., _R], **kwargs: Any) -> _R:
    """Call the endpoint decorated function, automatically handling both sync and async functions.

    Calls the application endpoint function, automatically handling both
    sync and async functions. Async functions are awaited directly,
    while sync functions are run on a thread pool to avoid blocking the
    event loop.

    Args:
        func: The application endpoint function to call (sync or async)
        **kwargs: Arguments to pass to the endpoint function

    Returns:
        The result from the function
    """
    if inspect.iscoroutinefunction(func):
        # Async endpoint - await it directly
        return await func(**kwargs)
    else:
        # Sync endpoint - run on thread pool to avoid blocking
        return await asyncio.to_thread(func, **kwargs)


def _build_response_headers(
    route_match: RouteInfo,
    response_status_code: int | None = None,
    response_cache_control: str | None = None,
    response_extra_headers: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Build response headers from route defaults and Response overrides.

    Args:
        route_match: Route info with default content_type, cache_control, extra_headers
        response_status_code: Optional status code from Response wrapper (unused for headers)
        response_cache_control: Optional cache_control from Response wrapper (overrides route default)
        response_extra_headers: Optional extra_headers from Response wrapper (merged with route defaults)

    Returns:
        Merged headers dictionary
    """
    headers: dict[str, str] = {"content-type": route_match.content_type}

    # Cache-Control: Response overrides route default
    cache_control = response_cache_control if response_cache_control is not None else route_match.cache_control
    if cache_control:
        headers["cache-control"] = cache_control

    # Extra headers: merge route defaults with Response overrides (Response wins on conflict)
    if route_match.extra_headers:
        for key, value in route_match.extra_headers.items():
            headers[key.lower()] = value
    if response_extra_headers:
        for key, value in response_extra_headers.items():
            headers[key.lower()] = value

    return headers


async def execute_function_and_format_response(
    route_match: RouteInfo,
    kwargs: Mapping[str, Any],  # This must be Any
) -> DataDict:
    """Execute the function and format the response.

    Supports both sync and async endpoints via the call_endpoint helper.
    Detects Response[T] wrappers and extracts data with custom status/headers.
    """
    func = route_match.endpoint
    result = await call_endpoint(func, **kwargs)

    # Check if result is a Response wrapper
    response_status_code: int | None = None
    response_cache_control: str | None = None
    response_extra_headers: Mapping[str, str] | None = None

    # Check if result is a Response wrapper and unwrap
    actual_result: TypedResponse | BaseModel
    if isinstance(result, Response):
        # Extract overrides from Response wrapper
        response_status_code = result.status_code
        response_cache_control = result.cache_control
        response_extra_headers = result.extra_headers
        # Unwrap the actual data (Response.data is generic _T)
        actual_result = cast(TypedResponse | BaseModel, result.data)  # type: ignore[reportUnknownMemberType]
    else:
        actual_result = result

    # Handle result conversion based on type
    # Use by_alias=True to ensure field aliases are used in serialization (e.g., schema not schema_)
    data: TypedResponse
    if isinstance(actual_result, BaseModel):
        data = cast(TypedResponse, actual_result.model_dump(by_alias=True))
    else:
        # actual_result is already TypedResponse
        data = actual_result  # type: ignore[reportAssignmentType]

    # Determine final status code: Response override > route default
    status_code = response_status_code if response_status_code is not None else route_match.status_code

    # Build headers
    headers = _build_response_headers(
        route_match,
        response_status_code=response_status_code,
        response_cache_control=response_cache_control,
        response_extra_headers=response_extra_headers,
    )

    return CogniteFunctionResponse(
        status_code=status_code,
        data=data,
        headers=headers,
    ).model_dump()
