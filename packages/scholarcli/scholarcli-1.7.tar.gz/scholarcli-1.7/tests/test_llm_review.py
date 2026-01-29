"""Tests for the LLM review module."""
import json
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from scholar.llm_review import *
from scholar.cache import save_all_caches
from scholar.llm_review import _format_paper_for_prompt, _collect_available_tags
from scholar.review import (
    ReviewSession, ReviewDecision, DecisionStatus, ReviewSource
)
from scholar.scholar import Paper


class TestDataStructures:
    """Tests for LLM review data structures."""

    def test_llm_decision_creation(self):
        """Can create an LLM decision."""
        decision = LLMDecision(
            paper_id="doi:10.1234/test",
            status="kept",
            tags=["relevant", "ml-focused"],
            confidence=0.85,
            reasoning="Paper discusses machine learning methods.",
        )
        assert decision.paper_id == "doi:10.1234/test"
        assert decision.status == "kept"
        assert decision.confidence == 0.85

    def test_llm_batch_result_creation(self):
        """Can create a batch result."""
        decisions = [
            LLMDecision(
                paper_id="doi:1",
                status="kept",
                tags=["good"],
                confidence=0.9,
                reasoning="Relevant.",
            ),
        ]
        result = LLMBatchResult(
            decisions=decisions,
            model_id="gpt-4",
            timestamp="2024-01-01T00:00:00",
        )
        assert len(result.decisions) == 1
        assert result.model_id == "gpt-4"
class TestExampleGathering:
    """Tests for example gathering functions."""

    def _create_session_with_examples(self):
        """Helper to create a session with various examples."""
        session = ReviewSession(
            query="test query",
            providers=["test"],
            timestamp=datetime.now(),
        )

        # Add some kept papers with tags
        for i in range(3):
            paper = Paper(
                title=f"Kept Paper {i}",
                authors=["Author"],
                year=2024,
                doi=f"10.1234/kept{i}",
            )
            decision = ReviewDecision(
                paper=paper,
                provider="test",
                status=DecisionStatus.KEPT,
                tags=["relevant", "ml"],
            )
            session.decisions.append(decision)

        # Add some discarded papers with tags
        for i in range(3):
            paper = Paper(
                title=f"Discarded Paper {i}",
                authors=["Author"],
                year=2024,
                doi=f"10.1234/discarded{i}",
            )
            decision = ReviewDecision(
                paper=paper,
                provider="test",
                status=DecisionStatus.DISCARDED,
                tags=["off-topic"],
            )
            session.decisions.append(decision)

        return session

    def test_get_example_decisions(self):
        """Gathers tagged examples correctly."""
        session = self._create_session_with_examples()

        kept, discarded = get_example_decisions(session)

        assert len(kept) == 3
        assert len(discarded) == 3
        assert all(d.status == DecisionStatus.KEPT for d in kept)
        assert all(d.status == DecisionStatus.DISCARDED for d in discarded)

    def test_excludes_untagged_papers(self):
        """Papers without tags are excluded from examples."""
        session = self._create_session_with_examples()

        # Add untagged paper
        paper = Paper(
            title="Untagged Paper",
            authors=["Author"],
            year=2024,
            doi="10.1234/untagged",
        )
        session.decisions.append(ReviewDecision(
            paper=paper,
            provider="test",
            status=DecisionStatus.KEPT,
            tags=[],  # No tags
        ))

        kept, discarded = get_example_decisions(session)

        # Untagged paper should not be included
        assert len(kept) == 3  # Still only the original 3

    def test_prioritizes_corrected_examples(self):
        """Corrected LLM decisions are prioritized."""
        session = ReviewSession(
            query="test",
            providers=["test"],
            timestamp=datetime.now(),
        )

        # Add regular example
        paper1 = Paper(title="Regular", authors=["A"], year=2024, doi="1")
        session.decisions.append(ReviewDecision(
            paper=paper1,
            provider="test",
            status=DecisionStatus.KEPT,
            tags=["good"],
            is_example=False,
        ))

        # Add corrected example
        paper2 = Paper(title="Corrected", authors=["A"], year=2024, doi="2")
        session.decisions.append(ReviewDecision(
            paper=paper2,
            provider="test",
            status=DecisionStatus.KEPT,
            tags=["also-good"],
            is_example=True,  # User corrected LLM
        ))

        kept, _ = get_example_decisions(session)

        # Corrected example should be first
        assert kept[0].is_example is True

    def test_validate_examples_success(self):
        """Validation passes with sufficient examples."""
        kept = [Mock() for _ in range(3)]
        discarded = [Mock() for _ in range(2)]

        is_valid, error = validate_examples(kept, discarded)

        assert is_valid is True
        assert error == ""

    def test_validate_examples_insufficient_total(self):
        """Validation fails with insufficient total examples."""
        kept = [Mock()]
        discarded = [Mock()]

        is_valid, error = validate_examples(kept, discarded)

        assert is_valid is False
        assert "at least 5" in error

    def test_validate_examples_no_kept(self):
        """Validation fails with no kept examples."""
        kept = []
        discarded = [Mock() for _ in range(5)]

        is_valid, error = validate_examples(kept, discarded)

        assert is_valid is False
        assert "kept" in error.lower()

    def test_validate_examples_no_discarded(self):
        """Validation fails with no discarded examples."""
        kept = [Mock() for _ in range(5)]
        discarded = []

        is_valid, error = validate_examples(kept, discarded)

        assert is_valid is False
        assert "discarded" in error.lower()

class TestPromptConstruction:
    """Tests for prompt construction functions."""

    def test_format_paper_for_prompt(self):
        """Papers are formatted correctly for prompts."""
        paper = Paper(
            title="Test Paper",
            authors=["Alice", "Bob", "Charlie", "David"],
            year=2024,
            abstract="This is the abstract.",
            venue="ICML",
        )
        decision = ReviewDecision(
            paper=paper,
            provider="test",
            status=DecisionStatus.KEPT,
            tags=["ml", "relevant"],
        )

        result = _format_paper_for_prompt(decision)

        assert "Test Paper" in result
        assert "Alice" in result
        assert "et al." in result  # More than 3 authors
        assert "2024" in result
        assert "ICML" in result
        assert "abstract" in result.lower()
        assert "ml, relevant" in result

    def test_format_paper_truncates_long_abstract(self):
        """Long abstracts are truncated."""
        paper = Paper(
            title="Test",
            authors=["A"],
            year=2024,
            abstract="x" * 2000,  # Very long
        )
        decision = ReviewDecision(
            paper=paper,
            provider="test",
            status=DecisionStatus.KEPT,
            tags=["test"],
        )

        result = _format_paper_for_prompt(decision)

        assert len(result) < 2000
        assert "..." in result

    def test_build_classification_prompt_includes_context(self):
        """Prompt includes research context when provided."""
        paper = Paper(title="Test", authors=["A"], year=2024)
        decision = ReviewDecision(
            paper=paper,
            provider="test",
            status=DecisionStatus.PENDING,
            tags=[],
        )

        prompt = build_classification_prompt(
            papers_to_classify=[decision],
            kept_examples=[],
            discarded_examples=[],
            research_context="Focus on privacy-preserving ML.",
        )

        assert "privacy-preserving" in prompt.lower()

    def test_build_classification_prompt_includes_examples(self):
        """Prompt includes kept and discarded examples."""
        paper = Paper(title="Test", authors=["A"], year=2024)
        to_classify = ReviewDecision(
            paper=paper,
            provider="test",
            status=DecisionStatus.PENDING,
            tags=[],
        )

        kept_paper = Paper(title="Kept Example", authors=["B"], year=2024)
        kept_example = ReviewDecision(
            paper=kept_paper,
            provider="test",
            status=DecisionStatus.KEPT,
            tags=["relevant"],
        )

        discarded_paper = Paper(
            title="Discarded Example", authors=["C"], year=2024
        )
        discarded_example = ReviewDecision(
            paper=discarded_paper,
            provider="test",
            status=DecisionStatus.DISCARDED,
            tags=["off-topic"],
        )

        prompt = build_classification_prompt(
            papers_to_classify=[to_classify],
            kept_examples=[kept_example],
            discarded_examples=[discarded_example],
        )

        assert "Kept Example" in prompt
        assert "Discarded Example" in prompt
        assert "KEPT Papers" in prompt
        assert "DISCARDED Papers" in prompt
class TestZeroShotClassification:
    """Tests for classification without example requirements."""

    def test_classify_without_examples_dry_run(self):
        """Zero-shot mode builds a prompt without raising."""
        session = ReviewSession(
            query="test",
            providers=["test"],
            timestamp=datetime.now(),
            research_context="I am studying X.",
        )
        session.decisions.append(
            ReviewDecision(
                paper=Paper(
                    title="Pending",
                    authors=["A"],
                    year=2024,
                    abstract="Abstract.",
                ),
                provider="test",
                status=DecisionStatus.PENDING,
            )
        )

        prompt = classify_papers_with_llm(
            session=session,
            count=1,
            dry_run=True,
            require_examples=False,
        )

        assert "Research Context" in prompt
        assert "Papers to Classify" in prompt
class TestLLMInteraction:
    """Tests for LLM interaction functions."""

    def test_parse_llm_response_json_in_code_block(self):
        """Parses JSON wrapped in markdown code block."""
        paper = Paper(title="Test", authors=["A"], year=2024, doi="1")
        decision = ReviewDecision(
            paper=paper,
            provider="test",
            status=DecisionStatus.PENDING,
            tags=[],
        )

        response = '''
Here's my classification:

```json
{
  "classifications": [
    {
      "paper_index": 0,
      "decision": "kept",
      "tags": ["relevant"],
      "confidence": 0.9,
      "reasoning": "Looks good."
    }
  ]
}
```
'''
        results = parse_llm_response(response, [decision])

        assert len(results) == 1
        assert results[0].status == "kept"
        assert results[0].confidence == 0.9

    def test_parse_llm_response_raw_json(self):
        """Parses raw JSON without code block."""
        paper = Paper(title="Test", authors=["A"], year=2024, doi="1")
        decision = ReviewDecision(
            paper=paper,
            provider="test",
            status=DecisionStatus.PENDING,
            tags=[],
        )

        response = '''{"classifications": [{"paper_index": 0, "decision": "discarded", "tags": ["off-topic"], "confidence": 0.8, "reasoning": "Not relevant."}]}'''

        results = parse_llm_response(response, [decision])

        assert len(results) == 1
        assert results[0].status == "discarded"

    def test_parse_llm_response_invalid_json(self):
        """Raises error for invalid JSON."""
        paper = Paper(title="Test", authors=["A"], year=2024, doi="1")
        decision = ReviewDecision(
            paper=paper,
            provider="test",
            status=DecisionStatus.PENDING,
            tags=[],
        )

        with pytest.raises(ValueError, match="Invalid JSON"):
            parse_llm_response("{invalid json}", [decision])

    def test_parse_llm_response_no_json(self):
        """Raises error when no JSON found."""
        paper = Paper(title="Test", authors=["A"], year=2024, doi="1")
        decision = ReviewDecision(
            paper=paper,
            provider="test",
            status=DecisionStatus.PENDING,
            tags=[],
        )

        with pytest.raises(ValueError, match="No JSON found"):
            parse_llm_response("No JSON here", [decision])

    def test_get_papers_needing_enrichment(self):
        """Identifies papers without abstracts."""
        paper_with = Paper(
            title="With", authors=["A"], year=2024,
            abstract="Has abstract"
        )
        paper_without = Paper(
            title="Without", authors=["A"], year=2024,
            abstract=None
        )

        decisions = [
            ReviewDecision(
                paper=paper_with,
                provider="test",
                status=DecisionStatus.PENDING,
            ),
            ReviewDecision(
                paper=paper_without,
                provider="test",
                status=DecisionStatus.PENDING,
            ),
        ]

        needing = get_papers_needing_enrichment(decisions)

        assert len(needing) == 1
        assert needing[0].title == "Without"
class TestDecisionApplication:
    """Tests for decision application functions."""

    def test_apply_llm_decisions(self):
        """LLM decisions are applied correctly."""
        from scholar.notes import get_paper_id

        paper = Paper(
            title="Test", authors=["A"], year=2024, doi="10.1234/test"
        )
        decision = ReviewDecision(
            paper=paper,
            provider="test",
            status=DecisionStatus.PENDING,
            tags=[],
        )

        session = ReviewSession(
            query="test",
            providers=["test"],
            timestamp=datetime.now(),
        )
        session.decisions.append(decision)

        # Get the actual paper_id that will be used
        paper_id = get_paper_id(paper)

        # Create LLM result with matching paper_id
        llm_decision = LLMDecision(
            paper_id=paper_id,
            status="kept",
            tags=["relevant"],
            confidence=0.85,
            reasoning="Good paper.",
        )
        batch = LLMBatchResult(
            decisions=[llm_decision],
            model_id="test",
            timestamp="2024-01-01",
        )

        updated = apply_llm_decisions(session, batch)

        # Should update correctly
        assert len(updated) == 1
        assert updated[0].status == DecisionStatus.KEPT
        assert updated[0].source == ReviewSource.LLM_UNREVIEWED
        assert updated[0].llm_confidence == 0.85

    def test_mark_as_reviewed_agrees(self):
        """Marking as reviewed when user agrees."""
        paper = Paper(title="Test", authors=["A"], year=2024)
        decision = ReviewDecision(
            paper=paper,
            provider="test",
            status=DecisionStatus.KEPT,
            tags=["relevant"],
            source=ReviewSource.LLM_UNREVIEWED,
        )

        mark_as_reviewed(decision, user_agrees=True)

        assert decision.source == ReviewSource.LLM_REVIEWED
        assert decision.is_example is False  # Not an example if agreed

    def test_mark_as_reviewed_disagrees(self):
        """Marking as reviewed when user disagrees becomes example."""
        paper = Paper(title="Test", authors=["A"], year=2024)
        decision = ReviewDecision(
            paper=paper,
            provider="test",
            status=DecisionStatus.KEPT,
            tags=["relevant"],
            source=ReviewSource.LLM_UNREVIEWED,
        )

        mark_as_reviewed(
            decision,
            user_agrees=False,
            new_status=DecisionStatus.DISCARDED,
            new_tags=["off-topic"],
        )

        assert decision.source == ReviewSource.LLM_REVIEWED
        assert decision.is_example is True  # Becomes example
        assert decision.status == DecisionStatus.DISCARDED
        assert decision.tags == ["off-topic"]

    def test_get_unreviewed_llm_decisions(self):
        """Gets unreviewed decisions sorted by confidence."""
        session = ReviewSession(
            query="test",
            providers=["test"],
            timestamp=datetime.now(),
        )

        # Add papers with different confidence levels
        for i, conf in enumerate([0.9, 0.3, 0.7]):
            paper = Paper(title=f"Paper {i}", authors=["A"], year=2024)
            decision = ReviewDecision(
                paper=paper,
                provider="test",
                status=DecisionStatus.KEPT,
                source=ReviewSource.LLM_UNREVIEWED,
                llm_confidence=conf,
            )
            session.decisions.append(decision)

        unreviewed = get_unreviewed_llm_decisions(session)

        assert len(unreviewed) == 3
        # Lowest confidence first
        assert unreviewed[0].llm_confidence == 0.3
        assert unreviewed[1].llm_confidence == 0.7
        assert unreviewed[2].llm_confidence == 0.9
class TestStatistics:
    """Tests for statistics functions."""

    def test_get_review_statistics(self):
        """Computes statistics correctly."""
        session = ReviewSession(
            query="test",
            providers=["test"],
            timestamp=datetime.now(),
        )

        # Add various decisions
        for i in range(3):
            paper = Paper(title=f"Human {i}", authors=["A"], year=2024)
            session.decisions.append(
                ReviewDecision(
                    paper=paper,
                    provider="test",
                    status=DecisionStatus.KEPT,
                    source=ReviewSource.HUMAN,
                )
            )

        for i in range(2):
            paper = Paper(title=f"LLM {i}", authors=["A"], year=2024)
            session.decisions.append(
                ReviewDecision(
                    paper=paper,
                    provider="test",
                    status=DecisionStatus.KEPT,
                    source=ReviewSource.LLM_UNREVIEWED,
                )
            )

        paper = Paper(title="Pending", authors=["A"], year=2024)
        session.decisions.append(
            ReviewDecision(
                paper=paper,
                provider="test",
                status=DecisionStatus.PENDING,
            )
        )

        paper = Paper(title="Example", authors=["A"], year=2024)
        session.decisions.append(
            ReviewDecision(
                paper=paper,
                provider="test",
                status=DecisionStatus.DISCARDED,
                source=ReviewSource.LLM_REVIEWED,
                is_example=True,
            )
        )

        stats = get_review_statistics(session)

        assert stats["human"] == 3
        assert stats["llm_unreviewed"] == 2
        assert stats["llm_reviewed"] == 1
        assert stats["pending"] == 1
        assert stats["examples"] == 1
        assert stats["total"] == 7
class TestSynthesisDataStructures:
    def test_synthesis_result_creation(self):
        result = SynthesisResult(
            synthesis="This is a test synthesis.",
            model_id="test-model",
            timestamp="2024-01-01T00:00:00",
            paper_count=5,
            themes=["theme1", "theme2"],
            references=[{"key": "smith2024", "title": "Test"}],
            theme_sections=[
                ThemeSectionResult(
                    theme="theme1",
                    title="Theme 1",
                    section="",
                    summary="",
                    paper_count=1,
                )
            ],
        )
        assert result.synthesis == "This is a test synthesis."
        assert result.paper_count == 5
        assert len(result.themes) == 2
class TestSynthesisCitationKeys:
    def test_get_author_surname_simple(self):
        from scholar.llm_review import _get_author_surname

        assert _get_author_surname("John Smith") == "Smith"
        assert _get_author_surname("Smith") == "Smith"

    def test_get_author_surname_comma_format(self):
        from scholar.llm_review import _get_author_surname

        assert _get_author_surname("Smith, John") == "Smith"
        assert _get_author_surname("van Gogh, Vincent") == "van Gogh"

    def test_generate_citation_key_single_author(self):
        from scholar.llm_review import _generate_citation_key

        paper = Paper(title="Test", authors=["Alice Smith"], year=2024)
        display, bibtex = _generate_citation_key(paper, "markdown")
        assert display == "[Smith, 2024]"
        assert bibtex == "smith2024"

    def test_generate_citation_key_two_authors(self):
        from scholar.llm_review import _generate_citation_key

        paper = Paper(
            title="Test",
            authors=["Alice Smith", "Bob Jones"],
            year=2024,
        )
        display, bibtex = _generate_citation_key(paper, "markdown")
        assert "Smith" in display
        assert "Jones" in display
        assert bibtex == "smith2024"

    def test_generate_citation_key_many_authors(self):
        from scholar.llm_review import _generate_citation_key

        paper = Paper(
            title="Test",
            authors=["Alice Smith", "Bob Jones", "Carol White"],
            year=2024,
        )
        display, bibtex = _generate_citation_key(paper, "markdown")
        assert "et al." in display
        assert bibtex == "smith2024"

    def test_generate_citation_key_latex(self):
        from scholar.llm_review import _generate_citation_key

        paper = Paper(title="Test", authors=["John Smith"], year=2024)
        display, bibtex = _generate_citation_key(paper, "latex")
        assert display == "smith2024"
        assert bibtex == "smith2024"
class TestSynthesisPrompts:
    def test_build_theme_section_prompt_includes_context(self):
        from scholar.llm_review import (
            SYNTHESIS_SECTION_START,
            SYNTHESIS_SUMMARY_START,
            build_theme_section_prompt,
            _generate_all_citation_keys,
        )

        paper = Paper(
            title="Test Paper",
            authors=["Alice Smith"],
            year=2024,
            abstract="Abstract text.",
        )
        decision = ReviewDecision(
            paper=paper,
            provider="test",
            status=DecisionStatus.KEPT,
            tags=["privacy"],
        )
        keys = _generate_all_citation_keys([decision], "markdown")
        prompt = build_theme_section_prompt(
            theme="privacy",
            kept_decisions=[decision],
            research_context="What are privacy concerns in ML?",
            citation_keys=keys,
            output_format="markdown",
        )

        assert "privacy concerns" in prompt.lower()
        assert "Test Paper" in prompt
        assert SYNTHESIS_SECTION_START in prompt
        assert SYNTHESIS_SUMMARY_START in prompt

    def test_build_conclusion_prompt_includes_summaries(self):
        from scholar.llm_review import SYNTHESIS_SECTION_START, build_conclusion_prompt

        prompt = build_conclusion_prompt(
            research_context="What are privacy concerns in ML?",
            theme_sections=[
                ThemeSectionResult(
                    theme="privacy",
                    title="Privacy methods",
                    section="",
                    summary="Key point [Smith, 2024].",
                    paper_count=1,
                )
            ],
            output_format="markdown",
        )

        assert "Key point" in prompt
        assert SYNTHESIS_SECTION_START in prompt
class TestSynthesisOrchestration:
    def test_synthesis_requires_kept_papers(self):
        session = ReviewSession(
            query="test",
            providers=["test"],
            timestamp=datetime.now(),
            research_context="Test question",
        )
        paper = Paper(title="Test", authors=["A"], year=2024)
        session.decisions.append(
            ReviewDecision(
                paper=paper,
                provider="test",
                status=DecisionStatus.PENDING,
            )
        )

        with pytest.raises(ValueError, match="No kept papers"):
            generate_literature_synthesis(session, dry_run=True)

    def test_synthesis_requires_research_context(self):
        session = ReviewSession(
            query="test",
            providers=["test"],
            timestamp=datetime.now(),
            research_context=None,
        )
        paper = Paper(title="Test", authors=["A"], year=2024)
        session.decisions.append(
            ReviewDecision(
                paper=paper,
                provider="test",
                status=DecisionStatus.KEPT,
                tags=["relevant"],
            )
        )

        with pytest.raises(ValueError, match="No research context"):
            generate_literature_synthesis(session, dry_run=True)

    def test_synthesis_dry_run_returns_prompts(self):
        session = ReviewSession(
            query="test",
            providers=["test"],
            timestamp=datetime.now(),
            research_context="What is the state of ML privacy?",
        )
        paper = Paper(
            title="Privacy in ML",
            authors=["Alice Smith"],
            year=2024,
            abstract="This paper studies privacy.",
        )
        session.decisions.append(
            ReviewDecision(
                paper=paper,
                provider="test",
                status=DecisionStatus.KEPT,
                tags=["privacy"],
            )
        )

        result = generate_literature_synthesis(session, dry_run=True)

        assert isinstance(result, str)
        assert "--- THEME PROMPT:" in result
        assert "--- CONCLUSION PROMPT ---" in result
        assert "Research Question" in result
        assert "Privacy in ML" in result
        assert "[Smith, 2024]" in result

    def test_synthesis_dry_run_uses_unthemed_when_no_tags(self):
        session = ReviewSession(
            query="test",
            providers=["test"],
            timestamp=datetime.now(),
            research_context="What is the state of ML privacy?",
        )
        paper = Paper(
            title="Privacy in ML",
            authors=["Alice Smith"],
            year=2024,
            abstract="This paper studies privacy.",
        )
        session.decisions.append(
            ReviewDecision(
                paper=paper,
                provider="test",
                status=DecisionStatus.KEPT,
                tags=[],
            )
        )

        result = generate_literature_synthesis(session, dry_run=True)

        assert "UNTHEMED" in result


class TestSynthesisCaching:
    def test_synthesis_cache_persists_to_disk(self, tmp_path, monkeypatch):
        """Theme and conclusion caches are persisted via the cache module."""
        import importlib
        import scholar.llm_review as llm_review

        monkeypatch.setenv("SCHOLAR_CACHE_DIR", str(tmp_path))

        llm_review = importlib.reload(llm_review)
        llm_review.SYNTHESIS_THEME_CACHE.clear()
        llm_review.SYNTHESIS_CONCLUSION_CACHE.clear()

        llm_review.SYNTHESIS_THEME_CACHE["k"] = {
            "theme": "privacy",
            "title": "Privacy methods",
            "section": "sec",
            "summary": "sum",
            "subquestions": ["What is privacy?"],
            "abstract": "Section abstract.",
            "paper_count": 1,
        }
        llm_review.SYNTHESIS_CONCLUSION_CACHE["c"] = {
            "conclusion": "con",
            "assembled": "assembled",
            "report_abstract": "report abstract",
        }

        save_all_caches()

        llm_review = importlib.reload(llm_review)
        assert llm_review.SYNTHESIS_THEME_CACHE.get("k")
        assert llm_review.SYNTHESIS_CONCLUSION_CACHE.get("c")

    def test_synthesis_uses_cache_on_second_run(self, monkeypatch):
        session = ReviewSession(
            query="test",
            providers=["test"],
            timestamp=datetime.now(),
            research_context="Test question",
        )
        paper = Paper(
            title="Privacy in ML",
            authors=["Alice Smith"],
            year=2024,
            abstract="This paper studies privacy.",
        )
        session.decisions.append(
            ReviewDecision(
                paper=paper,
                provider="test",
                status=DecisionStatus.KEPT,
                tags=["privacy"],
            )
        )

        class FakeResponse:
            def __init__(self, text):
                self._text = text

            def text(self):
                return self._text

        class FakeModel:
            model_id = "fake-model"

            def __init__(self):
                self.calls = 0

            def prompt(self, prompt):
                self.calls += 1

                if "Return your answer in four marked blocks" in prompt:
                    return FakeResponse(
                        "===TITLE_START===\n"
                        "Privacy methods\n"
                        "===TITLE_END===\n\n"
                        "===SUBQUESTIONS_START===\n"
                        "- What is privacy?\n"
                        "===SUBQUESTIONS_END===\n\n"
                        "===SECTION_ABSTRACT_START===\n"
                        "Section abstract.\n"
                        "===SECTION_ABSTRACT_END===\n\n"
                        "===SECTION_START===\n"
                        "### privacy\n\n"
                        "Theme synthesis [Smith, 2024].\n"
                        "===SECTION_END===\n\n"
                        "===SUMMARY_START===\n"
                        "Summary [Smith, 2024].\n"
                        "===SUMMARY_END==="
                    )

                if "Theme keyword:" in prompt:
                    return FakeResponse(
                        "===TITLE_START===\n"
                        "Improved title\n"
                        "===TITLE_END==="
                    )

                if "Return your answer as a marked block" in prompt:
                    return FakeResponse(
                        "===REPORT_ABSTRACT_START===\n"
                        "Overall abstract.\n"
                        "===REPORT_ABSTRACT_END==="
                    )

                return FakeResponse(
                    "===SECTION_START===\n"
                    "Conclusion [Smith, 2024].\n"
                    "===SECTION_END==="
                )

        fake_model = FakeModel()

        class FakeLLMModule:
            def get_model(self, _model_id=None):
                return fake_model

        import scholar.llm_review as llm_review

        monkeypatch.setattr(llm_review, "llm", FakeLLMModule(), raising=False)

        # Ensure empty caches for this test.
        llm_review.SYNTHESIS_THEME_CACHE.clear()
        llm_review.SYNTHESIS_CONCLUSION_CACHE.clear()

        result1 = generate_literature_synthesis(session, model_id="fake")
        calls_after_first = fake_model.calls
        assert calls_after_first == 3

        result2 = generate_literature_synthesis(session, model_id="fake")
        assert fake_model.calls == calls_after_first
        assert result1.synthesis == result2.synthesis

    def test_synthesis_cache_invalidates_on_abstract_change(self, monkeypatch):
        session = ReviewSession(
            query="test",
            providers=["test"],
            timestamp=datetime.now(),
            research_context="Test question",
        )
        paper = Paper(
            title="Privacy in ML",
            authors=["Alice Smith"],
            year=2024,
            abstract="Old abstract",
        )
        decision = ReviewDecision(
            paper=paper,
            provider="test",
            status=DecisionStatus.KEPT,
            tags=["privacy"],
        )
        session.decisions.append(decision)

        class FakeResponse:
            def __init__(self, text):
                self._text = text

            def text(self):
                return self._text

        class FakeModel:
            model_id = "fake-model"

            def __init__(self):
                self.calls = 0

            def prompt(self, prompt):
                self.calls += 1

                if "Return your answer in four marked blocks" in prompt:
                    return FakeResponse(
                        "===TITLE_START===\n"
                        "Privacy methods\n"
                        "===TITLE_END===\n\n"
                        "===SUBQUESTIONS_START===\n"
                        "- What is privacy?\n"
                        "===SUBQUESTIONS_END===\n\n"
                        "===SECTION_ABSTRACT_START===\n"
                        "Section abstract.\n"
                        "===SECTION_ABSTRACT_END===\n\n"
                        "===SECTION_START===\n"
                        "### privacy\n\n"
                        "Theme synthesis [Smith, 2024].\n"
                        "===SECTION_END===\n\n"
                        "===SUMMARY_START===\n"
                        "Summary [Smith, 2024].\n"
                        "===SUMMARY_END==="
                    )

                if "Theme keyword:" in prompt:
                    return FakeResponse(
                        "===TITLE_START===\n"
                        "Improved title\n"
                        "===TITLE_END==="
                    )

                if "Return your answer as a marked block" in prompt:
                    return FakeResponse(
                        "===REPORT_ABSTRACT_START===\n"
                        "Overall abstract.\n"
                        "===REPORT_ABSTRACT_END==="
                    )

                return FakeResponse(
                    "===SECTION_START===\n"
                    "Conclusion [Smith, 2024].\n"
                    "===SECTION_END==="
                )

        fake_model = FakeModel()

        class FakeLLMModule:
            def get_model(self, _model_id=None):
                return fake_model

        import scholar.llm_review as llm_review

        monkeypatch.setattr(llm_review, "llm", FakeLLMModule(), raising=False)

        llm_review.SYNTHESIS_THEME_CACHE.clear()
        llm_review.SYNTHESIS_CONCLUSION_CACHE.clear()

        generate_literature_synthesis(session, model_id="fake")
        calls_after_first = fake_model.calls

        # Simulate enrichment: abstract changes should invalidate.
        decision.paper.abstract = "New abstract"

        generate_literature_synthesis(session, model_id="fake")
        assert fake_model.calls == calls_after_first + 3
