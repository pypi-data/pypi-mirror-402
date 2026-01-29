"""Test fixtures using PEP 563 (from __future__ import annotations).

This module uses `from __future__ import annotations` to test that the framework
correctly handles string annotations (deferred evaluation).
"""

from __future__ import annotations

from logging import Logger
from typing import Any

from cognite.client import CogniteClient


def pep563_test_handler(
    client: CogniteClient,
    logger: Logger,
    item_id: int,
    include_details: bool = False,
) -> dict[str, Any]:
    """Test handler with PEP 563 string annotations.

    This handler is defined in a module with `from __future__ import annotations`,
    so all type annotations are stored as strings, not actual type objects.

    Returns information about injected dependencies so tests can verify DI worked.
    """
    return {
        "item_id": item_id,
        "include_details": include_details,
        # Return type names so tests can verify correct types were injected
        "client_type": type(client).__name__,
        "logger_type": type(logger).__name__,
    }
