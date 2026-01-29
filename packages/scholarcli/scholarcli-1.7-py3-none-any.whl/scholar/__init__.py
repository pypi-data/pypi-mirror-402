"""
Scholar package for structured literature searches.
"""

from .scholar import Search, SearchResult, Paper, SearchFilters
from .scholar import search, filter_papers
from .scholar import get_registry, isolated_registry
from .utils import safe_get_nested, ensure_list

__all__ = [
    "Search",
    "SearchResult",
    "Paper",
    "SearchFilters",
    "search",
    "filter_papers",
    "get_registry",
    "isolated_registry",
    "safe_get_nested",
    "ensure_list",
]
