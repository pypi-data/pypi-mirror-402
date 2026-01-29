"""
Core review session management for systematic literature reviews.

Provides data structures and functions for managing paper review decisions,
session persistence, and report generation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
import json
import logging

from scholar.scholar import Paper, SearchFilters
from scholar.notes import (
    get_paper_id,
    get_query_hash,
    get_data_dir,
    load_search_decisions,
    save_search_decisions as notes_save_decisions,
    ReviewDecisionRecord,
)

logger = logging.getLogger(__name__)
SESSIONS_DIR = "review_sessions"


class DecisionStatus(Enum):
    """Status of a paper review decision."""

    PENDING = "pending"
    KEPT = "kept"
    DISCARDED = "discarded"


class ReviewSource(Enum):
    """Source of a review decision."""

    HUMAN = "human"  # User decided directly
    LLM_UNREVIEWED = "llm"  # LLM decided, not yet reviewed by user
    LLM_REVIEWED = "llm_reviewed"  # LLM decided, user confirmed or changed


@dataclass
class ReviewDecision:
    """
    A review decision for a single paper.

    Tracks whether the paper was kept or discarded during review,
    along with tags (themes for kept, motivations for discarded).

    Attributes:
        paper: The Paper being reviewed.
        provider: Which search provider returned this paper.
        status: Current decision status (pending/kept/discarded).
        tags: List of tags (themes for kept, motivations for discarded).
        source: Where the decision came from (human or LLM).
        is_example: True if this paper is a training example for LLM.
        llm_confidence: Confidence score from LLM (0.0-1.0), if applicable.
    """

    paper: Paper
    provider: str
    status: DecisionStatus = DecisionStatus.PENDING
    tags: list[str] = field(default_factory=list)
    source: ReviewSource = ReviewSource.HUMAN
    is_example: bool = False
    llm_confidence: float | None = None

    @property
    def is_decided(self) -> bool:
        """Check if a decision has been made."""
        return self.status != DecisionStatus.PENDING

    @property
    def is_valid(self) -> bool:
        """
        Check if the decision is valid.

        Discarded papers require at least one tag (motivation).
        Kept and pending papers are always valid.
        """
        if self.status == DecisionStatus.DISCARDED:
            return len(self.tags) > 0
        return True

    def add_tag(self, tag: str) -> None:
        """Add a tag if not already present."""
        if tag and tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        """Remove a tag if present."""
        if tag in self.tags:
            self.tags.remove(tag)

    def has_tag(self, tag: str) -> bool:
        """Check if this decision has a specific tag."""
        return tag in self.tags

    def clear_tags(self) -> None:
        """Remove all tags."""
        self.tags.clear()

    # Backward compatibility for code using 'motivation' as single string
    @property
    def motivation(self) -> str:
        """Get first tag as motivation (backward compatibility)."""
        return self.tags[0] if self.tags else ""

    @motivation.setter
    def motivation(self, value: str) -> None:
        """Set motivation as single tag (backward compatibility)."""
        self.tags = [value] if value else []


@dataclass
class SnowballRound:
    """
    Record of a snowballing round.

    Tracks when snowballing was performed, which papers were used as sources,
    the direction (references or citations), and how many new papers were added.
    """

    timestamp: datetime
    source_papers: list[str]  # Paper IDs that were snowballed from
    direction: str  # "references" or "citations"
    papers_added: int  # Count of new papers added (excluding duplicates)


@dataclass
class ReviewSession:
    """
    A complete review session with all papers and decisions.

    Maintains the search parameters and all review decisions,
    supporting sorting, filtering, and analysis operations.

    The [[research_context]] field stores a description of the research goals,
    which is used by the LLM to understand what types of papers to keep or
    discard. This context is reused across LLM classification rounds.
    """

    query: str
    providers: list[str]
    timestamp: datetime
    decisions: list[ReviewDecision] = field(default_factory=list)
    name: str | None = None  # Optional session name for persistence
    research_context: str | None = None  # Research goals for LLM review
    query_provider_pairs: list[tuple[str, str]] = field(default_factory=list)
    snowball_rounds: list[SnowballRound] = field(default_factory=list)

    @property
    def kept_papers(self) -> list[ReviewDecision]:
        """Get all papers marked as kept."""
        return [d for d in self.decisions if d.status == DecisionStatus.KEPT]

    @property
    def discarded_papers(self) -> list[ReviewDecision]:
        """Get all papers marked as discarded."""
        return [
            d for d in self.decisions if d.status == DecisionStatus.DISCARDED
        ]

    @property
    def pending_papers(self) -> list[ReviewDecision]:
        """Get all papers still pending review."""
        return [
            d for d in self.decisions if d.status == DecisionStatus.PENDING
        ]

    def all_themes(self) -> set[str]:
        """Get all unique themes from kept papers."""
        themes: set[str] = set()
        for d in self.kept_papers:
            themes.update(d.tags)
        return themes

    def all_motivations(self) -> set[str]:
        """Get all unique motivations from discarded papers."""
        motivations: set[str] = set()
        for d in self.discarded_papers:
            motivations.update(d.tags)
        return motivations

    def theme_counts(self) -> dict[str, int]:
        """Count papers per theme."""
        counts: dict[str, int] = {}
        for d in self.kept_papers:
            for tag in d.tags:
                counts[tag] = counts.get(tag, 0) + 1
        return counts

    def motivation_counts(self) -> dict[str, int]:
        """Count papers per motivation."""
        counts: dict[str, int] = {}
        for d in self.discarded_papers:
            for tag in d.tags:
                counts[tag] = counts.get(tag, 0) + 1
        return counts

    def papers_with_tag(self, tag: str) -> list[ReviewDecision]:
        """Get all decisions with a specific tag."""
        return [d for d in self.decisions if d.has_tag(tag)]

    def sort_by(self, key: str, reverse: bool = False) -> None:
        """
        Sort decisions by a paper attribute.

        Supported keys: title, year, author, provider
        """
        if key == "title":
            self.decisions.sort(
                key=lambda d: d.paper.title.lower(), reverse=reverse
            )
        elif key == "year":
            self.decisions.sort(
                key=lambda d: d.paper.year or 0, reverse=reverse
            )
        elif key == "author":
            self.decisions.sort(
                key=lambda d: (
                    d.paper.authors[0].lower() if d.paper.authors else ""
                ),
                reverse=reverse,
            )
        elif key == "provider":
            self.decisions.sort(
                key=lambda d: d.provider.lower(), reverse=reverse
            )

    def llm_unreviewed_papers(self) -> list[ReviewDecision]:
        """Get papers decided by LLM but not yet reviewed by user."""
        return [
            d
            for d in self.decisions
            if d.source == ReviewSource.LLM_UNREVIEWED
        ]

    def example_papers(self) -> list[ReviewDecision]:
        """
        Get papers that serve as training examples for LLM.

        This includes:
        - Human decisions that have tags (themes or motivations)
        - User corrections of LLM decisions (is_example=True)
        """
        return [
            d
            for d in self.decisions
            if d.is_decided
            and d.tags
            and (d.source == ReviewSource.HUMAN or d.is_example)
        ]

    def llm_review_statistics(self) -> dict[str, int]:
        """
        Get statistics about LLM review progress.

        Returns dict with counts:
        - human: Human-only decisions
        - llm_unreviewed: LLM decisions pending review
        - llm_reviewed: LLM decisions confirmed by user
        - examples: Training examples for LLM
        - pending: Papers not yet decided
        """
        human = sum(
            1
            for d in self.decisions
            if d.source == ReviewSource.HUMAN and d.is_decided
        )
        llm_unreviewed = sum(
            1
            for d in self.decisions
            if d.source == ReviewSource.LLM_UNREVIEWED
        )
        llm_reviewed = sum(
            1 for d in self.decisions if d.source == ReviewSource.LLM_REVIEWED
        )
        examples = len(self.example_papers())
        pending = len(self.pending_papers)

        return {
            "human": human,
            "llm_unreviewed": llm_unreviewed,
            "llm_reviewed": llm_reviewed,
            "examples": examples,
            "pending": pending,
        }

    def add_query_provider_pair(self, query: str, provider: str) -> None:
        """
        Add a query-provider pair if not already present.

        This tracks which query was used with which provider, enabling
        different queries for different providers (e.g., natural language
        for OpenAlex, Boolean syntax for Web of Science).
        """
        pair = (query, provider)
        if pair not in self.query_provider_pairs:
            self.query_provider_pairs.append(pair)

    def queries_for_provider(self, provider: str) -> list[str]:
        """
        Get all queries used with a specific provider.

        Returns a list of queries that were used to search the given provider.
        """
        return [q for q, p in self.query_provider_pairs if p == provider]

    def add_papers_from_snowball(
        self,
        papers: list[Paper],
        direction: str,
        source_paper_ids: list[str],
    ) -> int:
        """
        Add papers from snowballing to the session.

        Papers are tagged with 'snowball-refs' or 'snowball-cites' to indicate
        their origin. Duplicate papers (already in session) are skipped.

        Args:
            papers: Papers to add (references or citations).
            direction: Either "references" or "citations".
            source_paper_ids: IDs of papers that were snowballed from.

        Returns:
            Count of new papers added (excluding duplicates).
        """
        # Build set of existing paper IDs for deduplication
        existing_ids = {get_paper_id(d.paper) for d in self.decisions}

        # Tag papers by snowball direction
        if direction == "references":
            tag = "snowball-refs"
        else:
            tag = "snowball-cite"
        added_count = 0

        for paper in papers:
            paper_id = get_paper_id(paper)
            if paper_id not in existing_ids:
                decision = ReviewDecision(
                    paper=paper,
                    provider="snowball",
                    status=DecisionStatus.PENDING,
                    tags=[tag],
                )
                self.decisions.append(decision)
                existing_ids.add(paper_id)
                added_count += 1

        # Record the snowball round
        if added_count > 0 or source_paper_ids:
            self.snowball_rounds.append(
                SnowballRound(
                    timestamp=datetime.now(),
                    source_papers=source_paper_ids,
                    direction=direction,
                    papers_added=added_count,
                )
            )

        return added_count


def _build_previous_decision_lookup(
    previous_session: ReviewSession | None,
) -> dict[str, ReviewDecision]:
    """
    Build a lookup dict from paper_id to ReviewDecision from previous session.

    This preserves ALL decision fields including LLM-related metadata.
    """
    if not previous_session:
        return {}
    return {get_paper_id(d.paper): d for d in previous_session.decisions}


def create_review_session(
    results: list[Any],  # list[SearchResult]
    query: str,
    session_name: str | None = None,
) -> ReviewSession:
    """
    Create a review session from search results.

    Loads any previous decisions for the same query/session and merges
    them with the new search results, preserving all decision metadata.

    Args:
        results: List of SearchResult objects from a search.
        query: The search query string.
        session_name: Optional name for the session (uses query if not provided).

    Returns:
        A ReviewSession ready for review.
    """
    logger.info("Creating review session for query: %s", query)
    # Use session_name for persistence, fall back to query
    persistence_key = session_name if session_name else query

    # Load previous session (primary source - has complete decision data)
    previous_session = load_session(persistence_key)

    # Build lookup for efficient merging
    prev_decision_lookup = _build_previous_decision_lookup(previous_session)
    if prev_decision_lookup:
        logger.debug(
            "Loaded %d previous decisions from session",
            len(prev_decision_lookup),
        )

    # Fallback: load from notes module for older sessions
    previous_decisions = None
    if not prev_decision_lookup:
        previous_decisions = load_search_decisions(persistence_key)
        if previous_decisions:
            logger.debug(
                "Loaded %d previous decisions from notes module",
                len(previous_decisions.decisions),
            )

    # Create review session
    providers = list(set(r.provider for r in results))
    logger.debug("Session includes providers: %s", providers)
    session = ReviewSession(
        query=query,
        providers=providers,
        timestamp=datetime.now(),
        name=session_name,
    )

    # Preserve research context from previous session
    if previous_session and previous_session.research_context:
        session.research_context = previous_session.research_context

    # Build query-provider pairs from results
    for result in results:
        session.add_query_provider_pair(result.query, result.provider)

    # Merge with previous session's query-provider pairs (if any)
    if previous_session:
        for (
            pair_query,
            pair_provider,
        ) in previous_session.query_provider_pairs:
            session.add_query_provider_pair(pair_query, pair_provider)

    # Collect paper IDs from current search results
    current_paper_ids = set()
    for result in results:
        for paper in result.papers:
            current_paper_ids.add(get_paper_id(paper))

    # First, restore decisions for papers NOT in current search results
    if prev_decision_lookup:
        # Use session data (preserves all fields)
        for paper_id, prev_dec in prev_decision_lookup.items():
            if paper_id not in current_paper_ids:
                session.decisions.append(prev_dec)
    elif previous_decisions:
        # Fallback to notes module (older format, no LLM fields)
        for paper_id, prev in previous_decisions.decisions.items():
            if paper_id not in current_paper_ids:
                paper = Paper(
                    title=prev.title,
                    authors=prev.authors if prev.authors else [],
                    year=prev.year,
                    doi=prev.doi,
                    abstract=prev.abstract,
                    venue=prev.venue,
                    url=prev.url,
                    pdf_url=prev.pdf_url,
                    source=getattr(prev, "source", "previous"),
                )
                status = DecisionStatus.PENDING
                if prev.status == "kept":
                    status = DecisionStatus.KEPT
                elif prev.status == "discarded":
                    status = DecisionStatus.DISCARDED

                tags = extract_tags_from_record(prev)

                # Restore LLM fields from notes if available
                source = ReviewSource.HUMAN
                source_str = getattr(prev, "source", "human")
                try:
                    source = ReviewSource(source_str)
                except ValueError:
                    pass

                session.decisions.append(
                    ReviewDecision(
                        paper=paper,
                        provider=getattr(prev, "provider", "previous"),
                        status=status,
                        tags=tags,
                        source=source,
                        is_example=getattr(prev, "is_example", False),
                        llm_confidence=getattr(prev, "llm_confidence", None),
                    )
                )

    # Convert search results to review decisions, merging with previous
    decision_lookup: dict[str, ReviewDecision] = {
        get_paper_id(d.paper): d for d in session.decisions
    }

    for result in results:
        for paper in result.papers:
            paper_id = get_paper_id(paper)

            existing = decision_lookup.get(paper_id)
            if existing is not None:
                try:
                    existing.paper = existing.paper.merge_with(paper)
                except ValueError:
                    pass
                continue

            # Check for previous decision (prefer session data over notes)
            prev_dec = prev_decision_lookup.get(paper_id)
            prev_record = None
            if not prev_dec and previous_decisions:
                prev_record = previous_decisions.decisions.get(paper_id)

            if prev_dec:
                # Use previous decision but with fresh paper data
                decision = ReviewDecision(
                    paper=paper,  # Fresh paper data from search
                    provider=result.provider,
                    status=prev_dec.status,
                    tags=prev_dec.tags,
                    source=prev_dec.source,
                    is_example=prev_dec.is_example,
                    llm_confidence=prev_dec.llm_confidence,
                )
            elif prev_record:
                # Fallback to notes module format
                status = DecisionStatus.PENDING
                if prev_record.status == "kept":
                    status = DecisionStatus.KEPT
                elif prev_record.status == "discarded":
                    status = DecisionStatus.DISCARDED
                tags = extract_tags_from_record(prev_record)

                # Restore LLM fields from notes if available
                source = ReviewSource.HUMAN
                source_str = getattr(prev_record, "source", "human")
                try:
                    source = ReviewSource(source_str)
                except ValueError:
                    pass

                decision = ReviewDecision(
                    paper=paper,
                    provider=result.provider,
                    status=status,
                    tags=tags,
                    source=source,
                    is_example=getattr(prev_record, "is_example", False),
                    llm_confidence=getattr(
                        prev_record, "llm_confidence", None
                    ),
                )
            else:
                # New paper, no previous decision
                decision = ReviewDecision(
                    paper=paper,
                    provider=result.provider,
                    status=DecisionStatus.PENDING,
                )

            session.decisions.append(decision)
            decision_lookup[paper_id] = decision

    logger.info(
        "Created session with %d papers (%d kept, %d discarded, %d pending)",
        len(session.decisions),
        len(session.kept_papers),
        len(session.discarded_papers),
        len(session.pending_papers),
    )
    return session


def extract_tags_from_record(record: ReviewDecisionRecord) -> list[str]:
    """
    Extract tags from a ReviewDecisionRecord.

    Handles both old format (motivation as string) and new format (tags as list).
    """
    # Check for new tags field first
    if hasattr(record, "tags") and record.tags:
        return list(record.tags)
    # Fall back to old motivation field
    if hasattr(record, "motivation") and record.motivation:
        return [record.motivation]
    return []


def create_notes_session() -> ReviewSession:
    """
    Create a session for browsing papers with notes.

    This is a notes-only session (no keep/discard) for reviewing
    previously annotated papers.

    Returns:
        A ReviewSession containing all papers with notes.
    """
    from scholar.notes import list_papers_with_notes

    papers_with_notes = list_papers_with_notes()

    session = ReviewSession(
        query="",
        providers=[],
        timestamp=datetime.now(),
    )

    for paper_note in papers_with_notes:
        paper = Paper(
            title=paper_note.title,
            authors=getattr(paper_note, "authors", []),
            year=getattr(paper_note, "year", None),
            doi=getattr(paper_note, "doi", None),
            abstract=None,
            venue=getattr(paper_note, "venue", None),
            url=getattr(paper_note, "url", None),
            pdf_url=getattr(paper_note, "pdf_url", None),
            source="notes",
        )
        session.decisions.append(
            ReviewDecision(paper=paper, provider="notes")
        )

    return session


def _get_sessions_dir() -> Path:
    """Get the directory for storing review sessions."""
    path = get_data_dir() / SESSIONS_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_session(session: ReviewSession) -> Path:
    """
    Save a review session to disk.

    Args:
        session: The ReviewSession to save.

    Returns:
        Path to the saved session file.
    """
    # Use session name or query hash as filename
    if session.name:
        filename = f"{session.name}.json"
    else:
        filename = f"{get_query_hash(session.query)}.json"

    session_path = _get_sessions_dir() / filename
    logger.info("Saving session to %s", session_path)

    # Convert to serializable format
    data = {
        "query": session.query,
        "name": session.name,
        "providers": session.providers,
        "timestamp": session.timestamp.isoformat(),
        "research_context": session.research_context,
        "query_provider_pairs": session.query_provider_pairs,
        "snowball_rounds": [
            {
                "timestamp": r.timestamp.isoformat(),
                "source_papers": r.source_papers,
                "direction": r.direction,
                "papers_added": r.papers_added,
            }
            for r in session.snowball_rounds
        ],
        "decisions": [
            {
                "paper_id": get_paper_id(d.paper),
                "provider": d.provider,
                "status": d.status.value,
                "tags": d.tags,
                "source": d.source.value,
                "is_example": d.is_example,
                "llm_confidence": d.llm_confidence,
                "paper": d.paper.to_dict(include_refs_cites=True),
            }
            for d in session.decisions
        ],
    }

    with open(session_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.debug(
        "Saved %d decisions (%d kept, %d discarded, %d pending)",
        len(session.decisions),
        len(session.kept_papers),
        len(session.discarded_papers),
        len(session.pending_papers),
    )
    return session_path


def load_session(name_or_query: str) -> ReviewSession | None:
    """
    Load a review session from disk.

    Args:
        name_or_query: Session name or query string.

    Returns:
        The loaded ReviewSession, or None if not found.
    """
    logger.debug("Loading session: %s", name_or_query)
    sessions_dir = _get_sessions_dir()

    # Try exact name first
    session_path = sessions_dir / f"{name_or_query}.json"
    if not session_path.exists():
        # Try query hash
        session_path = sessions_dir / f"{get_query_hash(name_or_query)}.json"

    if not session_path.exists():
        logger.debug("Session not found: %s", name_or_query)
        return None

    logger.debug("Found session file: %s", session_path)
    try:
        with open(session_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        session = ReviewSession(
            query=data["query"],
            providers=data["providers"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            name=data.get("name"),
            research_context=data.get("research_context"),
        )

        # Load query_provider_pairs with backward compatibility
        if "query_provider_pairs" in data:
            session.query_provider_pairs = [
                tuple(pair) for pair in data["query_provider_pairs"]
            ]
        else:
            # Reconstruct from query and providers for old sessions
            for provider in data["providers"]:
                session.add_query_provider_pair(data["query"], provider)

        # Load snowball_rounds with backward compatibility
        if "snowball_rounds" in data:
            for round_data in data["snowball_rounds"]:
                session.snowball_rounds.append(
                    SnowballRound(
                        timestamp=datetime.fromisoformat(
                            round_data["timestamp"]
                        ),
                        source_papers=round_data["source_papers"],
                        direction=round_data["direction"],
                        papers_added=round_data["papers_added"],
                    )
                )

        for dec_data in data["decisions"]:
            paper_data = dec_data["paper"]
            # Handle legacy format where "source" was a comma-separated string
            if "sources" not in paper_data and "source" in paper_data:
                paper_data["sources"] = (
                    [s.strip() for s in paper_data["source"].split(",")]
                    if paper_data["source"]
                    else []
                )
            paper = Paper.from_dict(paper_data)
            status = DecisionStatus(dec_data["status"])
            tags = dec_data.get("tags", [])

            # Load LLM-related fields with backward compatibility
            source_str = dec_data.get("source", "human")
            try:
                source = ReviewSource(source_str)
            except ValueError:
                source = ReviewSource.HUMAN
            is_example = dec_data.get("is_example", False)
            llm_confidence = dec_data.get("llm_confidence")

            session.decisions.append(
                ReviewDecision(
                    paper=paper,
                    provider=dec_data["provider"],
                    status=status,
                    tags=tags,
                    source=source,
                    is_example=is_example,
                    llm_confidence=llm_confidence,
                )
            )

        logger.info("Loaded session with %d papers", len(session.decisions))
        return session
    except (json.JSONDecodeError, KeyError, OSError) as e:
        logger.warning("Failed to load session %s: %s", name_or_query, e)
        return None


def list_sessions() -> list[dict[str, Any]]:
    """
    List all saved review sessions.

    Returns:
        List of session metadata dictionaries with keys:
        - name: Session name or query
        - query: Original search query
        - timestamp: datetime object
        - kept: Number of kept papers
        - discarded: Number of discarded papers
        - pending: Number of pending papers
        - path: Path to session file
    """
    sessions_dir = _get_sessions_dir()
    logger.debug("Listing sessions from %s", sessions_dir)
    sessions = []

    for session_file in sessions_dir.glob("*.json"):
        try:
            with open(session_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Parse timestamp string to datetime
            timestamp_str = data.get("timestamp", "")
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
            except (ValueError, TypeError):
                timestamp = datetime.now()

            # Count decisions by status
            decisions = data.get("decisions", [])
            kept = sum(1 for d in decisions if d.get("status") == "kept")
            discarded = sum(
                1 for d in decisions if d.get("status") == "discarded"
            )
            pending = sum(
                1 for d in decisions if d.get("status") == "pending"
            )

            sessions.append(
                {
                    "name": data.get("name") or data.get("query"),
                    "query": data.get("query"),
                    "timestamp": timestamp,
                    "kept": kept,
                    "discarded": discarded,
                    "pending": pending,
                    "path": session_file,
                }
            )
        except (json.JSONDecodeError, OSError) as e:
            logger.debug(
                "Failed to read session file %s: %s", session_file, e
            )

    logger.debug("Found %d sessions", len(sessions))
    return sorted(
        sessions, key=lambda s: s.get("timestamp", datetime.min), reverse=True
    )


def save_search_decisions(
    query: str, decisions: list[ReviewDecision]
) -> None:
    """
    Save decisions for a search query (compatible with notes module).

    This function bridges the review module with the notes persistence layer,
    converting ReviewDecision objects to the format expected by notes.py.

    Args:
        query: The search query string.
        decisions: List of ReviewDecision objects.
    """
    logger.debug("Saving %d decisions for query: %s", len(decisions), query)
    # Convert to notes module format
    decision_records = {}
    for d in decisions:
        paper_id = get_paper_id(d.paper)
        decision_records[paper_id] = ReviewDecisionRecord(
            status=d.status.value,
            tags=d.tags,  # Tags = motivations for discarded, themes for kept
            title=d.paper.title,
            authors=list(d.paper.authors),
            year=d.paper.year,
            doi=d.paper.doi,
            abstract=d.paper.abstract,
            venue=d.paper.venue,
            url=d.paper.url,
            pdf_url=d.paper.pdf_url,
            provider=d.provider,
            # LLM-related fields
            source=d.source.value,
            is_example=d.is_example,
            llm_confidence=d.llm_confidence,
        )

    notes_save_decisions(query, decision_records)


def filter_decisions(
    decisions: list[ReviewDecision], filters: SearchFilters
) -> list[ReviewDecision]:
    """
    Filter a list of review decisions using the given filters.

    This function applies filters locally to an existing collection of
    decisions, without making any API calls. The filtering is based on
    each decision's paper attributes (year, venue, etc.).

    Args:
        decisions: List of ReviewDecision objects to filter.
        filters: SearchFilters specifying the filtering criteria.

    Returns:
        List of decisions whose papers match all active filters.

    Example:
        >>> from scholar.review import ReviewDecision, filter_decisions
        >>> from scholar import Paper, SearchFilters
        >>> decisions = [
        ...     ReviewDecision(paper=Paper(title="New", year=2020), provider="test"),
        ...     ReviewDecision(paper=Paper(title="Old", year=2015), provider="test"),
        ... ]
        >>> filters = SearchFilters(year="2018-")
        >>> filter_decisions(decisions, filters)
        [ReviewDecision(paper=Paper(title="New", year=2020), ...)]
    """
    if filters.is_empty():
        return decisions
    return [d for d in decisions if filters.matches(d.paper)]


def escape_bibtex(text: str) -> str:
    """Escape special BibTeX characters."""
    text = text.replace("&", r"\&")
    text = text.replace("%", r"\%")
    text = text.replace("$", r"\$")
    text = text.replace("#", r"\#")
    text = text.replace("_", r"\_")
    return text


def escape_latex(text: str) -> str:
    """
    Escape special LaTeX characters.

    Order matters: backslash must be escaped first to avoid double-escaping.
    """
    text = text.replace("\\", r"\textbackslash{}")
    replacements = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text


def markdown_to_latex(markdown_text: str) -> str:
    """
    Convert Markdown text to LaTeX using pypandoc.

    Falls back to escaped plain text if pypandoc is not available.
    """
    try:
        import pypandoc

        return pypandoc.convert_text(
            markdown_text, "latex", format="markdown"
        )
    except Exception:
        return escape_latex(markdown_text)


def get_query_provider_pairs(session: ReviewSession) -> list[tuple[str, str]]:
    """Return query/provider pairs with backward-compatible fallback."""
    if session.query_provider_pairs:
        return session.query_provider_pairs
    return [(session.query, provider) for provider in session.providers]


def provider_queries_differ(session: ReviewSession) -> bool:
    """Whether any provider-specific query differs from the base query."""
    pairs = get_query_provider_pairs(session)
    return any(query != session.query for query, _ in pairs)


def build_research_context_markdown(
    session: ReviewSession,
    heading_level: int = 3,
) -> list[str]:
    """Build the research context section as Markdown lines."""
    if not session.research_context:
        return []

    heading = "#" * heading_level
    return [
        f"{heading} Research Context",
        "",
        session.research_context,
        "",
    ]


def build_search_parameters_markdown(
    session: ReviewSession,
    heading_level: int = 3,
) -> list[str]:
    """Build search parameters (including executed queries) as Markdown lines."""
    heading = "#" * heading_level
    providers = ", ".join(session.providers)

    lines: list[str] = [
        f"{heading} Search Parameters",
        "",
        f"- Base query: {session.query}",
        f"- Providers: {providers}",
        "",
    ]

    if provider_queries_differ(session):
        heading2 = "#" * (heading_level + 1)
        lines.extend(
            [
                f"{heading2} Provider-specific queries",
                "",
                "| Provider | Query |",
                "| --- | --- |",
            ]
        )
        for query, provider in get_query_provider_pairs(session):
            lines.append(f"| {provider} | {query} |")
        lines.append("")

    return lines


def build_research_context_latex(
    session: ReviewSession,
    heading_command: str = r"\section",
) -> list[str]:
    """Build the research context section as LaTeX lines."""
    if not session.research_context:
        return []

    lines = [f"{heading_command}{{Research Context}}"]
    lines.extend(markdown_to_latex(session.research_context).splitlines())
    lines.append("")
    return lines


def build_search_parameters_latex(
    session: ReviewSession,
    heading_command: str = r"\section",
) -> list[str]:
    """Build search parameters (including executed queries) as LaTeX lines."""
    providers = ", ".join(session.providers)

    lines: list[str] = [f"{heading_command}{{Search Parameters}}", ""]
    lines.extend(
        [
            r"\begin{description}",
            f"\\item[Base query] {escape_latex(session.query)}",
            f"\\item[Providers] {escape_latex(providers)}",
            r"\end{description}",
            "",
        ]
    )

    if provider_queries_differ(session):
        lines.extend(
            [
                r"\subsection{Provider-specific queries}",
                r"\begin{longtable}{lp{10cm}}",
                r"\toprule",
                r"Provider & Query \\",
                r"\midrule",
            ]
        )
        for query, provider in get_query_provider_pairs(session):
            lines.append(
                f"{escape_latex(provider)} & {escape_latex(query)} \\\\"
            )
        lines.extend(
            [
                r"\bottomrule",
                r"\end{longtable}",
                "",
            ]
        )

    return lines


def build_review_report_abstract(session: ReviewSession) -> str:
    """Build a deterministic one-paragraph abstract for the review report."""
    kept = len(session.kept_papers)
    discarded = len(session.discarded_papers)
    pending = len(session.pending_papers)
    total = len(session.decisions)

    context = (session.research_context or "").strip()
    if context:
        first = context.splitlines()[0].strip()
        lead = first.rstrip(".") + "."
    else:
        lead = "This report documents a systematic literature review session."

    providers = ", ".join(session.providers)
    summary = (
        f"{lead} The search covered {providers} and yielded {total} papers "
        f"({kept} kept, {discarded} discarded, {pending} pending)."
    )

    if session.snowball_rounds:
        summary += (
            " Manual snowballing was used to discover additional papers."
        )

    return summary


def generate_latex_report(session: ReviewSession, output_path: Path) -> None:
    """
    Generate a LaTeX report of the review session.

    The report includes:
    - Search parameters (query, providers, date)
    - Research context (if available)
    - Summary statistics
    - Kept papers grouped by theme
    - Discarded papers grouped by motivation

    Also generates a .bib file with the same base name.

    Args:
        session: The ReviewSession to report on.
        output_path: Path for the .tex file (will also create .bib).
    """

    def make_cite_key(paper: Paper, index: int) -> str:
        """Generate a unique citation key for a paper."""
        if paper.authors:
            first_author = paper.authors[0].split()[-1].lower()
            first_author = "".join(c for c in first_author if c.isalnum())
        else:
            first_author = "unknown"
        year = paper.year or "nd"
        return f"{first_author}{year}_{index}"

    def format_bibtex_entry(paper: Paper, cite_key: str) -> str:
        """Format a paper as a BibTeX entry."""
        lines = [f"@article{{{cite_key},"]
        lines.append(f"  title = {{{escape_bibtex(paper.title)}}},")
        if paper.authors:
            authors = " and ".join(paper.authors)
            lines.append(f"  author = {{{escape_bibtex(authors)}}},")
        if paper.year:
            lines.append(f"  year = {{{paper.year}}},")
        if paper.venue:
            lines.append(f"  journal = {{{escape_bibtex(paper.venue)}}},")
        if paper.doi:
            lines.append(f"  doi = {{{paper.doi}}},")
        if paper.url:
            lines.append(f"  url = {{{paper.url}}},")
        lines.append("}")
        return "\n".join(lines)

    def format_list_table(
        decisions: list[ReviewDecision],
        cite_keys: dict[int, str],
        tag_label: str,
    ) -> list[str]:
        """
        Generate LaTeX for a list table with Title, Year, Tags columns.

        Uses \\citetitle for paper titles to leverage biblatex formatting.
        """
        lines = [
            r"\begin{longtable}{>{\raggedright\arraybackslash}p{0.55\textwidth}"
            r"c>{\raggedright\arraybackslash}p{0.25\textwidth}}",
            r"\toprule",
            f"\\textbf{{Title}} & \\textbf{{Year}} & \\textbf{{{tag_label}}} \\\\",
            r"\midrule",
            r"\endhead",
            r"\bottomrule",
            r"\endlastfoot",
        ]
        for decision in decisions:
            cite_key = cite_keys[id(decision)]
            year = decision.paper.year or "---"
            tags = ", ".join(escape_latex(t) for t in sorted(decision.tags))
            lines.append(f"\\citetitle{{{cite_key}}} & {year} & {tags} \\\\")
        lines.append(r"\end{longtable}")
        return lines

    def format_matrix_table(
        decisions: list[ReviewDecision],
        cite_keys: dict[int, str],
        tags: set[str],
    ) -> list[str]:
        """
        Generate LaTeX for a cross-tabulation matrix (papers x tags).

        Uses \\citetitle for paper titles and \\checkmark for presence.
        """
        sorted_tags = sorted(tags)
        num_tags = len(sorted_tags)

        # Build column spec: title column + one centered column per tag
        col_spec = (
            r">{\raggedright\arraybackslash}p{0.4\textwidth}" + "c" * num_tags
        )

        lines = [
            f"\\begin{{longtable}}{{{col_spec}}}",
            r"\toprule",
        ]

        # Header row with rotated tag names
        header_cells = [r"\textbf{Title}"]
        for tag in sorted_tags:
            header_cells.append(f"\\rotatebox{{90}}{{{escape_latex(tag)}}}")
        lines.append(" & ".join(header_cells) + r" \\")
        lines.append(r"\midrule")
        lines.append(r"\endhead")
        lines.append(r"\bottomrule")
        lines.append(r"\endlastfoot")

        # Data rows
        for decision in decisions:
            cite_key = cite_keys[id(decision)]
            row_cells = [f"\\citetitle{{{cite_key}}}"]
            for tag in sorted_tags:
                if decision.has_tag(tag):
                    row_cells.append(r"$\checkmark$")
                else:
                    row_cells.append("")
            lines.append(" & ".join(row_cells) + r" \\")

        lines.append(r"\end{longtable}")
        return lines

    # Generate citation keys for all papers
    all_decisions = session.kept_papers + session.discarded_papers
    cite_keys: dict[int, str] = {}
    for i, decision in enumerate(all_decisions):
        cite_keys[id(decision)] = make_cite_key(decision.paper, i)

    # Generate .bib file
    bib_entries = []
    for decision in all_decisions:
        cite_key = cite_keys[id(decision)]
        bib_entries.append(format_bibtex_entry(decision.paper, cite_key))

    bib_path = output_path.with_suffix(".bib")
    bib_path.write_text("\n\n".join(bib_entries))

    # Generate .tex file
    lines = [
        r"\documentclass{article}",
        r"\usepackage[utf8]{inputenc}",
        r"\usepackage[colorlinks=true,allcolors=blue]{hyperref}",
        r"\usepackage{enumitem}",
        r"\usepackage{longtable}",
        r"\usepackage{booktabs}",
        r"\usepackage{array}",
        r"\usepackage{amssymb}",
        r"\usepackage{graphicx}",
        r"\usepackage[backend=biber,style=authoryear]{biblatex}",
        f"\\addbibresource{{{bib_path.name}}}",
        r"",
        r"\title{Literature Review Report}",
        f"\\date{{{session.timestamp.strftime('%Y-%m-%d')}}}",
        r"",
        r"\begin{document}",
        r"\maketitle",
        r"",
        r"\begin{abstract}",
        build_review_report_abstract(session),
        r"\end{abstract}",
        r"\clearpage",
        r"\clearpage",
        r"\tableofcontents",
        r"\clearpage",
        r"",
    ]

    lines.extend(
        build_research_context_latex(session, heading_command=r"\section")
    )
    lines.extend(
        build_search_parameters_latex(session, heading_command=r"\section")
    )

    lines.extend(
        [
            r"\begin{description}",
            f"\\item[Date] {session.timestamp.strftime('%Y-%m-%d %H:%M')}",
            f"\\item[Total Papers] {len(session.decisions)}",
            r"\end{description}",
            r"",
            r"\section{Summary}",
            r"\begin{description}",
            f"\\item[Kept] {len(session.kept_papers)}",
            f"\\item[Discarded] {len(session.discarded_papers)}",
            f"\\item[Pending] {len(session.pending_papers)}",
            r"\end{description}",
            r"",
        ]
    )

    # Snowballing section (if any rounds were performed)
    if session.snowball_rounds:
        lines.extend(
            [
                r"\section{Snowballing}",
                r"",
                r"Manual snowballing was performed to discover additional papers",
                r"through citations and references of kept papers.",
                r"",
                r"\begin{longtable}{llcl}",
                r"\toprule",
                r"Round & Direction & Papers Added & Source Papers \\",
                r"\midrule",
            ]
        )
        for i, round_info in enumerate(session.snowball_rounds, 1):
            direction = (
                "References"
                if round_info.direction == "references"
                else "Citations"
            )
            source_count = len(round_info.source_papers)
            source_label = (
                f"{source_count} paper{'s' if source_count != 1 else ''}"
            )
            lines.append(
                f"{i} & {direction} & {round_info.papers_added} & {source_label} \\\\"
            )
        lines.extend(
            [
                r"\bottomrule",
                r"\end{longtable}",
                r"",
            ]
        )

        # Summary of snowball-tagged papers
        snowball_refs = [
            d for d in session.kept_papers if d.has_tag("snowball-refs")
        ]
        snowball_cite = [
            d for d in session.kept_papers if d.has_tag("snowball-cite")
        ]
        if snowball_refs or snowball_cite:
            lines.extend(
                [
                    r"\subsection{Papers Added via Snowballing}",
                    r"\begin{description}",
                ]
            )
            if snowball_refs:
                lines.append(
                    f"\\item[From references] {len(snowball_refs)} papers"
                )
            if snowball_cite:
                lines.append(
                    f"\\item[From citations] {len(snowball_cite)} papers"
                )
            lines.extend(
                [
                    r"\end{description}",
                    r"",
                ]
            )

    # Summary Tables section
    if session.kept_papers or session.discarded_papers:
        lines.extend(
            [
                r"\section{Summary Tables}",
                r"",
            ]
        )

        if session.kept_papers:
            lines.extend(
                [
                    r"\subsection{Kept Papers Overview}",
                    r"",
                ]
            )
            lines.extend(
                format_list_table(session.kept_papers, cite_keys, "Themes")
            )
            lines.append(r"")
            themes = session.all_themes()
            if themes:
                lines.extend(
                    format_matrix_table(
                        session.kept_papers, cite_keys, themes
                    )
                )
                lines.append(r"")

        if session.discarded_papers:
            lines.extend(
                [
                    r"\subsection{Discarded Papers Overview}",
                    r"",
                ]
            )
            lines.extend(
                format_list_table(
                    session.discarded_papers, cite_keys, "Motivations"
                )
            )
            lines.append(r"")
            motivations = session.all_motivations()
            if motivations:
                lines.extend(
                    format_matrix_table(
                        session.discarded_papers, cite_keys, motivations
                    )
                )
                lines.append(r"")

    # Kept papers section - grouped by theme
    if session.kept_papers:
        lines.extend(
            [
                r"\section{Kept Papers}",
            ]
        )

        themes = session.all_themes()
        if themes:
            # Group by theme
            for theme in sorted(themes):
                papers_with_theme = [
                    d for d in session.kept_papers if d.has_tag(theme)
                ]
                lines.append(f"\\subsection{{{escape_latex(theme)}}}")
                lines.append(r"\begin{enumerate}")
                for decision in papers_with_theme:
                    cite_key = cite_keys[id(decision)]
                    lines.append(f"\\item \\fullcite{{{cite_key}}}")
                lines.append(r"\end{enumerate}")
                lines.append("")
        else:
            # No themes, just list papers
            lines.append(r"\begin{enumerate}")
            for decision in session.kept_papers:
                cite_key = cite_keys[id(decision)]
                lines.append(f"\\item \\fullcite{{{cite_key}}}")
            lines.append(r"\end{enumerate}")
            lines.append("")

    # Discarded papers section - grouped by motivation
    if session.discarded_papers:
        lines.extend(
            [
                r"\section{Discarded Papers}",
            ]
        )

        motivations = session.all_motivations()
        if motivations:
            # Group by motivation
            for motivation in sorted(motivations):
                papers_with_motivation = [
                    d
                    for d in session.discarded_papers
                    if d.has_tag(motivation)
                ]
                lines.append(f"\\subsection{{{escape_latex(motivation)}}}")
                lines.append(r"\begin{enumerate}")
                for decision in papers_with_motivation:
                    cite_key = cite_keys[id(decision)]
                    lines.append(f"\\item \\fullcite{{{cite_key}}}")
                lines.append(r"\end{enumerate}")
                lines.append("")
        else:
            # No motivations, just list papers
            lines.append(r"\begin{enumerate}")
            for decision in session.discarded_papers:
                cite_key = cite_keys[id(decision)]
                lines.append(f"\\item \\fullcite{{{cite_key}}}")
            lines.append(r"\end{enumerate}")
            lines.append("")

    lines.extend(
        [
            r"\end{document}",
        ]
    )

    output_path.write_text("\n".join(lines))


def generate_csv_report(session: ReviewSession, output_path: Path) -> None:
    """
    Generate a CSV report of the review session.

    The CSV includes all papers (kept and discarded) with columns:
    - status: kept/discarded/pending
    - title, authors, year, venue, doi, url
    - tags: semicolon-separated list of themes/motivations
    - abstract: full abstract text
    - provider: source of the paper

    Args:
        session: The ReviewSession to report on.
        output_path: Path for the .csv file.
    """
    import csv

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Header row
        writer.writerow(
            [
                "status",
                "title",
                "authors",
                "year",
                "venue",
                "doi",
                "url",
                "tags",
                "abstract",
                "provider",
            ]
        )

        # Write all decisions
        for decision in session.decisions:
            paper = decision.paper
            writer.writerow(
                [
                    decision.status.value,
                    paper.title,
                    "; ".join(paper.authors) if paper.authors else "",
                    paper.year or "",
                    paper.venue or "",
                    paper.doi or "",
                    paper.url or "",
                    "; ".join(decision.tags) if decision.tags else "",
                    paper.abstract or "",
                    decision.provider,
                ]
            )
