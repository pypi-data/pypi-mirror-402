"""
Scholar command-line interface.

Provides commands for structured literature searches
across bibliographic databases.
"""

from typing import Optional
from typing_extensions import Annotated
from pathlib import Path
import json
import logging

import typer
from rich import box
from rich.console import Console
from rich.table import Table

logger = logging.getLogger(__name__)

UNLIMITED_PROVIDER_LIMIT = 10**9


class TableFormatter:
    """Display results as Rich tables."""

    def __init__(self) -> None:
        self.console = Console()

    def format(self, results: list) -> None:
        """Display results in formatted tables."""
        for result in results:
            table = Table(
                title=f"Results for: {result.query}",
                caption=f"Provider: {result.provider} | {result.timestamp}",
                box=box.HORIZONTALS,
            )

            table.add_column("Title", style="cyan", no_wrap=False)
            table.add_column("Authors", style="green")
            table.add_column("Year", justify="right")
            table.add_column("DOI", style="dim")

            for paper in result.papers:
                authors = ", ".join(paper.authors[:3])
                if len(paper.authors) > 3:
                    authors += "..."
                table.add_row(
                    paper.title,
                    authors,
                    str(paper.year) if paper.year else "",
                    paper.doi or "",
                    end_section=True,
                )

            self.console.print(table)

            if not result.papers:
                self.console.print("[dim]No results found.[/dim]")


class CSVFormatter:
    """Output results as tab-separated values for scripting."""

    def format(self, results: list) -> None:
        """Output results as CSV with metadata header."""
        for result in results:
            # Metadata header as comments
            print(f"# Query: {result.query}")
            print(f"# Provider: {result.provider}")
            print(f"# Timestamp: {result.timestamp}")
            print(f"# Results: {len(result.papers)}")
            print()

            # Header row
            print("title\tauthors\tyear\tdoi\tvenue\turl")

            # Data rows
            for paper in result.papers:
                authors = "; ".join(paper.authors)
                year = str(paper.year) if paper.year else ""
                print(
                    f"{paper.title}\t{authors}\t{year}\t"
                    f"{paper.doi or ''}\t{paper.venue or ''}\t"
                    f"{paper.url or ''}"
                )
            print()


class JSONFormatter:
    """Output results as JSON for scripting."""

    def format(self, results: list) -> None:
        """Output results as JSON."""
        output = []
        for result in results:
            output.append(
                {
                    "query": result.query,
                    "provider": result.provider,
                    "timestamp": result.timestamp,
                    "papers": [
                        {
                            "title": p.title,
                            "authors": p.authors,
                            "year": p.year,
                            "doi": p.doi,
                            "abstract": p.abstract,
                            "venue": p.venue,
                            "url": p.url,
                        }
                        for p in result.papers
                    ],
                }
            )
        print(json.dumps(output, indent=2))


class BibTeXFormatter:
    """Output results as BibTeX entries."""

    def format(self, results: list) -> None:
        """Output results as BibTeX."""
        for result in results:
            for paper in result.papers:
                self._format_paper(paper)

    def _format_paper(self, paper) -> None:
        """Format a single paper as BibTeX."""
        first_author = (
            paper.authors[0].split()[-1] if paper.authors else "unknown"
        )
        year = paper.year or "nd"
        key = f"{first_author.lower()}{year}"

        print(f"@article{{{key},")
        print(f"  title = {{{paper.title}}},")
        print(f"  author = {{{' and '.join(paper.authors)}}},")
        if paper.year:
            print(f"  year = {{{paper.year}}},")
        if paper.doi:
            print(f"  doi = {{{paper.doi}}},")
        if paper.venue:
            print(f"  journal = {{{paper.venue}}},")
        print("}")
        print()


FORMATTERS: dict[str, type] = {
    "table": TableFormatter,
    "csv": CSVFormatter,
    "json": JSONFormatter,
    "bibtex": BibTeXFormatter,
}


def display_results(results: list, output_format: str = "table") -> None:
    """
    Display search results in the specified format.

    Args:
        results: List of SearchResult objects to display.
        output_format: One of 'table', 'csv', 'json', or 'bibtex'.
    """
    formatter_class = FORMATTERS.get(output_format, TableFormatter)
    formatter = formatter_class()
    formatter.format(results)


app = typer.Typer(
    name="scholar",
    help="Structured literature search tool for systematic reviews.",
    no_args_is_help=True,
)


@app.callback(
    epilog="Copyright (c) 2025--2026 Daniel Bosk, Ric Glassey.\n"
    "MIT License.\n"
    "Web: https://github.com/dbosk/scholar",
)
def callback(
    verbose: Annotated[
        int,
        typer.Option(
            "--verbose",
            "-v",
            count=True,
            help="Increase verbosity (can be repeated: -v, -vv, -vvv).",
        ),
    ] = 0,
    quiet: Annotated[
        int,
        typer.Option(
            "--quiet",
            "-q",
            count=True,
            help="Decrease verbosity (can be repeated: -q, -qq, -qqq).",
        ),
    ] = 0,
) -> None:
    """
    Scholar: A tool for structured literature searches.

    Use 'scholar search' to query bibliographic databases.
    Use 'scholar rq' to start from a research question.
    """
    # Calculate net verbosity: positive = more verbose, negative = quieter
    net_verbosity = verbose - quiet

    # Silence level for net_verbosity <= -3
    SILENCE_LEVEL = logging.CRITICAL + 50

    # Map net verbosity to logging levels
    if net_verbosity >= 2:
        log_level = logging.DEBUG  # 10
    elif net_verbosity == 1:
        log_level = logging.INFO  # 20
    elif net_verbosity == 0:
        log_level = logging.WARNING  # 30
    elif net_verbosity == -1:
        log_level = logging.ERROR  # 40
    elif net_verbosity == -2:
        log_level = logging.CRITICAL  # 50
    else:  # net_verbosity <= -3
        log_level = SILENCE_LEVEL  # Silence everything

    # Use force=True to ensure this takes effect even if another dependency
    # configured logging before Scholar's callback runs.
    logging.basicConfig(
        level=log_level,
        format="%(levelname)s: %(message)s",
        force=True,
    )


def complete_provider(incomplete: str) -> list[str]:
    """Provide shell completion for provider names."""
    from scholar.providers import PROVIDERS

    return [name for name in PROVIDERS.keys() if name.startswith(incomplete)]


SEARCH_FORMATS = ["auto", "table", "csv", "json", "bibtex"]
DISPLAY_FORMATS = ["table", "json"]
EXPORT_FORMATS = ["csv", "latex", "all"]
SYNTHESIS_FORMATS = ["markdown", "latex"]


def complete_search_format(incomplete: str) -> list[str]:
    """Provide shell completion for search output formats."""
    return [f for f in SEARCH_FORMATS if f.startswith(incomplete)]


def complete_display_format(incomplete: str) -> list[str]:
    """Provide shell completion for display formats (table/json)."""
    return [f for f in DISPLAY_FORMATS if f.startswith(incomplete)]


def complete_export_format(incomplete: str) -> list[str]:
    """Provide shell completion for export formats."""
    return [f for f in EXPORT_FORMATS if f.startswith(incomplete)]


def complete_synthesis_format(incomplete: str) -> list[str]:
    """Provide shell completion for synthesis formats."""
    return [f for f in SYNTHESIS_FORMATS if f.startswith(incomplete)]


CACHE_ACTIONS = ["clear", "info", "path"]
PDF_ACTIONS = ["open", "info", "clear", "path"]


def complete_cache_action(incomplete: str) -> list[str]:
    """Provide shell completion for cache actions."""
    return [a for a in CACHE_ACTIONS if a.startswith(incomplete)]


def complete_pdf_action(incomplete: str) -> list[str]:
    """Provide shell completion for PDF actions."""
    return [a for a in PDF_ACTIONS if a.startswith(incomplete)]


def complete_session_name(incomplete: str) -> list[str]:
    """Provide shell completion for session names."""
    from scholar.review import list_sessions

    try:
        sessions = list_sessions()
        return [
            s["name"] for s in sessions if s["name"].startswith(incomplete)
        ]
    except Exception:
        return []


def complete_model(incomplete: str) -> list[str]:
    """Provide shell completion for installed llm models."""
    try:
        import llm
    except Exception:
        return []

    try:
        model_ids = [m.model_id for m in llm.get_models()]
    except Exception:
        return []

    # Keep ordering stable and drop duplicates.
    seen: set[str] = set()
    results: list[str] = []
    for model_id in model_ids:
        if model_id in seen:
            continue
        seen.add(model_id)
        if model_id.startswith(incomplete):
            results.append(model_id)

    return results


def complete_paper_id(incomplete: str) -> list[str]:
    """Provide shell completion for paper IDs with notes."""
    from scholar.notes import list_papers_with_notes

    try:
        notes = list_papers_with_notes()
        return [
            n.paper_id for n in notes if n.paper_id.startswith(incomplete)
        ]
    except Exception:
        return []


@app.command()
def search(
    query: Annotated[str, typer.Argument(help="Search query string")],
    provider: Annotated[
        Optional[list[str]],
        typer.Option(
            "--provider",
            "-p",
            help="Provider to query. Repeatable. Default: all available providers.",
            autocompletion=complete_provider,
        ),
    ] = None,
    output_format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format: auto, table, csv, json, or bibtex. "
            "Auto selects table for TTY, csv otherwise.",
            autocompletion=complete_search_format,
        ),
    ] = "auto",
    review: Annotated[
        bool,
        typer.Option(
            "--review",
            "-r",
            help="Launch interactive TUI to review and filter results.",
        ),
    ] = False,
    name: Annotated[
        Optional[str],
        typer.Option(
            "--name",
            "-n",
            help="Session name for review. Use same name to append results from "
            "multiple searches. Defaults to query string.",
        ),
    ] = None,
    limit: Annotated[
        int,
        typer.Option(
            "--limit",
            "-l",
            help="Maximum results per provider (default: 1000). "
            "Use 0 for unlimited (fetch all pages).",
        ),
    ] = 1000,
    enrich: Annotated[
        bool,
        typer.Option(
            "--enrich",
            "-e",
            help="Fetch missing abstracts from Semantic Scholar/OpenAlex. "
            "Only works for papers with DOIs.",
        ),
    ] = False,
    report: Annotated[
        bool,
        typer.Option(
            "--report",
            "-R",
            help="Prompt to save reports (LaTeX, BibTeX, CSV) after review.",
        ),
    ] = False,
    year: Annotated[
        Optional[str],
        typer.Option(
            "--year",
            "-y",
            help="Publication year or range (e.g., 2020, 2020-2024, 2020-, -2024). "
            "Supported: all providers.",
        ),
    ] = None,
    open_access: Annotated[
        bool,
        typer.Option(
            "--open-access",
            "-oa",
            help="Only return open access papers. "
            "Supported: Semantic Scholar, OpenAlex, IEEE. "
            "Ignored: DBLP, WoS.",
        ),
    ] = False,
    venue: Annotated[
        Optional[str],
        typer.Option(
            "--venue",
            "-v",
            help="Filter by venue/journal name. "
            "Supported: Semantic Scholar, OpenAlex, DBLP (query), WoS (query). "
            "Ignored: IEEE.",
        ),
    ] = None,
    min_citations: Annotated[
        Optional[int],
        typer.Option(
            "--min-citations",
            "-c",
            help="Minimum citation count. "
            "Supported: Semantic Scholar, OpenAlex. "
            "Ignored: DBLP, WoS, IEEE.",
        ),
    ] = None,
    pub_type: Annotated[
        Optional[list[str]],
        typer.Option(
            "--type",
            "-t",
            help="Publication type(s): article, conference, review, book, preprint, dataset. "
            "Repeatable. Supported: all providers (with varying type mappings).",
        ),
    ] = None,
) -> None:
    """
    Search bibliographic databases with structured queries.

    Queries all available providers when no -p option is given. A provider is
    available if it doesn't require an API key, or has its API key configured.
    Use 'scholar providers' to see which providers are currently available.

    Query syntax varies by provider. Use 'scholar syntax' to see supported
    operators (AND, OR, NOT), wildcards, and phrase search for each provider.

    Examples:
        scholar search "machine learning privacy"
        scholar search "federated learning" -p s2 -f json
        scholar search "neural networks" -p openalex -p dblp -p s2
    """
    from scholar import Search, SearchFilters
    from scholar.providers import get_default_providers
    import sys

    # Determine which providers will be used
    if provider is None:
        provider_names = [p.name for p in get_default_providers()]
    else:
        provider_names = provider

    effective_limit = UNLIMITED_PROVIDER_LIMIT if limit == 0 else limit
    limit_label = "unlimited" if limit == 0 else str(limit)

    logger.info(f"Searching with providers: {', '.join(provider_names)}")
    logger.debug(f"Search query: '{query}'")
    logger.debug(f"Limit per provider: {limit_label}")

    # Build search filters from CLI options
    filters = None
    if any([year, open_access, venue, min_citations is not None, pub_type]):
        filters = SearchFilters(
            year=year,
            open_access=open_access,
            venue=venue,
            min_citations=min_citations,
            pub_types=pub_type,
        )

    s = Search(query)
    results = s.execute(
        providers=provider, limit=effective_limit, filters=filters
    )

    logger.debug(f"Retrieved {len(results)} result sets")

    # Merge results from all providers (deduplicates and consolidates data)
    from functools import reduce

    if len(results) > 1:
        logger.info(f"Merging {len(results)} result sets")
        merged = reduce(lambda a, b: a.merge(b), results)
        merged_results = [merged]
    elif len(results) == 1:
        merged_results = results
    else:
        logger.warning("No search results returned")
        merged_results = []

    # Optionally enrich papers with missing abstracts
    if enrich and merged_results:
        from scholar.enrich import enrich_papers, needs_enrichment
        from rich.progress import Progress

        # Count papers that need enrichment
        papers = merged_results[0].papers
        papers_to_enrich = [
            p for p in papers if needs_enrichment(p, ["abstract"]) and p.doi
        ]

        if papers_to_enrich:
            with Progress() as progress:
                task = progress.add_task(
                    "[cyan]Enriching papers...", total=len(papers_to_enrich)
                )

                def update_progress(current: int, total: int) -> None:
                    progress.update(task, completed=current)

                enriched = enrich_papers(
                    papers, progress_callback=update_progress
                )
                merged_results[0] = SearchResult(
                    query=merged_results[0].query,
                    provider=merged_results[0].provider,
                    timestamp=merged_results[0].timestamp,
                    papers=enriched,
                    filters=merged_results[0].filters,
                )

    # If review mode, launch TUI instead of displaying results
    if review:
        from scholar.tui import run_review

        session_name = name if name else query
        run_review(
            merged_results,
            query,
            session_name,
            prompt_report=report,
            search_filters=filters,
        )
        return

    # Auto-detect format based on TTY
    actual_format = output_format
    if output_format == "auto":
        actual_format = "table" if sys.stdout.isatty() else "csv"

    display_results(merged_results, actual_format)


@app.command()
def rq(
    research_question: Annotated[
        str | None,
        typer.Argument(
            help="Research question (omit to write in $EDITOR).",
        ),
    ] = None,
    provider: Annotated[
        Optional[list[str]],
        typer.Option(
            "--provider",
            "-p",
            help="Provider to query. Repeatable. Default: all available providers.",
            autocompletion=complete_provider,
        ),
    ] = None,
    name: Annotated[
        Optional[str],
        typer.Option(
            "--name",
            "-n",
            help="Session name for persistence. Defaults to derived from the research question.",
        ),
    ] = None,
    limit: Annotated[
        int,
        typer.Option(
            "--limit",
            "-l",
            help="Maximum results per provider (default: 1000). Use 0 for unlimited.",
        ),
    ] = 1000,
    count: Annotated[
        int,
        typer.Option(
            "--count",
            help="Number of papers to label with the LLM (default: 20).",
        ),
    ] = 20,
    model: Annotated[
        str | None,
        typer.Option(
            "--model",
            "-m",
            help="LLM model to use (uses llm default if not specified).",
            autocompletion=complete_model,
        ),
    ] = None,
    no_enrich: Annotated[
        bool,
        typer.Option(
            "--no-enrich",
            help="Skip automatic enrichment of papers without abstracts.",
        ),
    ] = False,
    year: Annotated[
        Optional[str],
        typer.Option(
            "--year",
            "-y",
            help="Publication year or range (e.g., 2020, 2020-2024, 2020-, -2024). "
            "Supported: all providers.",
        ),
    ] = None,
    open_access: Annotated[
        bool,
        typer.Option(
            "--open-access",
            "-oa",
            help="Only return open access papers. "
            "Supported: Semantic Scholar, OpenAlex, IEEE. "
            "Ignored: DBLP, WoS.",
        ),
    ] = False,
    venue: Annotated[
        Optional[str],
        typer.Option(
            "--venue",
            "-v",
            help="Filter by venue/journal name. "
            "Supported: Semantic Scholar, OpenAlex, DBLP (query), WoS (query). "
            "Ignored: IEEE.",
        ),
    ] = None,
    min_citations: Annotated[
        Optional[int],
        typer.Option(
            "--min-citations",
            "-c",
            help="Minimum citation count. "
            "Supported: Semantic Scholar, OpenAlex. "
            "Ignored: DBLP, WoS, IEEE.",
        ),
    ] = None,
    pub_type: Annotated[
        Optional[list[str]],
        typer.Option(
            "--type",
            "-t",
            help="Publication type(s): article, conference, review, book, preprint, dataset. "
            "Repeatable. Supported: all providers (with varying type mappings).",
        ),
    ] = None,
) -> None:
    """
    Research-question driven search with LLM query generation and labeling.

    The research question becomes the session's research context, and provider-
    specific queries are recorded in [[query_provider_pairs]] for
    reproducibility.

    Examples:
        scholar rq "How do LLMs support novice programming?" -p openalex -p dblp
        scholar rq --year 2020- --open-access --count 20
        scholar rq "..." --limit 0  # Fetch all pages
    """
    from datetime import datetime
    import json
    import re

    from scholar import SearchFilters
    from scholar.providers import get_default_providers, get_provider
    from scholar.scholar import SearchResult
    from scholar.review import create_review_session, save_session
    from scholar.llm_review import (
        classify_papers_with_llm,
        apply_llm_decisions,
        get_review_statistics,
    )

    console = Console()

    def generate_provider_queries(
        rq_text: str,
        provider_names: list[str],
        model_id: str | None,
    ) -> dict[str, str]:
        try:
            import llm
        except ImportError:
            raise ImportError(
                "The 'llm' package is required for 'rq'. "
                "Install it with: pip install llm"
            )

        model_obj = llm.get_model(model_id) if model_id else llm.get_model()

        rules = {
            "s2": (
                "Semantic Scholar: plain keywords and quoted phrases are fine; "
                "avoid provider-specific field prefixes."
            ),
            "openalex": (
                "OpenAlex: natural-language keywords work well; use UPPERCASE "
                "AND/OR/NOT if you include boolean operators."
            ),
            "dblp": (
                "DBLP: no OR/NOT support; space-separated terms behave like AND; "
                "keep it simple (keywords/phrases only)."
            ),
            "wos": (
                "Web of Science: use UPPERCASE boolean operators; if you include "
                "field tags use TS=(...), TI=(...), AU=(...). Prefer TS=(...)."
            ),
            "ieee": (
                "IEEE Xplore: supports boolean operators; keep query concise; "
                "avoid field-tag syntax."
            ),
            "arxiv": (
                "arXiv: supports boolean operators; avoid adding category filters "
                "(cat:) because --venue handles that separately."
            ),
        }

        rule_lines = [
            f"- {p}: {rules[p]}" for p in provider_names if p in rules
        ]
        rules_text = "\n".join(rule_lines)

        prompt = (
            "You generate search queries for academic literature databases.\n"
            "Given this research question, generate one concise query per provider.\n\n"
            "Important: Do NOT include year ranges, venue names, open access, "
            "citation counts, or publication types in the query text; those are "
            "handled separately via CLI filters.\n\n"
            f"Research question:\n{rq_text}\n\n"
            f"Providers: {', '.join(provider_names)}\n\n"
            "Provider-specific query rules:\n"
            f"{rules_text}\n\n"
            "Return JSON in exactly this format:\n"
            '{"queries":[{"provider":"openalex","query":"..."}, ...]}\n'
        )

        response = model_obj.prompt(prompt)
        text = response.text()

        # Extract JSON from possible markdown fences
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        json_str = match.group(1) if match else text

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            # Fallback: try to find any JSON object
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                raise ValueError("LLM did not return valid JSON for queries")
            data = json.loads(match.group(0))

        queries: dict[str, str] = {}
        if (
            isinstance(data, dict)
            and "queries" in data
            and isinstance(data["queries"], list)
        ):
            for item in data["queries"]:
                pname = str(item.get("provider", "")).strip()
                q = str(item.get("query", "")).strip()
                if pname and q:
                    queries[pname] = q
        elif isinstance(data, dict):
            # Allow mapping form: {"openalex": "...", ...}
            for pname, q in data.items():
                if isinstance(q, str) and q.strip():
                    queries[str(pname)] = q.strip()

        # Fill missing providers with a simple fallback query
        for pname in provider_names:
            if pname not in queries:
                queries[pname] = rq_text.splitlines()[0][:200]

        return queries

    if research_question is None:
        template = (
            "# Write your research question below. Lines starting with # are ignored.\n"
            "\n"
        )
        edited = typer.edit(template) or ""
        lines = [
            line
            for line in edited.splitlines()
            if not line.strip().startswith("#")
        ]
        rq_text = "\n".join(lines).strip()
    else:
        rq_text = research_question.strip()

    if not rq_text:
        console.print("[red]Research question cannot be empty[/red]")
        raise typer.Exit(1)

    if provider is None:
        provider_names = [p.name for p in get_default_providers()]
    else:
        provider_names = provider

    if not provider_names:
        console.print("[red]No providers available[/red]")
        raise typer.Exit(1)
    filters = None
    if any([year, open_access, venue, min_citations is not None, pub_type]):
        filters = SearchFilters(
            year=year,
            open_access=open_access,
            venue=venue,
            min_citations=min_citations,
            pub_types=pub_type,
        )
    effective_limit = UNLIMITED_PROVIDER_LIMIT if limit == 0 else limit
    provider_queries = generate_provider_queries(
        rq_text, provider_names, model
    )
    results: list[SearchResult] = []
    timestamp = datetime.now().isoformat()
    for pname in provider_names:
        p = get_provider(pname)
        if p is None:
            continue

        q = provider_queries.get(pname, rq_text)
        papers = p.search(q, limit=effective_limit, filters=filters)
        results.append(
            SearchResult(
                query=q,
                provider=pname,
                timestamp=timestamp,
                papers=papers,
                filters=filters.as_dict() if filters else None,
            )
        )

    if not results:
        console.print("[yellow]No results returned[/yellow]")
        raise typer.Exit(0)
    if name is None:
        safe_name = "".join(
            c if c.isalnum() or c in "-_" else "_" for c in rq_text[:30]
        )
        name = f"rq_{safe_name}" if safe_name else "rq"
    session = create_review_session(results, rq_text, session_name=name)
    session.research_context = rq_text
    try:
        batch = classify_papers_with_llm(
            session=session,
            count=count,
            model_id=model,
            enrich_missing=not no_enrich,
            require_examples=False,
        )
        updated = apply_llm_decisions(session, batch)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except ImportError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    session_path = save_session(session)
    stats = get_review_statistics(session)

    console.print(f"[green]Saved session:[/green] {session_path}")
    console.print(f"  Total papers: {stats['total']}")
    console.print(f"  Labeled by LLM: {len(updated)}")
    console.print(f"  Pending: {stats['pending']}")


@app.command()
def enrich(
    session: Annotated[
        str,
        typer.Argument(
            help="Name of the review session to enrich.",
            autocompletion=complete_session_name,
        ),
    ],
) -> None:
    """
    Fetch missing abstracts for papers in a review session.

    Looks up papers by DOI in Semantic Scholar and OpenAlex to fill in
    missing abstracts. Only papers with DOIs can be enriched.

    Example:
        scholar enrich "machine learning"
    """
    from scholar.review import load_session, save_session
    from scholar.enrich import enrich_papers, needs_enrichment
    from rich.progress import Progress

    console = Console()

    # Load the session
    session_data = load_session(session)
    if session_data is None:
        console.print(f"Session not found: {session}")
        raise typer.Exit(1)

    # Extract papers from decisions
    papers = [decision.paper for decision in session_data.decisions]
    papers_with_doi = [p for p in papers if p.doi]
    papers_to_enrich = [
        p for p in papers_with_doi if needs_enrichment(p, ["abstract"])
    ]

    if not papers_to_enrich:
        console.print(
            "[yellow]No papers need enrichment (all have abstracts or lack DOIs).[/yellow]"
        )
        return

    console.print(
        f"[cyan]Found {len(papers_to_enrich)} papers to enrich (of {len(papers)} total).[/cyan]"
    )

    # Enrich with progress bar
    with Progress() as progress:
        task = progress.add_task("[cyan]Enriching...", total=len(papers))

        def update_progress(current: int, total: int) -> None:
            progress.update(task, completed=current)

        enriched_papers = enrich_papers(
            papers, progress_callback=update_progress
        )

    # Update decisions with enriched papers
    paper_map = {p.doi: p for p in enriched_papers if p.doi}
    for decision in session_data.decisions:
        if decision.paper.doi and decision.paper.doi in paper_map:
            decision.paper = paper_map[decision.paper.doi]
    save_session(session_data)

    # Count how many were actually enriched
    enriched_count = sum(
        1
        for orig, new in zip(papers, enriched_papers)
        if orig.abstract != new.abstract and new.abstract
    )
    console.print(f"[green]Enriched {enriched_count} papers.[/green]")


@app.command()
def providers() -> None:
    """
    List available search providers and their configuration.

    Shows which providers require API keys and how to obtain them.
    """
    from scholar.providers import get_all_providers

    console = Console()

    table = Table(title="Available Search Providers", box=box.HORIZONTALS)
    table.add_column("Provider", style="cyan")
    table.add_column("Default", style="magenta")
    table.add_column("API Key", style="yellow")
    table.add_column("Environment Variable", style="green")
    table.add_column("How to Get Key", style="dim")

    provider_info = {
        "s2": {
            "required": False,
            "env_var": "S2_API_KEY",
            "how_to_get": "api.semanticscholar.org (optional, higher rate limits)",
        },
        "openalex": {
            "required": False,
            "env_var": "OPENALEX_EMAIL",
            "how_to_get": "Any email (optional, faster responses)",
        },
        "dblp": {
            "required": False,
            "env_var": "-",
            "how_to_get": "No key needed",
        },
        "wos": {
            "required": True,
            "env_var": "WOS_EXPANDED_API_KEY or WOS_STARTER_API_KEY",
            "how_to_get": "developer.clarivate.com (Expanded API preferred)",
        },
        "ieee": {
            "required": True,
            "env_var": "IEEE_API_KEY",
            "how_to_get": "developer.ieee.org",
        },
    }

    for provider in get_all_providers():
        info = provider_info.get(provider.name, {})
        is_available = provider.is_available()
        default_status = (
            "[green]Yes[/green]" if is_available else "[dim]No[/dim]"
        )
        required = info.get("required", False)
        key_status = (
            "[red]Required[/red]" if required else "[green]Optional[/green]"
        )
        table.add_row(
            provider.name,
            default_status,
            key_status,
            info.get("env_var", "-"),
            info.get("how_to_get", ""),
        )

    console.print(table)
    console.print()
    console.print(
        "[dim]Default providers are those currently available (no key required or key configured).[/dim]"
    )
    console.print(
        "[dim]Use -p <name> to select specific providers for a search.[/dim]"
    )


@app.command()
def syntax() -> None:
    """
    Show query syntax supported by each provider.

    Different providers support different features like boolean operators,
    wildcards, and phrase search. Use this command to see what's available.
    """
    console = Console()

    console.print()
    console.print("[bold]Query Syntax Reference[/bold]")
    console.print()
    console.print(
        "Different providers support different query syntax. This reference"
    )
    console.print("shows what features are available for each provider.")
    console.print()

    # Boolean operators table
    table = Table(title="Boolean Operators", box=box.HORIZONTALS)
    table.add_column("Provider", style="cyan")
    table.add_column("AND", style="green")
    table.add_column("OR", style="green")
    table.add_column("NOT", style="green")
    table.add_column("Grouping", style="green")
    table.add_column("Notes", style="dim")

    table.add_row(
        "s2",
        "[green]✓[/]",
        "[green]✓[/]",
        "[green]✓[/]",
        "[green]✓[/]",
        "Use + for AND, | for OR in bulk API",
    )
    table.add_row(
        "openalex",
        "[green]✓[/]",
        "[green]✓[/]",
        "[green]✓[/]",
        "[green]✓[/]",
        "Must be UPPERCASE",
    )
    table.add_row(
        "dblp",
        "[dim]implicit[/]",
        "[red]✗[/]",
        "[red]✗[/]",
        "[red]✗[/]",
        "Space = AND, NOT disabled",
    )
    table.add_row(
        "wos",
        "[green]✓[/]",
        "[green]✓[/]",
        "[green]✓[/]",
        "[green]✓[/]",
        "Must be UPPERCASE, supports NEAR/SAME",
    )
    table.add_row(
        "ieee",
        "[green]✓[/]",
        "[green]✓[/]",
        "[green]✓[/]",
        "[green]✓[/]",
        "Must be UPPERCASE, supports ONEAR",
    )
    table.add_row(
        "arxiv",
        "[green]✓[/]",
        "[green]✓[/]",
        "[green]✓[/]",
        "[green]✓[/]",
        "Use ANDNOT instead of NOT",
    )

    console.print(table)
    console.print()

    # Other features table
    table2 = Table(title="Other Features", box=box.HORIZONTALS)
    table2.add_column("Provider", style="cyan")
    table2.add_column("Wildcards", style="green")
    table2.add_column("Phrase", style="green")
    table2.add_column("Field Search", style="green")
    table2.add_column("Notes", style="dim")

    table2.add_row(
        "s2",
        "[red]✗[/]",
        '[green]✓[/] "..."',
        "[red]✗[/]",
        "Simple keyword search",
    )
    table2.add_row(
        "openalex",
        "[red]✗[/]",
        '[green]✓[/] "..."',
        "[red]✗[/]",
        "Stemming enabled",
    )
    table2.add_row(
        "dblp",
        "[green]✓[/] prefix*",
        "[red]✗[/] disabled",
        "[green]✓[/] author:",
        "author:Name, year:YYYY",
    )
    table2.add_row(
        "wos",
        "[green]✓[/] * $ ?",
        '[green]✓[/] "..."',
        "[green]✓[/] TS= TI= AU=",
        "TS=topic, TI=title, AU=author",
    )
    table2.add_row(
        "ieee",
        "[green]✓[/] *",
        '[green]✓[/] "..."',
        "[green]✓[/]",
        "Max 5 wildcards per search",
    )
    table2.add_row(
        "arxiv",
        "[red]✗[/]",
        '[green]✓[/] "..."',
        "[green]✓[/] ti: au: cat:",
        "ti:title, au:author, cat:category",
    )

    console.print(table2)
    console.print()

    # Examples
    console.print("[bold]Examples:[/bold]")
    console.print()
    examples = [
        ("s2/openalex", '"machine learning" AND privacy'),
        ("dblp", "machine learning privacy  [space = AND]"),
        ("wos", 'TS=("machine learning" AND privacy)'),
        ("ieee", '"machine learning" AND privacy NOT survey'),
        ("arxiv", 'ti:"machine learning" AND cat:cs.AI'),
    ]
    for provider, example in examples:
        console.print(f"  [cyan]{provider:12}[/]  {example}")
    console.print()

    console.print(
        "[dim]Tip: When in doubt, use simple keywords without operators.[/dim]"
    )
    console.print("[dim]All providers support basic keyword search.[/dim]")
    console.print()

    console.print("[bold]Documentation:[/bold]")
    console.print()
    docs = [
        ("s2", "https://www.semanticscholar.org/product/api/tutorial"),
        (
            "openalex",
            "https://docs.openalex.org/how-to-use-the-api/get-lists-of-entities/search-entities",
        ),
        ("dblp", "https://dblp.org/faq/How+to+use+the+dblp+search+API.html"),
        (
            "wos",
            "https://webofscience.help.clarivate.com/en-us/Content/search-rules.html",
        ),
        (
            "ieee",
            "https://ieeexplore.ieee.org/Xplorehelp/searching-ieee-xplore/command-search",
        ),
        (
            "arxiv",
            "https://info.arxiv.org/help/api/user-manual.html#query_details",
        ),
    ]
    for provider, url in docs:
        console.print(f"  [cyan]{provider:12}[/]  {url}")


@app.command()
def cache(
    action: Annotated[
        str,
        typer.Argument(
            help="Action: clear, info, or path",
            autocompletion=complete_cache_action,
        ),
    ],
) -> None:
    """
    Manage the search result cache.

    Actions:
        clear  - Delete all cached search results
        info   - Show cache statistics (entries, size, location)
        path   - Print the cache directory path
    """
    from scholar.cache import clear_cache, get_cache_stats

    console = Console()

    if action == "clear":
        count = clear_cache()
        console.print(f"Cleared {count} cached provider(s).")

    elif action == "info":
        stats = get_cache_stats()
        table = Table(title="Cache Statistics", box=box.HORIZONTALS)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Location", stats["cache_dir"])
        table.add_row("Total entries", str(stats["total_entries"]))
        size_kb = stats["total_size_bytes"] / 1024
        table.add_row("Total size", f"{size_kb:.1f} KB")

        console.print(table)

        if stats["providers"]:
            console.print()
            provider_table = Table(
                title="Entries per Provider", box=box.HORIZONTALS
            )
            provider_table.add_column("Provider", style="cyan")
            provider_table.add_column("Cached queries", justify="right")

            for provider_name, count in sorted(stats["providers"].items()):
                provider_table.add_row(provider_name, str(count))

            console.print(provider_table)

    elif action == "path":
        stats = get_cache_stats()
        print(stats["cache_dir"])

    else:
        console.print(f"[red]Unknown action: {action}[/red]")
        console.print("Valid actions: clear, info, path")
        raise typer.Exit(1)


@app.command()
def pdf(
    action: Annotated[
        str,
        typer.Argument(
            help="Action: open, info, clear, or path",
            autocompletion=complete_pdf_action,
        ),
    ],
    url: Annotated[
        Optional[str],
        typer.Argument(help="PDF URL (required for 'open' action)"),
    ] = None,
) -> None:
    """
    Manage PDF downloads and cache.

    Actions:
        open <url>  - Download (if needed) and open a PDF
        info        - Show PDF cache statistics
        clear       - Delete all cached PDFs
        path        - Print the PDF cache directory path

    Examples:
        scholar pdf open "https://arxiv.org/pdf/2301.00001.pdf"
        scholar pdf info
        scholar pdf clear
    """
    from scholar.pdf import (
        get_pdf_cache_dir,
        get_pdf,
        open_pdf,
        clear_pdf_cache,
        get_pdf_cache_info,
        PDFDownloadError,
    )

    console = Console()

    if action == "open":
        if not url:
            console.print("[red]Error: URL required for 'open' action[/red]")
            console.print("Usage: scholar pdf open <url>")
            raise typer.Exit(1)

        try:
            console.print(f"[dim]Fetching PDF...[/dim]")
            pdf_path = get_pdf(url)
            console.print(f"[green]PDF cached at: {pdf_path}[/green]")

            if open_pdf(pdf_path):
                console.print("[dim]Opened in system viewer[/dim]")
            else:
                console.print("[yellow]Could not open PDF viewer[/yellow]")
                console.print(f"[dim]PDF available at: {pdf_path}[/dim]")
        except PDFDownloadError as e:
            console.print(f"[red]Download failed: {e}[/red]")
            raise typer.Exit(1)

    elif action == "info":
        info = get_pdf_cache_info()
        table = Table(title="PDF Cache Statistics", box=box.HORIZONTALS)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Location", str(get_pdf_cache_dir()))
        table.add_row("Cached PDFs", str(info["count"]))
        size_mb = info["size_bytes"] / (1024 * 1024)
        table.add_row("Total size", f"{size_mb:.1f} MB")

        console.print(table)

    elif action == "clear":
        count = clear_pdf_cache()
        console.print(f"[green]Cleared {count} cached PDF(s).[/green]")

    elif action == "path":
        print(get_pdf_cache_dir())

    else:
        console.print(f"[red]Unknown action: {action}[/red]")
        console.print("Valid actions: open, info, clear, path")
        raise typer.Exit(1)


notes_app = typer.Typer(
    name="notes",
    help="Manage paper notes and annotations.",
    no_args_is_help=False,
)
app.add_typer(notes_app, name="notes")


@notes_app.callback(invoke_without_command=True)
def notes_callback(ctx: typer.Context) -> None:
    """
    Browse and manage paper notes.

    When invoked without a subcommand, launches an interactive TUI
    for browsing all papers with notes.
    """
    if ctx.invoked_subcommand is None:
        from scholar.tui import run_notes_browser

        run_notes_browser()


@notes_app.command("list")
def notes_list(
    output_format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format: table or json.",
            autocompletion=complete_display_format,
        ),
    ] = "table",
) -> None:
    """
    List all papers with notes.

    Shows paper titles, note excerpts, and timestamps.
    """
    from scholar.notes import list_papers_with_notes

    console = Console()
    notes = list_papers_with_notes()

    if not notes:
        console.print("[dim]No papers have notes yet.[/dim]")
        return

    if output_format == "json":
        import json

        output = [
            {
                "paper_id": n.paper_id,
                "title": n.title,
                "note": n.note,
                "created_at": n.created_at.isoformat(),
                "updated_at": n.updated_at.isoformat(),
            }
            for n in notes
        ]
        print(json.dumps(output, indent=2))
    else:
        table = Table(title="Papers with Notes", box=box.HORIZONTALS)
        table.add_column("Title", style="cyan", no_wrap=False, max_width=50)
        table.add_column("Note Preview", style="dim", max_width=30)
        table.add_column("Updated", style="green")

        for note in notes:
            preview = (
                note.note[:50] + "..." if len(note.note) > 50 else note.note
            )
            preview = preview.replace("\n", " ")
            table.add_row(
                note.title[:50] + ("..." if len(note.title) > 50 else ""),
                preview,
                note.updated_at.strftime("%Y-%m-%d"),
            )

        console.print(table)
        console.print(f"\n[dim]Total: {len(notes)} paper(s) with notes[/dim]")


@notes_app.command("show")
def notes_show(
    paper_id: Annotated[
        str,
        typer.Argument(
            help="Paper ID (DOI or hash) to show notes for.",
            autocompletion=complete_paper_id,
        ),
    ],
) -> None:
    """
    Show notes for a specific paper.

    Use 'scholar notes list' to find paper IDs.
    """
    from scholar.notes import list_papers_with_notes

    console = Console()
    notes = list_papers_with_notes()

    for note in notes:
        if note.paper_id == paper_id or paper_id in note.paper_id:
            console.print(f"[bold]{note.title}[/bold]")
            console.print(f"[dim]ID: {note.paper_id}[/dim]")
            console.print(
                f"[dim]Updated: {note.updated_at.strftime('%Y-%m-%d %H:%M')}[/dim]"
            )
            console.print()
            console.print(note.note)
            return

    console.print(f"[red]No notes found for paper ID: {paper_id}[/red]")
    raise typer.Exit(1)


@notes_app.command("export")
def notes_export(
    output: Annotated[
        Path,
        typer.Argument(help="Output file path (JSON format)."),
    ] = Path("scholar_notes.json"),
) -> None:
    """
    Export all notes to a JSON file.

    Creates a backup of all paper notes that can be imported later.
    """
    from scholar.notes import export_notes

    console = Console()
    count = export_notes(output)
    console.print(f"[green]Exported {count} note(s) to {output}[/green]")


@notes_app.command("import")
def notes_import(
    input_file: Annotated[
        Path,
        typer.Argument(help="Input file path (JSON format)."),
    ],
    merge: Annotated[
        bool,
        typer.Option(
            "--merge",
            "-m",
            help="Merge with existing notes (default: replace).",
        ),
    ] = False,
) -> None:
    """
    Import notes from a JSON file.

    By default, replaces existing notes. Use --merge to combine.
    """
    from scholar.notes import import_notes

    console = Console()

    if not input_file.exists():
        console.print(f"[red]File not found: {input_file}[/red]")
        raise typer.Exit(1)

    count = import_notes(input_file, merge=merge)
    action = "Merged" if merge else "Imported"
    console.print(
        f"[green]{action} {count} note(s) from {input_file}[/green]"
    )


@notes_app.command("clear")
def notes_clear(
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Skip confirmation prompt.",
        ),
    ] = False,
) -> None:
    """
    Delete all notes.

    Requires --force flag to confirm deletion.
    """
    from scholar.notes import list_papers_with_notes, get_data_dir
    import shutil

    console = Console()
    notes = list_papers_with_notes()

    if not notes:
        console.print("[dim]No notes to clear.[/dim]")
        return

    if not force:
        console.print(
            f"[yellow]This will delete {len(notes)} note(s).[/yellow]"
        )
        console.print("[yellow]Use --force to confirm.[/yellow]")
        raise typer.Exit(1)

    # Delete the notes file
    notes_file = get_data_dir() / "paper_notes.json"
    if notes_file.exists():
        notes_file.unlink()

    console.print(f"[green]Deleted {len(notes)} note(s).[/green]")


sessions_app = typer.Typer(
    name="sessions",
    help="Manage saved review sessions.",
    no_args_is_help=True,
)
app.add_typer(sessions_app, name="sessions")


@sessions_app.command("list")
def sessions_list(
    output_format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format: table or json.",
            autocompletion=complete_display_format,
        ),
    ] = "table",
) -> None:
    """
    List all saved review sessions.

    Shows query, providers, timestamps, and paper counts.
    """
    from scholar.review import list_sessions

    console = Console()
    sessions = list_sessions()

    if not sessions:
        console.print("[dim]No saved sessions found.[/dim]")
        return

    if output_format == "json":
        print(json.dumps(sessions, indent=2, default=str))
    else:
        table = Table(title="Saved Review Sessions", box=box.HORIZONTALS)
        table.add_column("Name", style="cyan", no_wrap=False)
        table.add_column("Date", style="dim")
        table.add_column("Kept", style="green", justify="right")
        table.add_column("Discarded", style="red", justify="right")
        table.add_column("Pending", style="yellow", justify="right")

        for s in sessions:
            table.add_row(
                s["name"],
                s["timestamp"].strftime("%Y-%m-%d %H:%M"),
                str(s["kept"]),
                str(s["discarded"]),
                str(s["pending"]),
            )

        console.print(table)
        console.print(f"\n[dim]Total: {len(sessions)} session(s)[/dim]")


@sessions_app.command("show")
def sessions_show(
    name: Annotated[
        str,
        typer.Argument(
            help="Session name or query to show.",
            autocompletion=complete_session_name,
        ),
    ],
    output_format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format: table or json.",
            autocompletion=complete_display_format,
        ),
    ] = "table",
) -> None:
    """
    Show details of a saved review session.

    Displays all papers with their decisions, themes, and motivations.
    Uses a pager for interactive viewing when output is a terminal.
    """
    import sys
    from scholar.review import load_session

    console = Console()
    session = load_session(name)

    if session is None:
        console.print(f"[red]Session not found: {name}[/red]")
        raise typer.Exit(1)

    if output_format == "json":
        output = {
            "query": session.query,
            "providers": session.providers,
            "query_provider_pairs": session.query_provider_pairs,
            "timestamp": session.timestamp.isoformat(),
            "decisions": [
                {
                    "title": d.paper.title,
                    "authors": d.paper.authors,
                    "year": d.paper.year,
                    "status": d.status.value,
                    "tags": d.tags,
                    "provider": d.provider,
                }
                for d in session.decisions
            ],
        }
        print(json.dumps(output, indent=2))
    else:
        # Build output using Rich markup, render directly to console
        def print_session_details(con: Console) -> None:
            """Print session details with Rich formatting."""
            con.print(f"[bold]Session: {session.query}[/bold]")
            con.print(
                f"[dim]Date: "
                f"{session.timestamp.strftime('%Y-%m-%d %H:%M')}[/dim]"
            )

            # Always show query per provider
            if session.query_provider_pairs:
                con.print("[dim]Queries by provider:[/dim]")
                for query, provider in session.query_provider_pairs:
                    con.print(f"[dim]  {provider}: {query}[/dim]")
            else:
                # Fallback: show providers with session query
                con.print("[dim]Queries by provider:[/dim]")
                for provider in session.providers:
                    con.print(f"[dim]  {provider}: {session.query}[/dim]")
            con.print()

            # Show kept papers
            kept = session.kept_papers
            if kept:
                con.print(f"[green bold]Kept ({len(kept)}):[/green bold]")
                for d in kept:
                    provider = (
                        f" [dim]({d.provider})[/dim]" if d.provider else ""
                    )
                    tags = (
                        f" [dim]\\[{', '.join(d.tags)}][/dim]"
                        if d.tags
                        else ""
                    )
                    con.print(f"  • {d.paper.title}{provider}{tags}")
                con.print()

            # Show discarded papers
            discarded = session.discarded_papers
            if discarded:
                con.print(
                    f"[red bold]Discarded ({len(discarded)}):[/red bold]"
                )
                for d in discarded:
                    provider = (
                        f" [dim]({d.provider})[/dim]" if d.provider else ""
                    )
                    tags = (
                        f" [dim]\\[{', '.join(d.tags)}][/dim]"
                        if d.tags
                        else ""
                    )
                    con.print(f"  • {d.paper.title}{provider}{tags}")
                con.print()

            # Show pending papers
            pending = session.pending_papers
            if pending:
                con.print(
                    f"[yellow bold]Pending ({len(pending)}):[/yellow bold]"
                )
                for d in pending:
                    provider = (
                        f" [dim]({d.provider})[/dim]" if d.provider else ""
                    )
                    con.print(f"  • {d.paper.title}{provider}")

        # Use pager if TTY, otherwise print directly
        if sys.stdout.isatty():
            with console.pager(styles=True):
                print_session_details(console)
        else:
            print_session_details(console)


@sessions_app.command("export")
def sessions_export(
    name: Annotated[
        str,
        typer.Argument(
            help="Session name or query to export.",
            autocompletion=complete_session_name,
        ),
    ],
    output: Annotated[
        Optional[str],
        typer.Option(
            "--output",
            "-o",
            help="Output base filename (without extension). Defaults to session name.",
        ),
    ] = None,
    format_type: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Export format: csv, latex, or all.",
            autocompletion=complete_export_format,
        ),
    ] = "all",
) -> None:
    """
    Export a saved session to file(s).

    Generates CSV and/or LaTeX reports from a saved review session.
    Use --format to select specific formats.
    """
    from scholar.review import (
        load_session,
        generate_latex_report,
        generate_csv_report,
    )

    console = Console()
    session = load_session(name)

    if session is None:
        console.print(f"[red]Session not found: {name}[/red]")
        raise typer.Exit(1)

    # Use session query as default output name (sanitized)
    if output is None:
        # Sanitize query for filename
        safe_name = "".join(
            c if c.isalnum() or c in "-_" else "_" for c in session.query[:30]
        )
        output = f"review_{safe_name}"

    files_created = []

    if format_type in ("csv", "all"):
        csv_path = Path(f"{output}.csv")
        generate_csv_report(session, csv_path)
        files_created.append(csv_path)

    if format_type in ("latex", "all"):
        tex_path = Path(f"{output}.tex")
        generate_latex_report(session, tex_path)
        files_created.append(tex_path)
        files_created.append(tex_path.with_suffix(".bib"))

    console.print("[green]Exported:[/green]")
    for f in files_created:
        console.print(f"  - {f}")


@sessions_app.command("resume")
def sessions_resume(
    name: Annotated[
        str,
        typer.Argument(
            help="Session name or query to resume.",
            autocompletion=complete_session_name,
        ),
    ],
    report: Annotated[
        bool,
        typer.Option(
            "--report",
            "-R",
            help="Prompt to save reports (LaTeX, BibTeX, CSV) after review.",
        ),
    ] = False,
) -> None:
    """
    Resume reviewing a saved session in the TUI.

    Opens the interactive review interface with the saved session loaded.
    Use --report/-R to be prompted for saving reports after review.
    """
    from scholar.review import load_session, save_session
    from scholar.tui import PaperReviewApp, prompt_for_report

    console = Console()
    session = load_session(name)

    if session is None:
        console.print(f"[red]Session not found: {name}[/red]")
        raise typer.Exit(1)

    console.print(f"[dim]Resuming session: {session.query}[/dim]")

    app = PaperReviewApp(session)
    app.run()

    # Save updated session
    save_session(session)

    if report:
        prompt_for_report(session)


llm_app = typer.Typer(
    name="llm",
    help="LLM-assisted paper classification.",
    no_args_is_help=True,
)
app.add_typer(llm_app, name="llm")


@llm_app.command("classify")
def llm_classify(
    session_name: Annotated[
        str,
        typer.Argument(
            help="Session name to classify papers in.",
            autocompletion=complete_session_name,
        ),
    ],
    count: Annotated[
        int,
        typer.Option(
            "--count",
            "-n",
            help="Number of papers to classify in this batch.",
        ),
    ] = 10,
    model: Annotated[
        str | None,
        typer.Option(
            "--model",
            "-m",
            help="LLM model to use (uses llm default if not specified).",
            autocompletion=complete_model,
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Show the prompt without calling LLM.",
        ),
    ] = False,
    no_enrich: Annotated[
        bool,
        typer.Option(
            "--no-enrich",
            help="Skip automatic enrichment of papers without abstracts.",
        ),
    ] = False,
) -> None:
    """
    Classify pending papers using LLM.

    Uses human-reviewed papers as training examples. Requires at least
    5 tagged examples (minimum 1 kept, 1 discarded) before classification.

    Example:
        scholar llm classify "my review" --count 20
    """
    from scholar.review import load_session, save_session
    from scholar.llm_review import (
        classify_papers_with_llm,
        apply_llm_decisions,
        get_review_statistics,
    )

    console = Console()
    session = load_session(session_name)

    if session is None:
        console.print(f"[red]Session not found: {session_name}[/red]")
        raise typer.Exit(1)

    try:
        result = classify_papers_with_llm(
            session=session,
            count=count,
            model_id=model,
            enrich_missing=not no_enrich,
            dry_run=dry_run,
        )

        if dry_run:
            console.print("[bold]Prompt (dry run):[/bold]")
            console.print(result)
            return

        # Apply decisions
        updated = apply_llm_decisions(session, result)

        # Save session
        save_session(session)

        # Show summary
        stats = get_review_statistics(session)
        console.print(f"[green]Classified {len(updated)} papers[/green]")
        console.print(f"  Model: {result.model_id}")
        console.print(f"  LLM unreviewed: {stats['llm_unreviewed']}")
        console.print(f"  Pending: {stats['pending']}")

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except ImportError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@llm_app.command("status")
def llm_status(
    session_name: Annotated[
        str,
        typer.Argument(
            help="Session name to show status for.",
            autocompletion=complete_session_name,
        ),
    ],
    output_format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format: table or json.",
            autocompletion=complete_display_format,
        ),
    ] = "table",
) -> None:
    """
    Show LLM review status for a session.

    Displays counts of human decisions, LLM decisions pending review,
    reviewed LLM decisions, and training examples.
    """
    from scholar.review import load_session
    from scholar.llm_review import get_review_statistics

    console = Console()
    session = load_session(session_name)

    if session is None:
        console.print(f"[red]Session not found: {session_name}[/red]")
        raise typer.Exit(1)

    stats = get_review_statistics(session)

    if output_format == "json":
        print(json.dumps(stats, indent=2))
    else:
        table = Table(
            title=f"LLM Review Status: {session.query}", box=box.ROUNDED
        )
        table.add_column("Category", style="cyan")
        table.add_column("Count", justify="right")

        table.add_row("Human decisions", str(stats["human"]))
        table.add_row("LLM (unreviewed)", str(stats["llm_unreviewed"]))
        table.add_row("LLM (reviewed)", str(stats["llm_reviewed"]))
        table.add_row("Training examples", str(stats["examples"]))
        table.add_row("Pending", str(stats["pending"]))
        table.add_row("Total", str(stats["total"]), style="bold")

        console.print(table)


@llm_app.command("context")
def llm_context(
    session_name: Annotated[
        str,
        typer.Argument(
            help="Session name.",
            autocompletion=complete_session_name,
        ),
    ],
    context: Annotated[
        str | None,
        typer.Argument(
            help="Research context to set (omit to show current).",
        ),
    ] = None,
) -> None:
    """
    Get or set the research context for LLM classification.

    The research context helps the LLM understand your review criteria.
    It should describe your research question and what makes papers relevant.

    Example:
        scholar llm context "my review" "I'm reviewing papers on ..."
    """
    from scholar.review import load_session, save_session

    console = Console()
    session = load_session(session_name)

    if session is None:
        console.print(f"[red]Session not found: {session_name}[/red]")
        raise typer.Exit(1)

    if context is None:
        # Show current context
        if session.research_context:
            console.print("[bold]Research context:[/bold]")
            console.print(session.research_context)
        else:
            console.print("[dim]No research context set.[/dim]")
            console.print(
                '[dim]Use: scholar llm context "session" "your context"[/dim]'
            )
    else:
        # Set context
        session.research_context = context
        save_session(session)
        console.print("[green]Research context updated.[/green]")


@llm_app.command("synthesize")
def llm_synthesize(
    session_name: Annotated[
        str,
        typer.Argument(
            help="Session name to synthesize.",
            autocompletion=complete_session_name,
        ),
    ],
    model: Annotated[
        str | None,
        typer.Option(
            "--model",
            "-m",
            help="LLM model to use (uses llm default if not specified).",
            autocompletion=complete_model,
        ),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output file path (prints to stdout if not specified).",
        ),
    ] = None,
    output_format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format: markdown or latex.",
            autocompletion=complete_synthesis_format,
        ),
    ] = "markdown",
    max_papers: Annotated[
        int | None,
        typer.Option(
            "--max-papers",
            help="Maximum papers to include (manages token limits).",
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Show the prompt without calling LLM.",
        ),
    ] = False,
) -> None:
    """
    Generate a prose literature synthesis from kept papers.

    Creates a coherent narrative explaining how papers in the review
    contribute to answering the research question.

    The output always begins with a "Research Question" section that
    includes provenance (query/provider pairs, timestamp, and review
    statistics), followed by a "Synthesis" section (organized by themes
    when paper tags are present), a "Conclusion", and a deterministic
    reference list.

    For LaTeX output, a full compilable document is produced, including an
    embedded BibTeX file and a biblatex reference section (run biber when
    compiling).

    Requires:
    - At least one kept paper in the session
    - A research context set for the session

    Examples:
         scholar llm synthesize "my review"
        scholar llm synthesize "my review" -o synthesis.md
        scholar llm synthesize "my review" --format latex -o synthesis.tex
    """
    from scholar.review import load_session
    from scholar.llm_review import generate_literature_synthesis

    console = Console()
    session = load_session(session_name)

    if session is None:
        console.print(f"[red]Session not found: {session_name}[/red]")
        raise typer.Exit(1)

    # Validate output format
    if output_format not in ("markdown", "latex"):
        console.print(
            f"[red]Invalid format: {output_format}. "
            "Use 'markdown' or 'latex'.[/red]"
        )
        raise typer.Exit(1)

    try:
        result = generate_literature_synthesis(
            session=session,
            model_id=model,
            output_format=output_format,
            max_papers=max_papers,
            dry_run=dry_run,
        )

        if dry_run:
            console.print("[bold]Prompt (dry run):[/bold]")
            console.print(result)
            return

        # Output the synthesis
        synthesis_text = result.synthesis

        if output:
            output.write_text(synthesis_text)
            console.print(f"[green]Synthesis written to {output}[/green]")
            console.print(f"  Papers: {result.paper_count}")
            console.print(f"  Themes: {', '.join(result.themes)}")
            console.print(f"  Model: {result.model_id}")
        else:
            # Print to stdout
            console.print(synthesis_text)

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except ImportError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


SUBMODULES = ["snowball", "tuxedo"]


def register_submodules() -> None:
    """
    Dynamically register subcommand modules if available.

    This allows snowball and tuxedo to be added as submodules
    without modifying this file. Each submodule should provide a
    `register_commands(app)` function.

    Tries both `scholar.<name>` and `<name>` import paths to support
    different installation configurations.
    """
    for name in SUBMODULES:
        module = None

        # Try scholar.<name> first (for nested packages)
        try:
            module = __import__(
                f"scholar.{name}", fromlist=["register_commands"]
            )
        except ImportError:
            pass

        # Fall back to top-level <name> (for sibling packages)
        if module is None:
            try:
                module = __import__(name, fromlist=["register_commands"])
            except ImportError:
                pass

        if module is not None and hasattr(module, "register_commands"):
            module.register_commands(app)


def main() -> None:
    """Main entry point for the Scholar CLI."""
    register_submodules()
    app()
