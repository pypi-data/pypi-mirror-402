from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from nazara.intelligence.domain.context_narrowing import NarrowingResult
    from nazara.intelligence.domain.models import DomainProfile
    from nazara.shared.enrichment_input import EnrichmentInput


class PromptNotFoundError(Exception):
    pass


@lru_cache(maxsize=32)
def load_prompt(name: str) -> str:
    """
    Load a prompt template from a .md file in the prompts directory.

    Prompts are cached after first load for performance.
    The cache can be cleared with `load_prompt.cache_clear()`.

    Note: This returns the raw template. For rendering with organizational
    context, use `render_prompt()` instead.

    Args:
        name: Prompt name without extension (e.g., "summary.v1")

    Returns:
        The prompt template as a string

    Raises:
        PromptNotFoundError: If the prompt file doesn't exist
    """
    prompts_dir = Path(__file__).parent
    prompt_path = prompts_dir / f"{name}.md"

    if not prompt_path.exists():
        available = [p.stem for p in prompts_dir.glob("*.md")]
        raise PromptNotFoundError(
            f"Prompt '{name}' not found at {prompt_path}. Available prompts: {available}"
        )

    return prompt_path.read_text().strip()


def list_prompts() -> list[str]:
    """
    List all available prompt names.

    Returns:
        List of prompt names (without .md extension)
    """
    prompts_dir = Path(__file__).parent
    return sorted(p.stem for p in prompts_dir.glob("*.md"))


def render_prompt(
    name: str,
    profile: DomainProfile | None = None,
    narrowing: NarrowingResult | None = None,
) -> str:
    """
    Load a prompt template and render with organizational context.

    This is the primary function for obtaining prompts for LLM calls.
    It injects organizational context (systems, glossary, policies) from
    the DomainProfile into the system prompt.

    Note: This function is NOT cached because the organizational context
    varies per profile. The underlying template loading is cached.

    Args:
        name: Prompt name without extension (e.g., "summary.v1")
        profile: Optional DomainProfile for organizational context
        narrowing: Optional NarrowingResult for signal-specific context

    Returns:
        The fully rendered prompt ready for LLM consumption
    """
    from nazara.intelligence.domain.context_narrowing import build_narrowed_context

    template = load_prompt(name)

    if narrowing is not None:
        context = build_narrowed_context(narrowing)
        return template.replace("{organizational_context}", context)

    if profile is None:
        return template.replace("{organizational_context}", "")

    context = build_organizational_context(profile)
    return template.replace("{organizational_context}", context)


def build_organizational_context(profile: DomainProfile) -> str:
    """
    Build organizational context string for prompt templates.

    Converts DomainProfile child entities into a human/AI-readable
    markdown format for system prompts.

    Sections included:
    - Categories: Business classification domains
    - Severity Levels: Impact scale definitions
    - Systems: Infrastructure and service inventory
    - Terminology: Glossary of domain-specific terms
    - Operational Priorities: Business rules and priorities

    Args:
        profile: The DomainProfile containing organizational context

    Returns:
        Formatted markdown string with organizational context sections
    """
    sections: list[str] = []

    # Business categories
    categories = profile.categories.all()
    if categories.exists():
        lines = ["## Business Categories"]
        for c in categories:
            desc = f": {c.description}" if c.description else ""
            lines.append(f"- **{c.label}**{desc}")
        sections.append("\n".join(lines))

    # Severity levels
    severities = profile.severities.all()
    if severities.exists():
        lines = ["## Severity Levels"]
        for sev in severities:
            desc = f": {sev.description}" if sev.description else ""
            lines.append(f"- **{sev.label}**{desc}")
        sections.append("\n".join(lines))

    # Systems catalog
    systems = profile.systems.all()
    if systems.exists():
        lines = ["## Known Systems"]
        for sys in systems:
            desc = f": {sys.description}" if sys.description else ""
            lines.append(f"- **{sys.label}** ({sys.get_entry_type_display()}){desc}")
        sections.append("\n".join(lines))

    # Glossary terms
    terms = profile.glossary.all()
    if terms.exists():
        lines = ["## Terminology"]
        for t in terms:
            aliases = f" (also: {', '.join(t.aliases)})" if t.aliases else ""
            lines.append(f"- **{t.term}**{aliases}: {t.definition}")
        sections.append("\n".join(lines))

    # Operational policies
    policies = profile.operational_policies.all()
    if policies.exists():
        lines = ["## Operational Priorities"]
        for p in policies:
            lines.append(f"- {p.statement}")
        sections.append("\n".join(lines))

    if not sections:
        return ""

    return "\n\n".join(sections) + "\n"


def format_user_content(
    title: str,
    description: str,
    metadata: dict[str, Any] | None = None,
) -> str:
    """
    Format user content for LLM including signal metadata.

    Creates a structured user message combining the signal's title,
    description, and optional metadata in a readable format.

    Args:
        title: The signal title
        description: The signal description/content
        metadata: Optional dict with signal metadata (severity, status, etc.)

    Returns:
        Formatted string ready for LLM user message

    Example:
        >>> format_user_content(
        ...     "Database connection exhausted",
        ...     "Multiple services reporting timeouts",
        ...     {"severity": "critical", "affected_services": ["billing-api"]}
        ... )
        'Title: Database connection exhausted\\n\\nDescription: Multiple services...\\n\\nSignal Metadata:\\n- Severity: critical\\n- Affected Services: billing-api'
    """
    parts = [f"Title: {title}", f"\nDescription: {description}"]

    if metadata:
        lines = ["\n\nSignal Metadata:"]
        for key, value in metadata.items():
            if value is None:
                continue
            label = key.replace("_", " ").title()
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            lines.append(f"- {label}: {value}")
        if len(lines) > 1:  # Only add if we have actual metadata
            parts.append("\n".join(lines))

    return "".join(parts)


def format_enrichment_input(enrichment_input: EnrichmentInput) -> str:
    """
    Format EnrichmentInput for LLM consumption.

    Produces structured text with:
    - Title
    - Content (signal-specific combined text)
    - Metadata section (structured facts)
    - Context section (timeline, tags, timestamps)

    This is the preferred way to format signal data for enrichment.
    Each signal's to_enrichment_input() method decides what data to include.

    Args:
        enrichment_input: The EnrichmentInput from a signal's to_enrichment_input()

    Returns:
        Formatted string ready for LLM user message
    """
    parts = [
        f"Title: {enrichment_input.title}",
        f"\n\nContent:\n{enrichment_input.content}",
    ]

    # Format metadata
    if enrichment_input.metadata:
        metadata_lines = ["\n\nMetadata:"]
        for key, value in enrichment_input.metadata.items():
            if value is None:
                continue
            label = key.replace("_", " ").title()
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            metadata_lines.append(f"- {label}: {value}")
        if len(metadata_lines) > 1:
            parts.append("\n".join(metadata_lines))

    # Format context
    if enrichment_input.context:
        context_lines = ["\n\nAdditional Context:"]

        # Tags
        if tags := enrichment_input.context.get("tags"):
            if isinstance(tags, list):
                context_lines.append(f"- Tags: {', '.join(str(t) for t in tags)}")

        # Time range
        if started := enrichment_input.context.get("started_at"):
            context_lines.append(f"- Started: {started}")
        if ended := enrichment_input.context.get("ended_at"):
            context_lines.append(f"- Ended: {ended}")
        if first_seen := enrichment_input.context.get("first_seen_at"):
            context_lines.append(f"- First Seen: {first_seen}")
        if last_seen := enrichment_input.context.get("last_seen_at"):
            context_lines.append(f"- Last Seen: {last_seen}")

        # Total messages for CustomerCase
        if total_messages := enrichment_input.context.get("total_messages"):
            context_lines.append(f"- Total Messages: {total_messages}")

        if len(context_lines) > 1:
            parts.append("\n".join(context_lines))

    return "".join(parts)
