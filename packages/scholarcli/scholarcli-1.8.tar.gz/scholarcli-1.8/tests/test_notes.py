"""Tests for the notes persistence module."""
import json
import pytest
from pathlib import Path
from unittest.mock import Mock

from scholar import Paper
from scholar.notes import *


class TestPaperIdentity:
    """Tests for paper identity functions."""

    def test_doi_takes_precedence(self):
        """Papers with DOI use DOI as identifier."""
        paper = Paper(
            title="Test Paper",
            authors=["John Doe"],
            doi="10.1234/TEST",
        )
        pid = get_paper_id(paper)
        assert pid == "doi:10.1234/test"

    def test_hash_without_doi(self):
        """Papers without DOI use hash of title+author."""
        paper = Paper(
            title="Test Paper",
            authors=["John Doe"],
        )
        pid = get_paper_id(paper)
        assert pid.startswith("hash:")
        assert len(pid) == 5 + 16  # "hash:" + 16 hex chars

    def test_same_paper_same_id(self):
        """Same title+author produces same ID."""
        paper1 = Paper(title="Test Paper", authors=["John Doe"])
        paper2 = Paper(title="test paper", authors=["John Doe"])
        assert get_paper_id(paper1) == get_paper_id(paper2)

    def test_different_author_different_id(self):
        """Different authors produce different IDs."""
        paper1 = Paper(title="Test Paper", authors=["John Doe"])
        paper2 = Paper(title="Test Paper", authors=["Jane Smith"])
        assert get_paper_id(paper1) != get_paper_id(paper2)

    def test_no_authors(self):
        """Papers with no authors still get valid ID."""
        paper = Paper(title="Test Paper", authors=[])
        pid = get_paper_id(paper)
        assert pid.startswith("hash:")

    def test_query_hash_consistent(self):
        """Same query produces same hash."""
        assert get_query_hash("machine learning") == get_query_hash("machine learning")
        assert get_query_hash("Machine Learning") == get_query_hash("machine learning")

    def test_query_hash_different(self):
        """Different queries produce different hashes."""
        assert get_query_hash("machine learning") != get_query_hash("deep learning")
class TestDataDirectory:
    """Tests for data directory functions."""

    def test_creates_directory(self, tmp_path, monkeypatch):
        """Data directory is created if it doesn't exist."""
        data_dir = tmp_path / "scholar_data"
        monkeypatch.setenv("SCHOLAR_DATA_DIR", str(data_dir))
        result = get_data_dir()
        assert result == data_dir
        assert data_dir.exists()

    def test_respects_environment_variable(self, tmp_path, monkeypatch):
        """SCHOLAR_DATA_DIR overrides default location."""
        custom_dir = tmp_path / "custom"
        monkeypatch.setenv("SCHOLAR_DATA_DIR", str(custom_dir))
        result = get_data_dir()
        assert result == custom_dir

    def test_decisions_dir_created(self, tmp_path, monkeypatch):
        """Decisions subdirectory is created."""
        monkeypatch.setenv("SCHOLAR_DATA_DIR", str(tmp_path))
        result = get_decisions_dir()
        assert result == tmp_path / DECISIONS_DIR
        assert result.exists()
class TestPaperNotes:
    """Tests for paper notes functions."""

    def test_save_and_get_note(self, tmp_path, monkeypatch):
        """Can save and retrieve a note."""
        monkeypatch.setenv("SCHOLAR_DATA_DIR", str(tmp_path))
        
        paper = Paper(
            title="Test Paper",
            authors=["Author"],
            doi="10.1234/test",
        )
        
        save_note(paper, "This is my note.")
        
        note = get_note(paper)
        assert note is not None
        assert note.note == "This is my note."
        assert note.title == "Test Paper"

    def test_update_note(self, tmp_path, monkeypatch):
        """Updating a note preserves created_at."""
        monkeypatch.setenv("SCHOLAR_DATA_DIR", str(tmp_path))
        
        paper = Paper(
            title="Test Paper",
            authors=["Author"],
            doi="10.1234/test",
        )
        
        note1 = save_note(paper, "First note")
        created_at = note1.created_at
        
        note2 = save_note(paper, "Updated note")
        assert note2.note == "Updated note"
        assert note2.created_at == created_at
        assert note2.updated_at >= note1.updated_at

    def test_delete_note(self, tmp_path, monkeypatch):
        """Can delete a note."""
        monkeypatch.setenv("SCHOLAR_DATA_DIR", str(tmp_path))
        
        paper = Paper(
            title="Test Paper",
            authors=["Author"],
            doi="10.1234/test",
        )
        
        save_note(paper, "Note to delete")
        assert has_note(paper)
        
        result = delete_note(paper)
        assert result is True
        assert not has_note(paper)

    def test_delete_nonexistent_note(self, tmp_path, monkeypatch):
        """Deleting nonexistent note returns False."""
        monkeypatch.setenv("SCHOLAR_DATA_DIR", str(tmp_path))
        
        paper = Paper(
            title="Test",
            authors=[],
            doi="10.1234/nonexistent",
        )
        
        result = delete_note(paper)
        assert result is False

    def test_list_papers_with_notes(self, tmp_path, monkeypatch):
        """Can list all papers with notes."""
        monkeypatch.setenv("SCHOLAR_DATA_DIR", str(tmp_path))
        
        paper1 = Paper(
            title="Paper 1",
            authors=["A"],
            doi="10.1234/test1",
        )
        
        paper2 = Paper(
            title="Paper 2",
            authors=["B"],
            doi="10.1234/test2",
        )
        
        save_note(paper1, "Note 1")
        save_note(paper2, "Note 2")
        
        notes = list_papers_with_notes()
        assert len(notes) == 2
        # Most recently updated first
        assert notes[0].title == "Paper 2"

    def test_has_note(self, tmp_path, monkeypatch):
        """has_note correctly identifies papers with notes."""
        monkeypatch.setenv("SCHOLAR_DATA_DIR", str(tmp_path))
        
        paper = Paper(
            title="Test",
            authors=[],
            doi="10.1234/test",
        )
        
        assert not has_note(paper)
        save_note(paper, "A note")
        assert has_note(paper)
class TestSearchDecisions:
    """Tests for search decisions functions."""

    def test_save_and_load_decisions(self, tmp_path, monkeypatch):
        """Can save and load search decisions."""
        monkeypatch.setenv("SCHOLAR_DATA_DIR", str(tmp_path))
        
        query = "machine learning"
        decisions = {
            "doi:10.1234/test1": ReviewDecisionRecord(
                status="kept",
                tags=["relevant", "ml"]
            ),
            "doi:10.1234/test2": ReviewDecisionRecord(
                status="discarded",
                tags=["Not relevant", "wrong-domain"]
            ),
        }
        
        save_search_decisions(query, decisions)
        
        loaded = load_search_decisions(query)
        assert loaded is not None
        assert loaded.query == query
        assert len(loaded.decisions) == 2
        assert loaded.decisions["doi:10.1234/test1"].status == "kept"
        assert loaded.decisions["doi:10.1234/test1"].tags == ["relevant", "ml"]
        assert loaded.decisions["doi:10.1234/test2"].tags == ["Not relevant", "wrong-domain"]
        # Backward compat: motivation property still works
        assert loaded.decisions["doi:10.1234/test2"].motivation == "Not relevant"

    def test_load_old_format_decisions(self, tmp_path, monkeypatch):
        """Can load decisions saved in old format (motivation instead of tags)."""
        monkeypatch.setenv("SCHOLAR_DATA_DIR", str(tmp_path))
        
        # Simulate old format file
        old_format = {
            "query": "old query",
            "query_hash": get_query_hash("old query"),
            "decisions": {
                "doi:10.1234/old": {
                    "status": "discarded",
                    "motivation": "Old format motivation",
                    "title": "Old Paper",
                    "authors": [],
                }
            },
            "timestamp": "2024-01-01",
        }
        
        decisions_file = get_decisions_dir() / f"{get_query_hash('old query')}.json"
        with open(decisions_file, "w") as f:
            json.dump(old_format, f)
        
        loaded = load_search_decisions("old query")
        assert loaded is not None
        record = loaded.decisions["doi:10.1234/old"]
        # Old motivation should be converted to tags
        assert record.tags == ["Old format motivation"]
        # Backward compat property still works
        assert record.motivation == "Old format motivation"

    def test_load_nonexistent_returns_none(self, tmp_path, monkeypatch):
        """Loading nonexistent decisions returns None."""
        monkeypatch.setenv("SCHOLAR_DATA_DIR", str(tmp_path))
        
        result = load_search_decisions("nonexistent query")
        assert result is None

    def test_get_previous_decision(self, tmp_path, monkeypatch):
        """Can get previous decision for a paper."""
        monkeypatch.setenv("SCHOLAR_DATA_DIR", str(tmp_path))
        
        query = "test query"
        paper = Paper(
            title="Test",
            authors=[],
            doi="10.1234/test",
        )
        
        paper_id = get_paper_id(paper)
        decisions = {
            paper_id: ReviewDecisionRecord(status="kept"),
        }
        save_search_decisions(query, decisions)
        
        result = get_previous_decision(query, paper)
        assert result is not None
        assert result.status == "kept"

    def test_get_previous_decision_not_found(self, tmp_path, monkeypatch):
        """Returns None for paper not in previous decisions."""
        monkeypatch.setenv("SCHOLAR_DATA_DIR", str(tmp_path))
        
        query = "test query"
        paper = Paper(
            title="Unknown",
            authors=[],
            doi="10.1234/unknown",
        )
        
        result = get_previous_decision(query, paper)
        assert result is None

    def test_clear_all_decisions(self, tmp_path, monkeypatch):
        """Can clear all decisions."""
        monkeypatch.setenv("SCHOLAR_DATA_DIR", str(tmp_path))

        # Create some decisions
        save_search_decisions("query1", {})
        save_search_decisions("query2", {})

        decisions_dir = get_decisions_dir()
        assert len(list(decisions_dir.glob("*.json"))) == 2

        count = clear_all_decisions()
        assert count == 2
        assert len(list(decisions_dir.glob("*.json"))) == 0

    def test_save_and_load_llm_fields(self, tmp_path, monkeypatch):
        """LLM-related fields are saved and loaded correctly."""
        monkeypatch.setenv("SCHOLAR_DATA_DIR", str(tmp_path))

        query = "llm test query"
        decisions = {
            "doi:10.1234/llm1": ReviewDecisionRecord(
                status="kept",
                tags=["relevant"],
                source="llm",
                is_example=False,
                llm_confidence=0.85,
            ),
            "doi:10.1234/llm2": ReviewDecisionRecord(
                status="discarded",
                tags=["off-topic"],
                source="llm_reviewed",
                is_example=True,
                llm_confidence=0.45,
            ),
        }

        save_search_decisions(query, decisions)

        loaded = load_search_decisions(query)
        assert loaded is not None

        # Check first record (LLM unreviewed)
        record1 = loaded.decisions["doi:10.1234/llm1"]
        assert record1.source == "llm"
        assert record1.is_example is False
        assert record1.llm_confidence == 0.85

        # Check second record (LLM reviewed, marked as example)
        record2 = loaded.decisions["doi:10.1234/llm2"]
        assert record2.source == "llm_reviewed"
        assert record2.is_example is True
        assert record2.llm_confidence == 0.45

    def test_load_old_format_without_llm_fields(self, tmp_path, monkeypatch):
        """Old format without LLM fields loads with sensible defaults."""
        monkeypatch.setenv("SCHOLAR_DATA_DIR", str(tmp_path))

        # Simulate old format file (no LLM fields)
        old_format = {
            "query": "old llm query",
            "query_hash": get_query_hash("old llm query"),
            "decisions": {
                "doi:10.1234/old_llm": {
                    "status": "kept",
                    "tags": ["good paper"],
                    "title": "Old Paper",
                    "authors": ["Author"],
                }
            },
            "timestamp": "2024-01-01",
        }

        decisions_file = (
            get_decisions_dir() / f"{get_query_hash('old llm query')}.json"
        )
        with open(decisions_file, "w") as f:
            json.dump(old_format, f)

        loaded = load_search_decisions("old llm query")
        assert loaded is not None
        record = loaded.decisions["doi:10.1234/old_llm"]

        # Verify defaults for missing LLM fields
        assert record.source == "human"
        assert record.is_example is False
        assert record.llm_confidence is None
class TestExportImport:
    """Tests for export and import functions."""

    def test_export_notes(self, tmp_path, monkeypatch):
        """Can export notes to file."""
        monkeypatch.setenv("SCHOLAR_DATA_DIR", str(tmp_path))
        
        paper = Paper(
            title="Test Paper",
            authors=["Author"],
            doi="10.1234/test",
        )
        save_note(paper, "Test note")
        
        export_path = tmp_path / "export.json"
        count = export_notes(export_path)
        
        assert count == 1
        assert export_path.exists()
        
        with open(export_path) as f:
            data = json.load(f)
        assert "notes" in data
        assert len(data["notes"]) == 1

    def test_import_notes_merge(self, tmp_path, monkeypatch):
        """Import with merge preserves existing notes."""
        monkeypatch.setenv("SCHOLAR_DATA_DIR", str(tmp_path))
        
        # Create existing note
        paper1 = Paper(
            title="Existing",
            authors=[],
            doi="10.1234/existing",
        )
        save_note(paper1, "Existing note")
        
        # Create export file with different note
        export_data = {
            "version": 1,
            "exported_at": "2024-01-01",
            "notes": {
                "doi:10.1234/existing": {
                    "paper_id": "doi:10.1234/existing",
                    "title": "Existing",
                    "note": "Imported note (should be ignored)",
                    "created_at": "2024-01-01",
                    "updated_at": "2024-01-01",
                },
                "doi:10.1234/new": {
                    "paper_id": "doi:10.1234/new",
                    "title": "New Paper",
                    "note": "New note",
                    "created_at": "2024-01-01",
                    "updated_at": "2024-01-01",
                },
            },
        }
        export_path = tmp_path / "import.json"
        with open(export_path, "w") as f:
            json.dump(export_data, f)
        
        import_notes(export_path, merge=True)
        
        # Existing note preserved
        existing_note = get_note(paper1)
        assert existing_note.note == "Existing note"
        
        # New note imported
        notes = list_papers_with_notes()
        assert len(notes) == 2
