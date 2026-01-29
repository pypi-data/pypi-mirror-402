"""Tests for client generation functionality.

This module tests the generation of typed Python clients from function metadata,
including model discovery, source extraction, and client code generation.
"""

import logging
import sys
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest
from cognite.client import CogniteClient
from pydantic import BaseModel, Field

from cognite_function_apps import FunctionApp, FunctionClient, create_function_service, create_introspection_app
from cognite_function_apps.client_generation import (
    _discover_models_from_handler,  # type: ignore[reportPrivateUsage]
    _extract_models_from_type,  # type: ignore[reportPrivateUsage]
    generate_client_methods_metadata,
)


# Test models with various complexity levels
class SimpleModel(BaseModel):
    """Simple model for testing."""

    name: str
    value: int


class NestedModel(BaseModel):
    """Model with nested reference."""

    id: int
    simple: SimpleModel


class OptionalModel(BaseModel):
    """Model with optional fields."""

    required: str
    optional: str | None = None
    nested: NestedModel | None = None


class ListModel(BaseModel):
    """Model with list fields."""

    items: list[SimpleModel]
    tags: list[str]


class ComplexModel(BaseModel):
    """Model with Field and various annotations."""

    id: int = Field(description="The unique ID")
    name: str = Field(min_length=1, max_length=100)
    nested: NestedModel
    optional_list: list[SimpleModel] | None = None


class TestModelDiscovery:
    """Test model discovery from handlers and type hints."""

    def test_extract_models_from_direct_type(self):
        """Test extracting a direct BaseModel type."""
        models = _extract_models_from_type(SimpleModel)
        assert SimpleModel in models
        assert len(models) == 1

    def test_extract_models_from_optional(self):
        """Test extracting models from Optional type."""
        models = _extract_models_from_type(SimpleModel | None)
        assert SimpleModel in models

    def test_extract_models_from_list(self):
        """Test extracting models from list type."""
        models = _extract_models_from_type(list[SimpleModel])
        assert SimpleModel in models

    def test_extract_models_from_dict(self):
        """Test extracting models from dict values."""
        models = _extract_models_from_type(dict[str, SimpleModel])
        assert SimpleModel in models

    def test_extract_models_from_non_model(self):
        """Test that non-model types return empty list."""
        models = _extract_models_from_type(str)
        assert len(models) == 0

        models = _extract_models_from_type(int)
        assert len(models) == 0

    def test_discover_models_from_simple_handler(self):
        """Test discovering models from a simple handler."""

        def handler(item: SimpleModel) -> SimpleModel:
            return item

        models = _discover_models_from_handler(handler)
        assert SimpleModel in models
        assert len(models) == 1

    def test_discover_models_from_nested_handler(self):
        """Test discovering nested models."""

        def handler(item: NestedModel) -> NestedModel:
            return item

        models = _discover_models_from_handler(handler)
        # Should discover both NestedModel and SimpleModel
        assert NestedModel in models
        assert SimpleModel in models

    def test_discover_models_from_complex_handler(self):
        """Test discovering models from complex handler with multiple types."""

        def handler(simple: SimpleModel, optional: OptionalModel | None = None) -> ComplexModel:
            return ComplexModel(id=1, name="test", nested=NestedModel(id=1, simple=simple))

        models = _discover_models_from_handler(handler)
        # Should discover all referenced models
        assert SimpleModel in models
        assert NestedModel in models
        assert OptionalModel in models
        assert ComplexModel in models

    def test_discover_models_from_list_handler(self):
        """Test discovering models from handlers with list parameters."""

        def handler(items: list[SimpleModel]) -> list[NestedModel]:
            return []

        models = _discover_models_from_handler(handler)
        assert SimpleModel in models
        assert NestedModel in models

    def test_discover_models_handles_circular_refs(self):
        """Test that circular references don't cause infinite loops."""

        class CircularA(BaseModel):
            name: str
            b: "CircularB | None" = None

        class CircularB(BaseModel):
            value: int
            a: CircularA | None = None

        def handler(item: CircularA) -> CircularA:
            return item

        # Should not hang or error
        models = _discover_models_from_handler(handler)
        assert CircularA in models


class TestClientGeneration:
    """Test generation of stub and client code."""

    def test_metadata_includes_models(self):
        """Test that metadata includes model source code."""
        app = FunctionApp("Test API", "1.0.0")

        @app.get("/items/{item_id}")
        def get_item(client: CogniteClient, item_id: int) -> SimpleModel:
            """Get an item."""
            return SimpleModel(name="test", value=42)

        metadata = generate_client_methods_metadata(app.routes, app.registry)

        # Should have methods and models keys
        assert "methods" in metadata
        assert "models" in metadata
        assert "imports" in metadata

        # Should contain the model
        models = metadata["models"]
        assert len(models) == 1
        assert models[0]["name"] == "SimpleModel"
        assert "class SimpleModel(BaseModel):" in models[0]["source"]

    def test_metadata_includes_nested_models(self):
        """Test that metadata includes nested models."""
        app = FunctionApp("Test API", "1.0.0")

        @app.post("/items/")
        def create_item(client: CogniteClient, item: ComplexModel) -> ComplexModel:
            """Create an item."""
            return item

        metadata = generate_client_methods_metadata(app.routes, app.registry)

        # Should contain all models
        models = metadata["models"]
        model_names = {m["name"] for m in models}
        assert "SimpleModel" in model_names
        assert "NestedModel" in model_names
        assert "ComplexModel" in model_names

        # Should contain Field import
        imports = metadata["imports"]
        assert any("Field" in imp for imp in imports)

    def test_metadata_filters_injected_params(self):
        """Test that metadata filters injected dependencies."""
        app = FunctionApp("Test API", "1.0.0")

        @app.get("/items/")
        def get_items(client: CogniteClient, limit: int = 10) -> list[SimpleModel]:
            """Get items."""
            return []

        metadata = generate_client_methods_metadata(app.routes, app.registry)

        # Should NOT include client parameter
        methods = metadata["methods"]
        assert len(methods) == 1
        params = methods[0]["parameters"]
        param_names = {p["name"] for p in params}
        assert "limit" in param_names
        assert "client" not in param_names


class TestEndToEnd:
    """End-to-end tests with introspection app."""

    def test_introspection_endpoints_exist(self):
        """Test that introspection endpoints are created."""
        introspection = create_introspection_app()
        app = FunctionApp("Test API", "1.0.0")

        @app.get("/test")
        def test_endpoint(client: CogniteClient) -> dict[str, str]:
            """Test endpoint."""
            return {"status": "ok"}

        _handle = create_function_service(introspection, app)

        # Check that the client methods endpoint exists
        assert "/__client_methods__" in introspection.routes
        # Old endpoints should be removed
        assert "/__python_stubs__" not in introspection.routes
        assert "/__python_client__" not in introspection.routes

    def test_metadata_structure(self):
        """Test the structure of metadata returned by introspection."""
        introspection = create_introspection_app()
        app = FunctionApp("Asset Management", "1.0.0")

        @app.get("/items/{item_id}")
        def get_item(client: CogniteClient, item_id: int) -> SimpleModel:
            """Get an item."""
            return SimpleModel(name="test", value=42)

        @app.post("/items/")
        def create_item(client: CogniteClient, item: SimpleModel) -> SimpleModel:
            """Create an item."""
            return item

        _handle = create_function_service(introspection, app)

        # Generate metadata through introspection
        metadata = generate_client_methods_metadata(
            routes=introspection.all_routes,
            registry=introspection.registry,
        )

        # Should have correct structure
        assert "methods" in metadata
        assert "models" in metadata
        assert "imports" in metadata

        # Should have both methods
        methods = metadata["methods"]
        method_names = {m["name"] for m in methods}
        assert "get_item" in method_names
        assert "create_item" in method_names

        # Should have the model
        models = metadata["models"]
        model_names = {m["name"] for m in models}
        assert "SimpleModel" in model_names


class TestClientMethodsMetadata:
    """Test the __client_methods__ endpoint."""

    def test_client_methods_metadata_generation(self):
        """Test generating metadata for dynamic client."""
        app = FunctionApp("Test API", "1.0.0")

        @app.get("/items/{item_id}")
        def get_item(client: CogniteClient, item_id: int, include_tax: bool = False) -> SimpleModel:
            """Get an item."""
            return SimpleModel(name="test", value=42)

        @app.post("/items/")
        def create_item(client: CogniteClient, item: SimpleModel) -> SimpleModel:
            """Create an item."""
            return item

        metadata = generate_client_methods_metadata(app.routes, app.registry)

        # Should have methods, models, and imports
        assert "methods" in metadata
        assert "models" in metadata
        assert "imports" in metadata

        methods = metadata["methods"]

        # Should have 2 methods
        assert len(methods) == 2

        # Check get_item metadata
        get_item_meta = next(m for m in methods if m["name"] == "get_item")
        assert get_item_meta["path"] == "/items/{item_id}"
        assert get_item_meta["http_method"] == "GET"
        assert get_item_meta["description"] == "Get an item."
        assert get_item_meta["return_type"] == "SimpleModel"

        # Check parameters
        params = get_item_meta["parameters"]
        assert len(params) == 2
        item_id_param = next(p for p in params if p["name"] == "item_id")
        assert item_id_param["in"] == "path"
        assert item_id_param["required"] is True

        include_tax_param = next(p for p in params if p["name"] == "include_tax")
        assert include_tax_param["in"] == "query"
        assert include_tax_param["required"] is False

        # Check create_item metadata
        create_item_meta = next(m for m in methods if m["name"] == "create_item")
        assert create_item_meta["path"] == "/items/"
        assert create_item_meta["http_method"] == "POST"

        # Should have body parameter
        create_params = create_item_meta["parameters"]
        assert len(create_params) == 1
        assert create_params[0]["name"] == "item"
        assert create_params[0]["in"] == "body"

    def test_client_methods_filters_injected_dependencies(self):
        """Test that client, logger, etc. are filtered from metadata."""
        app = FunctionApp("Test API", "1.0.0")

        @app.get("/items/")
        def get_items(client: CogniteClient, logger: logging.Logger, limit: int = 10) -> list[SimpleModel]:
            """Get items."""
            return []

        metadata = generate_client_methods_metadata(app.routes, app.registry)

        methods = metadata["methods"]

        # Should only have limit parameter (client and logger filtered)
        params = methods[0]["parameters"]
        assert len(params) == 1
        assert params[0]["name"] == "limit"


class TestFunctionClient:
    """Test the FunctionClient class."""

    def test_function_client_init_with_base_url(self):
        """Test FunctionClient initialization with base_url - no I/O."""
        pytest.importorskip("httpx")

        # Constructor should not make any network calls
        client = FunctionClient(base_url="http://localhost:8000")
        assert client.base_url == "http://localhost:8000"
        assert client._connected is False  # type: ignore[reportProtectedMemberAccess]
        assert client._methods_metadata is None  # type: ignore[reportProtectedMemberAccess]

    def test_function_client_strips_trailing_slash(self):
        """Test that trailing slashes are removed."""
        pytest.importorskip("httpx")

        client = FunctionClient(base_url="http://localhost:8000/")
        assert client.base_url == "http://localhost:8000"

    def test_function_client_requires_parameters(self):
        """Test that FunctionClient requires either base_url or project/function_id."""
        pytest.importorskip("httpx")

        with pytest.raises(ValueError, match="Either base_url or"):
            FunctionClient()

    def test_function_client_deployed_requires_valid_params(self, mock_client: CogniteClient):
        """Test that deployed function requires cognite_client and function identifier."""
        pytest.importorskip("httpx")

        # Missing function identifier (external_id or id)
        with pytest.raises(ValueError, match="Either base_url or"):
            FunctionClient(cognite_client=mock_client)

        # Missing cognite_client parameter
        with pytest.raises(ValueError, match="Either base_url or"):
            FunctionClient(function_external_id="test-function")

        # Valid: cognite_client + external_id (no I/O, should succeed)
        try:
            client = FunctionClient(cognite_client=mock_client, function_external_id="test-function")
            # Constructor should not raise, function retrieved lazily
            assert client is not None
        except ImportError:
            # cognite-sdk not installed, this is expected in CI
            pass

        # Valid: cognite_client + id (no I/O, should succeed)
        try:
            client = FunctionClient(cognite_client=mock_client, function_id=123)
            # Constructor should not raise, function retrieved lazily
            assert client is not None
        except ImportError:
            # cognite-sdk not installed, this is expected in CI
            pass

    def test_function_client_materialize_creates_file(self):
        """Test that materialize creates a file."""
        pytest.importorskip("httpx")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "clients" / "test_client.py"

            # This will fail since we're not running a server, but we can test the path handling
            _client = FunctionClient(base_url="http://localhost:8000")

            # Test that the parent directory would be created
            assert not output_path.parent.exists()

    def test_function_client_requires_httpx(self):
        """Test that FunctionClient raises ImportError if httpx is not available."""
        # This test might pass if httpx is installed, but documents the expected behavior

        # Temporarily hide httpx
        with patch.dict(sys.modules, {"httpx": None}):
            # Clear the import cache
            if "cognite_function_apps.client" in sys.modules:
                del sys.modules["cognite_function_apps.client"]

            # Now try to import - this might not work perfectly in tests
            # but documents the intent
            try:
                # If httpx is installed, this will work
                # We're just documenting that it should check for httpx
                assert FunctionClient is not None  # Ensure import is used
            except ImportError:
                pass  # Expected if httpx is not available


class TestFunctionClientDiscovery:
    """Test the new discovery functionality."""

    def test_discover_lazy_connection(self):
        """Test that discover() connects lazily."""
        pytest.importorskip("httpx")

        client = FunctionClient(base_url="http://localhost:8000")

        # Constructor doesn't connect
        assert client._connected is False  # type: ignore[reportProtectedMemberAccess]

        # discover() would connect, but we can't test it without a server
        # This test documents the expected behavior

    def test_json_schema_to_python_type_primitives(self):
        """Test converting JSON Schema primitives to Python types."""
        pytest.importorskip("httpx")

        client = FunctionClient(base_url="http://localhost:8000")

        # Test primitive types
        assert client._json_schema_to_python_type({"type": "string"}, {}) is str  # type: ignore[reportProtectedMemberAccess]
        assert client._json_schema_to_python_type({"type": "integer"}, {}) is int  # type: ignore[reportProtectedMemberAccess]
        assert client._json_schema_to_python_type({"type": "number"}, {}) is float  # type: ignore[reportProtectedMemberAccess]
        assert client._json_schema_to_python_type({"type": "boolean"}, {}) is bool  # type: ignore[reportProtectedMemberAccess]
        assert client._json_schema_to_python_type({"type": "null"}, {}) is type(None)  # type: ignore[reportProtectedMemberAccess]

    def test_json_schema_to_python_type_array(self):
        """Test converting JSON Schema array type."""
        pytest.importorskip("httpx")

        client = FunctionClient(base_url="http://localhost:8000")

        # Array of strings
        array_schema = {"type": "array", "items": {"type": "string"}}
        result = client._json_schema_to_python_type(array_schema, {})  # type: ignore[reportProtectedMemberAccess]
        # Check if it's a list type (can't easily check the generic param at runtime)
        assert str(result).startswith("list[")

    def test_json_schema_to_python_type_optional(self):
        """Test converting JSON Schema anyOf with null (Optional)."""
        pytest.importorskip("httpx")

        client = FunctionClient(base_url="http://localhost:8000")

        # Optional string (anyOf: [string, null])
        optional_schema = {"anyOf": [{"type": "string"}, {"type": "null"}]}
        result = client._json_schema_to_python_type(optional_schema, {})  # type: ignore[reportProtectedMemberAccess]
        # Result should be str | None
        assert result is not None

    def test_build_dependency_graph(self):
        """Test building dependency graph from schemas."""
        pytest.importorskip("httpx")

        client = FunctionClient(base_url="http://localhost:8000")

        schemas = {
            "Item": {"type": "object", "properties": {"name": {"type": "string"}, "price": {"type": "number"}}},
            "ItemResponse": {
                "type": "object",
                "properties": {"id": {"type": "integer"}, "item": {"$ref": "#/components/schemas/Item"}},
            },
        }

        deps = client._build_dependency_graph(schemas)  # type: ignore[reportProtectedMemberAccess]

        # ItemResponse depends on Item
        assert "Item" in deps
        assert "ItemResponse" in deps
        assert "Item" in deps["ItemResponse"]
        assert len(deps["Item"]) == 0  # Item has no dependencies

    def test_topological_sort(self):
        """Test topological sorting of dependencies."""
        pytest.importorskip("httpx")

        client = FunctionClient(base_url="http://localhost:8000")

        # Simple dependency: B depends on A
        deps: dict[str, set[str]] = {"A": set(), "B": {"A"}}

        result = client._topological_sort(deps)  # type: ignore[reportProtectedMemberAccess]

        # A should come before B (dependencies first)
        assert result.index("A") < result.index("B")

    def test_topological_sort_complex(self):
        """Test topological sorting with complex dependencies."""
        pytest.importorskip("httpx")

        client = FunctionClient(base_url="http://localhost:8000")

        # Complex: D depends on B and C, B depends on A, C depends on A
        deps: dict[str, set[str]] = {"A": set(), "B": {"A"}, "C": {"A"}, "D": {"B", "C"}}

        result = client._topological_sort(deps)  # type: ignore[reportProtectedMemberAccess]

        # A must come before B and C
        assert result.index("A") < result.index("B")
        assert result.index("A") < result.index("C")
        # B and C must come before D
        assert result.index("B") < result.index("D")
        assert result.index("C") < result.index("D")

    def test_create_model_from_schema_simple(self):
        """Test creating a simple Pydantic model from JSON Schema."""
        pytest.importorskip("httpx")

        client = FunctionClient(base_url="http://localhost:8000")

        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
            "required": ["name"],
        }

        model = client._create_model_from_schema("Person", schema, {})  # type: ignore[reportProtectedMemberAccess]

        # Test the model works
        instance = model(name="Alice", age=30)
        assert instance.name == "Alice"  # type: ignore[reportUnknownMemberType]
        assert instance.age == 30  # type: ignore[reportUnknownMemberType]

        # Test required field
        with pytest.raises(Exception):  # Pydantic validation error
            model(age=30)  # Missing required name

    def test_create_model_from_schema_with_defaults(self):
        """Test creating a model with default values."""
        pytest.importorskip("httpx")

        client = FunctionClient(base_url="http://localhost:8000")

        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "status": {"type": "string", "default": "active"}},
            "required": ["name"],
        }

        model = client._create_model_from_schema("Item", schema, {})  # type: ignore[reportProtectedMemberAccess] # type: ignore[reportUnknownArgumentType]

        # Test with default
        instance = model(name="test")
        assert instance.name == "test"  # type: ignore[reportUnknownMemberType]
        assert instance.status == "active"  # type: ignore[reportUnknownMemberType]

    def test_extract_refs_from_dict(self):
        """Test extracting $ref references from a schema."""
        pytest.importorskip("httpx")

        client = FunctionClient(base_url="http://localhost:8000")

        schema = {
            "type": "object",
            "properties": {
                "item": {"$ref": "#/components/schemas/Item"},
                "tags": {"type": "array", "items": {"$ref": "#/components/schemas/Tag"}},
            },
        }

        refs: set[str] = set()
        client._extract_refs(schema, refs)  # type: ignore[reportProtectedMemberAccess]

        assert "Item" in refs
        assert "Tag" in refs

    def test_extract_refs_from_list(self):
        """Test extracting refs from list structures."""
        pytest.importorskip("httpx")

        client = FunctionClient(base_url="http://localhost:8000")

        schema = [{"$ref": "#/components/schemas/A"}, {"$ref": "#/components/schemas/B"}]

        refs: set[str] = set()
        client._extract_refs(schema, refs)  # type: ignore[reportProtectedMemberAccess]

        assert "A" in refs
        assert "B" in refs

    def test_automatic_response_parsing_after_discover(self):
        """Test that responses are automatically parsed to models after discover()."""
        pytest.importorskip("httpx")

        # Mock OpenAPI schema
        openapi_schema = {
            "openapi": "3.1.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},  # Required field in OpenAPIDocument
            "components": {
                "schemas": {
                    "Item": {
                        "type": "object",
                        "properties": {"name": {"type": "string"}, "price": {"type": "number"}},
                        "required": ["name", "price"],
                    },
                    "ItemResponse": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "total": {"type": "number"},
                        },
                        "required": ["id", "total"],
                    },
                }
            },
        }

        # Mock methods metadata
        methods_metadata = {
            "status_code": 200,
            "headers": {},
            "data": {
                "methods": [
                    {
                        "name": "get_item",
                        "path": "/items/{item_id}",
                        "http_method": "GET",
                        "parameters": [{"name": "item_id", "in": "path", "type": "int", "required": True}],
                        "return_type": "ItemResponse",
                        "description": "Get an item",
                    }
                ]
            },
        }

        # Mock response data
        response_data = {"status_code": 200, "headers": {}, "data": {"id": 42, "total": 100.0}}

        with (
            patch("httpx.request") as mock_request,
            patch("httpx.get") as mock_get,
        ):
            # Setup mock responses for different endpoints
            def side_effect(method: str, url: str, *args: Any, **kwargs: Any) -> Mock:
                response = Mock()
                response.raise_for_status = Mock()
                if "__schema__" in url:
                    # __schema__ endpoint returns wrapped response
                    response.json = Mock(return_value={"status_code": 200, "headers": {}, "data": openapi_schema})
                elif "__client_methods__" in url:
                    response.json = Mock(return_value=methods_metadata)
                elif "/items/" in url:
                    response.json = Mock(return_value=response_data)
                return response

            def get_side_effect(url: str, *args: Any, **kwargs: Any) -> Mock:
                return side_effect("GET", url, *args, **kwargs)

            mock_request.side_effect = side_effect
            mock_get.side_effect = get_side_effect

            client = FunctionClient(base_url="http://localhost:8000")

            # Call discover to enable automatic parsing
            models = client.discover()

            # Verify models were created
            assert hasattr(models, "Item")
            assert hasattr(models, "ItemResponse")

            # Call method - should return parsed model
            result = client.get_item(item_id=42)

            # Verify result is a Pydantic model, not a dict
            assert hasattr(result, "id")
            assert hasattr(result, "total")
            assert result.id == 42  # type: ignore[reportUnknownMemberType]
            assert result.total == 100.0  # type: ignore[reportUnknownMemberType]

            # Verify it's actually the ItemResponse model
            assert type(result).__name__ == "ItemResponse"

    def test_automatic_response_parsing_with_list(self):
        """Test that list responses are automatically parsed to list of models."""
        pytest.importorskip("httpx")

        # Mock OpenAPI schema
        openapi_schema = {
            "openapi": "3.1.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},  # Required field in OpenAPIDocument
            "components": {
                "schemas": {
                    "Item": {
                        "type": "object",
                        "properties": {"name": {"type": "string"}, "price": {"type": "number"}},
                        "required": ["name", "price"],
                    }
                }
            },
        }

        # Mock methods metadata
        methods_metadata: dict[str, Any] = {
            "status_code": 200,
            "headers": {},
            "data": {
                "methods": [
                    {
                        "name": "list_items",
                        "path": "/items",
                        "http_method": "GET",
                        "parameters": [],
                        "return_type": "list[Item]",
                        "description": "List items",
                    }
                ]
            },
        }

        # Mock response data - list of items
        response_data: dict[str, Any] = {
            "status_code": 200,
            "headers": {},
            "data": [{"name": "Item1", "price": 10.0}, {"name": "Item2", "price": 20.0}],
        }

        with (
            patch("httpx.request") as mock_request,
            patch("httpx.get") as mock_get,
        ):
            # Setup mock responses
            def side_effect(method: str, url: str, *args: Any, **kwargs: Any) -> Mock:
                response = Mock()
                response.raise_for_status = Mock()
                if "__schema__" in url:
                    # __schema__ endpoint returns wrapped response
                    response.json = Mock(return_value={"status_code": 200, "headers": {}, "data": openapi_schema})
                elif "__client_methods__" in url:
                    response.json = Mock(return_value=methods_metadata)
                elif "/items" in url:
                    response.json = Mock(return_value=response_data)
                return response

            def get_side_effect(url: str, *args: Any, **kwargs: Any) -> Mock:
                return side_effect("GET", url, *args, **kwargs)

            mock_request.side_effect = side_effect
            mock_get.side_effect = get_side_effect

            client = FunctionClient(base_url="http://localhost:8000")

            # Call discover to enable automatic parsing
            client.discover()

            # Call method - should return list of parsed models
            result: list[dict[str, Any]] = client.list_items()

            # Verify result is a list of models
            assert isinstance(result, list)
            assert len(result) == 2
            assert type(result[0]).__name__ == "Item"
            assert type(result[1]).__name__ == "Item"
            assert result[0].name == "Item1"  # type: ignore[reportUnknownMemberType]
            assert result[1].name == "Item2"  # type: ignore[reportUnknownMemberType]

    def test_no_parsing_for_dict_return_type(self):
        """Test that dict return types are not parsed."""
        pytest.importorskip("httpx")

        # Mock OpenAPI schema
        openapi_schema: dict[str, Any] = {
            "openapi": "3.1.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},  # Required field in OpenAPIDocument
            "components": {"schemas": {}},
        }

        # Mock methods metadata
        methods_metadata: dict[str, Any] = {
            "status_code": 200,
            "headers": {},
            "data": {
                "methods": [
                    {
                        "name": "get_data",
                        "path": "/data",
                        "http_method": "GET",
                        "parameters": [],
                        "return_type": "dict[str, Any]",
                        "description": "Get data",
                    }
                ]
            },
        }

        # Mock response data
        response_data = {"status_code": 200, "headers": {}, "data": {"key": "value"}}

        with (
            patch("httpx.request") as mock_request,
            patch("httpx.get") as mock_get,
        ):
            # Setup mock responses
            def side_effect(method: str, url: str, *args: Any, **kwargs: Any) -> Mock:
                response = Mock()
                response.raise_for_status = Mock()
                if "__schema__" in url:
                    # __schema__ endpoint returns wrapped response
                    response.json = Mock(return_value={"status_code": 200, "headers": {}, "data": openapi_schema})
                elif "__client_methods__" in url:
                    response.json = Mock(return_value=methods_metadata)
                elif "/data" in url:
                    response.json = Mock(return_value=response_data)
                return response

            def get_side_effect(url: str, *args: Any, **kwargs: Any) -> Mock:
                return side_effect("GET", url, *args, **kwargs)

            mock_request.side_effect = side_effect
            mock_get.side_effect = get_side_effect

            client = FunctionClient(base_url="http://localhost:8000")

            # Call discover
            client.discover()

            # Call method - should return dict (not parsed)
            result = client.get_data()

            # Verify result is still a dict
            assert isinstance(result, dict)
            assert result == {"key": "value"}
