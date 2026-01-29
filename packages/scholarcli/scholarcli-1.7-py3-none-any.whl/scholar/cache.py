"""
Cache management for Scholar search providers.

Provides persistent caching of search results to avoid redundant API calls.
Cache is stored as pickled dictionaries, one per provider.
"""

import os
from pathlib import Path
import platformdirs
import logging

logger = logging.getLogger(__name__)
import pickle
from typing import Any
import atexit

# Registry of caches to save on exit: provider_name -> cache dict
CACHE_REGISTRY: dict[str, dict[Any, Any]] = {}


def get_cache_dir() -> Path:
    """
    Return the platform-appropriate cache directory for Scholar.

    The directory is created if it doesn't exist.
    Can be overridden with SCHOLAR_CACHE_DIR environment variable.
    """
    cache_dir = os.environ.get("SCHOLAR_CACHE_DIR")
    if cache_dir:
        path = Path(cache_dir)
    else:
        path = Path(platformdirs.user_cache_dir("scholar"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_cache(provider_name: str) -> dict[Any, Any]:
    """
    Load the cache for a provider from disk.

    Returns an empty dictionary if no cache exists or if loading fails.
    """
    cache_file = get_cache_dir() / f"{provider_name}.pkl"
    if not cache_file.exists():
        logger.debug(f"No cache file found for {provider_name}")
        return {}
    try:
        with open(cache_file, "rb") as f:
            cache = pickle.load(f)
            logger.debug(
                f"Loaded cache for {provider_name}: {len(cache)} entries"
            )
            return cache
    except (pickle.PickleError, EOFError, OSError) as e:
        logger.warning(f"Failed to load cache for {provider_name}: {e}")
        return {}


def save_cache(provider_name: str, cache: dict[Any, Any]) -> None:
    """
    Save the cache for a provider to disk.
    """
    cache_file = get_cache_dir() / f"{provider_name}.pkl"
    try:
        with open(cache_file, "wb") as f:
            pickle.dump(cache, f)
        logger.debug(f"Saved cache for {provider_name}: {len(cache)} entries")
    except OSError as e:
        logger.warning(f"Failed to save cache for {provider_name}: {e}")


def clear_cache() -> int:
    """
    Clear all cached search results.

    Returns the number of cache files deleted.
    """
    cache_dir = get_cache_dir()
    count = 0
    logger.info("Clearing all cache files")
    for cache_file in cache_dir.glob("*.pkl"):
        try:
            cache_file.unlink()
            count += 1
            logger.debug(f"Deleted cache file: {cache_file.name}")
        except OSError as e:
            logger.warning(f"Failed to delete {cache_file.name}: {e}")
    logger.info(f"Cleared {count} cache file(s)")
    return count


def get_cache_stats() -> dict[str, Any]:
    """
    Return statistics about the cache.

    Returns a dictionary with:
    - cache_dir: Path to the cache directory
    - providers: Dict mapping provider names to entry counts
    - total_entries: Total number of cached queries
    - total_size_bytes: Total size of cache files
    """
    cache_dir = get_cache_dir()
    providers: dict[str, int] = {}
    total_size = 0

    for cache_file in cache_dir.glob("*.pkl"):
        provider_name = cache_file.stem
        total_size += cache_file.stat().st_size
        try:
            cache = load_cache(provider_name)
            providers[provider_name] = len(cache)
        except Exception:
            providers[provider_name] = 0

    return {
        "cache_dir": str(cache_dir),
        "providers": providers,
        "total_entries": sum(providers.values()),
        "total_size_bytes": total_size,
    }


def register_cache(provider_name: str, cache: dict[Any, Any]) -> None:
    """
    Register a cache for automatic persistence on exit.
    """
    CACHE_REGISTRY[provider_name] = cache


def save_all_caches() -> None:
    """
    Save all registered caches to disk.

    Called automatically on program exit.
    """
    for provider_name, cache in CACHE_REGISTRY.items():
        save_cache(provider_name, cache)


atexit.register(save_all_caches)
