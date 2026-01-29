"""
Search providers for bibliographic databases.

Each provider implements the SearchProvider protocol and registers
itself with the provider registry on import.
"""

import logging
import os
from typing import Protocol

from cachetools import cachedmethod

from scholar import Paper, SearchFilters
from scholar.cache import load_cache, register_cache
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time

import pyalex
import requests
import re
import requests
from typing import Any

from scholar.utils import safe_get_nested, ensure_list
import time

import arxiv

logger = logging.getLogger(__name__)
# Provider constants
DEFAULT_LIMIT = 100
DBLP_API_URL = "https://dblp.org/search/publ/api"
WOS_STARTER_API_URL = (
    "https://api.clarivate.com/apis/wos-starter/v1/documents"
)
WOS_EXPANDED_API_URL = "https://wos-api.clarivate.com/api/wos"
_WOS_NOT_PROVIDED = object()  # Sentinel for "argument not passed"
IEEE_API_URL = "https://ieeexploreapi.ieee.org/api/v1/search/articles"


class SearchProvider(Protocol):
    """Protocol for search providers."""

    name: str

    def search(
        self,
        query: str,
        limit: int = 100,
        filters: "SearchFilters | None" = None,
    ) -> list[Paper]:
        """
        Search for papers matching the query.

        Args:
            query: The search query string.
            limit: Maximum number of results to return.
            filters: Optional SearchFilters to apply.

        Returns:
            List of Paper objects matching the query.
        """
        ...

    def is_available(self) -> bool:
        """
        Check if this provider is available for use.

        A provider is available if it either doesn't require an API key,
        or has its required API key configured in the environment.

        Returns:
            True if the provider can be used, False otherwise.
        """
        ...

    def get_paper_citations(
        self,
        paper_id: str,
        limit: int = 100,
    ) -> list[Paper]:
        """
        Get papers that cite the given paper.

        Args:
            paper_id: The paper identifier (DOI, provider-specific ID, etc.).
            limit: Maximum number of citing papers to return.

        Returns:
            List of Paper objects that cite this paper.

        Raises:
            NotImplementedError: If this provider doesn't support citation retrieval.
        """
        ...

    def get_paper_references(
        self,
        paper_id: str,
        limit: int = 100,
    ) -> list[Paper]:
        """
        Get papers referenced by the given paper.

        Args:
            paper_id: The paper identifier (DOI, provider-specific ID, etc.).
            limit: Maximum number of referenced papers to return.

        Returns:
            List of Paper objects referenced by this paper.

        Raises:
            NotImplementedError: If this provider doesn't support reference retrieval.
        """
        ...


PROVIDERS: dict[str, SearchProvider] = {}


def register_provider(provider: SearchProvider) -> None:
    """Register a provider for use in searches."""
    PROVIDERS[provider.name] = provider


def get_provider(name: str) -> SearchProvider | None:
    """Get a provider by name, or None if not found."""
    return PROVIDERS.get(name)


def get_all_providers() -> list[SearchProvider]:
    """Get all registered providers."""
    return list(PROVIDERS.values())


def get_snowball_providers() -> list[SearchProvider]:
    """
    Get all available providers that support citation/reference fetching.

    Returns providers in priority order: S2, OpenAlex, WOS (if expanded).
    Only returns providers that are available and have citation methods.

    Returns:
        List of providers with citation support.
    """
    # Priority order for DOI-based snowballing
    priority = ["s2", "openalex", "wos"]
    result = []

    for name in priority:
        provider = PROVIDERS.get(name)
        if provider is None:
            continue

        # Check if provider is available
        if not provider.is_available():
            continue

        # Check if provider has citation methods
        if not hasattr(provider, "get_paper_citations"):
            continue

        # For WOS, only use if Expanded API is available (required for citations)
        if (
            name == "wos"
            and getattr(provider, "_api_tier", None) != "expanded"
        ):
            continue

        result.append(provider)

    return result


def get_snowball_provider() -> SearchProvider | None:
    """
    Get the best available provider for citation/reference fetching.

    Returns the first available provider that supports citation retrieval.
    For fetching from multiple providers, use get_snowball_providers() instead.

    Returns:
        A provider with citation support, or None if none available.
    """
    providers = get_snowball_providers()
    return providers[0] if providers else None


def fetch_references(doi: str, limit: int = 100) -> list[Paper]:
    """
    Fetch references for a paper from all available providers.

    Tries each provider in priority order and merges results. Papers are
    deduplicated by DOI, with data merged from multiple sources.

    Args:
        doi: DOI of the paper to fetch references for.
        limit: Maximum number of references to return per provider.

    Returns:
        List of referenced papers, deduplicated and merged.
    """
    providers = get_snowball_providers()
    if not providers:
        return []

    all_papers: dict[str, Paper] = {}  # DOI -> Paper
    papers_without_doi: list[Paper] = []

    for provider in providers:
        try:
            refs = provider.get_paper_references(doi, limit)
            logger.info(f"{provider.name}: found {len(refs)} references")

            for paper in refs:
                if paper.doi:
                    # Merge with existing paper if we have it
                    if paper.doi in all_papers:
                        all_papers[paper.doi] = all_papers[
                            paper.doi
                        ].merge_with(paper)
                    else:
                        all_papers[paper.doi] = paper
                elif paper.title:
                    # No DOI - check if we can match by title
                    # For now, just add to the list (may have duplicates)
                    papers_without_doi.append(paper)

        except NotImplementedError:
            logger.debug(f"{provider.name}: references not supported")
        except Exception as e:
            logger.warning(f"{provider.name}: error fetching references: {e}")

    # Combine papers with DOIs and those without
    result = list(all_papers.values()) + papers_without_doi
    logger.info(f"Total unique references: {len(result)}")
    return result


def fetch_citations(doi: str, limit: int = 100) -> list[Paper]:
    """
    Fetch citing papers for a paper from all available providers.

    Tries each provider in priority order and merges results. Papers are
    deduplicated by DOI, with data merged from multiple sources.

    Args:
        doi: DOI of the paper to fetch citations for.
        limit: Maximum number of citing papers to return per provider.

    Returns:
        List of citing papers, deduplicated and merged.
    """
    providers = get_snowball_providers()
    if not providers:
        return []

    all_papers: dict[str, Paper] = {}  # DOI -> Paper
    papers_without_doi: list[Paper] = []

    for provider in providers:
        try:
            cites = provider.get_paper_citations(doi, limit)
            logger.info(f"{provider.name}: found {len(cites)} citations")

            for paper in cites:
                if paper.doi:
                    # Merge with existing paper if we have it
                    if paper.doi in all_papers:
                        all_papers[paper.doi] = all_papers[
                            paper.doi
                        ].merge_with(paper)
                    else:
                        all_papers[paper.doi] = paper
                elif paper.title:
                    # No DOI - check if we can match by title
                    papers_without_doi.append(paper)

        except NotImplementedError:
            logger.debug(f"{provider.name}: citations not supported")
        except Exception as e:
            logger.warning(f"{provider.name}: error fetching citations: {e}")

    # Combine papers with DOIs and those without
    result = list(all_papers.values()) + papers_without_doi
    logger.info(f"Total unique citations: {len(result)}")
    return result


def get_default_providers() -> list[SearchProvider]:
    """
    Get providers that are currently available for use.

    Returns all providers where [[is_available()]] returns [[True]].
    This includes providers that don't require API keys (s2,
    openalex, dblp) and providers with required API keys that are configured
    in the environment (wos, ieee).
    """
    return [p for p in PROVIDERS.values() if p.is_available()]


def get_provider_limits() -> dict[str, int | None]:
    """
    Get the maximum result limits for all registered providers.

    Returns a dict mapping provider names to their MAX_LIMIT values.
    A value of None indicates no documented maximum limit.
    """
    return {
        name: getattr(p, "MAX_LIMIT", None) for name, p in PROVIDERS.items()
    }


class SemanticScholarProvider:
    """Search provider for Semantic Scholar."""

    name = "s2"
    MAX_LIMIT: int | None = None  # No documented maximum
    API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
    RATE_LIMIT_WITH_KEY = 1.0  # 1 second between requests
    RATE_LIMIT_WITHOUT_KEY = 3.0  # 3 seconds (100 req/5min = 0.33/sec)

    def __init__(self, api_key: str | None = None):
        """
        Initialize the Semantic Scholar provider.

        Args:
            api_key: Optional API key for higher rate limits.
                     If not provided, uses S2_API_KEY environment variable.
        """
        self.api_key = api_key or os.environ.get("S2_API_KEY")
        self._cache: dict = load_cache(self.name)
        register_cache(self.name, self._cache)
        self._last_request_time: float = 0.0
        self._session = self._create_session()

    def is_available(self) -> bool:
        """Semantic Scholar is always available (API key is optional)."""
        return True

    @property
    def _min_request_interval(self) -> float:
        """Return minimum interval based on whether API key is set."""
        if self.api_key:
            return self.RATE_LIMIT_WITH_KEY
        return self.RATE_LIMIT_WITHOUT_KEY

    def _create_session(self) -> requests.Session:
        """Create a session with exponential back-off retry logic."""
        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=1,  # 1s, 2s, 4s delays
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        return session

    def _wait_for_rate_limit(self) -> None:
        """Ensure minimum interval between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()

    @cachedmethod(
        lambda self: self._cache,
        key=lambda self, query, limit=100, filters=None: (
            query,
            limit,
            filters.cache_key() if filters else "",
        ),
    )
    def search(
        self,
        query: str,
        limit: int = 100,
        filters: SearchFilters | None = None,
    ) -> list[Paper]:
        """
        Search Semantic Scholar for papers matching the query.

        Automatically fetches multiple pages if the requested limit exceeds
        the API's per-request maximum (100 results per page).
        """
        all_papers: list[Paper] = []
        offset = 0
        page_size = min(limit, 100)  # S2 API returns max 100 per request

        try:
            while len(all_papers) < limit:
                self._wait_for_rate_limit()

                headers = {}
                if self.api_key:
                    headers["x-api-key"] = self.api_key
                    logger.debug("semantic_scholar: Using API key")

                # Calculate how many results we still need
                remaining = limit - len(all_papers)
                current_page_size = min(page_size, remaining)

                params = {
                    "query": query,
                    "limit": current_page_size,
                    "offset": offset,
                    "fields": "title,authors,year,abstract,venue,externalIds,url,openAccessPdf,citationCount,publicationTypes",
                }

                # Apply filters (Semantic Scholar supports most filters natively)
                if filters:
                    # Year filter: Semantic Scholar accepts "YYYY" or "YYYY-YYYY"
                    if filters.year:
                        start, end = filters.year_range()
                        if start and end:
                            if start == end:
                                params["year"] = str(start)
                            else:
                                params["year"] = f"{start}-{end}"
                        elif start:
                            # Open end: from start year onwards
                            params["year"] = f"{start}-"
                        elif end:
                            # Open start: up to end year
                            params["year"] = f"-{end}"

                    # Open access: filter via openAccessPdf field
                    if filters.open_access:
                        params["openAccessPdf"] = ""

                    # Venue filter
                    if filters.venue:
                        params["venue"] = filters.venue

                    # Minimum citations
                    if filters.min_citations is not None:
                        params["minCitationCount"] = filters.min_citations

                    # Publication types: map our normalized types to S2 values
                    if filters.pub_types:
                        s2_types = []
                        type_mapping = {
                            "article": "JournalArticle",
                            "conference": "Conference",
                            "review": "Review",
                            "book": "Book",
                            "preprint": "Preprint",
                            "dataset": "Dataset",
                        }
                        for pt in filters.pub_types:
                            if pt.lower() in type_mapping:
                                s2_types.append(type_mapping[pt.lower()])
                        if s2_types:
                            params["publicationTypes"] = ",".join(s2_types)

                response = self._session.get(
                    self.API_URL,
                    params=params,
                    headers=headers,
                    timeout=30,
                )

                if response.status_code == 429:
                    logger.warning(
                        "s2: Rate limited. "
                        "Get a free API key at "
                        "https://www.semanticscholar.org/product/api#api-key-form "
                        "and set S2_API_KEY environment variable."
                    )
                    break

                response.raise_for_status()
                data = response.json()

                papers = data.get("data", [])
                if not papers:
                    # No more results available
                    break

                all_papers.extend(self._convert_paper(p) for p in papers)
                offset += len(papers)

                # Check if we've fetched all available results
                total = data.get("total", 0)
                if offset >= total:
                    break

            logger.debug(
                f"semantic_scholar: Retrieved {len(all_papers)} papers"
            )
            return all_papers
        except requests.exceptions.RetryError:
            logger.warning(
                "s2: Rate limited after retries. "
                "Get a free API key at "
                "https://www.semanticscholar.org/product/api#api-key-form "
                "and set S2_API_KEY environment variable."
            )
            return all_papers
        except requests.exceptions.HTTPError as e:
            logger.warning("s2: HTTP error: %s", e)
            return all_papers
        except Exception as e:
            logger.warning("s2: %s", e)
            return all_papers

    def get_paper_by_doi(self, doi: str | None) -> Paper | None:
        """
        Fetch a single paper by its DOI.

        Args:
            doi: The DOI to look up (e.g., "10.1145/1234567.1234568").

        Returns:
            Paper if found, None otherwise.
        """
        if not doi:
            return None

        # Check cache first
        cache_key = ("doi", doi)
        if cache_key in self._cache:
            logger.info(f"semantic_scholar: Cache hit for DOI {doi}")
            return self._cache[cache_key]

        logger.info(
            f"semantic_scholar: Cache miss for DOI {doi}, fetching from API"
        )

        try:
            self._wait_for_rate_limit()

            headers = {}
            if self.api_key:
                headers["x-api-key"] = self.api_key

            # Use the paper endpoint with DOI: prefix
            url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}"
            response = self._session.get(
                url,
                params={
                    "fields": "title,authors,year,abstract,venue,externalIds,url,openAccessPdf",
                },
                headers=headers,
                timeout=30,
            )

            if response.status_code == 404:
                # Paper not found - cache the miss to avoid repeated lookups
                self._cache[cache_key] = None
                return None

            if response.status_code == 429:
                logger.warning("s2: Rate limited during DOI lookup")
                return None

            response.raise_for_status()
            paper_data = response.json()

            paper = self._convert_paper(paper_data)
            self._cache[cache_key] = paper
            return paper

        except requests.exceptions.HTTPError as e:
            logger.warning("s2: DOI lookup error: %s", e)
            return None
        except Exception as e:
            logger.warning("s2: DOI lookup failed: %s", e)
            return None

    def get_paper_citations(
        self,
        paper_id: str,
        limit: int = 100,
    ) -> list[Paper]:
        """
        Get papers that cite the given paper.

        Args:
            paper_id: DOI or Semantic Scholar paper ID.
            limit: Maximum number of citing papers to return.

        Returns:
            List of Paper objects that cite this paper.
        """
        return self._get_related_papers(paper_id, "citations", limit)

    def get_paper_references(
        self,
        paper_id: str,
        limit: int = 100,
    ) -> list[Paper]:
        """
        Get papers referenced by the given paper.

        Args:
            paper_id: DOI or Semantic Scholar paper ID.
            limit: Maximum number of referenced papers to return.

        Returns:
            List of Paper objects referenced by this paper.
        """
        return self._get_related_papers(paper_id, "references", limit)

    def _get_related_papers(
        self,
        paper_id: str,
        relation: str,
        limit: int,
    ) -> list[Paper]:
        """
        Fetch related papers (citations or references) for a given paper.

        Args:
            paper_id: DOI or Semantic Scholar paper ID.
            relation: Either "citations" or "references".
            limit: Maximum number of papers to return.

        Returns:
            List of related Paper objects.
        """
        if not paper_id:
            return []

        # Use DOI: prefix if it looks like a DOI
        if "/" in paper_id and not paper_id.startswith("DOI:"):
            paper_id = f"DOI:{paper_id}"

        # Check cache first
        cache_key = (relation, paper_id, limit)
        if cache_key in self._cache:
            logger.info(f"s2: Cache hit for {relation} of {paper_id}")
            return self._cache[cache_key]

        logger.info(
            f"s2: Cache miss for {relation} of {paper_id}, fetching from API"
        )

        all_papers: list[Paper] = []
        offset = 0
        page_size = min(limit, 100)

        try:
            while len(all_papers) < limit:
                self._wait_for_rate_limit()

                headers = {}
                if self.api_key:
                    headers["x-api-key"] = self.api_key

                url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}/{relation}"
                response = self._session.get(
                    url,
                    params={
                        "fields": "title,authors,year,abstract,venue,externalIds,url,openAccessPdf",
                        "limit": page_size,
                        "offset": offset,
                    },
                    headers=headers,
                    timeout=30,
                )

                if response.status_code == 404:
                    logger.warning("s2: Paper not found: %s", paper_id)
                    break

                if response.status_code == 429:
                    logger.warning(
                        "s2: Rate limited during %s fetch", relation
                    )
                    break

                response.raise_for_status()
                data = response.json()

                items = data.get("data", [])
                if not items:
                    break

                # Extract papers from the response
                # Citations have "citingPaper", references have "citedPaper"
                paper_key = (
                    "citingPaper" if relation == "citations" else "citedPaper"
                )
                for item in items:
                    paper_data = item.get(paper_key)
                    if not paper_data:
                        # Some items may not have the nested paper data
                        continue
                    title = paper_data.get("title")
                    if not title:
                        # Skip papers without titles
                        continue
                    all_papers.append(self._convert_paper(paper_data))

                if len(items) < page_size:
                    break

                offset += page_size

        except requests.exceptions.HTTPError as e:
            logger.warning("s2: %s fetch error: %s", relation, e)
        except Exception as e:
            logger.warning("s2: %s fetch failed: %s", relation, e)

        logger.info(
            "s2: Found %d %s for %s", len(all_papers), relation, paper_id
        )

        # Cache the result
        self._cache[cache_key] = all_papers
        return all_papers

    def _convert_paper(self, paper_data: dict) -> Paper:
        """Convert a Semantic Scholar API response to our Paper type."""
        # Extract DOI from externalIds if available
        doi = None
        external_ids = paper_data.get("externalIds") or {}
        if external_ids:
            doi = external_ids.get("DOI")

        # Extract author names from list of author dicts
        authors = []
        for author in paper_data.get("authors") or []:
            if author.get("name"):
                authors.append(author["name"])

        # Extract PDF URL from openAccessPdf if available
        pdf_url = None
        open_access_pdf = paper_data.get("openAccessPdf") or {}
        if open_access_pdf:
            pdf_url = open_access_pdf.get("url")

        return Paper(
            title=paper_data.get("title") or "",
            authors=authors,
            year=paper_data.get("year"),
            doi=doi,
            abstract=paper_data.get("abstract"),
            venue=paper_data.get("venue"),
            url=paper_data.get("url"),
            pdf_url=pdf_url,
            sources=[self.name],
        )


# Register the provider on module import
register_provider(SemanticScholarProvider())


class OpenAlexProvider:
    """Search provider for OpenAlex."""

    name = "openalex"
    MAX_LIMIT: int | None = None  # No documented maximum
    RATE_LIMIT = 0.1  # 10 requests/second = 0.1 seconds between requests

    def __init__(self, email: str | None = None):
        """
        Initialize the OpenAlex provider.

        Args:
            email: Optional email for polite pool access (faster responses).
                   If not provided, uses OPENALEX_EMAIL environment variable.
        """
        configured_email = email or os.environ.get("OPENALEX_EMAIL")
        if configured_email:
            pyalex.config.email = configured_email
        self._cache: dict = load_cache(self.name)
        register_cache(self.name, self._cache)
        self._last_request_time: float = 0.0

    def is_available(self) -> bool:
        """OpenAlex is always available (email is optional)."""
        return True

    def _wait_for_rate_limit(self) -> None:
        """Ensure minimum interval between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.RATE_LIMIT:
            time.sleep(self.RATE_LIMIT - elapsed)
        self._last_request_time = time.time()

    @cachedmethod(
        lambda self: self._cache,
        key=lambda self, query, limit=100, filters=None: (
            query,
            limit,
            filters.cache_key() if filters else "",
        ),
    )
    def search(
        self,
        query: str,
        limit: int = 100,
        filters: SearchFilters | None = None,
    ) -> list[Paper]:
        """
        Search OpenAlex for papers matching the query.

        Automatically fetches multiple pages if the requested limit exceeds
        the API's per-request maximum (200 results per page).
        """
        try:
            all_papers: list[Paper] = []
            page_size = min(limit, 200)  # OpenAlex returns max 200 per page

            logger.debug(
                f"openalex: Searching for '{query}' with limit={limit}"
            )
            self._wait_for_rate_limit()
            works = pyalex.Works().search(query)

            # Apply filters (OpenAlex supports most filters natively)
            if filters:
                # Year filter
                if filters.year:
                    start, end = filters.year_range()
                    if start and end:
                        if start == end:
                            works = works.filter(publication_year=start)
                        else:
                            works = works.filter(
                                publication_year=f"{start}-{end}"
                            )
                    elif start:
                        works = works.filter(publication_year=f">{start-1}")
                    elif end:
                        works = works.filter(publication_year=f"<{end+1}")

                # Open access filter
                if filters.open_access:
                    works = works.filter(is_oa=True)

                # Venue filter (search in source display name)
                if filters.venue:
                    works = works.filter(
                        primary_location={
                            "source": {"display_name": filters.venue}
                        }
                    )

                # Minimum citations
                if filters.min_citations is not None:
                    works = works.filter(
                        cited_by_count=f">{filters.min_citations-1}"
                    )

                # Publication types: map our normalized types to OpenAlex values
                if filters.pub_types:
                    oa_types = []
                    type_mapping = {
                        "article": "article",
                        "conference": "proceedings-article",
                        "review": "review",
                        "book": "book",
                        "preprint": "preprint",
                        "dataset": "dataset",
                    }
                    for pt in filters.pub_types:
                        if pt.lower() in type_mapping:
                            oa_types.append(type_mapping[pt.lower()])
                    if oa_types:
                        # OpenAlex uses pipe for OR in filters
                        works = works.filter(type="|".join(oa_types))

            # Use pagination to fetch all results up to the limit
            for page in works.paginate(per_page=page_size):
                self._wait_for_rate_limit()
                for work in page:
                    all_papers.append(self._convert_work(work))
                    if len(all_papers) >= limit:
                        logger.debug(
                            f"openalex: Retrieved {len(all_papers)} papers"
                        )
                        return all_papers

            logger.debug(f"openalex: Retrieved {len(all_papers)} papers")
            return all_papers
        except Exception as e:
            logger.warning("openalex: %s", e)
            return []

    def get_paper_by_doi(self, doi: str | None) -> Paper | None:
        """
        Fetch a single paper by its DOI.

        Args:
            doi: The DOI to look up (e.g., "10.1145/1234567.1234568").

        Returns:
            Paper if found, None otherwise.
        """
        if not doi:
            return None

        # Check cache first
        cache_key = ("doi", doi)
        if cache_key in self._cache:
            logger.info(f"openalex: Cache hit for DOI {doi}")
            return self._cache[cache_key]

        logger.info(f"openalex: Cache miss for DOI {doi}, fetching from API")

        try:
            self._wait_for_rate_limit()

            # OpenAlex uses full DOI URL as identifier
            doi_url = f"https://doi.org/{doi}"
            work = pyalex.Works()[doi_url]

            if not work:
                self._cache[cache_key] = None
                return None

            paper = self._convert_work(work)
            self._cache[cache_key] = paper
            return paper

        except Exception as e:
            logger.warning("openalex: DOI lookup failed: %s", e)
            return None

    def _convert_work(self, work: dict) -> Paper:
        """Convert an OpenAlex work to our Paper type."""
        # Extract author names from authorships
        authors = []
        for authorship in work.get("authorships", []):
            author_info = authorship.get("author", {})
            name = author_info.get("display_name")
            if name:
                authors.append(name)

        # Extract DOI (remove URL prefix if present)
        doi = work.get("doi")
        if doi and doi.startswith("https://doi.org/"):
            doi = doi[16:]

        # Extract venue from primary location
        venue = None
        primary_location = work.get("primary_location", {})
        if primary_location:
            source = primary_location.get("source", {})
            if source:
                venue = source.get("display_name")

        # Extract PDF URL from open_access or primary_location
        pdf_url = None
        open_access = work.get("open_access", {})
        if open_access:
            pdf_url = open_access.get("oa_url")
        if not pdf_url and primary_location:
            pdf_url = primary_location.get("pdf_url")

        return Paper(
            title=work.get("title", ""),
            authors=authors,
            year=work.get("publication_year"),
            doi=doi,
            abstract=work.get("abstract"),
            venue=venue,
            url=work.get("id"),
            pdf_url=pdf_url,
            sources=[self.name],
        )


# Register the provider on module import
register_provider(OpenAlexProvider())


class DBLPProvider:
    """Search provider for DBLP."""

    name = "dblp"
    MAX_LIMIT = 1000  # DBLP API caps at 1000 results per request

    def __init__(self):
        """Initialize the DBLP provider."""
        self._cache: dict = load_cache(self.name)
        register_cache(self.name, self._cache)

    def is_available(self) -> bool:
        """DBLP is always available (no API key needed)."""
        return True

    @cachedmethod(
        lambda self: self._cache,
        key=lambda self, query, limit=100, filters=None: (
            query,
            limit,
            filters.cache_key() if filters else "",
        ),
    )
    def search(
        self,
        query: str,
        limit: int = 100,
        filters: SearchFilters | None = None,
    ) -> list[Paper]:
        """
        Search DBLP for papers matching the query.

        Automatically fetches multiple pages if the requested limit exceeds
        the API's per-request maximum (1000 results per page).
        """
        all_papers: list[Paper] = []
        offset = 0
        page_size = min(limit, 1000)  # DBLP API caps at 1000 per request

        try:
            # Build query with embedded filters
            effective_query = query
            if filters:
                # Year filter: DBLP uses "year:YYYY" or "year:YYYY:YYYY" syntax
                if filters.year:
                    start, end = filters.year_range()
                    if start and end:
                        if start == end:
                            effective_query += f" year:{start}"
                        else:
                            effective_query += f" year:{start}:{end}"
                    elif start:
                        # Open end: DBLP doesn't support this well, use current year
                        import datetime

                        current_year = datetime.datetime.now().year
                        effective_query += f" year:{start}:{current_year}"
                    elif end:
                        # Open start: use 1900 as earliest
                        effective_query += f" year:1900:{end}"

                # Venue filter
                if filters.venue:
                    effective_query += f" venue:{filters.venue}"

                # Publication types: map to DBLP type syntax
                if filters.pub_types:
                    dblp_types = []
                    type_mapping = {
                        "article": "Journal_Articles",
                        "conference": "Conference_and_Workshop_Papers",
                        "book": "Books_and_Theses",
                    }
                    for pt in filters.pub_types:
                        if pt.lower() in type_mapping:
                            dblp_types.append(type_mapping[pt.lower()])
                        else:
                            logger.warning(
                                "dblp: Publication type '%s' not supported, ignoring",
                                pt,
                            )
                    if dblp_types:
                        effective_query += f" type:{dblp_types[0]}"  # DBLP only supports one type

                # Warn about unsupported filters
                if filters.open_access:
                    logger.warning(
                        "dblp: Open access filter not supported, ignoring"
                    )
                if filters.min_citations is not None:
                    logger.warning(
                        "dblp: Citation count filter not supported, ignoring"
                    )

            logger.debug(f"dblp: Searching for '{query}' with limit={limit}")

            while len(all_papers) < limit:
                # Calculate how many results we still need
                remaining = limit - len(all_papers)
                current_page_size = min(page_size, remaining)

                response = requests.get(
                    DBLP_API_URL,
                    params={
                        "q": effective_query,
                        "format": "json",
                        "h": current_page_size,
                        "f": offset,
                    },
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()

                hits = data.get("result", {}).get("hits", {}).get("hit", [])
                if not hits:
                    # No more results available
                    break

                all_papers.extend(self._convert_hit(hit) for hit in hits)
                offset += len(hits)

                # Check if we've fetched all available results
                total_str = (
                    data.get("result", {}).get("hits", {}).get("@total", "0")
                )
                try:
                    total = int(total_str)
                except (ValueError, TypeError):
                    total = 0
                if offset >= total:
                    break

            logger.debug(f"dblp: Retrieved {len(all_papers)} papers")
            return all_papers
        except Exception as e:
            logger.warning("dblp: %s", e)
            return all_papers

    def _convert_hit(self, hit: dict) -> Paper:
        """Convert a DBLP API hit to our Paper type."""
        info = hit.get("info", {})

        # Extract year as integer if available
        year = None
        year_str = info.get("year")
        if year_str:
            try:
                year = int(year_str)
            except (ValueError, TypeError):
                pass

        # Extract author names from nested structure
        authors = []
        authors_data = info.get("authors", {}).get("author", [])
        # Handle single author (dict) vs multiple authors (list)
        if isinstance(authors_data, dict):
            authors_data = [authors_data]
        for author in authors_data:
            name = author.get("text") if isinstance(author, dict) else author
            if name:
                authors.append(name)

        return Paper(
            title=info.get("title", "") or "",
            authors=authors,
            year=year,
            doi=info.get("doi"),
            abstract=None,  # DBLP doesn't provide abstracts
            venue=info.get("venue"),
            url=info.get("url") or info.get("ee"),
            sources=[self.name],
        )


# Register the provider on module import
register_provider(DBLPProvider())


class WebOfScienceProvider:
    """Search provider for Web of Science.

    Supports both Starter and Expanded APIs, preferring Expanded when available.
    """

    name = "wos"

    def __init__(
        self,
        starter_api_key: str | None | object = _WOS_NOT_PROVIDED,
        expanded_api_key: str | None | object = _WOS_NOT_PROVIDED,
    ):
        """
        Initialize the Web of Science provider.

        Args:
            starter_api_key: API key for WoS Starter API.
                             If not provided, uses WOS_STARTER_API_KEY env var.
                             Pass None explicitly to disable.
            expanded_api_key: API key for WoS Expanded API.
                              If not provided, uses WOS_EXPANDED_API_KEY env var.
                              Pass None explicitly to disable.

        The legacy WOS_API_KEY environment variable is also checked and tried
        with both APIs for backward compatibility.
        """
        # Use env var only if argument was not provided at all
        if starter_api_key is _WOS_NOT_PROVIDED:
            self._starter_key = os.environ.get("WOS_STARTER_API_KEY")
        else:
            self._starter_key = starter_api_key

        if expanded_api_key is _WOS_NOT_PROVIDED:
            self._expanded_key = os.environ.get("WOS_EXPANDED_API_KEY")
        else:
            self._expanded_key = expanded_api_key

        # Legacy support: WOS_API_KEY can be used with either API
        legacy_key = os.environ.get("WOS_API_KEY")
        if legacy_key:
            if not self._expanded_key:
                self._expanded_key = legacy_key
            if not self._starter_key:
                self._starter_key = legacy_key

        # Determine which API tier to use (prefer Expanded)
        if self._expanded_key:
            self._api_tier = "expanded"
            self._api_key = self._expanded_key
            self._api_url = WOS_EXPANDED_API_URL
            self.MAX_LIMIT = 100
        elif self._starter_key:
            self._api_tier = "starter"
            self._api_key = self._starter_key
            self._api_url = WOS_STARTER_API_URL
            self.MAX_LIMIT = 50
        else:
            self._api_tier = None
            self._api_key = None
            self._api_url = None
            self.MAX_LIMIT = 50

        self._cache: dict = load_cache(self.name)
        register_cache(self.name, self._cache)

    def is_available(self) -> bool:
        """Web of Science requires an API key to be configured."""
        return bool(self._api_key)

    @cachedmethod(
        lambda self: self._cache,
        key=lambda self, query, limit=100, filters=None: (
            query,
            limit,
            filters.cache_key() if filters else "",
        ),
    )
    def search(
        self,
        query: str,
        limit: int = 100,
        filters: SearchFilters | None = None,
    ) -> list[Paper]:
        """Search Web of Science for papers matching the query."""
        if not self._api_key:
            return []

        logger.debug(f"wos: Searching for '{query}' with limit={limit}")

        if self._api_tier == "expanded":
            return self._search_expanded(query, limit, filters)
        else:
            return self._search_starter(query, limit, filters)

    def _format_query(self, query: str) -> str:
        """
        Format a query for the WoS APIs.

        Both Starter and Expanded APIs require field tags (e.g., TS=, TI=, AU=).
        If the query doesn't contain a field tag, wrap it with TS=()
        to search across topic fields (title, abstract, keywords).
        """
        if re.search(r"\b[A-Z]{2,3}=", query):
            return query
        return f"TS=({query})"

    def _search_starter(
        self,
        query: str,
        limit: int,
        filters: SearchFilters | None,
    ) -> list[Paper]:
        """
        Search using the WoS Starter API.

        Automatically fetches multiple pages if the requested limit exceeds
        the API's per-request maximum (50 results per page).
        """
        all_papers: list[Paper] = []
        page = 1
        page_size = 50  # Starter API max per page

        try:
            effective_query = self._format_query(query)
            if filters:
                if filters.year:
                    start, end = filters.year_range()
                    if start and end:
                        if start == end:
                            effective_query += f" AND PY={start}"
                        else:
                            effective_query += f" AND PY={start}-{end}"
                    elif start:
                        import datetime

                        current_year = datetime.datetime.now().year
                        effective_query += f" AND PY={start}-{current_year}"
                    elif end:
                        effective_query += f" AND PY=1900-{end}"
                if filters.venue:
                    effective_query += f' AND SO="{filters.venue}"'
                if filters.pub_types:
                    wos_types = []
                    type_mapping = {
                        "article": "Article",
                        "conference": "Proceedings Paper",
                        "review": "Review",
                        "book": "Book",
                    }
                    for pt in filters.pub_types:
                        if pt.lower() in type_mapping:
                            wos_types.append(type_mapping[pt.lower()])
                        else:
                            logger.warning(
                                "wos: Publication type '%s' not supported, ignoring",
                                pt,
                            )
                    if wos_types:
                        types_query = " OR ".join(
                            f'DT="{t}"' for t in wos_types
                        )
                        effective_query += f" AND ({types_query})"

                # Warn about unsupported filters in Starter API
                if filters.open_access:
                    logger.warning(
                        "wos: Open access filter not supported in Starter API, ignoring"
                    )
                if filters.min_citations is not None:
                    logger.warning(
                        "wos: Citation count filter not supported in Starter API, ignoring"
                    )

            while len(all_papers) < limit:
                # Calculate how many results we still need
                remaining = limit - len(all_papers)
                current_page_size = min(page_size, remaining)

                response = requests.get(
                    WOS_STARTER_API_URL,
                    params={
                        "q": effective_query,
                        "db": "WOS",
                        "limit": current_page_size,
                        "page": page,
                    },
                    headers={"X-ApiKey": self._api_key},
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()

                hits = data.get("hits", [])
                if not hits:
                    # No more results available
                    break

                all_papers.extend(
                    self._convert_starter_hit(hit) for hit in hits
                )
                page += 1

                # Check if we've fetched all available results
                metadata = data.get("metadata", {})
                total = metadata.get("total", 0)
                if len(all_papers) >= total:
                    break

            return all_papers
        except Exception as e:
            logger.warning("wos (starter): %s", e)
            return all_papers

    def _search_expanded(
        self,
        query: str,
        limit: int,
        filters: SearchFilters | None,
    ) -> list[Paper]:
        """
        Search using the WoS Expanded API.

        Automatically fetches multiple pages if the requested limit exceeds
        the API's per-request maximum (100 results per page).
        """
        all_papers: list[Paper] = []
        first_record = 1  # 1-indexed
        page_size = 100  # Expanded API max per page

        try:
            effective_query = self._format_query(query)
            if filters:
                if filters.year:
                    start, end = filters.year_range()
                    if start and end:
                        if start == end:
                            effective_query += f" AND PY={start}"
                        else:
                            effective_query += f" AND PY={start}-{end}"
                    elif start:
                        import datetime

                        current_year = datetime.datetime.now().year
                        effective_query += f" AND PY={start}-{current_year}"
                    elif end:
                        effective_query += f" AND PY=1900-{end}"
                if filters.venue:
                    effective_query += f' AND SO="{filters.venue}"'
                if filters.pub_types:
                    wos_types = []
                    type_mapping = {
                        "article": "Article",
                        "conference": "Proceedings Paper",
                        "review": "Review",
                        "book": "Book",
                    }
                    for pt in filters.pub_types:
                        if pt.lower() in type_mapping:
                            wos_types.append(type_mapping[pt.lower()])
                        else:
                            logger.warning(
                                "wos: Publication type '%s' not supported, ignoring",
                                pt,
                            )
                    if wos_types:
                        types_query = " OR ".join(
                            f'DT="{t}"' for t in wos_types
                        )
                        effective_query += f" AND ({types_query})"

                # Open access is supported in Expanded API via OA field
                if filters.open_access:
                    effective_query += " AND OA=(gold OR green OR bronze)"

                # Citation count filtering requires local filtering after results
                if filters.min_citations is not None:
                    logger.warning(
                        "wos: Citation count filter applied locally after search"
                    )

            while len(all_papers) < limit:
                # Calculate how many results we still need
                remaining = limit - len(all_papers)
                current_page_size = min(page_size, remaining)

                response = requests.get(
                    WOS_EXPANDED_API_URL,
                    params={
                        "databaseId": "WOS",
                        "usrQuery": effective_query,
                        "count": current_page_size,
                        "firstRecord": first_record,
                    },
                    headers={"X-ApiKey": self._api_key},
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()

                # Navigate the nested structure to get records
                # Use safe_get_nested to handle cases where intermediate fields are strings.
                records = safe_get_nested(
                    data, "Data", "Records", "records", "REC", default=[]
                )
                if not isinstance(records, list):
                    records = [records] if isinstance(records, dict) else []

                if not records:
                    # No more results available
                    break

                # Store query ID for potential citation report requests
                query_result = data.get("QueryResult", {})
                self._last_query_id = query_result.get("QueryID")

                all_papers.extend(
                    self._convert_expanded_hit(rec) for rec in records
                )
                first_record += len(records)

                # Check if we've fetched all available results
                total = query_result.get("RecordsFound", 0)
                if first_record > total:
                    break

            return all_papers
        except Exception as e:
            logger.warning("wos (expanded): %s", e)
            # Try falling back to Starter API if we have a starter key
            if self._starter_key and self._starter_key != self._expanded_key:
                logger.info("wos: Falling back to Starter API")
                self._api_tier = "starter"
                self._api_key = self._starter_key
                self._api_url = WOS_STARTER_API_URL
                self.MAX_LIMIT = 50
                return self._search_starter(query, limit, filters)
            return all_papers

    def _convert_starter_hit(self, hit: dict) -> Paper:
        """Convert a WoS Starter API hit to our Paper type."""
        source = hit.get("source", {})
        if not isinstance(source, dict):
            source = {}
        year = None
        pub_year = source.get("publishYear")
        if pub_year:
            try:
                year = int(pub_year)
            except (ValueError, TypeError):
                pass

        authors = []
        names = hit.get("names", {})
        if not isinstance(names, dict):
            names = {}
        for author in names.get("authors", []):
            if isinstance(author, dict):
                name = author.get("displayName")
                if name:
                    authors.append(name)

        identifiers = hit.get("identifiers", {})
        if not isinstance(identifiers, dict):
            identifiers = {}
        doi = identifiers.get("doi")

        links = hit.get("links", {})
        if not isinstance(links, dict):
            links = {}
        url = links.get("record")

        return Paper(
            title=hit.get("title", "") or "",
            authors=authors,
            year=year,
            doi=doi,
            abstract=None,  # Not available in Starter API
            venue=source.get("sourceTitle"),
            url=url,
            sources=[self.name],
        )

    def _convert_expanded_hit(self, rec: dict) -> Paper:
        """Convert a WoS Expanded API record to our Paper type."""
        static_data = rec.get("static_data", {})
        summary = static_data.get("summary", {})
        fullrecord = static_data.get("fullrecord_metadata", {})

        # Extract title (look for type="item")
        title = ""
        titles = ensure_list(
            safe_get_nested(summary, "titles", "title", default=[])
        )
        for t in titles:
            if isinstance(t, dict) and t.get("type") == "item":
                title = t.get("content", "")
                break
        if not title and titles:
            title = (
                titles[0].get("content", "")
                if isinstance(titles[0], dict)
                else ""
            )

        # Extract publication year
        year = None
        pub_year = safe_get_nested(
            summary, "pub_info", "pubyear", default=None
        )
        if pub_year:
            try:
                year = int(pub_year)
            except (ValueError, TypeError):
                pass

        # Extract authors
        authors = []
        names = ensure_list(
            safe_get_nested(summary, "names", "name", default=[])
        )
        for author in names:
            if isinstance(author, dict) and author.get("role") == "author":
                name = author.get("display_name") or author.get("full_name")
                if name:
                    authors.append(name)

        # Extract DOI from cluster_related identifiers
        doi = None
        dynamic_data = rec.get("dynamic_data", {})
        cluster = dynamic_data.get("cluster_related", {})
        identifiers = ensure_list(
            safe_get_nested(cluster, "identifiers", "identifier", default=[])
        )
        for ident in identifiers:
            if isinstance(ident, dict) and ident.get("type") == "doi":
                doi = ident.get("value")
                break

        # Extract abstract
        abstract = safe_get_nested(
            fullrecord,
            "abstracts",
            "abstract",
            "abstract_text",
            "p",
            default=None,
        )

        # Extract venue (source title)
        venue = None
        for t in titles:
            if isinstance(t, dict) and t.get("type") == "source":
                venue = t.get("content")
                break

        # Construct URL from UID
        uid = rec.get("UID", "")
        url = (
            f"https://www.webofscience.com/wos/woscc/full-record/{uid}"
            if uid
            else None
        )

        return Paper(
            title=title,
            authors=authors,
            year=year,
            doi=doi,
            abstract=abstract,
            venue=venue,
            url=url,
            sources=[self.name],
        )

    def _require_expanded_api(self, operation: str) -> None:
        """Raise an error if the Expanded API is not available."""
        if self._api_tier != "expanded":
            raise NotImplementedError(
                f"WoS {operation} requires the Expanded API. "
                f"Set WOS_EXPANDED_API_KEY environment variable."
            )

    def get_related_records(self, uid: str, limit: int = 10) -> list[Paper]:
        """
        Find records that share cited references with the given paper.

        Args:
            uid: Web of Science unique identifier (e.g., "WOS:000270372400005")
            limit: Maximum number of related records to return (1-100)

        Returns:
            List of related papers

        Raises:
            NotImplementedError: If Expanded API is not configured
        """
        self._require_expanded_api("get_related_records")

        try:
            response = requests.get(
                f"{WOS_EXPANDED_API_URL}/related",
                params={
                    "databaseId": "WOS",
                    "uniqueId": uid,
                    "count": min(limit, 100),
                    "firstRecord": 1,
                },
                headers={"X-ApiKey": self._api_key},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            # Use safe_get_nested to handle cases where intermediate fields are strings.
            records = safe_get_nested(
                data, "Data", "Records", "records", "REC", default=[]
            )
            if not isinstance(records, list):
                records = [records] if isinstance(records, dict) else []
            return [
                self._convert_expanded_hit(rec)
                for rec in records
                if isinstance(rec, dict)
            ]
        except NotImplementedError:
            raise
        except Exception as e:
            logger.warning("wos: get_related_records failed: %s", e)
            return []

    def get_citing_articles(self, uid: str, limit: int = 10) -> list[Paper]:
        """
        Find articles that cite the given paper.

        Args:
            uid: Web of Science unique identifier (e.g., "WOS:000270372400005")
            limit: Maximum number of citing articles to return (1-100)

        Returns:
            List of citing papers

        Raises:
            NotImplementedError: If Expanded API is not configured
        """
        self._require_expanded_api("get_citing_articles")

        # Check cache first
        cache_key = ("citing", uid, limit)
        if cache_key in self._cache:
            logger.info(f"wos: Cache hit for citing articles of {uid}")
            return self._cache[cache_key]

        logger.info(
            f"wos: Cache miss for citing articles of {uid}, fetching from API"
        )

        try:
            response = requests.get(
                f"{WOS_EXPANDED_API_URL}/citing",
                params={
                    "databaseId": "WOS",
                    "uniqueId": uid,
                    "count": min(limit, 100),
                    "firstRecord": 1,
                },
                headers={"X-ApiKey": self._api_key},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            # Use ensure_list because the API may return a single dict instead of
            # a list when there's only one citing article. Skip non-dict items.
            # Use safe_get_nested to handle cases where intermediate fields are strings.
            records = ensure_list(
                safe_get_nested(
                    data, "Data", "Records", "records", "REC", default=[]
                )
            )
            result = [
                self._convert_expanded_hit(rec)
                for rec in records
                if isinstance(rec, dict)
            ]
            self._cache[cache_key] = result
            return result
        except NotImplementedError:
            raise
        except Exception as e:
            logger.warning("wos: get_citing_articles failed: %s", e)
            return []

    def get_cited_references(self, uid: str, limit: int = 10) -> list[dict]:
        """
        Get references (bibliography) from a given paper.

        Args:
            uid: Web of Science unique identifier (e.g., "WOS:000270372400005")
            limit: Maximum number of references to return (1-100)

        Returns:
            List of reference dictionaries with fields:
            - uid: WOS UID of cited paper (if available)
            - citedAuthor: Author name
            - citedTitle: Title of cited work
            - citedWork: Source/journal name
            - year: Publication year
            - doi: DOI (if available)
            - timesCited: Citation count

        Raises:
            NotImplementedError: If Expanded API is not configured
        """
        self._require_expanded_api("get_cited_references")

        # Check cache first
        cache_key = ("references", uid, limit)
        if cache_key in self._cache:
            logger.info(f"wos: Cache hit for references of {uid}")
            return self._cache[cache_key]

        logger.info(
            f"wos: Cache miss for references of {uid}, fetching from API"
        )

        try:
            response = requests.get(
                f"{WOS_EXPANDED_API_URL}/references",
                params={
                    "databaseId": "WOS",
                    "uniqueId": uid,
                    "count": min(limit, 100),
                    "firstRecord": 1,
                },
                headers={"X-ApiKey": self._api_key},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            # References have a different structure than regular records.
            # Use ensure_list because the API may return a single dict or string
            # instead of a list when there's only one reference. We also skip any
            # non-dict items in the list (the API sometimes returns strings).
            references = ensure_list(data.get("Data", []))
            result = [
                {
                    "uid": ref.get("UID"),
                    "citedAuthor": ref.get("citedAuthor"),
                    "citedTitle": ref.get("citedTitle"),
                    "citedWork": ref.get("citedWork"),
                    "year": ref.get("year"),
                    "doi": ref.get("doi"),
                    "timesCited": ref.get("timesCited"),
                }
                for ref in references
                if isinstance(ref, dict)
            ]
            self._cache[cache_key] = result
            return result
        except NotImplementedError:
            raise
        except Exception as e:
            logger.warning("wos: get_cited_references failed: %s", e)
            return []

    def search_for_citation_report(
        self,
        query: str,
        limit: int = 100,
    ) -> dict | None:
        """
        Run a search and return citation statistics for the results.

        This method first performs a search to obtain a query ID, then fetches
        the citation report for that query.

        Args:
            query: Search query string
            limit: Maximum number of records to include in report (max 10000)

        Returns:
            Citation report dictionary with fields like:
            - TimesCited: Total citations
            - TimesCitedSansSelf: Citations excluding self-citations
            - AveragePerItem: Average citations per paper
            - AveragePerYear: Average citations per year
            - HValue: h-index for the result set
            - CitingYears: Breakdown by year
            Or None if the request fails

        Raises:
            NotImplementedError: If Expanded API is not configured
        """
        self._require_expanded_api("search_for_citation_report")

        try:
            # First, run a search to get a query ID
            response = requests.get(
                WOS_EXPANDED_API_URL,
                params={
                    "databaseId": "WOS",
                    "usrQuery": query,
                    "count": min(limit, 100),
                    "firstRecord": 1,
                },
                headers={"X-ApiKey": self._api_key},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            query_result = data.get("QueryResult", {})
            query_id = query_result.get("QueryID")

            if not query_id:
                logger.warning(
                    "wos: No query ID returned for citation report"
                )
                return None

            # Now fetch the citation report
            report_response = requests.get(
                f"{WOS_EXPANDED_API_URL}/citation-report/{query_id}",
                params={"reportLevel": "WOS"},
                headers={"X-ApiKey": self._api_key},
                timeout=30,
            )
            report_response.raise_for_status()
            report_data = report_response.json()

            # Return the first (WOS) report level
            if report_data and len(report_data) > 0:
                return report_data[0]
            return None
        except NotImplementedError:
            raise
        except Exception as e:
            logger.warning("wos: search_for_citation_report failed: %s", e)
            return None

    # Accept str | None to simplify calling code - callers can pass paper.doi
    # without checking for None first (see Semantic Scholar implementation notes).
    def get_paper_by_doi(self, doi: str | None) -> Paper | None:
        """
        Look up a paper by its DOI and return it with WOS metadata.

        This method searches WOS for the given DOI and returns the paper
        with its WOS UID stored, which is needed for citation operations.

        Args:
            doi: The DOI to look up (e.g., "10.1145/1234567.1234568").

        Returns:
            Paper if found, None otherwise. The paper will have WOS UID
            in its metadata if found via the Expanded API.
        """
        if not doi or not self._api_key:
            return None

        # Search by DOI using the DO= field tag
        query = f"DO={doi}"

        try:
            if self._api_tier == "expanded":
                papers = self._search_expanded(query, limit=1, filters=None)
            else:
                papers = self._search_starter(query, limit=1, filters=None)

            if papers:
                return papers[0]
            return None
        except Exception as e:
            logger.warning("wos: DOI lookup failed for %s: %s", doi, e)
            return None

    def _get_uid_for_doi(self, doi: str) -> str | None:
        """
        Get the WOS UID for a paper given its DOI.

        Args:
            doi: The DOI to look up.

        Returns:
            WOS UID string (e.g., "WOS:000123456789") or None if not found.
        """
        if not doi or not self._api_key:
            return None

        # Search by DOI using the DO= field tag
        query = f"DO={doi}"

        try:
            if self._api_tier == "expanded":
                response = requests.get(
                    WOS_EXPANDED_API_URL,
                    params={
                        "databaseId": "WOS",
                        "usrQuery": query,
                        "count": 1,
                        "firstRecord": 1,
                    },
                    headers={"X-ApiKey": self._api_key},
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()

                # Use safe_get_nested to handle cases where intermediate fields are strings.
                records = safe_get_nested(
                    data, "Data", "Records", "records", "REC", default=[]
                )
                if not isinstance(records, list):
                    records = [records] if isinstance(records, dict) else []
                if (
                    records
                    and len(records) > 0
                    and isinstance(records[0], dict)
                ):
                    return records[0].get("UID")
            else:
                # Starter API - search and extract UID from response
                response = requests.get(
                    WOS_STARTER_API_URL,
                    params={
                        "q": query,
                        "limit": 1,
                        "page": 1,
                    },
                    headers={"X-ApiKey": self._api_key},
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()

                hits = data.get("hits", [])
                if hits and len(hits) > 0:
                    return hits[0].get("uid")

            return None
        except Exception as e:
            logger.warning("wos: UID lookup failed for DOI %s: %s", doi, e)
            return None

    def get_paper_citations(
        self,
        paper_id: str,
        limit: int = 100,
    ) -> list[Paper]:
        """
        Get papers that cite the given paper.

        This method accepts either a WOS UID or a DOI. If a DOI is provided,
        it first looks up the WOS UID, then fetches citations.

        Args:
            paper_id: DOI or WOS UID (e.g., "10.1000/xyz" or "WOS:000123456").
            limit: Maximum number of citing papers to return.

        Returns:
            List of Paper objects that cite this paper.

        Raises:
            NotImplementedError: If Expanded API is not configured.
        """
        self._require_expanded_api("get_paper_citations")

        # Determine if this is a DOI or WOS UID
        if paper_id.startswith("WOS:"):
            uid = paper_id
        else:
            # Assume it's a DOI - look up the UID
            uid = self._get_uid_for_doi(paper_id)
            if not uid:
                logger.warning(
                    "wos: Could not find WOS UID for DOI %s", paper_id
                )
                return []

        return self.get_citing_articles(uid, limit)

    def get_paper_references(
        self,
        paper_id: str,
        limit: int = 100,
    ) -> list[Paper]:
        """
        Get papers referenced by the given paper.

        This method accepts either a WOS UID or a DOI. If a DOI is provided,
        it first looks up the WOS UID, then fetches references.

        Note: The WOS API returns reference metadata as dictionaries, not full
        Paper objects. We convert them to Paper objects with limited metadata.

        Args:
            paper_id: DOI or WOS UID (e.g., "10.1000/xyz" or "WOS:000123456").
            limit: Maximum number of referenced papers to return.

        Returns:
            List of Paper objects referenced by this paper.

        Raises:
            NotImplementedError: If Expanded API is not configured.
        """
        self._require_expanded_api("get_paper_references")

        # Determine if this is a DOI or WOS UID
        if paper_id.startswith("WOS:"):
            uid = paper_id
        else:
            # Assume it's a DOI - look up the UID
            uid = self._get_uid_for_doi(paper_id)
            if not uid:
                logger.warning(
                    "wos: Could not find WOS UID for DOI %s", paper_id
                )
                return []

        # Get references as dicts and convert to Papers
        ref_dicts = self.get_cited_references(uid, limit)

        papers = []
        for ref in ref_dicts:
            # Skip non-dict items (defensive check)
            if not isinstance(ref, dict):
                continue
            # Skip references without titles
            title = ref.get("citedTitle")
            if not title:
                continue

            # Convert reference dict to Paper
            # Parse author - may be "LastName, FirstName" format
            author = ref.get("citedAuthor", "")
            authors = [author] if author else []

            # Parse year
            year = None
            year_str = ref.get("year")
            if year_str:
                try:
                    year = int(year_str)
                except (ValueError, TypeError):
                    pass

            papers.append(
                Paper(
                    title=title,
                    authors=authors,
                    year=year,
                    doi=ref.get("doi"),
                    venue=ref.get("citedWork"),
                    sources=[self.name],
                )
            )

        return papers


# Register the provider on module import
register_provider(WebOfScienceProvider())


class IEEEXploreProvider:
    """Search provider for IEEE Xplore."""

    name = "ieee"
    MAX_LIMIT = 200  # IEEE API returns max 200 results per request

    def __init__(self, api_key: str | None = None):
        """
        Initialize the IEEE Xplore provider.

        Args:
            api_key: API key for IEEE Xplore API.
                     If not provided, uses IEEE_API_KEY environment variable.
        """
        self.api_key = api_key or os.environ.get("IEEE_API_KEY")
        self._cache: dict = load_cache(self.name)
        register_cache(self.name, self._cache)

    def is_available(self) -> bool:
        """IEEE Xplore requires an API key to be configured."""
        return bool(self.api_key)

    @cachedmethod(
        lambda self: self._cache,
        key=lambda self, query, limit=100, filters=None: (
            query,
            limit,
            filters.cache_key() if filters else "",
        ),
    )
    def search(
        self,
        query: str,
        limit: int = 100,
        filters: SearchFilters | None = None,
    ) -> list[Paper]:
        """
        Search IEEE Xplore for papers matching the query.

        Automatically fetches multiple pages if the requested limit exceeds
        the API's per-request maximum (200 results per page).
        """
        if not self.api_key:
            return []  # No API key configured

        logger.debug(f"ieee: Searching for '{query}' with limit={limit}")

        all_papers: list[Paper] = []
        start_record = 1  # 1-indexed
        page_size = 200  # IEEE API max per request

        try:
            while len(all_papers) < limit:
                # Calculate how many results we still need
                remaining = limit - len(all_papers)
                current_page_size = min(page_size, remaining)

                params = {
                    "querytext": query,
                    "max_records": current_page_size,
                    "start_record": start_record,
                    "apikey": self.api_key,
                }

                # Apply filters (IEEE supports some filters natively)
                if filters:
                    # Year filter: IEEE uses start_year and end_year parameters
                    if filters.year:
                        start, end = filters.year_range()
                        if start:
                            params["start_year"] = start
                        if end:
                            params["end_year"] = end

                    # Open access filter
                    if filters.open_access:
                        params["open_access"] = "true"

                    # Publication types: map to IEEE content_type values
                    if filters.pub_types:
                        ieee_types = []
                        type_mapping = {
                            "article": "Journals",
                            "conference": "Conferences",
                            "book": "Books",
                        }
                        for pt in filters.pub_types:
                            if pt.lower() in type_mapping:
                                ieee_types.append(type_mapping[pt.lower()])
                            else:
                                logger.warning(
                                    "ieee: Publication type '%s' not supported, ignoring",
                                    pt,
                                )
                        if ieee_types:
                            params["content_type"] = ieee_types[
                                0
                            ]  # IEEE only supports one type

                    # Warn about unsupported filters
                    if filters.venue:
                        logger.warning(
                            "ieee: Venue filter not supported, ignoring"
                        )
                    if filters.min_citations is not None:
                        logger.warning(
                            "ieee: Citation count filter not supported, ignoring"
                        )

                response = requests.get(
                    IEEE_API_URL,
                    params=params,
                    timeout=30,
                )
                if response.status_code != 200:
                    error_detail = response.headers.get(
                        "X-Error-Detail-Header", "Unknown error"
                    )
                    error_code = response.headers.get(
                        "X-Mashery-Error-Code", ""
                    )

                    if (
                        "DEVELOPER_INACTIVE" in error_code
                        or "Inactive" in error_detail
                    ):
                        logger.warning(
                            "ieee: Account inactive. "
                            "Visit https://developer.ieee.org/ to reactivate your API key. "
                            "Error: %s",
                            error_detail,
                        )
                    elif response.status_code == 403:
                        logger.warning(
                            "ieee: Access denied (HTTP 403). Error: %s. "
                            "Check your API key at https://developer.ieee.org/",
                            error_detail,
                        )
                    elif response.status_code == 429:
                        logger.warning(
                            "ieee: Rate limited (HTTP 429). "
                            "Wait before making more requests. Error: %s",
                            error_detail,
                        )
                    else:
                        logger.warning(
                            "ieee: API error (HTTP %d): %s",
                            response.status_code,
                            error_detail,
                        )
                    response.raise_for_status()
                data = response.json()

                articles = data.get("articles", [])
                if not articles:
                    # No more results available
                    break

                all_papers.extend(
                    self._convert_article(article) for article in articles
                )
                start_record += len(articles)

                # Check if we've fetched all available results
                total = data.get("total_records", 0)
                if start_record > total:
                    break

            logger.debug(f"ieee: Retrieved {len(all_papers)} papers")
            return all_papers
        except requests.exceptions.HTTPError:
            # Already logged with details in handle response errors
            return all_papers
        except Exception as e:
            logger.warning("ieee: %s", e)
            return all_papers

    def _convert_article(self, article: dict) -> Paper:
        """Convert an IEEE Xplore article to our Paper type."""
        # Extract publication year
        year = None
        pub_year = article.get("publication_year")
        if pub_year:
            try:
                year = int(pub_year)
            except (ValueError, TypeError):
                pass

        # Extract author names from authors object
        authors = []
        authors_data = article.get("authors", {}).get("authors", [])
        for author in authors_data:
            name = author.get("full_name")
            if name:
                authors.append(name)

        # Prefer html_url, fall back to abstract_url
        url = article.get("html_url") or article.get("abstract_url")

        return Paper(
            title=article.get("title", "") or "",
            authors=authors,
            year=year,
            doi=article.get("doi"),
            abstract=article.get("abstract"),
            venue=article.get("publication_title"),
            url=url,
            sources=[self.name],
        )


# Register the provider on module import
register_provider(IEEEXploreProvider())


class ArxivProvider:
    """Search provider for arXiv preprint server."""

    name = "arxiv"
    MAX_LIMIT: int | None = None  # No documented maximum
    MAX_RETRIES = 5
    INITIAL_BACKOFF = 3.0  # seconds

    def __init__(self):
        """Initialize the arXiv provider."""
        self._cache: dict = load_cache(self.name)
        register_cache(self.name, self._cache)
        # arxiv.Client handles rate limiting internally
        # We set num_retries=0 since we implement our own retry logic
        self._client = arxiv.Client(
            page_size=100,
            delay_seconds=3.0,
            num_retries=0,
        )

    def is_available(self) -> bool:
        """arXiv is always available (no API key required)."""
        return True

    def search(
        self,
        query: str,
        limit: int = 100,
        filters: SearchFilters | None = None,
    ) -> list[Paper]:
        """
        Search arXiv for papers matching the query.

        Only caches successful results. Failed requests are not cached,
        allowing immediate retry.
        """
        # Check cache first
        cache_key = (query, limit, filters.cache_key() if filters else "")
        if cache_key in self._cache:
            logger.debug(f"arxiv: Cache hit for '{query}'")
            return self._cache[cache_key]

        logger.debug(f"arxiv: Searching for '{query}' with limit={limit}")

        # Build query with filters
        effective_query = query
        if filters:
            # Category/venue filter: use arXiv category syntax
            if filters.venue:
                # User may specify "cs.AI" or just "cs"
                effective_query = f"cat:{filters.venue} AND ({query})"

            # Open access filter: arXiv is always open access
            if filters.open_access:
                logger.debug(
                    "arxiv: All papers are open access, filter has no effect"
                )

            # Publication types: arXiv only has preprints
            if filters.pub_types:
                # Only proceed if "preprint" is in the requested types
                if not any(
                    pt.lower() == "preprint" for pt in filters.pub_types
                ):
                    logger.warning(
                        "arxiv: Only preprints available, but requested types: %s",
                        filters.pub_types,
                    )

            # Minimum citations: not supported
            if filters.min_citations is not None:
                logger.warning("arxiv: Citation filtering not supported")

        search = arxiv.Search(
            query=effective_query,
            max_results=limit,
            sort_by=arxiv.SortCriterion.Relevance,
        )

        # Retry with exponential backoff
        last_exception: Exception | None = None

        for attempt in range(self.MAX_RETRIES):
            try:
                all_papers: list[Paper] = []
                for result in self._client.results(search):
                    paper = self._convert_result(result)
                    if filters and filters.year:
                        start_year, end_year = filters.year_range()
                        if paper.year:
                            if start_year and paper.year < start_year:
                                continue
                            if end_year and paper.year > end_year:
                                continue
                    all_papers.append(paper)

                logger.debug(f"arxiv: Retrieved {len(all_papers)} papers")

                # Only cache successful results
                if all_papers:
                    self._cache[cache_key] = all_papers

                return all_papers

            except (arxiv.HTTPError, arxiv.UnexpectedEmptyPageError) as e:
                last_exception = e
                if attempt < self.MAX_RETRIES - 1:
                    backoff = self.INITIAL_BACKOFF * (2**attempt)
                    logger.warning(
                        "arxiv: %s (attempt %d/%d, retrying in %.1fs)",
                        e,
                        attempt + 1,
                        self.MAX_RETRIES,
                        backoff,
                    )
                    time.sleep(backoff)
                else:
                    logger.warning(
                        "arxiv: %s (attempt %d/%d, giving up)",
                        e,
                        attempt + 1,
                        self.MAX_RETRIES,
                    )

            except Exception as e:
                # Non-retryable error
                logger.warning("arxiv: %s", e)
                return []

        # All retries exhausted
        return []

    def _convert_result(self, result: "arxiv.Result") -> Paper:
        """Convert an arXiv Result to our Paper type."""
        # Extract author names
        authors = [author.name for author in result.authors]

        # Extract year from published date
        year = result.published.year if result.published else None

        # Use provided DOI or derive from arXiv ID
        doi = result.doi
        if not doi and result.entry_id:
            # entry_id is like "http://arxiv.org/abs/2306.04338v1"
            arxiv_id = result.entry_id.split("/abs/")[-1]
            # Remove version suffix for DOI
            arxiv_id_base = (
                arxiv_id.split("v")[0] if "v" in arxiv_id else arxiv_id
            )
            if arxiv_id_base:
                doi = f"10.48550/arXiv.{arxiv_id_base}"

        # Extract primary category as venue
        venue = result.primary_category if result.primary_category else None

        return Paper(
            title=result.title or "",
            authors=authors,
            year=year,
            doi=doi,
            abstract=result.summary,
            venue=venue,
            url=result.entry_id,
            pdf_url=result.pdf_url,
            sources=[self.name],
        )

    def get_paper_citations(
        self,
        paper_id: str,
        limit: int = 100,
    ) -> list[Paper]:
        """
        Not supported by arXiv.

        arXiv does not provide citation data. Use Semantic Scholar or
        OpenAlex for citation information on arXiv papers.
        """
        raise NotImplementedError(
            "arXiv does not provide citation data. "
            "Use Semantic Scholar or OpenAlex instead."
        )

    def get_paper_references(
        self,
        paper_id: str,
        limit: int = 100,
    ) -> list[Paper]:
        """
        Not supported by arXiv.

        arXiv does not provide reference data. Use Semantic Scholar or
        OpenAlex for reference information on arXiv papers.
        """
        raise NotImplementedError(
            "arXiv does not provide reference data. "
            "Use Semantic Scholar or OpenAlex instead."
        )


# Register the provider on module import
register_provider(ArxivProvider())
