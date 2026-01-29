"""
Persistent storage for paper notes and search decisions.

Notes are global (per-paper) and persist forever.
Search decisions are per-query and help restore previous review state.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
import hashlib
import json
import os

import click
import platformdirs

# File names for persistent storage
NOTES_FILE = "paper_notes.json"
DECISIONS_DIR = "search_decisions"


@dataclass
class PaperNote:
    """
    A note attached to a paper.

    Notes are identified by paper_id (DOI or hash of title+author).
    The title is stored for display purposes in the notes browser.
    Timestamps are stored as datetime objects internally, but serialized
    to ISO format strings for JSON storage.
    """

    paper_id: str
    title: str
    note: str
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "paper_id": self.paper_id,
            "title": self.title,
            "note": self.note,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PaperNote":
        """Create from dictionary, parsing ISO timestamps to datetime."""
        return cls(
            paper_id=data["paper_id"],
            title=data["title"],
            note=data["note"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )


@dataclass
class ReviewDecisionRecord:
    """
    A single review decision for a paper within a search.

    Stores the status (keep/discard/pending), tags (themes for kept papers,
    motivations for discarded), and paper details needed for reconstruction
    when merging sessions.

    The [[tags]] field replaces the older [[motivation]] field. For backward
    compatibility, [[motivation]] is kept as a property that accesses the
    first tag.

    LLM-related fields track whether the decision was made by human or LLM,
    whether this paper is a training example for future LLM rounds, and the
    LLM's confidence score (if applicable).
    """

    status: str  # "kept", "discarded", "pending"
    tags: list[str] = field(default_factory=list)
    # Paper details for reconstruction
    title: str = ""
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    doi: str | None = None
    abstract: str | None = None
    venue: str | None = None
    url: str | None = None
    pdf_url: str | None = None
    provider: str = ""
    # LLM-related fields
    source: str = "human"  # "human", "llm", "llm_reviewed"
    is_example: bool = False  # True if user corrected an LLM decision
    llm_confidence: float | None = None  # 0.0-1.0 if LLM decided

    @property
    def motivation(self) -> str:
        """Get first tag as motivation (backward compatibility)."""
        return self.tags[0] if self.tags else ""

    @motivation.setter
    def motivation(self, value: str) -> None:
        """Set motivation as single tag (backward compatibility)."""
        if value:
            if not self.tags:
                self.tags = [value]
            else:
                self.tags[0] = value
        elif self.tags:
            self.tags = self.tags[1:]  # Remove first tag

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "status": self.status,
            "tags": self.tags,
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "doi": self.doi,
            "abstract": self.abstract,
            "venue": self.venue,
            "url": self.url,
            "pdf_url": self.pdf_url,
            "provider": self.provider,
            "source": self.source,
            "is_example": self.is_example,
            "llm_confidence": self.llm_confidence,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReviewDecisionRecord":
        """Create from dictionary, handling both old and new formats."""
        # Handle old format with 'motivation' field
        tags = data.get("tags", [])
        if not tags and data.get("motivation"):
            tags = [data["motivation"]]

        return cls(
            status=data.get("status", "pending"),
            tags=tags,
            title=data.get("title", ""),
            authors=data.get("authors", []),
            year=data.get("year"),
            doi=data.get("doi"),
            abstract=data.get("abstract"),
            venue=data.get("venue"),
            url=data.get("url"),
            pdf_url=data.get("pdf_url"),
            provider=data.get("provider", ""),
            source=data.get("source", "human"),
            is_example=data.get("is_example", False),
            llm_confidence=data.get("llm_confidence"),
        )


@dataclass
class SearchDecisions:
    """
    All review decisions for a specific search query.

    Decisions are keyed by paper_id, allowing lookup when the same
    paper appears in a repeated search.
    """

    query: str
    query_hash: str
    decisions: dict[str, ReviewDecisionRecord] = field(default_factory=dict)
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "query": self.query,
            "query_hash": self.query_hash,
            "decisions": {
                pid: dec.to_dict() for pid, dec in self.decisions.items()
            },
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SearchDecisions":
        """Create from dictionary."""
        decisions = {
            pid: ReviewDecisionRecord.from_dict(dec)
            for pid, dec in data.get("decisions", {}).items()
        }
        return cls(
            query=data["query"],
            query_hash=data["query_hash"],
            decisions=decisions,
            timestamp=data.get("timestamp", ""),
        )


def get_paper_id(paper: Any) -> str:
    """
    Generate a stable identifier for a paper.

    This is a wrapper around the Paper.id property for backward compatibility.
    Uses DOI if available, otherwise SHA256 hash of normalized
    title + first author's last name.

    Args:
        paper: A Paper object with title, authors, and optional doi.

    Returns:
        A string identifier unique to this paper.
    """
    return paper.id


def get_query_hash(query: str) -> str:
    """
    Generate a hash for a search query.

    Used as filename for storing search decisions.
    """
    normalized = query.lower().strip()
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


def get_data_dir() -> Path:
    """
    Return the platform-appropriate data directory for Scholar.

    The directory is created if it doesn't exist.
    Can be overridden with SCHOLAR_DATA_DIR environment variable.
    """
    data_dir = os.environ.get("SCHOLAR_DATA_DIR")
    if data_dir:
        path = Path(data_dir)
    else:
        path = Path(platformdirs.user_data_dir("scholar"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_decisions_dir() -> Path:
    """
    Return the directory for storing search decisions.

    Creates the directory if it doesn't exist.
    """
    path = get_data_dir() / DECISIONS_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def _load_all_notes() -> dict[str, PaperNote]:
    """
    Load all paper notes from disk.

    Returns empty dict if file doesn't exist or is corrupted.
    """
    notes_file = get_data_dir() / NOTES_FILE
    if not notes_file.exists():
        return {}
    try:
        with open(notes_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            pid: PaperNote.from_dict(note_data)
            for pid, note_data in data.items()
        }
    except (json.JSONDecodeError, OSError, KeyError):
        return {}


def _save_all_notes(notes: dict[str, PaperNote]) -> None:
    """
    Save all paper notes to disk.
    """
    notes_file = get_data_dir() / NOTES_FILE
    data = {pid: note.to_dict() for pid, note in notes.items()}
    try:
        with open(notes_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except OSError:
        pass  # Silently fail if we can't write


def get_note(paper: Any) -> PaperNote | None:
    """
    Get the note for a paper, if one exists.

    Args:
        paper: A Paper object.

    Returns:
        PaperNote if found, None otherwise.
    """
    paper_id = get_paper_id(paper)
    notes = _load_all_notes()
    return notes.get(paper_id)


def save_note(paper: Any, note_text: str) -> PaperNote:
    """
    Save or update a note for a paper.

    Args:
        paper: A Paper object.
        note_text: The markdown note content.

    Returns:
        The saved PaperNote object.
    """
    paper_id = get_paper_id(paper)
    notes = _load_all_notes()

    now = datetime.now()

    if paper_id in notes:
        # Update existing note
        existing = notes[paper_id]
        notes[paper_id] = PaperNote(
            paper_id=paper_id,
            title=paper.title,
            note=note_text,
            created_at=existing.created_at,
            updated_at=now,
        )
    else:
        # Create new note
        notes[paper_id] = PaperNote(
            paper_id=paper_id,
            title=paper.title,
            note=note_text,
            created_at=now,
            updated_at=now,
        )

    _save_all_notes(notes)
    return notes[paper_id]


def delete_note(paper: Any) -> bool:
    """
    Delete the note for a paper.

    Args:
        paper: A Paper object.

    Returns:
        True if a note was deleted, False if no note existed.
    """
    paper_id = get_paper_id(paper)
    notes = _load_all_notes()

    if paper_id in notes:
        del notes[paper_id]
        _save_all_notes(notes)
        return True
    return False


def list_papers_with_notes() -> list[PaperNote]:
    """
    Get all papers that have notes.

    Returns:
        List of PaperNote objects, sorted by updated_at descending.
    """
    notes = _load_all_notes()
    return sorted(
        notes.values(),
        key=lambda n: n.updated_at,
        reverse=True,
    )


def has_note(paper: Any) -> bool:
    """
    Check if a paper has a note.

    Args:
        paper: A Paper object.

    Returns:
        True if the paper has a note.
    """
    paper_id = get_paper_id(paper)
    notes = _load_all_notes()
    return paper_id in notes


def export_notes(output_path: Path) -> int:
    """
    Export all notes to a JSON file.

    Args:
        output_path: Path to write the export file.

    Returns:
        Number of notes exported.
    """
    notes = _load_all_notes()
    data = {
        "version": 1,
        "exported_at": datetime.now().isoformat(),
        "notes": {pid: note.to_dict() for pid, note in notes.items()},
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return len(notes)


def import_notes(input_path: Path, merge: bool = True) -> int:
    """
    Import notes from a JSON file.

    Args:
        input_path: Path to the export file.
        merge: If True, merge with existing notes (existing take precedence).
               If False, replace all notes.

    Returns:
        Number of notes imported.
    """
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    imported_notes = {
        pid: PaperNote.from_dict(note_data)
        for pid, note_data in data.get("notes", {}).items()
    }

    if merge:
        existing = _load_all_notes()
        # Imported notes fill in gaps, existing take precedence
        for pid, note in imported_notes.items():
            if pid not in existing:
                existing[pid] = note
        _save_all_notes(existing)
        return len(imported_notes)
    else:
        _save_all_notes(imported_notes)
        return len(imported_notes)


def load_search_decisions(query: str) -> SearchDecisions | None:
    """
    Load previous decisions for a search query.

    Args:
        query: The search query string.

    Returns:
        SearchDecisions if found, None otherwise.
    """
    query_hash = get_query_hash(query)
    decisions_file = get_decisions_dir() / f"{query_hash}.json"

    if not decisions_file.exists():
        return None

    try:
        with open(decisions_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return SearchDecisions.from_dict(data)
    except (json.JSONDecodeError, OSError, KeyError):
        return None


def save_search_decisions(
    query: str, decisions: dict[str, ReviewDecisionRecord]
) -> None:
    """
    Save decisions for a search query.

    Args:
        query: The search query string.
        decisions: Dictionary mapping paper_id to ReviewDecisionRecord.
    """
    query_hash = get_query_hash(query)

    search_decisions = SearchDecisions(
        query=query,
        query_hash=query_hash,
        decisions=decisions,
        timestamp=datetime.now().isoformat(),
    )

    decisions_file = get_decisions_dir() / f"{query_hash}.json"
    try:
        with open(decisions_file, "w", encoding="utf-8") as f:
            json.dump(
                search_decisions.to_dict(), f, indent=2, ensure_ascii=False
            )
    except OSError:
        pass  # Silently fail


def get_previous_decision(
    query: str, paper: Any
) -> ReviewDecisionRecord | None:
    """
    Get the previous decision for a paper in a specific search.

    Args:
        query: The search query string.
        paper: A Paper object.

    Returns:
        ReviewDecisionRecord if found, None otherwise.
    """
    search_decisions = load_search_decisions(query)
    if search_decisions is None:
        return None

    paper_id = get_paper_id(paper)
    return search_decisions.decisions.get(paper_id)


def clear_all_decisions() -> int:
    """
    Clear all saved search decisions.

    Returns:
        Number of decision files deleted.
    """
    decisions_dir = get_decisions_dir()
    count = 0
    for decision_file in decisions_dir.glob("*.json"):
        try:
            decision_file.unlink()
            count += 1
        except OSError:
            pass
    return count


def edit_note_in_editor(paper: Any) -> str | None:
    """
    Open the user's editor to edit a note for a paper.

    Uses the VISUAL or EDITOR environment variable, with sensible
    fallbacks. The editor is opened with the existing note content
    (if any) and the result is saved.

    Args:
        paper: A Paper object.

    Returns:
        The edited note text, or None if editing was cancelled.
    """
    existing = get_note(paper)
    initial_content = existing.note if existing else ""

    # Add header comment to help user
    header = f"# Notes for: {paper.title}\n"
    header += f"# Authors: {', '.join(paper.authors[:3])}"
    if len(paper.authors) > 3:
        header += " et al."
    header += "\n"
    if paper.doi:
        header += f"# DOI: {paper.doi}\n"
    header += "# Lines starting with # are stripped.\n"
    header += (
        "# Save and close to save notes, or delete all content to cancel.\n"
    )
    header += "#" + "=" * 60 + "\n\n"

    editor_content = header + initial_content

    # Use click.edit which handles VISUAL/EDITOR env vars
    edited = click.edit(editor_content, extension=".md")

    if edited is None:
        # User closed without saving
        return None

    # Strip header comments
    lines = edited.split("\n")
    content_lines = [line for line in lines if not line.startswith("#")]
    result = "\n".join(content_lines).strip()

    if not result:
        # Empty content - don't save (or delete existing)
        if existing:
            delete_note(paper)
        return None

    save_note(paper, result)
    return result
