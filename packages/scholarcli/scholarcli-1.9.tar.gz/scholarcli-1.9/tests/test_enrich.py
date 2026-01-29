"""Tests for the enrich module."""
import pytest
from unittest.mock import Mock, patch, MagicMock

from scholar import Paper
from scholar.enrich import *
from scholar.enrich import (
    _save_cached_enrichment,
    _load_cached_enrichment,
    _fetch_refs_cites,
    _get_enrichment_cache_dir,
    _safe_cache_filename,
)


class TestEnrichmentCache:
    """Tests for global enrichment cache."""

    def test_save_and_load_cached_enrichment(self, tmp_path, monkeypatch):
        """Can save and load refs/cites from cache."""
        monkeypatch.setenv("SCHOLAR_DATA_DIR", str(tmp_path))

        paper = Paper(
            title="Test Paper",
            authors=["Author"],
            doi="10.1234/test",
        )

        refs = [
            Paper(title="Reference 1", authors=["Ref Author"], doi="10.1/ref1"),
            Paper(title="Reference 2", authors=["Ref Author 2"], doi="10.1/ref2"),
        ]
        cites = [
            Paper(title="Citing Paper", authors=["Cite Author"], doi="10.1/cite1"),
        ]

        _save_cached_enrichment(paper, refs, cites)

        loaded_refs, loaded_cites = _load_cached_enrichment(paper)

        assert loaded_refs is not None
        assert len(loaded_refs) == 2
        assert loaded_refs[0].title == "Reference 1"
        assert loaded_refs[1].doi == "10.1/ref2"

        assert loaded_cites is not None
        assert len(loaded_cites) == 1
        assert loaded_cites[0].title == "Citing Paper"

    def test_load_nonexistent_returns_none(self, tmp_path, monkeypatch):
        """Loading from empty cache returns None, None."""
        monkeypatch.setenv("SCHOLAR_DATA_DIR", str(tmp_path))

        paper = Paper(
            title="Unknown Paper",
            authors=["Author"],
            doi="10.1234/unknown",
        )

        refs, cites = _load_cached_enrichment(paper)
        assert refs is None
        assert cites is None

    def test_fetch_refs_cites_uses_cache(self, tmp_path, monkeypatch):
        """_fetch_refs_cites returns cached data instead of fetching."""
        monkeypatch.setenv("SCHOLAR_DATA_DIR", str(tmp_path))

        paper = Paper(
            title="Cached Paper",
            authors=["Author"],
            doi="10.1234/cached",
        )

        # Pre-populate cache
        cached_refs = [Paper(title="Cached Ref", authors=[], doi="10.1/cached_ref")]
        cached_cites = [Paper(title="Cached Cite", authors=[], doi="10.1/cached_cite")]
        _save_cached_enrichment(paper, cached_refs, cached_cites)

        # Mock fetch functions to ensure they're not called
        with patch("scholar.providers.fetch_references") as mock_fetch_refs, \
             patch("scholar.providers.fetch_citations") as mock_fetch_cites:
            result = _fetch_refs_cites(paper)

        # Should NOT have called the fetch functions
        mock_fetch_refs.assert_not_called()
        mock_fetch_cites.assert_not_called()

        # Should have used cached data
        assert result.references is not None
        assert len(result.references) == 1
        assert result.references[0].title == "Cached Ref"
        assert result.citations is not None
        assert len(result.citations) == 1
        assert result.citations[0].title == "Cached Cite"

    def test_fetch_refs_cites_saves_to_cache(self, tmp_path, monkeypatch):
        """_fetch_refs_cites saves fetched data to cache."""
        monkeypatch.setenv("SCHOLAR_DATA_DIR", str(tmp_path))

        paper = Paper(
            title="New Paper",
            authors=["Author"],
            doi="10.1234/new",
        )

        fetched_refs = [Paper(title="Fetched Ref", authors=[], doi="10.1/fetched")]
        fetched_cites = [Paper(title="Fetched Cite", authors=[], doi="10.1/cite")]

        with patch("scholar.providers.fetch_references", return_value=fetched_refs), \
             patch("scholar.providers.fetch_citations", return_value=fetched_cites):
            result = _fetch_refs_cites(paper)

        # Verify data was returned
        assert result.references is not None
        assert result.citations is not None

        # Verify data was cached
        cached_refs, cached_cites = _load_cached_enrichment(paper)
        assert cached_refs is not None
        assert len(cached_refs) == 1
        assert cached_refs[0].title == "Fetched Ref"
        assert cached_cites is not None
        assert len(cached_cites) == 1
        assert cached_cites[0].title == "Fetched Cite"

    def test_cache_persists_across_sessions(self, tmp_path, monkeypatch):
        """Cached enrichment persists when simulating new session."""
        monkeypatch.setenv("SCHOLAR_DATA_DIR", str(tmp_path))

        paper = Paper(
            title="Persistent Paper",
            authors=["Author"],
            doi="10.1234/persist",
        )

        refs = [Paper(title="Persistent Ref", authors=[], doi="10.1/pref")]
        _save_cached_enrichment(paper, refs, None)

        # Simulate new session by creating new Paper object with same DOI
        paper2 = Paper(
            title="Persistent Paper",
            authors=["Author"],
            doi="10.1234/persist",
        )

        loaded_refs, loaded_cites = _load_cached_enrichment(paper2)
        assert loaded_refs is not None
        assert loaded_refs[0].title == "Persistent Ref"
        assert loaded_cites is None

    def test_partial_cache_only_refs(self, tmp_path, monkeypatch):
        """Can cache only refs without cites."""
        monkeypatch.setenv("SCHOLAR_DATA_DIR", str(tmp_path))

        paper = Paper(
            title="Partial Paper",
            authors=["Author"],
            doi="10.1234/partial",
        )

        refs = [Paper(title="Only Ref", authors=[], doi="10.1/only")]
        _save_cached_enrichment(paper, refs, None)

        loaded_refs, loaded_cites = _load_cached_enrichment(paper)
        assert loaded_refs is not None
        assert len(loaded_refs) == 1
        assert loaded_cites is None
class TestEnrichPaper:
    """Tests for enrich_paper function."""

    def test_enriches_missing_abstract(self):
        """enrich_paper fills in missing abstract."""
        paper = Paper(
            title="Test Paper",
            authors=["Author"],
            doi="10.1234/test",
            sources=["dblp"]
        )

        enriched_paper = Paper(
            title="Test Paper",
            authors=["Author"],
            doi="10.1234/test",
            abstract="This is the abstract",
            sources=["s2"]
        )

        mock_provider = MagicMock()
        mock_provider.get_paper_by_doi.return_value = enriched_paper

        with patch("scholar.enrich.get_provider", return_value=mock_provider):
            result = enrich_paper(paper)

        assert result.abstract == "This is the abstract"
        assert "dblp" in result.sources
        assert "s2" in result.sources

    def test_returns_original_if_no_doi(self):
        """enrich_paper returns original paper if no DOI."""
        paper = Paper(title="Test Paper", authors=["Author"])
        result = enrich_paper(paper)
        assert result is paper

    def test_returns_original_if_already_complete(self):
        """enrich_paper returns original if fields are already filled."""
        paper = Paper(
            title="Test Paper",
            authors=["Author"],
            doi="10.1234/test",
            year=2024,
            venue="Conference",
            abstract="Already has abstract",
            pdf_url="https://example.com/paper.pdf"
        )

        mock_provider = MagicMock()
        with patch("scholar.enrich.get_provider", return_value=mock_provider):
            result = enrich_paper(paper)

        # Should not have called the provider
        mock_provider.get_paper_by_doi.assert_not_called()
        assert result is paper

    def test_tries_fallback_provider(self):
        """enrich_paper tries fallback if first provider fails."""
        paper = Paper(
            title="Test Paper",
            authors=["Author"],
            doi="10.1234/test"
        )

        first_provider = MagicMock()
        first_provider.get_paper_by_doi.return_value = None  # Not found

        second_provider = MagicMock()
        second_provider.get_paper_by_doi.return_value = Paper(
            title="Test Paper",
            authors=["Author"],
            doi="10.1234/test",
            abstract="Found in second provider",
            sources=["openalex"]
        )

        def mock_get_provider(name):
            if name == "s2":
                return first_provider
            elif name == "openalex":
                return second_provider
            return None

        with patch("scholar.enrich.get_provider", side_effect=mock_get_provider):
            result = enrich_paper(paper)

        assert result.abstract == "Found in second provider"

    def test_returns_original_if_no_provider_finds(self):
        """enrich_paper returns original if no provider can enrich."""
        paper = Paper(
            title="Test Paper",
            authors=["Author"],
            doi="10.1234/test"
        )

        mock_provider = MagicMock()
        mock_provider.get_paper_by_doi.return_value = None

        with patch("scholar.enrich.get_provider", return_value=mock_provider):
            result = enrich_paper(paper)

        assert result is paper


class TestNeedsEnrichment:
    """Tests for needs_enrichment helper."""

    def test_needs_enrichment_missing_abstract(self):
        """Paper with missing abstract needs enrichment."""
        paper = Paper(title="Test", authors=["Author"], abstract=None)
        assert needs_enrichment(paper, ["abstract"]) is True

    def test_needs_enrichment_empty_abstract(self):
        """Paper with empty abstract needs enrichment."""
        paper = Paper(title="Test", authors=["Author"], abstract="")
        assert needs_enrichment(paper, ["abstract"]) is True

    def test_needs_enrichment_empty_authors(self):
        """Paper with empty authors list needs enrichment."""
        paper = Paper(title="Test", authors=[], abstract="Has abstract")
        assert needs_enrichment(paper, ["authors"]) is True

    def test_no_enrichment_if_complete(self):
        """Paper with filled fields doesn't need enrichment."""
        paper = Paper(title="Test", authors=["Author"], abstract="Has abstract")
        assert needs_enrichment(paper, ["abstract"]) is False

    def test_uses_all_fields_by_default(self):
        """needs_enrichment checks all enrichable fields when none specified."""
        # Paper missing abstract but has everything else
        paper = Paper(
            title="Test",
            authors=["Author"],
            year=2024,
            venue="Conference",
            pdf_url="https://example.com/paper.pdf",
            abstract=None  # Missing
        )
        assert needs_enrichment(paper) is True

    def test_complete_paper_needs_no_enrichment(self):
        """Paper with all fields filled doesn't need enrichment."""
        paper = Paper(
            title="Test",
            authors=["Author"],
            year=2024,
            venue="Conference",
            pdf_url="https://example.com/paper.pdf",
            abstract="Has abstract"
        )
        assert needs_enrichment(paper) is False
class TestEnrichPapers:
    """Tests for enrich_papers function."""

    def test_enriches_all_papers(self):
        """enrich_papers processes all papers in list."""
        papers = [
            Paper(title="Paper 1", authors=[], doi="10.1/a"),
            Paper(title="Paper 2", authors=[], doi="10.1/b"),
        ]

        def make_enriched(doi):
            return Paper(
                title="Enriched",
                authors=[],
                doi=doi,
                abstract=f"Abstract for {doi}",
                sources=["s2"]
            )

        mock_provider = MagicMock()
        mock_provider.get_paper_by_doi.side_effect = lambda doi: make_enriched(doi)

        with patch("scholar.enrich.get_provider", return_value=mock_provider):
            result = enrich_papers(papers)

        assert len(result) == 2
        assert result[0].abstract == "Abstract for 10.1/a"
        assert result[1].abstract == "Abstract for 10.1/b"

    def test_calls_progress_callback(self):
        """enrich_papers calls progress callback."""
        papers = [
            Paper(title="Paper 1", authors=[]),
            Paper(title="Paper 2", authors=[]),
        ]

        progress_calls = []

        def track_progress(current, total):
            progress_calls.append((current, total))

        # Papers without DOI won't be enriched
        result = enrich_papers(papers, progress_callback=track_progress)

        assert progress_calls == [(1, 2), (2, 2)]

    def test_preserves_order(self):
        """enrich_papers preserves paper order."""
        papers = [
            Paper(title="First", authors=[]),
            Paper(title="Second", authors=[]),
            Paper(title="Third", authors=[]),
        ]

        result = enrich_papers(papers)

        assert result[0].title == "First"
        assert result[1].title == "Second"
        assert result[2].title == "Third"
