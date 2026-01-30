"""EnrichmentInput contract for signal enrichment.

This module defines the data contract that signals implement to provide
structured data for enrichment operations (summary, embedding, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable
from uuid import UUID

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class EnrichmentInput:
    """
    Structured data contract for signal enrichment.

    Signals produce this; enrichers consume it.
    Designed to be signal-type-agnostic while allowing
    each signal to provide rich, relevant data.

    Attributes:
        signal_type: The type of signal (e.g., "Incident", "CustomerCase").
        signal_id: Unique identifier of the signal.
        title: Primary title/headline of the signal.
        content: Main text body - signal combines its relevant fields here.
        metadata: Structured facts (severity, status, service, etc.).
        context: Extended info (timeline, conversation, sample_payload, etc.).
    """

    signal_type: str
    signal_id: UUID
    title: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class SupportsEnrichment(Protocol):
    """Protocol for signals that can provide enrichment input."""

    SIGNAL_TYPE: str
    id: UUID

    def to_enrichment_input(self) -> EnrichmentInput:
        """Return structured data for enrichment operations."""
        ...
