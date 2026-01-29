"""Tests for the cache module."""
import os
import pytest
from pathlib import Path
from unittest.mock import patch

from scholar.cache import *
from scholar import *


class TestGetCacheDir:
    """Tests for get_cache_dir function."""

    def test_creates_directory(self, tmp_path, monkeypatch):
        """Cache directory is created if it doesn't exist."""
        cache_dir = tmp_path / "scholar_cache"
        monkeypatch.setenv("SCHOLAR_CACHE_DIR", str(cache_dir))
        result = get_cache_dir()
        assert result == cache_dir
        assert cache_dir.exists()

    def test_respects_environment_variable(self, tmp_path, monkeypatch):
        """SCHOLAR_CACHE_DIR overrides default location."""
        custom_dir = tmp_path / "custom"
        monkeypatch.setenv("SCHOLAR_CACHE_DIR", str(custom_dir))
        result = get_cache_dir()
        assert result == custom_dir
class TestLoadSaveCache:
    """Tests for load_cache and save_cache functions."""

    def test_load_nonexistent_returns_empty(self, tmp_path, monkeypatch):
        """Loading a nonexistent cache returns empty dict."""
        monkeypatch.setenv("SCHOLAR_CACHE_DIR", str(tmp_path))
        result = load_cache("nonexistent")
        assert result == {}

    def test_save_and_load_roundtrip(self, tmp_path, monkeypatch):
        """Saved cache can be loaded back."""
        monkeypatch.setenv("SCHOLAR_CACHE_DIR", str(tmp_path))
        cache = {
            ("query1", 100): [Paper(title="Test", authors=["A"])],
            ("query2", 50): [],
        }
        save_cache("test_provider", cache)
        loaded = load_cache("test_provider")
        assert loaded == cache

    def test_load_corrupted_returns_empty(self, tmp_path, monkeypatch):
        """Loading a corrupted cache file returns empty dict."""
        monkeypatch.setenv("SCHOLAR_CACHE_DIR", str(tmp_path))
        cache_file = tmp_path / "corrupted.pkl"
        cache_file.write_bytes(b"not valid pickle data")
        result = load_cache("corrupted")
        assert result == {}
class TestCacheManagement:
    """Tests for cache management functions."""

    def test_clear_cache(self, tmp_path, monkeypatch):
        """clear_cache removes all cache files."""
        monkeypatch.setenv("SCHOLAR_CACHE_DIR", str(tmp_path))
        # Create some cache files
        save_cache("provider1", {"key": "value"})
        save_cache("provider2", {"key": "value"})
        assert len(list(tmp_path.glob("*.pkl"))) == 2
        # Clear them
        count = clear_cache()
        assert count == 2
        assert len(list(tmp_path.glob("*.pkl"))) == 0

    def test_get_cache_stats(self, tmp_path, monkeypatch):
        """get_cache_stats returns accurate information."""
        monkeypatch.setenv("SCHOLAR_CACHE_DIR", str(tmp_path))
        save_cache("provider1", {("q1", 100): [], ("q2", 50): []})
        save_cache("provider2", {("q3", 100): []})
        stats = get_cache_stats()
        assert stats["cache_dir"] == str(tmp_path)
        assert stats["providers"]["provider1"] == 2
        assert stats["providers"]["provider2"] == 1
        assert stats["total_entries"] == 3
        assert stats["total_size_bytes"] > 0
class TestAutoPersistence:
    """Tests for automatic cache persistence."""

    def test_register_and_save_all(self, tmp_path, monkeypatch):
        """Registered caches are saved on save_all_caches."""
        monkeypatch.setenv("SCHOLAR_CACHE_DIR", str(tmp_path))
        # Clear any existing registrations
        CACHE_REGISTRY.clear()
        # Register a cache
        cache = {("query", 100): [Paper(title="Test", authors=["A"])]}
        register_cache("test_provider", cache)
        # Save all caches
        save_all_caches()
        # Verify it was saved
        loaded = load_cache("test_provider")
        assert loaded == cache
        # Clean up
        CACHE_REGISTRY.clear()
