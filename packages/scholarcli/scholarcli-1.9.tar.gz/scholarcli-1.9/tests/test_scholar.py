"""Tests for the scholar module."""
import pytest
from unittest.mock import Mock

from scholar import *


class TestPaperRegistry:
    """Tests for the PaperRegistry class."""

    def test_register_new_paper(self):
        """Registering a new paper adds it to the registry."""
        with isolated_registry() as registry:
            paper = Paper(title="Test Paper", authors=["Author A"])
            result = registry.register(paper)
            assert result is paper
            assert len(registry) == 1
            assert paper in registry

    def test_register_duplicate_returns_existing(self):
        """Registering a duplicate returns the existing paper."""
        with isolated_registry() as registry:
            paper1 = Paper(title="Test Paper", authors=["Author A"])
            paper2 = Paper(title="Test Paper", authors=["Author A"])
            registry.register(paper1)
            result = registry.register(paper2)
            assert result is paper1
            assert len(registry) == 1

    def test_get_existing_paper(self):
        """Can retrieve a registered paper by ID."""
        with isolated_registry() as registry:
            paper = Paper(title="Test Paper", authors=["Author A"])
            registry.register(paper)
            retrieved = registry.get(paper.id)
            assert retrieved is paper

    def test_get_nonexistent_returns_none(self):
        """Getting a non-existent paper returns None."""
        with isolated_registry() as registry:
            result = registry.get("nonexistent-id")
            assert result is None

    def test_get_or_create_new(self):
        """get_or_create creates and registers new papers."""
        with isolated_registry() as registry:
            paper = registry.get_or_create({
                "title": "New Paper",
                "authors": ["Author"],
            })
            assert paper.title == "New Paper"
            assert len(registry) == 1

    def test_get_or_create_existing(self):
        """get_or_create returns existing paper for duplicates."""
        with isolated_registry() as registry:
            paper1 = registry.get_or_create({
                "title": "Test Paper",
                "authors": ["Author A"],
            })
            paper2 = registry.get_or_create({
                "title": "Test Paper",
                "authors": ["Author A"],
            })
            assert paper1 is paper2
            assert len(registry) == 1

    def test_clear_removes_all_papers(self):
        """clear() removes all papers from the registry."""
        with isolated_registry() as registry:
            registry.register(Paper(title="A", authors=[]))
            registry.register(Paper(title="B", authors=[]))
            assert len(registry) == 2
            registry.clear()
            assert len(registry) == 0

    def test_all_papers(self):
        """all_papers() returns list of all registered papers."""
        with isolated_registry() as registry:
            p1 = Paper(title="A", authors=["X"])
            p2 = Paper(title="B", authors=["Y"])
            registry.register(p1)
            registry.register(p2)
            papers = registry.all_papers()
            assert len(papers) == 2
            assert p1 in papers
            assert p2 in papers


class TestIsolatedRegistry:
    """Tests for the isolated_registry context manager."""

    def test_isolated_registry_is_empty(self):
        """Isolated registry starts empty."""
        with isolated_registry() as registry:
            assert len(registry) == 0

    def test_isolated_registry_does_not_affect_global(self):
        """Changes in isolated registry don't affect global."""
        # Add a paper to global registry
        global_registry = get_registry()
        initial_count = len(global_registry)

        with isolated_registry() as registry:
            registry.register(Paper(title="Isolated", authors=[]))
            assert len(registry) == 1

        # Global registry unchanged
        assert len(get_registry()) == initial_count

    def test_nested_isolated_registries(self):
        """Nested isolated registries work correctly."""
        with isolated_registry() as outer:
            outer.register(Paper(title="Outer", authors=[]))
            assert len(outer) == 1

            with isolated_registry() as inner:
                assert len(inner) == 0
                inner.register(Paper(title="Inner", authors=[]))
                assert len(inner) == 1

            # Outer registry preserved
            assert len(outer) == 1
class TestPaper:
    """Tests for the Paper class."""

    def test_equality_by_doi(self):
        """Papers with same DOI are equal regardless of title/author."""
        with isolated_registry():
            p1 = Paper(title="Paper One", authors=["A"], doi="10.1234/test")
            p2 = Paper(title="Paper 1", authors=["B"], doi="10.1234/test")
            assert p1 == p2

    def test_equality_by_title_and_author(self):
        """Papers without DOI are equal by title + first author."""
        with isolated_registry():
            p1 = Paper(title="Test Paper", authors=["John Smith"])
            p2 = Paper(title="test paper", authors=["Alice Smith"])  # Same last name
            assert p1 == p2

    def test_inequality_different_authors(self):
        """Papers with same title but different first author are not equal."""
        with isolated_registry():
            p1 = Paper(title="Test Paper", authors=["Smith, John"])
            p2 = Paper(title="Test Paper", authors=["Jones, Alice"])
            assert p1 != p2

    def test_inequality_different_titles(self):
        """Different papers are not equal."""
        with isolated_registry():
            p1 = Paper(title="Paper A", authors=["A"])
            p2 = Paper(title="Paper B", authors=["B"])
            assert p1 != p2

    def test_hash_consistency(self):
        """Equal papers have the same hash."""
        with isolated_registry():
            p1 = Paper(title="Test", authors=["A"], doi="10.1234/test")
            p2 = Paper(title="Different", authors=["B"], doi="10.1234/test")
            assert hash(p1) == hash(p2)

    def test_paper_id_with_doi(self):
        """Paper ID uses DOI when available."""
        with isolated_registry():
            paper = Paper(title="Test", authors=["A"], doi="10.1234/TEST")
            assert paper.id == "doi:10.1234/test"

    def test_paper_id_without_doi(self):
        """Paper ID uses hash of title+author when no DOI."""
        with isolated_registry():
            paper = Paper(title="Test Paper", authors=["John Smith"])
            assert paper.id.startswith("hash:")
            assert len(paper.id) == 5 + 16  # "hash:" + 16 hex chars

    def test_paper_id_stable(self):
        """Paper ID is stable for same paper data."""
        with isolated_registry():
            p1 = Paper(title="Test", authors=["Smith"])
            p2 = Paper(title="Test", authors=["Smith"])
            assert p1.id == p2.id


class TestPaperMergeWith:
    """Tests for Paper.merge_with() consolidation."""

    def test_merge_keeps_abstract_from_other(self):
        """Merging keeps abstract from paper that has it."""
        with isolated_registry():
            p1 = Paper(title="Test", authors=["A"], doi="10.1/test", sources=["dblp"])
            p2 = Paper(title="Test", authors=["A"], doi="10.1/test",
                abstract="This is the abstract", sources=["s2"])
            merged = p1.merge_with(p2)
            assert merged.abstract == "This is the abstract"

    def test_merge_prefers_self_values(self):
        """When both have a value, prefer self."""
        with isolated_registry():
            p1 = Paper(title="Test", authors=["A"], doi="10.1/test",
                venue="Conference A", sources=["provider1"])
            p2 = Paper(title="Test", authors=["A"], doi="10.1/test",
                venue="Conference B", sources=["provider2"])
            merged = p1.merge_with(p2)
            assert merged.venue == "Conference A"

    def test_merge_combines_sources(self):
        """Merging combines sources from both papers."""
        with isolated_registry():
            p1 = Paper(title="Test", authors=["A"], sources=["dblp"])
            p2 = Paper(title="test", authors=["A"], sources=["s2"])
            merged = p1.merge_with(p2)
            assert "dblp" in merged.sources
            assert "s2" in merged.sources

    def test_merge_raises_for_unequal_papers(self):
        """Cannot merge papers that aren't equal."""
        with isolated_registry():
            p1 = Paper(title="Paper A", authors=["A"], doi="10.1/a")
            p2 = Paper(title="Paper B", authors=["B"], doi="10.1/b")
            with pytest.raises(ValueError, match="Can only merge equal papers"):
                p1.merge_with(p2)

    def test_merge_consolidates_all_fields(self):
        """Merging fills in all missing fields from other."""
        with isolated_registry():
            p1 = Paper(title="Test", authors=["A"], doi="10.1/test",
                year=2024, sources=["provider1"])
            p2 = Paper(title="Test", authors=["A"], doi="10.1/test",
                abstract="Abstract", venue="Venue", url="http://example.com",
                pdf_url="http://example.com/pdf", sources=["provider2"])
            merged = p1.merge_with(p2)
            assert merged.year == 2024  # From p1
            assert merged.abstract == "Abstract"  # From p2
            assert merged.venue == "Venue"  # From p2
            assert merged.url == "http://example.com"  # From p2
            assert merged.pdf_url == "http://example.com/pdf"  # From p2


class TestPaperSerialization:
    """Tests for Paper.to_dict() and Paper.from_dict()."""

    def test_to_dict_basic_fields(self):
        """to_dict includes all basic fields."""
        with isolated_registry():
            paper = Paper(
                title="Test Paper",
                authors=["Author A", "Author B"],
                year=2024,
                doi="10.1234/test",
                abstract="An abstract",
                venue="Conference",
                url="http://example.com",
                pdf_url="http://example.com/pdf",
                citation_count=42,
                sources=["s2", "dblp"],
            )
            d = paper.to_dict()
            assert d["title"] == "Test Paper"
            assert d["authors"] == ["Author A", "Author B"]
            assert d["year"] == 2024
            assert d["doi"] == "10.1234/test"
            assert d["abstract"] == "An abstract"
            assert d["venue"] == "Conference"
            assert d["url"] == "http://example.com"
            assert d["pdf_url"] == "http://example.com/pdf"
            assert d["citation_count"] == 42
            assert d["sources"] == ["s2", "dblp"]

    def test_to_dict_excludes_refs_cites_by_default(self):
        """to_dict excludes references/citations by default."""
        with isolated_registry():
            paper = Paper(
                title="Test",
                authors=[],
                references=[Paper(title="Ref", authors=[])],
                citations=[Paper(title="Cit", authors=[])],
            )
            d = paper.to_dict()
            assert "references" not in d
            assert "citations" not in d

    def test_to_dict_includes_refs_cites_when_requested(self):
        """to_dict includes refs/cites when include_refs_cites=True."""
        with isolated_registry():
            ref = Paper(title="Reference Paper", authors=["R"], year=2020)
            cit = Paper(title="Citing Paper", authors=["C"], year=2025)
            paper = Paper(title="Test", authors=[], references=[ref], citations=[cit])

            d = paper.to_dict(include_refs_cites=True)
            assert d["references"] is not None
            assert len(d["references"]) == 1
            assert d["references"][0]["title"] == "Reference Paper"
            assert d["citations"] is not None
            assert len(d["citations"]) == 1
            assert d["citations"][0]["title"] == "Citing Paper"

    def test_to_dict_refs_cites_one_level_deep(self):
        """Nested refs/cites are serialized without their own refs/cites."""
        with isolated_registry():
            nested_ref = Paper(
                title="Nested",
                authors=[],
                references=[Paper(title="Deep", authors=[])],
            )
            paper = Paper(title="Test", authors=[], references=[nested_ref])

            d = paper.to_dict(include_refs_cites=True)
            # The nested reference is serialized...
            assert d["references"][0]["title"] == "Nested"
            # ...but without its own references
            assert "references" not in d["references"][0]

    def test_from_dict_basic_fields(self):
        """from_dict reconstructs a paper from a dictionary."""
        with isolated_registry():
            d = {
                "title": "Test Paper",
                "authors": ["Author A"],
                "year": 2024,
                "doi": "10.1234/test",
                "abstract": "Abstract",
                "venue": "Venue",
                "url": "http://example.com",
                "pdf_url": "http://example.com/pdf",
                "citation_count": 10,
                "sources": ["s2"],
            }
            paper = Paper.from_dict(d)
            assert paper.title == "Test Paper"
            assert paper.authors == ["Author A"]
            assert paper.year == 2024
            assert paper.doi == "10.1234/test"
            assert paper.abstract == "Abstract"
            assert paper.venue == "Venue"
            assert paper.url == "http://example.com"
            assert paper.pdf_url == "http://example.com/pdf"
            assert paper.citation_count == 10
            assert paper.sources == ["s2"]

    def test_from_dict_with_refs_cites(self):
        """from_dict reconstructs nested references and citations."""
        with isolated_registry():
            d = {
                "title": "Test",
                "authors": [],
                "references": [{"title": "Ref Paper", "authors": ["R"], "year": 2020}],
                "citations": [{"title": "Cit Paper", "authors": ["C"], "year": 2025}],
            }
            paper = Paper.from_dict(d)
            assert paper.references is not None
            assert len(paper.references) == 1
            assert paper.references[0].title == "Ref Paper"
            assert paper.citations is not None
            assert len(paper.citations) == 1
            assert paper.citations[0].title == "Cit Paper"

    def test_from_dict_legacy_format(self):
        """from_dict handles legacy format without refs/cites."""
        with isolated_registry():
            d = {"title": "Old Paper", "authors": ["A"]}
            paper = Paper.from_dict(d)
            assert paper.title == "Old Paper"
            assert paper.references is None
            assert paper.citations is None

    def test_roundtrip_serialization(self):
        """Serializing and deserializing preserves paper data."""
        with isolated_registry():
            original = Paper(
                title="Test",
                authors=["A", "B"],
                year=2024,
                doi="10.1/test",
                abstract="Abstract",
                venue="Venue",
                sources=["s2"],
                references=[Paper(title="Ref", authors=["R"], year=2020)],
            )
            d = original.to_dict(include_refs_cites=True)
            restored = Paper.from_dict(d, use_registry=False)

            assert restored.title == original.title
            assert restored.authors == original.authors
            assert restored.year == original.year
            assert restored.doi == original.doi
            assert restored.references is not None
            assert len(restored.references) == 1
            assert restored.references[0].title == "Ref"

    def test_from_dict_uses_registry_by_default(self):
        """from_dict returns same object for duplicate papers."""
        with isolated_registry():
            d = {"title": "Test", "authors": ["A"], "doi": "10.1/test"}
            p1 = Paper.from_dict(d)
            p2 = Paper.from_dict(d)
            assert p1 is p2

    def test_from_dict_without_registry(self):
        """from_dict with use_registry=False creates new objects."""
        with isolated_registry():
            d = {"title": "Test", "authors": ["A"], "doi": "10.1/test"}
            p1 = Paper.from_dict(d, use_registry=False)
            p2 = Paper.from_dict(d, use_registry=False)
            assert p1 is not p2
            assert p1 == p2  # But they're equal


class TestPaperTitlePreview:
    """Tests for Paper.title_preview()."""

    def test_short_title_unchanged(self):
        """Short titles are returned unchanged."""
        with isolated_registry():
            paper = Paper(title="Short Title", authors=[])
            assert paper.title_preview(50) == "Short Title"

    def test_long_title_truncated(self):
        """Long titles are truncated with ellipsis."""
        with isolated_registry():
            paper = Paper(title="A" * 100, authors=[])
            preview = paper.title_preview(50)
            assert len(preview) == 50
            assert preview.endswith("...")

    def test_fallback_to_doi(self):
        """Falls back to DOI when no title."""
        with isolated_registry():
            paper = Paper(title="", authors=[], doi="10.1234/test")
            assert paper.title_preview() == "10.1234/test"

    def test_fallback_to_unknown(self):
        """Falls back to 'Unknown' when no title or DOI."""
        with isolated_registry():
            paper = Paper(title="", authors=[])
            assert paper.title_preview() == "Unknown"

    def test_custom_max_length(self):
        """Respects custom max_length parameter."""
        with isolated_registry():
            paper = Paper(title="A" * 50, authors=[])
            preview = paper.title_preview(20)
            assert len(preview) == 20
            assert preview.endswith("...")
class TestSearchFilters:
    """Tests for the SearchFilters class."""

    def test_year_range_single_year(self):
        """Single year returns same start and end."""
        f = SearchFilters(year="2020")
        assert f.year_range() == (2020, 2020)

    def test_year_range_full_range(self):
        """Full range returns both bounds."""
        f = SearchFilters(year="2020-2024")
        assert f.year_range() == (2020, 2024)

    def test_year_range_open_start(self):
        """Open start range returns None for start."""
        f = SearchFilters(year="-2024")
        assert f.year_range() == (None, 2024)

    def test_year_range_open_end(self):
        """Open end range returns None for end."""
        f = SearchFilters(year="2020-")
        assert f.year_range() == (2020, None)

    def test_year_range_no_year(self):
        """No year filter returns (None, None)."""
        f = SearchFilters()
        assert f.year_range() == (None, None)

    def test_year_range_invalid_format(self):
        """Invalid year format raises ValueError."""
        f = SearchFilters(year="invalid")
        with pytest.raises(ValueError, match="Invalid year format"):
            f.year_range()

    def test_as_dict_empty(self):
        """Empty filters produce empty dict."""
        f = SearchFilters()
        assert f.as_dict() == {}

    def test_as_dict_with_values(self):
        """Active filters appear in dict."""
        f = SearchFilters(
            year="2020-2024",
            open_access=True,
            venue="Nature",
            min_citations=10,
            pub_types=["article", "conference"],
        )
        d = f.as_dict()
        assert d["year"] == "2020-2024"
        assert d["open_access"] is True
        assert d["venue"] == "Nature"
        assert d["min_citations"] == 10
        assert d["pub_types"] == ["article", "conference"]

    def test_cache_key_empty(self):
        """Empty filters produce empty cache key."""
        f = SearchFilters()
        assert f.cache_key() == ""

    def test_cache_key_with_values(self):
        """Active filters produce stable cache key."""
        f = SearchFilters(year="2020", open_access=True, min_citations=5)
        key = f.cache_key()
        assert "y:2020" in key
        assert "oa:1" in key
        assert "c:5" in key

    def test_cache_key_stable_ordering(self):
        """Cache key is stable regardless of pub_types order."""
        f1 = SearchFilters(pub_types=["article", "conference"])
        f2 = SearchFilters(pub_types=["conference", "article"])
        assert f1.cache_key() == f2.cache_key()

    def test_is_empty_true(self):
        """is_empty returns True for default filters."""
        f = SearchFilters()
        assert f.is_empty() is True

    def test_is_empty_false(self):
        """is_empty returns False when any filter is set."""
        assert SearchFilters(year="2020").is_empty() is False
        assert SearchFilters(open_access=True).is_empty() is False
        assert SearchFilters(venue="Nature").is_empty() is False
        assert SearchFilters(min_citations=0).is_empty() is False
        assert SearchFilters(pub_types=["article"]).is_empty() is False

    def test_matches_empty_filters(self):
        """Empty filters match any paper."""
        with isolated_registry():
            f = SearchFilters()
            paper = Paper(title="Test", authors=[], year=2020)
            assert f.matches(paper) is True

    def test_matches_year_in_range(self):
        """Paper within year range matches."""
        with isolated_registry():
            f = SearchFilters(year="2018-2022")
            assert f.matches(Paper(title="Test", authors=[], year=2020)) is True
            assert f.matches(Paper(title="Test2", authors=[], year=2018)) is True
            assert f.matches(Paper(title="Test3", authors=[], year=2022)) is True

    def test_matches_year_out_of_range(self):
        """Paper outside year range doesn't match."""
        with isolated_registry():
            f = SearchFilters(year="2018-2022")
            assert f.matches(Paper(title="Test", authors=[], year=2017)) is False
            assert f.matches(Paper(title="Test2", authors=[], year=2023)) is False

    def test_matches_year_none(self):
        """Paper without year doesn't match year filter."""
        with isolated_registry():
            f = SearchFilters(year="2020")
            assert f.matches(Paper(title="Test", authors=[], year=None)) is False

    def test_matches_venue(self):
        """Venue filter uses case-insensitive substring match."""
        with isolated_registry():
            f = SearchFilters(venue="Nature")
            assert f.matches(Paper(title="Test", authors=[], venue="Nature Communications")) is True
            assert f.matches(Paper(title="Test2", authors=[], venue="nature")) is True
            assert f.matches(Paper(title="Test3", authors=[], venue="Science")) is False
            assert f.matches(Paper(title="Test4", authors=[], venue=None)) is False

    def test_matches_multiple_filters(self):
        """All active filters must match."""
        with isolated_registry():
            f = SearchFilters(year="2020-", venue="Nature")
            assert f.matches(Paper(title="Test", authors=[], year=2021, venue="Nature")) is True
            assert f.matches(Paper(title="Test2", authors=[], year=2019, venue="Nature")) is False
            assert f.matches(Paper(title="Test3", authors=[], year=2021, venue="Science")) is False


class TestFilterPapers:
    """Tests for the filter_papers function."""

    def test_filter_papers_empty_filters(self):
        """Empty filters return all papers."""
        with isolated_registry():
            papers = [Paper(title="A", authors=[], year=2020), Paper(title="B", authors=[], year=2015)]
            result = filter_papers(papers, SearchFilters())
            assert result == papers

    def test_filter_papers_by_year(self):
        """Filters papers by year range."""
        with isolated_registry():
            papers = [
                Paper(title="A", authors=[], year=2020),
                Paper(title="B", authors=[], year=2015),
                Paper(title="C", authors=[], year=2022),
            ]
            result = filter_papers(papers, SearchFilters(year="2018-"))
            assert len(result) == 2
            assert all(p.year >= 2018 for p in result)

    def test_filter_papers_preserves_order(self):
        """Filtered list preserves original order."""
        with isolated_registry():
            papers = [
                Paper(title="A", authors=[], year=2020),
                Paper(title="B", authors=[], year=2021),
                Paper(title="C", authors=[], year=2022),
            ]
            result = filter_papers(papers, SearchFilters(year="2020-"))
            assert [p.title for p in result] == ["A", "B", "C"]
class TestSearchResult:
    """Tests for the SearchResult class."""

    def test_merge_deduplicates(self):
        """Merging results deduplicates papers."""
        with isolated_registry():
            p1 = Paper(title="Paper A", authors=["A"])
            p2 = Paper(title="Paper B", authors=["B"])
            p3 = Paper(title="Paper A", authors=["A"])  # Duplicate of p1

            r1 = SearchResult(
                query="test",
                provider="p1",
                timestamp="2024-01-01",
                papers=[p1, p2],
            )
            r2 = SearchResult(
                query="test",
                provider="p2",
                timestamp="2024-01-01",
                papers=[p2, p3],
            )

            merged = r1.merge(r2)
            assert len(merged.papers) == 2

    def test_merge_consolidates_data(self):
        """Merging consolidates data from duplicate papers."""
        with isolated_registry():
            # DBLP paper without abstract
            p1 = Paper(
                title="Paper A", authors=["Author"], doi="10.1/a",
                sources=["dblp"]
            )
            # Semantic Scholar paper with abstract
            p2 = Paper(
                title="Paper A", authors=["Author"], doi="10.1/a",
                abstract="This is the abstract", sources=["s2"]
            )

            r1 = SearchResult(
                query="test", provider="dblp",
                timestamp="2024-01-01", papers=[p1]
            )
            r2 = SearchResult(
                query="test", provider="s2",
                timestamp="2024-01-01", papers=[p2]
            )

            merged = r1.merge(r2)
            assert len(merged.papers) == 1
            # Consolidated paper should have the abstract
            assert merged.papers[0].abstract == "This is the abstract"
            # And combined sources
            assert "dblp" in merged.papers[0].sources
            assert "s2" in merged.papers[0].sources
class TestSearch:
    """Tests for the Search class and search function."""

    def test_search_returns_result(self, monkeypatch):
        """search() returns a SearchResult."""
        with isolated_registry():
            from scholar import providers

            mock_provider = Mock()
            mock_provider.name = "mock"
            mock_provider.search.return_value = [
                Paper(title="Test", authors=["Author"])
            ]
            monkeypatch.setattr(providers, "PROVIDERS", {"mock": mock_provider})

            result = search("test query")
            assert isinstance(result, SearchResult)
            assert result.query == "test query"

    def test_search_class_execute(self, monkeypatch):
        """Search.execute() returns results when providers are specified."""
        with isolated_registry():
            from scholar import providers

            mock_provider = Mock()
            mock_provider.name = "mock"
            mock_provider.search.return_value = []
            monkeypatch.setattr(providers, "PROVIDERS", {"mock": mock_provider})

            s = Search("test")
            # Explicitly specify the mock provider since "mock" is not a default
            results = s.execute(providers=["mock"])
            assert len(results) > 0
