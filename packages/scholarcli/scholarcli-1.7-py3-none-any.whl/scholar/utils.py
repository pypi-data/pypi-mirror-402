"""
Utility functions for Scholar.

Provides general-purpose helpers for working with nested data structures
and normalizing API responses.
"""

from typing import Any


def safe_get_nested(obj: Any, *keys: str, default: Any = None) -> Any:
    """
    Safely navigate nested dictionaries.

    Traverses a nested dictionary structure following the given keys.
    Returns the default value if any intermediate level is not a dictionary
    or if any key is missing.

    Args:
        obj: The object to navigate (typically a dict).
        *keys: The sequence of keys to follow.
        default: Value to return if navigation fails.

    Returns:
        The value at the nested path, or default if not found.

    Examples:
        >>> data = {"a": {"b": {"c": 42}}}
        >>> safe_get_nested(data, "a", "b", "c")
        42
        >>> safe_get_nested(data, "a", "x", "c", default="missing")
        'missing'
        >>> safe_get_nested(data, "a", "b", "c", "d", default=None)
        None
    """
    for key in keys:
        if not isinstance(obj, dict):
            return default
        obj = obj.get(key, default)
    return obj


def ensure_list(value: Any) -> list:
    """
    Normalize a value to a list for safe iteration.

    Useful when an API inconsistently returns either a single item or a list
    of items. This function ensures you always get a list to iterate over.

    Args:
        value: The value to normalize.

    Returns:
        - If value is a list: returns it unchanged
        - If value is a dict: returns [value]
        - Otherwise: returns [] (empty list)

    Examples:
        >>> ensure_list([1, 2, 3])
        [1, 2, 3]
        >>> ensure_list({"key": "value"})
        [{'key': 'value'}]
        >>> ensure_list("string")
        []
        >>> ensure_list(None)
        []
    """
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [value]
    return []
