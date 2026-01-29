"""OpenAPI schema generation for Function Apps.

This module provides the SchemaGenerator class responsible for generating
OpenAPI 3.1 compliant schemas from function metadata. It handles:

- Converting Python types to OpenAPI type specifications
- Generating comprehensive API documentation schemas
- Processing path parameters, query parameters, and request bodies
- Creating response schemas with proper error handling definitions

OpenAPI 3.1 is fully compatible with JSON Schema Draft 2020-12, which means
Pydantic-generated schemas work almost natively with minimal cleanup!

The generated schemas are used for documentation and validation purposes
in the Cognite Functions platform.
"""

import copy
import inspect
import re
from collections.abc import Mapping, Sequence
from typing import Any, Literal, cast, get_args, get_origin

from pydantic import BaseModel, ConfigDict, Field

from .dependency_registry import DependencyRegistry
from .models import (
    CogniteFunctionError,
    CogniteFunctionResponse,
    HTTPMethod,
    Response,
)
from .routing import RouteInfo


# Client metadata models for type-safe introspection and code generation
class ParameterMetadata(BaseModel):
    """Metadata for a function parameter in client methods.

    Used for introspection and client generation to describe function parameters.
    """

    name: str
    """Parameter name"""
    type: str = "Any"
    """Type annotation as string (e.g., 'str', 'Item', 'list[Item]')"""
    required: bool = True
    """Whether the parameter is required"""
    default: str | None = None
    """Default value as string representation (e.g., '"default"', 'None')"""
    in_: Literal["path", "query", "body"] = Field(alias="in", default="query")
    """Parameter location: path, query, or body"""


class MethodMetadata(BaseModel):
    """Metadata for a client method.

    Complete information about a function endpoint for client generation.
    """

    name: str
    """Method/function name"""
    path: str
    """HTTP path (e.g., '/items/{item_id}')"""
    http_method: str
    """HTTP method (GET, POST, etc.)"""
    parameters: Sequence[ParameterMetadata] = Field(default_factory=lambda: [])
    """List of parameter metadata"""
    description: str = ""
    """Method description/docstring"""
    return_type: str = "Any"
    """Return type annotation as string"""
    path_params: Sequence[str] = Field(default_factory=lambda: [])
    """List of path parameter names"""


class ModelMetadata(BaseModel):
    """Metadata for a Pydantic model used in client methods.

    Contains source code for model definitions.
    """

    name: str
    """Model class name"""
    source: str
    """Complete source code of the model"""


class ClientMethodsMetadata(BaseModel):
    """Complete metadata for client generation and dynamic calling.

    Returned by introspection endpoints to enable client generation.
    """

    methods: Sequence[MethodMetadata]
    """All available methods"""
    models: Sequence[ModelMetadata] = Field(default_factory=lambda: [])
    """All Pydantic models used in methods"""
    imports: Sequence[str] = Field(default_factory=lambda: [])
    """Required import statements"""


# OpenAPI schema models for type-safe schema manipulation
class OpenAPIRef(BaseModel):
    """OpenAPI schema reference.

    Represents a $ref reference to a component schema.
    """

    model_config = ConfigDict(extra="forbid")

    ref: str = Field(alias="$ref", serialization_alias="$ref")
    """Reference path to component schema (e.g., '#/components/schemas/Item')"""


class OpenAPIProperty(BaseModel):
    """OpenAPI schema property definition.

    Represents a single property in an OpenAPI schema, supporting nested structures.
    """

    model_config = ConfigDict(extra="allow")  # Allow additional OpenAPI fields

    type: str | None = Field(default=None, exclude_if=lambda x: x is None)
    """Property type (string, integer, object, array, etc.)"""
    properties: dict[str, "OpenAPIProperty"] | None = Field(default=None, exclude_if=lambda x: not x)
    """Nested properties for object types"""
    items: "OpenAPIProperty | OpenAPIRef | None" = Field(default=None, exclude_if=lambda x: x is None)
    """Item schema for array types"""
    description: str | None = Field(default=None, exclude_if=lambda x: x is None)
    """Property description"""
    default: Any | None = Field(default=None, exclude_if=lambda x: x is None)
    """Default value"""
    required: list[str] = Field(default_factory=list, exclude_if=lambda x: not x)
    """Required fields (for object types)"""
    ref: str | None = Field(default=None, alias="$ref", serialization_alias="$ref", exclude_if=lambda x: x is None)
    """Reference to component schema (alternative to type/properties)"""


class OpenAPISchema(BaseModel):
    """OpenAPI component schema definition.

    Represents a complete schema in the components/schemas section.
    """

    model_config = ConfigDict(extra="allow")  # Allow additional OpenAPI fields

    type: str | None = Field(default=None, exclude_if=lambda x: x is None)
    """Schema type (object, array, string, etc.)"""
    properties: dict[str, OpenAPIProperty] = Field(default_factory=dict, exclude_if=lambda x: not x)
    """Schema properties"""
    required: list[str] = Field(default_factory=list, exclude_if=lambda x: not x)
    """Required property names"""
    description: str | None = Field(default=None, exclude_if=lambda x: x is None)
    """Schema description"""
    items: OpenAPIProperty | OpenAPIRef | None = Field(default=None, exclude_if=lambda x: x is None)
    """Item schema for array types (OpenAPIProperty or OpenAPIRef for $ref)"""


class OpenAPIInfo(BaseModel):
    """OpenAPI info object.

    Contains metadata about the API.
    """

    model_config = ConfigDict(extra="allow")

    title: str
    """API title"""
    version: str
    """API version"""
    description: str | None = None
    """API description"""


class OpenAPIServer(BaseModel):
    """OpenAPI server object.

    Represents a server hosting the API.
    """

    model_config = ConfigDict(extra="allow")

    url: str
    """Server URL"""
    description: str | None = None
    """Server description"""


class OpenAPIMediaType(BaseModel):
    """OpenAPI media type object.

    Defines the structure of content for a specific media type.
    """

    model_config = ConfigDict(extra="allow")

    schema_: OpenAPISchema | OpenAPIRef = Field(alias="schema")
    """Schema for this media type"""


class OpenAPIResponse(BaseModel):
    """OpenAPI response object.

    Describes a single response from an API operation.
    """

    model_config = ConfigDict(extra="allow")

    description: str
    """Response description"""
    content: dict[str, OpenAPIMediaType] | None = None
    """Response content by media type"""


class OpenAPIParameter(BaseModel):
    """OpenAPI parameter object.

    Describes a single operation parameter.
    """

    model_config = ConfigDict(extra="allow")

    name: str
    """Parameter name"""
    in_: Literal["query", "path", "header", "cookie"] = Field(alias="in")
    """Parameter location"""
    required: bool = False
    """Whether parameter is required"""
    schema_: OpenAPIProperty | None = Field(default=None, alias="schema")
    """Parameter schema"""
    description: str | None = None
    """Parameter description"""


class OpenAPIRequestBody(BaseModel):
    """OpenAPI request body object.

    Describes a single request body.
    """

    model_config = ConfigDict(extra="allow")

    required: bool = False
    """Whether request body is required"""
    content: dict[str, OpenAPIMediaType]
    """Request body content by media type"""


class OpenAPIOperation(BaseModel):
    """OpenAPI operation object.

    Describes a single API operation on a path.
    """

    model_config = ConfigDict(extra="allow", use_attribute_docstrings=True)

    summary: str | None = None
    """Short summary of the operation"""
    description: str | None = None
    """Detailed description of the operation"""
    parameters: list[OpenAPIParameter] = Field(default_factory=lambda: [])
    """Operation parameters"""
    request_body: OpenAPIRequestBody | None = Field(default=None, alias="requestBody", exclude_if=lambda x: x is None)
    """Operation request body"""
    responses: dict[str, OpenAPIResponse]
    """Operation responses by status code"""


class OpenAPIPathItem(BaseModel):
    """OpenAPI path item object.

    Describes the operations available on a single path.
    """

    model_config = ConfigDict(extra="allow", use_attribute_docstrings=True)

    get: OpenAPIOperation | None = Field(default=None, exclude_if=lambda x: x is None)
    """GET operation"""
    post: OpenAPIOperation | None = Field(default=None, exclude_if=lambda x: x is None)
    """POST operation"""
    put: OpenAPIOperation | None = Field(default=None, exclude_if=lambda x: x is None)
    """PUT operation"""
    delete: OpenAPIOperation | None = Field(default=None, exclude_if=lambda x: x is None)
    """DELETE operation"""
    patch: OpenAPIOperation | None = Field(default=None, exclude_if=lambda x: x is None)
    """PATCH operation"""


class OpenAPIComponents(BaseModel):
    """OpenAPI components object.

    Holds reusable objects for different aspects of the OAS.
    """

    model_config = {"extra": "allow"}

    schemas: dict[str, OpenAPISchema] = Field(default_factory=dict)
    """Reusable schemas"""


class OpenAPIDocument(BaseModel):
    """OpenAPI 3.1.0 document.

    Represents the complete OpenAPI specification for an API.
    """

    model_config = {"extra": "allow"}

    openapi: str
    """OpenAPI specification version"""
    info: OpenAPIInfo
    """API metadata"""
    servers: Sequence[OpenAPIServer] = Field(default_factory=lambda: [])
    """API servers"""
    paths: dict[str, OpenAPIPathItem]
    """API paths and operations"""
    components: OpenAPIComponents | None = None
    """Reusable components"""


class SchemaGenerator:
    """Handles OpenAPI 3.1 schema generation for Cognite Functions."""

    @staticmethod
    def _get_response_description(status_code: int) -> str:
        """Get appropriate description for HTTP status code.

        Args:
            status_code: HTTP status code

        Returns:
            Human-readable description for the status code
        """
        return {
            200: "Successful Response",
            201: "Created",
            202: "Accepted",
            204: "No Content",
        }.get(status_code, "Successful Response")

    @staticmethod
    def _clean_pydantic_schema_for_openapi(pydantic_schema: dict[str, Any]) -> dict[str, Any]:
        """Clean Pydantic-generated JSON schema to be OpenAPI 3.1 compliant.

        OpenAPI 3.1 is fully compatible with JSON Schema Draft 2020-12, but we need to
        ensure $ref paths work correctly within component schemas. This method inlines
        simple $defs to avoid reference resolution issues.

        Args:
            pydantic_schema: Raw schema from Pydantic's model_json_schema()

        Returns:
            OpenAPI 3.1 compliant schema with inlined definitions
        """
        cleaned_schema = copy.deepcopy(pydantic_schema)

        # Remove title if redundant in component schema context
        cleaned_schema.pop("title", None)

        # Inline simple $defs to avoid reference resolution issues
        defs = cleaned_schema.pop("$defs", {})
        if defs:
            SchemaGenerator._inline_simple_refs(cleaned_schema, defs)

        return cleaned_schema

    @staticmethod
    def _inline_simple_refs(schema: Any, defs: dict[str, Any], visited: set[str] | None = None) -> None:
        """Recursively inline simple $ref references with their definitions.

        This method safely handles nested references and circular dependencies by:
        1. Tracking visited definitions to prevent infinite recursion
        2. Deep copying definitions before inlining to avoid mutation issues
        3. Recursively processing inlined content for nested references
        """
        if visited is None:
            visited = set()

        if isinstance(schema, dict):
            schema = cast(dict[str, Any], schema)
            ref = schema.get("$ref")
            if ref:
                # Handle case where ref might be a dict (from OpenAPIRef serialization)
                if isinstance(ref, dict):
                    ref_dict = cast(dict[str, Any], ref)
                    ref = ref_dict.get("$ref") or ref_dict.get("ref")
                # Ensure ref is a string before processing
                if isinstance(ref, str):
                    # Check for BaseModel references first
                    if SchemaGenerator._is_basemodel_ref(ref):
                        # Handle BaseModel references - replace with generic object
                        schema.clear()
                        schema.update({"type": "object", "description": "Base model object"})
                        return
                    # Use regex patterns to extract definition names from different $ref formats
                    def_name = SchemaGenerator._extract_ref_name(ref)

                    if def_name and def_name in defs:
                        # Check for circular reference
                        if def_name in visited:
                            # Replace circular reference with generic object to break the cycle
                            schema.clear()
                            schema.update({"type": "object", "description": f"Circular reference to {def_name}"})
                            return

                        # Add to visited set and make a deep copy of the definition
                        visited.add(def_name)
                        definition = copy.deepcopy(defs[def_name])

                        # Recursively process the definition to handle nested references
                        SchemaGenerator._inline_simple_refs(definition, defs, visited)

                        # Replace the $ref with the processed definition
                        schema.clear()
                        schema.update(definition)

                        # Remove from visited set after processing
                        visited.discard(def_name)
            else:
                # Recursively process nested objects
                for value in schema.values():
                    SchemaGenerator._inline_simple_refs(value, defs, visited)
        elif isinstance(schema, list):
            schema = cast(list[Any], schema)
            for item in schema:
                SchemaGenerator._inline_simple_refs(item, defs, visited)

    @staticmethod
    def _extract_ref_name(ref: str) -> str | None:
        """Extract definition name from $ref string using regex patterns.

        Supports both JSON Schema ($defs) and OpenAPI (components/schemas) formats.

        Examples:
            "#/$defs/MyModel" -> "MyModel"
            "#/components/schemas/MyModel" -> "MyModel"
            "invalid/ref" -> None
        """
        # Pattern for JSON Schema $defs format: #/$defs/ModelName
        defs_pattern = r"^#/\$defs/(.+)$"

        # Pattern for OpenAPI components format: #/components/schemas/ModelName
        components_pattern = r"^#/components/schemas/(.+)$"

        for pattern in [defs_pattern, components_pattern]:
            match = re.match(pattern, ref)
            if match:
                return match.group(1)

        return None

    @staticmethod
    def _is_basemodel_ref(ref: str) -> bool:
        """Check if $ref points to BaseModel using regex pattern."""
        basemodel_pattern = r"^#/(?:\$defs|components/schemas)/BaseModel$"
        return bool(re.match(basemodel_pattern, ref))

    @staticmethod
    def _handle_list_type_schema(return_type: type[Any], component_schemas: dict[str, OpenAPISchema]) -> OpenAPISchema:
        """Generate OpenAPI schema for list types."""
        args = get_args(return_type)
        if not args:
            return OpenAPISchema(type="array", items=OpenAPIProperty(type="object"))

        item_type = args[0]

        # Handle Pydantic models
        if SchemaGenerator._is_pydantic_model(item_type):
            model_name = item_type.__name__
            if model_name not in component_schemas:
                model_schema = item_type.model_json_schema(by_alias=True, ref_template="#/components/schemas/{model}")
                cleaned = SchemaGenerator._clean_pydantic_schema_for_openapi(model_schema)
                component_schemas[model_name] = OpenAPISchema.model_validate(cleaned)
            # Return reference to the component schema
            return OpenAPISchema(
                type="array",
                items=OpenAPIRef.model_validate({"$ref": f"#/components/schemas/{model_name}"}),
            )

        # Handle basic types
        return OpenAPISchema(
            type="array", items=OpenAPIProperty(type=SchemaGenerator._python_type_to_openapi(item_type))
        )

    @staticmethod
    def _python_type_to_openapi(python_type: type[Any]) -> str:
        """Convert Python type to OpenAPI type string."""
        match python_type:
            case x if x is int:
                return "integer"
            case x if x is float:
                return "number"
            case x if x is bool:
                return "boolean"
            case x if x is str:
                return "string"
            case x if x is dict:
                return "object"
            case x if x is list:
                return "array"
            case _ if get_origin(python_type) is list:
                return "array"
            case _ if get_origin(python_type) is dict:
                return "object"
            case _:
                return "string"  # Default fallback

    @staticmethod
    def _unwrap_response_type(return_type: type[Any]) -> type[Any]:
        """Extract inner type T from Response[T] if present.

        Args:
            return_type: The return type annotation (might be Response[T])

        Returns:
            The inner type T if return_type is Response[T], otherwise return_type unchanged
        """
        origin = get_origin(return_type)
        if origin is Response:
            args = get_args(return_type)
            if args:
                return args[0]
        return return_type

    @staticmethod
    def _generate_response_schema(
        route_info: RouteInfo, component_schemas: dict[str, OpenAPISchema]
    ) -> OpenAPISchema | OpenAPIRef:
        """Generate response schema from function return type hint.

        Automatically unwraps Response[T] to extract the actual data type T.
        """
        return_type = route_info.type_hints.get("return")

        if return_type is None:
            # No return type hint, use generic object
            return OpenAPISchema(type="object")

        # Unwrap Response[T] to get the actual data type
        return_type = SchemaGenerator._unwrap_response_type(return_type)

        # Check if it's a Pydantic model
        if SchemaGenerator._is_pydantic_model(return_type):
            # Generate schema for Pydantic model and add to components
            model_name = return_type.__name__
            if model_name not in component_schemas:
                model_schema = return_type.model_json_schema(by_alias=True, ref_template="#/components/schemas/{model}")
                cleaned = SchemaGenerator._clean_pydantic_schema_for_openapi(model_schema)
                component_schemas[model_name] = OpenAPISchema.model_validate(cleaned)

            # Return reference to the component schema
            return OpenAPIRef.model_validate({"$ref": f"#/components/schemas/{model_name}"})

        # Handle basic Python types
        if return_type in (int, float, bool, str):
            return OpenAPISchema(type=SchemaGenerator._python_type_to_openapi(return_type))

        # Handle lists
        if get_origin(return_type) is list:
            return SchemaGenerator._handle_list_type_schema(return_type, component_schemas)

        # Handle dictionaries
        if get_origin(return_type) is dict:
            return OpenAPISchema(type="object")

        # Default fallback
        return OpenAPISchema(type="object")

    @staticmethod
    def _generate_request_body_schema(
        body_params: list[tuple[str, type[Any]]], component_schemas: dict[str, OpenAPISchema]
    ) -> OpenAPISchema | OpenAPIRef | None:
        """Generate request body schema from any parameter types.

        Handles primitives, lists, Pydantic models, etc.

        Args:
            body_params: List of (param_name, param_type) tuples
            component_schemas: Dictionary to accumulate component schemas

        Returns:
            OpenAPI request body schema or None if no params provided
        """
        if not body_params:
            return None

        def _get_schema_for_type(param_type: type[Any]) -> OpenAPISchema | OpenAPIRef:
            """Generate an OpenAPI schema for a given parameter type."""
            # Check if it's a sequence type
            origin = get_origin(param_type)
            if (
                origin
                and inspect.isclass(origin)
                and issubclass(origin, Sequence)
                and not issubclass(origin, (str, bytes))
            ):
                return SchemaGenerator._handle_list_type_schema(param_type, component_schemas)

            # Check if it's a Pydantic model
            if SchemaGenerator._is_pydantic_model(param_type):
                model_name = param_type.__name__
                if model_name not in component_schemas:
                    model_schema = param_type.model_json_schema(
                        by_alias=True, ref_template="#/components/schemas/{model}"
                    )
                    cleaned = SchemaGenerator._clean_pydantic_schema_for_openapi(model_schema)
                    component_schemas[model_name] = OpenAPISchema.model_validate(cleaned)
                # Return reference to the component schema
                return OpenAPIRef.model_validate({"$ref": f"#/components/schemas/{model_name}"})

            # Primitive type
            return OpenAPISchema(type=SchemaGenerator._python_type_to_openapi(param_type))

        if len(body_params) == 1:
            # Single parameter - unwrap it and use type directly
            _, param_type = body_params[0]
            return _get_schema_for_type(param_type)

        # Multiple parameters - create object with each as a property
        properties: dict[str, OpenAPIProperty] = {}
        required: list[str] = []

        for param_name, param_type in body_params:
            # Convert OpenAPISchema or OpenAPIRef to OpenAPIProperty for properties dict
            schema = _get_schema_for_type(param_type)
            if isinstance(schema, OpenAPIRef):
                # For $ref, create OpenAPIProperty with the ref field
                properties[param_name] = OpenAPIProperty.model_validate({"$ref": schema.ref})
            else:
                # For OpenAPISchema, convert to OpenAPIProperty
                properties[param_name] = OpenAPIProperty.model_validate(schema.model_dump(exclude_unset=True))
            required.append(param_name)

        return OpenAPISchema(type="object", properties=properties, required=required)

    @staticmethod
    def _add_path_parameters(
        operation: OpenAPIOperation, route_info: RouteInfo, dependency_param_names: frozenset[str]
    ) -> None:
        """Add path parameters to the OpenAPI operation.

        Args:
            operation: OpenAPI operation object to add parameters to
            route_info: Route information containing parameters
            dependency_param_names: Names of dependency parameters to exclude from schema
        """
        for param_name in route_info.path_params:
            # Skip dependency injection parameters
            if param_name in dependency_param_names:
                continue
            if param_name in route_info.parameters:
                param_type = route_info.type_hints.get(param_name, str)
                param = OpenAPIParameter.model_construct(
                    name=param_name,
                    in_="path",
                    required=True,
                    description=f"Path parameter {param_name}",
                    schema_=OpenAPIProperty(type=SchemaGenerator._python_type_to_openapi(param_type)),
                )
                operation.parameters.append(param)

    @staticmethod
    def _is_pydantic_model(param_type: type[Any]) -> bool:
        """Check if type is a Pydantic model.

        Args:
            param_type: The type to check

        Returns:
            True if type is a BaseModel subclass
        """
        return inspect.isclass(param_type) and issubclass(param_type, BaseModel)

    @staticmethod
    def _is_sequence_of_pydantic(param_type: type[Any]) -> bool:
        """Check if type is a sequence of Pydantic models.

        Supports list, tuple, Sequence, and other sequence types from collections.abc.
        Excludes str and bytes which are technically sequences but not collections.

        Args:
            param_type: The type to check

        Returns:
            True if type is a sequence containing BaseModel instances
        """
        origin = get_origin(param_type)
        if not origin:
            return False

        # Check if origin is a sequence type (but not str or bytes)
        if not (inspect.isclass(origin) and issubclass(origin, Sequence) and not issubclass(origin, (str, bytes))):
            return False

        args = get_args(param_type)
        if not args:
            return False

        return SchemaGenerator._is_pydantic_model(args[0])

    @staticmethod
    def _collect_parameters_by_location(
        operation: OpenAPIOperation,
        route_info: RouteInfo,
        dependency_param_names: frozenset[str],
        method: HTTPMethod,
    ) -> list[tuple[str, type[Any]]]:
        """Collect parameters and add them to appropriate locations (query or body).

        For GET/DELETE: Only primitive params go to query parameters (Pydantic models are skipped)
        For POST/PUT/PATCH: All non-path params go to request body

        Args:
            operation: OpenAPI operation object to add parameters to
            route_info: Route information containing parameters
            dependency_param_names: Names of dependency parameters to exclude from schema
            method: HTTP method to determine parameter location

        Returns:
            List of (param_name, param_type) tuples for parameters to include in request body
        """
        body_params: list[tuple[str, type[Any]]] = []

        for param_name, param_info in route_info.parameters.items():
            # Skip dependency injection parameters
            if param_name in dependency_param_names:
                continue
            if param_name not in route_info.path_params:
                param_type = route_info.type_hints.get(param_name, str)

                # For POST/PUT/PATCH: all params go in request body
                if method in [HTTPMethod.POST, HTTPMethod.PUT, HTTPMethod.PATCH]:
                    body_params.append((param_name, param_type))
                # For GET/DELETE: only primitives go in query parameters
                # (Pydantic models and sequences of Pydantic models can't be serialized as query strings)
                else:
                    # Skip Pydantic models and sequences of Pydantic models
                    if SchemaGenerator._is_pydantic_model(param_type) or SchemaGenerator._is_sequence_of_pydantic(
                        param_type
                    ):
                        continue

                    param = OpenAPIParameter.model_construct(
                        name=param_name,
                        in_="query",
                        required=param_info.default == inspect.Parameter.empty,
                        description=f"Query parameter {param_name}",
                        schema_=OpenAPIProperty(type=SchemaGenerator._python_type_to_openapi(param_type)),
                    )
                    operation.parameters.append(param)
        return body_params

    @staticmethod
    def _add_request_body_if_needed(
        operation: OpenAPIOperation,
        method: HTTPMethod,
        body_params: list[tuple[str, type[Any]]],
        component_schemas: dict[str, OpenAPISchema],
    ) -> None:
        """Add request body to operation if parameters exist for it.

        Note: body_params is already filtered by method in _collect_parameters_by_location(),
        so we don't need to check the method here.
        """
        if body_params:
            request_body_schema = SchemaGenerator._generate_request_body_schema(
                body_params,
                component_schemas,
            )
            if request_body_schema:
                operation.request_body = OpenAPIRequestBody(
                    required=True,
                    content={"application/json": OpenAPIMediaType(schema=request_body_schema)},
                )

    @staticmethod
    def _generate_component_schemas(component_schemas: dict[str, OpenAPISchema]) -> dict[str, OpenAPISchema]:
        """Generate component schemas section for OpenAPI."""
        error_schema = CogniteFunctionError.model_json_schema(
            by_alias=True,  # Use field aliases if defined
            ref_template="#/components/schemas/{model}",  # OpenAPI-style refs
        )
        response_schema = CogniteFunctionResponse.model_json_schema(
            by_alias=True,  # Use field aliases if defined
            ref_template="#/components/schemas/{model}",  # OpenAPI-style refs
        )

        base_schemas = {
            CogniteFunctionError.__name__: OpenAPISchema.model_validate(
                SchemaGenerator._clean_pydantic_schema_for_openapi(error_schema)
            ),
            CogniteFunctionResponse.__name__: OpenAPISchema.model_validate(
                SchemaGenerator._clean_pydantic_schema_for_openapi(response_schema)
            ),
        }

        # Merge with collected component schemas. We intentionally put the base schemas last to avoid overriding the
        # component schemas, e.g so users cannot redefine the base schemas like CogniteFunctionError and
        # CogniteFunctionResponse.
        return {**component_schemas, **base_schemas}

    @staticmethod
    def _create_operation_object(
        route_info: RouteInfo, response_schema: OpenAPISchema | OpenAPIRef
    ) -> OpenAPIOperation:
        """Create the base operation object for OpenAPI path item.

        Now returns a typed OpenAPIOperation that uses mutable list/dict for construction.
        Uses the route's configured status_code for the success response.
        """
        status_code_str = str(route_info.status_code)
        return OpenAPIOperation(
            summary=route_info.description.split("\n")[0],  # First line as summary
            description=route_info.description,
            parameters=[],
            responses={
                status_code_str: OpenAPIResponse(
                    description=SchemaGenerator._get_response_description(route_info.status_code),
                    content={route_info.content_type: OpenAPIMediaType(schema=response_schema)},
                ),
                "400": OpenAPIResponse(
                    description="Validation Error",
                    content={
                        "application/json": OpenAPIMediaType(
                            schema=OpenAPIRef.model_validate(
                                {"$ref": f"#/components/schemas/{CogniteFunctionError.__name__}"}
                            )
                        )
                    },
                ),
            },
        )

    @staticmethod
    def _add_route_content_type_to_operation(
        operation: OpenAPIOperation,
        route: RouteInfo,
        component_schemas: dict[str, OpenAPISchema],
    ) -> None:
        """Add a route's response content type to an operation.

        Used for content negotiation where multiple routes share the same path/method
        but have different accept headers and potentially different status codes.
        """
        schema = SchemaGenerator._generate_response_schema(route, component_schemas)
        status_code_str = str(route.status_code)

        if status_code_str not in operation.responses:
            operation.responses[status_code_str] = OpenAPIResponse(
                description=SchemaGenerator._get_response_description(route.status_code),
                content={route.content_type: OpenAPIMediaType(schema=schema)},
            )
            return

        response = operation.responses[status_code_str]
        if response.content is None:
            response.content = {}
        response.content[route.content_type] = OpenAPIMediaType(schema=schema)

    @staticmethod
    def generate_openapi_schema(
        title: str,
        version: str,
        routes: dict[str, Mapping[HTTPMethod, Sequence[RouteInfo]]],
        registry: DependencyRegistry | None = None,
    ) -> OpenAPIDocument:
        """Generate comprehensive OpenAPI 3.1 schema for documentation.

        OpenAPI 3.1 brings full JSON Schema compatibility, making this much simpler
        than previous versions that required complex transformations.

        Args:
            title: API title
            version: API version
            routes: Routes to include in the schema (supports multiple routes per path/method for content negotiation)
            registry: Dependency registry to filter out dependency parameters from schema

        Returns:
            OpenAPI 3.1 compliant document
        """
        # Build paths dictionary using typed models directly
        paths_dict: dict[str, dict[str, OpenAPIOperation]] = {}

        # Track schemas to add to components section
        component_schemas: dict[str, OpenAPISchema] = {}

        for path, methods in routes.items():
            paths_dict[path] = {}
            for method, route_infos in methods.items():
                # For multiple routes (content negotiation), merge into single operation
                # with multiple response content types. Use first route as primary for parameters.
                if not route_infos:
                    continue

                route_info = route_infos[0]  # Use first for parameters

                # Get dependency parameter names for filtering
                dependency_param_names = (
                    registry.get_dependency_param_names(route_info.signature) if registry else frozenset[str]()
                )

                # Generate response schema from return type
                response_schema = SchemaGenerator._generate_response_schema(route_info, component_schemas)

                # Create base operation object (typed and mutable during construction)
                operation = SchemaGenerator._create_operation_object(route_info, response_schema)

                # Add additional routes' content types for content negotiation
                for additional_route in route_infos[1:]:
                    SchemaGenerator._add_route_content_type_to_operation(operation, additional_route, component_schemas)

                # Add path parameters (excluding dependencies)
                SchemaGenerator._add_path_parameters(operation, route_info, dependency_param_names)

                # Collect parameters by location: query params for GET, body params for POST/PUT/PATCH
                body_params = SchemaGenerator._collect_parameters_by_location(
                    operation, route_info, dependency_param_names, method
                )

                # Add request body for methods that support it
                SchemaGenerator._add_request_body_if_needed(operation, method, body_params, component_schemas)

                # Add operation to path
                paths_dict[path][method.lower()] = operation

        # Add component schemas - now with full JSON Schema support in OpenAPI 3.1!
        all_schemas = SchemaGenerator._generate_component_schemas(component_schemas)

        # Build paths with typed models
        paths: dict[str, OpenAPIPathItem] = {
            path: OpenAPIPathItem(**operations) for path, operations in paths_dict.items()
        }

        return OpenAPIDocument(
            openapi="3.1.0",
            info=OpenAPIInfo(
                title=title,
                version=version,
                description=f"Auto-generated API documentation for {title}",
            ),
            servers=[OpenAPIServer(url="/", description="Cognite Function")],
            paths=paths,
            components=OpenAPIComponents(schemas=all_schemas),
        )
