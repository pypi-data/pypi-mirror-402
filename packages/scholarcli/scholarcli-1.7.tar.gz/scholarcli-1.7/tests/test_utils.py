"""Tests for the utils module."""
import pytest

from scholar.utils import *


class TestSafeGetNested:
    """Tests for safe_get_nested function."""

    def test_navigates_nested_dict(self):
        """Successfully navigates nested dictionaries."""
        data = {"a": {"b": {"c": 42}}}
        assert safe_get_nested(data, "a", "b", "c") == 42

    def test_returns_default_for_missing_key(self):
        """Returns default when key doesn't exist."""
        data = {"a": {"b": 1}}
        assert safe_get_nested(data, "a", "x", default="missing") == "missing"

    def test_returns_default_for_non_dict(self):
        """Returns default when intermediate value is not a dict."""
        data = {"a": "not a dict"}
        assert safe_get_nested(data, "a", "b", default=None) is None

    def test_returns_default_for_none_input(self):
        """Returns default when input is None."""
        assert safe_get_nested(None, "a", "b", default="fallback") == "fallback"

    def test_empty_keys_returns_object(self):
        """With no keys, returns the object itself."""
        data = {"a": 1}
        assert safe_get_nested(data) == {"a": 1}

    def test_single_key(self):
        """Works with single key."""
        data = {"a": 42}
        assert safe_get_nested(data, "a") == 42

    def test_default_is_none(self):
        """Default value is None when not specified."""
        data = {"a": 1}
        assert safe_get_nested(data, "x") is None
class TestEnsureList:
    """Tests for ensure_list function."""

    def test_list_unchanged(self):
        """Lists are returned as-is."""
        data = [1, 2, 3]
        assert ensure_list(data) == [1, 2, 3]

    def test_empty_list_unchanged(self):
        """Empty lists are returned as-is."""
        assert ensure_list([]) == []

    def test_dict_wrapped(self):
        """Dicts are wrapped in a list."""
        data = {"key": "value"}
        assert ensure_list(data) == [{"key": "value"}]

    def test_string_returns_empty(self):
        """Strings return empty list (not iterated as chars)."""
        assert ensure_list("hello") == []

    def test_none_returns_empty(self):
        """None returns empty list."""
        assert ensure_list(None) == []

    def test_int_returns_empty(self):
        """Integers return empty list."""
        assert ensure_list(42) == []

    def test_nested_list_unchanged(self):
        """Nested lists are returned as-is."""
        data = [[1, 2], [3, 4]]
        assert ensure_list(data) == [[1, 2], [3, 4]]
