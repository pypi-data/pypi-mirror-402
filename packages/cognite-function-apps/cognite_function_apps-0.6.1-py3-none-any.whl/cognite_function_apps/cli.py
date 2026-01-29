"""Command-line interface for Function Apps.

This module provides CLI commands for working with Function Apps,
including a development server for local testing.

Note: This module can be safely imported even if CLI dependencies (typer, uvicorn)
are not installed. Dependency checking only occurs when main() is executed.
"""

import importlib.util
import logging
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Annotated

from cognite_function_apps.devserver import create_asgi_app
from cognite_function_apps.service import FunctionService

logger = logging.getLogger(__name__)


def _load_handler_from_path(handler_path: Path) -> FunctionService:
    """Load the handle object from a handler.py file.

    Args:
        handler_path: Path to the directory containing handler.py

    Returns:
        The FunctionService handle object

    Raises:
        RuntimeError: If handler.py is not found or doesn't have a handle attribute
    """
    # Import typer only when needed (will be available when CLI is actually used)
    try:
        import typer  # noqa: PLC0415
    except ImportError:
        # If typer is not available, we can't use the nice colored output
        # but we can still provide the functionality for tests
        typer = None  # type: ignore[assignment]

    handler_file = handler_path / "handler.py"

    if not handler_file.exists():
        msg = f"Error: handler.py not found in {handler_path}\nExpected file: {handler_file}"
        if typer:
            typer.secho(f"Error: handler.py not found in {handler_path}", fg=typer.colors.RED, err=True)
            typer.secho(f"Expected file: {handler_file}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
        raise RuntimeError(msg)

    if not handler_file.is_file():
        msg = f"Error: {handler_file} is not a file"
        if typer:
            typer.secho(msg, fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
        raise RuntimeError(msg)

    # Load the module as a package module to support relative imports
    # Use the directory name as the package name (e.g., "my_function.handler")
    package_name = re.sub(r"\W|^(?=\d)", "_", handler_path.name)
    module_name = f"{package_name}.handler"
    spec = importlib.util.spec_from_file_location(module_name, handler_file)
    if spec is None or spec.loader is None:
        msg = f"Error: Failed to load {handler_file}"
        if typer:
            typer.secho(msg, fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
        raise RuntimeError(msg)

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module

    try:
        spec.loader.exec_module(module)
    except Exception as e:
        msg = f"Error: Failed to execute handler.py: {e}"
        if typer:
            typer.secho(msg, fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
        raise RuntimeError(msg) from e

    # Extract the handle object
    if not hasattr(module, "handle"):
        msg = f"Error: handler.py in {handler_path} does not define a 'handle' attribute"
        if typer:
            typer.secho(msg, fg=typer.colors.RED, err=True)
            typer.secho("\nExpected usage in handler.py:", fg=typer.colors.YELLOW, err=True)
            typer.secho("  from cognite_function_apps import create_function_service", err=True)
            typer.secho("  handle = create_function_service(app)", err=True)
            raise typer.Exit(code=1)
        raise RuntimeError(msg)

    handle = module.handle
    if not isinstance(handle, FunctionService):
        msg = f"Error: 'handle' must be a FunctionService instance, found type: {type(handle).__name__}"
        if typer:
            typer.secho("Error: 'handle' must be a FunctionService instance", fg=typer.colors.RED, err=True)
            typer.secho(f"Found type: {type(handle).__name__}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
        raise RuntimeError(msg)

    return handle


def main() -> None:
    """Main entry point for the CLI.

    Checks for CLI dependencies and runs the Typer app.
    """
    # Check for CLI dependencies only when main() is called
    try:
        import typer  # noqa: PLC0415
        import uvicorn  # noqa: PLC0415
    except ImportError as e:
        logger.error(
            """Error: CLI dependencies not installed. Missing: %s
Install CLI support with: pip install cognite-function-apps[cli]
Or with uv: uv add cognite-function-apps --extra cli""",
            e.name,
        )
        sys.exit(1)

    # Define CLI app and commands
    app = typer.Typer(
        name="fun",
        help="Function Apps CLI - Build and test Cognite Functions locally",
        add_completion=False,
        no_args_is_help=True,
        invoke_without_command=True,
    )

    @app.callback()
    def main_callback(ctx: typer.Context) -> None:
        """Function Apps CLI.

        A command-line interface for working with Function Apps,
        including local development server and testing utilities.
        """
        # If no subcommand is provided, Typer will show help due to no_args_is_help=True
        pass

    def _validate_handler_directory(handler_path: Path) -> None:
        """Validate that the handler directory exists and is valid.

        Args:
            handler_path: Path to the directory containing handler.py

        Raises:
            typer.Exit: If validation fails
        """
        if not handler_path.exists():
            typer.secho(f"Error: Path does not exist: {handler_path}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)

        if not handler_path.is_dir():
            typer.secho(f"Error: Path is not a directory: {handler_path}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)

        # Validate that the directory name is a valid Python module name
        dir_name = handler_path.name
        if not dir_name.isidentifier():
            suggested_name = re.sub(r"\W|^(?=\d)", "_", dir_name)
            typer.secho(
                f"Error: Directory name '{dir_name}' is not a valid Python module name", fg=typer.colors.RED, err=True
            )
            typer.secho("\nDirectory names must:", fg=typer.colors.YELLOW, err=True)
            typer.secho("  - Start with a letter or underscore", err=True)
            typer.secho("  - Contain only letters, numbers, and underscores", err=True)
            typer.secho("  - Not be a Python keyword", err=True)
            typer.secho(f"\nSuggested name: {suggested_name}", fg=typer.colors.GREEN, err=True)
            raise typer.Exit(code=1)

        if dir_name in sys.stdlib_module_names:
            typer.secho(
                f"Error: Directory name '{dir_name}' shadows a standard library module.", fg=typer.colors.RED, err=True
            )
            typer.secho("Please rename the directory to avoid import conflicts.", fg=typer.colors.YELLOW, err=True)
            raise typer.Exit(code=1)

    def _create_temp_reload_app(handler_path: Path) -> tuple[str, Path]:
        """Create a temporary ASGI app file for reload support.

        Args:
            handler_path: Path to the directory containing handler.py

        Returns:
            Tuple of (temp_dir, temp_app_file)
        """
        temp_dir = tempfile.mkdtemp(prefix="fun_serve_")
        temp_app_file = Path(temp_dir) / "_fun_asgi_app.py"

        # Get the package root and name to support relative imports in user code
        package_root = handler_path.parent
        package_name = re.sub(r"\W|^(?=\d)", "_", handler_path.name)

        # Write a Python file that imports and creates the ASGI app
        # The handler is imported as a package module (e.g., "my_function.handler")
        # to enable relative imports within the handler code
        temp_app_content = f'''"""Temporary ASGI app for fun serve with reload support."""
import sys
from pathlib import Path
import importlib

# Add package root to path to allow relative imports in handler
package_root = Path({str(package_root)!r})
if str(package_root) not in sys.path:
    sys.path.insert(0, str(package_root))

# Import and create the app
from cognite_function_apps.devserver import create_asgi_app

# Import the handler module as a package module
handler_module = importlib.import_module("{package_name}.handler")

# Create the ASGI app
app = create_asgi_app(handler_module.handle)
'''
        temp_app_file.write_text(temp_app_content)
        return temp_dir, temp_app_file

    def _run_server_with_reload(handler_path: Path, host: str, port: int, log_level: str) -> None:
        """Run the development server with auto-reload enabled.

        Args:
            handler_path: Path to the directory containing handler.py
            host: Host to bind to
            port: Port to bind to
            log_level: Log level for uvicorn
        """
        # For reload to work, we need to create a temporary Python file that uvicorn can import
        # This file will be re-imported on each reload
        temp_dir, _temp_app_file = _create_temp_reload_app(handler_path)

        # Add temp directory to Python path so it can be imported
        # Track whether we added it to avoid removing it if it was already present
        temp_dir_added = temp_dir not in sys.path
        if temp_dir_added:
            sys.path.insert(0, temp_dir)

        try:
            # Use import string for reload support
            uvicorn.run(
                "_fun_asgi_app:app",
                host=host,
                port=port,
                reload=True,
                reload_dirs=[str(handler_path)],
                log_level=log_level,
            )
        finally:
            # Clean up temp directory from sys.path only if we added it
            if temp_dir_added and temp_dir in sys.path:
                sys.path.remove(temp_dir)
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _run_server_without_reload(handler_path: Path, host: str, port: int, log_level: str) -> None:
        """Run the development server without auto-reload.

        Args:
            handler_path: Path to the directory containing handler.py
            host: Host to bind to
            port: Port to bind to
            log_level: Log level for uvicorn
        """
        # When reload is disabled, we can load and create the app directly
        # Add the parent directory to sys.path to support relative imports
        # Track whether we added it to avoid removing it if it was already present
        package_root = str(handler_path.parent)
        package_root_added = package_root not in sys.path
        if package_root_added:
            sys.path.insert(0, package_root)

        try:
            typer.secho(f"Loading handler from {handler_path}/handler.py...", fg=typer.colors.BLUE)
            handle = _load_handler_from_path(handler_path)
            typer.secho("✓ Handler loaded successfully", fg=typer.colors.GREEN)

            typer.secho("Creating ASGI app...", fg=typer.colors.BLUE)
            asgi_app = create_asgi_app(handle)
            typer.secho("✓ ASGI app created", fg=typer.colors.GREEN)

            # Pass app directly when reload is disabled
            uvicorn.run(
                asgi_app,
                host=host,
                port=port,
                reload=False,
                log_level=log_level,
            )
        finally:
            # Restore sys.path only if we added it
            if package_root_added and package_root in sys.path:
                sys.path.remove(package_root)

    @app.command()
    def serve(
        path: Annotated[Path, typer.Argument(help="Path to the directory containing handler.py")],
        host: Annotated[str, typer.Option(help="Host to bind to")] = "127.0.0.1",
        port: Annotated[int, typer.Option(help="Port to bind to")] = 8000,
        reload: Annotated[bool, typer.Option(help="Enable auto-reload on code changes")] = True,
        log_level: Annotated[
            str,
            typer.Option(help="Log level"),
        ] = "info",
    ) -> None:
        """Start a development server for local testing.

        This command loads your handler.py file and starts a local development server
        using uvicorn. It automatically detects code changes and reloads the server.

        Example:
            fun serve examples/
            fun serve . --port 3000 --log-level debug
        """
        handler_path = path.resolve()
        _validate_handler_directory(handler_path)

        # Print startup information
        typer.secho(f"\nStarting server at http://{host}:{port}", fg=typer.colors.GREEN, bold=True)
        if reload:
            typer.secho("Auto-reload enabled - watching for changes...", fg=typer.colors.YELLOW)
        typer.secho("Press CTRL+C to quit\n", fg=typer.colors.YELLOW)

        if reload:
            _run_server_with_reload(handler_path, host, port, log_level)
        else:
            _run_server_without_reload(handler_path, host, port, log_level)

    # Run the CLI app
    app()


if __name__ == "__main__":
    main()
