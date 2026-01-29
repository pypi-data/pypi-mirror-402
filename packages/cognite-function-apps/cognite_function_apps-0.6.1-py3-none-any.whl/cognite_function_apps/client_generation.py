"""Client generation for Function Apps.

This module provides functionality to generate production-ready typed Python clients
from function metadata. It discovers all Pydantic models used in routes, extracts their
source code using inspect.getsource(), and generates complete executable clients.

The generated clients are self-contained and include:
- Complete Pydantic model definitions with all validators and Field constraints
- Type-safe client methods for each route
- Proper imports for standard library types
- Full docstrings and type hints

Key Features:
    - Recursive model discovery: Finds all dependent models across fields
    - Source code extraction: Uses inspect.getsource() to preserve complete model definitions
    - Complete validation: Preserves all validators, Field constraints, and custom logic
    - Self-contained output: Generated clients need no manual imports
    - Production-ready: Full type safety for deployed code

Design Rationale:
    This module uses inspect.getsource() rather than OpenAPI schemas because:
    - OpenAPI cannot represent Python-specific features (validators, computed fields)
    - Users expect production clients to have complete model functionality
    - The FunctionClient.discover() method uses OpenAPI for fast exploration
    - The FunctionClient.materialize() method uses this module for production code

    This two-tier approach provides the best of both worlds:
    - Fast, simplified models for notebook exploration (discover)
    - Complete, production-ready models for deployed code (materialize)
"""

import inspect
import re
import warnings
from collections.abc import Callable, Mapping, Sequence
from typing import Any, get_args, get_origin, get_type_hints

from pydantic import BaseModel

from .dependency_registry import DependencyRegistry, create_default_registry
from .models import HTTPMethod, Response
from .routing import RouteInfo


def _unwrap_response_type(return_type: Any) -> Any:
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


# Standard library types that need imports
STDLIB_IMPORTS: dict[str, str] = {
    "datetime": "from datetime import datetime, date, time, timedelta",
    "date": "from datetime import datetime, date, time, timedelta",
    "time": "from datetime import datetime, date, time, timedelta",
    "timedelta": "from datetime import datetime, date, time, timedelta",
    "Decimal": "from decimal import Decimal",
    "UUID": "from uuid import UUID",
    "Path": "from pathlib import Path",
    "Mapping": "from collections.abc import Mapping, Sequence",
    "Sequence": "from collections.abc import Mapping, Sequence",
}


def generate_client_methods_metadata(
    routes: Mapping[str, Mapping[HTTPMethod, Sequence[RouteInfo]]],
    registry: DependencyRegistry | None = None,
) -> dict[str, Any]:
    """Generate metadata for dynamic client method calling and code generation.

    This generates complete metadata including method signatures, Pydantic models,
    and all information needed for client-side code generation.

    Args:
        routes: All routes in the application (supports multiple routes per path/method)
        registry: Dependency registry for filtering parameters (optional)

    Returns:
        Dictionary with 'methods' and 'models' keys containing all metadata
    """
    if registry is None:
        registry = create_default_registry()

    methods: list[dict[str, Any]] = []

    for route_path, route_methods in sorted(routes.items()):
        for http_method, route_infos in route_methods.items():
            # For content negotiation routes, use the first (primary) route for metadata
            if not route_infos:
                continue
            route_info = route_infos[0]
            # Get the actual function name
            function_name = route_info.endpoint.__name__

            # Filter out injected dependencies (pass type_hints for PEP 563/649 compatibility)
            type_hints = route_info.type_hints
            user_params = _filter_injected_params(list(route_info.signature.parameters.values()), registry, type_hints)

            # Build parameter information
            parameters: list[dict[str, Any]] = []
            for param in user_params:
                param_info: dict[str, Any] = {
                    "name": param.name,
                    "required": param.default == inspect.Parameter.empty,
                }

                # Add type information (use resolved type_hints for PEP 563/649 compatibility)
                resolved_type = type_hints.get(param.name, param.annotation)
                if resolved_type != inspect.Parameter.empty:
                    param_info["type"] = _format_type_annotation(resolved_type)

                # Add default value if present
                if param.default != inspect.Parameter.empty:
                    if isinstance(param.default, str):
                        param_info["default"] = f'"{param.default}"'
                    elif param.default is None:
                        param_info["default"] = "None"
                    else:
                        param_info["default"] = str(param.default)

                # Determine parameter location (path, query, or body)
                if param.name in route_info.path_params:
                    param_info["in"] = "path"
                elif http_method in (HTTPMethod.POST, HTTPMethod.PUT):
                    # Check if it's a Pydantic model (body parameter)
                    # Use resolved_type for PEP 563/649 compatibility
                    try:
                        if inspect.isclass(resolved_type) and issubclass(resolved_type, BaseModel):
                            param_info["in"] = "body"
                        else:
                            param_info["in"] = "body"
                    except TypeError:
                        param_info["in"] = "body"
                else:
                    param_info["in"] = "query"

                parameters.append(param_info)

            # Get return type information (unwrap Response[T] to get actual return type)
            return_type = "Any"
            if route_info.signature.return_annotation != inspect.Signature.empty:
                unwrapped_type = _unwrap_response_type(route_info.signature.return_annotation)
                return_type = _format_type_annotation(unwrapped_type)

            # Build method metadata
            method_metadata = {
                "name": function_name,
                "path": route_path,
                "http_method": str(http_method),
                "parameters": parameters,
                "description": route_info.description,
                "return_type": return_type,
                "path_params": list(route_info.path_params),
            }

            methods.append(method_metadata)

    # Discover all Pydantic models used in routes
    all_models = discover_all_models_from_routes(routes)
    _, imports = _collect_model_sources_and_imports(all_models)

    # Also check method return types and parameter types for needed imports
    for method_metadata in methods:
        _track_imports_from_type_string(method_metadata["return_type"], imports)
        for param in method_metadata["parameters"]:
            if "type" in param:
                _track_imports_from_type_string(param["type"], imports)

    # Build model metadata
    models_metadata: list[dict[str, str]] = []
    sorted_models = _topological_sort_models(all_models)
    for model in sorted_models:
        try:
            source = inspect.getsource(model)
            models_metadata.append(
                {
                    "name": model.__name__,
                    "source": source,
                }
            )
        except (OSError, TypeError):
            # Skip dynamically generated models
            pass

    return {
        "methods": methods,
        "models": models_metadata,
        "imports": sorted(imports),
    }


def discover_all_models_from_routes(
    routes: Mapping[str, Mapping[HTTPMethod, Sequence[RouteInfo]]],
) -> set[type[BaseModel]]:
    """Discover all Pydantic models used across all routes.

    Args:
        routes: Dictionary mapping route paths to their HTTP methods and route info

    Returns:
        Set of all unique Pydantic model classes found
    """
    all_models: set[type[BaseModel]] = set()

    for methods in routes.values():
        for route_infos in methods.values():
            for route_info in route_infos:
                models = _discover_models_from_handler(route_info.endpoint)
                all_models.update(models)

    return all_models


def _discover_models_from_handler(handler: Callable[..., Any]) -> set[type[BaseModel]]:
    """Recursively discover all models used by a handler, including nested dependencies.

    Args:
        handler: The route handler function to analyze

    Returns:
        Set of all Pydantic models used by this handler
    """
    discovered: set[type[BaseModel]] = set()
    to_process: list[type[BaseModel]] = []

    # Step 1: Get models from handler signature (parameters and return type)
    try:
        hints = get_type_hints(handler)
        for hint in hints.values():
            to_process.extend(_extract_models_from_type(hint))
    except (TypeError, NameError) as e:
        warnings.warn(f"Could not resolve type hints for handler {handler.__name__}: {e}", UserWarning, stacklevel=2)
        pass

    # Step 2: Recursively process model fields to find nested models
    while to_process:
        model = to_process.pop()
        if model in discovered:
            continue  # Already processed (handles circular references)

        discovered.add(model)

        # Step 3: Inspect each field's type annotation for more models
        try:
            for field_info in model.model_fields.values():
                to_process.extend(_extract_models_from_type(field_info.annotation))
        except NameError as e:
            warnings.warn(
                f"Failed to resolve type annotation in model {model.__name__}: {e}. "
                f"This may be due to forward references or missing imports.",
                UserWarning,
                stacklevel=2,
            )
        except AttributeError as e:
            warnings.warn(
                f"Failed to inspect fields of model {model.__name__}: {e}",
                UserWarning,
                stacklevel=2,
            )
        except Exception as e:
            warnings.warn(
                f"Unexpected error while inspecting model {model.__name__}: {type(e).__name__}: {e}",
                UserWarning,
                stacklevel=2,
            )

    return discovered


def _extract_models_from_type(type_hint: Any) -> list[type[BaseModel]]:
    """Extract BaseModel classes from a type hint (handles Optional, list, dict, etc.).

    Args:
        type_hint: A type annotation that might contain Pydantic models

    Returns:
        List of Pydantic model classes found in the type hint
    """
    models: list[type[BaseModel]] = []

    # Direct BaseModel subclass
    try:
        if inspect.isclass(type_hint) and issubclass(type_hint, BaseModel):
            models.append(type_hint)
            return models
    except TypeError:
        # issubclass can raise TypeError for non-class types
        pass

    # Generic types: Optional[Item], list[Item], dict[str, Item], etc.
    if hasattr(type_hint, "__args__"):
        args = getattr(type_hint, "__args__", ())
        for arg in args:
            models.extend(_extract_models_from_type(arg))

    return models


def _topological_sort_models(models: set[type[BaseModel]]) -> list[type[BaseModel]]:
    """Sort models topologically so dependencies come before dependents.

    Args:
        models: Set of Pydantic model classes

    Returns:
        List of models in dependency order
    """
    # Build dependency graph: model -> set of models that depend on it
    dependents: dict[type[BaseModel], set[type[BaseModel]]] = {model: set() for model in models}
    dependencies: dict[type[BaseModel], set[type[BaseModel]]] = {}

    for model in models:
        deps: set[type[BaseModel]] = set()
        try:
            # Get type hints for all fields
            hints = get_type_hints(model)
            for hint in hints.values():
                # Extract any Pydantic models from this type hint
                for dep_model in _extract_models_from_type(hint):
                    if dep_model in models and dep_model != model:
                        deps.add(dep_model)
                        # Build reverse graph: dep_model -> model (dep_model is needed by model)
                        dependents[dep_model].add(model)
        except NameError as e:
            warnings.warn(
                f"Failed to resolve type hints for model {model.__name__}: {e}. "
                f"This may be due to forward references or missing imports. "
                f"Dependencies for this model will be incomplete.",
                UserWarning,
                stacklevel=2,
            )
        except AttributeError as e:
            warnings.warn(
                f"Failed to get type hints for model {model.__name__}: {e}. "
                f"Dependencies for this model will be incomplete.",
                UserWarning,
                stacklevel=2,
            )
        except (NameError, AttributeError, TypeError) as e:
            warnings.warn(
                f"Unexpected error while analyzing dependencies for model {model.__name__}: "
                f"{type(e).__name__}: {e}. Dependencies for this model will be incomplete.",
                UserWarning,
                stacklevel=2,
            )
        dependencies[model] = deps

    # Topological sort using Kahn's algorithm
    sorted_models: list[type[BaseModel]] = []
    in_degree: dict[type[BaseModel], int] = {model: len(dependencies[model]) for model in models}

    # Start with models that have no dependencies
    queue: list[type[BaseModel]] = [model for model in models if in_degree[model] == 0]

    while queue:
        model = queue.pop(0)
        sorted_models.append(model)

        # For each model that depends on this one, reduce its in-degree
        for dependent in dependents[model]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    if len(sorted_models) != len(models):
        unresolved = {m.__name__ for m in models if m not in sorted_models}
        raise RuntimeError(
            f"Circular dependencies detected or missing model definition. Unresolved models: {unresolved}"
        )

    return sorted_models


def _collect_model_sources_and_imports(models: set[type[BaseModel]]) -> tuple[list[str], set[str]]:
    """Extract source code and collect necessary imports for all models.

    Args:
        models: Set of Pydantic model classes to process

    Returns:
        Tuple of (model_sources, standard_lib_imports)
    """
    sources: list[str] = []
    imports: set[str] = set()

    # Always need pydantic imports
    pydantic_imports: set[str] = set()

    # Sort models topologically
    sorted_models = _topological_sort_models(models)

    for model in sorted_models:
        try:
            # Get source code - this preserves everything
            source = inspect.getsource(model)
            sources.append(source)

            # Check for Pydantic-specific imports in the source
            if "Field(" in source:
                pydantic_imports.add("Field")

            if "@validator" in source:
                pydantic_imports.add("validator")

            if "@field_validator" in source:
                pydantic_imports.add("field_validator")

            # Check for standard library types in the source
            for type_name, import_stmt in STDLIB_IMPORTS.items():
                if type_name in source:
                    imports.add(import_stmt)

        except (OSError, TypeError):
            # Model might be dynamically generated - skip it
            pass

    # Add pydantic imports
    if pydantic_imports:
        pydantic_imports.add("BaseModel")
        imports.add(f"from pydantic import {', '.join(sorted(pydantic_imports))}")
    else:
        imports.add("from pydantic import BaseModel")

    return sources, imports


def _track_imports_from_type_string(type_str: str, imports: set[str]) -> None:
    """Track imports needed for a type string and add them to the imports set.

    Args:
        type_str: String representation of a type (e.g., "Mapping", "list[Item]")
        imports: Set of import statements to update
    """
    for type_name, import_stmt in STDLIB_IMPORTS.items():
        # Check if the type name appears in the type string
        # Use word boundaries to avoid false positives (e.g., "MyMapping" shouldn't trigger "Mapping")
        if re.search(rf"\b{type_name}\b", type_str):
            imports.add(import_stmt)


def _format_type_annotation(annotation: Any) -> str:
    """Format a type annotation as a string for code generation.

    Handles generic types, unions, and Pydantic models.

    Args:
        annotation: Type annotation to format

    Returns:
        String representation suitable for code generation
    """
    if annotation == inspect.Parameter.empty or annotation == inspect.Signature.empty:
        return "Any"

    # Check if it's a generic type with arguments first (e.g., list[Item], Mapping[str, Any])
    if hasattr(annotation, "__args__") and hasattr(annotation, "__origin__"):
        origin = annotation.__origin__
        args = annotation.__args__

        # Get the origin name
        if hasattr(origin, "__name__"):
            origin_name = origin.__name__
        else:
            origin_name = str(origin)

        # Format the arguments recursively
        formatted_args = [_format_type_annotation(arg) for arg in args]
        return f"{origin_name}[{', '.join(formatted_args)}]"

    # Handle simple types with __name__ (non-generic)
    if hasattr(annotation, "__name__"):
        name = annotation.__name__
        # Convert bare dict/list/Mapping/Sequence to generic versions
        match name:
            case "dict":
                return "dict[str, Any]"
            case "list":
                return "list[Any]"
            case "Mapping":
                return "Mapping[str, Any]"
            case "Sequence":
                return "Sequence[Any]"
            case _:
                return name

    # Convert to string and clean up
    type_str = str(annotation)

    # Clean up type string
    # Replace typing module prefixes
    type_str = type_str.replace("typing.", "")
    type_str = type_str.replace("collections.abc.", "")
    type_str = type_str.replace("<class '", "").replace("'>", "")

    return type_str


def _filter_injected_params(
    params: Sequence[inspect.Parameter],
    registry: DependencyRegistry | None,
    type_hints: Mapping[str, Any] | None = None,
) -> list[inspect.Parameter]:
    """Filter out dependency-injected parameters from a function signature.

    Args:
        params: List of function parameters
        registry: Dependency registry to check for injected dependencies (optional)
        type_hints: Optional mapping of parameter names to resolved type annotations
            (from get_type_hints). If provided, these are used instead of param.annotation.
            This handles PEP 563/649 where annotations may be strings or deferred.

    Returns:
        List of parameters that should be exposed in the client API
    """
    # Use default registry if none provided
    if registry is None:
        registry = create_default_registry()

    return [p for p in params if not registry.is_dependency(p.name, p, type_hints.get(p.name) if type_hints else None)]
