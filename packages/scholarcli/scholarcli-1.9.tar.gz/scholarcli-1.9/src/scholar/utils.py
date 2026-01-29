"""
Utility functions for Scholar.

Provides general-purpose helpers for working with nested data structures
and normalizing API responses.
"""

from typing import Any
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class LLMModelSelection:
    """Model selection policy for task-specific LLM calls.

    Scholar uses Simon Willison's [[llm]] package, where users may configure a
    global default model. For Scholar's workflow it is often useful to use a
    stronger model for analytic steps (classification, query generation) and a
    cheaper model for writing steps (long-form synthesis).

    [[base]] corresponds to the CLI [[-m/--model]] option.
    [[analytic]] and [[writing]] are optional overrides.

    When a field is [[None]], Scholar falls back to the next available choice:
    task override → base → llm default.
    """

    base: str | None
    analytic: str | None
    writing: str | None


LLMTask = Literal["analytic", "writing"]


def select_model_id(
    selection: LLMModelSelection,
    task: LLMTask,
) -> str | None:
    """Return the model id for a given task.

    Args:
        selection: The user-provided model selection.
        task: Which kind of LLM task to run.

    Returns:
        Model id to pass to [[llm.get_model()]], or [[None]] to use llm's default.
    """

    if task == "analytic" and selection.analytic:
        return selection.analytic
    if task == "writing" and selection.writing:
        return selection.writing
    return selection.base


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
