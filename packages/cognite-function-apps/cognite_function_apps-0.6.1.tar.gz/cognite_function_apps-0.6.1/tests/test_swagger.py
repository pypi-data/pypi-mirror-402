"""Tests for Swagger UI middleware."""
# pyright: reportPrivateUsage=false

import json
from http import HTTPStatus
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
from cognite.client import CogniteClient

from cognite_function_apps import FunctionApp, create_function_service
from cognite_function_apps.devserver.asgi import ASGIHttpScope

# Import private functions for testing
from cognite_function_apps.devserver.swagger import (
    SwaggerMiddleware,
    _send_html_response,
    _send_json_response,
    _serve_openapi_json,
    _serve_swagger_ui,
)
from cognite_function_apps.introspection import create_introspection_app

from .conftest import TestItem as Item
from .conftest import TestItemResponse as ItemResponse


def _create_http_scope(path: str, method: str = "GET") -> ASGIHttpScope:
    """Create a properly typed ASGI HTTP scope for testing.

    Args:
        path: Request path
        method: HTTP method

    Returns:
        ASGIHttpScope: Properly typed ASGI scope
    """
    return ASGIHttpScope(
        type="http",
        path=path,
        method=method,
        query_string=b"",
        headers=[],
        client=("127.0.0.1", 8000),
        server=("127.0.0.1", 8000),
        state={},
    )


class TestSwaggerHelperFunctions:
    """Test helper functions for sending responses."""

    @pytest.mark.asyncio
    async def test_send_html_response(self) -> None:
        """Test sending HTML response."""
        messages: list[dict[str, Any]] = []

        async def mock_send(message: dict[str, Any]) -> None:
            messages.append(message)

        html_content = "<html><body>Test</body></html>"
        await _send_html_response(mock_send, html_content)  # type: ignore[arg-type]

        # Should send two messages: start and body
        assert len(messages) == 2

        # Check start message
        start = messages[0]
        assert start["type"] == "http.response.start"
        assert start["status"] == HTTPStatus.OK
        assert (b"content-type", b"text/html; charset=utf-8") in start["headers"]
        assert (b"access-control-allow-origin", b"*") in start["headers"]

        # Check body message
        body = messages[1]
        assert body["type"] == "http.response.body"
        assert body["body"] == html_content.encode("utf-8")
        assert body["more_body"] is False

    @pytest.mark.asyncio
    async def test_send_html_response_with_custom_status(self) -> None:
        """Test sending HTML response with custom status."""
        messages: list[dict[str, Any]] = []

        async def mock_send(message: dict[str, Any]) -> None:
            messages.append(message)

        html_content = "<html><body>Not Found</body></html>"
        await _send_html_response(mock_send, html_content, status=HTTPStatus.NOT_FOUND)  # type: ignore[arg-type]

        # Check status
        start = messages[0]
        assert start["status"] == HTTPStatus.NOT_FOUND

    @pytest.mark.asyncio
    async def test_send_json_response(self) -> None:
        """Test sending JSON response."""
        messages: list[dict[str, Any]] = []

        async def mock_send(message: dict[str, Any]) -> None:
            messages.append(message)

        data = {"key": "value", "number": 42}
        await _send_json_response(mock_send, data)  # type: ignore[arg-type]

        # Should send two messages: start and body
        assert len(messages) == 2

        # Check start message
        start = messages[0]
        assert start["type"] == "http.response.start"
        assert start["status"] == HTTPStatus.OK
        assert (b"content-type", b"application/json") in start["headers"]
        assert (b"access-control-allow-origin", b"*") in start["headers"]

        # Check body message
        body = messages[1]
        assert body["type"] == "http.response.body"
        assert b"key" in body["body"]
        assert b"value" in body["body"]
        assert body["more_body"] is False

    @pytest.mark.asyncio
    async def test_send_json_response_with_custom_status(self) -> None:
        """Test sending JSON response with custom status."""
        messages: list[dict[str, Any]] = []

        async def mock_send(message: dict[str, Any]) -> None:
            messages.append(message)

        data = {"error": "not found"}
        await _send_json_response(mock_send, data, status=HTTPStatus.NOT_FOUND)  # type: ignore[arg-type]

        # Check status
        start = messages[0]
        assert start["status"] == HTTPStatus.NOT_FOUND


class TestSwaggerUIServing:
    """Test Swagger UI HTML serving."""

    @pytest.mark.asyncio
    async def test_serve_swagger_ui(self) -> None:
        """Test serving Swagger UI HTML."""
        messages: list[dict[str, Any]] = []

        async def mock_send(message: dict[str, Any]) -> None:
            messages.append(message)

        await _serve_swagger_ui(mock_send)  # type: ignore[arg-type]

        # Should send HTML response
        assert len(messages) == 2

        # Check body contains Swagger UI components
        body = messages[1]["body"].decode("utf-8")
        assert "swagger-ui" in body
        assert "SwaggerUIBundle" in body
        assert "/openapi.json" in body
        assert "<!DOCTYPE html>" in body


class TestOpenAPIJSONServing:
    """Test OpenAPI JSON serving."""

    @pytest.mark.asyncio
    async def test_serve_openapi_json_success(self, mock_client: CogniteClient, test_app: FunctionApp) -> None:
        """Test serving OpenAPI JSON when schema endpoint exists."""

        # Add a route to test app
        @test_app.get("/items/{item_id}")
        def get_item(client: CogniteClient, item_id: int) -> ItemResponse:
            item = Item(name="Test Item", price=100.0)
            return ItemResponse(id=item_id, item=item, total_price=100.0)

        # Create handler with introspection app for schema endpoint
        introspection_app = create_introspection_app()
        handle = create_function_service(introspection_app, test_app)

        messages: list[dict[str, Any]] = []

        async def mock_send(message: dict[str, Any]) -> None:
            messages.append(message)

        await _serve_openapi_json(mock_send, handle, mock_client)  # type: ignore[arg-type]

        # Should send JSON response
        assert len(messages) == 2

        # Check it's a valid OpenAPI response
        body_bytes = messages[1]["body"]

        openapi_spec = json.loads(body_bytes.decode("utf-8"))
        assert "openapi" in openapi_spec
        assert "info" in openapi_spec
        assert "paths" in openapi_spec
        assert openapi_spec["openapi"].startswith("3.")

    @pytest.mark.asyncio
    async def test_serve_openapi_json_route_not_found(self, mock_client: CogniteClient, test_app: FunctionApp) -> None:
        """Test serving OpenAPI JSON when schema endpoint doesn't exist."""
        # Create handler WITHOUT introspection app (no schema endpoint)
        handle = create_function_service(test_app)

        messages: list[dict[str, Any]] = []

        async def mock_send(message: dict[str, Any]) -> None:
            messages.append(message)

        await _serve_openapi_json(mock_send, handle, mock_client)  # type: ignore[arg-type]

        # Should still send a valid OpenAPI spec with error message
        assert len(messages) == 2

        # Check the error spec
        body_bytes = messages[1]["body"]

        error_spec = json.loads(body_bytes.decode("utf-8"))
        assert "openapi" in error_spec
        assert error_spec["info"]["title"] == "Schema Unavailable"
        assert "IntrospectionApp" in error_spec["info"]["description"]
        assert error_spec["paths"] == {}

    @pytest.mark.asyncio
    async def test_serve_openapi_json_other_error(self, mock_client: CogniteClient) -> None:
        """Test serving OpenAPI JSON when other error occurs."""
        # Create a handle that returns an error
        mock_handle = Mock()
        mock_handle.async_handle = AsyncMock(
            return_value={"status_code": 400, "error_type": "ValidationError", "message": "Test error", "headers": {}}
        )

        messages: list[dict[str, Any]] = []

        async def mock_send(message: dict[str, Any]) -> None:
            messages.append(message)

        await _serve_openapi_json(mock_send, mock_handle, mock_client)  # type: ignore[arg-type]

        # Should still send a valid OpenAPI spec with error message
        assert len(messages) == 2

        # Check the error spec
        body_bytes = messages[1]["body"]

        error_spec = json.loads(body_bytes.decode("utf-8"))
        assert "openapi" in error_spec
        assert error_spec["info"]["title"] == "Schema Error"
        assert "Test error" in error_spec["info"]["description"]


class TestSwaggerMiddleware:
    """Test SwaggerMiddleware class."""

    @pytest.mark.asyncio
    async def test_middleware_serves_docs(self, mock_client: CogniteClient, test_app: FunctionApp) -> None:
        """Test middleware intercepts /docs requests."""
        handle = create_function_service(test_app)

        # Create a mock app that should not be called
        mock_next_app = AsyncMock()

        middleware = SwaggerMiddleware(mock_next_app, handle, mock_client)

        messages: list[dict[str, Any]] = []

        async def mock_send(message: dict[str, Any]) -> None:
            messages.append(message)

        async def mock_receive() -> dict[str, Any]:
            return {"type": "http.request", "body": b"", "more_body": False}

        scope = _create_http_scope("/docs")

        await middleware(scope, mock_receive, mock_send)  # type: ignore[arg-type]

        # Should intercept and serve Swagger UI
        assert len(messages) == 2
        body = messages[1]["body"].decode("utf-8")
        assert "swagger-ui" in body

        # Next app should NOT be called
        mock_next_app.assert_not_called()

    @pytest.mark.asyncio
    async def test_middleware_serves_openapi_json(self, mock_client: CogniteClient, test_app: FunctionApp) -> None:
        """Test middleware intercepts /openapi.json requests."""
        introspection_app = create_introspection_app()
        handle = create_function_service(introspection_app, test_app)

        # Create a mock app that should not be called
        mock_next_app = AsyncMock()

        middleware = SwaggerMiddleware(mock_next_app, handle, mock_client)

        messages: list[dict[str, Any]] = []

        async def mock_send(message: dict[str, Any]) -> None:
            messages.append(message)

        async def mock_receive() -> dict[str, Any]:
            return {"type": "http.request", "body": b"", "more_body": False}

        scope = _create_http_scope("/openapi.json")

        await middleware(scope, mock_receive, mock_send)  # type: ignore[arg-type]

        # Should intercept and serve OpenAPI JSON
        assert len(messages) == 2

        openapi_spec = json.loads(messages[1]["body"].decode("utf-8"))
        assert "openapi" in openapi_spec

        # Next app should NOT be called
        mock_next_app.assert_not_called()

    @pytest.mark.asyncio
    async def test_middleware_passes_through_other_requests(
        self, mock_client: CogniteClient, test_app: FunctionApp
    ) -> None:
        """Test middleware passes through non-docs requests."""
        handle = create_function_service(test_app)

        # Create a mock app that should be called
        mock_next_app = AsyncMock()

        middleware = SwaggerMiddleware(mock_next_app, handle, mock_client)

        async def mock_send(message: dict[str, Any]) -> None:
            pass

        async def mock_receive() -> dict[str, Any]:
            return {"type": "http.request", "body": b"", "more_body": False}

        scope = _create_http_scope("/api/items")

        await middleware(scope, mock_receive, mock_send)  # type: ignore[arg-type]

        # Next app SHOULD be called
        mock_next_app.assert_called_once()

    @pytest.mark.asyncio
    async def test_middleware_passes_through_non_http_scope(
        self, mock_client: CogniteClient, test_app: FunctionApp
    ) -> None:
        """Test middleware passes through non-HTTP scopes (like WebSocket)."""
        handle = create_function_service(test_app)

        # Create a mock app that should be called
        mock_next_app = AsyncMock()

        middleware = SwaggerMiddleware(mock_next_app, handle, mock_client)

        async def mock_send(message: dict[str, Any]) -> None:
            pass

        async def mock_receive() -> dict[str, Any]:
            return {"type": "websocket.connect"}

        # WebSocket scope (not HTTP, so we don't use the helper)
        scope: dict[str, Any] = {
            "type": "websocket",
            "path": "/ws",
            "headers": [],
            "client": ("127.0.0.1", 8000),
            "server": ("127.0.0.1", 8000),
            "state": {},
        }

        await middleware(scope, mock_receive, mock_send)  # type: ignore[arg-type]

        # Next app SHOULD be called for websocket
        mock_next_app.assert_called_once()


class TestSwaggerIntegration:
    """Integration tests for Swagger middleware with real routes."""

    @pytest.mark.asyncio
    async def test_swagger_with_complex_app(self, mock_client: CogniteClient) -> None:
        """Test Swagger middleware with a complex app with multiple routes."""
        app = FunctionApp(title="E-Commerce API", version="2.0.0")

        @app.get("/products/{product_id}")
        def get_product(client: CogniteClient, product_id: int, include_stock: bool = False) -> dict[str, Any]:
            """Get product by ID."""
            return {"id": product_id, "name": "Product", "include_stock": include_stock}

        @app.post("/products")
        def create_product(client: CogniteClient, item: Item) -> ItemResponse:
            """Create a new product."""
            return ItemResponse(id=123, item=item, total_price=item.price)

        @app.delete("/products/{product_id}")
        def delete_product(client: CogniteClient, product_id: int) -> dict[str, str]:
            """Delete a product."""
            return {"status": "deleted", "id": str(product_id)}

        introspection_app = create_introspection_app()
        handle = create_function_service(introspection_app, app)
        middleware = SwaggerMiddleware(AsyncMock(), handle, mock_client)

        messages: list[dict[str, Any]] = []

        async def mock_send(message: dict[str, Any]) -> None:
            messages.append(message)

        async def mock_receive() -> dict[str, Any]:
            return {"type": "http.request", "body": b"", "more_body": False}

        scope = _create_http_scope("/openapi.json")

        await middleware(scope, mock_receive, mock_send)  # type: ignore[arg-type]

        # Parse the OpenAPI spec
        openapi_spec = json.loads(messages[1]["body"].decode("utf-8"))

        # Check it includes all our routes
        assert openapi_spec["info"]["title"] == "E-Commerce API"
        assert openapi_spec["info"]["version"] == "2.0.0"
        assert "/products/{product_id}" in openapi_spec["paths"]
        assert "/products" in openapi_spec["paths"]

        # Check HTTP methods
        product_path = openapi_spec["paths"]["/products/{product_id}"]
        assert "get" in product_path
        assert "delete" in product_path

        products_path = openapi_spec["paths"]["/products"]
        assert "post" in products_path

    @pytest.mark.asyncio
    async def test_swagger_ui_html_structure(self, mock_client: CogniteClient, test_app: FunctionApp) -> None:
        """Test that Swagger UI HTML has correct structure and security."""
        handle = create_function_service(test_app)
        middleware = SwaggerMiddleware(AsyncMock(), handle, mock_client)

        messages: list[dict[str, Any]] = []

        async def mock_send(message: dict[str, Any]) -> None:
            messages.append(message)

        async def mock_receive() -> dict[str, Any]:
            return {"type": "http.request", "body": b"", "more_body": False}

        scope = _create_http_scope("/docs")

        await middleware(scope, mock_receive, mock_send)  # type: ignore[arg-type]

        html = messages[1]["body"].decode("utf-8")

        # Check essential HTML structure
        assert "<!DOCTYPE html>" in html
        assert '<html lang="en">' in html
        assert '<meta charset="UTF-8">' in html
        assert "<title>Function Apps API - Swagger UI</title>" in html

        # Check Swagger UI assets are loaded with integrity hashes (security)
        assert "swagger-ui-dist" in html
        assert "integrity=" in html
        assert "crossorigin=" in html

        # Check Swagger configuration
        assert 'url: "/openapi.json"' in html
        assert "SwaggerUIBundle" in html
        assert "deepLinking: true" in html
        assert 'docExpansion: "list"' in html
        assert "filter: true" in html

    @pytest.mark.asyncio
    async def test_cors_headers_present(self, mock_client: CogniteClient, test_app: FunctionApp) -> None:
        """Test that CORS headers are present in responses."""
        handle = create_function_service(test_app)
        middleware = SwaggerMiddleware(AsyncMock(), handle, mock_client)

        messages: list[dict[str, Any]] = []

        async def mock_send(message: dict[str, Any]) -> None:
            messages.append(message)

        async def mock_receive() -> dict[str, Any]:
            return {"type": "http.request", "body": b"", "more_body": False}

        # Test /docs endpoint
        scope = _create_http_scope("/docs")

        await middleware(scope, mock_receive, mock_send)  # type: ignore[arg-type]

        # Check CORS headers in response
        headers = messages[0]["headers"]
        header_dict = {k.decode(): v.decode() for k, v in headers}

        assert "access-control-allow-origin" in header_dict
        assert header_dict["access-control-allow-origin"] == "*"
        assert "access-control-allow-methods" in header_dict
        assert "access-control-allow-headers" in header_dict
