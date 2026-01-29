"""Tests for the CLI module."""
import pytest
from unittest.mock import Mock
from typer.testing import CliRunner

from scholar.cli import *
from scholar import *


class TestVerbosityOptions:
    """Tests for verbosity and quiet command-line options."""

    def test_verbose_option(self, monkeypatch):
        """Verbose option increases logging level."""
        from scholar import providers
        import logging

        mock_provider = Mock()
        mock_provider.name = "mock"
        mock_provider.MAX_LIMIT = None
        mock_provider.search.return_value = []
        monkeypatch.setattr(providers, "PROVIDERS", {"mock": mock_provider})

        # Test -v option
        result = runner.invoke(app, ["-v", "search", "test"])
        assert result.exit_code == 0

        # Test -vv option
        result = runner.invoke(app, ["-vv", "search", "test"])
        assert result.exit_code == 0

    def test_quiet_option(self, monkeypatch):
        """Quiet option suppresses non-error output."""
        from scholar import providers

        mock_provider = Mock()
        mock_provider.name = "mock"
        mock_provider.MAX_LIMIT = None
        mock_provider.search.return_value = []
        monkeypatch.setattr(providers, "PROVIDERS", {"mock": mock_provider})

        # Test -q option
        result = runner.invoke(app, ["-q", "search", "test"])
        assert result.exit_code == 0

        # Test -qq option
        result = runner.invoke(app, ["-qq", "search", "test"])
        assert result.exit_code == 0

        # Test -qqq option (silence all)
        result = runner.invoke(app, ["-qqq", "search", "test"])
        assert result.exit_code == 0

    def test_verbose_and_quiet_together(self, monkeypatch):
        """Verbose and quiet offset each other."""
        from scholar import providers

        mock_provider = Mock()
        mock_provider.name = "mock"
        mock_provider.MAX_LIMIT = None
        mock_provider.search.return_value = []
        monkeypatch.setattr(providers, "PROVIDERS", {"mock": mock_provider})

        # -v and -q cancel out (net 0 = WARNING)
        result = runner.invoke(app, ["-v", "-q", "search", "test"])
        assert result.exit_code == 0

        # -vv and -q = net +1 = INFO
        result = runner.invoke(app, ["-vv", "-q", "search", "test"])
        assert result.exit_code == 0

        # -v and -qq = net -1 = ERROR
        result = runner.invoke(app, ["-v", "-qq", "search", "test"])
        assert result.exit_code == 0
class TestSearchCommand:
    """Tests for the search command."""

    def test_search_command_exists(self):
        """The search command is registered."""
        result = runner.invoke(app, ["search", "--help"])
        assert result.exit_code == 0
        assert "Search bibliographic databases" in result.stdout

    def test_search_runs(self, monkeypatch):
        """Search command executes without error."""
        # Mock the provider to avoid real API calls
        from scholar import providers

        mock_provider = Mock()
        mock_provider.name = "mock"
        mock_provider.MAX_LIMIT = None
        mock_provider.search.return_value = []
        monkeypatch.setattr(providers, "PROVIDERS", {"mock": mock_provider})

        result = runner.invoke(app, ["search", "test query"])
        assert result.exit_code == 0
class TestRQCommand:
    """Tests for the rq command."""

    def test_rq_runs_and_saves_session(self, tmp_path, monkeypatch):
        """rq generates queries, searches, labels, and saves a session."""
        import json
        import sys
        import types

        from scholar import providers

        monkeypatch.setenv("SCHOLAR_DATA_DIR", str(tmp_path))

        mock_provider = Mock()
        mock_provider.name = "mock"
        mock_provider.is_available.return_value = True
        mock_provider.search.return_value = [
            Paper(
                title="Test Paper",
                authors=["Alice"],
                year=2024,
                doi="10.1234/test",
                abstract="Abstract.",
                sources=["mock"],
            )
        ]
        monkeypatch.setattr(providers, "PROVIDERS", {"mock": mock_provider})

        class DummyResponse:
            def __init__(self, text: str):
                self._text = text

            def text(self) -> str:
                return self._text

        class DummyModel:
            model_id = "dummy"

            def __init__(self):
                self._calls = 0

            def prompt(self, prompt: str):
                self._calls += 1
                if "Papers to Classify" in prompt:
                    return DummyResponse(
                        json.dumps(
                            {
                                "classifications": [
                                    {
                                        "paper_index": 0,
                                        "decision": "kept",
                                        "tags": ["theme"],
                                        "confidence": 0.9,
                                        "reasoning": "Relevant.",
                                    }
                                ]
                            }
                        )
                    )
                return DummyResponse(
                    json.dumps(
                        {
                            "queries": [
                                {"provider": "mock", "query": "test query"}
                            ]
                        }
                    )
                )

        llm_mod = types.ModuleType("llm")
        llm_mod.get_model = lambda model_id=None: DummyModel()  # noqa: E731
        sys.modules["llm"] = llm_mod

        rq_text = "How do we test rq?"
        result = runner.invoke(
            app,
            [
                "rq",
                rq_text,
                "--provider",
                "mock",
                "--count",
                "1",
                "--no-enrich",
            ],
        )
        assert result.exit_code == 0

        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in rq_text[:30])
        session_file = tmp_path / "review_sessions" / f"rq_{safe}.json"
        assert session_file.exists()

        data = json.loads(session_file.read_text(encoding="utf-8"))
        assert data["research_context"] == rq_text
        assert ("test query", "mock") in [tuple(x) for x in data["query_provider_pairs"]]
        assert data["decisions"][0]["source"] == "llm"
class TestProvidersCommand:
    """Tests for the providers command."""

    def test_providers_command_exists(self):
        """The providers command is registered."""
        result = runner.invoke(app, ["providers", "--help"])
        assert result.exit_code == 0
        assert "List available search providers" in result.stdout

    def test_providers_lists_providers(self):
        """The providers command lists available providers."""
        result = runner.invoke(app, ["providers"])
        assert result.exit_code == 0
        # Should show at least these providers
        assert "s2" in result.stdout
        assert "openalex" in result.stdout
        assert "dblp" in result.stdout

    def test_providers_shows_api_info(self):
        """The providers command shows API key information."""
        result = runner.invoke(app, ["providers"])
        assert result.exit_code == 0
        # Should show environment variable names
        assert "S2_API_KEY" in result.stdout
        assert "WOS_EXPANDED_API_KEY" in result.stdout
        assert "IEEE_API_KEY" in result.stdout
class TestSyntaxCommand:
    """Tests for the syntax command."""

    def test_syntax_command_exists(self):
        """The syntax command is registered."""
        result = runner.invoke(app, ["syntax", "--help"])
        assert result.exit_code == 0
        assert "query syntax" in result.stdout.lower()

    def test_syntax_shows_providers(self):
        """The syntax command shows all providers."""
        result = runner.invoke(app, ["syntax"])
        assert result.exit_code == 0
        assert "s2" in result.stdout
        assert "openalex" in result.stdout
        assert "dblp" in result.stdout
        assert "arxiv" in result.stdout

    def test_syntax_shows_operators(self):
        """The syntax command shows boolean operators."""
        result = runner.invoke(app, ["syntax"])
        assert result.exit_code == 0
        assert "AND" in result.stdout
        assert "OR" in result.stdout

    def test_syntax_shows_documentation_urls(self):
        """The syntax command shows documentation URLs."""
        result = runner.invoke(app, ["syntax"])
        assert result.exit_code == 0
        assert "Documentation" in result.stdout
        assert "https://" in result.stdout
class TestCacheCommand:
    """Tests for the cache command."""

    def test_cache_command_exists(self):
        """The cache command is registered."""
        result = runner.invoke(app, ["cache", "--help"])
        assert result.exit_code == 0
        assert "Manage the search result cache" in result.stdout

    def test_cache_info(self, tmp_path, monkeypatch):
        """Cache info shows statistics."""
        monkeypatch.setenv("SCHOLAR_CACHE_DIR", str(tmp_path))
        result = runner.invoke(app, ["cache", "info"])
        assert result.exit_code == 0
        assert "Location" in result.stdout
        assert "Total entries" in result.stdout

    def test_cache_clear(self, tmp_path, monkeypatch):
        """Cache clear removes cache files."""
        monkeypatch.setenv("SCHOLAR_CACHE_DIR", str(tmp_path))
        # Create a dummy cache file
        (tmp_path / "test.pkl").touch()
        result = runner.invoke(app, ["cache", "clear"])
        assert result.exit_code == 0
        assert "Cleared" in result.stdout

    def test_cache_path(self, tmp_path, monkeypatch):
        """Cache path prints directory."""
        monkeypatch.setenv("SCHOLAR_CACHE_DIR", str(tmp_path))
        result = runner.invoke(app, ["cache", "path"])
        assert result.exit_code == 0
        assert str(tmp_path) in result.stdout

    def test_cache_invalid_action(self):
        """Cache with invalid action shows error."""
        result = runner.invoke(app, ["cache", "invalid"])
        assert result.exit_code == 1
        assert "Unknown action" in result.stdout
class TestLLMCommands:
    """Tests for LLM command group."""

    def test_llm_status_session_not_found(self):
        """llm status shows error for missing session."""
        result = runner.invoke(app, ["llm", "status", "nonexistent"])
        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()

    def test_llm_context_session_not_found(self):
        """llm context shows error for missing session."""
        result = runner.invoke(app, ["llm", "context", "nonexistent"])
        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()

    def test_llm_classify_session_not_found(self):
        """llm classify shows error for missing session."""
        result = runner.invoke(app, ["llm", "classify", "nonexistent"])
        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()

    def test_llm_synthesize_session_not_found(self):
        """llm synthesize shows error for missing session."""
        result = runner.invoke(app, ["llm", "synthesize", "nonexistent"])
        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()

    def test_llm_synthesize_invalid_format(self, monkeypatch, tmp_path):
        """llm synthesize rejects invalid output format."""
        from scholar import review
        from datetime import datetime

        # Create a mock session
        session = review.ReviewSession(
            query="test",
            providers=["test"],
            timestamp=datetime.now(),
            research_context="Test question",
            name="test-session",
        )
        monkeypatch.setattr(review, "load_session", lambda x: session)

        result = runner.invoke(
            app, ["llm", "synthesize", "test-session", "--format", "invalid"]
        )
        assert result.exit_code == 1
        assert "invalid format" in result.stdout.lower()
class TestFormatters:
    """Tests for output formatters."""

    @pytest.fixture
    def sample_results(self):
        """Create sample search results for testing."""
        papers = [
            Paper(
                title="Test Paper",
                authors=["Alice", "Bob"],
                year=2024,
                doi="10.1234/test",
            ),
        ]
        return [
            SearchResult(
                query="test",
                provider="test_provider",
                timestamp="2024-01-01T00:00:00",
                papers=papers,
            )
        ]
    def test_table_formatter(self, sample_results, capsys):
        """TableFormatter produces output."""
        formatter = TableFormatter()
        formatter.format(sample_results)
        captured = capsys.readouterr()
        assert "Test Paper" in captured.out
    def test_csv_formatter(self, sample_results, capsys):
        """CSVFormatter produces tab-separated output with header."""
        formatter = CSVFormatter()
        formatter.format(sample_results)
        captured = capsys.readouterr()
        # Check metadata comments
        assert "# Query: test" in captured.out
        assert "# Provider: test_provider" in captured.out
        # Check header row
        assert "title\tauthors\tyear\tdoi\tvenue\turl" in captured.out
        # Check data row
        assert "Test Paper\tAlice; Bob\t2024\t10.1234/test" in captured.out
    def test_json_formatter(self, sample_results, capsys):
        """JSONFormatter produces valid JSON."""
        formatter = JSONFormatter()
        formatter.format(sample_results)
        captured = capsys.readouterr()
        import json
        data = json.loads(captured.out)
        assert data[0]["query"] == "test"
        assert data[0]["papers"][0]["title"] == "Test Paper"
    def test_bibtex_formatter(self, sample_results, capsys):
        """BibTeXFormatter produces BibTeX entries."""
        formatter = BibTeXFormatter()
        formatter.format(sample_results)
        captured = capsys.readouterr()
        assert "@article{" in captured.out
        assert "title = {Test Paper}" in captured.out
runner = CliRunner()


class TestCLI:
    """Tests for general CLI application functionality."""

    def test_help_displayed(self):
        """Running without args shows help with 'search' command listed."""
        result = runner.invoke(app, [])
        # Exit code 2 is expected (no command given), but help should show
        assert "search" in result.stdout
        assert "Commands" in result.stdout

    def test_explicit_help(self):
        """Running with --help shows help with exit code 0."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "search" in result.stdout

class TestSubcommandRegistration:
    """Tests for subcommand registration from snowball and tuxedo."""

    @pytest.fixture(autouse=True)
    def register_submodules(self):
        """Ensure submodules are registered before each test."""
        from scholar.cli import register_submodules

        register_submodules()

    def test_snowball_subcommand_registered(self):
        """Snowball subcommand is registered and shows help."""
        result = runner.invoke(app, ["snowball", "--help"])
        assert result.exit_code == 0
        # Should show snowball help
        assert "snowball" in result.stdout.lower() or "usage" in result.stdout.lower()

    def test_tuxedo_subcommand_registered(self):
        """Tuxedo subcommand is registered and shows help."""
        result = runner.invoke(app, ["tuxedo", "--help"])
        assert result.exit_code == 0
        # Should show tuxedo help
        assert "tuxedo" in result.stdout.lower() or "usage" in result.stdout.lower()

    def test_subcommands_appear_in_main_help(self):
        """Snowball and tuxedo appear in main help output."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        # Both should be listed as subcommands
        assert "snowball" in result.stdout.lower()
        assert "tuxedo" in result.stdout.lower()

    def test_snowball_register_commands_function_exists(self):
        """Snowball module has register_commands function."""
        import snowball

        assert hasattr(snowball, "register_commands")
        assert callable(snowball.register_commands)

    def test_tuxedo_register_commands_function_exists(self):
        """Tuxedo module has register_commands function."""
        import tuxedo

        assert hasattr(tuxedo, "register_commands")
        assert callable(tuxedo.register_commands)

