"""
LLM-assisted paper classification for systematic reviews.

Provides functions for classifying papers using large language models,
learning from human-tagged examples in a round-based workflow.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import hashlib
import json
import logging
import re

from scholar.cache import load_cache, register_cache
from scholar.review import (
    ReviewSession,
    ReviewDecision,
    DecisionStatus,
    ReviewSource,
)
from scholar.scholar import Paper

logger = logging.getLogger(__name__)
# Minimum requirements for LLM classification
MIN_TOTAL_EXAMPLES = 5
MIN_KEPT_EXAMPLES = 1
MIN_DISCARDED_EXAMPLES = 1

# Default batch size for classification
DEFAULT_BATCH_SIZE = 10

# Maximum examples to include in prompt (to manage token limits)
MAX_KEPT_EXAMPLES = 10
MAX_DISCARDED_EXAMPLES = 10


@dataclass
class LLMDecision:
    """
    A single LLM classification decision for a paper.

    Attributes:
        paper_id: Identifier of the classified paper
        status: Classification result ("kept" or "discarded")
        tags: Themes (kept) or motivations (discarded) assigned
        confidence: LLM's confidence in the decision (0.0-1.0)
        reasoning: Brief explanation of the classification
    """

    paper_id: str
    status: str  # "kept" or "discarded"
    tags: list[str]
    confidence: float
    reasoning: str


@dataclass
class LLMBatchResult:
    """
    Results from a batch LLM classification.

    Attributes:
        decisions: List of individual paper decisions
        model_id: Identifier of the LLM model used
        timestamp: When the classification was performed
        prompt_tokens: Optional token count for the prompt
        completion_tokens: Optional token count for the response
    """

    decisions: list[LLMDecision]
    model_id: str
    timestamp: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


def get_example_decisions(
    session: ReviewSession,
    max_kept: int = MAX_KEPT_EXAMPLES,
    max_discarded: int = MAX_DISCARDED_EXAMPLES,
) -> tuple[list[ReviewDecision], list[ReviewDecision]]:
    """
    Gather tagged examples from a review session.

    Prioritizes user-corrected LLM decisions (is_example=True) as these
    represent cases where the LLM's initial classification was wrong.

    Args:
        session: The review session to gather examples from
        max_kept: Maximum number of kept examples to include
        max_discarded: Maximum number of discarded examples to include

    Returns:
        Tuple of (kept_examples, discarded_examples)
    """
    kept_examples: list[ReviewDecision] = []
    discarded_examples: list[ReviewDecision] = []

    for decision in session.decisions:
        # Only include papers with tags (our example requirement)
        if not decision.tags:
            continue

        if decision.status == DecisionStatus.KEPT:
            kept_examples.append(decision)
        elif decision.status == DecisionStatus.DISCARDED:
            discarded_examples.append(decision)

    # Sort to prioritize corrected examples (is_example=True first)
    # Then by confidence (lower first, as these are harder cases)
    def sort_key(d: ReviewDecision) -> tuple[int, float]:
        # is_example=True should come first (0), then False (1)
        example_priority = 0 if d.is_example else 1
        # Lower confidence first (more informative examples)
        confidence = d.llm_confidence if d.llm_confidence is not None else 1.0
        return (example_priority, confidence)

    kept_examples.sort(key=sort_key)
    discarded_examples.sort(key=sort_key)

    # Limit to max and log selected examples
    kept_result = kept_examples[:max_kept]
    discarded_result = discarded_examples[:max_discarded]

    # Log info about selected examples
    if kept_result or discarded_result:
        logger.info(
            f"Selected {len(kept_result)} kept and "
            f"{len(discarded_result)} discarded examples for LLM"
        )
        for example in kept_result:
            logger.info(
                f"  KEPT example: {example.paper.title[:60]}... "
                f"[tags: {', '.join(example.tags)}]"
            )
        for example in discarded_result:
            logger.info(
                f"  DISCARDED example: {example.paper.title[:60]}... "
                f"[tags: {', '.join(example.tags)}]"
            )

    return kept_result, discarded_result


def validate_examples(
    kept_examples: list[ReviewDecision],
    discarded_examples: list[ReviewDecision],
    min_total: int = MIN_TOTAL_EXAMPLES,
    min_kept: int = MIN_KEPT_EXAMPLES,
    min_discarded: int = MIN_DISCARDED_EXAMPLES,
) -> tuple[bool, str]:
    """
    Check if examples meet minimum requirements for LLM classification.

    Args:
        kept_examples: List of kept paper examples
        discarded_examples: List of discarded paper examples
        min_total: Minimum total examples required
        min_kept: Minimum kept examples required
        min_discarded: Minimum discarded examples required

    Returns:
        Tuple of (is_valid, error_message)
        If valid, error_message is empty string.
    """
    total = len(kept_examples) + len(discarded_examples)

    if total < min_total:
        return False, (
            f"Need at least {min_total} tagged examples, "
            f"but only have {total}."
        )

    if len(kept_examples) < min_kept:
        return False, (
            f"Need at least {min_kept} kept example(s) with tags, "
            f"but only have {len(kept_examples)}."
        )

    if len(discarded_examples) < min_discarded:
        return False, (
            f"Need at least {min_discarded} discarded example(s) with tags, "
            f"but only have {len(discarded_examples)}."
        )

    return True, ""


def _format_paper_for_prompt(
    decision: ReviewDecision,
    include_abstract: bool = True,
) -> str:
    """
    Format a paper decision for inclusion in the prompt.

    Args:
        decision: The review decision containing the paper
        include_abstract: Whether to include the abstract

    Returns:
        Formatted string representation of the paper
    """
    paper = decision.paper
    lines = [
        f"Title: {paper.title}",
        f"Authors: {', '.join(paper.authors[:3])}"
        + (" et al." if len(paper.authors) > 3 else ""),
    ]

    if paper.year:
        lines.append(f"Year: {paper.year}")

    if paper.venue:
        lines.append(f"Venue: {paper.venue}")

    if include_abstract and paper.abstract:
        # Truncate very long abstracts
        abstract = paper.abstract
        if len(abstract) > 1000:
            abstract = abstract[:1000] + "..."
        lines.append(f"Abstract: {abstract}")

    lines.append(f"Tags: {', '.join(decision.tags)}")

    return "\n".join(lines)


def _format_paper_to_classify(
    decision: ReviewDecision,
    index: int,
) -> str:
    """
    Format a paper for classification request.

    Args:
        decision: The review decision containing the paper
        index: Zero-based index for reference in response

    Returns:
        Formatted string representation
    """
    paper = decision.paper
    lines = [
        f"[Paper {index}]",
        f"Title: {paper.title}",
        f"Authors: {', '.join(paper.authors[:3])}"
        + (" et al." if len(paper.authors) > 3 else ""),
    ]

    if paper.year:
        lines.append(f"Year: {paper.year}")

    if paper.venue:
        lines.append(f"Venue: {paper.venue}")

    if paper.abstract:
        abstract = paper.abstract
        if len(abstract) > 1000:
            abstract = abstract[:1000] + "..."
        lines.append(f"Abstract: {abstract}")
    else:
        lines.append("Abstract: [Not available]")

    return "\n".join(lines)


def _collect_available_tags(
    session: ReviewSession,
) -> tuple[set[str], set[str]]:
    """
    Collect all tags used in the session.

    Args:
        session: The review session

    Returns:
        Tuple of (themes_for_kept, motivations_for_discarded)
    """
    themes: set[str] = set()
    motivations: set[str] = set()

    for decision in session.decisions:
        if decision.status == DecisionStatus.KEPT:
            themes.update(decision.tags)
        elif decision.status == DecisionStatus.DISCARDED:
            motivations.update(decision.tags)

    return themes, motivations


def build_classification_prompt(
    papers_to_classify: list[ReviewDecision],
    kept_examples: list[ReviewDecision],
    discarded_examples: list[ReviewDecision],
    research_context: str | None = None,
    available_themes: set[str] | None = None,
    available_motivations: set[str] | None = None,
) -> str:
    """
    Construct the LLM prompt for paper classification.

    Args:
        papers_to_classify: Papers needing classification
        kept_examples: Example papers that were kept
        discarded_examples: Example papers that were discarded
        research_context: Description of the research focus
        available_themes: Tags used for kept papers
        available_motivations: Tags used for discarded papers

    Returns:
        Complete prompt string for the LLM
    """
    sections = []

    # Introduction
    sections.append(
        "You are helping with a systematic literature review. "
        "Your task is to classify papers as 'kept' (relevant to the review) "
        "or 'discarded' (not relevant)."
    )

    # Research context
    if research_context:
        sections.append(f"\n## Research Context\n\n{research_context}")

    # Available tags
    if available_themes:
        themes_list = ", ".join(sorted(available_themes))
        sections.append(
            f"\n## Available Themes (for kept papers)\n\n{themes_list}"
        )

    if available_motivations:
        motivations_list = ", ".join(sorted(available_motivations))
        sections.append(
            f"\n## Available Motivations (for discarded papers)\n\n"
            f"{motivations_list}"
        )

    # Kept examples
    if kept_examples:
        sections.append("\n## Examples of KEPT Papers\n")
        for example in kept_examples:
            sections.append(_format_paper_for_prompt(example))
            sections.append("")

    # Discarded examples
    if discarded_examples:
        sections.append("\n## Examples of DISCARDED Papers\n")
        for example in discarded_examples:
            sections.append(_format_paper_for_prompt(example))
            sections.append("")

    # Papers to classify
    sections.append("\n## Papers to Classify\n")
    for i, decision in enumerate(papers_to_classify):
        sections.append(_format_paper_to_classify(decision, i))
        sections.append("")

    # Instructions
    sections.append(
        """
## Instructions

For each paper above, classify it as 'kept' or 'discarded'.
Respond with a JSON object in exactly this format:

```json
{
  "classifications": [
    {
      "paper_index": 0,
      "decision": "kept",
      "tags": ["theme1", "theme2"],
      "confidence": 0.85,
      "reasoning": "Brief explanation of why this paper is relevant."
    },
    {
      "paper_index": 1,
      "decision": "discarded",
      "tags": ["motivation1"],
      "confidence": 0.90,
      "reasoning": "Brief explanation of why this paper is not relevant."
    }
  ]
}
```

Guidelines:
- Use existing themes/motivations when appropriate
- Create new tags only when existing ones don't fit
- Confidence should reflect how certain you are (0.0 to 1.0)
- Keep reasoning brief (1-2 sentences)
- Every discarded paper MUST have at least one motivation tag
"""
    )

    return "\n".join(sections)


def parse_llm_response(
    response_text: str,
    papers: list[ReviewDecision],
) -> list[LLMDecision]:
    """
    Parse JSON response from LLM into decisions.

    Args:
        response_text: Raw text response from LLM
        papers: The papers that were classified (for ID lookup)

    Returns:
        List of LLMDecision objects

    Raises:
        ValueError: If response cannot be parsed
    """
    from scholar.notes import get_paper_id

    # Extract JSON from response (may be wrapped in markdown code block)
    json_match = re.search(
        r"```(?:json)?\s*(\{.*?\})\s*```",
        response_text,
        re.DOTALL,
    )
    if json_match:
        json_str = json_match.group(1)
    else:
        # Try to find raw JSON
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            raise ValueError("No JSON found in LLM response")

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in LLM response: {e}")

    if "classifications" not in data:
        raise ValueError("Response missing 'classifications' key")

    decisions = []
    for item in data["classifications"]:
        paper_index = item.get("paper_index", 0)
        if paper_index < 0 or paper_index >= len(papers):
            logger.warning(f"Invalid paper_index {paper_index}, skipping")
            continue

        paper_decision = papers[paper_index]
        paper_id = get_paper_id(paper_decision.paper)

        # Validate status
        status = item.get("decision", "").lower()
        if status not in ("kept", "discarded"):
            logger.warning(f"Invalid decision '{status}', defaulting to kept")
            status = "kept"

        # Ensure tags are present
        tags = item.get("tags", [])
        if not isinstance(tags, list):
            tags = [str(tags)]

        # Validate confidence
        confidence = item.get("confidence", 0.5)
        try:
            confidence = float(confidence)
            confidence = max(0.0, min(1.0, confidence))
        except (TypeError, ValueError):
            confidence = 0.5

        decisions.append(
            LLMDecision(
                paper_id=paper_id,
                status=status,
                tags=tags,
                confidence=confidence,
                reasoning=item.get("reasoning", ""),
            )
        )

    return decisions


def get_papers_needing_enrichment(
    papers: list[ReviewDecision],
) -> list[Paper]:
    """
    Return papers that lack abstracts (required for LLM classification).

    Args:
        papers: List of review decisions to check

    Returns:
        List of Paper objects that need enrichment
    """
    return [
        decision.paper for decision in papers if not decision.paper.abstract
    ]


def classify_papers_with_llm(
    session: ReviewSession,
    count: int = DEFAULT_BATCH_SIZE,
    model_id: str | None = None,
    enrich_missing: bool = True,
    dry_run: bool = False,
    require_examples: bool = True,
) -> LLMBatchResult | str:
    """
    Classify pending papers using LLM.

    This is the main entry point for LLM-assisted classification. It:
    1. Optionally gathers training examples from human-reviewed papers
    2. Optionally validates minimum example requirements
    3. Optionally enriches papers lacking abstracts
    4. Constructs a prompt with examples and papers to classify
    5. Invokes the LLM and parses the response

    Args:
        session: The review session
        count: Number of papers to classify in this batch
        model_id: LLM model to use (uses llm default if None)
        enrich_missing: Whether to auto-enrich papers without abstracts
        dry_run: If True, return the prompt without calling LLM
        require_examples: If True (default), require tagged example papers
            before classification. Set False for zero-shot classification
            using only the research context.

    Returns:
        LLMBatchResult with decisions, or prompt string if dry_run=True

    Raises:
        ValueError: If there are no papers to classify, or if
            require_examples=True and there are insufficient examples
        ImportError: If llm package is not installed
    """
    # Gather examples (optional)
    if require_examples:
        kept_examples, discarded_examples = get_example_decisions(session)

        # Validate
        is_valid, error = validate_examples(kept_examples, discarded_examples)
        if not is_valid:
            raise ValueError(error)
    else:
        kept_examples = []
        discarded_examples = []

    # Get pending papers
    pending = [
        d for d in session.decisions if d.status == DecisionStatus.PENDING
    ]

    if not pending:
        raise ValueError("No pending papers to classify")

    # Limit to requested count
    to_classify = pending[:count]

    # Check for papers needing enrichment
    if enrich_missing:
        needing_enrichment = get_papers_needing_enrichment(to_classify)
        if needing_enrichment:
            try:
                from scholar.enrich import enrich_papers

                logger.info(
                    f"Enriching {len(needing_enrichment)} papers "
                    "before classification"
                )
                enrich_papers(needing_enrichment)
            except ImportError:
                logger.warning(
                    "Enrich module not available, "
                    "some papers may lack abstracts"
                )

    # Collect available tags
    themes, motivations = _collect_available_tags(session)

    # Build prompt
    prompt = build_classification_prompt(
        papers_to_classify=to_classify,
        kept_examples=kept_examples,
        discarded_examples=discarded_examples,
        research_context=session.research_context,
        available_themes=themes,
        available_motivations=motivations,
    )

    if dry_run:
        return prompt

    # Import llm and call
    try:
        import llm
    except ImportError:
        raise ImportError(
            "The 'llm' package is required for LLM classification. "
            "Install it with: pip install llm"
        )

    model = llm.get_model(model_id) if model_id else llm.get_model()
    logger.info(
        f"Classifying {len(to_classify)} papers with {model.model_id}"
    )

    # Log papers being sent for classification
    logger.info("Papers to classify:")
    for i, decision in enumerate(to_classify):
        abstract_status = (
            "with abstract" if decision.paper.abstract else "NO ABSTRACT"
        )
        logger.info(
            f"  [{i}] {decision.paper.title[:50]}... ({abstract_status})"
        )

    response = model.prompt(prompt)
    response_text = response.text()

    # Parse response
    decisions = parse_llm_response(response_text, to_classify)

    return LLMBatchResult(
        decisions=decisions,
        model_id=model.model_id,
        timestamp=datetime.now().isoformat(),
        prompt_tokens=getattr(response, "prompt_tokens", None),
        completion_tokens=getattr(response, "completion_tokens", None),
    )


def _build_paper_id_lookup(
    session: ReviewSession,
) -> dict[str, ReviewDecision]:
    """Build a lookup dict from paper_id to decision."""
    from scholar.notes import get_paper_id

    return {get_paper_id(d.paper): d for d in session.decisions}


def apply_llm_decisions(
    session: ReviewSession,
    batch_result: LLMBatchResult,
) -> list[ReviewDecision]:
    """
    Apply LLM decisions to session, marking as LLM_UNREVIEWED.

    Args:
        session: The review session to update
        batch_result: Results from LLM classification

    Returns:
        List of ReviewDecision objects that were updated
    """
    updated = []

    # Build lookup for efficient paper_id matching
    paper_id_lookup = _build_paper_id_lookup(session)

    logger.info(
        f"Applying LLM decisions for {len(batch_result.decisions)} papers"
    )

    for llm_decision in batch_result.decisions:
        if llm_decision.paper_id not in paper_id_lookup:
            logger.warning(
                f"Paper {llm_decision.paper_id} not in session, skipping"
            )
            continue

        decision = paper_id_lookup[llm_decision.paper_id]

        # Only update pending papers
        if decision.status != DecisionStatus.PENDING:
            logger.debug(
                f"Paper {llm_decision.paper_id} already decided, skipping"
            )
            continue

        # Apply LLM decision
        decision.status = (
            DecisionStatus.KEPT
            if llm_decision.status == "kept"
            else DecisionStatus.DISCARDED
        )
        decision.tags = llm_decision.tags
        decision.source = ReviewSource.LLM_UNREVIEWED
        decision.llm_confidence = llm_decision.confidence
        decision.is_example = False  # Not an example until user reviews

        # Log info about each paper's review outcome
        status_str = "KEPT" if llm_decision.status == "kept" else "DISCARDED"
        logger.info(
            f"  {status_str} (conf={llm_decision.confidence:.2f}): "
            f"{decision.paper.title[:50]}..."
        )
        logger.info(f"    Tags: {', '.join(llm_decision.tags)}")
        if llm_decision.reasoning:
            logger.info(f"    Reason: {llm_decision.reasoning[:80]}...")

        updated.append(decision)

    logger.info(f"Applied LLM decisions to {len(updated)} papers")
    return updated


def mark_as_reviewed(
    decision: ReviewDecision,
    user_agrees: bool,
    new_status: DecisionStatus | None = None,
    new_tags: list[str] | None = None,
) -> None:
    """
    Mark an LLM decision as reviewed by user.

    If the user changed the decision (disagrees), the paper becomes a
    training example for future LLM rounds.

    Args:
        decision: The decision to mark as reviewed
        user_agrees: Whether user agrees with LLM classification
        new_status: New status if user disagrees (ignored if agrees)
        new_tags: New tags if user disagrees (ignored if agrees)
    """
    if decision.source != ReviewSource.LLM_UNREVIEWED:
        logger.warning("Decision is not LLM_UNREVIEWED, nothing to mark")
        return

    decision.source = ReviewSource.LLM_REVIEWED

    if not user_agrees:
        # User corrected the LLM - this becomes an example
        decision.is_example = True

        if new_status is not None:
            decision.status = new_status

        if new_tags is not None:
            decision.tags = new_tags


def get_unreviewed_llm_decisions(
    session: ReviewSession,
    sort_by_confidence: bool = True,
) -> list[ReviewDecision]:
    """
    Get LLM decisions that haven't been reviewed by user.

    Args:
        session: The review session
        sort_by_confidence: If True, sort by confidence (lowest first)
            so users review uncertain decisions first

    Returns:
        List of ReviewDecision objects pending user review
    """
    unreviewed = [
        d
        for d in session.decisions
        if d.source == ReviewSource.LLM_UNREVIEWED
    ]

    if sort_by_confidence:
        # Sort by confidence, lowest first (most uncertain)
        unreviewed.sort(
            key=lambda d: d.llm_confidence if d.llm_confidence else 0.5
        )

    return unreviewed


def get_review_statistics(session: ReviewSession) -> dict[str, int]:
    """
    Get counts of decisions by source and status.

    Args:
        session: The review session

    Returns:
        Dictionary with counts:
        - human: Decisions made by human directly
        - llm_unreviewed: LLM decisions pending review
        - llm_reviewed: LLM decisions reviewed by user
        - examples: Papers marked as training examples
        - pending: Papers not yet decided
        - total: Total papers in session
    """
    stats = {
        "human": 0,
        "llm_unreviewed": 0,
        "llm_reviewed": 0,
        "examples": 0,
        "pending": 0,
        "total": len(session.decisions),
    }

    for decision in session.decisions:
        if decision.status == DecisionStatus.PENDING:
            stats["pending"] += 1
        elif decision.source == ReviewSource.HUMAN:
            stats["human"] += 1
        elif decision.source == ReviewSource.LLM_UNREVIEWED:
            stats["llm_unreviewed"] += 1
        elif decision.source == ReviewSource.LLM_REVIEWED:
            stats["llm_reviewed"] += 1

        if decision.is_example:
            stats["examples"] += 1

    return stats


SYNTHESIS_SECTION_START = "===SECTION_START==="
SYNTHESIS_SECTION_END = "===SECTION_END==="
SYNTHESIS_SUMMARY_START = "===SUMMARY_START==="
SYNTHESIS_SUMMARY_END = "===SUMMARY_END==="

SYNTHESIS_CACHE_VERSION = "v4"
SYNTHESIS_THEME_CACHE = load_cache("llm_synthesis_theme")
SYNTHESIS_CONCLUSION_CACHE = load_cache("llm_synthesis_conclusion")
register_cache("llm_synthesis_theme", SYNTHESIS_THEME_CACHE)
register_cache("llm_synthesis_conclusion", SYNTHESIS_CONCLUSION_CACHE)


@dataclass
class ThemeSectionResult:
    """
    Result from generating one theme section of a synthesis.

    Attributes:
        theme: Theme name, or None for an unthemed synthesis
        title: LLM-generated human-readable section title
        section: Generated section text (Markdown or LaTeX fragment)
        summary: Short summary used as input to the conclusion round
        subquestions: Sub-questions answered by this section
        abstract: One-paragraph section abstract, for report abstracts
        paper_count: Number of papers included in this section
    """

    theme: str | None
    title: str
    section: str
    summary: str
    subquestions: list[str] = field(default_factory=list)
    abstract: str = ""
    paper_count: int = 0


@dataclass
class SynthesisResult:
    """
    Result from literature synthesis generation.

    Attributes:
        synthesis: The assembled synthesis document
        model_id: Identifier of the LLM model used
        timestamp: When the synthesis was generated
        paper_count: Number of papers included in synthesis
        themes: Themes used to organize the synthesis
        references: Paper metadata used to build the bibliography
        theme_sections: Generated theme sections from multi-round synthesis
        conclusion: Generated conclusion text (without heading)
    """

    synthesis: str
    model_id: str
    timestamp: str
    paper_count: int
    themes: list[str]
    references: list[dict[str, Any]]
    theme_sections: list[ThemeSectionResult] = field(default_factory=list)
    conclusion: str = ""


def _get_author_surname(author: str) -> str:
    """
    Extract surname from author name.

    Handles formats like "John Smith", "Smith, John", "J. Smith".
    """
    author = author.strip()
    if "," in author:
        # "Smith, John" format
        return author.split(",")[0].strip()
    parts = author.split()
    if parts:
        # "John Smith" or "J. Smith" - take last part
        return parts[-1]
    return author


def _generate_citation_key(
    paper: Paper,
    output_format: str = "markdown",
) -> tuple[str, str]:
    """
    Generate citation key for a paper.

    Args:
        paper: The paper to generate a key for
        output_format: "markdown" for [Author, Year] or "latex" for cite key

    Returns:
        Tuple of (display_key, bibtex_key)
        - display_key: "[Smith, 2024]" for markdown, "smith2024" for latex
        - bibtex_key: Always "smith2024" style for reference list
    """
    # Get first author surname
    if paper.authors:
        first_surname = _get_author_surname(paper.authors[0])
    else:
        first_surname = "Unknown"

    year = paper.year or "n.d."

    # Generate BibTeX-style key (always needed for reference list)
    bibtex_key = f"{first_surname.lower()}{year}".replace(" ", "")

    if output_format == "latex":
        display_key = bibtex_key
    else:
        # Author-year display format
        if len(paper.authors) == 1:
            display_key = f"[{first_surname}, {year}]"
        elif len(paper.authors) == 2:
            second_surname = _get_author_surname(paper.authors[1])
            display_key = f"[{first_surname} \\& {second_surname}, {year}]"
        else:
            display_key = f"[{first_surname} et al., {year}]"

    return display_key, bibtex_key


def _generate_all_citation_keys(
    decisions: list[ReviewDecision],
    output_format: str = "markdown",
) -> dict[str, tuple[str, str]]:
    """
    Generate citation keys for all papers.

    Args:
        decisions: List of kept paper decisions
        output_format: "markdown" or "latex"

    Returns:
        Dict mapping paper_id to (display_key, bibtex_key)
    """
    from scholar.notes import get_paper_id

    keys: dict[str, tuple[str, str]] = {}
    seen_bibtex: dict[str, int] = {}

    for decision in decisions:
        paper_id = get_paper_id(decision.paper)
        display_key, bibtex_key = _generate_citation_key(
            decision.paper, output_format
        )

        # Handle duplicate BibTeX keys by adding suffix
        if bibtex_key in seen_bibtex:
            seen_bibtex[bibtex_key] += 1
            suffix = chr(ord("a") + seen_bibtex[bibtex_key] - 1)
            bibtex_key = f"{bibtex_key}{suffix}"
            if output_format == "latex":
                display_key = bibtex_key
            else:
                # Add suffix to display key too
                display_key = display_key[:-1] + suffix + "]"
        else:
            seen_bibtex[bibtex_key] = 1

        keys[paper_id] = (display_key, bibtex_key)

    return keys


def _decision_cache_fingerprint(decision: ReviewDecision) -> dict[str, Any]:
    """Return a deterministic fingerprint for cache invalidation."""
    from scholar.notes import get_paper_id

    paper_id = get_paper_id(decision.paper)
    return {
        "paper_id": paper_id,
        "paper": _paper_cache_fingerprint(decision.paper),
        "tags": sorted(decision.tags),
    }


def _hash_cache_payload(payload: dict[str, Any]) -> str:
    """Hash a JSON payload into a stable cache key."""
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _theme_cache_key(
    *,
    theme: str | None,
    decisions: list[ReviewDecision],
    research_context: str,
    model_id: str,
    output_format: str,
) -> str:
    fingerprints = [_decision_cache_fingerprint(d) for d in decisions]
    fingerprints.sort(key=lambda d: d["paper_id"])

    payload = {
        "version": SYNTHESIS_CACHE_VERSION,
        "kind": "theme",
        "theme": theme,
        "research_context": research_context,
        "model_id": model_id,
        "output_format": output_format,
        "papers": fingerprints,
    }
    return _hash_cache_payload(payload)


def _conclusion_cache_key(
    *,
    theme_sections: list[ThemeSectionResult],
    theme_cache_keys: list[str],
    research_context: str,
    model_id: str,
    output_format: str,
) -> str:
    summaries = [
        {
            "theme": section.theme,
            "summary": section.summary,
        }
        for section in theme_sections
    ]

    payload = {
        "version": SYNTHESIS_CACHE_VERSION,
        "kind": "conclusion",
        "research_context": research_context,
        "model_id": model_id,
        "output_format": output_format,
        "theme_cache_keys": theme_cache_keys,
        "theme_summaries": summaries,
    }
    return _hash_cache_payload(payload)


def _paper_cache_fingerprint(paper: Paper) -> dict[str, Any]:
    """Return a deterministic JSON-serializable paper fingerprint."""
    return {
        "title": paper.title or "",
        "authors": paper.authors or [],
        "year": paper.year or "",
        "abstract": paper.abstract or "",
        "venue": paper.venue or "",
        "doi": paper.doi or "",
        "url": paper.url or "",
    }


def _format_paper_for_synthesis(
    decision: ReviewDecision,
    citation_key: str,
    bibtex_key: str,
) -> str:
    """
    Format a kept paper for inclusion in synthesis prompt.

    Args:
        decision: The review decision containing the paper
        citation_key: Display citation key (e.g., "[Smith, 2024]")
        bibtex_key: BibTeX key (e.g., "smith2024")

    Returns:
        Formatted string representation
    """
    paper = decision.paper
    lines = [
        f"### {citation_key} (key: {bibtex_key})",
        f"**Title:** {paper.title}",
    ]

    if paper.authors:
        author_str = ", ".join(paper.authors[:5])
        if len(paper.authors) > 5:
            author_str += " et al."
        lines.append(f"**Authors:** {author_str}")

    if paper.year:
        lines.append(f"**Year:** {paper.year}")

    if paper.venue:
        lines.append(f"**Venue:** {paper.venue}")

    if decision.tags:
        lines.append(f"**Themes:** {', '.join(decision.tags)}")

    if paper.abstract:
        abstract = paper.abstract
        if len(abstract) > 1500:
            abstract = abstract[:1500] + "..."
        lines.append(f"**Abstract:** {abstract}")
    else:
        lines.append("**Abstract:** [Not available]")

    return "\n".join(lines)


def _extract_marked_block(
    text: str,
    start_marker: str,
    end_marker: str,
) -> str | None:
    """Return the text between two markers, or None if not present."""
    start_index = text.find(start_marker)
    end_index = text.find(end_marker)
    if start_index == -1 or end_index == -1 or end_index < start_index:
        return None
    start_index += len(start_marker)
    return text[start_index:end_index].strip()


def _fallback_summary(
    text: str,
    max_sentences: int = 3,
    max_chars: int = 600,
) -> str:
    """Create a small summary if the LLM omitted summary markers."""
    flattened = re.sub(r"\s+", " ", text.strip())
    sentences = re.split(r"(?<=[.!?])\s+", flattened)
    summary = " ".join(sentences[:max_sentences]).strip()
    if len(summary) > max_chars:
        summary = summary[:max_chars].rstrip() + "..."
    return summary


def _strip_conclusion_heading(text: str, output_format: str) -> str:
    """Strip a Conclusion heading if the model included one."""
    lines = text.strip().splitlines()
    if not lines:
        return ""

    first = lines[0].strip()
    if output_format == "latex":
        if first.startswith("\\section{Conclusion}") or first.startswith(
            "\\subsection{Conclusion}"
        ):
            return "\n".join(lines[1:]).lstrip()
    else:
        if first.lower().startswith("## conclusion"):
            return "\n".join(lines[1:]).lstrip()

    return text.strip()


def _ensure_theme_heading(
    text: str,
    title: str,
    output_format: str,
) -> str:
    """Ensure the section starts with a heading using the given title."""
    stripped = text.lstrip()
    if output_format == "latex":
        if stripped.startswith("\\subsection"):
            return text.strip()
        return f"\\subsection{{{title}}}\n" + text.strip()

    if stripped.startswith("###"):
        return text.strip()
    return f"### {title}\n\n" + text.strip()


def _replace_theme_heading(
    text: str,
    title: str,
    output_format: str,
) -> str:
    """Replace the first heading with the given title, or insert one."""
    stripped = text.lstrip()
    if not stripped:
        return _ensure_theme_heading(text, title, output_format)

    lines = stripped.splitlines()
    if output_format == "latex":
        if lines and lines[0].startswith("\\subsection{"):
            lines[0] = f"\\subsection{{{title}}}"
            return "\n".join(lines).strip()
        return _ensure_theme_heading(stripped, title, output_format)

    if lines and lines[0].startswith("###"):
        lines[0] = f"### {title}"
        return "\n".join(lines).strip()
    return _ensure_theme_heading(stripped, title, output_format)


SYNTHESIS_TITLE_START = "===TITLE_START==="
SYNTHESIS_TITLE_END = "===TITLE_END==="
SYNTHESIS_SUBQUESTIONS_START = "===SUBQUESTIONS_START==="
SYNTHESIS_SUBQUESTIONS_END = "===SUBQUESTIONS_END==="
SYNTHESIS_SECTION_ABSTRACT_START = "===SECTION_ABSTRACT_START==="
SYNTHESIS_SECTION_ABSTRACT_END = "===SECTION_ABSTRACT_END==="


def _parse_subquestions(text: str | None) -> list[str]:
    if not text:
        return []
    lines = []
    for raw in text.splitlines():
        stripped = raw.strip()
        stripped = stripped.lstrip("-*").strip()
        if stripped:
            lines.append(stripped)
    return lines


def title_needs_improvement(theme: str | None, title: str) -> bool:
    """Heuristic: did the model just repeat the theme tag as title?"""
    if theme is None:
        return False

    theme_norm = re.sub(r"\s+", " ", theme.strip().lower())
    title_norm = re.sub(r"\s+", " ", title.strip().lower())
    if not title_norm:
        return True

    if title_norm == theme_norm:
        return True

    # Common minimal variations that still indicate no real improvement.
    if title_norm.replace("-", " ") == theme_norm.replace("-", " "):
        return True

    return False


def build_title_from_abstract_prompt(
    theme: str,
    section_abstract: str,
    output_format: str,
) -> str:
    """Ask the LLM for a better title if the theme title was not improved."""
    return (
        "You are a research assistant improving section titles in a literature "
        "synthesis report.\n\n"
        f"Theme keyword: {theme}\n\n"
        "Section abstract:\n"
        f"{section_abstract}\n\n"
        "Instructions:\n"
        "- Propose a concise, descriptive section title (max 10 words).\n"
        "- Do not include citations.\n"
        "- Do not include punctuation at the end.\n\n"
        "Return the title in this marked block:\n\n"
        f"{SYNTHESIS_TITLE_START}\n"
        "<title>\n"
        f"{SYNTHESIS_TITLE_END}\n"
    )


def parse_theme_section_response(
    response_text: str,
    theme: str | None,
    output_format: str,
    paper_count: int,
) -> ThemeSectionResult:
    """Parse an LLM theme section response into section + metadata."""
    section = _extract_marked_block(
        response_text, SYNTHESIS_SECTION_START, SYNTHESIS_SECTION_END
    )
    if section is None:
        section = response_text.strip()

    summary = _extract_marked_block(
        response_text, SYNTHESIS_SUMMARY_START, SYNTHESIS_SUMMARY_END
    )
    if not summary:
        summary = _fallback_summary(section)

    title = _extract_marked_block(
        response_text, SYNTHESIS_TITLE_START, SYNTHESIS_TITLE_END
    )
    if not title:
        title = theme or "Synthesis"

    section_abstract = _extract_marked_block(
        response_text,
        SYNTHESIS_SECTION_ABSTRACT_START,
        SYNTHESIS_SECTION_ABSTRACT_END,
    )
    if not section_abstract:
        section_abstract = _fallback_summary(
            summary, max_sentences=2, max_chars=400
        )

    subquestions_text = _extract_marked_block(
        response_text,
        SYNTHESIS_SUBQUESTIONS_START,
        SYNTHESIS_SUBQUESTIONS_END,
    )
    subquestions = _parse_subquestions(subquestions_text)

    if theme is not None:
        section = _ensure_theme_heading(section, title, output_format)

    return ThemeSectionResult(
        theme=theme,
        title=title,
        section=section,
        summary=summary,
        subquestions=subquestions,
        abstract=section_abstract,
        paper_count=paper_count,
    )


def _group_kept_papers_by_theme(
    kept_decisions: list[ReviewDecision],
) -> tuple[list[str], dict[str | None, list[ReviewDecision]]]:
    """Group kept papers by theme; returns (themes, groups)."""
    themes = sorted({tag for d in kept_decisions for tag in d.tags})
    if not themes:
        return [], {None: kept_decisions}

    groups: dict[str | None, list[ReviewDecision]] = {}
    for theme in themes:
        groups[theme] = [d for d in kept_decisions if theme in d.tags]
    return themes, groups


def build_theme_section_prompt(
    theme: str | None,
    kept_decisions: list[ReviewDecision],
    research_context: str,
    citation_keys: dict[str, tuple[str, str]],
    output_format: str = "markdown",
) -> str:
    """Construct a prompt for a single theme (or unthemed) synthesis section."""
    from scholar.notes import get_paper_id

    sections: list[str] = []
    sections.append(
        "You are a research assistant writing part of a literature synthesis "
        "for a systematic review. Write only the requested synthesis text, "
        "grounded strictly in the provided papers."
    )
    sections.append(f"\n## Research Question\n\n{research_context}")

    if theme is None:
        sections.append(
            "\n## Synthesis Focus\n\n"
            "Write the body text for the Synthesis section. Do not add any "
            "theme heading."
        )
    else:
        sections.append(
            "\n## Theme Focus\n\n"
            f"Write a focused synthesis for the theme: {theme}."
        )

    sections.append(
        f"\n## Papers for This Round ({len(kept_decisions)} total)\n"
    )
    for decision in kept_decisions:
        paper_id = get_paper_id(decision.paper)
        display_key, bibtex_key = citation_keys[paper_id]
        sections.append(
            _format_paper_for_synthesis(decision, display_key, bibtex_key)
        )
        sections.append("")

    if output_format == "latex":
        cite_instruction = (
            "Use biblatex citation commands like \\textcite{key}, \\parencite{key}, "
            "or \\autocite{key} (e.g., \\textcite{smith2024})."
        )
        format_note = "Output must be a valid LaTeX fragment (no preamble)."
        if theme is None:
            heading_requirement = (
                "Do not include any \\section or \\subsection heading."
            )
            heading_example = ""
        else:
            heading_requirement = "Start the section block with this exact heading on a single line:"
            heading_example = f"```latex\n\\subsection{{{theme}}}\n```"
    else:
        cite_instruction = (
            "Use [Author, Year] format for citations (e.g., [Smith, 2024])."
        )
        format_note = "Output must be Markdown format."
        if theme is None:
            heading_requirement = "Do not include a theme heading."
            heading_example = ""
        else:
            heading_requirement = "Start the section block with this exact heading on a single line:"
            heading_example = f"```markdown\n### {theme}\n```"

    sections.append(
        f"""
## Instructions

Write a synthesis section that:

1. **Stays focused** - Use only the papers provided for this round.
2. **Synthesizes, don't summarize** - Draw connections and compare approaches.
3. **Uses proper citations** - {cite_instruction} Every substantive claim must cite.
4. **No references section** - Do not add a reference list.

### Heading Requirement

{heading_requirement}
{heading_example}

Return your answer in four marked blocks exactly as follows:

{SYNTHESIS_TITLE_START}
<short section title derived from your summary>
{SYNTHESIS_TITLE_END}

{SYNTHESIS_SUBQUESTIONS_START}
- <subresearch question 1 answered by this section>
- <subresearch question 2 answered by this section>
{SYNTHESIS_SUBQUESTIONS_END}

{SYNTHESIS_SECTION_ABSTRACT_START}
<one paragraph that can be used in the report abstract>
{SYNTHESIS_SECTION_ABSTRACT_END}

{SYNTHESIS_SECTION_START}
<your synthesis text>
{SYNTHESIS_SECTION_END}

{SYNTHESIS_SUMMARY_START}
<2--4 sentence summary for the conclusion round, including citations>
{SYNTHESIS_SUMMARY_END}

{format_note}
"""
    )

    return "\n".join(sections)


def build_conclusion_prompt(
    research_context: str,
    theme_sections: list[ThemeSectionResult],
    output_format: str = "markdown",
) -> str:
    """Construct a prompt for the final conclusion round."""
    sections: list[str] = []
    sections.append(
        "You are a research assistant writing the conclusion of a literature "
        "synthesis for a systematic review."
    )
    sections.append(f"\n## Research Question\n\n{research_context}")

    sections.append("\n## Theme Summaries\n")
    for section in theme_sections:
        label = section.theme if section.theme is not None else "Synthesis"
        sections.append(f"### {label}\n{section.summary}\n")

    if output_format == "latex":
        cite_instruction = (
            "Use biblatex citation commands like \\textcite{key}, \\parencite{key}, "
            "or \\autocite{key} (e.g., \\textcite{smith2024})."
        )
        format_note = "Output must be a valid LaTeX fragment (no preamble)."
    else:
        cite_instruction = (
            "Use [Author, Year] format for citations (e.g., [Smith, 2024])."
        )
        format_note = "Output must be Markdown format."

    sections.append(
        f"""
## Instructions

Write a conclusion that:

1. **Connects to the research question** - Answer it based on the synthesis.
2. **Connects across themes** - Compare, contrast, and relate the themes.
3. **Identifies gaps** - Note limitations and open questions.
4. **Uses citations** - {cite_instruction}
5. **No headings** - Do not include a \"Conclusion\" heading.
6. **No references section** - Do not add a reference list.

Return your answer in a marked block exactly as follows:

{SYNTHESIS_SECTION_START}
<your conclusion text>
{SYNTHESIS_SECTION_END}

{format_note}
"""
    )

    return "\n".join(sections)


SYNTHESIS_REPORT_ABSTRACT_START = "===REPORT_ABSTRACT_START==="
SYNTHESIS_REPORT_ABSTRACT_END = "===REPORT_ABSTRACT_END==="


def build_synthesis_abstract_prompt(
    research_context: str,
    theme_sections: list[ThemeSectionResult],
    conclusion: str,
    output_format: str,
) -> str:
    """Build a prompt for generating an overall report abstract."""
    lines: list[str] = []
    lines.append(
        "You are a research assistant writing the abstract for a literature "
        "synthesis report."
    )
    lines.append(f"\n## Research Question\n\n{research_context}")

    lines.append("\n## Section Abstracts\n")
    for section in theme_sections:
        if section.abstract:
            lines.append(f"- {section.abstract}")

    lines.append("\n## Conclusion\n")
    lines.append(conclusion)

    lines.append(
        f"""
## Instructions

Write one paragraph suitable as a report abstract.
It should summarize the synthesis at a high level, grounded in the research
question, the section abstracts, and the conclusion.
Do not include citations.

Return your answer as a marked block exactly as follows:

{SYNTHESIS_REPORT_ABSTRACT_START}
<one paragraph abstract>
{SYNTHESIS_REPORT_ABSTRACT_END}
"""
    )

    return "\n".join(lines)


def parse_report_abstract(response_text: str) -> str:
    abstract = _extract_marked_block(
        response_text,
        SYNTHESIS_REPORT_ABSTRACT_START,
        SYNTHESIS_REPORT_ABSTRACT_END,
    )
    if abstract is None:
        abstract = response_text.strip()
    return re.sub(r"\s+", " ", abstract).strip()


def build_research_question_section_markdown(
    session: ReviewSession,
    included_kept_papers: int,
    total_kept_papers: int,
) -> str:
    """Build the provenance section for Markdown output."""
    from scholar.review import (
        build_research_context_markdown,
        build_search_parameters_markdown,
    )

    lines: list[str] = ["## Research Question", ""]

    # Put research context first.
    lines.extend(build_research_context_markdown(session, heading_level=3))
    lines.extend(build_search_parameters_markdown(session, heading_level=3))

    lines.extend(["### Summary", ""])
    lines.append(f"- Date: {session.timestamp.strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"- Total Papers: {len(session.decisions)}")
    lines.append(f"- Kept: {len(session.kept_papers)}")
    lines.append(f"- Discarded: {len(session.discarded_papers)}")
    lines.append(f"- Pending: {len(session.pending_papers)}")
    if included_kept_papers != total_kept_papers:
        lines.append(
            f"- Included kept papers: {included_kept_papers}/{total_kept_papers} "
            "(due to --max-papers)"
        )
    lines.append("")

    if session.snowball_rounds:
        lines.extend(["### Snowballing", ""])
        lines.append("| Round | Direction | Papers Added | Source Papers |")
        lines.append("| --- | --- | --- | --- |")
        for i, round_info in enumerate(session.snowball_rounds, 1):
            direction = (
                "References"
                if round_info.direction == "references"
                else "Citations"
            )
            source_label = f"{len(round_info.source_papers)}"
            lines.append(
                f"| {i} | {direction} | {round_info.papers_added} | {source_label} |"
            )
        lines.append("")

    return "\n".join(lines)


def build_research_question_section_latex(
    session: ReviewSession,
    included_kept_papers: int,
    total_kept_papers: int,
) -> str:
    """Build the provenance section for LaTeX output."""
    from scholar.review import (
        build_research_context_latex,
        build_search_parameters_latex,
    )

    lines: list[str] = [r"\section{Research Question}", ""]

    # Put research context first.
    lines.extend(
        build_research_context_latex(session, heading_command=r"\subsection")
    )
    lines.extend(
        build_search_parameters_latex(session, heading_command=r"\subsection")
    )

    lines.extend([r"\subsection{Summary}", ""])
    lines.extend(
        [
            r"\begin{description}",
            f"\\item[Date] {session.timestamp.strftime('%Y-%m-%d %H:%M')}",
            f"\\item[Total Papers] {len(session.decisions)}",
            f"\\item[Kept] {len(session.kept_papers)}",
            f"\\item[Discarded] {len(session.discarded_papers)}",
            f"\\item[Pending] {len(session.pending_papers)}",
        ]
    )
    if included_kept_papers != total_kept_papers:
        lines.append(
            f"\\item[Included kept papers] {included_kept_papers}/{total_kept_papers}"
        )
    lines.extend([r"\end{description}", ""])

    if session.snowball_rounds:
        lines.extend([r"\subsection{Snowballing}", ""])
        lines.extend(
            [
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
        lines.extend([r"\bottomrule", r"\end{longtable}", ""])

    return "\n".join(lines)


def _build_references_markdown(
    kept_decisions: list[ReviewDecision],
    citation_keys: dict[str, tuple[str, str]],
) -> str:
    """Build a deterministic reference list in Markdown."""
    from scholar.notes import get_paper_id

    lines: list[str] = []
    for decision in kept_decisions:
        paper = decision.paper
        paper_id = get_paper_id(paper)
        display_key, _ = citation_keys[paper_id]

        authors = ", ".join(paper.authors[:5]) if paper.authors else ""
        if paper.authors and len(paper.authors) > 5:
            authors += " et al."
        year = paper.year or "n.d."
        venue = paper.venue or ""

        entry = f"{display_key} {paper.title} ({year}). {authors}. {venue}."
        if paper.doi:
            entry += f" DOI: {paper.doi}."
        if paper.url:
            entry += f" URL: {paper.url}."
        lines.append(f"- {entry}")

    return "\n".join(lines)


def _format_bibtex_entry(paper: Paper, cite_key: str) -> str:
    """Format a paper as a BibTeX entry."""
    from scholar.review import escape_bibtex

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


def _build_bibtex_content(
    kept_decisions: list[ReviewDecision],
    citation_keys: dict[str, tuple[str, str]],
) -> str:
    """Build BibTeX content for the included kept papers."""
    from scholar.notes import get_paper_id

    entries: list[str] = []
    for decision in kept_decisions:
        paper_id = get_paper_id(decision.paper)
        _, bibtex_key = citation_keys[paper_id]
        entries.append(_format_bibtex_entry(decision.paper, bibtex_key))

    return "\n\n".join(entries)


def _assemble_markdown_synthesis(
    session: ReviewSession,
    theme_sections: list[ThemeSectionResult],
    conclusion: str,
    references_markdown: str,
    included_kept_papers: int,
    total_kept_papers: int,
) -> str:
    parts: list[str] = []
    parts.append(
        build_research_question_section_markdown(
            session,
            included_kept_papers=included_kept_papers,
            total_kept_papers=total_kept_papers,
        )
    )

    parts.append("## Synthesis\n")
    for section in theme_sections:
        parts.append(section.section.strip())
        parts.append("")

    parts.append("## Conclusion\n")
    parts.append(conclusion.strip())
    parts.append("")

    parts.append("## References\n")
    parts.append(references_markdown.strip())

    return "\n".join(parts).strip() + "\n"


def _assemble_latex_synthesis(
    session: ReviewSession,
    theme_sections: list[ThemeSectionResult],
    conclusion: str,
    bibtex_content: str,
    included_kept_papers: int,
    total_kept_papers: int,
    report_abstract: str,
) -> str:
    """Assemble a complete LaTeX synthesis document."""
    lines: list[str] = []

    # BibTeX file embedded into the generated LaTeX.
    lines.extend(
        [
            r"\begin{filecontents*}{synthesis.bib}",
            bibtex_content,
            r"\end{filecontents*}",
            "",
        ]
    )

    lines.extend(
        [
            r"\documentclass{article}",
            r"\usepackage[utf8]{inputenc}",
            r"\usepackage[colorlinks=true,allcolors=blue]{hyperref}",
            r"\usepackage{enumitem}",
            r"\usepackage{longtable}",
            r"\usepackage{booktabs}",
            r"\usepackage{array}",
            r"\usepackage[backend=biber,style=authoryear]{biblatex}",
            r"\addbibresource{synthesis.bib}",
            "",
            f"\\title{{{session.name or session.query}}}",
            f"\\date{{{session.timestamp.strftime('%Y-%m-%d')}}}",
            "",
            r"\begin{document}",
            r"\maketitle",
            "",
            r"\begin{abstract}",
            report_abstract,
            r"\end{abstract}",
            r"\clearpage",
            r"\clearpage",
            r"\tableofcontents",
            r"\clearpage",
            "",
        ]
    )

    lines.append(
        build_research_question_section_latex(
            session,
            included_kept_papers=included_kept_papers,
            total_kept_papers=total_kept_papers,
        )
    )
    lines.append("")

    lines.extend([r"\section{Synthesis}", ""])
    for section in theme_sections:
        lines.append(section.section.strip())
        lines.append("")

    lines.extend([r"\section{Conclusion}", ""])
    lines.append(conclusion.strip())
    lines.append("")

    lines.extend([r"\printbibliography", r"\end{document}"])

    return "\n".join(lines).strip() + "\n"


def generate_literature_synthesis(
    session: ReviewSession,
    model_id: str | None = None,
    output_format: str = "markdown",
    max_papers: int | None = None,
    dry_run: bool = False,
) -> SynthesisResult | str:
    """Generate a multi-round literature synthesis from kept papers."""
    from scholar.notes import get_paper_id

    # Validate research context
    if not session.research_context:
        raise ValueError(
            "No research context set. Use 'scholar llm context <session> "
            "<context>' to set the research question first."
        )

    kept_all = [
        d for d in session.decisions if d.status == DecisionStatus.KEPT
    ]
    if not kept_all:
        raise ValueError(
            "No kept papers to synthesize. Use 'scholar sessions show' to "
            "check session status, or review papers first."
        )

    total_kept_papers = len(kept_all)
    kept_decisions = kept_all

    # Limit papers if requested
    if max_papers and len(kept_decisions) > max_papers:
        logger.warning(
            f"Limiting synthesis to {max_papers} papers "
            f"(session has {len(kept_decisions)})"
        )
        kept_decisions = kept_decisions[:max_papers]

    # Warn about large paper counts
    if len(kept_decisions) > 30 and not max_papers:
        logger.warning(
            f"Synthesizing {len(kept_decisions)} papers may exceed token "
            "limits. Consider using --max-papers to limit."
        )

    included_kept_papers = len(kept_decisions)

    citation_keys = _generate_all_citation_keys(kept_decisions, output_format)
    themes, groups = _group_kept_papers_by_theme(kept_decisions)

    # Prepare prompts (for dry-run and execution).
    theme_prompts: list[tuple[str | None, str]] = []
    for theme, group_decisions in groups.items():
        theme_prompts.append(
            (
                theme,
                build_theme_section_prompt(
                    theme=theme,
                    kept_decisions=group_decisions,
                    research_context=session.research_context,
                    citation_keys=citation_keys,
                    output_format=output_format,
                ),
            )
        )

    if dry_run:
        parts: list[str] = []
        for theme, prompt in theme_prompts:
            label = theme if theme is not None else "UNTHEMED"
            parts.append(f"--- THEME PROMPT: {label} ---\n{prompt}\n")

        placeholder_sections: list[ThemeSectionResult] = []
        for theme in groups:
            label = theme if theme is not None else "Synthesis"
            placeholder_sections.append(
                ThemeSectionResult(
                    theme=theme,
                    title=label,
                    section="",
                    summary=(
                        f"[Placeholder summary for {label}; generated in a previous round.]"
                    ),
                    abstract="",
                    paper_count=len(groups[theme]),
                )
            )

        conclusion_prompt = build_conclusion_prompt(
            research_context=session.research_context,
            theme_sections=placeholder_sections,
            output_format=output_format,
        )
        parts.append(f"--- CONCLUSION PROMPT ---\n{conclusion_prompt}\n")
        return "\n".join(parts)

    # Import llm and call
    try:
        import llm as llm_module
    except ImportError:
        raise ImportError(
            "The 'llm' package is required for synthesis. "
            "Install it with: pip install llm"
        )

    llm = globals().get("llm", llm_module)
    model = llm.get_model(model_id) if model_id else llm.get_model()
    effective_model_id = model.model_id
    logger.info(
        f"Generating multi-round synthesis from {len(kept_decisions)} papers "
        f"with {effective_model_id}"
    )

    theme_results: list[ThemeSectionResult] = []
    theme_cache_keys: list[str] = []
    for theme, prompt in theme_prompts:
        group_decisions = groups[theme]
        cache_key = _theme_cache_key(
            theme=theme,
            decisions=group_decisions,
            research_context=session.research_context,
            model_id=effective_model_id,
            output_format=output_format,
        )
        theme_cache_keys.append(cache_key)

        cached = SYNTHESIS_THEME_CACHE.get(cache_key)
        if isinstance(cached, dict):
            logger.info(
                "synthesis: Cache hit for theme "
                f"{theme if theme is not None else 'UNTHEMED'}"
            )
            theme_results.append(
                ThemeSectionResult(
                    theme=cached.get("theme"),
                    title=cached.get("title") or (theme or "Synthesis"),
                    section=cached.get("section", ""),
                    summary=cached.get("summary", ""),
                    subquestions=cached.get("subquestions", []),
                    abstract=cached.get("abstract", ""),
                    paper_count=cached.get(
                        "paper_count", len(group_decisions)
                    ),
                )
            )
            continue

        logger.info(
            "synthesis: Cache miss for theme "
            f"{theme if theme is not None else 'UNTHEMED'}"
        )
        response = model.prompt(prompt)
        parsed = parse_theme_section_response(
            response.text(),
            theme=theme,
            output_format=output_format,
            paper_count=len(group_decisions),
        )

        # If the model failed to propose a better title, do a focused follow-up
        # prompt using the section abstract.
        if (
            theme is not None
            and title_needs_improvement(theme, parsed.title)
            and parsed.abstract
        ):
            title_prompt = build_title_from_abstract_prompt(
                theme=theme,
                section_abstract=parsed.abstract,
                output_format=output_format,
            )
            title_response = model.prompt(title_prompt)
            better_title = _extract_marked_block(
                title_response.text(),
                SYNTHESIS_TITLE_START,
                SYNTHESIS_TITLE_END,
            )
            if better_title:
                parsed.title = better_title.strip()
                parsed.section = _replace_theme_heading(
                    parsed.section,
                    parsed.title,
                    output_format,
                )

        theme_results.append(parsed)
        SYNTHESIS_THEME_CACHE[cache_key] = {
            "theme": parsed.theme,
            "title": parsed.title,
            "section": parsed.section,
            "summary": parsed.summary,
            "subquestions": parsed.subquestions,
            "abstract": parsed.abstract,
            "paper_count": parsed.paper_count,
        }

    # Conclusion round based on summaries.
    conclusion_cache_key = _conclusion_cache_key(
        theme_sections=theme_results,
        theme_cache_keys=theme_cache_keys,
        research_context=session.research_context,
        model_id=effective_model_id,
        output_format=output_format,
    )
    cached_conclusion = SYNTHESIS_CONCLUSION_CACHE.get(conclusion_cache_key)
    if isinstance(cached_conclusion, dict) and cached_conclusion.get(
        "conclusion"
    ):
        logger.info("synthesis: Cache hit for conclusion")
        conclusion_text = str(cached_conclusion.get("conclusion"))
    else:
        logger.info("synthesis: Cache miss for conclusion")
        conclusion_prompt = build_conclusion_prompt(
            research_context=session.research_context,
            theme_sections=theme_results,
            output_format=output_format,
        )
        conclusion_response = model.prompt(conclusion_prompt)
        conclusion_text = _extract_marked_block(
            conclusion_response.text(),
            SYNTHESIS_SECTION_START,
            SYNTHESIS_SECTION_END,
        )
        if conclusion_text is None:
            conclusion_text = conclusion_response.text().strip()
        conclusion_text = _strip_conclusion_heading(
            conclusion_text, output_format
        )
        SYNTHESIS_CONCLUSION_CACHE[conclusion_cache_key] = {
            "conclusion": conclusion_text,
        }

    # Build references list and assemble final output.
    references: list[dict[str, Any]] = []
    for decision in kept_decisions:
        paper_id = get_paper_id(decision.paper)
        _, bibtex_key = citation_keys[paper_id]
        references.append(
            {
                "key": bibtex_key,
                "title": decision.paper.title,
                "authors": decision.paper.authors,
                "year": decision.paper.year,
                "venue": decision.paper.venue,
                "doi": decision.paper.doi,
                "url": decision.paper.url,
            }
        )

    # Report abstract (cached via conclusion cache entry).
    cached_abstract = SYNTHESIS_CONCLUSION_CACHE.get(
        conclusion_cache_key, {}
    ).get("report_abstract")
    if cached_abstract:
        report_abstract = str(cached_abstract)
    else:
        abstract_prompt = build_synthesis_abstract_prompt(
            research_context=session.research_context,
            theme_sections=theme_results,
            conclusion=conclusion_text,
            output_format=output_format,
        )
        abstract_response = model.prompt(abstract_prompt)
        report_abstract = parse_report_abstract(abstract_response.text())

    if output_format == "latex":
        bibtex_content = _build_bibtex_content(kept_decisions, citation_keys)
        synthesis_text = _assemble_latex_synthesis(
            session=session,
            theme_sections=theme_results,
            conclusion=conclusion_text,
            bibtex_content=bibtex_content,
            included_kept_papers=included_kept_papers,
            total_kept_papers=total_kept_papers,
            report_abstract=report_abstract,
        )
    else:
        references_markdown = _build_references_markdown(
            kept_decisions, citation_keys
        )
        synthesis_text = _assemble_markdown_synthesis(
            session=session,
            theme_sections=theme_results,
            conclusion=conclusion_text,
            references_markdown=references_markdown,
            included_kept_papers=included_kept_papers,
            total_kept_papers=total_kept_papers,
        )

    # Persist final output too, since it's cheap and avoids re-assembly.
    SYNTHESIS_CONCLUSION_CACHE[conclusion_cache_key][
        "assembled"
    ] = synthesis_text
    SYNTHESIS_CONCLUSION_CACHE[conclusion_cache_key][
        "report_abstract"
    ] = report_abstract

    return SynthesisResult(
        synthesis=synthesis_text,
        model_id=effective_model_id,
        timestamp=datetime.now().isoformat(),
        paper_count=len(kept_decisions),
        themes=themes,
        references=references,
        theme_sections=theme_results,
        conclusion=conclusion_text,
    )
