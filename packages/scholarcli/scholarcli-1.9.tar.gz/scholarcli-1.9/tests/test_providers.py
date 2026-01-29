"""Tests for the providers module."""
import pytest
import requests
from unittest.mock import Mock, patch

from scholar import *
from scholar.providers import *


class TestProviderRegistry:
    """Tests for the provider registry."""

    def test_s2_registered(self):
        """Semantic Scholar provider is auto-registered."""
        provider = get_provider("s2")
        assert provider is not None
        assert provider.name == "s2"

    def test_openalex_registered(self):
        """OpenAlex provider is auto-registered."""
        provider = get_provider("openalex")
        assert provider is not None
        assert provider.name == "openalex"

    def test_dblp_registered(self):
        """DBLP provider is auto-registered."""
        provider = get_provider("dblp")
        assert provider is not None
        assert provider.name == "dblp"

    def test_wos_registered(self):
        """Web of Science provider is auto-registered."""
        provider = get_provider("wos")
        assert provider is not None
        assert provider.name == "wos"

    def test_ieee_registered(self):
        """IEEE Xplore provider is auto-registered."""
        provider = get_provider("ieee")
        assert provider is not None
        assert provider.name == "ieee"

    def test_get_all_providers(self):
        """get_all_providers returns registered providers."""
        providers = get_all_providers()
        assert len(providers) >= 5
        names = [p.name for p in providers]
        assert "s2" in names
        assert "openalex" in names
        assert "dblp" in names
        assert "wos" in names
        assert "ieee" in names

    def test_get_unknown_provider(self):
        """get_provider returns None for unknown providers."""
        assert get_provider("unknown_provider") is None

    def test_providers_have_max_limit(self):
        """All providers have MAX_LIMIT attribute."""
        for name, provider in PROVIDERS.items():
            assert hasattr(provider, "MAX_LIMIT"), f"{name} missing MAX_LIMIT"

    def test_get_provider_limits(self):
        """get_provider_limits returns correct limits."""
        limits = get_provider_limits()
        assert limits["s2"] is None
        assert limits["openalex"] is None
        assert limits["dblp"] == 1000
        # WoS limit depends on API tier: 50 for Starter, 100 for Expanded
        assert limits["wos"] in (50, 100)
        assert limits["ieee"] == 200
class TestDefaultProviders:
    """Tests for get_default_providers functionality."""

    def test_get_default_providers_returns_list(self):
        """get_default_providers returns a list of providers."""
        defaults = get_default_providers()
        assert isinstance(defaults, list)

    def test_default_providers_are_available(self):
        """All default providers report is_available() as True."""
        for provider in get_default_providers():
            assert provider.is_available() is True

    def test_always_available_providers_in_defaults(self):
        """Providers that don't require API keys are always in defaults."""
        defaults = get_default_providers()
        default_names = [p.name for p in defaults]
        # These providers don't require API keys
        assert "s2" in default_names
        assert "openalex" in default_names
        assert "dblp" in default_names

    def test_wos_in_defaults_only_with_key(self, monkeypatch):
        """WoS is in defaults only when API keys are set."""
        # Without any keys
        monkeypatch.delenv("WOS_API_KEY", raising=False)
        monkeypatch.delenv("WOS_STARTER_API_KEY", raising=False)
        monkeypatch.delenv("WOS_EXPANDED_API_KEY", raising=False)
        # Re-register provider without keys
        wos_provider = WebOfScienceProvider(
            starter_api_key=None, expanded_api_key=None
        )
        register_provider(wos_provider)
        defaults = get_default_providers()
        assert "wos" not in [p.name for p in defaults]

    def test_ieee_in_defaults_only_with_key(self, monkeypatch):
        """IEEE is in defaults only when IEEE_API_KEY is set."""
        # Without key
        monkeypatch.delenv("IEEE_API_KEY", raising=False)
        # Re-register provider without key
        ieee_provider = IEEEXploreProvider(api_key=None)
        ieee_provider.api_key = None
        register_provider(ieee_provider)  # type: ignore[arg-type]
        defaults = get_default_providers()
        assert "ieee" not in [p.name for p in defaults]
class TestSemanticScholarProvider:
    """Tests for the SemanticScholar provider."""

    def test_is_available_always_true(self):
        """Semantic Scholar is available without API key."""
        provider = SemanticScholarProvider(api_key=None)
        provider.api_key = None  # Ensure no key
        assert provider.is_available() is True

    def test_search_converts_papers(self):
        """search() converts API results to Paper objects."""
        provider = SemanticScholarProvider()

        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "total": 1,
            "data": [{
                "paperId": "abc123",
                "title": "Test Paper",
                "authors": [{"name": "Alice"}, {"name": "Bob"}],
                "year": 2024,
                "externalIds": {"DOI": "10.1234/test"},
                "abstract": "Test abstract",
                "venue": "Test Conference",
                "url": "https://example.com/paper",
                "openAccessPdf": {
                    "url": "https://arxiv.org/pdf/1234.5678.pdf",
                    "status": "GREEN",
                },
            }]
        }

        with patch.object(provider._session, "get", return_value=mock_response):
            results = provider.search("test query")

            assert len(results) == 1
            paper = results[0]
            assert isinstance(paper, Paper)
            assert paper.title == "Test Paper"
            assert paper.year == 2024
            assert paper.doi == "10.1234/test"
            assert paper.sources == ["s2"]
            assert "Alice" in paper.authors
            assert "Bob" in paper.authors
            assert paper.pdf_url == "https://arxiv.org/pdf/1234.5678.pdf"

    def test_search_handles_empty_results(self):
        """search() returns empty list when no results."""
        provider = SemanticScholarProvider()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"total": 0, "data": []}

        with patch.object(provider._session, "get", return_value=mock_response):
            results = provider.search("obscure query")
            assert results == []

    def test_search_handles_api_error(self):
        """search() returns empty list on API error."""
        provider = SemanticScholarProvider()

        with patch.object(provider._session, "get") as mock_get:
            mock_get.side_effect = Exception("API error")

            results = provider.search("test")
            assert results == []

    def test_search_handles_rate_limit(self):
        """search() returns empty list on rate limit (429)."""
        provider = SemanticScholarProvider()

        mock_response = Mock()
        mock_response.status_code = 429

        with patch.object(provider._session, "get", return_value=mock_response):
            results = provider.search("test")
            assert results == []

    def test_rate_limiting_with_api_key(self):
        """Provider uses faster rate limit when API key is set."""
        provider = SemanticScholarProvider(api_key="test-key")
        assert provider._min_request_interval == 1.0

    def test_rate_limiting_without_api_key(self):
        """Provider uses slower rate limit without API key."""
        with patch.dict(os.environ, {}, clear=True):
            # Ensure no S2_API_KEY in environment
            if "S2_API_KEY" in os.environ:
                del os.environ["S2_API_KEY"]
            provider = SemanticScholarProvider(api_key=None)
            # Force api_key to None even if env var exists
            provider.api_key = None
            assert provider._min_request_interval == 3.0


class TestSemanticScholarGetPaperByDoi:
    """Tests for SemanticScholar DOI lookup."""

    def test_get_paper_by_doi_returns_paper(self):
        """get_paper_by_doi() returns a Paper when found."""
        provider = SemanticScholarProvider()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "paperId": "abc123",
            "title": "Test Paper",
            "authors": [{"name": "Alice"}],
            "year": 2024,
            "externalIds": {"DOI": "10.1234/test"},
            "abstract": "This is the abstract",
            "venue": "Test Conference",
            "url": "https://example.com/paper",
        }

        with patch.object(provider._session, "get", return_value=mock_response):
            paper = provider.get_paper_by_doi("10.1234/test")

            assert paper is not None
            assert paper.title == "Test Paper"
            assert paper.abstract == "This is the abstract"
            assert paper.doi == "10.1234/test"
            assert paper.sources == ["s2"]

    def test_get_paper_by_doi_returns_none_on_404(self):
        """get_paper_by_doi() returns None when paper not found."""
        provider = SemanticScholarProvider()

        mock_response = Mock()
        mock_response.status_code = 404

        with patch.object(provider._session, "get", return_value=mock_response):
            paper = provider.get_paper_by_doi("10.1234/nonexistent")
            assert paper is None

    def test_get_paper_by_doi_returns_none_on_empty_doi(self):
        """get_paper_by_doi() returns None for empty DOI."""
        provider = SemanticScholarProvider()
        assert provider.get_paper_by_doi("") is None
        assert provider.get_paper_by_doi(None) is None

    def test_get_paper_by_doi_handles_rate_limit(self):
        """get_paper_by_doi() returns None on rate limit."""
        provider = SemanticScholarProvider()

        mock_response = Mock()
        mock_response.status_code = 429

        with patch.object(provider._session, "get", return_value=mock_response):
            paper = provider.get_paper_by_doi("10.1234/test")
            assert paper is None

    def test_get_paper_by_doi_caches_results(self):
        """get_paper_by_doi() caches successful lookups."""
        provider = SemanticScholarProvider()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "paperId": "abc123",
            "title": "Test Paper",
            "authors": [],
            "externalIds": {"DOI": "10.1234/test"},
        }

        with patch.object(provider._session, "get", return_value=mock_response) as mock_get:
            # First call
            paper1 = provider.get_paper_by_doi("10.1234/test")
            # Second call should use cache
            paper2 = provider.get_paper_by_doi("10.1234/test")

            assert mock_get.call_count == 1  # Only one API call
            assert paper1 is not None
            assert paper2 is not None
            assert paper1.title == paper2.title


class TestSemanticScholarPagination:
    """Tests for Semantic Scholar pagination."""

    def test_search_fetches_multiple_pages(self):
        """search() fetches multiple pages when limit exceeds page size."""
        provider = SemanticScholarProvider()

        # Create responses for two pages
        page1_response = Mock()
        page1_response.status_code = 200
        page1_response.json.return_value = {
            "total": 150,
            "data": [{"title": f"Paper {i}", "authors": []} for i in range(100)],
        }

        page2_response = Mock()
        page2_response.status_code = 200
        page2_response.json.return_value = {
            "total": 150,
            "data": [{"title": f"Paper {i}", "authors": []} for i in range(100, 150)],
        }

        with patch.object(
            provider._session, "get", side_effect=[page1_response, page2_response]
        ) as mock_get:
            results = provider.search("test query", limit=150)

            assert len(results) == 150
            assert mock_get.call_count == 2
            # Verify offset was used correctly
            calls = mock_get.call_args_list
            assert calls[0][1]["params"]["offset"] == 0
            assert calls[1][1]["params"]["offset"] == 100

    def test_search_stops_when_no_more_results(self):
        """search() stops pagination when API returns empty data."""
        provider = SemanticScholarProvider()

        page1_response = Mock()
        page1_response.status_code = 200
        page1_response.json.return_value = {
            "total": 50,
            "data": [{"title": f"Paper {i}", "authors": []} for i in range(50)],
        }

        page2_response = Mock()
        page2_response.status_code = 200
        page2_response.json.return_value = {"total": 50, "data": []}

        with patch.object(
            provider._session, "get", side_effect=[page1_response, page2_response]
        ):
            results = provider.search("test query", limit=200)

            # Should stop after getting 50 results even though limit is 200
            assert len(results) == 50

    def test_search_returns_partial_results_on_rate_limit(self):
        """search() returns collected results when rate limited mid-pagination."""
        provider = SemanticScholarProvider()

        page1_response = Mock()
        page1_response.status_code = 200
        page1_response.json.return_value = {
            "total": 200,
            "data": [{"title": f"Paper {i}", "authors": []} for i in range(100)],
        }

        page2_response = Mock()
        page2_response.status_code = 429  # Rate limited

        with patch.object(
            provider._session, "get", side_effect=[page1_response, page2_response]
        ):
            results = provider.search("test query", limit=200)

            # Should return partial results from first page
            assert len(results) == 100


class TestSemanticScholarIntegration:
    """Integration test for the SemanticScholar provider."""

    @pytest.mark.integration
    @pytest.mark.skip(reason="Skipped by default due to API rate limits")
    def test_real_api_call(self):
        """Make one real API call to verify the provider works."""
        try:
            provider = SemanticScholarProvider()
            papers = provider.search("machine learning", limit=1)
            assert len(papers) >= 1, "Provider returned no results"

            paper = papers[0]
            assert isinstance(paper, Paper)
            assert paper.title
            assert paper.sources == ["s2"]
        except Exception as e:
            pytest.skip(f"Semantic Scholar API unavailable: {e}")
class TestOpenAlexProvider:
    """Tests for the OpenAlex provider."""

    def test_is_available_always_true(self):
        """OpenAlex is available without email."""
        provider = OpenAlexProvider(email=None)
        assert provider.is_available() is True

    def test_search_converts_works(self):
        """search() converts API results to Paper objects."""
        provider = OpenAlexProvider()

        # Create mock work (OpenAlex returns dicts)
        mock_work = {
            "title": "Test Paper",
            "authorships": [
                {"author": {"display_name": "Alice"}},
                {"author": {"display_name": "Bob"}},
            ],
            "publication_year": 2024,
            "doi": "https://doi.org/10.1234/test",
            "abstract": "Test abstract",
            "primary_location": {
                "source": {"display_name": "Test Journal"}
            },
            "id": "https://openalex.org/W123456",
        }

        with patch("pyalex.Works") as mock_works:
            # paginate() returns an iterator of pages, where each page is a list
            mock_works.return_value.search.return_value.paginate.return_value = [
                [mock_work]  # Single page with one result
            ]

            results = provider.search("test query")

            assert len(results) == 1
            paper = results[0]
            assert isinstance(paper, Paper)
            assert paper.title == "Test Paper"
            assert paper.authors == ["Alice", "Bob"]
            assert paper.year == 2024
            assert paper.doi == "10.1234/test"
            assert paper.venue == "Test Journal"
            assert paper.sources == ["openalex"]

    def test_search_handles_empty_results(self):
        """search() returns empty list when no results."""
        provider = OpenAlexProvider()

        with patch("pyalex.Works") as mock_works:
            # paginate() returns an iterator of pages - empty list means no pages
            mock_works.return_value.search.return_value.paginate.return_value = []

            results = provider.search("obscure query")
            assert results == []

    def test_search_handles_api_error(self):
        """search() returns empty list on API error."""
        provider = OpenAlexProvider()

        with patch("pyalex.Works") as mock_works:
            mock_works.return_value.search.side_effect = Exception("API error")

            results = provider.search("test")
            assert results == []

    def test_handles_missing_fields(self):
        """search() handles works with missing optional fields."""
        provider = OpenAlexProvider()

        # Minimal work with only required fields
        mock_work = {
            "title": "Minimal Paper",
            "authorships": [],
        }

        with patch("pyalex.Works") as mock_works:
            # paginate() returns an iterator of pages
            mock_works.return_value.search.return_value.paginate.return_value = [
                [mock_work]  # Single page with one result
            ]

            results = provider.search("test")

            assert len(results) == 1
            paper = results[0]
            assert paper.title == "Minimal Paper"
            assert paper.authors == []
            assert paper.year is None
            assert paper.doi is None


class TestOpenAlexGetPaperByDoi:
    """Tests for OpenAlex DOI lookup."""

    def test_get_paper_by_doi_returns_paper(self):
        """get_paper_by_doi() returns a Paper when found."""
        provider = OpenAlexProvider()

        mock_work = {
            "title": "Test Paper",
            "authorships": [{"author": {"display_name": "Alice"}}],
            "publication_year": 2024,
            "doi": "https://doi.org/10.1234/test",
            "abstract": "This is the abstract",
            "id": "https://openalex.org/W123456",
        }

        with patch("pyalex.Works") as mock_works:
            mock_works.return_value.__getitem__.return_value = mock_work

            paper = provider.get_paper_by_doi("10.1234/test")

            assert paper is not None
            assert paper.title == "Test Paper"
            assert paper.abstract == "This is the abstract"
            assert paper.doi == "10.1234/test"
            assert paper.sources == ["openalex"]

    def test_get_paper_by_doi_returns_none_when_not_found(self):
        """get_paper_by_doi() returns None when paper not found."""
        provider = OpenAlexProvider()

        with patch("pyalex.Works") as mock_works:
            mock_works.return_value.__getitem__.return_value = None

            paper = provider.get_paper_by_doi("10.1234/nonexistent")
            assert paper is None

    def test_get_paper_by_doi_returns_none_on_empty_doi(self):
        """get_paper_by_doi() returns None for empty DOI."""
        provider = OpenAlexProvider()
        assert provider.get_paper_by_doi("") is None
        assert provider.get_paper_by_doi(None) is None

    def test_get_paper_by_doi_handles_exception(self):
        """get_paper_by_doi() returns None on API error."""
        provider = OpenAlexProvider()

        with patch("pyalex.Works") as mock_works:
            mock_works.return_value.__getitem__.side_effect = Exception("API error")

            paper = provider.get_paper_by_doi("10.1234/test")
            assert paper is None

    def test_get_paper_by_doi_caches_results(self):
        """get_paper_by_doi() caches successful lookups."""
        provider = OpenAlexProvider()

        mock_work = {
            "title": "Test Paper",
            "authorships": [],
            "doi": "https://doi.org/10.1234/test",
        }

        with patch("pyalex.Works") as mock_works:
            mock_works.return_value.__getitem__.return_value = mock_work

            # First call
            paper1 = provider.get_paper_by_doi("10.1234/test")
            # Second call should use cache
            paper2 = provider.get_paper_by_doi("10.1234/test")

            assert mock_works.return_value.__getitem__.call_count == 1  # Only one API call
            assert paper1 is not None
            assert paper2 is not None
            assert paper1.title == paper2.title


class TestOpenAlexIntegration:
    """Integration test for the OpenAlex provider."""

    @pytest.mark.integration
    @pytest.mark.skip(reason="Skipped by default to avoid API calls")
    def test_real_api_call(self):
        """Make one real API call to verify the provider works."""
        provider = OpenAlexProvider()

        try:
            papers = provider.search("machine learning", limit=1)

            assert len(papers) >= 1, "Provider returned no results"

            paper = papers[0]
            assert isinstance(paper, Paper)
            assert paper.title
            assert paper.sources == ["openalex"]
        except Exception as e:
            pytest.skip(f"OpenAlex API unavailable: {e}")
class TestDBLPProvider:
    """Tests for the DBLP provider."""

    def test_is_available_always_true(self):
        """DBLP is available (no credentials needed)."""
        provider = DBLPProvider()
        assert provider.is_available() is True

    def test_search_converts_publications(self):
        """search() converts API results to Paper objects."""
        provider = DBLPProvider()

        mock_response = Mock()
        mock_response.json.return_value = {
            "result": {
                "hits": {
                    "hit": [{
                        "info": {
                            "title": "Test Paper",
                            "authors": {
                                "author": [
                                    {"text": "Alice"},
                                    {"text": "Bob"},
                                ]
                            },
                            "year": "2024",
                            "venue": "ICSE",
                            "doi": "10.1234/test",
                            "url": "https://dblp.org/rec/conf/icse/Test24",
                        }
                    }]
                }
            }
        }
        mock_response.raise_for_status = Mock()

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_response

            results = provider.search("test query")

            assert len(results) == 1
            paper = results[0]
            assert isinstance(paper, Paper)
            assert paper.title == "Test Paper"
            assert paper.authors == ["Alice", "Bob"]
            assert paper.year == 2024
            assert paper.doi == "10.1234/test"
            assert paper.venue == "ICSE"
            assert paper.sources == ["dblp"]

    def test_search_handles_single_author(self):
        """search() handles single author as dict instead of list."""
        provider = DBLPProvider()

        mock_response = Mock()
        mock_response.json.return_value = {
            "result": {
                "hits": {
                    "hit": [{
                        "info": {
                            "title": "Solo Paper",
                            "authors": {"author": {"text": "Solo Author"}},
                            "year": "2024",
                        }
                    }]
                }
            }
        }
        mock_response.raise_for_status = Mock()

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_response

            results = provider.search("test")

            assert len(results) == 1
            assert results[0].authors == ["Solo Author"]

    def test_search_handles_empty_results(self):
        """search() returns empty list when no results."""
        provider = DBLPProvider()

        mock_response = Mock()
        mock_response.json.return_value = {
            "result": {"hits": {"hit": []}}
        }
        mock_response.raise_for_status = Mock()

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_response

            results = provider.search("obscure query")
            assert results == []

    def test_search_handles_api_error(self):
        """search() returns empty list on API error."""
        provider = DBLPProvider()

        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception("API error")

            results = provider.search("test")
            assert results == []

    def test_handles_missing_fields(self):
        """search() handles publications with missing optional fields."""
        provider = DBLPProvider()

        mock_response = Mock()
        mock_response.json.return_value = {
            "result": {
                "hits": {
                    "hit": [{
                        "info": {"title": "Minimal Paper"}
                    }]
                }
            }
        }
        mock_response.raise_for_status = Mock()

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_response

            results = provider.search("test")

            assert len(results) == 1
            paper = results[0]
            assert paper.title == "Minimal Paper"
            assert paper.authors == []
            assert paper.year is None
            assert paper.doi is None
            assert paper.abstract is None

    def test_respects_limit_parameter(self):
        """search() passes limit to API."""
        provider = DBLPProvider()

        mock_response = Mock()
        mock_response.json.return_value = {"result": {"hits": {"hit": [], "@total": "0"}}}
        mock_response.raise_for_status = Mock()

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_response

            provider.search("test", limit=50)

            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert call_args[1]["params"]["h"] == 50

    def test_fetches_multiple_pages(self):
        """search() fetches multiple pages when limit exceeds page size."""
        provider = DBLPProvider()

        # Create responses for two pages
        page1_response = Mock()
        page1_response.json.return_value = {
            "result": {
                "hits": {
                    "@total": "1500",
                    "hit": [{"info": {"title": f"Paper {i}"}} for i in range(1000)],
                }
            }
        }
        page1_response.raise_for_status = Mock()

        page2_response = Mock()
        page2_response.json.return_value = {
            "result": {
                "hits": {
                    "@total": "1500",
                    "hit": [{"info": {"title": f"Paper {i}"}} for i in range(1000, 1500)],
                }
            }
        }
        page2_response.raise_for_status = Mock()

        with patch("requests.get", side_effect=[page1_response, page2_response]) as mock_get:
            results = provider.search("test", limit=1500)

            assert len(results) == 1500
            assert mock_get.call_count == 2
            # Verify offset was used correctly
            calls = mock_get.call_args_list
            assert calls[0][1]["params"]["f"] == 0
            assert calls[1][1]["params"]["f"] == 1000

    def test_stops_when_total_reached(self):
        """search() stops pagination when all results have been fetched."""
        provider = DBLPProvider()

        page1_response = Mock()
        page1_response.json.return_value = {
            "result": {
                "hits": {
                    "@total": "50",
                    "hit": [{"info": {"title": f"Paper {i}"}} for i in range(50)],
                }
            }
        }
        page1_response.raise_for_status = Mock()

        with patch("requests.get", return_value=page1_response) as mock_get:
            results = provider.search("test", limit=200)

            # Should stop after first page since total (50) < limit (200)
            assert len(results) == 50
            assert mock_get.call_count == 1


class TestDBLPIntegration:
    """Integration test for the DBLP provider."""

    @pytest.mark.integration
    @pytest.mark.skip(reason="Skipped by default to avoid API calls")
    def test_real_api_call(self):
        """Make one real API call to verify the provider works."""
        provider = DBLPProvider()

        try:
            papers = provider.search("machine learning", limit=1)

            assert len(papers) >= 1, "Provider returned no results"

            paper = papers[0]
            assert isinstance(paper, Paper)
            assert paper.title
            assert paper.sources == ["dblp"]
        except Exception as e:
            pytest.skip(f"DBLP API unavailable: {e}")
class TestWebOfScienceProvider:
    """Tests for the Web of Science provider."""

    def test_is_available_false_without_key(self):
        """Web of Science is unavailable without any API key."""
        provider = WebOfScienceProvider(
            starter_api_key=None, expanded_api_key=None
        )
        assert provider.is_available() is False

    def test_is_available_true_with_starter_key(self):
        """Web of Science is available with Starter API key."""
        provider = WebOfScienceProvider(
            starter_api_key="test_key", expanded_api_key=None
        )
        assert provider.is_available() is True
        assert provider._api_tier == "starter"

    def test_is_available_true_with_expanded_key(self):
        """Web of Science is available with Expanded API key."""
        provider = WebOfScienceProvider(
            starter_api_key=None, expanded_api_key="test_key"
        )
        assert provider.is_available() is True
        assert provider._api_tier == "expanded"

    def test_prefers_expanded_when_both_keys_available(self):
        """Provider prefers Expanded API when both keys are set."""
        provider = WebOfScienceProvider(
            starter_api_key="starter_key",
            expanded_api_key="expanded_key",
        )
        assert provider._api_tier == "expanded"
        assert provider._api_key == "expanded_key"
        assert provider.MAX_LIMIT == 100

    def test_uses_starter_when_only_starter_key(self):
        """Provider uses Starter API when only starter key is set."""
        provider = WebOfScienceProvider(
            starter_api_key="starter_key", expanded_api_key=None
        )
        assert provider._api_tier == "starter"
        assert provider._api_key == "starter_key"
        assert provider.MAX_LIMIT == 50

    def test_legacy_wos_api_key_sets_both(self, monkeypatch):
        """Legacy WOS_API_KEY environment variable is tried with both APIs."""
        monkeypatch.setenv("WOS_API_KEY", "legacy_key")
        monkeypatch.delenv("WOS_STARTER_API_KEY", raising=False)
        monkeypatch.delenv("WOS_EXPANDED_API_KEY", raising=False)

        provider = WebOfScienceProvider()

        # Should prefer expanded (tries legacy key as expanded first)
        assert provider._api_tier == "expanded"
        assert provider._expanded_key == "legacy_key"
        assert provider._starter_key == "legacy_key"

    def test_search_returns_empty_without_api_key(self):
        """search() returns empty list when no API key is configured."""
        provider = WebOfScienceProvider(
            starter_api_key=None, expanded_api_key=None
        )
        results = provider.search("test")
        assert results == []
class TestWebOfScienceStarterAPI:
    """Tests for Web of Science Starter API."""

    def test_search_converts_documents(self):
        """search() converts Starter API results to Paper objects."""
        provider = WebOfScienceProvider(
            starter_api_key="test_key", expanded_api_key=None
        )

        mock_response = Mock()
        mock_response.json.return_value = {
            "hits": [{
                "title": "Test Paper",
                "names": {
                    "authors": [
                        {"displayName": "Alice Smith"},
                        {"displayName": "Bob Jones"},
                    ]
                },
                "source": {
                    "sourceTitle": "Nature",
                    "publishYear": "2024",
                },
                "identifiers": {"doi": "10.1234/test"},
                "links": {"record": "https://wos.com/record/123"},
            }]
        }
        mock_response.raise_for_status = Mock()

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_response

            results = provider.search("test query")

            assert len(results) == 1
            paper = results[0]
            assert isinstance(paper, Paper)
            assert paper.title == "Test Paper"
            assert paper.authors == ["Alice Smith", "Bob Jones"]
            assert paper.year == 2024
            assert paper.doi == "10.1234/test"
            assert paper.venue == "Nature"
            assert paper.abstract is None  # Starter API has no abstracts
            assert paper.sources == ["wos"]

    def test_search_handles_empty_results(self):
        """search() returns empty list when no results."""
        provider = WebOfScienceProvider(
            starter_api_key="test_key", expanded_api_key=None
        )

        mock_response = Mock()
        mock_response.json.return_value = {"hits": []}
        mock_response.raise_for_status = Mock()

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_response

            results = provider.search("obscure query")
            assert results == []

    def test_search_handles_api_error(self):
        """search() returns empty list on API error."""
        provider = WebOfScienceProvider(
            starter_api_key="test_key", expanded_api_key=None
        )

        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception("API error")

            results = provider.search("test")
            assert results == []

    def test_handles_missing_fields(self):
        """search() handles documents with missing optional fields."""
        provider = WebOfScienceProvider(
            starter_api_key="test_key", expanded_api_key=None
        )

        mock_response = Mock()
        mock_response.json.return_value = {
            "hits": [{"title": "Minimal Paper"}]
        }
        mock_response.raise_for_status = Mock()

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_response

            results = provider.search("test")

            assert len(results) == 1
            paper = results[0]
            assert paper.title == "Minimal Paper"
            assert paper.authors == []
            assert paper.year is None
            assert paper.doi is None
            assert paper.abstract is None

    def test_fetches_multiple_pages(self):
        """Starter API fetches multiple pages when limit exceeds page size."""
        provider = WebOfScienceProvider(
            starter_api_key="test_key", expanded_api_key=None
        )

        # Create responses for two pages
        page1_response = Mock()
        page1_response.json.return_value = {
            "metadata": {"total": 75},
            "hits": [{"title": f"Paper {i}"} for i in range(50)],
        }
        page1_response.raise_for_status = Mock()

        page2_response = Mock()
        page2_response.json.return_value = {
            "metadata": {"total": 75},
            "hits": [{"title": f"Paper {i}"} for i in range(50, 75)],
        }
        page2_response.raise_for_status = Mock()

        with patch("requests.get", side_effect=[page1_response, page2_response]) as mock_get:
            results = provider.search("test", limit=75)

            assert len(results) == 75
            assert mock_get.call_count == 2
            # Verify page parameter increments
            calls = mock_get.call_args_list
            assert calls[0][1]["params"]["page"] == 1
            assert calls[1][1]["params"]["page"] == 2

    def test_sends_api_key_header(self):
        """search() sends API key in header."""
        provider = WebOfScienceProvider(
            starter_api_key="my_secret_key", expanded_api_key=None
        )

        mock_response = Mock()
        mock_response.json.return_value = {"hits": []}
        mock_response.raise_for_status = Mock()

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_response

            provider.search("test")

            call_args = mock_get.call_args
            assert call_args[1]["headers"]["X-ApiKey"] == "my_secret_key"

    def test_uses_starter_api_url(self):
        """Starter API uses correct URL."""
        provider = WebOfScienceProvider(
            starter_api_key="test_key", expanded_api_key=None
        )

        mock_response = Mock()
        mock_response.json.return_value = {"hits": []}
        mock_response.raise_for_status = Mock()

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_response

            provider.search("test")

            call_args = mock_get.call_args
            assert "wos-starter" in call_args[0][0]

    def test_formats_plain_query_with_ts_tag(self):
        """Plain queries are wrapped with TS= for topic search."""
        provider = WebOfScienceProvider(
            starter_api_key="test_key", expanded_api_key=None
        )

        mock_response = Mock()
        mock_response.json.return_value = {"hits": []}
        mock_response.raise_for_status = Mock()

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_response

            provider.search("machine learning")

            call_args = mock_get.call_args
            # Query should be wrapped with TS=()
            assert call_args[1]["params"]["q"] == "TS=(machine learning)"

    def test_preserves_existing_field_tags(self):
        """Queries with field tags are not double-wrapped."""
        provider = WebOfScienceProvider(
            starter_api_key="test_key", expanded_api_key=None
        )

        mock_response = Mock()
        mock_response.json.return_value = {"hits": []}
        mock_response.raise_for_status = Mock()

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_response

            provider.search("TI=(machine learning) AND AU=Smith")

            call_args = mock_get.call_args
            # Query should NOT be wrapped again
            assert call_args[1]["params"]["q"] == "TI=(machine learning) AND AU=Smith"
class TestWebOfScienceExpandedAPI:
    """Tests for Web of Science Expanded API."""

    def test_search_converts_documents_with_abstracts(self):
        """search() converts Expanded API results including abstracts."""
        provider = WebOfScienceProvider(
            starter_api_key=None, expanded_api_key="test_key"
        )

        mock_response = Mock()
        mock_response.json.return_value = {
            "Data": {
                "Records": {
                    "records": {
                        "REC": [{
                            "UID": "WOS:000123456789",
                            "static_data": {
                                "summary": {
                                    "titles": {
                                        "title": [
                                            {"type": "item", "content": "Test Paper"},
                                            {"type": "source", "content": "Nature"},
                                        ]
                                    },
                                    "names": {
                                        "name": [
                                            {"role": "author", "display_name": "Alice Smith"},
                                            {"role": "author", "display_name": "Bob Jones"},
                                        ]
                                    },
                                    "pub_info": {"pubyear": 2024},
                                },
                                "fullrecord_metadata": {
                                    "abstracts": {
                                        "abstract": {
                                            "abstract_text": {"p": "This is the abstract."}
                                        }
                                    }
                                },
                            },
                            "dynamic_data": {
                                "cluster_related": {
                                    "identifiers": {
                                        "identifier": [
                                            {"type": "doi", "value": "10.1234/test"}
                                        ]
                                    }
                                }
                            },
                        }]
                    }
                }
            },
            "QueryResult": {"QueryID": 1, "RecordsFound": 1},
        }
        mock_response.raise_for_status = Mock()

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_response

            results = provider.search("test query")

            assert len(results) == 1
            paper = results[0]
            assert isinstance(paper, Paper)
            assert paper.title == "Test Paper"
            assert paper.authors == ["Alice Smith", "Bob Jones"]
            assert paper.year == 2024
            assert paper.doi == "10.1234/test"
            assert paper.venue == "Nature"
            assert paper.abstract == "This is the abstract."
            assert paper.sources == ["wos"]

    def test_handles_malformed_nested_fields(self):
        """search() handles cases where nested fields are strings instead of dicts."""
        provider = WebOfScienceProvider(
            starter_api_key=None, expanded_api_key="test_key"
        )

        # This mock response simulates the bug: titles, names, identifiers
        # are strings instead of the expected dict structure
        mock_response = Mock()
        mock_response.json.return_value = {
            "Data": {
                "Records": {
                    "records": {
                        "REC": [{
                            "UID": "WOS:000123456789",
                            "static_data": {
                                "summary": {
                                    "titles": "Some malformed string",  # Should be dict
                                    "names": "Another malformed string",  # Should be dict
                                    "pub_info": "Not a dict either",  # Should be dict
                                },
                                "fullrecord_metadata": {
                                    "abstracts": "String instead of dict"
                                },
                            },
                            "dynamic_data": {
                                "cluster_related": {
                                    "identifiers": "String instead of dict"
                                }
                            },
                        }]
                    }
                }
            },
            "QueryResult": {"QueryID": 1, "RecordsFound": 1},
        }
        mock_response.raise_for_status = Mock()

        with patch("requests.get", return_value=mock_response):
            # This should not raise AttributeError: 'str' object has no attribute 'get'
            results = provider.search("test", limit=10)

            # Should still return a Paper with empty/None fields
            assert len(results) == 1
            paper = results[0]
            assert paper.title == ""
            assert paper.authors == []
            assert paper.year is None
            assert paper.doi is None
            assert paper.abstract is None
            assert paper.sources == ["wos"]

    def test_fetches_multiple_pages(self):
        """Expanded API fetches multiple pages when limit exceeds page size."""
        provider = WebOfScienceProvider(
            starter_api_key=None, expanded_api_key="test_key"
        )

        # Create responses for two pages
        page1_response = Mock()
        page1_response.json.return_value = {
            "Data": {
                "Records": {
                    "records": {
                        "REC": [
                            {
                                "UID": f"WOS:{i}",
                                "static_data": {
                                    "summary": {
                                        "titles": {"title": [{"type": "item", "content": f"Paper {i}"}]},
                                        "names": {"name": []},
                                        "pub_info": {},
                                    },
                                    "fullrecord_metadata": {},
                                },
                                "dynamic_data": {},
                            }
                            for i in range(100)
                        ]
                    }
                }
            },
            "QueryResult": {"QueryID": 1, "RecordsFound": 150},
        }
        page1_response.raise_for_status = Mock()

        page2_response = Mock()
        page2_response.json.return_value = {
            "Data": {
                "Records": {
                    "records": {
                        "REC": [
                            {
                                "UID": f"WOS:{i}",
                                "static_data": {
                                    "summary": {
                                        "titles": {"title": [{"type": "item", "content": f"Paper {i}"}]},
                                        "names": {"name": []},
                                        "pub_info": {},
                                    },
                                    "fullrecord_metadata": {},
                                },
                                "dynamic_data": {},
                            }
                            for i in range(100, 150)
                        ]
                    }
                }
            },
            "QueryResult": {"QueryID": 1, "RecordsFound": 150},
        }
        page2_response.raise_for_status = Mock()

        with patch("requests.get", side_effect=[page1_response, page2_response]) as mock_get:
            results = provider.search("test", limit=150)

            assert len(results) == 150
            assert mock_get.call_count == 2
            # Verify firstRecord parameter increments
            calls = mock_get.call_args_list
            assert calls[0][1]["params"]["firstRecord"] == 1
            assert calls[1][1]["params"]["firstRecord"] == 101

    def test_uses_expanded_api_url(self):
        """Expanded API uses correct URL."""
        provider = WebOfScienceProvider(
            starter_api_key=None, expanded_api_key="test_key"
        )

        mock_response = Mock()
        mock_response.json.return_value = {
            "Data": {"Records": {"records": {"REC": []}}},
            "QueryResult": {"QueryID": 1},
        }
        mock_response.raise_for_status = Mock()

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_response

            provider.search("test")

            call_args = mock_get.call_args
            assert "wos-api.clarivate.com" in call_args[0][0]

    def test_uses_usrquery_parameter(self):
        """Expanded API uses usrQuery parameter with formatted query."""
        provider = WebOfScienceProvider(
            starter_api_key=None, expanded_api_key="test_key"
        )

        mock_response = Mock()
        mock_response.json.return_value = {
            "Data": {"Records": {"records": {"REC": []}}},
            "QueryResult": {"QueryID": 1},
        }
        mock_response.raise_for_status = Mock()

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_response

            provider.search("machine learning")

            call_args = mock_get.call_args
            # Plain queries are wrapped with TS=()
            assert call_args[1]["params"]["usrQuery"] == "TS=(machine learning)"

    def test_formats_plain_query_with_ts_tag(self):
        """Plain queries are wrapped with TS= for topic search."""
        provider = WebOfScienceProvider(
            starter_api_key=None, expanded_api_key="test_key"
        )

        mock_response = Mock()
        mock_response.json.return_value = {
            "Data": {"Records": {"records": {"REC": []}}},
            "QueryResult": {"QueryID": 1},
        }
        mock_response.raise_for_status = Mock()

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_response

            provider.search("deep learning")

            call_args = mock_get.call_args
            assert call_args[1]["params"]["usrQuery"] == "TS=(deep learning)"

    def test_preserves_existing_field_tags(self):
        """Queries with field tags are not double-wrapped."""
        provider = WebOfScienceProvider(
            starter_api_key=None, expanded_api_key="test_key"
        )

        mock_response = Mock()
        mock_response.json.return_value = {
            "Data": {"Records": {"records": {"REC": []}}},
            "QueryResult": {"QueryID": 1},
        }
        mock_response.raise_for_status = Mock()

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_response

            provider.search("TI=(neural networks) AND AU=LeCun")

            call_args = mock_get.call_args
            assert call_args[1]["params"]["usrQuery"] == "TI=(neural networks) AND AU=LeCun"

    def test_fallback_to_starter_on_expanded_error(self):
        """Falls back to Starter API when Expanded API fails."""
        provider = WebOfScienceProvider(
            starter_api_key="starter_key",
            expanded_api_key="expanded_key",
        )

        # First call (Expanded) fails, second call (Starter) succeeds
        expanded_error = Exception("Expanded API error")
        starter_response = Mock()
        starter_response.json.return_value = {
            "hits": [{"title": "Fallback Paper"}]
        }
        starter_response.raise_for_status = Mock()

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [expanded_error, starter_response]

            results = provider.search("test")

            assert len(results) == 1
            assert results[0].title == "Fallback Paper"
            # Provider should have switched to starter tier
            assert provider._api_tier == "starter"
class TestWebOfScienceExtendedMethods:
    """Tests for WoS extended methods (Expanded API only)."""

    def test_extended_methods_require_expanded_api(self):
        """Extended methods raise NotImplementedError on Starter API."""
        provider = WebOfScienceProvider(
            starter_api_key="test_key", expanded_api_key=None
        )

        with pytest.raises(NotImplementedError):
            provider.get_related_records("WOS:000123")

        with pytest.raises(NotImplementedError):
            provider.get_citing_articles("WOS:000123")

        with pytest.raises(NotImplementedError):
            provider.get_cited_references("WOS:000123")

        with pytest.raises(NotImplementedError):
            provider.search_for_citation_report("test query")

    def test_get_related_records_returns_papers(self):
        """get_related_records() returns list of Paper objects."""
        provider = WebOfScienceProvider(
            starter_api_key=None, expanded_api_key="test_key"
        )

        mock_response = Mock()
        mock_response.json.return_value = {
            "Data": {
                "Records": {
                    "records": {
                        "REC": [{
                            "UID": "WOS:000999999",
                            "static_data": {
                                "summary": {
                                    "titles": {"title": [{"type": "item", "content": "Related Paper"}]},
                                    "names": {"name": []},
                                    "pub_info": {"pubyear": 2023},
                                },
                                "fullrecord_metadata": {},
                            },
                            "dynamic_data": {},
                        }]
                    }
                }
            },
        }
        mock_response.raise_for_status = Mock()

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_response

            results = provider.get_related_records("WOS:000123456")

            assert len(results) == 1
            assert results[0].title == "Related Paper"
            # Verify correct endpoint was called
            call_args = mock_get.call_args
            assert "/related" in call_args[0][0]

    def test_get_citing_articles_returns_papers(self):
        """get_citing_articles() returns list of Paper objects."""
        provider = WebOfScienceProvider(
            starter_api_key=None, expanded_api_key="test_key"
        )

        mock_response = Mock()
        mock_response.json.return_value = {
            "Data": {
                "Records": {
                    "records": {
                        "REC": [{
                            "UID": "WOS:000888888",
                            "static_data": {
                                "summary": {
                                    "titles": {"title": [{"type": "item", "content": "Citing Paper"}]},
                                    "names": {"name": []},
                                    "pub_info": {"pubyear": 2024},
                                },
                                "fullrecord_metadata": {},
                            },
                            "dynamic_data": {},
                        }]
                    }
                }
            },
        }
        mock_response.raise_for_status = Mock()

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_response

            results = provider.get_citing_articles("WOS:000123456")

            assert len(results) == 1
            assert results[0].title == "Citing Paper"
            call_args = mock_get.call_args
            assert "/citing" in call_args[0][0]

    def test_get_cited_references_returns_dicts(self):
        """get_cited_references() returns list of reference dicts."""
        provider = WebOfScienceProvider(
            starter_api_key=None, expanded_api_key="test_key"
        )

        mock_response = Mock()
        mock_response.json.return_value = {
            "Data": [{
                "UID": "WOS:000111111",
                "citedAuthor": "Smith, J",
                "citedTitle": "A Referenced Paper",
                "citedWork": "Science",
                "year": 2020,
                "doi": "10.1234/ref",
                "timesCited": 100,
            }],
        }
        mock_response.raise_for_status = Mock()

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_response

            results = provider.get_cited_references("WOS:000123456")

            assert len(results) == 1
            assert results[0]["citedAuthor"] == "Smith, J"
            assert results[0]["citedTitle"] == "A Referenced Paper"
            assert results[0]["doi"] == "10.1234/ref"
            call_args = mock_get.call_args
            assert "/references" in call_args[0][0]

    def test_search_for_citation_report_returns_stats(self):
        """search_for_citation_report() returns citation statistics."""
        provider = WebOfScienceProvider(
            starter_api_key=None, expanded_api_key="test_key"
        )

        # First response: search that returns query ID
        search_response = Mock()
        search_response.json.return_value = {
            "Data": {"Records": {"records": {"REC": []}}},
            "QueryResult": {"QueryID": 42, "RecordsFound": 10},
        }
        search_response.raise_for_status = Mock()

        # Second response: citation report
        report_response = Mock()
        report_response.json.return_value = [{
            "ReportLevel": "WOS",
            "TimesCited": "500",
            "TimesCitedSansSelf": "450",
            "AveragePerItem": "50.0",
            "HValue": "10",
        }]
        report_response.raise_for_status = Mock()

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [search_response, report_response]

            result = provider.search_for_citation_report("machine learning")

            assert result is not None
            assert result["TimesCited"] == "500"
            assert result["HValue"] == "10"

            # Verify citation-report endpoint was called
            calls = mock_get.call_args_list
            assert len(calls) == 2
            assert "/citation-report/42" in calls[1][0][0]
class TestWebOfScienceIntegration:
    """Integration test for the Web of Science provider."""

    @pytest.mark.integration
    @pytest.mark.skip(reason="Skipped by default; requires WOS API key")
    def test_real_api_call(self):
        """Make one real API call to verify the provider works."""
        import os

        # Try expanded key first, then starter, then legacy
        expanded_key = os.environ.get("WOS_EXPANDED_API_KEY")
        starter_key = os.environ.get("WOS_STARTER_API_KEY")
        legacy_key = os.environ.get("WOS_API_KEY")

        if not (expanded_key or starter_key or legacy_key):
            pytest.skip("No WOS API key environment variable set")

        provider = WebOfScienceProvider(
            expanded_api_key=expanded_key,
            starter_api_key=starter_key,
        )

        try:
            papers = provider.search("machine learning", limit=1)

            assert len(papers) >= 1, "Provider returned no results"

            paper = papers[0]
            assert isinstance(paper, Paper)
            assert paper.title
            assert paper.sources == ["wos"]
        except Exception as e:
            pytest.skip(f"Web of Science API unavailable: {e}")
class TestIEEEXploreProvider:
    """Tests for the IEEE Xplore provider."""

    def test_is_available_false_without_key(self):
        """IEEE Xplore is unavailable without API key."""
        provider = IEEEXploreProvider(api_key=None)
        provider.api_key = None  # Ensure no key
        assert provider.is_available() is False

    def test_is_available_true_with_key(self):
        """IEEE Xplore is available with API key."""
        provider = IEEEXploreProvider(api_key="test_key")
        assert provider.is_available() is True

    def test_search_returns_empty_without_api_key(self, monkeypatch):
        """search() returns empty list when no API key is configured."""
        monkeypatch.delenv("IEEE_API_KEY", raising=False)
        provider = IEEEXploreProvider(api_key=None)
        results = provider.search("test")
        assert results == []

    def test_search_converts_articles(self):
        """search() converts API results to Paper objects."""
        provider = IEEEXploreProvider(api_key="test_key")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "articles": [{
                "title": "Test Paper on Neural Networks",
                "authors": {
                    "authors": [
                        {"full_name": "Alice Smith", "author_order": 1},
                        {"full_name": "Bob Jones", "author_order": 2},
                    ]
                },
                "abstract": "This paper presents...",
                "publication_title": "IEEE Trans. Neural Networks",
                "publication_year": "2024",
                "doi": "10.1109/TNN.2024.1234567",
                "html_url": "https://ieeexplore.ieee.org/document/1234567",
            }]
        }
        mock_response.raise_for_status = Mock()

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_response

            results = provider.search("neural networks")

            assert len(results) == 1
            paper = results[0]
            assert isinstance(paper, Paper)
            assert paper.title == "Test Paper on Neural Networks"
            assert paper.authors == ["Alice Smith", "Bob Jones"]
            assert paper.year == 2024
            assert paper.doi == "10.1109/TNN.2024.1234567"
            assert paper.abstract == "This paper presents..."
            assert paper.venue == "IEEE Trans. Neural Networks"
            assert paper.sources == ["ieee"]

    def test_search_handles_empty_results(self):
        """search() returns empty list when no results."""
        provider = IEEEXploreProvider(api_key="test_key")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"articles": []}
        mock_response.raise_for_status = Mock()

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_response

            results = provider.search("obscure query")
            assert results == []

    def test_search_handles_api_error(self):
        """search() returns empty list on API error."""
        provider = IEEEXploreProvider(api_key="test_key")

        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception("API error")

            results = provider.search("test")
            assert results == []

    def test_handles_missing_fields(self):
        """search() handles articles with missing optional fields."""
        provider = IEEEXploreProvider(api_key="test_key")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "articles": [{"title": "Minimal Paper"}]
        }
        mock_response.raise_for_status = Mock()

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_response

            results = provider.search("test")

            assert len(results) == 1
            paper = results[0]
            assert paper.title == "Minimal Paper"
            assert paper.authors == []
            assert paper.year is None
            assert paper.doi is None
            assert paper.abstract is None

    def test_caps_limit_at_200(self):
        """search() caps limit at IEEE's maximum of 200."""
        provider = IEEEXploreProvider(api_key="test_key")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"articles": []}
        mock_response.raise_for_status = Mock()

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_response

            provider.search("test", limit=500)

            call_args = mock_get.call_args
            assert call_args[1]["params"]["max_records"] == 200

    def test_sends_api_key_as_parameter(self):
        """search() sends API key as query parameter."""
        provider = IEEEXploreProvider(api_key="my_ieee_key")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"articles": []}
        mock_response.raise_for_status = Mock()

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_response

            provider.search("test")

            call_args = mock_get.call_args
            assert call_args[1]["params"]["apikey"] == "my_ieee_key"

    def test_uses_abstract_url_as_fallback(self):
        """search() uses abstract_url when html_url is not available."""
        provider = IEEEXploreProvider(api_key="test_key")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "articles": [{
                "title": "Paper",
                "abstract_url": "https://ieeexplore.ieee.org/abstract/1234",
            }]
        }
        mock_response.raise_for_status = Mock()

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_response

            results = provider.search("test")

            assert results[0].url == "https://ieeexplore.ieee.org/abstract/1234"

    def test_search_handles_inactive_account(self):
        """search() returns empty list and logs warning for inactive account."""
        provider = IEEEXploreProvider(api_key="test_key")

        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.headers = {
            "X-Error-Detail-Header": "Account Inactive",
            "X-Mashery-Error-Code": "ERR_403_DEVELOPER_INACTIVE",
        }
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "403 Client Error: Forbidden"
        )

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_response

            results = provider.search("test")

            assert results == []

    def test_search_handles_rate_limit(self):
        """search() returns empty list and logs warning for rate limiting."""
        provider = IEEEXploreProvider(api_key="test_key")

        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {
            "X-Error-Detail-Header": "Rate limit exceeded",
            "X-Mashery-Error-Code": "ERR_429_RATE_LIMIT_EXCEEDED",
        }
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "429 Client Error: Too Many Requests"
        )

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_response

            results = provider.search("test")

            assert results == []

    def test_fetches_multiple_pages(self):
        """IEEE fetches multiple pages when limit exceeds page size."""
        provider = IEEEXploreProvider(api_key="test_key")

        # Create responses for two pages (IEEE returns max 200 per page)
        page1_response = Mock()
        page1_response.status_code = 200
        page1_response.json.return_value = {
            "total_records": 350,
            "articles": [
                {
                    "title": f"Paper {i}",
                    "authors": {"authors": []},
                    "publication_year": "2024",
                }
                for i in range(200)
            ],
        }
        page1_response.raise_for_status = Mock()

        page2_response = Mock()
        page2_response.status_code = 200
        page2_response.json.return_value = {
            "total_records": 350,
            "articles": [
                {
                    "title": f"Paper {i}",
                    "authors": {"authors": []},
                    "publication_year": "2024",
                }
                for i in range(200, 350)
            ],
        }
        page2_response.raise_for_status = Mock()

        with patch("requests.get", side_effect=[page1_response, page2_response]) as mock_get:
            results = provider.search("test", limit=350)

            assert len(results) == 350
            assert mock_get.call_count == 2
            # Verify start_record parameter increments (1-indexed)
            calls = mock_get.call_args_list
            assert calls[0][1]["params"]["start_record"] == 1
            assert calls[1][1]["params"]["start_record"] == 201


class TestIEEEXploreIntegration:
    """Integration test for the IEEE Xplore provider."""

    @pytest.mark.integration
    @pytest.mark.skip(reason="Skipped by default; requires IEEE_API_KEY")
    def test_real_api_call(self):
        """Make one real API call to verify the provider works."""
        import os

        api_key = os.environ.get("IEEE_API_KEY")
        if not api_key:
            pytest.skip("IEEE_API_KEY environment variable not set")

        provider = IEEEXploreProvider(api_key=api_key)

        try:
            papers = provider.search("machine learning", limit=1)

            assert len(papers) >= 1, "Provider returned no results"

            paper = papers[0]
            assert isinstance(paper, Paper)
            assert paper.title
            assert paper.sources == ["ieee"]
        except Exception as e:
            pytest.skip(f"IEEE Xplore API unavailable: {e}")
class TestArxivProvider:
    """Tests for the arXiv provider."""

    def test_is_available_always_true(self):
        """arXiv is available without API key."""
        provider = ArxivProvider()
        assert provider.is_available() is True

    def test_search_converts_results(self):
        """search() converts API results to Paper objects."""
        provider = ArxivProvider()

        # Create mock arxiv.Result object
        mock_result = Mock()
        mock_result.title = "Test Paper on Machine Learning"
        mock_result.authors = [Mock(name="Alice Smith"), Mock(name="Bob Jones")]
        mock_result.published = Mock(year=2024)
        mock_result.doi = "10.48550/arXiv.2401.12345"
        mock_result.summary = "This paper presents a novel approach..."
        mock_result.primary_category = "cs.LG"
        mock_result.entry_id = "http://arxiv.org/abs/2401.12345v1"
        mock_result.pdf_url = "http://arxiv.org/pdf/2401.12345v1"
        # Set author names correctly
        mock_result.authors[0].name = "Alice Smith"
        mock_result.authors[1].name = "Bob Jones"

        with patch.object(provider._client, "results", return_value=iter([mock_result])):
            results = provider.search("machine learning")

            assert len(results) == 1
            paper = results[0]
            assert isinstance(paper, Paper)
            assert paper.title == "Test Paper on Machine Learning"
            assert paper.authors == ["Alice Smith", "Bob Jones"]
            assert paper.year == 2024
            assert paper.doi == "10.48550/arXiv.2401.12345"
            assert paper.abstract == "This paper presents a novel approach..."
            assert paper.venue == "cs.LG"
            assert paper.sources == ["arxiv"]

    def test_search_handles_empty_results(self):
        """search() returns empty list when no results."""
        provider = ArxivProvider()

        with patch.object(provider._client, "results", return_value=iter([])):
            results = provider.search("obscure query xyz123")
            assert results == []

    def test_search_handles_api_error(self):
        """search() returns empty list on non-retryable API error."""
        provider = ArxivProvider()

        with patch.object(provider._client, "results", side_effect=Exception("API error")):
            results = provider.search("test")
            assert results == []

    def test_retries_on_http_error(self):
        """search() retries with exponential backoff on HTTP errors."""
        provider = ArxivProvider()

        # Create a mock that fails twice then succeeds
        mock_result = Mock()
        mock_result.title = "Success Paper"
        mock_result.authors = []
        mock_result.published = Mock(year=2024)
        mock_result.doi = None
        mock_result.summary = None
        mock_result.primary_category = None
        mock_result.entry_id = "http://arxiv.org/abs/2401.12345v1"
        mock_result.pdf_url = None

        call_count = 0
        def mock_results(search):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                # arxiv.HTTPError signature is (url: str, retry: int, status: int),
                # not (url, status, message) as one might expect.
                raise arxiv.HTTPError("http://example.com", 0, 500)
            return iter([mock_result])

        with patch.object(provider._client, "results", side_effect=mock_results):
            with patch("time.sleep") as mock_sleep:
                results = provider.search("test")

                # Should succeed after retries
                assert len(results) == 1
                assert results[0].title == "Success Paper"
                # Should have slept twice (for 2 failed attempts)
                assert mock_sleep.call_count == 2

    def test_does_not_cache_failed_results(self):
        """search() does not cache results from failed requests."""
        provider = ArxivProvider()

        # First call fails
        with patch.object(provider._client, "results", side_effect=Exception("API error")):
            results1 = provider.search("test query")
            assert results1 == []

        # Create mock success result
        mock_result = Mock()
        mock_result.title = "Success Paper"
        mock_result.authors = []
        mock_result.published = Mock(year=2024)
        mock_result.doi = None
        mock_result.summary = None
        mock_result.primary_category = None
        mock_result.entry_id = "http://arxiv.org/abs/2401.12345v1"
        mock_result.pdf_url = None

        # Second call succeeds - should not be blocked by cached failure
        with patch.object(provider._client, "results", return_value=iter([mock_result])):
            results2 = provider.search("test query")
            assert len(results2) == 1
            assert results2[0].title == "Success Paper"

    def test_handles_missing_fields(self):
        """search() handles results with missing optional fields."""
        provider = ArxivProvider()

        mock_result = Mock()
        mock_result.title = "Minimal Paper"
        mock_result.authors = []
        mock_result.published = None
        mock_result.doi = None
        mock_result.summary = None
        mock_result.primary_category = None
        mock_result.entry_id = None
        mock_result.pdf_url = None

        with patch.object(provider._client, "results", return_value=iter([mock_result])):
            results = provider.search("test")

            assert len(results) == 1
            paper = results[0]
            assert paper.title == "Minimal Paper"
            assert paper.authors == []
            assert paper.year is None
            assert paper.doi is None

    def test_derives_doi_from_entry_id(self):
        """DOI is derived from arXiv ID when not provided."""
        provider = ArxivProvider()

        mock_result = Mock()
        mock_result.title = "Test"
        mock_result.authors = []
        mock_result.published = Mock(year=2024)
        mock_result.doi = None  # No DOI provided
        mock_result.summary = None
        mock_result.primary_category = None
        mock_result.entry_id = "http://arxiv.org/abs/2401.12345v2"
        mock_result.pdf_url = None

        with patch.object(provider._client, "results", return_value=iter([mock_result])):
            results = provider.search("test")

            paper = results[0]
            # DOI should be derived, without version suffix
            assert paper.doi == "10.48550/arXiv.2401.12345"

    def test_category_filter_modifies_query(self):
        """Venue filter is converted to arXiv category syntax."""
        provider = ArxivProvider()

        with patch.object(provider._client, "results", return_value=iter([])) as mock_results:
            with patch("arxiv.Search") as mock_search:
                provider.search("neural networks", filters=SearchFilters(venue="cs.AI"))

                # Verify the Search was created with category-filtered query
                call_args = mock_search.call_args
                assert "cat:cs.AI" in call_args[1]["query"]
                assert "neural networks" in call_args[1]["query"]

    def test_citations_raise_not_implemented(self):
        """get_paper_citations raises NotImplementedError."""
        provider = ArxivProvider()

        with pytest.raises(NotImplementedError) as exc_info:
            provider.get_paper_citations("2401.12345")

        assert "arXiv does not provide citation data" in str(exc_info.value)

    def test_references_raise_not_implemented(self):
        """get_paper_references raises NotImplementedError."""
        provider = ArxivProvider()

        with pytest.raises(NotImplementedError) as exc_info:
            provider.get_paper_references("2401.12345")

        assert "arXiv does not provide reference data" in str(exc_info.value)


class TestArxivIntegration:
    """Integration test for the arXiv provider."""

    @pytest.mark.integration
    @pytest.mark.skip(reason="Skipped by default to avoid API calls")
    def test_real_api_call(self):
        """Make one real API call to verify the provider works."""
        provider = ArxivProvider()

        try:
            papers = provider.search("machine learning", limit=1)

            assert len(papers) >= 1, "Provider returned no results"

            paper = papers[0]
            assert isinstance(paper, Paper)
            assert paper.title
            assert paper.sources == ["arxiv"]
        except Exception as e:
            pytest.skip(f"arXiv API unavailable: {e}")
