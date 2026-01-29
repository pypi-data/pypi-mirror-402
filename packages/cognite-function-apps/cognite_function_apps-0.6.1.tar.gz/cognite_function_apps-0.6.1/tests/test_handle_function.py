"""Tests for the main handle function dispatcher."""

from typing import Any

from cognite.client import CogniteClient

from cognite_function_apps import FunctionApp, create_function_service

from .conftest import TestItem as Item
from .conftest import TestItemResponse as ItemResponse


class TestHandleFunction:
    """Test the main handle function that dispatches requests."""

    def setup_method(self) -> None:
        """Set up test app with sample routes."""
        self.app = FunctionApp(title="Test App", version="1.0.0")

        # Add some test routes
        @self.app.get("/items/{item_id}")
        def get_item(client: CogniteClient, item_id: int, include_tax: bool = False) -> ItemResponse:
            """Get an item by ID."""
            tax = 10.0 if include_tax else None
            item = Item(name=f"Item {item_id}", price=100.0, tax=tax)
            total = item.price + (item.tax or 0)
            return ItemResponse(id=item_id, item=item, total_price=total)

        @self.app.post("/items/")
        def create_item(client: CogniteClient, item: Item) -> ItemResponse:
            """Create a new item."""
            total = item.price + (item.tax or 0)
            return ItemResponse(id=999, item=item, total_price=total)

        @self.app.post("/process/batch")
        def process_batch(client: CogniteClient, items: list[Item]) -> dict[str, int | float]:
            """Process multiple items in batch."""
            total_value = sum(item.price + (item.tax or 0) for item in items)
            return {"processed_count": len(items), "total_value": total_value}

        # Create the handler
        self.handle = create_function_service(self.app)

    def test_get_request_with_path_params(self, mock_client: CogniteClient) -> None:
        """Test GET request with path parameters."""
        request_data: dict[str, Any] = {
            "path": "/items/123?include_tax=true",
            "method": "GET",
            "body": {},
        }

        response = self.handle(client=mock_client, data=request_data)
        assert isinstance(response, dict)

        # Should return successful response (status_code < 400)
        assert isinstance(response["status_code"], int)
        assert response["status_code"] < 400
        assert "data" in response

        # Check the returned data
        data = response["data"]
        assert isinstance(data, dict)
        assert data["id"] == 123
        assert isinstance(data["item"], dict)
        assert data["item"]["name"] == "Item 123"
        assert data["item"]["tax"] == 10.0  # include_tax=true
        assert data["total_price"] == 110.0

    def test_get_request_without_optional_params(self, mock_client: CogniteClient) -> None:
        """Test GET request without optional query parameters."""
        request_data: dict[str, Any] = {
            "path": "/items/456",
            "method": "GET",
            "body": {},
        }

        response = self.handle(client=mock_client, data=request_data)
        assert isinstance(response, dict)

        # Should return successful response (status_code < 400)
        assert isinstance(response["status_code"], int)
        assert response["status_code"] < 400
        data = response["data"]
        assert isinstance(data, dict)
        assert data["id"] == 456
        assert isinstance(data["item"], dict)
        assert data["item"]["tax"] is None  # include_tax defaults to False
        assert data["total_price"] == 100.0

    def test_post_request_with_body(self, mock_client: CogniteClient) -> None:
        """Test POST request with request body."""
        item_data = {
            "name": "New Item",
            "description": "A new test item",
            "price": 50.0,
            "tax": 5.0,
        }

        request_data: dict[str, Any] = {
            "path": "/items/",
            "method": "POST",
            "body": {"item": item_data},
        }

        response = self.handle(client=mock_client, data=request_data)
        assert isinstance(response, dict)

        # Should return successful response (status_code < 400)
        assert isinstance(response["status_code"], int)
        assert response["status_code"] < 400
        data = response["data"]
        assert isinstance(data, dict)
        assert isinstance(data["item"], dict)
        assert data["id"] == 999
        assert data["item"]["name"] == "New Item"
        assert data["item"]["price"] == 50.0
        assert data["total_price"] == 55.0

    def test_post_request_with_list_data(self, mock_client: CogniteClient) -> None:
        """Test POST request with list data for batch processing."""
        items_data = [
            {"name": "Item 1", "price": 100.0, "tax": 10.0},
            {"name": "Item 2", "price": 200.0, "tax": 20.0},
        ]

        request_data: dict[str, Any] = {
            "path": "/process/batch",
            "method": "POST",
            "body": {"items": items_data},
        }

        response = self.handle(client=mock_client, data=request_data)
        assert isinstance(response, dict)

        # Should return successful response (status_code < 400)
        assert isinstance(response["status_code"], int)
        assert response["status_code"] < 400
        data = response["data"]
        assert isinstance(data, dict)
        assert data["processed_count"] == 2
        assert data["total_value"] == 330.0  # (100+10) + (200+20)

    def test_route_not_found_error(self, mock_client: CogniteClient) -> None:
        """Test error handling for non-existent routes."""
        request_data: dict[str, Any] = {
            "path": "/nonexistent/route",
            "method": "GET",
            "body": {},
        }

        response = self.handle(client=mock_client, data=request_data)
        assert isinstance(response, dict)

        # Should return error response (status_code >= 400)
        assert isinstance(response["status_code"], int)
        assert response["status_code"] >= 400
        assert response["error_type"] == "RouteNotFound"
        assert isinstance(response["message"], str)
        assert "No route found" in response["message"]
        assert isinstance(response["details"], dict)
        assert "available_routes" in response["details"]

    def test_route_not_found_includes_all_composed_app_routes(self, mock_client: CogniteClient) -> None:
        """Test that RouteNotFound error includes routes from all composed apps."""
        # Create a second app with different routes
        app2 = FunctionApp(title="Second App", version="1.0.0")

        @app2.get("/app2/users/{user_id}")
        def get_user(client: CogniteClient, user_id: int) -> dict[str, Any]:
            """Get a user from app2."""
            return {"user_id": user_id, "name": "Test User"}

        @app2.post("/app2/users/")
        def create_user(client: CogniteClient, name: str) -> dict[str, Any]:
            """Create a user in app2."""
            return {"user_id": 1, "name": name}

        # Compose apps together
        composed_handle = create_function_service(self.app, app2)

        # Request a non-existent route
        request_data: dict[str, Any] = {
            "path": "/nonexistent/route",
            "method": "GET",
            "body": {},
        }

        response = composed_handle(client=mock_client, data=request_data)
        assert isinstance(response, dict)

        # Should return error response (status_code >= 400)
        assert isinstance(response["status_code"], int)
        assert response["status_code"] >= 400
        assert response["error_type"] == "RouteNotFound"
        assert isinstance(response["details"], dict)
        # Check that available_routes includes routes from both apps
        available_routes = response["details"]["available_routes"]
        assert isinstance(available_routes, list)

        # Routes from first app (self.app)
        assert "/items/{item_id}" in available_routes
        assert "/items/" in available_routes
        assert "/process/batch" in available_routes

        # Routes from second app (app2)
        assert "/app2/users/{user_id}" in available_routes
        assert "/app2/users/" in available_routes

        # Should have at least 5 routes total
        assert len(available_routes) >= 5

    def test_method_not_allowed_error(self, mock_client: CogniteClient) -> None:
        """Test error handling for unsupported methods on existing routes."""
        # Try DELETE on /items/123 (only GET is supported)
        request_data: dict[str, Any] = {
            "path": "/items/123",
            "method": "DELETE",
            "body": {},
        }

        response = self.handle(client=mock_client, data=request_data)

        # Should return error response (status_code >= 400)
        assert isinstance(response, dict)
        assert isinstance(response["status_code"], int)
        assert response["status_code"] >= 400
        assert response["error_type"] == "RouteNotFound"

    def test_invalid_path_parameter_type(self, mock_client: CogniteClient) -> None:
        """Test error handling for invalid path parameter types."""
        # Try to pass string where int is expected
        request_data: dict[str, Any] = {
            "path": "/items/not-a-number",
            "method": "GET",
            "body": {},
        }

        response = self.handle(client=mock_client, data=request_data)

        # Should return error response (status_code >= 400)
        assert isinstance(response, dict)
        assert isinstance(response["status_code"], int)
        assert response["status_code"] >= 400
        assert response["error_type"] == "ValidationError"

    def test_invalid_request_body(self, mock_client: CogniteClient) -> None:
        """Test error handling for invalid request body."""
        # Missing required field in item
        invalid_item_data: dict[str, Any] = {
            "name": "Item without price"
            # Missing required 'price' field
        }

        request_data: dict[str, Any] = {
            "path": "/items/",
            "method": "POST",
            "body": {"item": invalid_item_data},
        }

        response = self.handle(client=mock_client, data=request_data)

        # Should return error response (status_code >= 400)
        assert isinstance(response, dict)
        assert isinstance(response["status_code"], int)
        assert response["status_code"] >= 400
        assert response["error_type"] == "ValidationError"

    def test_malformed_request_data(self, mock_client: CogniteClient) -> None:
        """Test error handling for malformed request data."""
        # Invalid request data structure
        invalid_request_data = {
            "path": "/items/123",
            "method": 123,  # Should be string
            "body": "not a dict",  # Should be dict
        }

        response: Any = self.handle(client=mock_client, data=invalid_request_data)

        # Should return error response (status_code >= 400)
        assert isinstance(response["status_code"], int)
        assert response["status_code"] >= 400
        assert response["error_type"] == "ValidationError"

    def test_default_method_handling(self, mock_client: CogniteClient) -> None:
        """Test handling of default method (POST) when not specified."""
        request_data = {
            "path": "/process/batch",
            # No method specified, should default to POST
            "body": {"items": [{"name": "Item", "price": 100.0}]},
        }

        response = self.handle(client=mock_client, data=request_data)

        # Should work with default method (status_code < 400)
        assert isinstance(response, dict)
        assert isinstance(response["status_code"], int)
        assert response["status_code"] < 400
        assert isinstance(response["data"], dict)
        assert response["data"]["processed_count"] == 1

    def test_client_parameter_injection(self, mock_client: CogniteClient) -> None:
        """Test that CogniteClient is properly injected into route functions."""

        # Add a route that uses the client
        @self.app.get("/client-test")
        def client_test(client: CogniteClient) -> dict[str, str]:
            """Test client injection."""
            return {"client_type": type(client).__name__}

        # Recreate handler with new route
        handle = create_function_service(self.app)

        request_data: dict[str, Any] = {
            "path": "/client-test",
            "method": "GET",
            "body": {},
        }

        response: Any = handle(client=mock_client, data=request_data)

        # Should work and show that client was injected (status_code < 400)
        assert isinstance(response["status_code"], int)
        assert response["status_code"] < 400
        # The exact type might be Mock, but the important thing is it was passed


class TestAcceptHeaderRouting:
    """Test content negotiation via Accept header."""

    def setup_method(self) -> None:
        """Set up test app with routes that have different accept values."""
        self.app = FunctionApp(title="Content Negotiation App", version="1.0.0")

        @self.app.get("/items/{item_id}", accept="application/json")
        def get_item_json(client: CogniteClient, item_id: int) -> dict[str, Any]:
            """Get item as JSON."""
            return {"id": item_id, "format": "json"}

        @self.app.get("/items/{item_id}", accept="text/html", content_type="text/html")
        def get_item_html(client: CogniteClient, item_id: int) -> str:
            """Get item as HTML."""
            return f"<html><body>Item {item_id}</body></html>"

        @self.app.get("/data", accept=None)  # Default fallback
        def get_data_default(client: CogniteClient) -> dict[str, str]:
            """Default data endpoint."""
            return {"format": "default"}

        self.handle = create_function_service(self.app)

    def test_accept_header_routes_to_json_handler(self, mock_client: CogniteClient) -> None:
        """Test that Accept: application/json routes to JSON handler."""
        request_data: dict[str, Any] = {
            "path": "/items/123",
            "method": "GET",
            "body": {},
            "headers": {"accept": "application/json"},
        }

        response: Any = self.handle(client=mock_client, data=request_data)
        assert response["status_code"] == 200
        assert response["data"]["format"] == "json"
        assert response["data"]["id"] == 123

    def test_accept_header_routes_to_html_handler(self, mock_client: CogniteClient) -> None:
        """Test that Accept: text/html routes to HTML handler."""
        request_data: dict[str, Any] = {
            "path": "/items/456",
            "method": "GET",
            "body": {},
            "headers": {"accept": "text/html"},
        }

        response: Any = self.handle(client=mock_client, data=request_data)
        assert response["status_code"] == 200
        assert "<html>" in response["data"]
        assert "456" in response["data"]

    def test_no_accept_header_uses_first_matching_route(self, mock_client: CogniteClient) -> None:
        """Test that missing Accept header uses first matching route."""
        request_data: dict[str, Any] = {
            "path": "/items/789",
            "method": "GET",
            "body": {},
            # No headers
        }

        response: Any = self.handle(client=mock_client, data=request_data)
        assert response["status_code"] == 200
        # Without Accept header, first route that matches (JSON) should be used
        assert response["data"]["format"] == "json"

    def test_wildcard_accept_matches(self, mock_client: CogniteClient) -> None:
        """Test that Accept: */* matches a route."""
        request_data: dict[str, Any] = {
            "path": "/items/100",
            "method": "GET",
            "body": {},
            "headers": {"accept": "*/*"},
        }

        response: Any = self.handle(client=mock_client, data=request_data)
        assert response["status_code"] == 200
        # Wildcard should match first registered route (JSON in this case)
        assert response["data"]["format"] == "json"
        assert response["data"]["id"] == 100

    def test_fallback_route_used_when_no_specific_match(self, mock_client: CogniteClient) -> None:
        """Test that fallback route (accept=None) is used for unmatched Accept."""
        request_data: dict[str, Any] = {
            "path": "/data",
            "method": "GET",
            "body": {},
            "headers": {"accept": "application/xml"},  # Not specifically handled
        }

        response: Any = self.handle(client=mock_client, data=request_data)
        assert response["status_code"] == 200
        assert response["data"]["format"] == "default"

    def test_no_matching_accept_returns_406_not_acceptable(self, mock_client: CogniteClient) -> None:
        """Test that 406 Not Acceptable is returned when Accept header doesn't match any route."""
        # Create an app with only specific accept handlers (no fallback)
        app = FunctionApp(title="Strict Accept App", version="1.0.0")

        @app.get("/strict", accept="application/json")
        def get_json_only(client: CogniteClient) -> dict[str, str]:
            """Only accepts application/json."""
            return {"format": "json"}

        @app.get("/strict", accept="text/html", content_type="text/html")
        def get_html_only(client: CogniteClient) -> str:
            """Only accepts text/html."""
            return "<html>HTML</html>"

        handle = create_function_service(app)

        # Request with Accept header that doesn't match any route
        request_data: dict[str, Any] = {
            "path": "/strict",
            "method": "GET",
            "body": {},
            "headers": {"accept": "application/xml"},  # Not handled by any route
        }

        response: Any = handle(client=mock_client, data=request_data)

        # Should return 406 Not Acceptable
        assert response["status_code"] == 406
        assert response["error_type"] == "NotAcceptable"
        assert "accept" in response.get("message", "").lower()
        assert "application/xml" in response.get("message", "")
        assert "available_content_types" in response.get("details", {})
        assert response["details"]["available_content_types"] == ["application/json", "text/html"]


class TestResponseContentTypeHeaders:
    """Test that response includes correct content-type headers."""

    def setup_method(self) -> None:
        """Set up test app with routes having different content types."""
        self.app = FunctionApp(title="Content Type App", version="1.0.0")

        @self.app.get("/json-data")
        def get_json(client: CogniteClient) -> dict[str, str]:
            """Default JSON response."""
            return {"key": "value"}

        @self.app.get("/html-page", content_type="text/html")
        def get_html(client: CogniteClient) -> str:
            """HTML response."""
            return "<html><body>Hello</body></html>"

        @self.app.get("/plain-text", content_type="text/plain")
        def get_text(client: CogniteClient) -> str:
            """Plain text response."""
            return "Hello, World!"

        @self.app.post("/items", status_code=201)
        def create_item(client: CogniteClient, name: str) -> dict[str, Any]:
            """Create item with 201 status."""
            return {"id": 1, "name": name}

        self.handle = create_function_service(self.app)

    def test_default_content_type_is_json(self, mock_client: CogniteClient) -> None:
        """Test that default response has application/json content-type header."""
        request_data: dict[str, Any] = {
            "path": "/json-data",
            "method": "GET",
            "body": {},
        }

        response: Any = self.handle(client=mock_client, data=request_data)
        assert response["status_code"] < 400
        assert "headers" in response
        assert response["headers"]["content-type"] == "application/json"

    def test_html_content_type_in_response(self, mock_client: CogniteClient) -> None:
        """Test that HTML route returns text/html content-type header."""
        request_data: dict[str, Any] = {
            "path": "/html-page",
            "method": "GET",
            "body": {},
        }

        response: Any = self.handle(client=mock_client, data=request_data)
        assert response["status_code"] < 400
        assert "headers" in response
        assert response["headers"]["content-type"] == "text/html"

    def test_plain_text_content_type_in_response(self, mock_client: CogniteClient) -> None:
        """Test that text/plain route returns correct content-type header."""
        request_data: dict[str, Any] = {
            "path": "/plain-text",
            "method": "GET",
            "body": {},
        }

        response: Any = self.handle(client=mock_client, data=request_data)
        assert response["status_code"] < 400
        assert "headers" in response
        assert response["headers"]["content-type"] == "text/plain"

    def test_custom_status_code_with_content_type(self, mock_client: CogniteClient) -> None:
        """Test that custom status code works alongside content-type."""
        request_data: dict[str, Any] = {
            "path": "/items",
            "method": "POST",
            "body": {"name": "Test Item"},
        }

        response: Any = self.handle(client=mock_client, data=request_data)
        assert response["status_code"] == 201  # Custom status code
        assert "headers" in response
        assert response["headers"]["content-type"] == "application/json"
        assert response["data"]["name"] == "Test Item"
