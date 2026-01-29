"""Route matching and management for Cognite Functions.

This module contains all routing logic, separated from the main FunctionApp
to follow the Single Responsibility Principle. The Router class handles:
- Route storage and sorting
- Path parameter extraction and matching
- Route lookup and selection

This separation makes the code more testable, reusable, and maintainable.
"""

import inspect
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, NewType, TypeAlias

from .models import ConfigurationError, HTTPMethod, NotAcceptableError, TypedResponse

# Type aliases for routing
PathParams: TypeAlias = Mapping[str, str]

# MIME type pattern following RFC 6838
# - Character set !#$&\-^_.+ matches restricted-name-chars
# - Requires alphanumeric first character
# - Accepts vendor types (e.g., application/vnd.api+json, x-custom/format)
# - Permissive on parameters (;.*) since we're catching developer mistakes at registration,
#   not sanitizing untrusted input. Stricter validation would be: (;\s*[a-zA-Z0-9\-]+=\S+)*
# Matches: application/json, text/html, text/plain; charset=utf-8, application/vnd.api+json
_MIME_TYPE_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9!#$&\-^_.+]*/[a-zA-Z0-9][a-zA-Z0-9!#$&\-^_.+]*(;.*)?$")


def _validate_mime_type(mime_type: str, field_name: str) -> None:
    """Validate that a string is a valid MIME type.

    Validates MIME types at route registration time (developer-provided values).
    Follows RFC 6838 for type/subtype format. Intentionally permissive on:
    - Primary types (accepts vendor types like 'banana/json', 'x-custom/format')
    - Parameters (accepts any text after semicolon for simplicity)

    This is appropriate for catching developer typos at registration, not for
    sanitizing untrusted user input.

    Args:
        mime_type: The MIME type string to validate
        field_name: Name of the field for error messages (e.g., 'content_type', 'accept')

    Raises:
        ConfigurationError: If the MIME type is invalid
    """
    if not _MIME_TYPE_PATTERN.match(mime_type):
        raise ConfigurationError(
            f"Invalid {field_name}: '{mime_type}'. "
            f"Expected format: type/subtype (e.g., 'application/json', 'text/html')"
        )


@dataclass
class RouteInfo:
    """Information about a registered route in FunctionApp."""

    path: str
    """The route path pattern (e.g., /items/{item_id})"""
    method: HTTPMethod
    """HTTPMethod value"""
    endpoint: Callable[..., TypedResponse]
    """The actual callable decorated application endpoint for this route"""

    signature: inspect.Signature
    """Function's signature obtained from inspect.signature()"""
    parameters: Mapping[str, inspect.Parameter]
    """Parameter names mapped to Parameter objects"""
    type_hints: Mapping[str, Any]
    """Type annotations for the function parameters"""
    path_params: Sequence[str]
    """List of path parameter names extracted from the route pattern"""
    description: str
    """Human-readable description of what this route does"""

    # Response customization fields
    content_type: str = "application/json"
    """Response MIME type (default: application/json)"""
    accept: str | None = None
    """Accept header value for content negotiation (None matches any)"""
    status_code: int = 200
    """Default success status code"""
    cache_control: str | None = None
    """Cache-Control header value"""
    extra_headers: Mapping[str, str] | None = None
    """Additional custom response headers"""


# NewType for type-safe sorted routes - ensures find_matching_route only accepts properly sorted routes
# Changed to support multiple routes per path/method with different accept headers
SortedRoutes = NewType("SortedRoutes", Sequence[tuple[str, Mapping[HTTPMethod, Sequence[RouteInfo]]]])


class Router:
    """Route management system for HTTP-style path matching and parameter extraction.

    The Router class handles all routing logic for Cognite Functions, including:
    - Route storage and organization
    - Intelligent route sorting (exact paths before parameterized)
    - Path parameter extraction from URLs like /items/{item_id}
    - Route matching with type-safe results
    - Content negotiation via Accept header matching

    ## Architecture

    Extracted from FunctionApp to follow the Single Responsibility Principle.
    While FunctionApp provides the high-level decorator API (@app.get, @app.post),
    Router focuses purely on the mechanics of routing.

    ## Key Features

    - **Type Safety**: Uses SortedRoutes NewType to prevent misuse
    - **Smart Sorting**: Exact paths like '/items/special' match before '/items/{id}'
    - **Parameter Extraction**: Automatically extracts {param} values from URLs
    - **Content Negotiation**: Routes can specify Accept header requirements
    - **Reusability**: Can be used standalone or embedded in other frameworks
    - **Testability**: Clean, focused API makes testing straightforward

    ## Usage

    ### Basic Usage
    ```python
    router = Router()

    # Register a route
    route_info = RouteInfo(...)
    router.register_route("/items/{item_id}", HTTPMethod.GET, route_info)

    # Find matching routes
    route, params = router.find_matching_route("/items/123", "GET")
    # Returns: (RouteInfo, {"item_id": "123"})
    ```

    ### Route Matching Priority
    ```python
    router.register_route("/items/special", HTTPMethod.GET, exact_route)
    router.register_route("/items/{item_id}", HTTPMethod.GET, param_route)

    # Exact matches take priority
    route, params = router.find_matching_route("/items/special", "GET")
    # Returns: (exact_route, {})

    route, params = router.find_matching_route("/items/123", "GET")
    # Returns: (param_route, {"item_id": "123"})
    ```

    ### Content Negotiation
    ```python
    # Same path, different handlers based on Accept header
    json_route = RouteInfo(..., accept="application/json")
    html_route = RouteInfo(..., accept="text/html", content_type="text/html")
    router.register_route("/items/{item_id}", HTTPMethod.GET, json_route)
    router.register_route("/items/{item_id}", HTTPMethod.GET, html_route)

    # Match based on Accept header
    route, params = router.find_matching_route("/items/123", "GET", accept="text/html")
    # Returns: (html_route, {"item_id": "123"})
    ```

    ### Multiple Routers (Advanced)
    ```python
    api_v1_router = Router()
    api_v2_router = Router()

    # Each router maintains independent route tables
    # Useful for API versioning or modular applications
    ```

    ## Implementation Notes

    - Routes are sorted on-demand via the `sorted_routes` property
    - Sorting algorithm: exact paths (priority 0) before parameterized (priority 1)
    - Secondary sort by path string for deterministic ordering
    - Path parameters are extracted using regex matching
    - Type-safe SortedRoutes prevent accidentally passing unsorted route data
    - Multiple routes with same path/method but different accept values are supported
    """

    def __init__(self) -> None:
        """Initialize an empty router."""
        # Routes are stored as: path -> method -> list of RouteInfo
        # Multiple RouteInfo per method allows content negotiation via accept header
        self.routes: dict[str, dict[HTTPMethod, list[RouteInfo]]] = {}

    def register_route(self, path: str, method: HTTPMethod, route_info: RouteInfo) -> None:
        """Register a route with the router.

        Args:
            path: The route path pattern (e.g., "/items/{item_id}")
            method: The HTTP method
            route_info: Complete route information including application endpoint, parameters, etc.

        Note:
            Multiple routes with the same path and method but different accept values
            are allowed for content negotiation.

        Raises:
            ConfigurationError: If a default route (accept=None) is already registered
                for this path and method combination, or if content_type/accept are invalid MIME types.
        """
        # Validate MIME types
        _validate_mime_type(route_info.content_type, "content_type")
        if route_info.accept is not None:
            _validate_mime_type(route_info.accept, "accept")

        path_routes = self.routes.setdefault(path, {})
        method_routes = path_routes.setdefault(method, [])

        if route_info.accept is None and any(r.accept is None for r in method_routes):
            raise ConfigurationError(
                f"A default route (accept=None) is already registered for path='{path}' and method='{method}'."
            )

        method_routes.append(route_info)

    @property
    def sorted_routes(self) -> SortedRoutes:
        """Get routes sorted for efficient matching (exact paths before parameterized paths).

        Exact paths like '/items/special' are matched before parameterized paths like '/items/{item_id}'.
        This ensures that more specific routes take precedence over generic ones.

        Returns:
            SortedRoutes: Type-safe sorted routes that can only be created through this property
        """
        return SortedRoutes(sorted(self.routes.items(), key=self._route_sort_key))

    @staticmethod
    def _route_sort_key(route_item: tuple[str, dict[HTTPMethod, list[RouteInfo]]]) -> tuple[int, str]:
        """Sort key for route prioritization.

        Returns:
            Tuple of (priority, path) where:
            - priority: 0 for exact paths, 1 for parameterized paths
            - path: the route path for deterministic secondary sorting
        """
        path, _ = route_item
        # Exact paths (priority 0) come before parameterized paths (priority 1)
        priority = 1 if "{" in path else 0
        return (priority, path)

    @staticmethod
    def extract_path_params(path: str) -> Sequence[str]:
        """Extract parameter names from path like /items/{item_id}."""
        return re.findall(r"\{(\w+)\}", path)

    def find_matching_route(
        self, path: str, method: HTTPMethod, accept: str | None = None
    ) -> tuple[RouteInfo | None, PathParams]:
        """Find matching route and extract path parameters.

        Args:
            path: The target path to match against
            method: The HTTP method to match
            accept: Optional Accept header value for content negotiation

        Returns:
            Tuple of (matched RouteInfo, extracted path parameters) or (None, {}) if no match
        """
        return find_matching_route(self.sorted_routes, path, method, accept)


def _build_route_pattern(route_path: str, param_names: Sequence[str]) -> str:
    """Convert route path with {param} to regex pattern."""
    pattern = route_path
    for param in param_names:
        pattern = pattern.replace(f"{{{param}}}", r"([^/]+)")
    return f"^{pattern}$"


def _extract_path_parameters(match: re.Match[str], param_names: Sequence[str]) -> PathParams:
    """Extract path parameter values from regex match."""
    return {param: match.group(i + 1) for i, param in enumerate(param_names)}


def _match_path_with_parameters(route_path: str, target_path: str, param_names: Sequence[str]) -> PathParams | None:
    """Handle path parameter matching for a route with known parameters."""
    pattern = _build_route_pattern(route_path, param_names)
    match = re.match(pattern, target_path)
    if match:
        return _extract_path_parameters(match, param_names)
    return None


def _check_path_match(route_path: str, target_path: str, param_names: Sequence[str]) -> PathParams | None:
    """Check if target path matches route path and extract parameters."""
    # Exact path matches: /items, /health, /users
    if route_path == target_path:
        return {}

    # Handle path parameters: /items/{item_id}, /users/{user_id}/orders
    if param_names:
        return _match_path_with_parameters(route_path, target_path, param_names)

    return None


def _parse_accept_header(accept_header: str) -> Sequence[str]:
    """Parse Accept header into media types, respecting quoted strings.

    Follows RFC 7231 by properly handling quoted commas within media type parameters.
    For example: 'application/json; profile="http://example.com/profile,v1"'

    Args:
        accept_header: The Accept header value to parse

    Returns:
        List of media type strings (including parameters)
    """
    # Match sequences of non-comma/non-quote chars OR complete quoted strings
    pattern = r'(?:[^,"]|"[^"]*")+'
    return [m.strip() for m in re.findall(pattern, accept_header) if m.strip()]


def _accept_matches(route_accept: str, request_accept: str) -> bool:
    """Check if route's accept header matches request's Accept header.

    Matching rules (following FastAPI pattern):
    - Request with "*/*" anywhere in Accept header matches any route
    - Media range wildcards like "text/*" match any subtype (e.g., "text/html")
    - Otherwise, route accept must exactly match one of the accepted types

    Follows RFC 7231 by properly parsing quoted strings in Accept headers.

    Note:
        This function expects non-None arguments. None cases are handled by
        _find_best_route_for_accept before calling this function.

    Args:
        route_accept: The route's configured accept value (must be non-None)
        request_accept: The request's Accept header value (must be non-None)

    Returns:
        True if the route should handle this request based on accept headers
    """
    # Parse Accept header respecting quoted strings
    for accepted in _parse_accept_header(request_accept):
        # Strip quality values and whitespace: "text/html;q=0.9" -> "text/html"
        accepted_type = accepted.strip().split(";")[0]

        # Global wildcard matches any route
        if accepted_type == "*/*":
            return True

        # Exact match
        if accepted_type == route_accept:
            return True

        # Media range wildcard: "text/*" matches "text/html", "text/plain", etc.
        if accepted_type.endswith("/*") and route_accept.startswith(accepted_type[:-1]):
            return True

    return False


def _find_best_route_for_accept(route_infos: Sequence[RouteInfo], request_accept: str | None) -> RouteInfo | None:
    """Find the best matching route from a list based on Accept header.

    Priority:
    1. If no Accept header (request_accept=None), defaults to application/json
    2. Routes with specific accept that matches the request
    3. Routes with accept=None (fallback/default)

    Note:
        When request has no Accept header, it defaults to application/json.
        This means routes with accept="application/json" or accept=None will match.
        Routes with accept=None serve as fallback when no specific match is found.

    Args:
        route_infos: List of routes for the same path/method (in registration order)
        request_accept: The request's Accept header value

    Returns:
        Best matching RouteInfo or None if no match
    """
    if not route_infos:
        return None

    # No Accept header defaults to application/json
    if request_accept is None:
        request_accept = "application/json"

    fallback_route: RouteInfo | None = None

    for route_info in route_infos:
        if route_info.accept is None:
            if fallback_route is None:
                fallback_route = route_info
        elif _accept_matches(route_info.accept, request_accept):
            # Specific match takes priority
            return route_info

    # No specific match found, use fallback if available
    return fallback_route


def find_matching_route(
    sorted_routes: SortedRoutes, path: str, method: HTTPMethod, accept: str | None = None
) -> tuple[RouteInfo | None, PathParams]:
    """Find matching route and extract path parameters.

    Args:
        sorted_routes: Type-safe sorted routes from Router.sorted_routes property
        path: The target path to match against
        method: The HTTP method to match
        accept: Optional Accept header for content negotiation

    Returns:
        Tuple of (matched RouteInfo, extracted path parameters) or (None, {}) if no match

    Raises:
        NotAcceptableError: When path/method matches but Accept header doesn't match any route
    """
    for route_path, methods in sorted_routes:
        if method not in methods:
            continue

        route_infos = methods[method]
        if not route_infos:
            continue

        # Check path match using the first route's path_params (all routes for same path have same params)
        extracted_params = _check_path_match(route_path, path, route_infos[0].path_params)
        if extracted_params is None:
            continue

        # Path matches, now find best route based on Accept header
        best_route = _find_best_route_for_accept(route_infos, accept)
        if best_route is not None:
            return best_route, extracted_params

        # Path and method matched, but Accept header doesn't match any route
        # Collect available content types for error message
        available_types = sorted(
            list({route_info.content_type for route_info in route_infos if route_info.accept is not None})
        )
        # Use provided Accept header or default
        accept_header = accept if accept is not None else "application/json"
        raise NotAcceptableError(path=path, method=method.value, accept=accept_header, available_types=available_types)

    return None, {}
