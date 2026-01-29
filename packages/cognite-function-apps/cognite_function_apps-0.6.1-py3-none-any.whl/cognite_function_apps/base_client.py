"""Base client infrastructure for Function Apps.

This module provides the BaseFunctionClient class, which contains all shared
infrastructure for making HTTP calls to devservers and deployed Cognite Functions.
Both the dynamic FunctionClient and generated typed clients inherit from this base class.

The base class handles:
- Initialization for both devserver and deployed function modes
- Lazy function retrieval for deployed functions
- HTTP calls via httpx (devserver mode)
- SDK calls via CogniteClient (deployed mode)
- Response unwrapping and error handling
- Deserialization of responses into Pydantic models
"""

import inspect
import re
import sys
from typing import Any, cast, overload
from urllib.parse import urlencode

from cognite.client import CogniteClient
from cognite.client.data_classes import Function
from pydantic import BaseModel

from .models import CogniteFunctionError, CogniteFunctionResponse, HTTPMethod

# Optional OpenTelemetry support for trace propagation
try:
    from opentelemetry.propagate import inject as _otel_inject
except ImportError:

    def _otel_inject(*args: Any, **kwargs: Any) -> None:
        """No-op inject when OpenTelemetry not installed."""
        pass


class BaseFunctionClient:
    """Base class for Cognite Function App clients.

    Provides shared infrastructure for both dynamic and generated clients:
    - HTTP calling via httpx (devserver mode)
    - SDK calling via CogniteClient (deployed mode)
    - Response unwrapping and error handling
    - Model deserialization

    Supports two modes:
    1. Local devserver: Pass base_url (requires httpx)
    2. Deployed function: Pass cognite_client and function_external_id or function_id
    """

    base_url: str
    _cognite_client: CogniteClient | None
    _function_id: int | None
    _function_external_id: str | None
    _function: Function | None
    _is_deployed: bool

    @overload
    def __init__(self, *, base_url: str) -> None: ...

    @overload
    def __init__(self, *, cognite_client: CogniteClient, function_id: int) -> None: ...

    @overload
    def __init__(self, *, cognite_client: CogniteClient, function_external_id: str) -> None: ...

    def __init__(
        self,
        *,
        base_url: str | None = None,
        cognite_client: CogniteClient | None = None,
        function_id: int | None = None,
        function_external_id: str | None = None,
    ) -> None:
        """Initialize the client.

        Args:
            base_url: Base URL for local devserver (e.g., 'http://localhost:8000')
            cognite_client: CogniteClient instance for deployed functions
            function_id: ID of deployed function
            function_external_id: External ID of deployed function

        Raises:
            ValueError: If invalid parameter combination is provided
            ImportError: If required dependencies are not installed

        Example:
            # Local devserver
            client = BaseFunctionClient(base_url="http://localhost:8000")

            # Deployed function
            from cognite.client import CogniteClient
            cognite = CogniteClient(...)
            client = BaseFunctionClient(cognite_client=cognite, function_external_id="my-function")
        """
        if base_url:
            # Devserver mode
            try:
                import httpx  # type: ignore[import-not-found]  # noqa: PLC0415, F401
            except ImportError as e:
                raise ImportError(
                    "The 'httpx' package is required for devserver mode. Please install it using: pip install httpx"
                ) from e
            self.base_url = base_url.rstrip("/")
            self._is_deployed = False
        elif cognite_client and (function_external_id or function_id):
            # Deployed function mode
            self._is_deployed = True
            self.base_url = "__deployed__"  # Placeholder
        else:
            raise ValueError(
                "Either base_url or (cognite_client with function_external_id or function_id) must be provided"
            )
        self._cognite_client = cognite_client
        self._function_id = function_id
        self._function_external_id = function_external_id
        self._function = None  # Retrieved lazily

    def _ensure_function_retrieved(self) -> None:
        """Lazily retrieve the deployed function if not already retrieved.

        Raises:
            RuntimeError: If function retrieval fails
        """
        if not self._is_deployed or self._function is not None:
            return

        if self._cognite_client is None:
            raise RuntimeError("CogniteClient not available")

        try:
            if self._function_external_id:
                self._function = self._cognite_client.functions.retrieve(external_id=self._function_external_id)
            elif self._function_id:
                self._function = self._cognite_client.functions.retrieve(id=self._function_id)
            else:
                raise ValueError("Neither function_id nor function_external_id provided")

            if self._function is None:
                raise RuntimeError("Function not found")
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve function: {e}") from e

    def _call_deployed(
        self,
        path: str,
        method: HTTPMethod,
        body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Call deployed function using Cognite SDK.

        Args:
            path: Path to call (e.g., "/items/123")
            method: HTTP method (GET, POST, PUT, DELETE)
            body: Request body for POST/PUT
            params: Query parameters for GET

        Returns:
            Raw response from function call

        Raises:
            RuntimeError: If function not retrieved or call fails

        Note:
            Trace propagation for deployed functions requires the CDF Functions API
            to forward the traceparent header from the calling function to the target
            function. This is not currently implemented in the SDK's function.call() API.
        """
        self._ensure_function_retrieved()

        if self._function is None:
            raise RuntimeError("Function not retrieved")

        # Build full path with query parameters
        full_path = path
        if params:
            query_string = urlencode({k: v for k, v in params.items() if v is not None})
            full_path = f"{path}?{query_string}"

        # Call using SDK
        # TODO: FUN-688 - Add trace propagation when SDK supports custom headers
        # For now, trace context is lost when calling deployed functions via SDK
        request_data: dict[str, Any] = {
            "path": full_path,
            "method": method,
        }
        if body:
            request_data["body"] = body

        call = self._function.call(data=request_data, wait=True)
        return call.get_response()

    def _call_devserver(
        self,
        path: str,
        method: HTTPMethod,
        body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Call local devserver using httpx.

        Args:
            path: Path to call (e.g., "/items/123")
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            body: Request body for POST/PUT
            params: Query parameters for GET

        Returns:
            Raw response from HTTP call

        Raises:
            ImportError: If httpx is not installed
            httpx.HTTPError: If HTTP request fails
        """
        import httpx  # noqa: PLC0415

        url = f"{self.base_url}{path}"
        headers: dict[str, str] = {}
        _otel_inject(headers)  # Injects traceparent header if active span exists, no-op if no tracing is active.

        if method not in {HTTPMethod.GET, HTTPMethod.POST, HTTPMethod.PUT, HTTPMethod.DELETE, HTTPMethod.PATCH}:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response = httpx.request(
            method=method.value,
            url=url,
            params=params if method == HTTPMethod.GET else None,
            json=body if method in {HTTPMethod.POST, HTTPMethod.PUT, HTTPMethod.PATCH} else None,
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    def _call_method(
        self,
        path: str,
        method: HTTPMethod,
        body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Dispatch method call to appropriate backend and unwrap response.

        Args:
            path: Path to call (e.g., "/items/123")
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            body: Request body for POST/PUT
            params: Query parameters for GET

        Returns:
            Unwrapped response data

        Raises:
            RuntimeError: If response indicates an error
        """
        # Dispatch to appropriate backend
        if self._is_deployed:
            result = self._call_deployed(path, method, body, params)
        else:
            result = self._call_devserver(path, method, body, params)

        # Unwrap Cognite Functions response format
        # Use status_code < 400 to determine success (new wire format)
        status_code: int | None = None
        if isinstance(result, dict):
            result = cast(dict[str, Any], result)
            raw_status = result.get("status_code")
            if isinstance(raw_status, int):
                status_code = raw_status
        if status_code is None or status_code >= 400:
            error = CogniteFunctionError.model_validate(result)
            raise RuntimeError(f"{error.error_type}: {error.message}")

        typed_response = CogniteFunctionResponse.model_validate(result)
        return typed_response.data  # type: ignore[reportReturnType]

    def _deserialize_response(self, data: Any, return_type: str) -> Any:
        """Deserialize response data into Pydantic models if applicable.

        This method looks up model classes in the subclass's module namespace and
        validates responses against them if the return type matches a Pydantic model.

        Args:
            data: Raw response data
            return_type: String representation of the return type

        Returns:
            Deserialized data if a Pydantic model, otherwise raw data
        """
        # Get the module namespace where the actual client class is defined
        # This allows us to find models defined in generated clients
        module_namespace = sys.modules[type(self).__module__].__dict__

        if return_type.startswith("list["):
            # Handle list responses - extract model name
            if match := re.search(r"list\[([A-Z][a-zA-Z0-9_]*)\]", return_type):
                model_name = match.group(1)
                if model_name in module_namespace:
                    model_class = module_namespace[model_name]
                    # Verify it's actually a Pydantic model class
                    if inspect.isclass(model_class) and issubclass(model_class, BaseModel):
                        if isinstance(data, list):
                            return [model_class.model_validate(item) for item in cast(list[Any], data)]
        elif return_type and return_type[0].isupper():
            # Single model response - check if it's a known model
            # Extract base type name (e.g., "Item" from "Item")
            if match := re.search(r"^([A-Z][a-zA-Z0-9_]*)", return_type):
                model_name = match.group(1)
                if model_name in module_namespace:
                    model_class = module_namespace[model_name]
                    # Verify it's actually a Pydantic model class
                    if inspect.isclass(model_class) and issubclass(model_class, BaseModel):
                        return model_class.model_validate(data)

        return data
