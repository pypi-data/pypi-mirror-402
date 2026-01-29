"""Tests for CLI functionality, especially handler loading with relative imports."""

import sys
from pathlib import Path
from typing import Any, cast
from unittest.mock import Mock

import pytest
import typer
from cognite.client import CogniteClient

from cognite_function_apps.cli import _load_handler_from_path  # pyright: ignore[reportPrivateUsage]
from cognite_function_apps.service import FunctionService


class TestCLIHandlerLoading:
    """Test CLI handler loading with various import scenarios."""

    def test_load_simple_handler(self, tmp_path: Path) -> None:
        """Test loading a simple handler without relative imports."""
        handler_dir = tmp_path / "simple_function"
        handler_dir.mkdir()

        handler_content = '''"""Simple handler without relative imports."""
from cognite_function_apps import FunctionApp, create_function_service

app = FunctionApp(title="Simple", version="1.0.0")

@app.post("/test")
def test_endpoint() -> dict[str, str]:
    """Test endpoint."""
    return {"message": "success"}

handle = create_function_service(app)
'''
        (handler_dir / "handler.py").write_text(handler_content)

        # Add parent to sys.path as the CLI does
        parent_dir = str(tmp_path)
        sys.path.insert(0, parent_dir)
        try:
            handle = _load_handler_from_path(handler_dir)
            assert isinstance(handle, FunctionService)

            # Verify the handler is callable
            mock_client = Mock(spec=CogniteClient)
            result = cast(
                dict[str, Any],
                handle(
                    client=mock_client,
                    data={"path": "/test", "method": "POST", "body": {}},
                ),
            )
            assert result["status_code"] < 400  # Success
            assert result["data"] == {"message": "success"}
        finally:
            # Clean up sys.path
            if parent_dir in sys.path:
                sys.path.remove(parent_dir)
            # Clean up sys.modules
            module_name = f"{handler_dir.name}.handler"
            if module_name in sys.modules:
                del sys.modules[module_name]

    def test_load_handler_with_relative_imports(self, tmp_path: Path) -> None:
        """Test loading a handler that uses relative imports."""
        handler_dir = tmp_path / "complex_function"
        handler_dir.mkdir()

        # Create a utils module that will be imported relatively
        utils_content = '''"""Utils module for testing relative imports."""

def get_greeting(name: str) -> str:
    """Get a greeting message."""
    return f"Hello, {name}!"

def calculate_sum(a: int, b: int) -> int:
    """Calculate sum of two numbers."""
    return a + b
'''
        (handler_dir / "utils.py").write_text(utils_content)

        # Create handler that uses relative import
        handler_content = '''"""Handler with relative imports."""
from cognite_function_apps import FunctionApp, create_function_service
from . import utils

app = FunctionApp(title="Complex", version="1.0.0")

@app.post("/greet")
def greet(name: str) -> dict[str, str]:
    """Greet endpoint using relative import."""
    return {"message": utils.get_greeting(name)}

@app.post("/add")
def add(a: int, b: int) -> dict[str, int]:
    """Add endpoint using relative import."""
    return {"result": utils.calculate_sum(a, b)}

handle = create_function_service(app)
'''
        (handler_dir / "handler.py").write_text(handler_content)

        # Add parent to sys.path as the CLI does
        parent_dir = str(tmp_path)
        sys.path.insert(0, parent_dir)
        try:
            handle = _load_handler_from_path(handler_dir)
            assert isinstance(handle, FunctionService)

            # Test that the handler actually works
            mock_client = Mock(spec=CogniteClient)

            # Test greet endpoint
            greet_result = cast(
                dict[str, Any],
                handle(
                    client=mock_client,
                    data={"path": "/greet", "method": "POST", "body": {"name": "World"}},
                ),
            )
            assert greet_result["status_code"] < 400  # Success
            assert greet_result["data"] == {"message": "Hello, World!"}

            # Test add endpoint
            add_result = cast(
                dict[str, Any],
                handle(
                    client=mock_client,
                    data={"path": "/add", "method": "POST", "body": {"a": 5, "b": 3}},
                ),
            )
            assert add_result["status_code"] < 400  # Success
            assert add_result["data"] == {"result": 8}
        finally:
            # Clean up sys.path
            if sys.path and parent_dir in sys.path:
                sys.path.remove(parent_dir)
            module_name = f"{handler_dir.name}.handler"
            utils_module_name = f"{handler_dir.name}.utils"
            if module_name in sys.modules:
                del sys.modules[module_name]
            if utils_module_name in sys.modules:
                del sys.modules[utils_module_name]

    def test_load_handler_with_nested_relative_imports(self, tmp_path: Path) -> None:
        """Test loading a handler with nested package structure."""
        handler_dir = tmp_path / "nested_function"
        handler_dir.mkdir()

        # Create nested subpackage
        subpackage_dir = handler_dir / "helpers"
        subpackage_dir.mkdir()
        (subpackage_dir / "__init__.py").write_text("")

        # Create helper module
        helper_content = '''"""Helper module in subpackage."""

def format_response(data: str) -> dict[str, str]:
    """Format response."""
    return {"formatted": data.upper()}
'''
        (subpackage_dir / "formatter.py").write_text(helper_content)

        # Create handler that imports from subpackage
        handler_content = '''"""Handler with nested relative imports."""
from cognite_function_apps import FunctionApp, create_function_service
from .helpers.formatter import format_response

app = FunctionApp(title="Nested", version="1.0.0")

@app.post("/format")
def format_text(text: str) -> dict[str, str]:
    """Format endpoint using nested import."""
    return format_response(text)

handle = create_function_service(app)
'''
        (handler_dir / "handler.py").write_text(handler_content)
        (handler_dir / "__init__.py").write_text("")

        # Add parent to sys.path as the CLI does
        parent_dir = str(tmp_path)
        sys.path.insert(0, parent_dir)
        try:
            handle = _load_handler_from_path(handler_dir)
            assert isinstance(handle, FunctionService)

            # Test that the handler works
            mock_client = Mock(spec=CogniteClient)
            result = cast(
                dict[str, Any],
                handle(
                    client=mock_client,
                    data={"path": "/format", "method": "POST", "body": {"text": "hello"}},
                ),
            )
            assert result["status_code"] < 400  # Success
            assert result["data"] == {"formatted": "HELLO"}
        finally:
            # Clean up sys.path
            if sys.path and parent_dir in sys.path:
                sys.path.remove(parent_dir)
            base_module = handler_dir.name
            for module_name in list(sys.modules.keys()):
                if module_name.startswith(f"{base_module}."):
                    del sys.modules[module_name]

    def test_load_handler_missing_file(self, tmp_path: Path) -> None:
        """Test error handling when handler.py doesn't exist."""
        handler_dir = tmp_path / "missing_handler"
        handler_dir.mkdir()

        # Add parent to sys.path as the CLI does
        parent_dir = str(tmp_path)
        sys.path.insert(0, parent_dir)
        try:
            with pytest.raises(typer.Exit) as exc_info:
                _load_handler_from_path(handler_dir)
            assert exc_info.value.exit_code == 1
        finally:
            # Clean up sys.path
            if sys.path and sys.path[0] == parent_dir:
                sys.path.pop(0)

    def test_load_handler_missing_handle_attribute(self, tmp_path: Path) -> None:
        """Test error handling when handler.py doesn't have handle attribute."""
        handler_dir = tmp_path / "no_handle"
        handler_dir.mkdir()

        handler_content = '''"""Handler without handle attribute."""
from cognite_function_apps import FunctionApp

app = FunctionApp(title="NoHandle", version="1.0.0")
# Missing: handle = create_function_service(app)
'''
        (handler_dir / "handler.py").write_text(handler_content)

        # Add parent to sys.path as the CLI does
        parent_dir = str(tmp_path)
        sys.path.insert(0, parent_dir)
        try:
            with pytest.raises(typer.Exit) as exc_info:
                _load_handler_from_path(handler_dir)
            assert exc_info.value.exit_code == 1
        finally:
            # Clean up sys.path
            if sys.path and sys.path[0] == parent_dir:
                sys.path.pop(0)
            # Clean up sys.modules
            module_name = f"{handler_dir.name}.handler"
            if module_name in sys.modules:
                del sys.modules[module_name]
