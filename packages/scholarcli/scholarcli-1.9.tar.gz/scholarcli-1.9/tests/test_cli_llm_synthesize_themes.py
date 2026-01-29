import types
import sys
from typer.testing import CliRunner
from unittest.mock import patch

from scholar.cli import app


runner = CliRunner()


def test_cli_synthesize_with_themes_and_interactive(monkeypatch, tmp_path):
    # Build a fake session with themes
    import scholar.review as review
    from scholar.review import ReviewSession, ReviewDecision, DecisionStatus
    from scholar.scholar import Paper
    from datetime import datetime

    session = ReviewSession(
        query="test",
        providers=["test"],
        timestamp=datetime.now(),
        research_context="Testing themes",
        name="test-session",
    )

    # kept paper with 'privacy' tag
    p1 = Paper(title="A", authors=["A"], year=2024, abstract="abs")
    d1 = ReviewDecision(paper=p1, provider="test", status=DecisionStatus.KEPT, tags=["privacy"])
    session.decisions.append(d1)

    # kept paper with 'ml' tag
    p2 = Paper(title="B", authors=["B"], year=2024, abstract="abs")
    d2 = ReviewDecision(paper=p2, provider="test", status=DecisionStatus.KEPT, tags=["ml"])
    session.decisions.append(d2)

    # Monkeypatch load_session
    monkeypatch.setenv("SCHOLAR_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(review, "load_session", lambda x: session)

    # Monkeypatch questionary to simulate user selecting only 'ml'
    import questionary

    class FakeQuestion:
        def __init__(self, choices):
            self.choices = choices

        def ask(self):
            return ["ml"]

    monkeypatch.setattr(questionary, "checkbox", lambda **kw: FakeQuestion(kw.get("choices")))

    # Monkeypatch generate_literature_synthesis to inspect 'selected_themes' arg
    import scholar.llm_review as llm_review

    called = {}

    def fake_generate(
        session,
        model_id=None,
        output_format="markdown",
        max_papers=None,
        dry_run=False,
        selected_themes=None,
    ):
        called["selected_themes"] = selected_themes
        return types.SimpleNamespace(
            synthesis="synth",
            paper_count=2,
            themes=[t for t in (selected_themes or []) if t is not None],
            model_id="fake",
        )

    monkeypatch.setattr(llm_review, "generate_literature_synthesis", fake_generate)

    result = runner.invoke(app, ["llm", "synthesize", "test-session", "-t", "privacy", "-t", "ml", "-i"]) 
    assert result.exit_code == 0
    assert called["selected_themes"] == ["ml"]


def test_cli_synthesize_with_themes_noninteractive(monkeypatch, tmp_path):
    import scholar.review as review
    from scholar.review import ReviewSession, ReviewDecision, DecisionStatus
    from scholar.scholar import Paper
    from datetime import datetime

    session = ReviewSession(
        query="test",
        providers=["test"],
        timestamp=datetime.now(),
        research_context="Testing themes",
        name="test-session",
    )

    p1 = Paper(title="A", authors=["A"], year=2024, abstract="abs")
    d1 = ReviewDecision(paper=p1, provider="test", status=DecisionStatus.KEPT, tags=["privacy"])
    session.decisions.append(d1)

    p2 = Paper(title="B", authors=["B"], year=2024, abstract="abs")
    d2 = ReviewDecision(paper=p2, provider="test", status=DecisionStatus.KEPT, tags=["ml"])
    session.decisions.append(d2)

    monkeypatch.setattr(review, "load_session", lambda x: session)

    import scholar.llm_review as llm_review

    called = {}

    def fake_generate(
        session,
        model_id=None,
        output_format="markdown",
        max_papers=None,
        dry_run=False,
        selected_themes=None,
    ):
        called["selected_themes"] = selected_themes
        return types.SimpleNamespace(
            synthesis="synth",
            paper_count=2,
            themes=[t for t in (selected_themes or []) if t is not None],
            model_id="fake",
        )

    monkeypatch.setattr(llm_review, "generate_literature_synthesis", fake_generate)

    result = runner.invoke(app, ["llm", "synthesize", "test-session", "-t", "privacy"]) 
    assert result.exit_code == 0
    assert called["selected_themes"] == ["privacy"]
