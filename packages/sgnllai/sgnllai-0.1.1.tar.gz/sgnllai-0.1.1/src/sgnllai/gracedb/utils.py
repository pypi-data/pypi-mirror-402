"""Shared utilities for GraceDB operations."""

from __future__ import annotations

from typing import Any


def get_nested(d: dict[Any, Any], path: str) -> Any:
    """Get nested dict value using dot notation path.

    Example:
        get_nested({"a": {"b": 1}}, "a.b") -> 1
        get_nested({"a": {"b": 1}}, "a.c") -> None

    Args:
        d: Dictionary to search
        path: Dot-separated path to value (e.g., "g_event.graceid")

    Returns:
        Value at path, or None if path doesn't exist
    """
    value: Any = d
    for key in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(key)
        if value is None:
            return None
    return value
