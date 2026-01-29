"""Tests for the review module."""
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

from scholar.review import *
from scholar.scholar import Paper, SearchFilters


class TestReviewDecision:
    """Tests for ReviewDecision dataclass."""

    def test_default_status_is_pending(self):
        """New decisions should be pending."""
        paper = Paper(title="Test", authors=["Author"], year=2024)
        decision = ReviewDecision(paper=paper, provider="test")
        assert decision.status == DecisionStatus.PENDING
        assert not decision.is_decided

    def test_kept_is_decided(self):
        """Kept papers are decided."""
        paper = Paper(title="Test", authors=["Author"], year=2024)
        decision = ReviewDecision(
            paper=paper,
            provider="test",
            status=DecisionStatus.KEPT
        )
        assert decision.is_decided

    def test_discarded_requires_tag(self):
        """Discarded papers without tags are invalid."""
        paper = Paper(title="Test", authors=["Author"], year=2024)
        decision = ReviewDecision(
            paper=paper,
            provider="test",
            status=DecisionStatus.DISCARDED,
            tags=[]
        )
        assert not decision.is_valid
        
        decision.add_tag("Not relevant")
        assert decision.is_valid

    def test_add_remove_tags(self):
        """Can add and remove tags."""
        paper = Paper(title="Test", authors=["Author"], year=2024)
        decision = ReviewDecision(paper=paper, provider="test")
        
        decision.add_tag("theme1")
        decision.add_tag("theme2")
        assert decision.has_tag("theme1")
        assert len(decision.tags) == 2
        
        # Adding duplicate doesn't add again
        decision.add_tag("theme1")
        assert len(decision.tags) == 2
        
        decision.remove_tag("theme1")
        assert not decision.has_tag("theme1")
        assert len(decision.tags) == 1

    def test_backward_compat_motivation(self):
        """motivation property works for backward compatibility."""
        paper = Paper(title="Test", authors=["Author"], year=2024)
        decision = ReviewDecision(paper=paper, provider="test")

        decision.motivation = "Not relevant"
        assert decision.tags == ["Not relevant"]
        assert decision.motivation == "Not relevant"

        decision.motivation = ""
        assert decision.tags == []
        assert decision.motivation == ""

    def test_default_source_is_human(self):
        """New decisions default to human source."""
        paper = Paper(title="Test", authors=["Author"], year=2024)
        decision = ReviewDecision(paper=paper, provider="test")
        assert decision.source == ReviewSource.HUMAN
        assert not decision.is_example
        assert decision.llm_confidence is None

    def test_llm_source_tracking(self):
        """Can track LLM source and confidence."""
        paper = Paper(title="Test", authors=["Author"], year=2024)
        decision = ReviewDecision(
            paper=paper,
            provider="test",
            status=DecisionStatus.KEPT,
            source=ReviewSource.LLM_UNREVIEWED,
            llm_confidence=0.85,
        )
        assert decision.source == ReviewSource.LLM_UNREVIEWED
        assert decision.llm_confidence == 0.85

    def test_example_flag(self):
        """Can mark a decision as a training example."""
        paper = Paper(title="Test", authors=["Author"], year=2024)
        decision = ReviewDecision(
            paper=paper,
            provider="test",
            is_example=True,
        )
        assert decision.is_example
class TestSnowballing:
    """Tests for snowballing functionality."""

    def test_add_papers_from_snowball_adds_new_papers(self):
        """New papers are added with snowball tag."""
        session = ReviewSession(
            query="test",
            providers=["s2"],
            timestamp=datetime.now(),
        )
        papers = [
            Paper(title="Reference 1", authors=["Author A"], year=2020,
                  doi="10.1000/ref1"),
            Paper(title="Reference 2", authors=["Author B"], year=2021,
                  doi="10.1000/ref2"),
        ]

        count = session.add_papers_from_snowball(
            papers, "references", ["doi:10.1000/source"]
        )

        assert count == 2
        assert len(session.decisions) == 2
        assert all(d.provider == "snowball" for d in session.decisions)
        assert all("snowball-refs" in d.tags for d in session.decisions)

    def test_add_papers_from_snowball_skips_duplicates(self):
        """Existing papers are not duplicated."""
        session = ReviewSession(
            query="test",
            providers=["s2"],
            timestamp=datetime.now(),
        )
        existing = Paper(title="Existing", authors=["Author"], year=2020,
                        doi="10.1000/existing")
        session.decisions.append(ReviewDecision(
            paper=existing, provider="s2"
        ))

        papers = [
            existing,  # Duplicate
            Paper(title="New Paper", authors=["Author B"], year=2021,
                  doi="10.1000/new"),
        ]

        count = session.add_papers_from_snowball(
            papers, "citations", ["doi:10.1000/source"]
        )

        assert count == 1
        assert len(session.decisions) == 2

    def test_snowball_round_recorded(self):
        """Snowball rounds are tracked for reporting."""
        session = ReviewSession(
            query="test",
            providers=["s2"],
            timestamp=datetime.now(),
        )
        papers = [
            Paper(title="Citation 1", authors=["Author"], year=2022,
                  doi="10.1000/cit1"),
        ]

        session.add_papers_from_snowball(
            papers, "citations", ["doi:10.1000/paper1", "doi:10.1000/paper2"]
        )

        assert len(session.snowball_rounds) == 1
        round_info = session.snowball_rounds[0]
        assert round_info.direction == "citations"
        assert round_info.papers_added == 1
        assert len(round_info.source_papers) == 2
class TestQueryProviderPairs:
    """Tests for query-provider pair tracking."""

    def test_add_query_provider_pair(self):
        """Adding pairs associates queries with their providers."""
        session = ReviewSession(
            query="test",
            providers=["openalex", "wos"],
            timestamp=datetime.now(),
        )
        session.add_query_provider_pair("llm programming education", "openalex")
        session.add_query_provider_pair("llm AND programming AND education", "wos")
        
        assert len(session.query_provider_pairs) == 2
        assert ("llm programming education", "openalex") in session.query_provider_pairs
        assert ("llm AND programming AND education", "wos") in session.query_provider_pairs

    def test_add_query_provider_pair_no_duplicates(self):
        """Duplicate pairs are silently ignored."""
        session = ReviewSession(
            query="test",
            providers=["openalex"],
            timestamp=datetime.now(),
        )
        session.add_query_provider_pair("test query", "openalex")
        session.add_query_provider_pair("test query", "openalex")  # duplicate
        
        assert len(session.query_provider_pairs) == 1

    def test_queries_for_provider(self):
        """Can retrieve all queries used with a specific provider."""
        session = ReviewSession(
            query="test",
            providers=["openalex", "wos"],
            timestamp=datetime.now(),
        )
        session.add_query_provider_pair("natural language query", "openalex")
        session.add_query_provider_pair("another query", "openalex")
        session.add_query_provider_pair("boolean AND query", "wos")
        
        openalex_queries = session.queries_for_provider("openalex")
        wos_queries = session.queries_for_provider("wos")
        
        assert len(openalex_queries) == 2
        assert "natural language query" in openalex_queries
        assert "another query" in openalex_queries
        assert len(wos_queries) == 1
        assert "boolean AND query" in wos_queries
class TestReviewSession:
    """Tests for ReviewSession dataclass."""

    @pytest.fixture
    def sample_session(self):
        """Create a sample session with mixed decisions."""
        papers = [
            Paper(title="Paper A", authors=["Author A"], year=2020),
            Paper(title="Paper B", authors=["Author B"], year=2022),
            Paper(title="Paper C", authors=["Author C"], year=2021),
        ]
        session = ReviewSession(
            query="test query",
            providers=["provider1"],
            timestamp=datetime.now(),
        )
        session.decisions = [
            ReviewDecision(
                paper=papers[0], provider="p1", 
                status=DecisionStatus.KEPT, tags=["privacy", "ml"]
            ),
            ReviewDecision(
                paper=papers[1], provider="p1", 
                status=DecisionStatus.DISCARDED, tags=["off-topic"]
            ),
            ReviewDecision(paper=papers[2], provider="p1", status=DecisionStatus.PENDING),
        ]
        return session

    def test_kept_papers(self, sample_session):
        """Test filtering kept papers."""
        kept = sample_session.kept_papers
        assert len(kept) == 1
        assert kept[0].paper.title == "Paper A"

    def test_discarded_papers(self, sample_session):
        """Test filtering discarded papers."""
        discarded = sample_session.discarded_papers
        assert len(discarded) == 1
        assert discarded[0].paper.title == "Paper B"
        assert "off-topic" in discarded[0].tags

    def test_all_themes(self, sample_session):
        """Test getting all themes."""
        themes = sample_session.all_themes()
        assert themes == {"privacy", "ml"}

    def test_all_motivations(self, sample_session):
        """Test getting all motivations."""
        motivations = sample_session.all_motivations()
        assert motivations == {"off-topic"}

    def test_theme_counts(self, sample_session):
        """Test counting papers per theme."""
        counts = sample_session.theme_counts()
        assert counts["privacy"] == 1
        assert counts["ml"] == 1

    def test_papers_with_tag(self, sample_session):
        """Test finding papers with specific tag."""
        papers = sample_session.papers_with_tag("privacy")
        assert len(papers) == 1
        assert papers[0].paper.title == "Paper A"

    def test_sort_by_year(self, sample_session):
        """Test sorting by year."""
        sample_session.sort_by("year")
        years = [d.paper.year for d in sample_session.decisions]
        assert years == [2020, 2021, 2022]

    def test_sort_by_year_reverse(self, sample_session):
        """Test sorting by year descending."""
        sample_session.sort_by("year", reverse=True)
        years = [d.paper.year for d in sample_session.decisions]
        assert years == [2022, 2021, 2020]

    def test_llm_unreviewed_papers(self):
        """Test getting LLM unreviewed papers."""
        session = ReviewSession(
            query="test",
            providers=["test"],
            timestamp=datetime.now(),
        )
        papers = [
            Paper(title="Human", authors=["A"], year=2024),
            Paper(title="LLM Unreviewed", authors=["B"], year=2024),
            Paper(title="LLM Reviewed", authors=["C"], year=2024),
        ]
        session.decisions = [
            ReviewDecision(
                paper=papers[0], provider="test",
                status=DecisionStatus.KEPT,
                source=ReviewSource.HUMAN,
            ),
            ReviewDecision(
                paper=papers[1], provider="test",
                status=DecisionStatus.KEPT,
                source=ReviewSource.LLM_UNREVIEWED,
            ),
            ReviewDecision(
                paper=papers[2], provider="test",
                status=DecisionStatus.KEPT,
                source=ReviewSource.LLM_REVIEWED,
            ),
        ]
        unreviewed = session.llm_unreviewed_papers()
        assert len(unreviewed) == 1
        assert unreviewed[0].paper.title == "LLM Unreviewed"

    def test_example_papers(self):
        """Test getting training example papers."""
        session = ReviewSession(
            query="test",
            providers=["test"],
            timestamp=datetime.now(),
        )
        papers = [
            Paper(title="Human with tags", authors=["A"], year=2024),
            Paper(title="Human without tags", authors=["B"], year=2024),
            Paper(title="LLM corrected", authors=["C"], year=2024),
            Paper(title="LLM not example", authors=["D"], year=2024),
        ]
        session.decisions = [
            ReviewDecision(
                paper=papers[0], provider="test",
                status=DecisionStatus.KEPT,
                tags=["ml"],
                source=ReviewSource.HUMAN,
            ),
            ReviewDecision(
                paper=papers[1], provider="test",
                status=DecisionStatus.KEPT,
                source=ReviewSource.HUMAN,
            ),
            ReviewDecision(
                paper=papers[2], provider="test",
                status=DecisionStatus.KEPT,
                tags=["corrected"],
                source=ReviewSource.LLM_REVIEWED,
                is_example=True,
            ),
            ReviewDecision(
                paper=papers[3], provider="test",
                status=DecisionStatus.KEPT,
                tags=["ml"],
                source=ReviewSource.LLM_REVIEWED,
                is_example=False,
            ),
        ]
        examples = session.example_papers()
        assert len(examples) == 2
        titles = {e.paper.title for e in examples}
        assert "Human with tags" in titles
        assert "LLM corrected" in titles

    def test_llm_review_statistics(self):
        """Test LLM review statistics."""
        session = ReviewSession(
            query="test",
            providers=["test"],
            timestamp=datetime.now(),
        )
        papers = [
            Paper(title=f"Paper {i}", authors=["A"], year=2024)
            for i in range(5)
        ]
        session.decisions = [
            ReviewDecision(
                paper=papers[0], provider="test",
                status=DecisionStatus.KEPT, tags=["ml"],
                source=ReviewSource.HUMAN,
            ),
            ReviewDecision(
                paper=papers[1], provider="test",
                status=DecisionStatus.KEPT,
                source=ReviewSource.LLM_UNREVIEWED,
            ),
            ReviewDecision(
                paper=papers[2], provider="test",
                status=DecisionStatus.DISCARDED, tags=["off-topic"],
                source=ReviewSource.LLM_REVIEWED,
            ),
            ReviewDecision(
                paper=papers[3], provider="test",
                status=DecisionStatus.PENDING,
            ),
            ReviewDecision(
                paper=papers[4], provider="test",
                status=DecisionStatus.KEPT, tags=["corrected"],
                source=ReviewSource.LLM_REVIEWED,
                is_example=True,
            ),
        ]
        stats = session.llm_review_statistics()
        assert stats["human"] == 1
        assert stats["llm_unreviewed"] == 1
        assert stats["llm_reviewed"] == 2
        assert stats["examples"] == 2  # Human with tags + corrected
        assert stats["pending"] == 1

    def test_research_context(self):
        """Test research context field."""
        session = ReviewSession(
            query="test",
            providers=["test"],
            timestamp=datetime.now(),
            research_context="Focus on privacy-preserving machine learning",
        )
        assert session.research_context == "Focus on privacy-preserving machine learning"
class TestQueryProviderPairsPersistence:
    """Tests for query-provider pair persistence."""

    def test_save_and_load_query_provider_pairs(self, tmp_path, monkeypatch):
        """Query-provider pairs are saved and loaded correctly."""
        monkeypatch.setenv("SCHOLAR_DATA_DIR", str(tmp_path))
        
        session = ReviewSession(
            query="test query",
            providers=["openalex", "wos"],
            timestamp=datetime.now(),
            name="pairs-session",
        )
        session.add_query_provider_pair("natural language", "openalex")
        session.add_query_provider_pair("boolean AND query", "wos")
        
        save_session(session)
        loaded = load_session("pairs-session")
        
        assert loaded is not None
        assert len(loaded.query_provider_pairs) == 2
        assert ("natural language", "openalex") in loaded.query_provider_pairs
        assert ("boolean AND query", "wos") in loaded.query_provider_pairs

    def test_save_and_load_references_citations(self, tmp_path, monkeypatch):
        """References and citations are persisted with the session."""
        monkeypatch.setenv("SCHOLAR_DATA_DIR", str(tmp_path))

        # Create paper with refs and cites
        ref = Paper(title="Reference Paper", authors=["Ref Author"], year=2020,
                    doi="10.1000/ref")
        cite = Paper(title="Citing Paper", authors=["Cite Author"], year=2024,
                     doi="10.1000/cite")
        paper = Paper(
            title="Main Paper", authors=["Main Author"], year=2022,
            doi="10.1000/main",
            references=[ref],
            citations=[cite],
        )

        session = ReviewSession(
            query="test",
            providers=["s2"],
            timestamp=datetime.now(),
            name="refs-cites-session",
        )
        session.decisions.append(ReviewDecision(paper=paper, provider="s2"))

        save_session(session)
        loaded = load_session("refs-cites-session")

        assert loaded is not None
        assert len(loaded.decisions) == 1
        loaded_paper = loaded.decisions[0].paper

        # Check refs were persisted
        assert loaded_paper.references is not None
        assert len(loaded_paper.references) == 1
        assert loaded_paper.references[0].title == "Reference Paper"
        assert loaded_paper.references[0].doi == "10.1000/ref"

        # Check cites were persisted
        assert loaded_paper.citations is not None
        assert len(loaded_paper.citations) == 1
        assert loaded_paper.citations[0].title == "Citing Paper"
        assert loaded_paper.citations[0].doi == "10.1000/cite"

    def test_load_session_without_refs_cites(self, tmp_path, monkeypatch):
        """Old sessions without refs/cites load correctly with None values."""
        monkeypatch.setenv("SCHOLAR_DATA_DIR", str(tmp_path))

        # Create session file without refs/cites fields
        sessions_dir = tmp_path / "review_sessions"
        sessions_dir.mkdir(parents=True)
        old_session_data = {
            "query": "test",
            "name": "old-format",
            "providers": ["s2"],
            "timestamp": datetime.now().isoformat(),
            "research_context": None,
            "query_provider_pairs": [],
            "snowball_rounds": [],
            "decisions": [{
                "paper_id": "doi:10.1000/test",
                "provider": "s2",
                "status": "pending",
                "tags": [],
                "source": "human",
                "is_example": False,
                "llm_confidence": None,
                "paper": {
                    "title": "Test Paper",
                    "authors": ["Author"],
                    "year": 2024,
                    "doi": "10.1000/test",
                    "abstract": None,
                    "venue": None,
                    "url": None,
                    "pdf_url": None,
                    "sources": ["s2"],
                    # No references or citations fields
                },
            }],
        }
        session_file = sessions_dir / "old-format.json"
        with open(session_file, "w") as f:
            json.dump(old_session_data, f)

        loaded = load_session("old-format")

        assert loaded is not None
        assert len(loaded.decisions) == 1
        # Should have None for refs/cites (not fetched yet)
        assert loaded.decisions[0].paper.references is None
        assert loaded.decisions[0].paper.citations is None
def test_load_session_backward_compatibility(tmp_path, monkeypatch):
    """Old sessions without query_provider_pairs get pairs reconstructed."""
    monkeypatch.setenv("SCHOLAR_DATA_DIR", str(tmp_path))
    
    # Create session file in old format (no query_provider_pairs)
    sessions_dir = tmp_path / "review_sessions"
    sessions_dir.mkdir(parents=True)
    old_session_data = {
        "query": "old query",
        "name": "old-session",
        "providers": ["openalex", "wos"],
        "timestamp": datetime.now().isoformat(),
        "research_context": None,
        "decisions": [],
    }
    session_file = sessions_dir / "old-session.json"
    with open(session_file, "w") as f:
        json.dump(old_session_data, f)
    
    loaded = load_session("old-session")
    
    assert loaded is not None
    # Backward compat: pairs should be reconstructed from query + providers
    assert len(loaded.query_provider_pairs) == 2
    assert ("old query", "openalex") in loaded.query_provider_pairs
    assert ("old query", "wos") in loaded.query_provider_pairs
class TestSessionFunctions:
    """Tests for session creation and persistence."""

    def test_create_review_session(self):
        """Can create a review session from search results."""
        # Create mock search result
        result = Mock()
        result.provider = "test"
        result.query = "test query"
        result.papers = [
            Paper(title="Paper 1", authors=["Author"], year=2024),
        ]

        session = create_review_session([result], "test query")

        assert session.query == "test query"
        assert len(session.decisions) == 1
        assert session.decisions[0].status == DecisionStatus.PENDING
        # Check query_provider_pairs is populated
        assert len(session.query_provider_pairs) == 1
        assert ("test query", "test") in session.query_provider_pairs

    def test_create_review_session_deduplicates_papers(self):
        """Duplicate papers from multiple providers are merged."""
        r1 = Mock()
        r1.provider = "dblp"
        r1.query = "q1"
        r1.papers = [
            Paper(
                title="Paper",
                authors=["Author"],
                year=2024,
                doi="10.1234/paper",
                abstract=None,
                sources=["dblp"],
            )
        ]

        r2 = Mock()
        r2.provider = "s2"
        r2.query = "q2"
        r2.papers = [
            Paper(
                title="Paper",
                authors=["Author"],
                year=2024,
                doi="10.1234/paper",
                abstract="Has abstract",
                sources=["s2"],
            )
        ]

        session = create_review_session([r1, r2], "test query")

        assert len(session.decisions) == 1
        assert session.decisions[0].paper.abstract == "Has abstract"
        assert set(session.decisions[0].paper.sources) == {"dblp", "s2"}
        assert ("q1", "dblp") in session.query_provider_pairs
        assert ("q2", "s2") in session.query_provider_pairs

    def test_save_and_load_session(self, tmp_path, monkeypatch):
        """Can save and load a session."""
        monkeypatch.setenv("SCHOLAR_DATA_DIR", str(tmp_path))
        
        paper = Paper(title="Test Paper", authors=["Author"], year=2024)
        session = ReviewSession(
            query="test query",
            providers=["test"],
            timestamp=datetime.now(),
            name="my-session",
        )
        session.decisions.append(
            ReviewDecision(
                paper=paper,
                provider="test",
                status=DecisionStatus.KEPT,
                tags=["relevant", "ml"],
            )
        )
        
        save_session(session)
        loaded = load_session("my-session")
        
        assert loaded is not None
        assert loaded.query == "test query"
        assert len(loaded.decisions) == 1
        assert loaded.decisions[0].status == DecisionStatus.KEPT
        assert loaded.decisions[0].tags == ["relevant", "ml"]

    def test_list_sessions(self, tmp_path, monkeypatch):
        """Can list all sessions."""
        monkeypatch.setenv("SCHOLAR_DATA_DIR", str(tmp_path))
        
        session1 = ReviewSession(
            query="query1", providers=["test"], 
            timestamp=datetime.now(), name="session1"
        )
        session2 = ReviewSession(
            query="query2", providers=["test"], 
            timestamp=datetime.now(), name="session2"
        )
        
        save_session(session1)
        save_session(session2)
        
        sessions = list_sessions()
        assert len(sessions) == 2

    def test_create_session_preserves_llm_fields(self, tmp_path, monkeypatch):
        """Adding search to session preserves LLM decision metadata."""
        monkeypatch.setenv("SCHOLAR_DATA_DIR", str(tmp_path))
        
        # Create initial session with LLM-reviewed paper
        paper1 = Paper(
            title="Paper 1", authors=["Author 1"], year=2024,
            doi="10.1234/paper1"
        )
        session = ReviewSession(
            query="test query",
            providers=["openalex"],
            timestamp=datetime.now(),
            name="merge-test",
        )
        session.decisions.append(
            ReviewDecision(
                paper=paper1,
                provider="openalex",
                status=DecisionStatus.KEPT,
                tags=["ml", "privacy"],
                source=ReviewSource.LLM_REVIEWED,
                is_example=True,
                llm_confidence=0.85,
            )
        )
        save_session(session)
        
        # Add new search that includes same paper
        result = Mock()
        result.provider = "openalex"
        result.query = "new query"
        result.papers = [
            Paper(
                title="Paper 1", authors=["Author 1"], year=2024,
                doi="10.1234/paper1"  # Same paper
            ),
            Paper(
                title="Paper 2", authors=["Author 2"], year=2023,
                doi="10.1234/paper2"  # New paper
            ),
        ]
        
        new_session = create_review_session([result], "new query", "merge-test")
        
        # Find the previously-reviewed paper
        paper1_decisions = [
            d for d in new_session.decisions 
            if d.paper.doi == "10.1234/paper1"
        ]
        assert len(paper1_decisions) == 1
        dec = paper1_decisions[0]
        
        # All LLM fields should be preserved
        assert dec.status == DecisionStatus.KEPT
        assert dec.tags == ["ml", "privacy"]
        assert dec.source == ReviewSource.LLM_REVIEWED
        assert dec.is_example is True
        assert dec.llm_confidence == 0.85
        
        # New paper should be pending
        paper2_decisions = [
            d for d in new_session.decisions
            if d.paper.doi == "10.1234/paper2"
        ]
        assert len(paper2_decisions) == 1
        assert paper2_decisions[0].status == DecisionStatus.PENDING

    def test_create_session_preserves_papers_not_in_new_search(
        self, tmp_path, monkeypatch
    ):
        """Papers from previous session not in new search are preserved."""
        monkeypatch.setenv("SCHOLAR_DATA_DIR", str(tmp_path))
        
        # Create initial session with reviewed paper
        paper1 = Paper(
            title="Old Paper", authors=["Author"], year=2020,
            doi="10.1234/old"
        )
        session = ReviewSession(
            query="old query",
            providers=["openalex"],
            timestamp=datetime.now(),
            name="preserve-test",
        )
        session.decisions.append(
            ReviewDecision(
                paper=paper1,
                provider="openalex",
                status=DecisionStatus.DISCARDED,
                tags=["off-topic"],
                source=ReviewSource.HUMAN,
            )
        )
        save_session(session)
        
        # Add new search with different paper
        result = Mock()
        result.provider = "dblp"
        result.query = "new query"
        result.papers = [
            Paper(
                title="New Paper", authors=["Author 2"], year=2024,
                doi="10.1234/new"
            ),
        ]
        
        new_session = create_review_session([result], "new query", "preserve-test")
        
        # Should have both papers
        assert len(new_session.decisions) == 2
        
        # Old paper should be preserved with all metadata
        old_decisions = [
            d for d in new_session.decisions
            if d.paper.doi == "10.1234/old"
        ]
        assert len(old_decisions) == 1
        assert old_decisions[0].status == DecisionStatus.DISCARDED
        assert old_decisions[0].tags == ["off-topic"]

    def test_create_session_preserves_research_context(
        self, tmp_path, monkeypatch
    ):
        """Research context from previous session is preserved."""
        monkeypatch.setenv("SCHOLAR_DATA_DIR", str(tmp_path))
        
        session = ReviewSession(
            query="test",
            providers=["openalex"],
            timestamp=datetime.now(),
            name="context-test",
            research_context="Focus on privacy in ML",
        )
        save_session(session)
        
        result = Mock()
        result.provider = "openalex"
        result.query = "new query"
        result.papers = [
            Paper(title="Paper", authors=["Author"], year=2024),
        ]
        
        new_session = create_review_session([result], "new query", "context-test")
        
        assert new_session.research_context == "Focus on privacy in ML"
class TestFilterDecisions:
    """Tests for the filter_decisions function."""

    @pytest.fixture
    def sample_decisions(self):
        """Create sample decisions for testing."""
        return [
            ReviewDecision(
                paper=Paper(
                    title="Recent ML", authors=["Author A"], year=2023, venue="NeurIPS"
                ),
                provider="test",
            ),
            ReviewDecision(
                paper=Paper(
                    title="Older Work", authors=["Author B"], year=2018, venue="ICML"
                ),
                provider="test",
            ),
            ReviewDecision(
                paper=Paper(
                    title="Very Old", authors=["Author C"], year=2010, venue="Nature"
                ),
                provider="test",
            ),
        ]

    def test_filter_by_year(self, sample_decisions):
        """Can filter decisions by year range."""
        filters = SearchFilters(year="2015-")
        result = filter_decisions(sample_decisions, filters)
        assert len(result) == 2
        assert all(d.paper.year >= 2015 for d in result)

    def test_filter_by_venue(self, sample_decisions):
        """Can filter decisions by venue."""
        filters = SearchFilters(venue="NeurIPS")
        result = filter_decisions(sample_decisions, filters)
        assert len(result) == 1
        assert result[0].paper.title == "Recent ML"

    def test_empty_filter_returns_all(self, sample_decisions):
        """Empty filters return all decisions."""
        filters = SearchFilters()
        result = filter_decisions(sample_decisions, filters)
        assert len(result) == 3

    def test_combined_filters(self, sample_decisions):
        """Can combine multiple filters."""
        filters = SearchFilters(year="2015-", venue="ICML")
        result = filter_decisions(sample_decisions, filters)
        assert len(result) == 1
        assert result[0].paper.title == "Older Work"

    def test_no_matches_returns_empty(self, sample_decisions):
        """Returns empty list when no decisions match."""
        filters = SearchFilters(year="2025-")
        result = filter_decisions(sample_decisions, filters)
        assert result == []
class TestReportGeneration:
    """Tests for LaTeX report generation."""

    def test_generate_report_with_themes(self, tmp_path):
        """Report groups kept papers by theme."""
        paper1 = Paper(title="Paper 1", authors=["Author A"], year=2024)
        paper2 = Paper(title="Paper 2", authors=["Author B"], year=2024)
        
        session = ReviewSession(
            query="test",
            providers=["test"],
            timestamp=datetime.now(),
        )
        session.decisions = [
            ReviewDecision(
                paper=paper1, provider="test",
                status=DecisionStatus.KEPT, tags=["ml", "privacy"]
            ),
            ReviewDecision(
                paper=paper2, provider="test",
                status=DecisionStatus.KEPT, tags=["ml"]
            ),
        ]
        
        output_path = tmp_path / "report.tex"
        generate_latex_report(session, output_path)
        
        content = output_path.read_text()
        assert r"\subsection{ml}" in content
        assert r"\subsection{privacy}" in content

    def test_generate_report_with_motivations(self, tmp_path):
        """Report groups discarded papers by motivation."""
        paper = Paper(title="Discarded Paper", authors=["Author"], year=2024)

        session = ReviewSession(
            query="test",
            providers=["test"],
            timestamp=datetime.now(),
        )
        session.decisions = [
            ReviewDecision(
                paper=paper,
                provider="test",
                status=DecisionStatus.DISCARDED,
                tags=["off-topic"],
            ),
        ]

        output_path = tmp_path / "report.tex"
        generate_latex_report(session, output_path)

        content = output_path.read_text()
        assert r"\section{Discarded Papers}" in content
        assert r"\subsection{off-topic}" in content

    def test_report_includes_research_context(self, tmp_path):
        """Report includes research context when present."""
        paper = Paper(title="Paper", authors=["Author"], year=2024)

        session = ReviewSession(
            query="test",
            providers=["test"],
            timestamp=datetime.now(),
            research_context="This is the research context.",
        )
        session.decisions = [
            ReviewDecision(
                paper=paper,
                provider="test",
                status=DecisionStatus.KEPT,
                tags=["ml"],
            ),
        ]

        output_path = tmp_path / "report.tex"
        generate_latex_report(session, output_path)

        content = output_path.read_text()
        assert r"\section{Research Context}" in content
        assert "This is the research context." in content

    def test_escapes_special_characters(self, tmp_path):
        """Special characters are escaped in report."""
        paper = Paper(
            title="Test & Paper with 100% special_chars",
            authors=["O'Brien"],
            year=2024,
        )
        
        session = ReviewSession(
            query="test",
            providers=["test"],
            timestamp=datetime.now(),
        )
        session.decisions = [
            ReviewDecision(paper=paper, provider="test", status=DecisionStatus.KEPT),
        ]
        
        output_path = tmp_path / "report.tex"
        generate_latex_report(session, output_path)
        
        bib_content = output_path.with_suffix(".bib").read_text()
        assert r"\&" in bib_content
        assert r"\%" in bib_content

    def test_generate_report_with_list_table(self, tmp_path):
        """Report includes list table for kept papers with longtable."""
        paper1 = Paper(title="Paper 1", authors=["Author A"], year=2024)
        paper2 = Paper(title="Paper 2", authors=["Author B"], year=2023)

        session = ReviewSession(
            query="test",
            providers=["test"],
            timestamp=datetime.now(),
        )
        session.decisions = [
            ReviewDecision(
                paper=paper1, provider="test",
                status=DecisionStatus.KEPT, tags=["ml", "privacy"]
            ),
            ReviewDecision(
                paper=paper2, provider="test",
                status=DecisionStatus.KEPT, tags=["ml"]
            ),
        ]

        output_path = tmp_path / "report.tex"
        generate_latex_report(session, output_path)

        content = output_path.read_text()
        assert r"\begin{longtable}" in content
        assert r"\toprule" in content
        assert "Kept Papers Overview" in content

    def test_generate_report_with_matrix_table(self, tmp_path):
        """Report includes cross-tabulation matrix with checkmarks."""
        paper1 = Paper(title="Paper 1", authors=["Author A"], year=2024)
        paper2 = Paper(title="Paper 2", authors=["Author B"], year=2023)

        session = ReviewSession(
            query="test",
            providers=["test"],
            timestamp=datetime.now(),
        )
        session.decisions = [
            ReviewDecision(
                paper=paper1, provider="test",
                status=DecisionStatus.KEPT, tags=["ml", "privacy"]
            ),
            ReviewDecision(
                paper=paper2, provider="test",
                status=DecisionStatus.KEPT, tags=["ml"]
            ),
        ]

        output_path = tmp_path / "report.tex"
        generate_latex_report(session, output_path)

        content = output_path.read_text()
        assert r"$\checkmark$" in content
        assert r"\rotatebox{90}" in content

    def test_generate_report_uses_citetitle(self, tmp_path):
        """Report uses citetitle for paper titles in tables."""
        paper = Paper(title="Test Paper", authors=["Author"], year=2024)

        session = ReviewSession(
            query="test",
            providers=["test"],
            timestamp=datetime.now(),
        )
        session.decisions = [
            ReviewDecision(
                paper=paper, provider="test",
                status=DecisionStatus.KEPT, tags=["ml"]
            ),
        ]

        output_path = tmp_path / "report.tex"
        generate_latex_report(session, output_path)

        content = output_path.read_text()
        assert r"\citetitle{" in content

    def test_table_handles_no_tags(self, tmp_path):
        """Report shows list table but skips matrix when no tags present."""
        paper = Paper(title="Paper Without Tags", authors=["Author"], year=2024)

        session = ReviewSession(
            query="test",
            providers=["test"],
            timestamp=datetime.now(),
        )
        session.decisions = [
            ReviewDecision(
                paper=paper, provider="test",
                status=DecisionStatus.KEPT, tags=[]
            ),
        ]

        output_path = tmp_path / "report.tex"
        generate_latex_report(session, output_path)

        content = output_path.read_text()
        # Should have list table
        assert r"\begin{longtable}" in content
        # Should not have checkmarks (no matrix table)
        assert r"$\checkmark$" not in content

    def test_discarded_papers_tables(self, tmp_path):
        """Report includes tables for discarded papers."""
        paper = Paper(title="Discarded Paper", authors=["Author"], year=2024)

        session = ReviewSession(
            query="test",
            providers=["test"],
            timestamp=datetime.now(),
        )
        session.decisions = [
            ReviewDecision(
                paper=paper, provider="test",
                status=DecisionStatus.DISCARDED, tags=["off-topic", "not-peer-reviewed"]
            ),
        ]

        output_path = tmp_path / "report.tex"
        generate_latex_report(session, output_path)

        content = output_path.read_text()
        assert "Discarded Papers Overview" in content
        assert "off-topic" in content
        assert "not-peer-reviewed" in content
