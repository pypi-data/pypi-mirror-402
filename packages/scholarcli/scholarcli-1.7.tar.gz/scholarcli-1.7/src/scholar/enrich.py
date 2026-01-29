"""
Paper enrichment using DOI lookups.

Fetches missing paper metadata (especially abstracts and PDF URLs) from providers
with better coverage like Semantic Scholar and OpenAlex.
"""

import logging
from typing import Callable

from scholar import Paper
from scholar.providers import get_provider
import json
import os
from dataclasses import replace
from pathlib import Path

import platformdirs

from scholar.notes import get_paper_id

logger = logging.getLogger(__name__)
# Providers that support DOI lookup and provide abstracts
ENRICHMENT_PROVIDERS = ["s2", "openalex"]

# Global cache for enriched paper data (refs/cites)
# Stored in data dir (not cache dir) since fetching refs/cites is expensive
ENRICHMENT_CACHE_DIR = "enrichment_cache"
# All fields that can be enriched via DOI lookup
ENRICHABLE_FIELDS = [
    "title",
    "authors",
    "abstract",
    "year",
    "venue",
    "pdf_url",
]


def enrich_paper(
    paper: Paper,
    fields: list[str] | None = None,
    fetch_refs_cites: bool = False,
) -> Paper:
    """
    Enrich a paper by fetching missing fields from other providers.

    This function fills in any missing metadata by looking up the paper's DOI
    in providers with better coverage. It's useful for:
    - Papers from DBLP/WOS that lack abstracts
    - Papers from snowballing that may only have a DOI
    - Any paper missing title, authors, abstract, year, venue, or pdf_url

    When [[fetch_refs_cites]] is True, also fetches references and citations
    if they are not already present on the paper. The refs/cites are stored
    directly on the Paper object, so they persist with any caching.

    Args:
        paper: The paper to enrich.
        fields: Fields to check and enrich. If None, checks all enrichable
            fields (title, authors, abstract, year, venue, pdf_url).
        fetch_refs_cites: If True, also fetch references and citations.

    Returns:
        A new Paper with enriched fields, or the original if enrichment
        fails or isn't needed.
    """
    if fields is None:
        fields = ENRICHABLE_FIELDS

    result = paper

    # Check if metadata enrichment is needed
    if needs_enrichment(paper, fields):
        # Need DOI for lookup
        if not paper.doi:
            logger.debug(
                f"Paper '{paper.title_preview()}' has no DOI, cannot enrich"
            )
        else:
            logger.debug(
                f"Enriching paper '{paper.title_preview()}' (DOI: {paper.doi})"
            )

            # Try each enrichment provider in order
            for provider_name in ENRICHMENT_PROVIDERS:
                provider = get_provider(provider_name)
                if provider is None:
                    continue

                if not hasattr(provider, "get_paper_by_doi"):
                    continue

                logger.debug(f"Trying to enrich from {provider_name}")
                enriched = provider.get_paper_by_doi(paper.doi)
                if enriched is None:
                    logger.debug(
                        f"{provider_name} returned no data for DOI {paper.doi}"
                    )
                    continue

                # Merge the enriched data into our paper
                # We want to keep our paper's existing data and fill in gaps
                logger.info(
                    f"Successfully enriched paper from {provider_name}"
                )
                result = paper.merge_with(enriched)
                break
    else:
        logger.debug(
            f"Paper '{paper.title_preview()}' doesn't need metadata enrichment"
        )

    # Fetch references and citations if requested
    if fetch_refs_cites and result.doi:
        result = _fetch_refs_cites(result)

    return result


def _get_enrichment_cache_dir() -> Path:
    """
    Return the directory for storing enriched paper data.

    Uses SCHOLAR_DATA_DIR if set, otherwise platform-appropriate data dir.
    Creates the directory if it doesn't exist.
    """
    data_dir = os.environ.get("SCHOLAR_DATA_DIR")
    if data_dir:
        path = Path(data_dir) / ENRICHMENT_CACHE_DIR
    else:
        path = (
            Path(platformdirs.user_data_dir("scholar")) / ENRICHMENT_CACHE_DIR
        )
    path.mkdir(parents=True, exist_ok=True)
    return path


def _safe_cache_filename(paper_id: str) -> str:
    """Convert a paper ID to a safe filename."""
    return paper_id.replace(":", "_").replace("/", "_")


def _load_cached_enrichment(
    paper: Paper,
) -> tuple[list[Paper] | None, list[Paper] | None]:
    """
    Load cached references and citations for a paper.

    Args:
        paper: The paper to load enrichment for.

    Returns:
        Tuple of (references, citations), each may be None if not cached.
    """
    paper_id = get_paper_id(paper)
    cache_file = (
        _get_enrichment_cache_dir() / f"{_safe_cache_filename(paper_id)}.json"
    )

    if not cache_file.exists():
        return None, None

    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        refs = None
        if "references" in data and data["references"] is not None:
            refs = [Paper.from_dict(p) for p in data["references"]]

        cites = None
        if "citations" in data and data["citations"] is not None:
            cites = [Paper.from_dict(p) for p in data["citations"]]

        logger.debug(f"Loaded cached enrichment for {paper.title_preview()}")
        return refs, cites
    except (json.JSONDecodeError, OSError, KeyError) as e:
        logger.debug(f"Failed to load cached enrichment: {e}")
        return None, None


def _save_cached_enrichment(
    paper: Paper,
    references: list[Paper] | None,
    citations: list[Paper] | None,
) -> None:
    """
    Save references and citations to the global cache.

    Args:
        paper: The paper these refs/cites belong to.
        references: List of reference papers, or None.
        citations: List of citing papers, or None.
    """
    paper_id = get_paper_id(paper)
    cache_file = (
        _get_enrichment_cache_dir() / f"{_safe_cache_filename(paper_id)}.json"
    )

    data = {
        "paper_id": paper_id,
        "title": paper.title,  # For debugging/inspection
        "doi": paper.doi,
    }

    if references is not None:
        data["references"] = [p.to_dict() for p in references]

    if citations is not None:
        data["citations"] = [p.to_dict() for p in citations]

    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.debug(f"Saved enrichment cache for {paper.title_preview()}")
    except OSError as e:
        logger.warning(f"Failed to save enrichment cache: {e}")


def _fetch_refs_cites(paper: Paper) -> Paper:
    """
    Fetch references and citations for a paper if not already present.

    Checks the global enrichment cache first. If not cached, fetches from
    the API and saves to the cache for future use.

    Args:
        paper: The paper to fetch refs/cites for (must have DOI).

    Returns:
        A new Paper with references and citations populated.
    """
    from scholar.providers import fetch_references, fetch_citations

    result = paper

    # Check global cache first
    cached_refs, cached_cites = _load_cached_enrichment(paper)

    # Track what we fetched (for saving to cache)
    fetched_refs = None
    fetched_cites = None

    # Use cached refs if available, otherwise fetch
    if result.references is None:
        if cached_refs is not None:
            logger.info(
                f"Using cached references for {result.title_preview()}"
            )
            result = replace(result, references=cached_refs)
        else:
            logger.info(f"Fetching references for {result.title_preview()}")
            try:
                refs = fetch_references(result.doi)
                # Enrich the references too (metadata only, no recursive refs/cites)
                refs = [enrich_paper(r, fetch_refs_cites=False) for r in refs]
                fetched_refs = refs  # Track for caching
                result = replace(result, references=refs)
                logger.info(f"Found {len(refs)} references")
            except Exception as e:
                logger.warning(f"Failed to fetch references: {e}")

    # Use cached cites if available, otherwise fetch
    if result.citations is None:
        if cached_cites is not None:
            logger.info(
                f"Using cached citations for {result.title_preview()}"
            )
            result = replace(result, citations=cached_cites)
        else:
            logger.info(f"Fetching citations for {result.title_preview()}")
            try:
                cites = fetch_citations(result.doi)
                # Enrich the citations too (metadata only, no recursive refs/cites)
                cites = [
                    enrich_paper(c, fetch_refs_cites=False) for c in cites
                ]
                fetched_cites = cites  # Track for caching
                result = replace(result, citations=cites)
                logger.info(f"Found {len(cites)} citations")
            except Exception as e:
                logger.warning(f"Failed to fetch citations: {e}")

    # Save newly fetched data to cache
    if fetched_refs is not None or fetched_cites is not None:
        # Load existing cache to merge (in case we only fetched one of refs/cites)
        existing_refs, existing_cites = _load_cached_enrichment(paper)
        save_refs = (
            fetched_refs if fetched_refs is not None else existing_refs
        )
        save_cites = (
            fetched_cites if fetched_cites is not None else existing_cites
        )
        _save_cached_enrichment(paper, save_refs, save_cites)

    return result


def needs_enrichment(paper: Paper, fields: list[str] | None = None) -> bool:
    """
    Check if a paper needs enrichment for the specified fields.

    Args:
        paper: The paper to check.
        fields: Fields to check. If None, checks all enrichable fields.

    Returns:
        True if any of the specified fields are missing or empty.
    """
    if fields is None:
        fields = ENRICHABLE_FIELDS

    for field in fields:
        value = getattr(paper, field, None)
        if value is None:
            return True
        if isinstance(value, str) and value.strip() == "":
            return True
        if isinstance(value, list) and len(value) == 0:
            return True
    return False


def enrich_papers(
    papers: list[Paper],
    fields: list[str] | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
) -> list[Paper]:
    """
    Enrich multiple papers.

    Args:
        papers: List of papers to enrich.
        fields: Fields to enrich. If None, enriches 'abstract' and 'pdf_url'.
        progress_callback: Called with (current, total) after each paper.

    Returns:
        List of enriched papers in the same order.
    """
    if fields is None:
        fields = ["abstract", "pdf_url"]

    logger.info(f"Starting batch enrichment of {len(papers)} papers")

    enriched = []
    total = len(papers)
    enriched_count = 0

    for i, paper in enumerate(papers):
        result = enrich_paper(paper, fields)
        if result != paper:  # Paper was enriched
            enriched_count += 1
        enriched.append(result)
        if progress_callback:
            progress_callback(i + 1, total)

    logger.info(
        f"Batch enrichment complete: {enriched_count}/{total} papers enriched"
    )
    return enriched
