"""Interactive TUI for reviewing academic papers."""

from datetime import datetime
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import Screen, ModalScreen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Markdown,
    OptionList,
    SelectionList,
    Static,
    TextArea,
)
from textual.widgets.selection_list import Selection
from textual.message import Message
from textual import work
from rich.text import Text
from rich.console import Console

from scholar.scholar import Paper, SearchResult, SearchFilters
from scholar.notes import (
    get_note,
    has_note,
    edit_note_in_editor,
)
from scholar.review import (
    DecisionStatus,
    ReviewDecision,
    ReviewSession,
    ReviewSource,
    create_review_session,
    save_search_decisions,
    save_session,
    escape_latex,
    filter_decisions,
    generate_csv_report,
    generate_latex_report,
)
from scholar.pdf import (
    get_pdf_cache_dir,
    get_cached_pdf_path,
    download_pdf,
    open_pdf,
    PDFDownloadError,
)
from scholar.enrich import enrich_paper, needs_enrichment


# Data structures imported from scholar.review:
# - DecisionStatus: Enum for pending/kept/discarded
# - ReviewDecision: Decision for a single paper with tags
# - ReviewSession: Complete review session with all decisions
#
# The review module's ReviewDecision uses tags: list[str] instead of motivation: str,
# with a backward-compatible motivation property that accesses the first tag.
# PDF caching functions imported from scholar.pdf:
# - get_pdf_cache_dir(): Get cache directory
# - get_cached_pdf_path(url): Get cache path for URL
# - download_pdf(url): Download PDF to cache
# - open_pdf(path): Open PDF with system viewer
# - PDFDownloadError: Exception for download failures
class PaperListItem(ListItem):
    """A list item displaying a paper with its review status."""

    def __init__(
        self, decision: ReviewDecision, index: int, review_mode: bool = True
    ) -> None:
        super().__init__()
        self.decision = decision
        self.index = index
        self.review_mode = review_mode

    def compose(self) -> ComposeResult:
        paper = self.decision.paper
        status = self.decision.status
        source = self.decision.source

        # Note indicator
        note_indicator = "[yellow]📝[/yellow] " if has_note(paper) else "   "

        # LLM source indicator
        if source == ReviewSource.LLM_UNREVIEWED:
            # Show confidence if available
            conf = self.decision.llm_confidence
            if conf is not None:
                conf_pct = int(conf * 100)
                llm_indicator = f"[magenta]🤖{conf_pct}%[/magenta] "
            else:
                llm_indicator = "[magenta]🤖[/magenta] "
        elif source == ReviewSource.LLM_REVIEWED:
            llm_indicator = "[cyan]🤖✓[/cyan] "
        else:
            llm_indicator = ""

        # Color code by status (only in review mode)
        if self.review_mode:
            if status == DecisionStatus.KEPT:
                status_indicator = "[green]✓[/green]"
            elif status == DecisionStatus.DISCARDED:
                status_indicator = "[red]✗[/red]"
            else:
                status_indicator = "[dim]○[/dim]"
        else:
            status_indicator = " "

        # Format authors (truncate if too many)
        authors = ", ".join(paper.authors[:3])
        if len(paper.authors) > 3:
            authors += " et al."

        year = paper.year or "n/a"
        provider = f"[dim]{self.decision.provider}[/dim]"

        # Truncate title accounting for LLM indicator width
        max_title = (
            55
            - len(
                llm_indicator.replace("[", "").replace("]", "").split("/")[0]
            )
            if llm_indicator
            else 55
        )
        title_display = paper.title[:max_title] + (
            "..." if len(paper.title) > max_title else ""
        )

        yield Static(
            f"{status_indicator} {note_indicator}{llm_indicator}{title_display}\n"
            f"   [dim]{authors} ({year})[/dim] {provider}"
        )


class AbstractScreen(Screen[None]):
    """Full-screen view of a paper's abstract and details."""

    BINDINGS = [
        Binding("escape", "dismiss_screen", "Back"),
        Binding("q", "dismiss_screen", "Back"),
        Binding("K", "keep", "Keep"),
        Binding("T", "keep_with_themes", "Themes"),
        Binding("d", "discard", "Discard"),
        Binding("p", "open_pdf", "Open PDF"),
        Binding("n", "edit_notes", "Notes"),
        Binding("e", "enrich", "Enrich"),
        Binding("C", "confirm_llm", "Confirm"),
        Binding("a", "add_references", "+Refs"),
        Binding("A", "add_citations", "+Cites"),
        Binding("j", "scroll_down", "Down", show=False),
        Binding("k", "scroll_up", "Up", show=False),
    ]

    def __init__(
        self,
        decision: ReviewDecision,
        session: ReviewSession,
        review_mode: bool = True,
    ) -> None:
        super().__init__()
        self.decision = decision
        self.session = session
        self.review_mode = review_mode
        self.pdf_status: str = ""

    def compose(self) -> ComposeResult:
        paper = self.decision.paper

        yield Header()
        with VerticalScroll():
            yield Static(f"[bold]{paper.title}[/bold]", classes="title")
            yield Static(f"[dim]Provider: {self.decision.provider}[/dim]")
            yield Static("")

            authors = ", ".join(paper.authors) if paper.authors else "Unknown"
            yield Static(f"[bold]Authors:[/bold] {authors}")
            yield Static(f"[bold]Year:[/bold] {paper.year or 'Unknown'}")
            yield Static(f"[bold]Venue:[/bold] {paper.venue or 'Unknown'}")

            if paper.doi:
                yield Static(f"[bold]DOI:[/bold] {paper.doi}")
            if paper.url:
                yield Static(f"[bold]URL:[/bold] {paper.url}")
            if paper.pdf_url:
                yield Static(f"[bold]PDF:[/bold] {paper.pdf_url}")

            yield Static("")
            yield Static("[bold]Abstract:[/bold]")
            if paper.abstract:
                yield Static(paper.abstract)
            else:
                if paper.pdf_url:
                    yield Static(
                        "[dim]No abstract available. Press [bold yellow]p[/bold yellow] to open PDF.[/dim]"
                    )
                else:
                    yield Static(
                        "[dim]No abstract available and no PDF link found.[/dim]"
                    )

            # Show notes section if paper has notes
            note = get_note(paper)
            if note:
                yield Static("")
                yield Static("[bold cyan]─── Notes ───[/bold cyan]")
                yield Markdown(note.note, id="notes-content")
            else:
                yield Static("")
                yield Static(
                    "[dim]No notes. Press [bold yellow]n[/bold yellow] to add notes.[/dim]"
                )

            # Show tags (themes for kept, motivations for discarded)
            if self.decision.tags:
                yield Static("")
                if self.decision.status == DecisionStatus.KEPT:
                    yield Static("[bold green]─── Themes ───[/bold green]")
                elif self.decision.status == DecisionStatus.DISCARDED:
                    yield Static("[bold red]─── Motivations ───[/bold red]")
                else:
                    yield Static("[bold yellow]─── Tags ───[/bold yellow]")
                tags_text = ", ".join(self.decision.tags)
                yield Static(tags_text)

            # Show references if paper has them
            if paper.references:
                yield Static("")
                yield Static(
                    f"[bold blue]─── References ({len(paper.references)}) ───[/bold blue] [dim]Press [bold yellow]a[/bold yellow] to add to session.[/dim]"
                )
                for ref_paper in paper.references:
                    yield self._render_paper_entry(ref_paper)

            # Show citations if paper has them
            if paper.citations:
                yield Static("")
                yield Static(
                    f"[bold magenta]─── Citing Papers ({len(paper.citations)}) ───[/bold magenta] [dim]Press [bold yellow]A[/bold yellow] to add to session.[/dim]"
                )
                for cite_paper in paper.citations:
                    yield self._render_paper_entry(cite_paper)

            yield Static("", id="pdf-status")
        yield Footer()

    def action_edit_notes(self) -> None:
        """Open editor to edit notes for this paper."""
        paper = self.decision.paper
        with self.app.suspend():
            edit_note_in_editor(paper)
        # Refresh the screen to show updated notes
        self.refresh(recompose=True)

    def action_enrich(self) -> None:
        """Fetch missing metadata, references, and citations."""
        paper = self.decision.paper

        if not paper.doi:
            self.notify("No DOI available for enrichment", severity="warning")
            return

        # Brief title preview for notifications
        title_preview = (paper.title or "")[:30]
        if len(paper.title or "") > 30:
            title_preview += "..."

        self.notify(f"Enriching '{title_preview}'", severity="information")
        self._do_enrich()

    def _do_enrich(self) -> None:
        """Start enrichment in a background thread.

        Uses a plain thread instead of @work so the enrichment continues
        even if the screen is dismissed before it completes.
        """
        import threading

        decision = self.decision  # Capture reference
        app = self.app  # Capture app reference
        screen = self  # Capture screen reference for refresh
        paper = decision.paper

        # Brief title preview for notifications
        title_preview = (paper.title or "")[:30]
        if len(paper.title or "") > 30:
            title_preview += "..."

        def enrich_thread():
            from scholar.enrich import enrich_paper

            enriched = enrich_paper(paper, fetch_refs_cites=True)

            # Check what was enriched
            enriched_fields = []
            if enriched.abstract and enriched.abstract != paper.abstract:
                enriched_fields.append("abstract")
            if enriched.pdf_url and enriched.pdf_url != paper.pdf_url:
                enriched_fields.append("PDF URL")
            if enriched.references is not None and paper.references is None:
                enriched_fields.append(f"{len(enriched.references)} refs")
            if enriched.citations is not None and paper.citations is None:
                enriched_fields.append(f"{len(enriched.citations)} cites")

            # Update decision and notify from main thread
            def finish():
                if enriched_fields:
                    decision.paper = enriched
                    app.notify(
                        f"'{title_preview}': {', '.join(enriched_fields)}",
                        severity="information",
                    )
                    # Refresh screen if still mounted
                    if screen.is_mounted:
                        screen.refresh(recompose=True)
                else:
                    app.notify(
                        f"'{title_preview}' already enriched",
                        severity="information",
                    )

            app.call_from_thread(finish)

        thread = threading.Thread(target=enrich_thread, daemon=True)
        thread.start()

    def action_open_pdf(self) -> None:
        """Download and open the PDF."""
        paper = self.decision.paper

        if not paper.pdf_url:
            self.notify("No PDF URL available", severity="error")
            return

        cache_path = get_cached_pdf_path(paper.pdf_url)

        if cache_path.exists():
            self.notify(f"Using cached PDF", severity="information")
        else:
            self.notify(f"Downloading PDF...", severity="information")
            try:
                download_pdf(paper.pdf_url)
                self.notify("Download complete", severity="information")
            except PDFDownloadError as e:
                self.notify(f"Download failed: {e}", severity="error")
                return

        if open_pdf(cache_path):
            self.notify("PDF opened", severity="information")
        else:
            self.notify("Failed to open PDF viewer", severity="error")

    async def action_dismiss_screen(self) -> None:
        """Return to the paper list."""
        self.dismiss(None)

    def _render_paper_entry(self, paper: Paper) -> Static:
        """Render a single paper in the citation/reference list."""
        from rich.markup import escape

        title = escape(paper.title) if paper.title else "Unknown title"
        year = f"({paper.year})" if paper.year else ""
        citations = (
            f"- {paper.citation_count} citations"
            if paper.citation_count
            else ""
        )
        authors = ", ".join(paper.authors[:3]) if paper.authors else ""
        if paper.authors and len(paper.authors) > 3:
            authors += " et al."
        authors = escape(authors)

        return Static(
            f"  [bold]{title}[/bold] {year}\n"
            f"    [dim]{authors}[/dim] {citations}"
        )

    def action_add_references(self) -> None:
        """Add references of this paper to the session for review."""
        paper = self.decision.paper

        # Ensure we have references on the paper
        if paper.references is None:
            if not paper.doi:
                self.notify("No DOI available", severity="warning")
                return

            self.notify("Fetching references...", severity="information")
            from scholar.providers import fetch_references
            from scholar.enrich import enrich_papers

            try:
                refs = fetch_references(paper.doi)
                refs = enrich_papers(refs)
                # Store on the paper object
                self.decision.paper = Paper(
                    title=paper.title,
                    authors=paper.authors,
                    year=paper.year,
                    doi=paper.doi,
                    abstract=paper.abstract,
                    venue=paper.venue,
                    url=paper.url,
                    pdf_url=paper.pdf_url,
                    citation_count=paper.citation_count,
                    sources=paper.sources,
                    references=refs,
                    citations=paper.citations,
                )
                paper = self.decision.paper
            except Exception as e:
                self.notify(f"Error: {e}", severity="error")
                return

        if not paper.references:
            self.notify("No references found", severity="warning")
            return

        # Add references to session
        from scholar.review import get_paper_id

        source_id = get_paper_id(paper)
        added = self.session.add_papers_from_snowball(
            papers=paper.references,
            source_paper_ids=[source_id],
            direction="references",
        )
        self.notify(
            f"Added {added} new papers from references",
            severity="information",
        )

    def action_add_citations(self) -> None:
        """Add citing papers of this paper to the session for review."""
        paper = self.decision.paper

        # Ensure we have citations on the paper
        if paper.citations is None:
            if not paper.doi:
                self.notify("No DOI available", severity="warning")
                return

            self.notify("Fetching citing papers...", severity="information")
            from scholar.providers import fetch_citations
            from scholar.enrich import enrich_papers

            try:
                cites = fetch_citations(paper.doi)
                cites = enrich_papers(cites)
                # Store on the paper object
                self.decision.paper = Paper(
                    title=paper.title,
                    authors=paper.authors,
                    year=paper.year,
                    doi=paper.doi,
                    abstract=paper.abstract,
                    venue=paper.venue,
                    url=paper.url,
                    pdf_url=paper.pdf_url,
                    citation_count=paper.citation_count,
                    sources=paper.sources,
                    references=paper.references,
                    citations=cites,
                )
                paper = self.decision.paper
            except Exception as e:
                self.notify(f"Error: {e}", severity="error")
                return

        if not paper.citations:
            self.notify("No citing papers found", severity="warning")
            return

        # Add citations to session
        from scholar.review import get_paper_id

        source_id = get_paper_id(paper)
        added = self.session.add_papers_from_snowball(
            papers=paper.citations,
            source_paper_ids=[source_id],
            direction="citations",
        )
        self.notify(
            f"Added {added} new papers from citations", severity="information"
        )

    def action_keep(self) -> None:
        """Quick keep---mark paper as kept without themes."""
        if not self.review_mode:
            self.notify(
                "Keep/discard disabled in notes mode", severity="warning"
            )
            return

        # Check if changing an LLM decision
        was_llm = self.decision.source == ReviewSource.LLM_UNREVIEWED
        was_discarded = self.decision.status == DecisionStatus.DISCARDED

        self.decision.status = DecisionStatus.KEPT
        self.decision.clear_tags()

        # Mark as reviewed if it was an LLM decision
        if was_llm:
            from scholar.llm_review import mark_as_reviewed

            mark_as_reviewed(
                self.decision,
                user_agrees=not was_discarded,
                new_status=DecisionStatus.KEPT,
                new_tags=[],
            )

        self.dismiss(None)

    def action_keep_with_themes(self) -> None:
        """Keep with themes---open theme selection modal."""
        if not self.review_mode:
            self.notify(
                "Keep/discard disabled in notes mode", severity="warning"
            )
            return

        # Capture LLM state before modal opens
        was_llm = self.decision.source == ReviewSource.LLM_UNREVIEWED
        was_discarded = self.decision.status == DecisionStatus.DISCARDED

        def handle_themes(result: list[str] | None) -> None:
            if result is not None:  # None means cancelled
                self.decision.status = DecisionStatus.KEPT
                self.decision.tags = result

                # Mark as reviewed if it was an LLM decision
                if was_llm:
                    from scholar.llm_review import mark_as_reviewed

                    mark_as_reviewed(
                        self.decision,
                        user_agrees=not was_discarded,
                        new_status=DecisionStatus.KEPT,
                        new_tags=result,
                    )

                self.dismiss(None)

        self.app.push_screen(
            TagSelectionModal(
                title=f"Themes: {self.decision.paper.title[:50]}...",
                available_tags=list(self.session.all_themes()),
                tag_counts=self.session.theme_counts(),
                selected_tags=self.decision.tags,
                require_at_least_one=False,
            ),
            handle_themes,
        )

    def action_discard(self) -> None:
        """Open motivation selection modal."""
        if not self.review_mode:
            self.notify(
                "Keep/discard disabled in notes mode", severity="warning"
            )
            return

        # Capture LLM state before modal opens
        was_llm = self.decision.source == ReviewSource.LLM_UNREVIEWED
        was_kept = self.decision.status == DecisionStatus.KEPT

        def handle_discard(result: list[str] | None) -> None:
            if result is not None:  # None means cancelled
                self.decision.status = DecisionStatus.DISCARDED
                self.decision.tags = result

                # Mark as reviewed if it was an LLM decision
                if was_llm:
                    from scholar.llm_review import mark_as_reviewed

                    mark_as_reviewed(
                        self.decision,
                        user_agrees=not was_kept,
                        new_status=DecisionStatus.DISCARDED,
                        new_tags=result,
                    )

                self.dismiss(None)

        self.app.push_screen(
            TagSelectionModal(
                title=f"Motivations: {self.decision.paper.title[:50]}...",
                available_tags=list(self.session.all_motivations()),
                tag_counts=self.session.motivation_counts(),
                selected_tags=self.decision.tags,
                require_at_least_one=True,
            ),
            handle_discard,
        )

    def action_confirm_llm(self) -> None:
        """Confirm current LLM decision as correct (mark as reviewed)."""
        if not self.review_mode:
            self.notify(
                "Keep/discard disabled in notes mode", severity="warning"
            )
            return
        if self.decision.source != ReviewSource.LLM_UNREVIEWED:
            self.notify("Not an unreviewed LLM decision", severity="warning")
            return

        # Mark as reviewed without changing the decision
        from scholar.llm_review import mark_as_reviewed

        mark_as_reviewed(self.decision, user_agrees=True)
        self.notify(f"Confirmed LLM decision: {self.decision.status.value}")
        self.dismiss(None)

    def action_scroll_down(self) -> None:
        """Scroll the abstract view down."""
        scroll = self.query_one(VerticalScroll)
        scroll.scroll_down()

    def action_scroll_up(self) -> None:
        """Scroll the abstract view up."""
        scroll = self.query_one(VerticalScroll)
        scroll.scroll_up()


class TagSelectionModal(ModalScreen[list[str] | None]):
    """Modal for selecting multiple tags from a checklist.

    Used for both motivations (discarding) and themes (keeping).
    Shows a SelectionList of existing tags with checkboxes,
    plus an Input to add new tags.

    Args:
        title: Modal title displayed at the top.
        available_tags: List of existing tags to show.
        tag_counts: Optional dict mapping tags to usage counts.
        selected_tags: Tags that should be pre-selected.
        require_at_least_one: If True, dismissal requires selection.

    Returns:
        List of selected tag strings, or None if cancelled.
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "confirm", "Confirm", priority=True),
    ]

    DEFAULT_CSS = """
    TagSelectionModal {
        align: center middle;
    }
    #tag-dialog {
        width: 70;
        height: auto;
        max-height: 80%;
        padding: 1 2;
        border: thick $primary;
        background: $surface;
    }
    #tag-title {
        margin-bottom: 1;
    }
    #tag-list {
        height: auto;
        max-height: 15;
        margin-bottom: 1;
        border: solid $primary-darken-2;
    }
    #tag-input {
        margin-top: 1;
    }
    #tag-help {
        margin-top: 1;
        color: $text-muted;
    }
    """

    def __init__(
        self,
        title: str,
        available_tags: list[str],
        tag_counts: dict[str, int] | None = None,
        selected_tags: list[str] | None = None,
        require_at_least_one: bool = False,
    ) -> None:
        super().__init__()
        self.title_text = title
        # Deduplicate while preserving order
        self.available_tags = list(dict.fromkeys(available_tags))
        self.tag_counts = tag_counts or {}
        self.selected_tags = set(selected_tags or [])
        self.require_at_least_one = require_at_least_one

    def compose(self) -> ComposeResult:
        with Container(id="tag-dialog"):
            yield Static(f"[bold]{self.title_text}[/bold]", id="tag-title")

            # Build selection list with counts
            selections = []
            for tag in self.available_tags:
                count = self.tag_counts.get(tag, 0)
                label = f"{tag} ({count})" if count > 0 else tag
                is_selected = tag in self.selected_tags
                selections.append(
                    Selection(label, tag, initial_state=is_selected)
                )

            yield SelectionList[str](*selections, id="tag-list")
            yield Input(
                placeholder="Type new tag and press Enter (empty to confirm)",
                id="tag-input",
            )

            # Show contextual help, noting if selection is required
            help_text = "[dim]Space: toggle, Enter: confirm, Tab: add new, Escape: cancel[/dim]"
            if self.require_at_least_one:
                help_text = "[dim]At least one required. " + help_text[5:]
            yield Static(help_text, id="tag-help")

    def on_mount(self) -> None:
        """Focus appropriate widget based on available tags."""
        if self.available_tags:
            self.query_one("#tag-list", SelectionList).focus()
        else:
            self.query_one("#tag-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter in input field."""
        tag = event.value.strip()
        if tag:
            # Add new tag to list and auto-select it
            self._add_and_select_tag(tag)
            event.input.value = ""  # Clear for more input
        else:
            # Empty input = confirm selection
            self._confirm_selection()

    def _add_and_select_tag(self, tag: str) -> None:
        """Add a new tag to the list and select it."""
        selection_list = self.query_one("#tag-list", SelectionList)

        # Check if tag already exists (user might not have noticed it)
        # Use public API: iterate with get_option_at_index
        for i in range(selection_list.option_count):
            option = selection_list.get_option_at_index(i)
            if option.value == tag:
                # Tag exists - just select it if not already selected
                if tag not in selection_list.selected:
                    selection_list.select(tag)
                return

        # Add new tag (no count since it's new to this session)
        selection_list.add_option(Selection(tag, tag, initial_state=True))

    def _confirm_selection(self) -> None:
        """Confirm the current selection and dismiss."""
        selection_list = self.query_one("#tag-list", SelectionList)
        selected = list(selection_list.selected)

        if self.require_at_least_one and not selected:
            self.notify("At least one selection required", severity="warning")
            return

        self.dismiss(selected)

    def action_cancel(self) -> None:
        """Cancel without making changes."""
        self.dismiss(None)

    def action_confirm(self) -> None:
        """Confirm selection when Enter pressed."""
        input_widget = self.query_one("#tag-input", Input)
        if input_widget.has_focus:
            # Input has focus - if there's text, add it; otherwise confirm
            tag = input_widget.value.strip()
            if tag:
                self._add_and_select_tag(tag)
                input_widget.value = ""
            else:
                self._confirm_selection()
        else:
            # SelectionList has focus - just confirm
            self._confirm_selection()


class SortModal(ModalScreen[tuple[str, bool] | None]):
    """Modal dialog to select sort criteria."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("t", "sort_title", "Title A-Z", priority=True),
        Binding("T", "sort_title_rev", "Title Z-A", priority=True),
        Binding("y", "sort_year", "Year ↑", priority=True),
        Binding("Y", "sort_year_rev", "Year ↓", priority=True),
        Binding("a", "sort_author", "Author A-Z", priority=True),
        Binding("A", "sort_author_rev", "Author Z-A", priority=True),
        Binding("p", "sort_provider", "Provider", priority=True),
    ]

    DEFAULT_CSS = """
    SortModal {
        align: center middle;
    }
    #sort-dialog {
        width: 50;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    #sort-title {
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }
    .sort-option {
        margin: 0 1;
    }
    .key {
        color: $warning;
        text-style: bold;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="sort-dialog"):
            yield Static("[bold]Sort Papers[/bold]", id="sort-title")
            yield Static("")
            yield Static(
                "[bold yellow]t[/] Title (A→Z)    [bold yellow]T[/] Title (Z→A)"
            )
            yield Static(
                "[bold yellow]y[/] Year (oldest)  [bold yellow]Y[/] Year (newest)"
            )
            yield Static(
                "[bold yellow]a[/] Author (A→Z)   [bold yellow]A[/] Author (Z→A)"
            )
            yield Static("[bold yellow]p[/] Provider")
            yield Static("")
            yield Static("[dim]Press [bold]Escape[/bold] to cancel[/dim]")

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_sort_title(self) -> None:
        self.dismiss(("title", False))

    def action_sort_title_rev(self) -> None:
        self.dismiss(("title", True))

    def action_sort_year(self) -> None:
        self.dismiss(("year", False))

    def action_sort_year_rev(self) -> None:
        self.dismiss(("year", True))

    def action_sort_author(self) -> None:
        self.dismiss(("author", False))

    def action_sort_author_rev(self) -> None:
        self.dismiss(("author", True))

    def action_sort_provider(self) -> None:
        self.dismiss(("provider", False))


class FilterModal(ModalScreen[str | None]):
    """Modal dialog to select paper filter by decision status."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("a", "filter_all", "All", priority=True),
        Binding("K", "filter_kept", "Kept", priority=True),
        Binding("d", "filter_discarded", "Discarded", priority=True),
        Binding("p", "filter_pending", "Pending", priority=True),
        Binding(
            "l", "filter_llm_unreviewed", "LLM Unreviewed", priority=True
        ),
        Binding("L", "filter_llm_reviewed", "LLM Reviewed", priority=True),
        Binding("e", "filter_examples", "Examples", priority=True),
    ]

    DEFAULT_CSS = """
    FilterModal {
        align: center middle;
    }
    #filter-dialog {
        width: 45;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    #filter-title {
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="filter-dialog"):
            yield Static("[bold]Filter Papers[/bold]", id="filter-title")
            yield Static("")
            yield Static("[bold yellow]a[/] All papers")
            yield Static("[bold yellow]K[/] Kept only")
            yield Static("[bold yellow]d[/] Discarded only")
            yield Static("[bold yellow]p[/] Pending only")
            yield Static("")
            yield Static("[dim]LLM Filters:[/dim]")
            yield Static("[bold yellow]l[/] LLM unreviewed (need review)")
            yield Static("[bold yellow]L[/] LLM reviewed")
            yield Static("[bold yellow]e[/] Training examples")
            yield Static("")
            yield Static("[dim]Press [bold]Escape[/bold] to cancel[/dim]")

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_filter_all(self) -> None:
        self.dismiss("all")

    def action_filter_kept(self) -> None:
        self.dismiss("kept")

    def action_filter_discarded(self) -> None:
        self.dismiss("discarded")

    def action_filter_pending(self) -> None:
        self.dismiss("pending")

    def action_filter_llm_unreviewed(self) -> None:
        self.dismiss("llm_unreviewed")

    def action_filter_llm_reviewed(self) -> None:
        self.dismiss("llm_reviewed")

    def action_filter_examples(self) -> None:
        self.dismiss("examples")


class SearchFiltersModal(ModalScreen[SearchFilters | None]):
    """Modal dialog to configure search filters."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+s", "apply", "Apply", priority=True),
    ]
    DEFAULT_CSS = """
    SearchFiltersModal {
        align: center middle;
    }
    #search-filters-dialog {
        width: 60;
        height: auto;
        max-height: 80%;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    #search-filters-title {
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }
    .filter-row {
        height: auto;
        margin-bottom: 1;
    }
    .filter-label {
        width: 20;
    }
    .filter-input {
        width: 1fr;
    }
    #pub-types-list {
        height: 8;
        border: solid $primary-darken-2;
    }
    .help-text {
        color: $text-muted;
        text-style: italic;
    }
    """

    def __init__(self, current_filters: SearchFilters | None = None) -> None:
        super().__init__()
        self.current_filters = current_filters or SearchFilters()

    def compose(self) -> ComposeResult:
        with Container(id="search-filters-dialog"):
            yield Static(
                "[bold]Search Filters[/bold]", id="search-filters-title"
            )
            yield Static(
                "[dim]Modify filters and press Ctrl+S to apply[/dim]",
                classes="help-text",
            )
            yield Static("")

            with Horizontal(classes="filter-row"):
                yield Static("Year:", classes="filter-label")
                yield Input(
                    value=self.current_filters.year or "",
                    placeholder="e.g., 2020, 2020-2024, 2020-, -2024",
                    id="year-input",
                    classes="filter-input",
                )
            with Horizontal(classes="filter-row"):
                yield Static("Venue:", classes="filter-label")
                yield Input(
                    value=self.current_filters.venue or "",
                    placeholder="Journal or conference name",
                    id="venue-input",
                    classes="filter-input",
                )
            with Horizontal(classes="filter-row"):
                yield Static("Min Citations:", classes="filter-label")
                yield Input(
                    value=(
                        str(self.current_filters.min_citations)
                        if self.current_filters.min_citations
                        else ""
                    ),
                    placeholder="e.g., 10",
                    id="citations-input",
                    classes="filter-input",
                )
            with Horizontal(classes="filter-row"):
                yield Static("Open Access:", classes="filter-label")
                yield SelectionList[str](
                    Selection(
                        "Only open access papers",
                        "open_access",
                        self.current_filters.open_access,
                    ),
                    id="open-access-list",
                )
            yield Static("Publication Types:", classes="filter-label")
            pub_types = self.current_filters.pub_types or []
            yield SelectionList[str](
                Selection("Article", "article", "article" in pub_types),
                Selection(
                    "Conference", "conference", "conference" in pub_types
                ),
                Selection("Review", "review", "review" in pub_types),
                Selection("Book", "book", "book" in pub_types),
                Selection("Preprint", "preprint", "preprint" in pub_types),
                Selection("Dataset", "dataset", "dataset" in pub_types),
                id="pub-types-list",
            )

            yield Static("")
            with Horizontal(classes="filter-row"):
                yield Button(
                    "Apply (Ctrl+S)", id="apply-btn", variant="primary"
                )
                yield Button("Clear All", id="clear-btn", variant="warning")
                yield Button("Cancel", id="cancel-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "apply-btn":
            self.action_apply()
        elif event.button.id == "clear-btn":
            self._clear_all_filters()
        elif event.button.id == "cancel-btn":
            self.action_cancel()

    def _clear_all_filters(self) -> None:
        """Clear all filter inputs to their default (empty) state."""
        self.query_one("#year-input", Input).value = ""
        self.query_one("#venue-input", Input).value = ""
        self.query_one("#citations-input", Input).value = ""
        self.query_one("#open-access-list", SelectionList).deselect_all()
        self.query_one("#pub-types-list", SelectionList).deselect_all()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_apply(self) -> None:
        filters = self._build_filters()
        self.dismiss(filters)

    def _build_filters(self) -> SearchFilters | None:
        """Build SearchFilters from current input values.

        Returns None if all filters are empty (indicating no filtering),
        otherwise returns a SearchFilters with the specified values.
        """
        year = self.query_one("#year-input", Input).value.strip() or None
        venue = self.query_one("#venue-input", Input).value.strip() or None

        # Parse citations as integer, defaulting to None if invalid
        citations_str = self.query_one(
            "#citations-input", Input
        ).value.strip()
        min_citations = (
            int(citations_str) if citations_str.isdigit() else None
        )

        open_access_list = self.query_one("#open-access-list", SelectionList)
        open_access = "open_access" in open_access_list.selected

        pub_types_list = self.query_one("#pub-types-list", SelectionList)
        pub_types = (
            list(pub_types_list.selected) if pub_types_list.selected else None
        )

        # Return None if no filters are set (semantically: no filtering)
        if not any([year, venue, min_citations, open_access, pub_types]):
            return None

        return SearchFilters(
            year=year,
            open_access=open_access,
            venue=venue,
            min_citations=min_citations,
            pub_types=pub_types,
        )


class PaperReviewApp(App):
    """Interactive paper review application."""

    CSS = """
    #paper-list {
        height: 1fr;
    }
    
    #status-bar {
        dock: bottom;
        height: 1;
        background: $primary;
        color: $text;
        padding: 0 1;
    }
    
    #discard-dialog {
        width: 60;
        height: auto;
        padding: 1 2;
        background: $surface;
        border: solid $primary;
    }
    
    #discard-buttons {
        margin-top: 1;
        height: auto;
    }
    
    #discard-buttons Button {
        margin-right: 1;
    }
    
    #motivation-input {
        height: 5;
        margin: 1 0;
    }
    
    #sort-dialog {
        width: 40;
        height: auto;
        padding: 1 2;
        background: $surface;
        border: solid $primary;
    }
    
    .title {
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("down", "cursor_down", "Down", show=False),
        Binding("up", "cursor_up", "Up", show=False),
        Binding("K", "keep", "Keep"),
        Binding("T", "keep_with_themes", "Themes"),
        Binding("d", "discard", "Discard"),
        Binding("C", "confirm_llm", "Confirm"),
        Binding("s", "sort", "Sort"),
        Binding("f", "filter", "Filter"),
        Binding("F", "search_filters", "Search"),
        Binding("n", "edit_notes", "Notes"),
        Binding("a", "add_all_references", "+Refs"),
        Binding("A", "add_all_citations", "+Cites"),
    ]

    def __init__(
        self,
        session: ReviewSession,
        review_mode: bool = True,
        search_filters: SearchFilters | None = None,
    ) -> None:
        super().__init__()
        self.theme = "textual-light"
        self.session = session
        self.review_mode = review_mode
        self.current_index = 0
        self.current_filter = "all"
        self.search_filters = search_filters

    def compose(self) -> ComposeResult:
        yield Header()
        yield ListView(id="paper-list")
        yield Static(id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the paper list after mounting."""
        self._refresh_list()
        self._update_status()

    def get_filtered_decisions(self) -> list[ReviewDecision]:
        """Get decisions filtered by current status filter and search filters.

        This method applies both the status filter (all/kept/discarded/pending
        plus LLM-specific filters) and any paper-level filters (year, venue,
        etc.) to return the currently visible decisions.

        Returns:
            List of ReviewDecision objects matching current filters.
        """
        # First filter by decision status or source
        if self.current_filter == "all":
            decisions = self.session.decisions
        elif self.current_filter == "kept":
            decisions = self.session.kept_papers
        elif self.current_filter == "discarded":
            decisions = self.session.discarded_papers
        elif self.current_filter == "pending":
            decisions = self.session.pending_papers
        elif self.current_filter == "llm_unreviewed":
            # LLM decisions pending user review
            decisions = [
                d
                for d in self.session.decisions
                if d.source == ReviewSource.LLM_UNREVIEWED
            ]
        elif self.current_filter == "llm_reviewed":
            # LLM decisions that user has reviewed
            decisions = [
                d
                for d in self.session.decisions
                if d.source == ReviewSource.LLM_REVIEWED
            ]
        elif self.current_filter == "examples":
            # Training examples for LLM
            decisions = [d for d in self.session.decisions if d.is_example]
        else:
            decisions = self.session.decisions

        # Then apply paper-level filters (year, venue, etc.)
        if self.search_filters is None or self.search_filters.is_empty():
            return decisions

        return filter_decisions(decisions, self.search_filters)

    def _refresh_list(self) -> None:
        """Refresh the paper list display."""
        list_view = self.query_one("#paper-list", ListView)
        list_view.clear()

        filtered = self.get_filtered_decisions()
        for i, decision in enumerate(filtered):
            list_view.append(PaperListItem(decision, i, self.review_mode))

        # Restore selection and focus after UI updates complete.
        # We must defer the index setting to after the DOM is updated,
        # otherwise the highlight doesn't appear when returning from screens.
        def restore_selection():
            if filtered:
                target_index = min(self.current_index, len(filtered) - 1)
                # Reset to None first to ensure watcher fires even if same value
                list_view.index = None
                list_view.index = target_index
            list_view.focus()

        self.call_after_refresh(restore_selection)

    def _update_status(self) -> None:
        """Update the status bar with current counts."""
        kept = len(self.session.kept_papers)
        discarded = len(self.session.discarded_papers)
        pending = len(self.session.pending_papers)
        total = len(self.session.decisions)
        filtered_count = len(self.get_filtered_decisions())

        # Build filter indicator
        filter_text = ""
        if self.current_filter != "all":
            filter_text = f" | [yellow]Filter: {self.current_filter} ({filtered_count})[/yellow]"

        # Build session identifier for status bar
        if self.session.name:
            session_id = self.session.name
        elif len(self.session.query_provider_pairs) > 1:
            session_id = f"{len(self.session.query_provider_pairs)} queries"
        else:
            session_id = self.session.query

        status = self.query_one("#status-bar", Static)
        if self.review_mode:
            status.update(
                f"Session: {session_id} | "
                f"[green]Kept: {kept}[/green] | "
                f"[red]Discarded: {discarded}[/red] | "
                f"Pending: {pending} | "
                f"Total: {total}"
                f"{filter_text}"
            )
        else:
            # Notes mode - simpler status
            status.update(
                f"Papers with notes: {total} | "
                f"Press [bold yellow]n[/bold yellow] to edit notes, "
                f"[bold yellow]p[/bold yellow] to open PDF"
                f"{filter_text}"
            )

    def get_current_decision(self) -> ReviewDecision | None:
        """Get the currently selected decision from filtered list.

        Returns:
            The ReviewDecision for the currently highlighted paper,
            or None if no paper is selected.
        """
        list_view = self.query_one("#paper-list", ListView)
        filtered = self.get_filtered_decisions()
        if list_view.index is not None and list_view.index < len(filtered):
            self.current_index = list_view.index
            return filtered[list_view.index]
        return None

    def action_cursor_down(self) -> None:
        list_view = self.query_one("#paper-list", ListView)
        list_view.action_cursor_down()

    def action_cursor_up(self) -> None:
        list_view = self.query_one("#paper-list", ListView)
        list_view.action_cursor_up()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle Enter key on ListView - show abstract."""
        self.action_view_abstract()

    def action_view_abstract(self) -> None:
        """Show the abstract screen for current paper."""
        decision = self.get_current_decision()
        if decision:
            self.push_screen(
                AbstractScreen(decision, self.session, self.review_mode),
                self._on_abstract_closed,
            )

    def _on_abstract_closed(self, result: None) -> None:
        """Called when abstract screen is closed."""
        self._refresh_list()
        self._update_status()
        self.query_one("#paper-list", ListView).focus()

    def action_edit_notes(self) -> None:
        """Open editor to edit notes for current paper."""
        decision = self.get_current_decision()
        if decision:
            with self.suspend():
                edit_note_in_editor(decision.paper)
            self._refresh_list()

    def action_keep(self) -> None:
        """Quick keep---mark current paper as kept without themes."""
        if not self.review_mode:
            self.notify(
                "Keep/discard disabled in notes mode", severity="warning"
            )
            return
        decision = self.get_current_decision()
        if decision:
            # Check if changing an LLM decision
            was_llm = decision.source == ReviewSource.LLM_UNREVIEWED
            was_discarded = decision.status == DecisionStatus.DISCARDED

            decision.status = DecisionStatus.KEPT
            decision.clear_tags()

            # Mark as reviewed if it was an LLM decision
            if was_llm:
                from scholar.llm_review import mark_as_reviewed

                mark_as_reviewed(
                    decision,
                    user_agrees=not was_discarded,
                    new_status=DecisionStatus.KEPT,
                    new_tags=[],
                )

            self._refresh_list()
            self._update_status()

    def action_keep_with_themes(self) -> None:
        """Keep with themes---open theme selection modal."""
        if not self.review_mode:
            self.notify(
                "Keep/discard disabled in notes mode", severity="warning"
            )
            return
        decision = self.get_current_decision()
        if decision:
            self.push_screen(
                TagSelectionModal(
                    title=f"Themes: {decision.paper.title[:50]}...",
                    available_tags=list(self.session.all_themes()),
                    tag_counts=self.session.theme_counts(),
                    selected_tags=decision.tags,
                    require_at_least_one=False,
                ),
                self._on_themes_closed,
            )

    def _on_themes_closed(self, result: list[str] | None) -> None:
        """Called when theme selection modal is closed."""
        if result is not None:  # None means cancelled
            decision = self.get_current_decision()
            if decision:
                # Check if this is changing an LLM decision
                was_llm = decision.source == ReviewSource.LLM_UNREVIEWED
                was_discarded = decision.status == DecisionStatus.DISCARDED

                decision.status = DecisionStatus.KEPT
                decision.tags = result

                # Mark as reviewed if it was an LLM decision
                if was_llm:
                    from scholar.llm_review import mark_as_reviewed

                    # User changed it if it was discarded, or agrees if already kept
                    mark_as_reviewed(
                        decision,
                        user_agrees=not was_discarded,
                        new_status=DecisionStatus.KEPT,
                        new_tags=result,
                    )
        self._refresh_list()
        self._update_status()
        self.query_one("#paper-list", ListView).focus()

    def action_discard(self) -> None:
        """Open motivation selection modal for current paper."""
        if not self.review_mode:
            self.notify(
                "Keep/discard disabled in notes mode", severity="warning"
            )
            return
        decision = self.get_current_decision()
        if decision:
            self.push_screen(
                TagSelectionModal(
                    title=f"Motivations: {decision.paper.title[:50]}...",
                    available_tags=list(self.session.all_motivations()),
                    tag_counts=self.session.motivation_counts(),
                    selected_tags=decision.tags,
                    require_at_least_one=True,
                ),
                self._on_discard_closed,
            )

    def _on_discard_closed(self, result: list[str] | None) -> None:
        """Called when motivation selection modal is closed."""
        if result is not None:  # None means cancelled
            decision = self.get_current_decision()
            if decision:
                # Check if this is changing an LLM decision
                was_llm = decision.source == ReviewSource.LLM_UNREVIEWED
                was_kept = decision.status == DecisionStatus.KEPT

                decision.status = DecisionStatus.DISCARDED
                decision.tags = result

                # Mark as reviewed if it was an LLM decision
                if was_llm:
                    from scholar.llm_review import mark_as_reviewed

                    # User changed it if it was kept, or agrees if already discarded
                    mark_as_reviewed(
                        decision,
                        user_agrees=not was_kept,
                        new_status=DecisionStatus.DISCARDED,
                        new_tags=result,
                    )
        self._refresh_list()
        self._update_status()
        self.query_one("#paper-list", ListView).focus()

    def action_confirm_llm(self) -> None:
        """Confirm current LLM decision as correct (mark as reviewed)."""
        if not self.review_mode:
            self.notify(
                "Keep/discard disabled in notes mode", severity="warning"
            )
            return
        decision = self.get_current_decision()
        if not decision:
            return
        if decision.source != ReviewSource.LLM_UNREVIEWED:
            self.notify("Not an unreviewed LLM decision", severity="warning")
            return

        # Mark as reviewed without changing the decision
        from scholar.llm_review import mark_as_reviewed

        mark_as_reviewed(decision, user_agrees=True)
        self.notify(f"Confirmed LLM decision: {decision.status.value}")
        self._refresh_list()
        self._update_status()

    async def action_add_all_references(self) -> None:
        """Add references from all kept papers to session for review."""
        if not self.review_mode:
            self.notify(
                "Snowballing disabled in notes mode", severity="warning"
            )
            return

        kept_papers = self.session.kept_papers
        if not kept_papers:
            self.notify("No kept papers to snowball from", severity="warning")
            return

        # Only use papers with DOIs
        papers_with_doi = [d for d in kept_papers if d.paper.doi]
        if not papers_with_doi:
            self.notify("No kept papers have DOIs", severity="warning")
            return

        from scholar.providers import fetch_references
        from scholar.enrich import enrich_papers
        from scholar.review import get_paper_id

        self.notify(
            f"Fetching references from {len(papers_with_doi)} papers...",
            severity="information",
        )

        all_refs: list[Paper] = []
        source_ids: list[str] = []

        for decision in papers_with_doi:
            paper = decision.paper
            try:
                # Use cached references if available
                if decision.cached_references is not None:
                    refs = decision.cached_references
                else:
                    refs = fetch_references(paper.doi)
                    refs = enrich_papers(refs)
                    decision.cached_references = refs

                all_refs.extend(refs)
                source_ids.append(get_paper_id(paper))
                self.notify(
                    f"Found {len(refs)} refs for {paper.title_preview(30)}"
                )
            except Exception as e:
                self.notify(
                    f"Error for {paper.title_preview(30)}: {e}",
                    severity="warning",
                )

        if all_refs:
            added = self.session.add_papers_from_snowball(
                papers=all_refs,
                source_paper_ids=source_ids,
                direction="references",
            )
            self.notify(
                f"Added {added} new papers from {len(all_refs)} references",
                severity="information",
            )
            self._refresh_list()
            self._update_status()
        else:
            self.notify("No references found", severity="warning")

    async def action_add_all_citations(self) -> None:
        """Add citing papers from all kept papers to session for review."""
        if not self.review_mode:
            self.notify(
                "Snowballing disabled in notes mode", severity="warning"
            )
            return

        kept_papers = self.session.kept_papers
        if not kept_papers:
            self.notify("No kept papers to snowball from", severity="warning")
            return

        # Only use papers with DOIs
        papers_with_doi = [d for d in kept_papers if d.paper.doi]
        if not papers_with_doi:
            self.notify("No kept papers have DOIs", severity="warning")
            return

        from scholar.providers import fetch_citations
        from scholar.enrich import enrich_papers
        from scholar.review import get_paper_id

        self.notify(
            f"Fetching citations from {len(papers_with_doi)} papers...",
            severity="information",
        )

        all_cites: list[Paper] = []
        source_ids: list[str] = []

        for decision in papers_with_doi:
            paper = decision.paper
            try:
                # Use cached citations if available
                if decision.cached_citations is not None:
                    cites = decision.cached_citations
                else:
                    cites = fetch_citations(paper.doi)
                    cites = enrich_papers(cites)
                    decision.cached_citations = cites

                all_cites.extend(cites)
                source_ids.append(get_paper_id(paper))
                self.notify(
                    f"Found {len(cites)} cites for {paper.title_preview(30)}"
                )
            except Exception as e:
                self.notify(
                    f"Error for {paper.title_preview(30)}: {e}",
                    severity="warning",
                )

        if all_cites:
            added = self.session.add_papers_from_snowball(
                papers=all_cites,
                source_paper_ids=source_ids,
                direction="citations",
            )
            self.notify(
                f"Added {added} new papers from {len(all_cites)} citations",
                severity="information",
            )
            self._refresh_list()
            self._update_status()
        else:
            self.notify("No citing papers found", severity="warning")

    def action_sort(self) -> None:
        """Open sort modal."""
        self.push_screen(SortModal(), self._on_sort_closed)

    def _on_sort_closed(self, result: tuple[str, bool] | None) -> None:
        """Called when sort modal is closed."""
        if result:
            key, reverse = result
            self.session.sort_by(key, reverse)
            self._refresh_list()
        self.query_one("#paper-list", ListView).focus()

    def action_filter(self) -> None:
        """Open filter modal to select which papers to display.

        Filtering helps manage large result sets by focusing on papers with
        a specific status. This is particularly useful when:
        - Resuming a partially completed review (filter to pending)
        - Double-checking kept papers before report generation
        - Reviewing discard motivations for consistency
        """
        self.push_screen(FilterModal(), self._on_filter_closed)

    def _on_filter_closed(self, result: str | None) -> None:
        """Apply the selected filter and refresh the display.

        When changing filters, we reset to the first item in the filtered list
        to avoid index-out-of-bounds issues and give users a clear starting point.
        """
        if result:
            self.current_filter = result
            self.current_index = 0
            self._refresh_list()
            self._update_status()
        self.query_one("#paper-list", ListView).focus()

    def action_search_filters(self) -> None:
        """Open search filters modal to modify bibliographic filters."""
        if not self.review_mode:
            self.notify(
                "Search filters only available in review mode",
                severity="warning",
            )
            return
        self.push_screen(
            SearchFiltersModal(self.search_filters),
            self._on_search_filters_closed,
        )

    def _on_search_filters_closed(self, result: SearchFilters | None) -> None:
        """Handle search filters modal result and apply local filtering."""
        # result is None if user cancelled
        if result is None:
            self.query_one("#paper-list", ListView).focus()
            return

        # Update filters and refresh display
        self.search_filters = result
        self.current_index = 0
        self._refresh_list()
        self._update_status()

        # Notify user about filter status
        if result.is_empty():
            self.notify("Filters cleared", severity="information")
        else:
            filtered = self.get_filtered_decisions()
            self.notify(
                f"Showing {len(filtered)} of {len(self.session.decisions)} papers",
                severity="information",
            )
        self.query_one("#paper-list", ListView).focus()

    # Local filtering is now handled by filter_decisions() from scholar.review
    # which uses SearchFilters.matches() to check each paper.
    # See get_filtered_decisions() for the implementation.


def prompt_for_report(session: ReviewSession) -> None:
    """
    Prompt the user to save reports after the review session.

    Generates three files with the same base name:
    - .tex: LaTeX report with citations
    - .bib: BibTeX bibliography
    - .csv: Spreadsheet-friendly export

    Called after the TUI exits if any decisions were made.
    """
    from rich.prompt import Prompt, Confirm
    from rich.console import Console

    console = Console()

    kept = len(session.kept_papers)
    discarded = len(session.discarded_papers)

    if kept == 0 and discarded == 0:
        return

    console.print(f"\n[bold]Review session complete![/bold]")
    console.print(f"  [green]Kept:[/green] {kept}")
    console.print(f"  [red]Discarded:[/red] {discarded}")
    console.print(f"  Pending: {len(session.pending_papers)}")

    if Confirm.ask("\nWould you like to save reports?", default=True):
        default_name = f"review_{session.timestamp.strftime('%Y%m%d_%H%M%S')}"
        basename = Prompt.ask(
            "Base filename (without extension)", default=default_name
        )

        # Generate all three report files
        tex_path = Path(f"{basename}.tex")
        csv_path = Path(f"{basename}.csv")

        generate_latex_report(session, tex_path)
        generate_csv_report(session, csv_path)

        console.print(f"[green]Reports saved:[/green]")
        console.print(f"  - {tex_path}")
        console.print(f"  - {tex_path.with_suffix('.bib')}")
        console.print(f"  - {csv_path}")


def run_review(
    results: list[SearchResult],
    query: str,
    session_name: str | None = None,
    prompt_report: bool = False,
    search_filters: SearchFilters | None = None,
) -> ReviewSession:
    """
    Run the interactive review TUI for search results.

    Converts SearchResult objects into a ReviewSession, launches the TUI,
    and returns the session with all decisions after the user exits.

    Args:
        results: Search results to review
        query: The search query (for display)
        session_name: Name for decision persistence. If provided, decisions are
                      stored under this name instead of the query. This allows
                      the same query with different names (different purposes)
                      or multiple queries with the same name (appending results).
        prompt_report: If True, prompt the user to save reports after the review
                       session. If False (the default), no prompt is shown.
        search_filters: Initial search filters for local filtering within TUI
    """
    # Use session_name for persistence, fall back to query
    persistence_key = session_name if session_name else query

    # Create review session using the review module
    session = create_review_session(results, query, session_name)

    # Run the TUI in review mode
    app = PaperReviewApp(
        session,
        review_mode=True,
        search_filters=search_filters,
    )
    app.run()

    # Save decisions for this session (legacy per-query storage)
    save_search_decisions(persistence_key, session.decisions)

    # Save the complete session for `scholar sessions` commands
    save_session(session)

    # Prompt for report only if requested
    if prompt_report:
        prompt_for_report(session)

    return session


def run_notes_browser() -> None:
    """
    Run the notes browser TUI for viewing and editing paper notes.

    This launches the TUI in notes-only mode (no keep/discard functionality),
    showing all papers that have notes attached.
    """
    from scholar.review import create_notes_session

    session = create_notes_session()

    if not session.decisions:
        console = Console()
        console.print("[yellow]No papers with notes found.[/yellow]")
        console.print(
            "Use 'scholar search --review' to review papers and add notes."
        )
        return

    # Run the TUI in notes-only mode (no keep/discard)
    app = PaperReviewApp(session, review_mode=False)
    app.run()
