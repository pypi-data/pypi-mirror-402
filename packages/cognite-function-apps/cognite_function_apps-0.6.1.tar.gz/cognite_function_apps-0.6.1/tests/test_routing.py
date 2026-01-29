"""Unit tests for Router class and standalone routing functions.

Tests route registration, path matching, parameter extraction, and route
sorting independently of the full FunctionApp context for better isolation.
"""

import inspect
from collections.abc import Mapping

import pytest
from cognite.client import CogniteClient

from cognite_function_apps.models import (
    ConfigurationError,
    FunctionCallInfo,
    HTTPMethod,
    NotAcceptableError,
    SecretsMapping,
)
from cognite_function_apps.routing import (
    RouteInfo,
    Router,
    SortedRoutes,
    _accept_matches,  # type: ignore[reportPrivateUsage]
    _find_best_route_for_accept,  # type: ignore[reportPrivateUsage]
    _parse_accept_header,  # type: ignore[reportPrivateUsage]
    find_matching_route,
)

from .conftest import TestItem as Item
from .conftest import TestItemResponse as ItemResponse


class TestRouter:
    """Tests for Router class functionality including registration, sorting, and matching."""

    def test_router_route_registration(self):
        """Test that the Router can register routes and store them correctly."""
        router = Router()

        # Create a simple route handler
        def get_item(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> ItemResponse:
            item_id = params.get("item_id", 1)
            if not isinstance(item_id, int):
                item_id = 1
            item = Item(name=f"Item {item_id}", price=100.0)
            return ItemResponse(id=item_id, item=item, total_price=100.0)

        # Create route info with handler metadata
        route_info = RouteInfo(
            path="/items/{item_id}",
            method=HTTPMethod.GET,
            endpoint=get_item,
            signature=inspect.signature(get_item),
            parameters={
                name: param for name, param in inspect.signature(get_item).parameters.items() if name != "client"
            },
            type_hints={},
            path_params=["item_id"],
            description="Get an item by ID",
        )

        # Register the route
        router.register_route("/items/{item_id}", HTTPMethod.GET, route_info)

        # Verify registration - routes are now stored as lists for content negotiation
        assert "/items/{item_id}" in router.routes
        assert HTTPMethod.GET in router.routes["/items/{item_id}"]
        assert router.routes["/items/{item_id}"][HTTPMethod.GET][0] == route_info

    def test_router_sorting_behavior_directly(self):
        """Test that routes are sorted with exact paths before parameterized paths, alphabetically within each group."""
        router = Router()

        def dummy_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> Mapping[str, str]:
            return {"status": "ok"}

        # Create minimal route info for testing sorting
        def create_route_info(path: str, path_params: list[str]) -> RouteInfo:
            return RouteInfo(
                path=path,
                method=HTTPMethod.GET,
                endpoint=dummy_handler,
                signature=inspect.signature(dummy_handler),
                parameters={},
                type_hints={},
                path_params=path_params,
                description="Test route",
            )

        # Register routes in mixed order to test sorting
        router.register_route(
            "/users/{user_id}", HTTPMethod.GET, create_route_info("/users/{user_id}", ["user_id"])
        )  # param
        router.register_route("/health", HTTPMethod.GET, create_route_info("/health", []))  # exact
        router.register_route(
            "/items/{item_id}", HTTPMethod.GET, create_route_info("/items/{item_id}", ["item_id"])
        )  # param
        router.register_route("/status", HTTPMethod.GET, create_route_info("/status", []))  # exact

        # Get sorted routes
        sorted_routes = router.sorted_routes
        route_paths = [path for path, _ in sorted_routes]

        # Verify sorting: exact paths before parameterized, alphabetical within each group
        exact_paths = [p for p in route_paths if "{" not in p]
        param_paths = [p for p in route_paths if "{" in p]

        assert exact_paths == ["/health", "/status"]  # Sorted alphabetically
        assert param_paths == ["/items/{item_id}", "/users/{user_id}"]  # Sorted alphabetically

        # Verify exact paths come before parameterized paths
        health_index = route_paths.index("/health")
        status_index = route_paths.index("/status")
        items_index = route_paths.index("/items/{item_id}")
        users_index = route_paths.index("/users/{user_id}")

        assert health_index < items_index
        assert health_index < users_index
        assert status_index < items_index
        assert status_index < users_index

    def test_path_parameter_extraction(self):
        """Test path parameter extraction from route patterns."""
        router = Router()

        # Test various path patterns
        assert router.extract_path_params("/items") == []
        assert router.extract_path_params("/items/{item_id}") == ["item_id"]
        assert router.extract_path_params("/users/{user_id}/items/{item_id}") == ["user_id", "item_id"]
        assert router.extract_path_params("/complex/{a}/{b}/nested/{c}") == ["a", "b", "c"]

    def test_route_matching_directly(self):
        """Test route matching for both exact and parameterized paths."""
        router = Router()

        def dummy_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"test": "value"}

        # Add some test routes
        exact_route = RouteInfo(
            path="/items/special",
            method=HTTPMethod.GET,
            endpoint=dummy_handler,
            signature=inspect.signature(dummy_handler),
            parameters={},
            type_hints={},
            path_params=[],
            description="Exact route",
        )

        param_route = RouteInfo(
            path="/items/{item_id}",
            method=HTTPMethod.GET,
            endpoint=dummy_handler,
            signature=inspect.signature(dummy_handler),
            parameters={},
            type_hints={},
            path_params=["item_id"],
            description="Parameterized route",
        )

        router.register_route("/items/special", HTTPMethod.GET, exact_route)
        router.register_route("/items/{item_id}", HTTPMethod.GET, param_route)

        # Test exact match
        found_route, path_params = router.find_matching_route("/items/special", HTTPMethod.GET)
        assert found_route is not None
        assert found_route.description == "Exact route"
        assert path_params == {}

        # Test parameterized match
        found_route, path_params = router.find_matching_route("/items/123", HTTPMethod.GET)
        assert found_route is not None
        assert found_route.description == "Parameterized route"
        assert path_params == {"item_id": "123"}

        # Test no match
        found_route, path_params = router.find_matching_route("/nonexistent", HTTPMethod.GET)
        assert found_route is None
        assert path_params == {}

    def test_multiple_routers_independence(self):
        """Test that multiple routers work independently - demonstrates reusability!"""
        router1 = Router()
        router2 = Router()

        def handler1(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"router": "1"}

        def handler2(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"router": "2"}

        route_info1 = RouteInfo(
            path="/test",
            method=HTTPMethod.GET,
            endpoint=handler1,
            signature=inspect.signature(handler1),
            parameters={},
            type_hints={},
            path_params=[],
            description="Router 1",
        )

        route_info2 = RouteInfo(
            path="/test",
            method=HTTPMethod.GET,
            endpoint=handler2,
            signature=inspect.signature(handler2),
            parameters={},
            type_hints={},
            path_params=[],
            description="Router 2",
        )

        # Each router has different routes
        router1.register_route("/test", HTTPMethod.GET, route_info1)
        router2.register_route("/test", HTTPMethod.GET, route_info2)

        # They should be independent
        route1, _ = router1.find_matching_route("/test", HTTPMethod.GET)
        route2, _ = router2.find_matching_route("/test", HTTPMethod.GET)

        assert route1 is not None and route1.description == "Router 1"
        assert route2 is not None and route2.description == "Router 2"

        # One router's routes don't affect the other
        assert len(router1.routes) == 1
        assert len(router2.routes) == 1

    def test_sorted_routes_complex_ordering(self):
        """Test that sorted routes handles complex ordering scenarios correctly."""
        router = Router()

        def dummy_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"status": "ok"}

        def create_route_info(path: str, path_params: list[str]) -> RouteInfo:
            return RouteInfo(
                path=path,
                method=HTTPMethod.GET,
                endpoint=dummy_handler,
                signature=inspect.signature(dummy_handler),
                parameters={},
                type_hints={},
                path_params=path_params,
                description="Test route",
            )

        # Register routes to test sorting behavior
        router.register_route("/items/special", HTTPMethod.GET, create_route_info("/items/special", []))  # exact
        router.register_route(
            "/items/{item_id}", HTTPMethod.GET, create_route_info("/items/{item_id}", ["item_id"])
        )  # param
        router.register_route("/users", HTTPMethod.GET, create_route_info("/users", []))  # exact

        sorted_routes = router.sorted_routes
        route_paths = [path for path, _ in sorted_routes]

        # Exact paths should come before parameterized paths
        # Within each category, they should be sorted alphabetically
        expected_paths = ["/items/special", "/users", "/items/{item_id}"]
        assert route_paths == expected_paths

    def test_mixed_order_route_registration_sorting(self):
        """Test that routes registered in mixed order are sorted correctly."""
        router = Router()

        def dummy_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"status": "ok"}

        def create_route_info(path: str, path_params: list[str]) -> RouteInfo:
            return RouteInfo(
                path=path,
                method=HTTPMethod.GET,
                endpoint=dummy_handler,
                signature=inspect.signature(dummy_handler),
                parameters={},
                type_hints={},
                path_params=path_params,
                description="Test route",
            )

        # Add routes in non-ideal order to verify sorting works
        router.register_route(
            "/items/{item_id}", HTTPMethod.GET, create_route_info("/items/{item_id}", ["item_id"])
        )  # param - should come later
        router.register_route(
            "/items/special", HTTPMethod.GET, create_route_info("/items/special", [])
        )  # exact - should come first
        router.register_route(
            "/users/{user_id}", HTTPMethod.GET, create_route_info("/users/{user_id}", ["user_id"])
        )  # param - should come later
        router.register_route("/health", HTTPMethod.GET, create_route_info("/health", []))  # exact - should come first

        # Get sorted routes and verify ordering
        sorted_routes = router.sorted_routes
        route_paths = [path for path, _ in sorted_routes]

        # All exact paths should come before all parameterized paths
        exact_paths = [p for p in route_paths if "{" not in p]
        param_paths = [p for p in route_paths if "{" in p]

        # Check that exact paths come first in the full list
        exact_indices = [route_paths.index(p) for p in exact_paths]
        param_indices = [route_paths.index(p) for p in param_paths]

        # All exact path indices should be less than all parameterized path indices
        assert all(e < p for e in exact_indices for p in param_indices), (
            f"Exact paths {exact_paths} should come before parameterized paths {param_paths} in {route_paths}"
        )

        # Within each category, paths should be sorted alphabetically
        assert exact_paths == sorted(exact_paths)
        assert param_paths == sorted(param_paths)

    def test_router_same_path_different_methods(self):
        """Test that Router can handle same path with different HTTP methods."""
        router = Router()

        def get_items_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"method": "GET", "action": "list_items"}

        def post_items_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"method": "POST", "action": "create_item"}

        # Create route info for both methods
        get_route_info = RouteInfo(
            path="/items",
            method=HTTPMethod.GET,
            endpoint=get_items_handler,
            signature=inspect.signature(get_items_handler),
            parameters={},
            type_hints={},
            path_params=[],
            description="List all items",
        )

        post_route_info = RouteInfo(
            path="/items",
            method=HTTPMethod.POST,
            endpoint=post_items_handler,
            signature=inspect.signature(post_items_handler),
            parameters={},
            type_hints={},
            path_params=[],
            description="Create new item",
        )

        # Register both methods for the same path
        router.register_route("/items", HTTPMethod.GET, get_route_info)
        router.register_route("/items", HTTPMethod.POST, post_route_info)

        # Verify both routes are stored - routes are now stored as lists for content negotiation
        assert "/items" in router.routes
        assert HTTPMethod.GET in router.routes["/items"]
        assert HTTPMethod.POST in router.routes["/items"]
        assert router.routes["/items"][HTTPMethod.GET][0] == get_route_info
        assert router.routes["/items"][HTTPMethod.POST][0] == post_route_info

        # Test finding GET route
        found_route, path_params = router.find_matching_route("/items", HTTPMethod.GET)
        assert found_route is not None
        assert found_route.description == "List all items"
        assert found_route.endpoint == get_items_handler
        assert path_params == {}

        # Test finding POST route
        found_route, path_params = router.find_matching_route("/items", HTTPMethod.POST)
        assert found_route is not None
        assert found_route.description == "Create new item"
        assert found_route.endpoint == post_items_handler
        assert path_params == {}

        # Test method not registered (PUT)
        found_route, path_params = router.find_matching_route("/items", HTTPMethod.PUT)
        assert found_route is None
        assert path_params == {}

    def test_router_parameterized_path_multiple_methods(self):
        """Test Router with parameterized paths and multiple HTTP methods."""
        router = Router()

        def get_item_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"method": "GET", "action": "get_item"}

        def put_item_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"method": "PUT", "action": "update_item"}

        # Create route info for both methods with path parameters
        get_route_info = RouteInfo(
            path="/items/{item_id}",
            method=HTTPMethod.GET,
            endpoint=get_item_handler,
            signature=inspect.signature(get_item_handler),
            parameters={},
            type_hints={},
            path_params=["item_id"],
            description="Get item by ID",
        )

        put_route_info = RouteInfo(
            path="/items/{item_id}",
            method=HTTPMethod.PUT,
            endpoint=put_item_handler,
            signature=inspect.signature(put_item_handler),
            parameters={},
            type_hints={},
            path_params=["item_id"],
            description="Update item",
        )

        # Register both methods for the same parameterized path
        router.register_route("/items/{item_id}", HTTPMethod.GET, get_route_info)
        router.register_route("/items/{item_id}", HTTPMethod.PUT, put_route_info)

        # Test GET with parameter extraction
        found_route, path_params = router.find_matching_route("/items/42", HTTPMethod.GET)
        assert found_route is not None
        assert found_route.description == "Get item by ID"
        assert found_route.endpoint == get_item_handler
        assert path_params == {"item_id": "42"}

        # Test PUT with parameter extraction
        found_route, path_params = router.find_matching_route("/items/99", HTTPMethod.PUT)
        assert found_route is not None
        assert found_route.description == "Update item"
        assert found_route.endpoint == put_item_handler
        assert path_params == {"item_id": "99"}

        # Test unsupported method (DELETE)
        found_route, path_params = router.find_matching_route("/items/42", HTTPMethod.DELETE)
        assert found_route is None
        assert path_params == {}

    def test_duplicate_default_route_raises_configuration_error(self):
        """Test that registering two default routes (accept=None) for same path/method raises ConfigurationError."""
        router = Router()

        def handler1(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"handler": "1"}

        def handler2(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"handler": "2"}

        # First default route should work fine
        route_info1 = RouteInfo(
            path="/items",
            method=HTTPMethod.GET,
            endpoint=handler1,
            signature=inspect.signature(handler1),
            parameters={},
            type_hints={},
            path_params=[],
            description="First default route",
            accept=None,  # default route
        )
        router.register_route("/items", HTTPMethod.GET, route_info1)

        # Second default route for same path/method should raise
        route_info2 = RouteInfo(
            path="/items",
            method=HTTPMethod.GET,
            endpoint=handler2,
            signature=inspect.signature(handler2),
            parameters={},
            type_hints={},
            path_params=[],
            description="Second default route",
            accept=None,  # also default route - should fail
        )

        with pytest.raises(ConfigurationError) as exc_info:
            router.register_route("/items", HTTPMethod.GET, route_info2)

        assert "default route" in str(exc_info.value).lower()
        assert "/items" in str(exc_info.value)
        assert "GET" in str(exc_info.value)

    def test_multiple_routes_with_different_accept_values_allowed(self):
        """Test that multiple routes with different non-None accept values are allowed."""
        router = Router()

        def json_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"format": "json"}

        def html_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"format": "html"}

        def default_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"format": "default"}

        # Register route with specific accept
        json_route = RouteInfo(
            path="/items",
            method=HTTPMethod.GET,
            endpoint=json_handler,
            signature=inspect.signature(json_handler),
            parameters={},
            type_hints={},
            path_params=[],
            description="JSON handler",
            accept="application/json",
        )
        router.register_route("/items", HTTPMethod.GET, json_route)

        # Register another route with different accept - should work
        html_route = RouteInfo(
            path="/items",
            method=HTTPMethod.GET,
            endpoint=html_handler,
            signature=inspect.signature(html_handler),
            parameters={},
            type_hints={},
            path_params=[],
            description="HTML handler",
            accept="text/html",
        )
        router.register_route("/items", HTTPMethod.GET, html_route)

        # Register one default route - should work
        default_route = RouteInfo(
            path="/items",
            method=HTTPMethod.GET,
            endpoint=default_handler,
            signature=inspect.signature(default_handler),
            parameters={},
            type_hints={},
            path_params=[],
            description="Default handler",
            accept=None,
        )
        router.register_route("/items", HTTPMethod.GET, default_route)

        # Verify all three routes are registered
        assert len(router.routes["/items"][HTTPMethod.GET]) == 3

        # Verify content negotiation works
        json_result, _ = router.find_matching_route("/items", HTTPMethod.GET, accept="application/json")
        assert json_result is not None
        assert json_result.description == "JSON handler"

        html_result, _ = router.find_matching_route("/items", HTTPMethod.GET, accept="text/html")
        assert html_result is not None
        assert html_result.description == "HTML handler"

        # Unknown accept falls back to default
        unknown_result, _ = router.find_matching_route("/items", HTTPMethod.GET, accept="application/xml")
        assert unknown_result is not None
        assert unknown_result.description == "Default handler"

    @pytest.mark.parametrize(
        "invalid_content_type",
        [
            "invalid",
            "no-slash",
            "/missing-type",
            "missing-subtype/",
            "",
            "has spaces/json",
            "<script>/html",
        ],
    )
    def test_invalid_content_type_raises_error(self, invalid_content_type: str):
        """Invalid content_type MIME format raises ConfigurationError."""
        router = Router()

        def handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {}

        route_info = RouteInfo(
            path="/items",
            method=HTTPMethod.GET,
            endpoint=handler,
            signature=inspect.signature(handler),
            parameters={},
            type_hints={},
            path_params=[],
            description="Test route",
            content_type=invalid_content_type,
        )

        with pytest.raises(ConfigurationError) as exc_info:
            router.register_route("/items", HTTPMethod.GET, route_info)

        assert "content_type" in str(exc_info.value)

    @pytest.mark.parametrize(
        "invalid_accept",
        [
            "invalid",
            "no-slash",
            "/missing-type",
            "missing-subtype/",
            "",
        ],
    )
    def test_invalid_accept_raises_error(self, invalid_accept: str):
        """Invalid accept MIME format raises ConfigurationError."""
        router = Router()

        def handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {}

        route_info = RouteInfo(
            path="/items",
            method=HTTPMethod.GET,
            endpoint=handler,
            signature=inspect.signature(handler),
            parameters={},
            type_hints={},
            path_params=[],
            description="Test route",
            accept=invalid_accept,
        )

        with pytest.raises(ConfigurationError) as exc_info:
            router.register_route("/items", HTTPMethod.GET, route_info)

        assert "accept" in str(exc_info.value)

    @pytest.mark.parametrize(
        "valid_content_type",
        [
            "application/json",
            "text/html",
            "text/plain; charset=utf-8",
            "application/vnd.api+json",
            "image/svg+xml",
            "application/x-www-form-urlencoded",
        ],
    )
    def test_valid_content_type_accepted(self, valid_content_type: str):
        """Valid MIME types are accepted without error."""
        router = Router()

        def handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {}

        route_info = RouteInfo(
            path="/items",
            method=HTTPMethod.GET,
            endpoint=handler,
            signature=inspect.signature(handler),
            parameters={},
            type_hints={},
            path_params=[],
            description="Test route",
            content_type=valid_content_type,
        )

        # Should not raise
        router.register_route("/items", HTTPMethod.GET, route_info)
        assert len(router.routes["/items"][HTTPMethod.GET]) == 1


class TestStandaloneFindMatchingRoute:
    """Test the standalone find_matching_route function."""

    @staticmethod
    def create_sorted_routes(routes_data: list[tuple[str, dict[HTTPMethod, list[RouteInfo]]]]) -> SortedRoutes:
        """Helper to create type-safe SortedRoutes for testing."""
        return SortedRoutes(routes_data)

    def test_exact_path_match(self):
        """Test exact path matching without parameters."""

        def dummy_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {}

        route_info = RouteInfo(
            path="/test",  # Generic path for test RouteInfo
            method=HTTPMethod.GET,
            endpoint=dummy_handler,
            signature=inspect.signature(dummy_handler),
            parameters={},
            type_hints={},
            path_params=[],
            description="Test route",
        )

        sorted_routes = self.create_sorted_routes(
            [
                ("/items", {HTTPMethod.GET: [route_info]}),
                ("/users", {HTTPMethod.POST: [route_info]}),
            ]
        )

        # Test matching route
        found_route, path_params = find_matching_route(sorted_routes, "/items", HTTPMethod.GET)
        assert found_route is not None
        assert found_route.method == HTTPMethod.GET
        assert path_params == {}

        # Test non-matching path
        found_route, path_params = find_matching_route(sorted_routes, "/nonexistent", HTTPMethod.GET)
        assert found_route is None
        assert path_params == {}

        # Test non-matching method
        found_route, path_params = find_matching_route(sorted_routes, "/items", HTTPMethod.POST)
        assert found_route is None
        assert path_params == {}

    def test_path_parameter_matching(self):
        """Test path parameter extraction."""

        def dummy_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {}

        route_info = RouteInfo(
            path="/items/{item_id}",
            method=HTTPMethod.GET,
            endpoint=dummy_handler,
            signature=inspect.signature(dummy_handler),
            parameters={},
            type_hints={},
            path_params=["item_id"],
            description="Test route",
        )

        sorted_routes = self.create_sorted_routes(
            [
                ("/items/{item_id}", {HTTPMethod.GET: [route_info]}),
            ]
        )

        # Test parameter extraction
        found_route, path_params = find_matching_route(sorted_routes, "/items/123", HTTPMethod.GET)
        assert found_route is not None
        assert path_params == {"item_id": "123"}

        # Test non-matching path
        found_route, path_params = find_matching_route(sorted_routes, "/items/123/extra", HTTPMethod.GET)
        assert found_route is None
        assert path_params == {}

    def test_type_safety_with_sorted_routes(self):
        """Test that SortedRoutes type provides proper type safety."""

        def dummy_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {}

        route_info = RouteInfo(
            path="/items",
            method=HTTPMethod.GET,
            endpoint=dummy_handler,
            signature=inspect.signature(dummy_handler),
            parameters={},
            type_hints={},
            path_params=[],
            description="Type safety test",
        )

        # This is the correct way - using our helper
        proper_sorted_routes = self.create_sorted_routes(
            [
                ("/items", {HTTPMethod.GET: [route_info]}),
            ]
        )

        # This should work fine
        found_route, path_params = find_matching_route(proper_sorted_routes, "/items", HTTPMethod.GET)
        assert found_route is not None
        assert found_route.description == "Type safety test"
        assert path_params == {}

    def test_same_path_different_methods(self):
        """Test that the same path can have different handlers for different HTTP methods."""

        def get_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"method": "GET"}

        def post_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"method": "POST"}

        get_route_info = RouteInfo(
            path="/items",
            method=HTTPMethod.GET,
            endpoint=get_handler,
            signature=inspect.signature(get_handler),
            parameters={},
            type_hints={},
            path_params=[],
            description="GET handler",
        )

        post_route_info = RouteInfo(
            path="/items",
            method=HTTPMethod.POST,
            endpoint=post_handler,
            signature=inspect.signature(post_handler),
            parameters={},
            type_hints={},
            path_params=[],
            description="POST handler",
        )

        sorted_routes = self.create_sorted_routes(
            [
                ("/items", {HTTPMethod.GET: [get_route_info], HTTPMethod.POST: [post_route_info]}),
            ]
        )

        # Test GET method
        found_route, path_params = find_matching_route(sorted_routes, "/items", HTTPMethod.GET)
        assert found_route is not None
        assert found_route.description == "GET handler"
        assert found_route.endpoint == get_handler
        assert path_params == {}

        # Test POST method
        found_route, path_params = find_matching_route(sorted_routes, "/items", HTTPMethod.POST)
        assert found_route is not None
        assert found_route.description == "POST handler"
        assert found_route.endpoint == post_handler
        assert path_params == {}

        # Test non-existent method (PUT)
        found_route, path_params = find_matching_route(sorted_routes, "/items", HTTPMethod.PUT)
        assert found_route is None
        assert path_params == {}

    def test_same_parameterized_path_different_methods(self):
        """Test that parameterized paths can have different handlers for different HTTP methods."""

        def get_item_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"method": "GET", "action": "retrieve"}

        def put_item_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"method": "PUT", "action": "update"}

        def delete_item_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"method": "DELETE", "action": "remove"}

        get_route_info = RouteInfo(
            path="/items/{item_id}",
            method=HTTPMethod.GET,
            endpoint=get_item_handler,
            signature=inspect.signature(get_item_handler),
            parameters={},
            type_hints={},
            path_params=["item_id"],
            description="Get item by ID",
        )

        put_route_info = RouteInfo(
            path="/items/{item_id}",
            method=HTTPMethod.PUT,
            endpoint=put_item_handler,
            signature=inspect.signature(put_item_handler),
            parameters={},
            type_hints={},
            path_params=["item_id"],
            description="Update item by ID",
        )

        delete_route_info = RouteInfo(
            path="/items/{item_id}",
            method=HTTPMethod.DELETE,
            endpoint=delete_item_handler,
            signature=inspect.signature(delete_item_handler),
            parameters={},
            type_hints={},
            path_params=["item_id"],
            description="Delete item by ID",
        )

        sorted_routes = self.create_sorted_routes(
            [
                (
                    "/items/{item_id}",
                    {
                        HTTPMethod.GET: [get_route_info],
                        HTTPMethod.PUT: [put_route_info],
                        HTTPMethod.DELETE: [delete_route_info],
                    },
                ),
            ]
        )

        # Test GET method with parameter extraction
        found_route, path_params = find_matching_route(sorted_routes, "/items/123", HTTPMethod.GET)
        assert found_route is not None
        assert found_route.description == "Get item by ID"
        assert found_route.endpoint == get_item_handler
        assert path_params == {"item_id": "123"}

        # Test PUT method with parameter extraction
        found_route, path_params = find_matching_route(sorted_routes, "/items/456", HTTPMethod.PUT)
        assert found_route is not None
        assert found_route.description == "Update item by ID"
        assert found_route.endpoint == put_item_handler
        assert path_params == {"item_id": "456"}

        # Test DELETE method with parameter extraction
        found_route, path_params = find_matching_route(sorted_routes, "/items/789", HTTPMethod.DELETE)
        assert found_route is not None
        assert found_route.description == "Delete item by ID"
        assert found_route.endpoint == delete_item_handler
        assert path_params == {"item_id": "789"}

        # Test non-existent method (POST)
        found_route, path_params = find_matching_route(sorted_routes, "/items/123", HTTPMethod.POST)
        assert found_route is None
        assert path_params == {}


class TestParseAcceptHeader:
    """Tests for _parse_accept_header - RFC 7231 compliant Accept header parsing."""

    @pytest.mark.parametrize(
        "accept_header,expected",
        [
            # Simple cases
            ("text/html", ["text/html"]),
            ("application/json", ["application/json"]),
            # Multiple types
            ("text/html, application/json", ["text/html", "application/json"]),
            ("text/html,application/json,image/png", ["text/html", "application/json", "image/png"]),
            # With quality values
            ("text/html;q=0.9", ["text/html;q=0.9"]),
            ("text/html;q=0.9, application/json;q=1.0", ["text/html;q=0.9", "application/json;q=1.0"]),
            # Quoted commas (RFC 7231 compliance)
            (
                'application/json; profile="http://example.com/profile,v1"',
                ['application/json; profile="http://example.com/profile,v1"'],
            ),
            ('text/html, application/json; msg="hello, world"', ["text/html", 'application/json; msg="hello, world"']),
            ('application/json; data="a,b,c"', ['application/json; data="a,b,c"']),
            # Complex quoted strings with multiple commas
            (
                'text/html, application/json; complex="one,two,three", image/png',
                ["text/html", 'application/json; complex="one,two,three"', "image/png"],
            ),
            # Empty and edge cases (empty strings are skipped - not valid media types)
            ("", []),
            (",", []),  # Empty strings skipped
            ("text/html,", ["text/html"]),  # Trailing comma ignored
            (",text/html", ["text/html"]),  # Leading comma ignored
        ],
    )
    def test_parse_accept_header(self, accept_header: str, expected: list[str]):
        """Test Accept header parsing with various formats including quoted commas."""
        assert list(_parse_accept_header(accept_header)) == expected

    def test_nested_quotes(self):
        """Test that parser handles malformed unclosed quotes gracefully."""
        # Opening quote without closing - malformed but shouldn't crash
        header = 'text/html, application/json; broken="unclosed'
        result = _parse_accept_header(header)
        # Parser should return results without crashing (exact count may vary)
        assert len(result) >= 2
        assert "text/html" in result

    def test_real_world_browser_headers(self):
        """Test with realistic browser Accept headers."""
        browser_header = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        result = _parse_accept_header(browser_header)
        assert len(result) == 5
        assert "text/html" in result[0]


class TestAcceptMatches:
    """Tests for _accept_matches - Accept header content negotiation."""

    @pytest.mark.parametrize(
        "route_accept,request_accept,expected",
        [
            # Global wildcard */* matches any route
            ("application/json", "*/*", True),
            ("text/html", "*/*", True),
            ("image/png", "*/*", True),
            # Wildcard in Accept list
            ("application/json", "text/html, */*", True),
            ("image/png", "text/html, application/json, */*", True),
            # Exact matches
            ("application/json", "application/json", True),
            ("text/html", "text/html", True),
            ("image/png", "image/png", True),
            # Exact match in list
            ("application/json", "text/html, application/json", True),
            ("text/html", "application/json, text/html, image/png", True),
            # No match
            ("application/json", "text/html", False),
            ("text/html", "application/json", False),
            ("image/png", "text/html, application/json", False),
        ],
    )
    def test_basic_matching(self, route_accept: str, request_accept: str, expected: bool):
        """Basic accept header matching scenarios."""
        assert _accept_matches(route_accept, request_accept) is expected

    @pytest.mark.parametrize(
        "route_accept,wildcard",
        [
            ("text/html", "text/*"),
            ("text/plain", "text/*"),
            ("text/css", "text/*"),
            ("application/json", "application/*"),
            ("application/xml", "application/*"),
            ("application/pdf", "application/*"),
            ("image/png", "image/*"),
            ("image/jpeg", "image/*"),
            ("image/gif", "image/*"),
        ],
    )
    def test_media_range_wildcard_match(self, route_accept: str, wildcard: str):
        """Media range wildcard (type/*) matches subtypes."""
        assert _accept_matches(route_accept, wildcard) is True

    @pytest.mark.parametrize(
        "route_accept,wildcard",
        [
            ("application/json", "text/*"),
            ("text/html", "image/*"),
            ("image/png", "application/*"),
        ],
    )
    def test_media_range_no_cross_type(self, route_accept: str, wildcard: str):
        """Media range wildcard doesn't match different types."""
        assert _accept_matches(route_accept, wildcard) is False

    @pytest.mark.parametrize(
        "route_accept,request_accept",
        [
            ("text/html", "application/json, text/*"),
            ("image/png", "text/html, image/*, application/json"),
            ("text/html", "text/html;q=0.9"),
            ("application/json", "application/json;q=1.0"),
            ("text/html", "application/json;q=0.9, text/html;q=0.8"),
            ("text/html", "text/*;q=0.5"),
            ("application/json", "*/*;q=0.1"),
            ("application/json", "text/html , application/json"),
            ("text/html", "  text/html  "),
            ("image/png", "text/html,  image/png  , application/json"),
            ("text/html", ",text/html,"),
            ("application/json", "application/json,"),
        ],
    )
    def test_complex_accept_patterns(self, route_accept: str, request_accept: str):
        """Wildcards in lists, quality values, and whitespace handling."""
        assert _accept_matches(route_accept, request_accept) is True

    def test_browser_accept_header(self):
        """Real-world browser Accept header pattern."""
        browser_accept = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        assert _accept_matches("text/html", browser_accept) is True
        assert _accept_matches("application/json", browser_accept) is True  # matches */*
        assert _accept_matches("image/webp", browser_accept) is True

    @pytest.mark.parametrize(
        "route_accept,request_accept,expected",
        [
            # Quoted commas should not cause incorrect splits
            ("text/html", 'text/html; profile="http://example.com/profile,v1"', True),
            ("application/json", 'application/json; msg="hello, world"', True),
            ("text/html", 'application/json; data="a,b,c", text/html', True),
            # Quoted comma should not prevent matching
            ("application/json", 'text/html, application/json; complex="one,two,three"', True),
        ],
    )
    def test_quoted_commas_rfc_7231_compliance(self, route_accept: str, request_accept: str, expected: bool):
        """RFC 7231: Quoted commas in parameters should not cause incorrect splitting."""
        assert _accept_matches(route_accept, request_accept) is expected


class TestFindBestRouteForAccept:
    """Tests for _find_best_route_for_accept function - priority logic for content negotiation."""

    @staticmethod
    def create_route_info(accept: str | None, description: str) -> RouteInfo:
        """Helper to create RouteInfo with specific accept value."""

        def dummy_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {}

        return RouteInfo(
            path="/items",
            method=HTTPMethod.GET,
            endpoint=dummy_handler,
            signature=inspect.signature(dummy_handler),
            parameters={},
            type_hints={},
            path_params=[],
            description=description,
            accept=accept,
        )

    def test_specific_match_takes_priority_over_fallback(self):
        """Specific accept match should win over accept=None fallback."""
        json_route = self.create_route_info("application/json", "JSON handler")
        fallback_route = self.create_route_info(None, "Fallback handler")

        routes = [fallback_route, json_route]  # fallback first in list

        # Specific match should win even though fallback is first
        result = _find_best_route_for_accept(routes, "application/json")
        assert result is not None
        assert result.description == "JSON handler"

    def test_fallback_used_when_no_specific_match(self):
        """Fallback (accept=None) should be used when no specific match."""
        json_route = self.create_route_info("application/json", "JSON handler")
        fallback_route = self.create_route_info(None, "Fallback handler")

        routes = [json_route, fallback_route]

        # Request for XML should fall back to default
        result = _find_best_route_for_accept(routes, "application/xml")
        assert result is not None
        assert result.description == "Fallback handler"

    def test_no_match_returns_none_when_no_fallback(self):
        """Should return None when Accept doesn't match and no fallback exists."""
        json_route = self.create_route_info("application/json", "JSON handler")
        html_route = self.create_route_info("text/html", "HTML handler")

        routes = [json_route, html_route]  # No fallback (accept=None)

        # Request for XML with no fallback should return None
        result = _find_best_route_for_accept(routes, "application/xml")
        assert result is None

    def test_first_specific_match_wins(self):
        """When multiple routes match, first specific match should be returned."""
        json_route_1 = self.create_route_info("application/json", "First JSON handler")
        json_route_2 = self.create_route_info("application/json", "Second JSON handler")

        routes = [json_route_1, json_route_2]

        result = _find_best_route_for_accept(routes, "application/json")
        assert result is not None
        assert result.description == "First JSON handler"

    def test_request_accept_none_defaults_to_application_json(self):
        """Request with no Accept header should default to application/json."""
        json_route = self.create_route_info("application/json", "JSON handler")
        fallback_route = self.create_route_info(None, "Fallback handler")

        # No Accept header defaults to application/json, so json_route matches
        routes = [json_route, fallback_route]
        result = _find_best_route_for_accept(routes, None)
        assert result is not None
        assert result.description == "JSON handler"

        # Order doesn't matter - json route always matches when Accept is None
        routes = [fallback_route, json_route]
        result = _find_best_route_for_accept(routes, None)
        assert result is not None
        assert result.description == "JSON handler"

        # If no json route, fallback route (accept=None) should match
        routes = [fallback_route]
        result = _find_best_route_for_accept(routes, None)
        assert result is not None
        assert result.description == "Fallback handler"

    def test_wildcard_accept_matches_specific_route(self):
        """Request with */* should match specific routes."""
        json_route = self.create_route_info("application/json", "JSON handler")

        routes = [json_route]

        result = _find_best_route_for_accept(routes, "*/*")
        assert result is not None
        assert result.description == "JSON handler"

    def test_media_range_wildcard_matches(self):
        """Request with text/* should match text/html route."""
        html_route = self.create_route_info("text/html", "HTML handler")
        json_route = self.create_route_info("application/json", "JSON handler")

        routes = [html_route, json_route]

        result = _find_best_route_for_accept(routes, "text/*")
        assert result is not None
        assert result.description == "HTML handler"

    def test_empty_routes_returns_none(self):
        """Empty route list should return None."""
        result = _find_best_route_for_accept([], "application/json")
        assert result is None

    def test_only_fallback_route_works(self):
        """Single fallback route should always match."""
        fallback_route = self.create_route_info(None, "Fallback handler")

        routes = [fallback_route]

        # Any accept should match fallback
        assert _find_best_route_for_accept(routes, "application/json") == fallback_route
        assert _find_best_route_for_accept(routes, "text/html") == fallback_route
        assert _find_best_route_for_accept(routes, None) == fallback_route


class TestRouterQuotedCommasBugfix:
    """Tests verifying quoted commas don't cause silent fallback to default routes (Gemini issue)."""

    def test_quoted_commas_match_correct_route_no_fallback(self):
        """Quoted commas should match the correct specific route, not fall back silently."""
        router = Router()

        def html_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"format": "html"}

        def json_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"format": "json"}

        # Register HTML route with specific accept
        html_route = RouteInfo(
            path="/items/{id}",
            method=HTTPMethod.GET,
            endpoint=html_handler,
            signature=inspect.signature(html_handler),
            parameters={},
            type_hints={},
            path_params=["id"],
            description="HTML handler",
            accept="text/html",
        )

        # Register JSON route as default (accept=None)
        json_route = RouteInfo(
            path="/items/{id}",
            method=HTTPMethod.GET,
            endpoint=json_handler,
            signature=inspect.signature(json_handler),
            parameters={},
            type_hints={},
            path_params=["id"],
            description="JSON handler",
            accept=None,  # default fallback
        )

        router.register_route("/items/{id}", HTTPMethod.GET, html_route)
        router.register_route("/items/{id}", HTTPMethod.GET, json_route)

        # Request with quoted comma in Accept header should match HTML route, not fall back to JSON
        accept_with_quoted_comma = 'text/html; profile="http://example.com/profile,v1"'
        found_route, params = router.find_matching_route("/items/123", HTTPMethod.GET, accept=accept_with_quoted_comma)

        assert found_route is not None
        assert found_route.description == "HTML handler", (
            "Bug: Quoted comma caused incorrect parsing, falling back to default JSON handler instead of matching HTML"
        )
        assert params == {"id": "123"}


class TestRouterNoMatchNoFallback:
    """Tests for scenarios where Accept header doesn't match and no fallback exists."""

    def test_find_matching_route_raises_406_no_fallback(self):
        """Router should raise NotAcceptableError when Accept doesn't match and no fallback route exists."""
        router = Router()

        def json_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"format": "json"}

        def html_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"format": "html"}

        # Register routes with specific accept values but NO fallback
        json_route = RouteInfo(
            path="/items",
            method=HTTPMethod.GET,
            endpoint=json_handler,
            signature=inspect.signature(json_handler),
            parameters={},
            type_hints={},
            path_params=[],
            description="JSON handler",
            accept="application/json",
        )
        html_route = RouteInfo(
            path="/items",
            method=HTTPMethod.GET,
            endpoint=html_handler,
            signature=inspect.signature(html_handler),
            parameters={},
            type_hints={},
            path_params=[],
            description="HTML handler",
            accept="text/html",
        )

        router.register_route("/items", HTTPMethod.GET, json_route)
        router.register_route("/items", HTTPMethod.GET, html_route)

        # Request for XML should raise NotAcceptableError (no match, no fallback)
        with pytest.raises(NotAcceptableError) as exc_info:
            router.find_matching_route("/items", HTTPMethod.GET, accept="application/xml")

        assert exc_info.value.path == "/items"
        assert exc_info.value.method == "GET"
        assert exc_info.value.accept == "application/xml"
        assert "application/json" in exc_info.value.available_types
