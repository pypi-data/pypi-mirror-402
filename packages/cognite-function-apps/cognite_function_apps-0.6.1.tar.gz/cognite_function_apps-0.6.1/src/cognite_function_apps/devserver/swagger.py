"""Swagger UI middleware for serving interactive API documentation.

This middleware intercepts requests to /docs and /openapi.json to serve
Swagger UI and the OpenAPI specification. All other requests are passed
through to the next app in the ASGI middleware chain.
"""

import json
from http import HTTPStatus

from cognite.client import CogniteClient

from cognite_function_apps.service import FunctionService

from .asgi import ASGIApp, ASGIHttpScope, ASGIReceive, ASGISend, create_synthetic_function_call_info


async def _send_html_response(send: ASGISend, html: str, status: HTTPStatus = HTTPStatus.OK) -> None:
    """Send HTML response via ASGI send.

    Args:
        send: ASGI send callable
        html: HTML content to send
        status: HTTP status code
    """
    body = html.encode("utf-8")

    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"text/html; charset=utf-8"),
                (b"content-length", str(len(body)).encode("utf-8")),
                # CORS headers for browser-based clients (Pyodide, JupyterLite)
                (b"access-control-allow-origin", b"*"),
                (b"access-control-allow-methods", b"GET, POST, PUT, DELETE, OPTIONS"),
                (b"access-control-allow-headers", b"content-type"),
            ],
            "trailers": False,
        }
    )

    await send(
        {
            "type": "http.response.body",
            "body": body,
            "more_body": False,
        }
    )


async def _serve_swagger_ui(send: ASGISend) -> None:
    """Serve Swagger UI HTML that loads the OpenAPI spec from /openapi.json.

    Args:
        send: ASGI send callable
    """
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Function Apps API - Swagger UI</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.29.4/swagger-ui.css"
          integrity="sha384-++DMKo1369T5pxDNqojF1F91bYxYiT1N7b1M15a7oCzEodfljztKlApQoH6eQSKI"
          crossorigin="anonymous">
    <style>
        html {
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }
        *, *:before, *:after {
            box-sizing: inherit;
        }
        body {
            margin: 0;
            padding: 0;
        }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.29.4/swagger-ui-bundle.js"
            integrity="sha384-eGAqzBSdqmAnsjFjrz0Ua2nJFnpAzDMmRg4mr6jwRwzcjSmL9FMmXAhMwX+mTFfs"
            crossorigin="anonymous"></script>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.29.4/swagger-ui-standalone-preset.js"
            integrity="sha384-Se2dMItBjKehkhvdy8ZDK8Qbj8wWIgvme6DMtaefAPiGI75QN4jG8LS/eFfkUxi2"
            crossorigin="anonymous"></script>
    <script>
        window.onload = function() {
            window.ui = SwaggerUIBundle({
                url: "/openapi.json",
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout",
                docExpansion: "list",
                filter: true,
                displayRequestDuration: true
            });
        };
    </script>
</body>
</html>
"""
    await _send_html_response(send, html)


async def _serve_openapi_json(send: ASGISend, handle: FunctionService, client: "CogniteClient") -> None:
    """Serve raw OpenAPI JSON for Swagger UI.

    This endpoint fetches the schema from /__schema__ and unwraps it from the
    framework's response envelope, providing the raw OpenAPI spec that tools expect.

    Args:
        send: ASGI send callable
        handle: FunctionService instance
        client: CogniteClient instance
    """
    # Call the /__schema__ endpoint to get the OpenAPI spec
    schema_data = await handle.async_handle(
        client=client,
        data={"path": "/__schema__", "method": "GET", "body": {}},
        secrets=None,
        function_call_info=create_synthetic_function_call_info(path="/__schema__"),
    )

    # Extract the actual schema from the response wrapper
    raw_status = schema_data.get("status_code", 500)
    status_code = int(raw_status) if isinstance(raw_status, (int, float)) else 500
    if status_code < 400 and "data" in schema_data:
        openapi_spec = schema_data["data"]
        await _send_json_response(send, openapi_spec, status=HTTPStatus.OK)
    # If there was an error, return a minimal valid OpenAPI spec with the error message
    # This ensures Swagger UI can display the error instead of showing "Not found"
    elif schema_data.get("error_type") == "RouteNotFound":
        # Extract available routes for helpful error message
        details = schema_data.get("details")
        available_routes: list[str] = []
        if isinstance(details, dict):
            routes = details.get("available_routes")
            if isinstance(routes, list):
                available_routes = [str(r) for r in routes]

        routes_text = ", ".join(available_routes) if available_routes else "None"

        # Create a minimal OpenAPI spec that explains the issue
        error_spec = {
            "openapi": "3.1.0",
            "info": {
                "title": "Schema Unavailable",
                "version": "1.0.0",
                "description": (
                    f"""
⚠️ **OpenAPI schema could not be generated**


This usually means the `IntrospectionApp` is not included in your function service composition.


**To fix this:**

```python
from cognite_function_apps import create_introspection_app
introspection = create_introspection_app()
handle = create_function_service(app, introspection)
```

**Available routes:** {routes_text}"
"""
                ),
            },
            "paths": {},
        }
        await _send_json_response(send, error_spec, status=HTTPStatus.OK)
    else:
        # For other errors, return a minimal spec with error details
        message = schema_data.get("message")
        error_message = str(message) if message is not None else "Unknown error"

        error_spec = {
            "openapi": "3.1.0",
            "info": {
                "title": "Schema Error",
                "version": "1.0.0",
                "description": f"⚠️ **Error generating schema:** {error_message}",
            },
            "paths": {},
        }
        await _send_json_response(send, error_spec, status=HTTPStatus.OK)


async def _send_json_response(send: ASGISend, data: object, status: HTTPStatus = HTTPStatus.OK) -> None:
    """Send JSON response via ASGI send.

    Args:
        send: ASGI send callable
        data: Data to serialize as JSON
        status: HTTP status code
    """
    body = json.dumps(data).encode("utf-8")

    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode("utf-8")),
                # CORS headers for browser-based clients (Pyodide, JupyterLite)
                (b"access-control-allow-origin", b"*"),
                (b"access-control-allow-methods", b"GET, POST, PUT, DELETE, OPTIONS"),
                (b"access-control-allow-headers", b"content-type"),
            ],
            "trailers": False,
        }
    )

    await send(
        {
            "type": "http.response.body",
            "body": body,
            "more_body": False,
        }
    )


class SwaggerMiddleware:
    """ASGI middleware that serves Swagger UI and OpenAPI documentation.

    This middleware intercepts requests to /docs and /openapi.json to serve
    interactive API documentation. All other requests are passed through to
    the next app in the ASGI middleware chain.

    Args:
        app: The next ASGI app in the middleware chain
        handle: FunctionService instance for accessing the OpenAPI schema
        client: CogniteClient instance for making API calls
    """

    def __init__(self, app: ASGIApp, handle: FunctionService, client: "CogniteClient") -> None:
        """Initialize the Swagger middleware.

        Args:
            app: The next ASGI app in the middleware chain
            handle: FunctionService instance for accessing the OpenAPI schema
            client: CogniteClient instance for making API calls
        """
        self.app = app
        self.handle = handle
        self.client = client

    async def __call__(self, scope: ASGIHttpScope, receive: ASGIReceive, send: ASGISend) -> None:
        """Handle ASGI requests, intercepting documentation endpoints.

        Args:
            scope: ASGI connection scope with request metadata
            receive: ASGI receive callable for reading request body
            send: ASGI send callable for writing response
        """
        if scope["type"] == "http":
            path = scope["path"]

            # Intercept documentation endpoints
            if path == "/docs":
                await _serve_swagger_ui(send)
                return
            elif path == "/openapi.json":
                await _serve_openapi_json(send, self.handle, self.client)
                return

        # Pass through to next app in the chain
        await self.app(scope, receive, send)
