"""
PDF download and caching for academic papers.

Provides functions to download, cache, and open PDFs from paper URLs.
The cache is content-addressed using SHA-256 hashes of URLs.
"""

from pathlib import Path
from typing import Any, Callable
import hashlib
import logging
import os
import subprocess
import sys

import platformdirs
import requests

logger = logging.getLogger(__name__)
PDF_CACHE_SUBDIR = "pdfs"


def get_pdf_cache_dir() -> Path:
    """
    Get the PDF cache directory, creating it if needed.

    The cache location can be overridden with the SCHOLAR_CACHE_DIR
    environment variable.

    Returns:
        Path to the PDF cache directory.
    """
    base_cache = os.environ.get("SCHOLAR_CACHE_DIR")
    if base_cache:
        cache_dir = Path(base_cache) / PDF_CACHE_SUBDIR
    else:
        cache_dir = (
            Path(platformdirs.user_cache_dir("scholar")) / PDF_CACHE_SUBDIR
        )
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_cached_pdf_path(url: str) -> Path:
    """
    Get the cache path for a PDF URL.

    Uses SHA-256 hash of the URL (truncated to 16 hex chars) as filename.
    This provides sufficient uniqueness while keeping paths readable.

    Args:
        url: The PDF URL.

    Returns:
        Path where this PDF would be cached.
    """
    url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
    return get_pdf_cache_dir() / f"{url_hash}.pdf"


def clear_pdf_cache() -> int:
    """
    Delete all cached PDFs.

    Returns:
        Number of PDF files deleted.
    """
    cache_dir = get_pdf_cache_dir()
    logger.info("Clearing PDF cache at %s", cache_dir)
    count = 0
    for pdf_file in cache_dir.glob("*.pdf"):
        try:
            pdf_file.unlink()
            count += 1
            logger.debug("Deleted cached PDF: %s", pdf_file.name)
        except OSError as e:
            logger.warning("Failed to delete %s: %s", pdf_file.name, e)
    logger.info("Deleted %d cached PDF files", count)
    return count


def get_pdf_cache_info() -> dict[str, int]:
    """
    Get information about the PDF cache.

    Returns:
        Dictionary with 'count' (number of files) and 'size_bytes' (total size).
    """
    cache_dir = get_pdf_cache_dir()
    count = 0
    size_bytes = 0
    for pdf_file in cache_dir.glob("*.pdf"):
        count += 1
        try:
            size_bytes += pdf_file.stat().st_size
        except OSError:
            pass
    return {"count": count, "size_bytes": size_bytes}


import re

DOI_PATTERN = re.compile(r"^10\.\d{4,}/[^\s]+$")
DOI_URL_PATTERN = re.compile(
    r"(?:https?://)?(?:dx\.)?doi\.org/(10\.\d{4,}/[^\s]+)"
)


def is_doi(identifier: str) -> bool:
    """
    Check if a string is a DOI.

    Accepts both raw DOIs (10.1234/example) and DOI URLs
    (https://doi.org/10.1234/example).

    Args:
        identifier: String to check.

    Returns:
        True if the string is a DOI or DOI URL.
    """
    identifier = identifier.strip()
    if DOI_PATTERN.match(identifier):
        return True
    if DOI_URL_PATTERN.match(identifier):
        return True
    return False


def extract_doi(identifier: str) -> str | None:
    """
    Extract the DOI from a string.

    Handles both raw DOIs and DOI URLs.

    Args:
        identifier: String potentially containing a DOI.

    Returns:
        The extracted DOI, or None if not a DOI.
    """
    identifier = identifier.strip()
    if DOI_PATTERN.match(identifier):
        return identifier
    match = DOI_URL_PATTERN.match(identifier)
    if match:
        return match.group(1)
    return None


UNPAYWALL_API = "https://api.unpaywall.org/v2/{doi}"
UNPAYWALL_EMAIL = "scholar-cli@example.com"  # Required by Unpaywall API


def resolve_doi_unpaywall(
    doi: str,
    progress_callback: Callable[[str], None] | None = None,
) -> str | None:
    """
    Resolve a DOI to a PDF URL using Unpaywall.

    Args:
        doi: The DOI to resolve.
        progress_callback: Optional callback for status messages.

    Returns:
        PDF URL if found, None otherwise.
    """
    logger.debug("Resolving DOI via Unpaywall: %s", doi)
    if progress_callback:
        progress_callback(f"Checking Unpaywall for {doi}...")

    try:
        url = UNPAYWALL_API.format(doi=doi)
        response = requests.get(
            url,
            params={"email": UNPAYWALL_EMAIL},
            timeout=10,
        )

        if response.status_code != 200:
            logger.debug(
                "Unpaywall returned status %d for DOI %s",
                response.status_code,
                doi,
            )
            return None

        data = response.json()

        # Try best_oa_location first
        best_oa = data.get("best_oa_location")
        if best_oa and best_oa.get("url_for_pdf"):
            logger.debug("Found PDF URL via Unpaywall best_oa_location")
            return best_oa["url_for_pdf"]

        # Fall back to any OA location with a PDF
        for location in data.get("oa_locations", []):
            if location.get("url_for_pdf"):
                logger.debug("Found PDF URL via Unpaywall oa_locations")
                return location["url_for_pdf"]

        logger.debug("No PDF URL found in Unpaywall response for DOI %s", doi)
        return None

    except Exception as e:
        logger.debug("Unpaywall request failed for DOI %s: %s", doi, e)
        return None


S2_PAPER_API = "https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}"


def resolve_doi_s2(
    doi: str,
    progress_callback: Callable[[str], None] | None = None,
) -> str | None:
    """
    Resolve a DOI to a PDF URL using Semantic Scholar.

    Args:
        doi: The DOI to resolve.
        progress_callback: Optional callback for status messages.

    Returns:
        PDF URL if found, None otherwise.
    """
    logger.debug("Resolving DOI via Semantic Scholar: %s", doi)
    if progress_callback:
        progress_callback(f"Checking Semantic Scholar for {doi}...")

    try:
        url = S2_PAPER_API.format(doi=doi)
        response = requests.get(
            url,
            params={"fields": "openAccessPdf"},
            timeout=10,
        )

        if response.status_code != 200:
            logger.debug(
                "Semantic Scholar returned status %d for DOI %s",
                response.status_code,
                doi,
            )
            return None

        data = response.json()
        oa_pdf = data.get("openAccessPdf")
        if oa_pdf and oa_pdf.get("url"):
            logger.debug("Found PDF URL via Semantic Scholar")
            return oa_pdf["url"]

        logger.debug(
            "No PDF URL found in Semantic Scholar response for DOI %s", doi
        )
        return None

    except Exception as e:
        logger.debug("Semantic Scholar request failed for DOI %s: %s", doi, e)
        return None


def resolve_doi_to_pdf(
    doi: str,
    progress_callback: Callable[[str], None] | None = None,
) -> str:
    """
    Resolve a DOI to a PDF URL.

    Tries multiple sources in order: Unpaywall, Semantic Scholar.

    Args:
        doi: The DOI to resolve.
        progress_callback: Optional callback for status messages.

    Returns:
        PDF URL.

    Raises:
        PDFDownloadError: If no PDF URL could be found.
    """
    logger.info("Resolving DOI to PDF: %s", doi)
    # Try Unpaywall first (best source for legal OA)
    url = resolve_doi_unpaywall(doi, progress_callback)
    if url:
        if progress_callback:
            progress_callback(f"Found PDF via Unpaywall")
        logger.info("Found PDF via Unpaywall for DOI %s", doi)
        return url

    # Try Semantic Scholar
    url = resolve_doi_s2(doi, progress_callback)
    if url:
        if progress_callback:
            progress_callback(f"Found PDF via Semantic Scholar")
        logger.info("Found PDF via Semantic Scholar for DOI %s", doi)
        return url

    # No PDF found
    logger.warning("Could not find open access PDF for DOI: %s", doi)
    raise PDFDownloadError(
        f"Could not find open access PDF for DOI: {doi}\n"
        f"The paper may not be available as open access."
    )


class PDFDownloadError(Exception):
    """
    Exception raised when PDF download fails.

    Contains a descriptive error message suitable for display to users.
    """

    pass


def download_pdf(
    url: str,
    progress_callback: Callable[[str], None] | None = None,
) -> Path:
    """
    Download a PDF to the cache if not already cached.

    Args:
        url: URL of the PDF to download.
        progress_callback: Optional callback for status messages.

    Returns:
        Path to the cached PDF file.

    Raises:
        PDFDownloadError: If download fails with descriptive message.
    """
    cache_path = get_cached_pdf_path(url)

    if cache_path.exists():
        logger.debug("PDF cache hit: %s", cache_path.name)
        if progress_callback:
            progress_callback(f"Using cached PDF: {cache_path}")
        return cache_path

    logger.info("Downloading PDF from %s", url)
    if progress_callback:
        progress_callback(f"Downloading PDF from {url}...")

    try:
        response = requests.get(url, timeout=30, stream=True)
        response.raise_for_status()

        # Validate content type
        content_type = response.headers.get("content-type", "")
        if (
            "pdf" not in content_type.lower()
            and "octet-stream" not in content_type.lower()
        ):
            logger.warning(
                "URL did not return PDF content-type: %s", content_type
            )
            raise PDFDownloadError(
                f"URL did not return a PDF. Content-Type: {content_type}\nURL: {url}"
            )

        # Stream to file
        with open(cache_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.debug("PDF downloaded and cached at %s", cache_path.name)
        if progress_callback:
            progress_callback("Download complete")

        return cache_path

    except requests.exceptions.HTTPError as e:
        logger.warning(
            "HTTP error downloading PDF: %s %s",
            e.response.status_code,
            e.response.reason,
        )
        raise PDFDownloadError(
            f"HTTP error {e.response.status_code}: {e.response.reason}\nURL: {url}"
        )
    except requests.exceptions.ConnectionError as e:
        logger.warning("Connection error downloading PDF: %s", e)
        raise PDFDownloadError(f"Connection error: {e}\nURL: {url}")
    except requests.exceptions.Timeout:
        logger.warning("Timeout downloading PDF from %s", url)
        raise PDFDownloadError(
            f"Request timed out after 30 seconds\nURL: {url}"
        )
    except requests.exceptions.RequestException as e:
        logger.warning("Request failed downloading PDF: %s", e)
        raise PDFDownloadError(f"Request failed: {e}\nURL: {url}")


def get_pdf(
    source: Any,
    progress_callback: Callable[[str], None] | None = None,
) -> Path:
    """
    Get a PDF, downloading if necessary.

    This is the main entry point for PDF access. It accepts:
    - A Paper object (using its pdf_url or doi attributes)
    - A DOI string (resolved via Unpaywall/Semantic Scholar)
    - A direct URL string

    Args:
        source: A Paper object, DOI string, or URL string.
        progress_callback: Optional callback for status messages.

    Returns:
        Path to the cached PDF file.

    Raises:
        PDFDownloadError: If download fails or no PDF available.
    """
    url: str | None = None

    if isinstance(source, str):
        # Check if it's a DOI
        doi = extract_doi(source)
        if doi:
            logger.debug("Source is a DOI: %s", doi)
            if progress_callback:
                progress_callback(f"Resolving DOI: {doi}")
            url = resolve_doi_to_pdf(doi, progress_callback)
        else:
            # Assume it's a URL
            logger.debug("Source is a URL: %s", source)
            url = source
    else:
        # Assume it's a Paper object
        paper_title = getattr(source, "title", "Unknown")
        logger.debug("Getting PDF for paper: %s", paper_title)
        # Try pdf_url first, then doi
        url = getattr(source, "pdf_url", None)
        if not url:
            doi = getattr(source, "doi", None)
            if doi:
                logger.debug("Paper has no pdf_url, trying DOI: %s", doi)
                if progress_callback:
                    progress_callback(f"Resolving DOI: {doi}")
                url = resolve_doi_to_pdf(doi, progress_callback)
        if not url:
            logger.warning("Paper has no PDF URL or DOI: %s", paper_title)
            raise PDFDownloadError(
                f"Paper has no PDF URL or DOI: {paper_title}"
            )

    return download_pdf(url, progress_callback)


def open_pdf(path: Path) -> bool:
    """
    Open a PDF with the system default viewer.

    Uses platform-appropriate commands:
    - macOS: open
    - Windows: start
    - Linux/other: xdg-open

    Args:
        path: Path to the PDF file.

    Returns:
        True if the viewer was launched successfully, False otherwise.
    """
    logger.debug("Opening PDF: %s", path)
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=True)
        elif sys.platform == "win32":
            os.startfile(str(path))  # type: ignore
        else:
            subprocess.run(["xdg-open", str(path)], check=True)
        logger.debug("Successfully launched PDF viewer")
        return True
    except Exception as e:
        logger.warning("Failed to open PDF viewer: %s", e)
        return False
