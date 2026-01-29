"""
Scholar: A tool for structured literature searches.

Provides a unified interface for searching bibliographic databases
and generating reproducible search reports.
"""

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import logging

logger = logging.getLogger(__name__)
VERSION = "0.1.0"


class PaperRegistry:
    """
    Central registry ensuring each unique paper exists as a single object.

    Papers are keyed by their stable identifier (DOI or title+author hash).
    When deserializing or creating papers, use get_or_create() to either
    retrieve an existing paper or register a new one.
    """

    def __init__(self):
        self._papers: dict[str, "Paper"] = {}

    def get(self, paper_id: str) -> "Paper | None":
        """
        Retrieve a paper by its stable identifier.

        Args:
            paper_id: The paper's stable ID (from Paper.id property).

        Returns:
            The Paper if found, None otherwise.
        """
        return self._papers.get(paper_id)

    def register(self, paper: "Paper") -> "Paper":
        """
        Register a paper in the registry.

        If a paper with the same ID already exists, returns the existing paper
        (the new paper is discarded). Otherwise, adds the paper to the registry.

        Args:
            paper: The Paper to register.

        Returns:
            The registered paper (may be different from input if duplicate).
        """
        paper_id = paper.id
        if paper_id in self._papers:
            return self._papers[paper_id]
        self._papers[paper_id] = paper
        return paper

    def get_or_create(self, data: dict) -> "Paper":
        """
        Get an existing paper or create and register a new one.

        This is the primary interface for obtaining Paper objects. It ensures
        that papers with the same identity (DOI or title+author) are represented
        by a single object.

        Args:
            data: Dictionary with paper fields (as from Paper.to_dict()).

        Returns:
            Either an existing Paper from the registry, or a newly created
            and registered Paper.
        """
        # Create a temporary paper to compute its ID
        paper = Paper._from_dict_without_registry(data)
        paper_id = paper.id

        if paper_id in self._papers:
            existing = self._papers[paper_id]
            # Optionally merge new data into existing paper
            # For now, just return existing
            return existing

        self._papers[paper_id] = paper
        return paper

    def __len__(self) -> int:
        """Return the number of papers in the registry."""
        return len(self._papers)

    def __contains__(self, paper: "Paper") -> bool:
        """Check if a paper is in the registry."""
        return paper.id in self._papers

    def clear(self) -> None:
        """Remove all papers from the registry."""
        self._papers.clear()

    def all_papers(self) -> list["Paper"]:
        """Return all papers in the registry."""
        return list(self._papers.values())


@dataclass
class Paper:
    """Represents a paper from a bibliographic database."""

    title: str
    authors: list[str]
    year: int | None = None
    doi: str | None = None
    abstract: str | None = None
    venue: str | None = None
    url: str | None = None
    pdf_url: str | None = None
    citation_count: int | None = None
    sources: list[str] = field(default_factory=list)
    references: list["Paper"] | None = None
    citations: list["Paper"] | None = None

    @property
    def id(self) -> str:
        """
        Generate a stable identifier for this paper.

        Uses DOI if available, otherwise SHA256 hash of normalized
        title + first author's last name.

        Returns:
            A string identifier unique to this paper's identity.
        """
        if self.doi:
            return f"doi:{self.doi.lower()}"

        # Normalize title
        title_normalized = self.title.lower().strip()

        # Get first author's last name if available
        author_part = ""
        if self.authors:
            first_author = self.authors[0]
            # Extract last name (last word of author name)
            last_name = (
                first_author.split()[-1].lower() if first_author else ""
            )
            author_part = last_name

        # Create hash
        content = f"{title_normalized}|{author_part}"
        hash_value = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"hash:{hash_value}"

    def __eq__(self, other: object) -> bool:
        """
        Check equality based on stable paper identity.

        Two papers are equal if they have the same DOI (case-insensitive),
        or if they have the same normalized title and first author's last name.
        """
        if not isinstance(other, Paper):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on stable paper identity."""
        return hash(self.id)

    def to_dict(self, include_refs_cites: bool = False) -> dict:
        """
        Convert paper to a dictionary for serialization.

        Args:
            include_refs_cites: If True, include references and citations
                (serialized one level deep, without their own refs/cites).

        Returns:
            Dictionary representation of the paper.
        """
        result = {
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "doi": self.doi,
            "abstract": self.abstract,
            "venue": self.venue,
            "url": self.url,
            "pdf_url": self.pdf_url,
            "citation_count": self.citation_count,
            "sources": self.sources,
        }

        if include_refs_cites:
            result["references"] = (
                [p.to_dict(include_refs_cites=False) for p in self.references]
                if self.references
                else None
            )
            result["citations"] = (
                [p.to_dict(include_refs_cites=False) for p in self.citations]
                if self.citations
                else None
            )

        return result

    @classmethod
    def from_dict(cls, data: dict, use_registry: bool = True) -> "Paper":
        """
        Create a Paper from a dictionary, using the registry for deduplication.

        Handles both legacy format (no refs/cites) and new format
        (refs/cites as list of dicts).

        Args:
            data: Dictionary with paper fields.
            use_registry: If True (default), use the Paper Registry to ensure
                each unique paper is represented by a single object.

        Returns:
            Paper instance (may be an existing paper from the registry).
        """
        if use_registry:
            return get_registry().get_or_create(data)
        return cls._from_dict_without_registry(data)

    @classmethod
    def _from_dict_without_registry(cls, data: dict) -> "Paper":
        """
        Create a Paper from a dictionary without using the registry.

        This is used internally by the registry's get_or_create method,
        and for cases where registry use should be bypassed.

        Args:
            data: Dictionary with paper fields.

        Returns:
            New Paper instance.
        """
        # Parse references if present (recursively, but without registry
        # to avoid infinite loops during get_or_create)
        references = None
        if "references" in data and data["references"] is not None:
            references = [
                cls._from_dict_without_registry(ref)
                for ref in data["references"]
            ]

        # Parse citations if present
        citations = None
        if "citations" in data and data["citations"] is not None:
            citations = [
                cls._from_dict_without_registry(cit)
                for cit in data["citations"]
            ]

        return cls(
            title=data.get("title", ""),
            authors=data.get("authors", []),
            year=data.get("year"),
            doi=data.get("doi"),
            abstract=data.get("abstract"),
            venue=data.get("venue"),
            url=data.get("url"),
            pdf_url=data.get("pdf_url"),
            citation_count=data.get("citation_count"),
            sources=data.get("sources", []),
            references=references,
            citations=citations,
        )

    def title_preview(self, max_length: int = 50) -> str:
        """
        Return a truncated title for display in logs or UI.

        Args:
            max_length: Maximum length of the returned string.

        Returns:
            Truncated title, or DOI if no title, or "Unknown" as fallback.
        """
        text = self.title or self.doi or "Unknown"
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."

    def merge_with(self, other: "Paper") -> "Paper":
        """
        Create a consolidated paper from two equal papers.

        Keeps non-None values, preferring self when both have values.
        Combines sources lists (union, preserving order).

        Raises:
            ValueError: If papers are not equal (different DOI/title).
        """
        if self != other:
            raise ValueError("Can only merge equal papers")

        # Combine sources for provenance tracking (union, preserving order)
        combined_sources = list(self.sources)
        for src in other.sources:
            if src not in combined_sources:
                combined_sources.append(src)

        # For citation count, prefer higher value when both exist
        merged_citation_count = None
        if (
            self.citation_count is not None
            and other.citation_count is not None
        ):
            merged_citation_count = max(
                self.citation_count, other.citation_count
            )
        elif self.citation_count is not None:
            merged_citation_count = self.citation_count
        elif other.citation_count is not None:
            merged_citation_count = other.citation_count

        return Paper(
            title=self.title or other.title,
            authors=self.authors if self.authors else other.authors,
            year=self.year if self.year is not None else other.year,
            doi=self.doi or other.doi,
            abstract=self.abstract or other.abstract,
            venue=self.venue or other.venue,
            url=self.url or other.url,
            pdf_url=self.pdf_url or other.pdf_url,
            citation_count=merged_citation_count,
            sources=combined_sources,
            references=(
                self.references
                if self.references is not None
                else other.references
            ),
            citations=(
                self.citations
                if self.citations is not None
                else other.citations
            ),
        )


@dataclass
class SearchFilters:
    """
    Common filtering criteria for academic paper searches.

    Fields:
        year: Publication year or range (e.g., "2020", "2020-2024", "2020-", "-2024")
        open_access: If True, only return open access papers
        venue: Filter by venue/journal name (substring match)
        min_citations: Minimum citation count
        pub_types: List of publication types to include
            (article, conference, review, book, preprint, dataset)
    """

    year: str | None = None
    open_access: bool = False
    venue: str | None = None
    min_citations: int | None = None
    pub_types: list[str] | None = None

    def year_range(self) -> tuple[int | None, int | None]:
        """
        Parse the year field into a (start, end) tuple.

        Returns:
            Tuple of (start_year, end_year) where None indicates open boundary.
            Returns (None, None) if no year filter is set.

        Raises:
            ValueError: If year format is invalid.
        """
        if not self.year:
            return (None, None)

        year_str = self.year.strip()

        # Single year: "2020"
        if year_str.isdigit():
            year = int(year_str)
            return (year, year)

        # Range with dash
        if "-" in year_str:
            parts = year_str.split("-", 1)

            # Open start: "-2024"
            if parts[0] == "":
                return (None, int(parts[1]))

            # Open end: "2020-"
            if parts[1] == "":
                return (int(parts[0]), None)

            # Full range: "2020-2024"
            return (int(parts[0]), int(parts[1]))

        raise ValueError(f"Invalid year format: {year_str}")

    def as_dict(self) -> dict:
        """
        Convert filters to a dictionary for display or storage.

        Only includes non-default (active) filters.
        """
        result = {}
        if self.year:
            result["year"] = self.year
        if self.open_access:
            result["open_access"] = True
        if self.venue:
            result["venue"] = self.venue
        if self.min_citations is not None:
            result["min_citations"] = self.min_citations
        if self.pub_types:
            result["pub_types"] = self.pub_types
        return result

    def cache_key(self) -> str:
        """
        Generate a stable string key for caching filtered searches.

        Returns an empty string if no filters are active, so unfiltered
        searches maintain backward compatibility with existing cache entries.
        """
        parts = []
        if self.year:
            parts.append(f"y:{self.year}")
        if self.open_access:
            parts.append("oa:1")
        if self.venue:
            parts.append(f"v:{self.venue}")
        if self.min_citations is not None:
            parts.append(f"c:{self.min_citations}")
        if self.pub_types:
            parts.append(f"t:{','.join(sorted(self.pub_types))}")
        return "|".join(parts)

    def is_empty(self) -> bool:
        """Return True if no filters are active."""
        return not any(
            [
                self.year,
                self.open_access,
                self.venue,
                self.min_citations is not None,
                self.pub_types,
            ]
        )

    def matches(self, paper: Paper) -> bool:
        """
        Check if a paper matches all active filters.

        Args:
            paper: The Paper object to check.

        Returns:
            True if the paper matches all active filters, False otherwise.
            Returns True if no filters are active.
        """
        if self.is_empty():
            return True

        # Year filter
        if self.year:
            try:
                start, end = self.year_range()
                if paper.year is None:
                    return False
                if start is not None and paper.year < start:
                    return False
                if end is not None and paper.year > end:
                    return False
            except ValueError:
                pass  # Invalid year format, skip filter

        # Venue filter (case-insensitive substring match)
        if self.venue:
            if not paper.venue:
                return False
            if self.venue.lower() not in paper.venue.lower():
                return False

        # Citation count filter
        if self.min_citations is not None:
            paper_citations = getattr(paper, "citation_count", None)
            if (
                paper_citations is None
                or paper_citations < self.min_citations
            ):
                return False

        # Open access filter
        if self.open_access:
            paper_oa = getattr(paper, "open_access", False)
            if not paper_oa:
                return False

        # Publication type filter
        if self.pub_types:
            paper_type = getattr(paper, "publication_type", None)
            if paper_type is None or paper_type not in self.pub_types:
                return False

        return True


@dataclass
class SearchResult:
    """Represents the result of a search query."""

    query: str
    provider: str
    timestamp: str
    papers: list[Paper]
    filters: dict | None = None

    def merge(self, other: "SearchResult") -> "SearchResult":
        """Merge two search results, deduplicating and consolidating papers."""
        logger.debug(
            f"Merging search results: {len(self.papers)} + {len(other.papers)} papers"
        )

        # Use dict keyed by paper identity to enable consolidation
        paper_map: dict[Paper, Paper] = {}

        for paper in self.papers:
            paper_map[paper] = paper

        duplicates = 0
        for paper in other.papers:
            if paper in paper_map:
                # Consolidate with existing paper
                paper_map[paper] = paper_map[paper].merge_with(paper)
                duplicates += 1
            else:
                paper_map[paper] = paper

        merged_count = len(paper_map)
        logger.info(
            f"Merged results: {merged_count} unique papers ({duplicates} duplicates removed)"
        )

        return SearchResult(
            query=f"{self.query} | {other.query}",
            provider=f"{self.provider}, {other.provider}",
            timestamp=self.timestamp,
            papers=list(paper_map.values()),
            filters=None,
        )


class Search:
    """Manages a structured search across bibliographic databases."""

    def __init__(self, query: str):
        """Initialize a search with the given query."""
        self.query = query
        self.results: list[SearchResult] = []

    def execute(
        self,
        providers: list[str] | None = None,
        limit: int = 100,
        filters: SearchFilters | None = None,
    ) -> list[SearchResult]:
        """
        Execute the search across specified providers.

        Args:
            providers: List of provider names to search. If None, uses the
                default providers (openalex, dblp).
            limit: Maximum number of results per provider.
            filters: Optional SearchFilters to apply to the search.

        Returns:
            List of SearchResult objects, one per provider.
        """
        from scholar.providers import get_provider, get_default_providers

        timestamp = datetime.now().isoformat()

        # Determine which providers to use
        if providers is None:
            provider_list = get_default_providers()
        else:
            provider_list = [
                get_provider(name)
                for name in providers
                if get_provider(name) is not None
            ]

        logger.info(f"Executing search for query: '{self.query}'")
        logger.debug(
            f"Using {len(provider_list)} provider(s): {[p.name for p in provider_list]}"
        )

        # Query each provider
        for provider in provider_list:
            logger.debug(f"Querying {provider.name} with limit={limit}")
            papers = provider.search(self.query, limit=limit, filters=filters)
            logger.info(f"{provider.name}: Retrieved {len(papers)} papers")
            result = SearchResult(
                query=self.query,
                provider=provider.name,
                timestamp=timestamp,
                papers=papers,
                filters=filters.as_dict() if filters else None,
            )
            self.results.append(result)

        logger.info(f"Search complete: {len(self.results)} result set(s)")
        return self.results


# Module-level registry instance
_registry: PaperRegistry | None = None


def get_registry() -> PaperRegistry:
    """
    Get the global paper registry.

    The registry is created lazily on first access.

    Returns:
        The global PaperRegistry instance.
    """
    global _registry
    if _registry is None:
        _registry = PaperRegistry()
    return _registry


@contextmanager
def isolated_registry():
    """
    Context manager providing an isolated paper registry for testing.

    Within the context, a fresh registry is used. The original registry
    is restored when the context exits, preventing test pollution.

    Example:
        with isolated_registry():
            paper = Paper.from_dict({"title": "Test", "authors": []})
            assert len(get_registry()) == 1
        # Original registry restored here

    Yields:
        The isolated PaperRegistry instance.
    """
    global _registry
    original = _registry
    _registry = PaperRegistry()
    try:
        yield _registry
    finally:
        _registry = original


def filter_papers(papers: list[Paper], filters: SearchFilters) -> list[Paper]:
    """
    Filter a list of papers using the given filters.

    This function applies filters locally to an existing collection of papers,
    without making any API calls. Useful for narrowing down results from
    multiple merged searches.

    Args:
        papers: List of Paper objects to filter.
        filters: SearchFilters specifying the filtering criteria.

    Returns:
        List of papers matching all active filters.

    Example:
        >>> from scholar import Paper, SearchFilters, filter_papers
        >>> papers = [Paper(title="ML Paper", year=2020),
        ...           Paper(title="Old Paper", year=2015)]
        >>> filters = SearchFilters(year="2018-")
        >>> filter_papers(papers, filters)
        [Paper(title="ML Paper", year=2020)]
    """
    if filters.is_empty():
        return papers
    return [p for p in papers if filters.matches(p)]


def search(query: str) -> SearchResult:
    """
    Perform a simple search and return results.

    This is a convenience function for quick searches.
    For more control, use the Search class directly.
    """
    s = Search(query)
    s.execute()
    return (
        s.results[0]
        if s.results
        else SearchResult(
            query=query,
            provider="none",
            timestamp=datetime.now().isoformat(),
            papers=[],
        )
    )
