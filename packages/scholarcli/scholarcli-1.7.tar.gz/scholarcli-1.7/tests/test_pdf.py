"""Tests for the PDF module."""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from scholar.pdf import *


class TestPDFCache:
    """Tests for PDF cache functions."""

    def test_get_pdf_cache_dir_creates_directory(self, tmp_path, monkeypatch):
        """Cache directory is created if it doesn't exist."""
        cache_dir = tmp_path / "scholar_cache"
        monkeypatch.setenv("SCHOLAR_CACHE_DIR", str(cache_dir))
        
        result = get_pdf_cache_dir()
        
        assert result == cache_dir / PDF_CACHE_SUBDIR
        assert result.exists()

    def test_get_cached_pdf_path_deterministic(self):
        """Same URL always produces same cache path."""
        url = "https://example.com/paper.pdf"
        path1 = get_cached_pdf_path(url)
        path2 = get_cached_pdf_path(url)
        assert path1 == path2

    def test_get_cached_pdf_path_different_urls(self):
        """Different URLs produce different cache paths."""
        url1 = "https://example.com/paper1.pdf"
        url2 = "https://example.com/paper2.pdf"
        path1 = get_cached_pdf_path(url1)
        path2 = get_cached_pdf_path(url2)
        assert path1 != path2

    def test_clear_pdf_cache(self, tmp_path, monkeypatch):
        """Can clear all cached PDFs."""
        monkeypatch.setenv("SCHOLAR_CACHE_DIR", str(tmp_path))
        
        cache_dir = get_pdf_cache_dir()
        (cache_dir / "test1.pdf").write_bytes(b"pdf1")
        (cache_dir / "test2.pdf").write_bytes(b"pdf2")
        
        count = clear_pdf_cache()
        
        assert count == 2
        assert len(list(cache_dir.glob("*.pdf"))) == 0

    def test_get_pdf_cache_info(self, tmp_path, monkeypatch):
        """Can get cache statistics."""
        monkeypatch.setenv("SCHOLAR_CACHE_DIR", str(tmp_path))
        
        cache_dir = get_pdf_cache_dir()
        (cache_dir / "test1.pdf").write_bytes(b"x" * 100)
        (cache_dir / "test2.pdf").write_bytes(b"y" * 200)
        
        info = get_pdf_cache_info()
        
        assert info["count"] == 2
        assert info["size_bytes"] == 300
class TestDOIResolution:
    """Tests for DOI resolution functions."""

    def test_is_doi_raw(self):
        """Recognizes raw DOI format."""
        assert is_doi("10.1234/test.paper")
        assert is_doi("10.48550/arXiv.2301.00001")

    def test_is_doi_url(self):
        """Recognizes DOI URLs."""
        assert is_doi("https://doi.org/10.1234/test")
        assert is_doi("http://dx.doi.org/10.1234/test")
        assert is_doi("doi.org/10.1234/test")

    def test_is_doi_false(self):
        """Rejects non-DOIs."""
        assert not is_doi("https://example.com/paper.pdf")
        assert not is_doi("not a doi")
        assert not is_doi("10.123/short")  # Too short registrant

    def test_extract_doi_raw(self):
        """Extracts raw DOI."""
        assert extract_doi("10.1234/test.paper") == "10.1234/test.paper"

    def test_extract_doi_from_url(self):
        """Extracts DOI from URL."""
        assert extract_doi("https://doi.org/10.1234/test") == "10.1234/test"
        assert extract_doi("http://dx.doi.org/10.5678/paper") == "10.5678/paper"

    def test_extract_doi_none(self):
        """Returns None for non-DOIs."""
        assert extract_doi("not a doi") is None
        assert extract_doi("https://example.com") is None

    def test_resolve_doi_unpaywall(self, monkeypatch):
        """Unpaywall resolution finds PDF URL."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "best_oa_location": {"url_for_pdf": "https://example.com/paper.pdf"}
        }
        
        with patch("scholar.pdf.requests.get", return_value=mock_response):
            url = resolve_doi_unpaywall("10.1234/test")
        
        assert url == "https://example.com/paper.pdf"

    def test_resolve_doi_s2(self, monkeypatch):
        """Semantic Scholar resolution finds PDF URL."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "openAccessPdf": {"url": "https://arxiv.org/pdf/2301.00001.pdf"}
        }
        
        with patch("scholar.pdf.requests.get", return_value=mock_response):
            url = resolve_doi_s2("10.1234/test")
        
        assert url == "https://arxiv.org/pdf/2301.00001.pdf"

    def test_resolve_doi_to_pdf_tries_sources(self, monkeypatch):
        """Combined resolution tries multiple sources."""
        # First call (Unpaywall) fails, second (S2) succeeds
        mock_response_fail = Mock()
        mock_response_fail.status_code = 404
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "openAccessPdf": {"url": "https://example.com/paper.pdf"}
        }
        
        with patch("scholar.pdf.requests.get", side_effect=[
            mock_response_fail, mock_response_success
        ]):
            url = resolve_doi_to_pdf("10.1234/test")
        
        assert url == "https://example.com/paper.pdf"

    def test_resolve_doi_to_pdf_no_pdf_raises(self):
        """Raises error when no PDF found."""
        mock_response = Mock()
        mock_response.status_code = 404
        
        with patch("scholar.pdf.requests.get", return_value=mock_response):
            with pytest.raises(PDFDownloadError) as exc_info:
                resolve_doi_to_pdf("10.1234/no-pdf")
        
        assert "Could not find open access PDF" in str(exc_info.value)
class TestPDFDownload:
    """Tests for PDF download functions."""

    def test_download_pdf_caches_result(self, tmp_path, monkeypatch):
        """Downloaded PDF is cached."""
        monkeypatch.setenv("SCHOLAR_CACHE_DIR", str(tmp_path))
        
        # Mock requests.get
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "application/pdf"}
        mock_response.iter_content.return_value = [b"PDF content"]
        
        with patch("scholar.pdf.requests.get", return_value=mock_response):
            path = download_pdf("https://example.com/paper.pdf")
        
        assert path.exists()
        assert path.read_bytes() == b"PDF content"

    def test_download_pdf_uses_cache(self, tmp_path, monkeypatch):
        """Second download uses cached file."""
        monkeypatch.setenv("SCHOLAR_CACHE_DIR", str(tmp_path))
        
        # Pre-create cached file
        url = "https://example.com/cached.pdf"
        cache_path = get_cached_pdf_path(url)
        cache_path.write_bytes(b"Cached PDF")
        
        # Should not make HTTP request
        with patch("scholar.pdf.requests.get") as mock_get:
            path = download_pdf(url)
            mock_get.assert_not_called()
        
        assert path == cache_path

    def test_download_pdf_validates_content_type(self, tmp_path, monkeypatch):
        """Rejects non-PDF content types."""
        monkeypatch.setenv("SCHOLAR_CACHE_DIR", str(tmp_path))
        
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "text/html"}
        
        with patch("scholar.pdf.requests.get", return_value=mock_response):
            with pytest.raises(PDFDownloadError) as exc_info:
                download_pdf("https://example.com/not-a-pdf")
        
        assert "did not return a PDF" in str(exc_info.value)

    def test_get_pdf_from_paper(self, tmp_path, monkeypatch):
        """get_pdf works with Paper objects."""
        monkeypatch.setenv("SCHOLAR_CACHE_DIR", str(tmp_path))
        
        paper = Mock()
        paper.pdf_url = "https://example.com/paper.pdf"
        paper.title = "Test Paper"
        
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "application/pdf"}
        mock_response.iter_content.return_value = [b"PDF"]
        
        with patch("scholar.pdf.requests.get", return_value=mock_response):
            path = get_pdf(paper)
        
        assert path.exists()

    def test_get_pdf_from_url_string(self, tmp_path, monkeypatch):
        """get_pdf works with URL strings."""
        monkeypatch.setenv("SCHOLAR_CACHE_DIR", str(tmp_path))
        
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "application/pdf"}
        mock_response.iter_content.return_value = [b"PDF"]
        
        with patch("scholar.pdf.requests.get", return_value=mock_response):
            path = get_pdf("https://example.com/paper.pdf")
        
        assert path.exists()

    def test_get_pdf_no_url_raises_error(self):
        """get_pdf raises error when paper has no PDF URL or DOI."""
        paper = Mock()
        paper.pdf_url = None
        paper.doi = None
        paper.title = "No PDF Paper"
        
        with pytest.raises(PDFDownloadError) as exc_info:
            get_pdf(paper)
        
        assert "no PDF URL or DOI" in str(exc_info.value)
class TestOpenPDF:
    """Tests for PDF open function."""

    def test_open_pdf_macos(self, tmp_path, monkeypatch):
        """Uses 'open' command on macOS."""
        monkeypatch.setattr(sys, "platform", "darwin")
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"PDF")
        
        with patch("scholar.pdf.subprocess.run") as mock_run:
            mock_run.return_value = None
            result = open_pdf(pdf_path)
        
        assert result is True
        mock_run.assert_called_once()
        assert "open" in mock_run.call_args[0][0]

    def test_open_pdf_linux(self, tmp_path, monkeypatch):
        """Uses 'xdg-open' command on Linux."""
        monkeypatch.setattr(sys, "platform", "linux")
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"PDF")
        
        with patch("scholar.pdf.subprocess.run") as mock_run:
            mock_run.return_value = None
            result = open_pdf(pdf_path)
        
        assert result is True
        mock_run.assert_called_once()
        assert "xdg-open" in mock_run.call_args[0][0]

    def test_open_pdf_failure_returns_false(self, tmp_path, monkeypatch):
        """Returns False when open command fails."""
        monkeypatch.setattr(sys, "platform", "linux")
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"PDF")
        
        with patch("scholar.pdf.subprocess.run", side_effect=Exception("Failed")):
            result = open_pdf(pdf_path)
        
        assert result is False
