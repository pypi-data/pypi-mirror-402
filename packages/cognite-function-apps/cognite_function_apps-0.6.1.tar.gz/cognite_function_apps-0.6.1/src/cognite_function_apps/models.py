"""Cross-cutting types and models for Cognite Functions.

This module contains types, protocols, and models that are shared across
multiple components of the framework. It focuses on cross-cutting concerns
rather than module-specific implementations.

Core Framework Types:
    - JSONLike, DataDict, TypedParam, TypedResponse: Universal data types
    - Handler: Protocol definition for traditional function handlers
    - RouteHandler: Type alias for flexible route handler functions
    - HTTPMethod: Shared enumeration for HTTP operations
    - Response[T]: Generic wrapper for dynamic status codes and headers

Cognite Integration:
    - FunctionCallInfo: Cognite-specific metadata for function calls
    - CogniteFunctionError, CogniteFunctionResponse: Standardized response formats
    - RequestData: Parsed request data structure
    - RequestHeaders: Type for accessing incoming HTTP headers

Design Philosophy:
    This module serves as the "shared vocabulary" of the framework, containing
    types that need to be consistent across routing, application logic, and
    response handling. Module-specific types (like RouteInfo) belong in their
    respective modules to maintain clear boundaries and reduce coupling.
"""

from collections.abc import Awaitable, Callable, Mapping, MutableMapping, Sequence
from enum import Enum
from typing import TYPE_CHECKING, Any, Generic, Literal, Protocol, TypeAlias, TypedDict, TypeVar
from urllib.parse import parse_qs, urlparse

from cognite.client import CogniteClient
from pydantic import BaseModel, Field
from typing_extensions import NotRequired, TypeAliasType

# Type variable for Response[T] generic
_T = TypeVar("_T")


# Exception hierarchy for framework-specific errors
class FunctionAppError(Exception):
    """Base exception for all Function Apps framework errors.

    This base class allows callers to catch all framework-specific errors
    while still being able to distinguish between different error types
    using more specific subclasses.
    """

    pass


class ConfigurationError(FunctionAppError):
    """Exception raised when there is a configuration error in the framework.

    This includes errors such as:
    - Invalid dependency registrations
    - Path parameter conflicts with dependencies
    - Invalid route configurations
    - Other setup/configuration issues that should be caught during development

    These errors indicate problems with how the framework is configured,
    not runtime errors from user requests.
    """

    pass


class NotAcceptableError(FunctionAppError):
    """Exception raised when Accept header doesn't match any available content type.

    This is a runtime error (HTTP 406 Not Acceptable) that occurs when:
    - The requested path and method exist
    - But no route matches the client's Accept header
    - And no fallback route (accept=None) is available

    Attributes:
        path: The requested path
        method: The HTTP method
        accept: The Accept header value from the request
        available_types: List of content types available for this path/method
    """

    def __init__(self, path: str, method: str, accept: str, available_types: Sequence[str]):
        """Initialize NotAcceptableError with request details.

        Args:
            path: The requested path
            method: The HTTP method
            accept: The Accept header value from the request
            available_types: List of content types available for this path/method
        """
        self.path = path
        self.method = method
        self.accept = accept
        self.available_types = available_types
        super().__init__(
            f"Accept header '{accept}' does not match any available content types "
            f"for {method} {path}: {', '.join(available_types)}"
        )


class Response(BaseModel, Generic[_T]):
    """Generic response wrapper for dynamic status codes and headers.

    The type parameter T preserves return type information for schema generation.
    Schema generators should extract T from Response[T] for OpenAPI documentation.

    Use this when you need to dynamically control status codes or headers at
    runtime. For static configurations, use decorator parameters instead.

    Example:
        ```python
        @app.post("/jobs")
        def create_job(client: CogniteClient, job: Job) -> Response[Job]:
            if async_mode:
                return Response(data=job, status_code=202, cache_control="no-store")
            return Response(data=job, status_code=201)
        ```

    Attributes:
        data: The actual response data (typed for schema generation)
        status_code: HTTP status code (overrides decorator default)
        cache_control: Cache-Control header value (overrides decorator default)
        extra_headers: Additional HTTP headers (merged with decorator defaults)
    """

    data: _T
    """The actual response data (typed for schema generation)"""

    status_code: int = 200
    """HTTP status code (overrides decorator default)"""

    cache_control: str | None = None
    """Cache-Control header value (overrides decorator default)"""

    extra_headers: dict[str, str] | None = None
    """Additional HTTP headers (merged with decorator defaults)"""


class FunctionCallInfo(TypedDict):
    """Function call information."""

    function_id: str
    call_id: str

    # If the call is scheduled
    schedule_id: str | None
    scheduled_time: str | None


if TYPE_CHECKING:
    # Recursive types for type checking (pyright). These work with pyright, but not for Pydantic (RecursionError)
    Json: TypeAlias = Mapping[str, "Json"] | Sequence["Json"] | str | int | float | bool | None
    TypedResponse: TypeAlias = (
        BaseModel | Sequence["TypedResponse"] | Mapping[str, "TypedResponse"] | str | int | float | bool | None
    )

else:
    # Recursive types for runtime (Pydantic)
    # These work for Pydantic, but not with pyright. Note the use of `Mapping` and
    # `Sequence` to make them covariant. For more information, see
    # https://docs.pydantic.dev/2.11/concepts/types/#named-recursive-types
    Json = TypeAliasType(
        "Json",
        "Mapping[str, Json] | Sequence[Json] | str | int | float | bool | None",
    )
    TypedResponse = TypeAliasType(
        "TypedResponse",
        "BaseModel | Sequence[TypedResponse] | Mapping[str, TypedResponse] | str | int | float | bool | None",
    )


# Type aliases for better readability
DataDict: TypeAlias = Mapping[str, Json]
SecretsMapping: TypeAlias = Mapping[str, str]
RequestHeaders: TypeAlias = Mapping[str, str]  # Header names are lowercase (HTTP/2 convention)


class HTTPMethod(str, Enum):
    """HTTP methods."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    OPTIONS = "OPTIONS"

    def __str__(self) -> str:
        """Return the string value of the HTTP method."""
        return self.value


class Handle(Protocol):
    """Handler function type.

    This is the traditional function handler type used in Cognite Functions.
    """

    def __call__(
        self,
        *,
        client: CogniteClient,
        data: DataDict,
        secrets: SecretsMapping | None = None,
        function_call_info: FunctionCallInfo | None = None,
    ) -> Json:
        """Call the handler."""
        ...


class CogniteFunctionError(BaseModel):
    """Structured error response.

    This is the wire format DTO for Cognite Functions (the platform).

    Use `status_code < 400` to determine if the response is an error.
    """

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status_code": 400,
                    "error_type": "ValidationError",
                    "message": "Invalid input data",
                    "details": {"field": "value"},
                    "headers": {"content-type": "application/json"},
                }
            ]
        }
    }

    status_code: int = 400
    """HTTP status code for the error"""
    error_type: str
    """Error type identifier (e.g., ValidationError, NotFound)"""
    message: str
    """Human-readable error message"""
    details: Mapping[str, Any] | None = None
    """Optional additional error details"""
    headers: Mapping[str, str] = Field(default_factory=lambda: {"content-type": "application/json"})
    """Response headers"""


class CogniteFunctionResponse(BaseModel):
    """Wrapper for successful responses.

    This is the wire format DTO for Cognite Functions (the platform).

    Use `status_code < 400` to determine if the response is successful.
    """

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status_code": 200,
                    "data": {"result": "example response"},
                    "headers": {"content-type": "application/json"},
                }
            ]
        }
    }

    status_code: int = 200
    """HTTP status code"""
    data: TypedResponse
    """Response data"""
    headers: Mapping[str, str] = Field(default_factory=lambda: {"content-type": "application/json"})
    """Response headers"""


class RequestData(BaseModel):
    """Parsed request data from a Cognite Function call."""

    path: str = "/"
    """Raw path with query string (e.g., "/items/123?include_tax=true")"""
    method: HTTPMethod = HTTPMethod.POST
    """HTTP method (GET, POST, etc.)"""
    body: Mapping[str, Any] = Field(default_factory=dict)
    """Request body data"""
    headers: Mapping[str, str] = Field(default_factory=dict)
    """HTTP headers (header names should be lowercase per HTTP/2 convention)"""

    # Computed fields that are parsed from path
    clean_path: str = ""
    """Just the path part (e.g., "/items/123")"""
    query: Mapping[str, str | Sequence[str]] = Field(default_factory=dict)
    """Parsed query parameters"""

    def model_post_init(self, __context: Any) -> None:
        """Parse path and query string after Pydantic validation."""
        # Parse the full path to extract clean path and query params
        parsed = urlparse(self.path)

        # Set the clean path (without query string)
        self.clean_path = parsed.path or "/"

        # Parse query parameters
        query_params = parse_qs(parsed.query)
        query: dict[str, str | list[str]] = {}
        for key, value_list in query_params.items():
            if len(value_list) == 1:
                query[key] = value_list[0]
            else:
                query[key] = value_list  # Keep as list if multiple values

        self.query = query


# ASGI-related types for middleware architecture
class ASGITypedFunctionRequestMessage(TypedDict):
    """Typed Function ASGI request message."""

    type: Literal["cognite.function.request"]
    body: RequestData
    """Parsed request data. This is resonable to avoid having to parse
    the request data for every composed app."""


class ASGITypedFunctionResponseMessage(TypedDict):
    """Typed Function ASGI response message."""

    type: Literal["cognite.function.response"]
    body: DataDict


class ASGIScopeAsgi(TypedDict):
    """ASGI scope."""

    version: str


class ASGITypedFunctionScope(TypedDict):
    """ASGI typed function scope.

    The scope should will be passed through by middleware layers. The
    'state' dict should be used for sharing mutable information between
    middleware layers as a reference even if the scope is altered and
    copied by middleware.
    """

    type: Literal["cognite.function"]
    asgi: ASGIScopeAsgi
    client: CogniteClient
    secrets: SecretsMapping | None
    function_call_info: FunctionCallInfo | None
    request: RequestData

    state: MutableMapping[str, Any]
    """State mutable dictionary for sharing information between
    middleware layers."""

    headers: NotRequired[Mapping[str, str]]
    """Optional HTTP headers from incoming request (for trace propagation)."""


ASGIReceiveCallable: TypeAlias = Callable[[], Awaitable[ASGITypedFunctionRequestMessage]]
"""ASGI receive callable type."""

ASGISendCallable: TypeAlias = Callable[[ASGITypedFunctionResponseMessage], Awaitable[None]]
"""ASGI send callable type."""

ASGIApp: TypeAlias = Callable[
    [ASGITypedFunctionScope, ASGIReceiveCallable, ASGISendCallable],
    Awaitable[None],
]
"""ASGI application callable type (scope, receive, send) -> None."""
