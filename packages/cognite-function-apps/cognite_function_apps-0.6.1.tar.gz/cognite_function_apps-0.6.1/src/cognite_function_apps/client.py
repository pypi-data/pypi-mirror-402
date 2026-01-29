"""FunctionClient for generating and consuming typed clients.

This module provides the FunctionClient class, a developer tool for generating
typed Python clients from Cognite Functions. The client connects to either a
local devserver or deployed function to enable interactive exploration and
production-ready client generation.

Key Features:
    - Notebook-first design: Optimized for interactive exploration
    - Dynamic calling: Use methods directly without code generation
    - Two-tier model approach:
        * discover(): Creates simplified models from OpenAPI (fast, for exploration)
        * materialize(): Extracts complete models with validators (production-ready)
    - Runtime model discovery: Get Pydantic models on-demand for validation
    - Progressive enhancement from dynamic to fully typed
    - Self-contained generated clients with no manual imports needed
    - Support for deployed Cognite Functions via CogniteClient

Workflow Tiers:
    Tier 1 (Quick Exploration):
        Use dynamic client with dicts - fast, no validation needed

    Tier 2 (Interactive Validation):
        Use discover() to get runtime models with automatic response parsing

    Tier 3 (Production):
        Use materialize() to generate fully typed client

Example Usage (Local Devserver):
    ```python
    from cognite_function_apps import FunctionClient

    # Create client (no I/O, safe constructor)
    client = FunctionClient(base_url="http://localhost:8000")

    # Tier 1: Quick exploration with dicts
    result = client.get_item(item_id=42)  # Returns dict

    # Tier 2: Discover and use runtime models
    models = client.discover()
    # ✓ Connected to Asset Management API v1.0.0
    # Available methods: get_item, create_item, ...
    # Models: Item, ItemResponse

    # After discover(), responses are automatically parsed to models!
    item = models.Item(name="Widget", price=99.99)  # Validated request
    result = client.create_item(item=item)  # Returns ItemResponse (not dict!)
    print(result.total_price)  # Direct typed access

    # Explore a specific method
    client.describe("create_item")

    # Tier 3: Generate typed client for production
    client.materialize("clients/my_client.py")
    ```

Example Usage (Deployed Function):
    ```python
    from cognite.client import CogniteClient
    from cognite_function_apps import FunctionClient

    # User has CogniteClient for other purposes
    cognite_client = CogniteClient(...)

    # Create FunctionClient - function is retrieved lazily on first use
    client = FunctionClient(
        cognite_client=cognite_client,
        function_external_id="my-function"
    )
    # or with function ID:
    # client = FunctionClient(cognite_client=cognite_client, function_id=5199938255797384)

    # Function is retrieved automatically on first discover() or method call
    models = client.discover()
    result = client.get_item(item_id=42)
    ```

Note:
    This module requires httpx, which is available as an optional dependency:
    `pip install cognite-function-apps[client]`

    For deployed functions, cognite-sdk is required:
    `pip install cognite-sdk`
"""

import re
import warnings
from collections.abc import Mapping
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast, overload

from cognite.client import CogniteClient
from cognite.client.exceptions import CogniteException
from pydantic import BaseModel, ValidationError, create_model

from .base_client import BaseFunctionClient
from .models import (
    CogniteFunctionError,
    CogniteFunctionResponse,
    HTTPMethod,
    Json,
)
from .schema import (
    ClientMethodsMetadata,
    MethodMetadata,
    OpenAPIComponents,
    OpenAPIDocument,
    OpenAPIInfo,
    OpenAPIMediaType,
    OpenAPIOperation,
    OpenAPIParameter,
    OpenAPIPathItem,
    OpenAPIProperty,
    OpenAPIRef,
    OpenAPIRequestBody,
    OpenAPIResponse,
    OpenAPISchema,
    OpenAPIServer,
)


class FunctionClient(BaseFunctionClient):
    """Developer tool for generating typed clients from Cognite Functions.

    Notebook-first design optimized for interactive exploration with three tiers:

    Tier 1 (Quick Exploration):
        Use dynamic client with dicts - no validation, fast iteration

    Tier 2 (Interactive Validation):
        Use discover() to get runtime models with automatic response parsing

    Tier 3 (Production):
        Use materialize() to generate a fully typed client for production code

    Key Features:
        - Safe constructor (no I/O) - never fails on instantiation
        - Lazy connection - connects when you first interact with methods or discover()
        - Runtime model loading - get Pydantic models from OpenAPI schemas
        - Automatic response parsing - after discover(), model responses are typed
        - Discovery helpers - explore methods interactively with describe()
        - Progressive enhancement - easy path from exploration to production
        - Support for both local devserver and deployed Cognite Functions

    The generated clients (Tier 3) are self-contained Python modules that include:
        - All Pydantic model definitions
        - Type-safe methods for each endpoint
        - Proper imports and type hints
        - Full docstrings

    Attributes:
        base_url: The base URL of the function endpoint (for devserver or direct function URLs)
    """

    @overload
    def __init__(
        self,
        *,
        base_url: str | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        *,
        cognite_client: CogniteClient | None = None,
        function_id: int | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        *,
        cognite_client: CogniteClient | None = None,
        function_external_id: str | None = None,
    ) -> None: ...

    def __init__(
        self,
        *,
        base_url: str | None = None,
        cognite_client: CogniteClient | None = None,
        function_id: int | None = None,
        function_external_id: str | None = None,
    ) -> None:
        """Initialize FunctionClient - no I/O, safe constructor.

        Args:
            base_url: Direct URL to devserver (e.g., "http://localhost:8000")
            cognite_client: CogniteClient instance for deployed functions
            function_id: ID of deployed function to retrieve
            function_external_id: External ID of deployed function to retrieve

        Raises:
            ValueError: If invalid parameter combination is provided
            ImportError: If required dependencies are not installed

        Example:
            ```python
            # For local development
            client = FunctionClient(base_url="http://localhost:8000")

            # For deployed functions
            from cognite.client import CogniteClient

            cognite_client = CogniteClient(...)
            client = FunctionClient(
                cognite_client=cognite_client,
                function_external_id="my-function"
            )
            # Function is retrieved lazily on first discover() or method call
            ```
        """
        # Initialize base client infrastructure
        super().__init__(  # type: ignore[call-overload]
            base_url=base_url,
            cognite_client=cognite_client,
            function_id=function_id,
            function_external_id=function_external_id,
        )

        # FunctionClient-specific state management - no I/O in constructor
        self._connected = False
        self._methods_metadata: ClientMethodsMetadata | None = None
        self._methods_by_name: dict[str, MethodMetadata] | None = None  # O(1) lookup cache
        self._models: dict[str, type[BaseModel]] | None = None  # Store models after discover()

    def discover(self) -> SimpleNamespace:
        """Discover API methods and return simplified runtime Pydantic models.

        Single entry point for interactive exploration in notebooks:
        - Connects to the server (lazy connection)
        - Displays available methods and their signatures
        - Returns simplified Pydantic models from OpenAPI schemas (structure only)
        - Enables automatic response parsing for model return types

        The returned models are simplified (structure only, no Field constraints or
        validators) for fast exploration. Server-side validation handles all constraints.
        For production code with complete models, use materialize() instead.

        After calling discover(), methods that return Pydantic models will
        automatically parse responses into the appropriate model type instead
        of returning raw dicts.

        No caching - each call fetches fresh data (function may have been redeployed).

        Returns:
            SimpleNamespace with Pydantic model classes as attributes

        Raises:
            httpx.HTTPError: If connection fails
            RuntimeError: If model creation fails

        Example:
            ```python
            client = FunctionClient("http://localhost:8000")

            # Before discover: returns dict
            result = client.get_item(item_id=42)
            print(type(result))  # <class 'dict'>

            # Discover and get models
            models = client.discover()
            # ✓ Connected to Asset Management API v1.0.0
            # Available methods:
            #   - get_item(item_id: int, include_tax: bool) -> ItemResponse
            #   - create_item(item: Item) -> ItemResponse
            # Models: Item, ItemResponse

            # After discover: returns typed model automatically!
            result = client.get_item(item_id=42)
            print(type(result))  # <class 'ItemResponse'>
            print(result.total_price)  # Direct typed access

            # Use models for validated requests
            item = models.Item(name="Widget", price=99.99)
            result = client.create_item(item=item)  # Returns ItemResponse

            # Or just explore without saving return value
            client.discover()  # Shows info, return value ignored
            ```
        """
        # Connect and fetch metadata if not already connected
        if not self._connected:
            self._fetch_methods_metadata()

        # Fetch OpenAPI schema for model creation (returns both document and schemas)
        openapi_doc, schemas = self._fetch_schemas()

        # Print formatted function information using already-fetched document
        self._print_function_info(openapi_doc, schemas)

        # Create Pydantic models from JSON schemas
        models_namespace = self._create_models_from_schemas(schemas)

        # Store models for automatic response parsing
        self._models = {
            name: getattr(models_namespace, name) for name in dir(models_namespace) if not name.startswith("_")
        }

        return models_namespace

    def describe(self, method_name: str) -> None:
        """Display detailed information about a specific method.

        Alternative to Python's built-in help() with richer formatting.
        Shows method signature, parameters, return type, and HTTP details.

        Args:
            method_name: Name of the method to describe

        Raises:
            ValueError: If method doesn't exist

        Example:
            ```python
            client = FunctionClient("http://localhost:8000")
            client.describe("create_item")
            # create_item(item: Item) -> ItemResponse
            #     Create a new item.
            #
            #     Parameters:
            #       item: Item (required)
            #         Field: name (str, required)
            #         Field: price (float, required)
            #         Field: description (str | None, optional)
            #
            #     Returns: ItemResponse
            #         Field: id (int)
            #         Field: total_price (float)
            #
            #     HTTP: POST /items/
            ```
        """
        # Connect if needed
        if not self._connected:
            self._fetch_methods_metadata()

        # Find the method metadata using O(1) lookup
        if self._methods_metadata is None:
            raise ValueError("No methods metadata available. Failed to connect?")

        method_metadata: MethodMetadata | None = (
            self._methods_by_name.get(method_name) if self._methods_by_name else None
        )

        if method_metadata is None:
            available = [m.name for m in self._methods_metadata.methods]
            raise ValueError(f"Method '{method_name}' not found. Available methods: {available}")

        # Get schemas for showing detailed type information
        _openapi_doc, schemas = self._fetch_schemas()

        # Print method signature
        param_strs = [f"{param.name}: {param.type}" for param in method_metadata.parameters]
        signature = f"{method_metadata.name}({', '.join(param_strs)}) -> {method_metadata.return_type}"
        print(signature)  # noqa: T201

        # Print description
        if method_metadata.description:
            print(f"    {method_metadata.description}")  # noqa: T201
            print()  # noqa: T201

        # Print parameters with details
        if method_metadata.parameters:
            print("    Parameters:")  # noqa: T201
            for param in method_metadata.parameters:
                required = "required" if param.required else "optional"
                print(f"      {param.name}: {param.type} ({required})")  # noqa: T201

                # Show field details for complex types (if schema available)
                # Extract base type name (e.g., "Item" from "Item" or "list[Item]")
                base_type = param.type.replace("list[", "").replace("]", "")
                if base_type in schemas:
                    schema = schemas[base_type]
                    required_fields = set(schema.required)
                    for field_name, field_schema in schema.properties.items():
                        field_type = field_schema.type or "any"
                        field_required = "required" if field_name in required_fields else "optional"
                        print(f"        Field: {field_name} ({field_type}, {field_required})")  # noqa: T201
            print()  # noqa: T201

        # Print return type details
        print(f"    Returns: {method_metadata.return_type}")  # noqa: T201
        if method_metadata.return_type in schemas:
            schema = schemas[method_metadata.return_type]
            for field_name, field_schema in schema.properties.items():
                field_type = field_schema.type or "any"
                print(f"        Field: {field_name} ({field_type})")  # noqa: T201
        print()  # noqa: T201

        # Print HTTP details
        print(f"    HTTP: {method_metadata.http_method} {method_metadata.path}")  # noqa: T201

    def _fetch_methods_metadata(self) -> None:
        """Fetch method metadata from the function for dynamic calling.

        Called lazily on first method access or discover() call.
        Handles both devserver (HTTP) and deployed function (SDK) modes.
        """
        if self._methods_metadata is not None:
            # Already fetched
            return

        if self._is_deployed:
            # Deployed function: use func.call() with introspection endpoint
            # /__client_methods__ is a framework-defined GET endpoint (see introspection.py)
            result = self._call_deployed("/__client_methods__", HTTPMethod.GET)
        else:
            # Devserver: direct HTTP
            import httpx  # type: ignore[import-not-found] # noqa: PLC0415

            response = httpx.get(f"{self.base_url}/__client_methods__", timeout=10.0)
            response.raise_for_status()
            result = response.json()

        # Unwrap Cognite Functions response format using Pydantic models
        # Use status_code < 400 to determine success (new wire format)
        try:
            status_code: int | None = None
            if isinstance(result, dict):
                result = cast(dict[str, Any], result)
                raw_status = result.get("status_code")
                if isinstance(raw_status, int):
                    status_code = raw_status
            if status_code is None or status_code >= 400:
                error = CogniteFunctionError.model_validate(result)
                raise RuntimeError(f"{error.error_type}: {error.message}")
            response_obj = CogniteFunctionResponse.model_validate(result)
            data_dict = response_obj.data
        except ValidationError as e:
            warnings.warn(
                f"Response validation failed during method discovery - this may indicate a schema mismatch. "
                f"Falling back to raw result. Validation error: {e}",
                UserWarning,
                stacklevel=2,
            )
            data_dict = result  # type: ignore[reportUnknownVariableType]

        # Parse into typed ClientMethodsMetadata model
        try:
            self._methods_metadata = ClientMethodsMetadata.model_validate(data_dict)
        except ValidationError as e:
            raise RuntimeError(f"Failed to parse method metadata: {e}") from e

        # Build O(1) method lookup cache
        if self._methods_metadata:
            self._methods_by_name = {method.name: method for method in self._methods_metadata.methods}

        # Attach methods as instance attributes for IDE tab completion
        self._attach_methods()
        self._connected = True

    def _fetch_full_metadata(self) -> dict[str, Any]:
        """Fetch complete metadata including models for code generation.

        Returns:
            Dictionary with 'methods', 'models', and 'imports' keys
        """
        if self._is_deployed:
            # Deployed function: use func.call()
            # /__client_methods__ is a framework-defined GET endpoint (see introspection.py)
            result = self._call_deployed("/__client_methods__", HTTPMethod.GET)
        else:
            # Devserver: direct HTTP
            import httpx  # type: ignore[import-not-found]  # noqa: PLC0415

            response = httpx.get(f"{self.base_url}/__client_methods__", timeout=30.0)
            response.raise_for_status()
            result = response.json()

        # Unwrap Cognite Functions response format
        # Use status_code < 400 to determine success (new wire format)
        try:
            status_code2: int | None = None
            if isinstance(result, dict):
                result = cast(dict[str, Any], result)
                raw_status2 = result.get("status_code")
                if isinstance(raw_status2, int):
                    status_code2 = raw_status2
            if status_code2 is None or status_code2 >= 400:
                error = CogniteFunctionError.model_validate(result)
                raise RuntimeError(f"{error.error_type}: {error.message}")
            response_obj = CogniteFunctionResponse.model_validate(result)
            if isinstance(response_obj.data, dict):
                return response_obj.data
            raise TypeError(f"Expected metadata to be a dict, but got {type(response_obj.data).__name__}")
        except ValidationError as e:
            warnings.warn(
                f"Response validation failed while fetching full metadata - this may indicate a schema mismatch. "
                f"Falling back to raw result. Validation error: {e}",
                UserWarning,
                stacklevel=2,
            )
            if isinstance(result, dict):
                return cast(dict[str, Any], result)  # Safe to cast because we check for dict above
            raise TypeError(f"Expected metadata to be a dict, but got {type(result).__name__}")

    def _fetch_schemas(self) -> tuple[OpenAPIDocument, dict[str, OpenAPISchema]]:
        """Fetch and parse OpenAPI specification.

        Returns:
            Tuple of (openapi_document, schemas_dict) where:
            - openapi_document: Typed OpenAPIDocument from the /__schema__ endpoint
            - schemas_dict: Parsed OpenAPISchema models by name
        """
        # Use /__schema__ endpoint which works for both devserver and deployed functions
        # _call_method automatically handles unwrapping the response envelope
        try:
            openapi_dict = self._call_method("/__schema__", HTTPMethod.GET)
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve schema: {e}") from e

        # Validate response structure
        if not isinstance(openapi_dict, dict):
            raise TypeError(f"Expected OpenAPI spec to be a dict, but got {type(openapi_dict).__name__}")

        # Parse into typed OpenAPIDocument
        try:
            openapi_doc = OpenAPIDocument.model_validate(openapi_dict)
        except ValidationError as e:
            raise RuntimeError(f"Failed to parse OpenAPI document: {e}") from e

        # Extract and parse component schemas
        typed_schemas: dict[str, OpenAPISchema] = {}
        if openapi_doc.components:
            for schema_name, schema_data in openapi_doc.components.schemas.items():
                try:
                    typed_schemas[schema_name] = OpenAPISchema.model_validate(schema_data)
                except ValidationError as e:
                    warnings.warn(
                        f"Failed to parse schema for '{schema_name}': {e}. Using empty schema.",
                        UserWarning,
                        stacklevel=2,
                    )
                    typed_schemas[schema_name] = OpenAPISchema()

        return openapi_doc, typed_schemas

    def _print_function_info(self, openapi_doc: OpenAPIDocument, schemas: dict[str, OpenAPISchema]) -> None:
        """Print formatted information about available methods and models.

        Args:
            openapi_doc: Typed OpenAPI document
            schemas: Dictionary of typed OpenAPI schema definitions
        """
        title = openapi_doc.info.title
        version = openapi_doc.info.version

        # Print connection success
        print(f"✓ Connected to {title} v{version}")  # noqa: T201
        print()  # noqa: T201

        # Print available methods
        if self._methods_metadata:
            print("Available methods:")  # noqa: T201
            for method in self._methods_metadata.methods:
                # Format parameters
                param_strs: list[str] = []
                for param in method.parameters:
                    param_strs.append(f"{param.name}: {param.type}")

                # Build signature
                signature = f"{method.name}({', '.join(param_strs)}) -> {method.return_type}"
                print(f"  - {signature}")  # noqa: T201
            print()  # noqa: T201

        # Print available models
        if schemas:
            model_names = ", ".join(sorted(schemas.keys()))
            print(f"Models: {model_names}")  # noqa: T201
            print()  # noqa: T201

        print("Use help(client.method_name) or client.describe('method_name') for details")  # noqa: T201

    def _create_models_from_schemas(self, schemas: dict[str, OpenAPISchema]) -> SimpleNamespace:
        """Dynamically create Pydantic model classes from OpenAPI schemas.

        Creates simplified models with just structure (no Field constraints).
        Server-side validation handles all constraints anyway.

        Args:
            schemas: Dictionary of schema_name -> typed OpenAPI schema

        Returns:
            SimpleNamespace with model classes as attributes

        Raises:
            RuntimeError: If model creation fails with details about the error
        """
        if not schemas:
            return SimpleNamespace()

        # Filter out built-in models that are already defined in the framework
        # These are shipped with the library and shouldn't be recreated
        # Reference classes directly so names stay in sync if models are renamed
        builtin_model_classes = [
            # Response/error models
            CogniteFunctionError,
            CogniteFunctionResponse,
            # OpenAPI document models
            OpenAPIDocument,
            OpenAPISchema,
            OpenAPIProperty,
            OpenAPIRef,
            OpenAPIInfo,
            OpenAPIServer,
            OpenAPIPathItem,
            OpenAPIOperation,
            OpenAPIParameter,
            OpenAPIRequestBody,
            OpenAPIResponse,
            OpenAPIMediaType,
            OpenAPIComponents,
        ]
        builtin_models = {cls.__name__ for cls in builtin_model_classes}

        # Pre-populate created_models with built-in types so dependencies resolve correctly
        # Only include models that might be referenced in user schemas
        created_models: dict[str, type[BaseModel]] = {
            CogniteFunctionError.__name__: CogniteFunctionError,
            CogniteFunctionResponse.__name__: CogniteFunctionResponse,
            OpenAPIDocument.__name__: OpenAPIDocument,
        }

        # Filter schemas to only user-defined models
        user_schemas = {name: schema for name, schema in schemas.items() if name not in builtin_models}

        if not user_schemas:
            return SimpleNamespace(**created_models)

        # Build dependency graph from $ref references (only for user schemas)
        deps = self._build_dependency_graph(user_schemas)

        # Topological sort to determine creation order
        creation_order = self._topological_sort(deps)

        # Create models in dependency order
        for model_name in creation_order:
            if model_name not in user_schemas:
                # Dependency not in schemas, skip it
                continue

            schema = user_schemas[model_name]
            try:
                created_models[model_name] = self._create_model_from_schema(model_name, schema, created_models)
            except (TypeError, ValueError) as e:
                raise RuntimeError(
                    f"Failed to create model '{model_name}' from schema. Schema: {schema}. Error: {e}"
                ) from e

        return SimpleNamespace(**created_models)

    def _create_model_from_schema(
        self, model_name: str, schema: OpenAPISchema | dict[str, Any], existing_models: dict[str, type[BaseModel]]
    ) -> type[BaseModel]:
        """Create a Pydantic model from OpenAPI schema.

        Creates a simplified model with just structure, no Field constraints.
        Server-side validation handles all constraints anyway.

        Args:
            model_name: Name of the model to create
            schema: Typed OpenAPI schema definition or raw dict (converted internally)
            existing_models: Already created models (for resolving references)

        Returns:
            Dynamically created Pydantic model class
        """
        # Convert dict to OpenAPISchema at the boundary for type safety
        if isinstance(schema, dict):
            schema = OpenAPISchema.model_validate(schema)

        # Now we always work with typed objects
        properties = schema.properties
        required_fields = set(schema.required)

        fields: dict[str, Any] = {}
        for field_name, field_schema in properties.items():
            # Parse type from JSON Schema (field_schema is always OpenAPIProperty)
            field_type = self._json_schema_to_python_type(field_schema, existing_models)

            # Determine if field is required
            if field_name in required_fields:
                fields[field_name] = (field_type, ...)  # Required
            else:
                # Check if schema specifies a default
                default = field_schema.default
                fields[field_name] = (field_type, default)

        return create_model(model_name, **fields)

    def _json_schema_to_python_type(
        self, schema: OpenAPIProperty | OpenAPIRef | dict[str, Any], existing_models: dict[str, type[BaseModel]]
    ) -> Any:
        """Convert OpenAPI Property schema to Python type annotation.

        Handles:
        - Primitives: string, number, integer, boolean
        - Arrays: {"type": "array", "items": {...}} - recursively processes items
        - Objects: {"type": "object"} -> dict[str, Any]
        - References: OpenAPIRef or {"$ref": "#/components/schemas/Item"} -> Item model
        - anyOf/oneOf for unions (e.g., Optional types)
        - null types

        Args:
            schema: Typed OpenAPI property, OpenAPIRef, or raw dict (converted internally)
            existing_models: Already created models (for resolving references)

        Returns:
            Python type annotation
        """
        # Handle OpenAPIRef directly - extract model from $ref
        if isinstance(schema, OpenAPIRef):
            ref_value = schema.ref
            if ref_value:
                model_name = ref_value.split("/")[-1]
                if model_name in existing_models:
                    return existing_models[model_name]
            return Any

        # Convert dict to OpenAPIProperty at the boundary for type safety
        if isinstance(schema, dict):
            schema = OpenAPIProperty.model_validate(schema)

        # Now work directly with the typed object - access extra fields via model_extra
        # This is more efficient than model_dump() especially in recursive calls
        model_extra = schema.model_extra or {}

        # Handle $ref (model references)
        ref_path = schema.ref or model_extra.get("$ref")
        if ref_path:
            model_name = ref_path.split("/")[-1]  # Extract "Item" from "#/components/schemas/Item"
            return existing_models.get(model_name, Any)

        # Handle anyOf/oneOf (unions, including Optional) - stored in extra fields
        if "anyOf" in model_extra:
            any_of_schemas = cast(list[dict[str, Any]], model_extra["anyOf"])
            types: list[Any] = []
            for s_dict in any_of_schemas:
                # Recursively parse - convert dict to OpenAPIProperty
                types.append(self._json_schema_to_python_type(s_dict, existing_models))
            # Filter out NoneType and create Union
            non_none: list[Any] = [t for t in types if t is not type(None)]
            has_none = type(None) in types
            if len(non_none) == 1 and has_none:
                return non_none[0] | None  # type: ignore[reportReturnType]
            # For complex unions, fall back to Any - server validates anyway
            return Any

        # Handle arrays - use typed property
        if schema.type == "array" and schema.items:
            # Recursively process items - _json_schema_to_python_type handles all types
            item_type = self._json_schema_to_python_type(schema.items, existing_models)
            return list[item_type]  # type: ignore[reportReturnType]

        # Handle primitives - use typed property directly
        type_map: dict[str, Any] = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "object": dict[str, Any],
            "null": type(None),
        }

        return type_map.get(schema.type, Any) if schema.type else Any  # type: ignore[reportReturnType]

    def _build_dependency_graph(self, schemas: Mapping[str, OpenAPISchema | dict[str, Any]]) -> dict[str, set[str]]:
        """Build dependency graph from OpenAPI schema $ref references.

        Args:
            schemas: Dictionary of typed OpenAPI schema definitions or dicts (converted internally)

        Returns:
            Dictionary mapping model_name -> set of model names it depends on
        """
        deps: dict[str, set[str]] = {}

        for model_name, schema in schemas.items():
            deps[model_name] = set()
            # Convert to OpenAPISchema at boundary, then to dict for recursive ref extraction
            if isinstance(schema, dict):
                schema = OpenAPISchema.model_validate(schema)
            schema_dict = schema.model_dump(exclude_none=True)
            # Recursively find all $ref references in the schema
            self._extract_refs(schema_dict, deps[model_name])

        return deps

    def _extract_refs(self, obj: Json, refs: set[str]) -> None:
        """Recursively extract all $ref model names from a schema.

        Args:
            obj: Schema object to search (dict, list, or primitive)
            refs: Set to accumulate found model names
        """
        if isinstance(obj, dict):
            # Handle $ref key (or variations: empty string or 'ref' if serializer didn't run)
            ref = obj.get("$ref") or obj.get("") or obj.get("ref")
            if ref and isinstance(ref, str):
                model_name = ref.split("/")[-1]
                refs.add(model_name)
                return  # Don't recurse into $ref objects
            # Recursively process all values
            for value in obj.values():
                self._extract_refs(value, refs)
        elif isinstance(obj, list):
            for item in obj:
                self._extract_refs(item, refs)

    def _topological_sort(self, deps: dict[str, set[str]]) -> list[str]:
        """Topologically sort models by dependencies.

        Models with no dependencies come first, then models that depend on them, etc.

        Args:
            deps: Dictionary mapping model_name -> set of dependencies

        Returns:
            List of model names in dependency order

        Raises:
            RuntimeError: If circular dependencies are detected
        """
        # Kahn's algorithm for topological sort
        # in_degree represents how many dependencies a node has
        in_degree: dict[str, int] = {node: len(deps[node]) for node in deps}

        # Queue of nodes with no dependencies (in_degree == 0)
        queue: list[str] = [node for node, degree in in_degree.items() if degree == 0]
        result: list[str] = []

        while queue:
            # Sort for deterministic output
            queue.sort()
            node = queue.pop(0)
            result.append(node)

            # For each other node that depends on this node, reduce its in-degree
            for other_node, _ in deps.items():
                if node in deps[other_node]:
                    in_degree[other_node] -= 1
                    if in_degree[other_node] == 0:
                        queue.append(other_node)

        # Check for cycles
        if len(result) != len(deps):
            unresolved = set(deps.keys()) - set(result)
            raise RuntimeError(
                f"Circular dependencies detected or missing model definition. Unresolved models: {unresolved}"
            )

        return result

    def _attach_methods(self) -> None:
        """Attach all methods as instance attributes for IDE tab completion.

        This enables IDE autocompletion by making methods discoverable via
        introspection rather than just through __getattr__.
        """
        if self._methods_metadata is None:
            return

        for method in self._methods_metadata.methods:
            # Create and attach the method as an instance attribute
            dynamic_method = self._create_dynamic_method(method.name, method)
            setattr(self, method.name, dynamic_method)

    def __getattr__(self, name: str) -> Any:
        """Dynamically create callable methods from fetched metadata.

        Lazy loads metadata on first access.

        Args:
            name: Method name to call

        Returns:
            Callable that makes the HTTP request

        Raises:
            AttributeError: If method doesn't exist
        """
        import httpx  # type: ignore[import-not-found]  # noqa: PLC0415

        if name.startswith("_"):
            # Don't intercept private attributes
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        # Lazy load metadata on first method access
        if self._methods_metadata is None:
            try:
                self._fetch_methods_metadata()
            except (httpx.HTTPError, RuntimeError, CogniteException) as e:
                raise AttributeError(f"Failed to fetch methods from {self.base_url}. Is the server running?") from e

        # Find the method in the metadata using O(1) lookup
        if self._methods_by_name:
            method = self._methods_by_name.get(name)
            if method:
                return self._create_dynamic_method(name, method)

        available = [m.name for m in self._methods_metadata.methods] if self._methods_metadata else []
        raise AttributeError(f"Method '{name}' not found. Available methods: {available}")

    def _create_dynamic_method(self, method_name: str, metadata: MethodMetadata) -> Any:
        """Create a callable method from metadata.

        Args:
            method_name: Name of the method
            metadata: Typed method metadata including path, http_method, parameters

        Returns:
            Callable that makes the HTTP request or SDK call
        """

        def dynamic_method(**kwargs: Any) -> Any:
            """Dynamically generated method that makes HTTP request or SDK call."""
            path = metadata.path
            http_method_str = metadata.http_method
            parameters = metadata.parameters

            # Build path parameters
            for param in parameters:
                if param.in_ == "path" and param.name in kwargs:
                    path = path.replace(f"{{{param.name}}}", str(kwargs[param.name]))

            # Build query parameters
            query_params: dict[str, Any] = {}
            for param in parameters:
                if param.in_ == "query" and param.name in kwargs:
                    query_params[param.name] = kwargs[param.name]

            # Build body
            body_data: dict[str, Any] = {}
            for param in parameters:
                if param.in_ == "body" and param.name in kwargs:
                    value = kwargs[param.name]
                    # Check if it's a Pydantic model
                    if hasattr(value, "model_dump"):
                        body_data[param.name] = value.model_dump()
                    else:
                        body_data[param.name] = value

            # Make the request using base class method (handles both devserver and deployed)
            try:
                data = self._call_method(
                    path=path,
                    method=HTTPMethod(http_method_str),
                    body=body_data if body_data else None,
                    params=query_params if query_params else None,
                )
            except RuntimeError as e:
                # Re-raise RuntimeError from _call_method (already formatted)
                raise RuntimeError(f"Method '{method_name}' failed: {e}") from e

            except Exception as e:
                # Catch any other unexpected errors
                warnings.warn(
                    f"Request failed for method '{method_name}': {e}",
                    UserWarning,
                    stacklevel=2,
                )
                raise

            # Parse response into Pydantic model if return type is a model
            if self._models:
                return_type = metadata.return_type
                # Extract base type name (e.g., "Item" from "Item" or "list[Item]")
                base_type = m.group(1) if (m := re.search(r"([A-Z][a-zA-Z0-9_]*)", return_type)) else ""
                if base_type in self._models:
                    model_class = self._models[base_type]
                    # Handle list responses
                    if return_type.startswith("list["):
                        if isinstance(data, list):
                            data = cast(list[object], data)
                            return [model_class.model_validate(item) for item in data]
                    else:
                        # Single model response
                        return model_class.model_validate(data)

            return data

        # Set docstring
        dynamic_method.__doc__ = metadata.description or f"Call {method_name}"
        dynamic_method.__name__ = method_name

        return dynamic_method

    def materialize(self, output_path: str | Path | None = None) -> str | None:
        """Generate a fully typed Python client with complete models and methods.

        Creates a complete, executable Python client that can be imported and used
        in your code. Uses inspect.getsource() to extract the actual Pydantic model
        definitions, preserving all validators, Field constraints, and custom logic.

        The generated client includes:
        - Complete Pydantic models with all validators and Field constraints
        - Type-safe client methods for each endpoint
        - Proper imports and error handling
        - Full docstrings

        The generated client is self-contained and production-ready - no manual imports
        or modifications needed.

        Args:
            output_path: Path where the generated client should be saved. If None, returns the client content.

        Returns:
            Client content as string if output_path is None, otherwise None

        Raises:
            httpx.HTTPError: If the request fails
            ImportError: If jinja2 is not installed

        Example:
            ```python
            client = FunctionClient("http://localhost:8000")

            # Save to file
            client.materialize("clients/asset_management.py")

            # Or print to stdout for testing
            print(client.materialize())

            # Import and use the generated client (when saved)
            from clients.asset_management import AssetManagementClient, Item

            typed_client = AssetManagementClient("http://localhost:8000")
            item = Item(name="Widget", price=99.99)
            result = typed_client.create_item(item)
            ```
        """
        try:
            import jinja2  # type: ignore[import-not-found]  # noqa: PLC0415, F401
        except ImportError as e:
            raise ImportError(
                "Client generation requires jinja2. Install it with: pip install cognite-function-apps[client]"
            ) from e

        # Fetch complete metadata
        metadata = self._fetch_full_metadata()

        # Generate client content using Jinja2
        content = self._render_client_template(metadata)

        if output_path is None:
            return content

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w") as f:
            f.write(content)

        print(f"✓ Generated typed client: {output_path}")  # noqa: T201
        return None

    def _render_client_template(self, metadata: dict[str, Any]) -> str:
        """Render full client using Jinja2 template.

        Args:
            metadata: Metadata dictionary with 'methods', 'models', and 'imports' keys

        Returns:
            Generated client file content
        """
        from jinja2 import Template  # type: ignore[import-not-found]  # noqa: PLC0415

        # Get app title from OpenAPI spec using /__schema__ endpoint
        # _call_method automatically handles unwrapping the response envelope
        openapi_spec = self._call_method("/__schema__", HTTPMethod.GET)
        info = openapi_spec.get("info", {})
        app_title = info.get("title", "Generated API")

        # Generate class name from app title
        words: list[str] = []
        for word in app_title.split():
            if word.isupper() and len(word) > 1:
                words.append(word)
            else:
                words.append(word.capitalize())
        class_name = "".join(words) + "Client"

        # Load template from package resources
        try:
            # Python 3.9+ importlib.resources approach
            from importlib.resources import files  # type: ignore[attr-defined]  # noqa: PLC0415

            template_path = files("cognite_function_apps.templates").joinpath("client_template.jinja2")
            template_content = template_path.read_text()
        except (ImportError, AttributeError):
            # Fallback for older Python versions
            from importlib.resources import read_text  # type: ignore[attr-defined]  # noqa: PLC0415

            template_content = read_text("cognite_function_apps.templates", "client_template.jinja2")

        template = Template(template_content)  # type: ignore[reportUnknownVariableType]

        return template.render(  # type: ignore[reportUnknownMemberType,reportReturnType]
            app_title=app_title,
            class_name=class_name,
            methods=metadata.get("methods", []),
            models=metadata.get("models", []),
            imports=metadata.get("imports", []),
        )
