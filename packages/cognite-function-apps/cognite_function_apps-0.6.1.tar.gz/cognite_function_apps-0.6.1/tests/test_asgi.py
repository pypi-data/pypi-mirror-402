"""Tests for ASGI adapter module."""
# pyright: reportPrivateUsage=false

import json
from http import HTTPStatus
from typing import Any
from unittest.mock import Mock

import pytest
from cognite.client import CogniteClient
from pytest import MonkeyPatch

from cognite_function_apps.app import FunctionApp
from cognite_function_apps.devserver.asgi import (
    ASGIHttpRequestMessage,
    ASGIHttpResponseBodyMessage,
    ASGIHttpResponseStartMessage,
    ASGIHttpScope,
    _read_body,
    _run_cognite_asgi_app,
    _send_json_response,
    asgi_error_handler,
    create_asgi_app,
    create_synthetic_function_call_info,
)
from cognite_function_apps.models import DataDict
from cognite_function_apps.service import create_function_service

from .conftest import TestItem as Item
from .conftest import TestItemResponse as ItemResponse


def _create_http_scope(path: str, method: str = "GET", query_string: bytes = b"") -> ASGIHttpScope:
    """Create a properly typed ASGI HTTP scope for testing."""
    return ASGIHttpScope(
        type="http",
        path=path,
        method=method,
        query_string=query_string,
        headers=[],
        client=("127.0.0.1", 12345),
        server=("localhost", 8000),
        state={},
    )


class TestSyntheticFunctionCallInfo:
    """Test creation of synthetic function call info for dev server."""

    def test_create_synthetic_function_call_info(self) -> None:
        """Test that synthetic call info is created with correct structure."""
        path = "/api/test"
        call_info = create_synthetic_function_call_info(path)

        assert call_info["function_id"] == "local-dev-server"
        assert call_info["call_id"].startswith("dev-")
        assert len(call_info["call_id"]) == 20  # "dev-" + 16 hex chars
        assert call_info["schedule_id"] is None
        assert call_info["scheduled_time"] is None

    def test_synthetic_call_info_unique_ids(self) -> None:
        """Test that each call generates a unique call_id."""
        call_info_1 = create_synthetic_function_call_info("/path1")
        call_info_2 = create_synthetic_function_call_info("/path2")

        assert call_info_1["call_id"] != call_info_2["call_id"]


class TestReadBody:
    """Test ASGI request body reading."""

    @pytest.mark.asyncio
    async def test_read_single_chunk(self) -> None:
        """Test reading request body in a single chunk."""
        body_data = b'{"name": "test"}'

        async def receive() -> ASGIHttpRequestMessage:
            return ASGIHttpRequestMessage(
                type="http.request",
                body=body_data,
                more_body=False,
            )

        body = await _read_body(receive)
        assert body == body_data

    @pytest.mark.asyncio
    async def test_read_multiple_chunks(self) -> None:
        """Test reading request body in multiple chunks."""
        chunks = [b'{"name":', b' "test"}']
        chunk_index = 0

        async def receive() -> ASGIHttpRequestMessage:
            nonlocal chunk_index
            if chunk_index < len(chunks):
                result = ASGIHttpRequestMessage(
                    type="http.request",
                    body=chunks[chunk_index],
                    more_body=chunk_index < len(chunks) - 1,
                )
                chunk_index += 1
                return result
            return ASGIHttpRequestMessage(
                type="http.request",
                body=b"",
                more_body=False,
            )

        body = await _read_body(receive)
        assert body == b'{"name": "test"}'

    @pytest.mark.asyncio
    async def test_read_empty_body(self) -> None:
        """Test reading empty request body."""

        async def receive() -> ASGIHttpRequestMessage:
            return ASGIHttpRequestMessage(
                type="http.request",
                body=b"",
                more_body=False,
            )

        body = await _read_body(receive)
        assert body == b""

    @pytest.mark.asyncio
    async def test_read_body_with_disconnect(self) -> None:
        """Test handling client disconnect during body read."""

        async def receive() -> ASGIHttpRequestMessage:
            return ASGIHttpRequestMessage(
                type="http.disconnect",  # type: ignore[typeddict-item]
                body=b"",
                more_body=False,
            )

        body = await _read_body(receive)
        assert body == b""


class TestSendJsonResponse:
    """Test ASGI JSON response sending."""

    @pytest.mark.asyncio
    async def test_send_success_response(self) -> None:
        """Test sending a successful JSON response."""
        messages: list[ASGIHttpResponseStartMessage | ASGIHttpResponseBodyMessage] = []

        async def send(message: ASGIHttpResponseStartMessage | ASGIHttpResponseBodyMessage) -> None:
            messages.append(message)

        response_data: DataDict = {"status_code": 200, "data": {"id": 123}, "headers": {}}
        await _send_json_response(send, response_data, status=HTTPStatus.OK)

        # Check response start
        assert len(messages) == 2
        start_msg = messages[0]
        assert start_msg["type"] == "http.response.start"
        if start_msg["type"] == "http.response.start":
            assert start_msg["status"] == HTTPStatus.OK
            headers_dict = dict(start_msg["headers"])
            assert headers_dict[b"content-type"] == b"application/json"
            assert b"access-control-allow-origin" in headers_dict

        # Check response body
        body_msg = messages[1]
        assert body_msg["type"] == "http.response.body"
        if body_msg["type"] == "http.response.body":
            body = json.loads(body_msg["body"])
            assert body == response_data
            assert body_msg["more_body"] is False

    @pytest.mark.asyncio
    async def test_send_error_response(self) -> None:
        """Test sending an error JSON response."""
        messages: list[ASGIHttpResponseStartMessage | ASGIHttpResponseBodyMessage] = []

        async def send(message: ASGIHttpResponseStartMessage | ASGIHttpResponseBodyMessage) -> None:
            messages.append(message)

        error_data: DataDict = {
            "status_code": 400,
            "error_type": "ValidationError",
            "message": "Invalid input",
            "headers": {},
        }
        await _send_json_response(send, error_data, status=HTTPStatus.BAD_REQUEST)

        assert len(messages) == 2
        start_msg = messages[0]
        if start_msg["type"] == "http.response.start":
            assert start_msg["status"] == HTTPStatus.BAD_REQUEST
        body_msg = messages[1]
        if body_msg["type"] == "http.response.body":
            body = json.loads(body_msg["body"])
            assert body == error_data


class TestAsgiErrorHandler:
    """Test ASGI error handler decorator."""

    @pytest.mark.asyncio
    async def test_successful_request_passes_through(self) -> None:
        """Test that successful requests pass through without modification."""
        messages: list[ASGIHttpResponseStartMessage | ASGIHttpResponseBodyMessage] = []

        async def send(message: ASGIHttpResponseStartMessage | ASGIHttpResponseBodyMessage) -> None:
            messages.append(message)

        @asgi_error_handler
        async def app(scope: ASGIHttpScope, receive: Any, send: Any) -> None:
            await send(
                ASGIHttpResponseStartMessage(
                    type="http.response.start",
                    status=HTTPStatus.OK,
                    headers=[(b"content-type", b"text/plain")],
                    trailers=False,
                )
            )
            await send(
                ASGIHttpResponseBodyMessage(
                    type="http.response.body",
                    body=b"Success",
                    more_body=False,
                )
            )

        scope = _create_http_scope("/test")

        async def receive() -> ASGIHttpRequestMessage:
            return ASGIHttpRequestMessage(type="http.request", body=b"", more_body=False)

        await app(scope, receive, send)

        assert len(messages) == 2
        start_msg = messages[0]
        if start_msg["type"] == "http.response.start":
            assert start_msg["status"] == HTTPStatus.OK

    @pytest.mark.asyncio
    async def test_json_decode_error_handling(self) -> None:
        """Test that JSON decode errors are caught and formatted."""
        messages: list[ASGIHttpResponseStartMessage | ASGIHttpResponseBodyMessage] = []

        async def send(message: ASGIHttpResponseStartMessage | ASGIHttpResponseBodyMessage) -> None:
            messages.append(message)

        @asgi_error_handler
        async def app(scope: ASGIHttpScope, receive: Any, send: Any) -> None:
            # Simulate JSON decode error
            json.loads("{invalid json")

        scope = _create_http_scope("/test", "POST")

        async def receive() -> ASGIHttpRequestMessage:
            return ASGIHttpRequestMessage(type="http.request", body=b"", more_body=False)

        await app(scope, receive, send)

        # Check error response
        assert len(messages) == 2
        start_msg = messages[0]
        if start_msg["type"] == "http.response.start":
            assert start_msg["status"] == HTTPStatus.BAD_REQUEST
        body_msg = messages[1]
        if body_msg["type"] == "http.response.body":
            body = json.loads(body_msg["body"])
            assert body["status_code"] >= 400  # Error
            assert body["error_type"] == "InvalidJSON"
            assert "Invalid JSON" in body["message"]

    @pytest.mark.asyncio
    async def test_unexpected_exception_handling(self) -> None:
        """Test that unexpected exceptions are caught and formatted."""
        messages: list[ASGIHttpResponseStartMessage | ASGIHttpResponseBodyMessage] = []

        async def send(message: ASGIHttpResponseStartMessage | ASGIHttpResponseBodyMessage) -> None:
            messages.append(message)

        @asgi_error_handler
        async def app(scope: ASGIHttpScope, receive: Any, send: Any) -> None:
            raise ValueError("Unexpected error")

        scope = _create_http_scope("/test")

        async def receive() -> ASGIHttpRequestMessage:
            return ASGIHttpRequestMessage(type="http.request", body=b"", more_body=False)

        await app(scope, receive, send)

        # Check error response
        assert len(messages) == 2
        start_msg = messages[0]
        if start_msg["type"] == "http.response.start":
            assert start_msg["status"] == HTTPStatus.INTERNAL_SERVER_ERROR
        body_msg = messages[1]
        if body_msg["type"] == "http.response.body":
            body = json.loads(body_msg["body"])
            assert body["status_code"] >= 400  # Error
            assert body["error_type"] == "ServerError"
            assert body["details"]["exception_type"] == "ValueError"


class TestCreateAsgiApp:
    """Test ASGI app creation and routing."""

    @pytest.mark.asyncio
    async def test_create_asgi_app_basic(self, monkeypatch: MonkeyPatch) -> None:
        """Test creating a basic ASGI app from a FunctionService."""
        # Mock the get_cognite_client_from_env function
        mock_client = Mock(spec=CogniteClient)
        monkeypatch.setattr(
            "cognite_function_apps.devserver.asgi.get_cognite_client_from_env",
            lambda: mock_client,
        )

        # Create a simple app
        app = FunctionApp(title="Test App", version="1.0.0")

        @app.get("/test")
        def test_endpoint(client: CogniteClient) -> dict[str, str]:
            """Test endpoint."""
            return {"message": "Hello"}

        handle = create_function_service(app)
        asgi_app = create_asgi_app(handle)

        # Verify the app is callable
        assert callable(asgi_app)

    @pytest.mark.asyncio
    async def test_options_request_cors_preflight(self, monkeypatch: MonkeyPatch) -> None:
        """Test that OPTIONS requests return proper CORS headers."""
        mock_client = Mock(spec=CogniteClient)
        monkeypatch.setattr(
            "cognite_function_apps.devserver.asgi.get_cognite_client_from_env",
            lambda: mock_client,
        )

        app = FunctionApp(title="Test App", version="1.0.0")

        @app.post("/test")
        def test_endpoint(client: CogniteClient, data: dict[str, Any]) -> dict[str, Any]:
            """Test endpoint."""
            return {"received": data}

        handle = create_function_service(app)
        asgi_app = create_asgi_app(handle)

        messages: list[ASGIHttpResponseStartMessage | ASGIHttpResponseBodyMessage] = []

        async def send(message: ASGIHttpResponseStartMessage | ASGIHttpResponseBodyMessage) -> None:
            messages.append(message)

        scope = ASGIHttpScope(
            type="http",
            method="OPTIONS",
            path="/test",
            query_string=b"",
            headers=[(b"origin", b"https://example.com")],
            client=("127.0.0.1", 12345),
            server=("localhost", 8000),
            state={},
        )

        async def receive() -> ASGIHttpRequestMessage:
            return ASGIHttpRequestMessage(type="http.request", body=b"", more_body=False)

        await asgi_app(scope, receive, send)

        assert len(messages) == 2

        # Check response start
        start_msg = messages[0]
        assert start_msg["type"] == "http.response.start"
        assert start_msg["status"] == HTTPStatus.NO_CONTENT

        headers_dict = dict(start_msg["headers"])
        assert headers_dict[b"access-control-allow-origin"] == b"https://example.com"
        assert headers_dict[b"access-control-allow-methods"] == b"GET, POST, PUT, DELETE, OPTIONS"
        assert headers_dict[b"content-length"] == b"0"

        # Check response body
        body_msg = messages[1]
        assert body_msg["type"] == "http.response.body"
        assert body_msg["body"] == b""
        assert body_msg["more_body"] is False

    @pytest.mark.asyncio
    async def test_non_http_scope_ignored(self, monkeypatch: MonkeyPatch) -> None:
        """Test that non-HTTP scopes are ignored."""
        mock_client = Mock(spec=CogniteClient)
        monkeypatch.setattr(
            "cognite_function_apps.devserver.asgi.get_cognite_client_from_env",
            lambda: mock_client,
        )

        app = FunctionApp(title="Test App", version="1.0.0")

        @app.get("/test")
        def test_endpoint(client: CogniteClient) -> dict[str, str]:
            return {"message": "Hello"}

        handle = create_function_service(app)
        asgi_app = create_asgi_app(handle)  # ← Create real app

        messages: list[ASGIHttpResponseStartMessage | ASGIHttpResponseBodyMessage] = []

        async def send(message: ASGIHttpResponseStartMessage | ASGIHttpResponseBodyMessage) -> None:
            messages.append(message)

        # Websocket scope
        scope = ASGIHttpScope(
            type="websocket",  # type: ignore[typeddict-item] # Testing non-http type
            path="/ws",
            method="GET",
            query_string=b"",
            headers=[],
            client=("127.0.0.1", 12345),
            server=("localhost", 8000),
            state={},
        )

        async def receive() -> ASGIHttpRequestMessage:
            return ASGIHttpRequestMessage(type="websocket.connect")  # type: ignore[typeddict-item] # Testing non-http type

        await asgi_app(scope, receive, send)  # ← Test real app

        # Should not process websocket requests (no messages sent)
        assert len(messages) == 0


class TestAsgiIntegration:
    """Integration tests for ASGI app with actual routes."""

    @pytest.mark.asyncio
    async def test_get_request_integration(self, monkeypatch: MonkeyPatch) -> None:
        """Test a complete GET request through the ASGI app."""
        mock_client = Mock(spec=CogniteClient)
        monkeypatch.setattr(
            "cognite_function_apps.devserver.asgi.get_cognite_client_from_env",
            lambda: mock_client,
        )

        app = FunctionApp(title="Test App", version="1.0.0")

        @app.get("/items/{item_id}")
        def get_item(client: CogniteClient, item_id: int) -> dict[str, Any]:
            """Get an item."""
            return {"id": item_id, "name": f"Item {item_id}"}

        handle = create_function_service(app)
        asgi_app = create_asgi_app(handle)

        messages: list[ASGIHttpResponseStartMessage | ASGIHttpResponseBodyMessage] = []

        async def send(message: ASGIHttpResponseStartMessage | ASGIHttpResponseBodyMessage) -> None:
            messages.append(message)

        scope = _create_http_scope("/items/123")

        async def receive() -> ASGIHttpRequestMessage:
            return ASGIHttpRequestMessage(type="http.request", body=b"", more_body=False)

        await asgi_app(scope, receive, send)

        # Verify response
        assert len(messages) >= 2
        # Find the response body message
        body_msg = next(msg for msg in messages if msg.get("type") == "http.response.body")
        if body_msg["type"] == "http.response.body":
            body = json.loads(body_msg["body"])
            assert body["status_code"] < 400  # Success
            assert body["data"]["id"] == 123

    @pytest.mark.asyncio
    async def test_post_request_integration(self, monkeypatch: MonkeyPatch) -> None:
        """Test a complete POST request through the ASGI app."""
        mock_client = Mock(spec=CogniteClient)
        monkeypatch.setattr(
            "cognite_function_apps.devserver.asgi.get_cognite_client_from_env",
            lambda: mock_client,
        )

        app = FunctionApp(title="Test App", version="1.0.0")

        @app.post("/items")
        def create_item(client: CogniteClient, item: Item) -> ItemResponse:
            """Create an item."""
            return ItemResponse(id=456, item=item, total_price=item.price + (item.tax or 0))

        handle = create_function_service(app)
        asgi_app = create_asgi_app(handle)

        messages: list[ASGIHttpResponseStartMessage | ASGIHttpResponseBodyMessage] = []

        async def send(message: ASGIHttpResponseStartMessage | ASGIHttpResponseBodyMessage) -> None:
            messages.append(message)

        request_body = json.dumps({"item": {"name": "New Item", "price": 99.99, "tax": 10.0}}).encode("utf-8")

        scope = _create_http_scope("/items", "POST")

        async def receive() -> ASGIHttpRequestMessage:
            return ASGIHttpRequestMessage(type="http.request", body=request_body, more_body=False)

        await asgi_app(scope, receive, send)

        # Verify response
        assert len(messages) >= 2
        body_msg = next(msg for msg in messages if msg.get("type") == "http.response.body")
        assert body_msg["type"] == "http.response.body"
        body = json.loads(body_msg["body"])
        assert body["status_code"] < 400  # Success, f"Expected success but got: {body}"
        assert body["data"]["id"] == 456
        assert body["data"]["item"]["name"] == "New Item"
        assert body["data"]["total_price"] == 109.99

    @pytest.mark.asyncio
    async def test_get_with_query_parameters(self, monkeypatch: MonkeyPatch) -> None:
        """Test GET request with query parameters."""
        mock_client = Mock(spec=CogniteClient)
        monkeypatch.setattr(
            "cognite_function_apps.devserver.asgi.get_cognite_client_from_env",
            lambda: mock_client,
        )

        app = FunctionApp(title="Test App", version="1.0.0")

        @app.get("/items")
        def list_items(client: CogniteClient, limit: int = 10, offset: int = 0) -> dict[str, Any]:
            """List items with pagination."""
            return {"limit": limit, "offset": offset, "items": []}

        handle = create_function_service(app)
        asgi_app = create_asgi_app(handle)

        messages: list[ASGIHttpResponseStartMessage | ASGIHttpResponseBodyMessage] = []

        async def send(message: ASGIHttpResponseStartMessage | ASGIHttpResponseBodyMessage) -> None:
            messages.append(message)

        scope = _create_http_scope("/items", "GET", query_string=b"limit=50&offset=100")

        async def receive() -> ASGIHttpRequestMessage:
            return ASGIHttpRequestMessage(type="http.request", body=b"", more_body=False)

        await asgi_app(scope, receive, send)

        # Verify response
        assert len(messages) >= 2
        body_msg = next(msg for msg in messages if msg.get("type") == "http.response.body")
        assert body_msg["type"] == "http.response.body"
        body = json.loads(body_msg["body"])
        assert body["status_code"] < 400  # Success
        assert body["data"]["limit"] == 50
        assert body["data"]["offset"] == 100

    @pytest.mark.asyncio
    async def test_put_request_integration(self, monkeypatch: MonkeyPatch) -> None:
        """Test PUT request with body."""
        mock_client = Mock(spec=CogniteClient)
        monkeypatch.setattr(
            "cognite_function_apps.devserver.asgi.get_cognite_client_from_env",
            lambda: mock_client,
        )

        app = FunctionApp(title="Test App", version="1.0.0")

        @app.put("/items/{item_id}")
        def update_item(client: CogniteClient, item_id: int, item: Item) -> ItemResponse:
            """Update an item."""
            return ItemResponse(id=item_id, item=item, total_price=item.price + (item.tax or 0))

        handle = create_function_service(app)
        asgi_app = create_asgi_app(handle)

        messages: list[ASGIHttpResponseStartMessage | ASGIHttpResponseBodyMessage] = []

        async def send(message: ASGIHttpResponseStartMessage | ASGIHttpResponseBodyMessage) -> None:
            messages.append(message)

        request_body = json.dumps({"item": {"name": "Updated Item", "price": 150.0, "tax": 15.0}}).encode("utf-8")

        scope = _create_http_scope("/items/789", "PUT")

        async def receive() -> ASGIHttpRequestMessage:
            return ASGIHttpRequestMessage(type="http.request", body=request_body, more_body=False)

        await asgi_app(scope, receive, send)

        # Verify response
        assert len(messages) >= 2
        body_msg = next(msg for msg in messages if msg.get("type") == "http.response.body")
        assert body_msg["type"] == "http.response.body"
        body = json.loads(body_msg["body"])
        assert body["status_code"] < 400  # Success
        assert body["data"]["id"] == 789
        assert body["data"]["item"]["name"] == "Updated Item"
        assert body["data"]["total_price"] == 165.0

    @pytest.mark.asyncio
    async def test_delete_request_integration(self, monkeypatch: MonkeyPatch) -> None:
        """Test DELETE request."""
        mock_client = Mock(spec=CogniteClient)
        monkeypatch.setattr(
            "cognite_function_apps.devserver.asgi.get_cognite_client_from_env",
            lambda: mock_client,
        )

        app = FunctionApp(title="Test App", version="1.0.0")

        @app.delete("/items/{item_id}")
        def delete_item(client: CogniteClient, item_id: int) -> dict[str, Any]:
            """Delete an item."""
            return {"id": item_id, "deleted": True}

        handle = create_function_service(app)
        asgi_app = create_asgi_app(handle)

        messages: list[ASGIHttpResponseStartMessage | ASGIHttpResponseBodyMessage] = []

        async def send(message: ASGIHttpResponseStartMessage | ASGIHttpResponseBodyMessage) -> None:
            messages.append(message)

        scope = _create_http_scope("/items/999", "DELETE")

        async def receive() -> ASGIHttpRequestMessage:
            return ASGIHttpRequestMessage(type="http.request", body=b"", more_body=False)

        await asgi_app(scope, receive, send)

        # Verify response
        assert len(messages) >= 2
        body_msg = next(msg for msg in messages if msg.get("type") == "http.response.body")
        assert body_msg["type"] == "http.response.body"
        body = json.loads(body_msg["body"])
        assert body["status_code"] < 400  # Success
        assert body["data"]["id"] == 999
        assert body["data"]["deleted"] is True


class TestAsgiEdgeCases:
    """Test edge cases and error conditions in ASGI app."""

    @pytest.mark.asyncio
    async def test_multiple_response_sends_error(self, monkeypatch: MonkeyPatch) -> None:
        """Test that sending multiple responses raises an error."""
        mock_client = Mock(spec=CogniteClient)

        app = FunctionApp(title="Test App", version="1.0.0")

        # Create a misbehaving ASGI app that sends response twice
        original_asgi_app = app

        class DoubleSendApp:
            """ASGI app that sends response twice."""

            async def __call__(
                self,
                scope: Any,
                receive: Any,
                send: Any,
            ) -> None:
                """Send response twice to trigger error."""
                # Send first response
                await send(
                    {
                        "type": "cognite.function.response",
                        "body": {"status_code": 200, "data": {"first": True}, "headers": {}},
                    }
                )
                # Try to send second response (should fail)
                await send(
                    {
                        "type": "cognite.function.response",
                        "body": {"status_code": 200, "data": {"second": True}, "headers": {}},
                    }
                )

        handle = create_function_service(original_asgi_app)
        handle.asgi_app = DoubleSendApp()  # type: ignore[assignment]

        messages: list[ASGIHttpResponseStartMessage | ASGIHttpResponseBodyMessage] = []

        async def send(message: ASGIHttpResponseStartMessage | ASGIHttpResponseBodyMessage) -> None:
            messages.append(message)

        scope = _create_http_scope("/test", "GET")

        async def receive() -> ASGIHttpRequestMessage:
            return ASGIHttpRequestMessage(type="http.request", body=b"", more_body=False)

        # The error should be caught by asgi_error_handler
        with pytest.raises(RuntimeError, match="Response has already been sent"):
            await _run_cognite_asgi_app(handle, scope, receive, send, mock_client)

    @pytest.mark.asyncio
    async def test_no_response_sent_error(self, monkeypatch: MonkeyPatch) -> None:
        """Test that an app that doesn't send a response returns an error."""
        mock_client = Mock(spec=CogniteClient)

        app = FunctionApp(title="Test App", version="1.0.0")

        # Create an ASGI app that doesn't send any response
        original_asgi_app = app

        class NoResponseApp:
            """ASGI app that doesn't send a response."""

            async def __call__(
                self,
                scope: Any,
                receive: Any,
                send: Any,
            ) -> None:
                """Do nothing - don't send a response."""
                pass

        handle = create_function_service(original_asgi_app)
        handle.asgi_app = NoResponseApp()  # type: ignore[assignment]

        messages: list[ASGIHttpResponseStartMessage | ASGIHttpResponseBodyMessage] = []

        async def send(message: ASGIHttpResponseStartMessage | ASGIHttpResponseBodyMessage) -> None:
            messages.append(message)

        scope = _create_http_scope("/test", "GET")

        async def receive() -> ASGIHttpRequestMessage:
            return ASGIHttpRequestMessage(type="http.request", body=b"", more_body=False)

        await _run_cognite_asgi_app(handle, scope, receive, send, mock_client)

        # Verify error response was sent
        assert len(messages) >= 2
        body_msg = next(msg for msg in messages if msg.get("type") == "http.response.body")
        assert body_msg["type"] == "http.response.body"
        body = json.loads(body_msg["body"])
        assert body["status_code"] >= 400  # Error
        assert body["error_type"] == "InternalError"
        assert "did not send response" in body["message"]
