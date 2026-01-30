from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar


@dataclass(frozen=True)
class StepResult:
    success: bool
    output: dict[str, Any] | None = None
    embedding: list[float] | None = None
    error: str | None = None


class EnrichmentStep(ABC):
    """
    Contract for enrichment pipeline steps.

    Steps are version-agnostic: GenerateSummary handles summary.v1, summary.v2, etc.
    The version is determined by the enrichment_type in context, which selects the prompt.
    """

    # Intrinsic dependencies - override in subclass if step has dependencies
    # Used for flow VALIDATION at save time, not execution order
    requires: ClassVar[list[str]] = []

    @property
    @abstractmethod
    def key(self) -> str:
        """Base key without version (e.g., 'summary', 'embedding')."""

    @property
    @abstractmethod
    def produces(self) -> str:
        """What this step outputs: 'result' (JSONField) or 'embedding' (VectorField)."""

    @property
    @abstractmethod
    def uses_llm(self) -> bool:
        """Whether this step requires an LLM connector."""

    @abstractmethod
    def is_available(self) -> bool:
        """Whether the step can execute (e.g., connector configured)."""

    @abstractmethod
    def compute_input_hash(self, signal: Any, context: dict[str, Any]) -> str:
        """Compute hash of inputs for idempotency checking."""

    @abstractmethod
    def should_run(
        self, signal: Any, record: Any, context: dict[str, Any], force: bool = False
    ) -> tuple[bool, str]:
        """
        Determine if step should execute.

        Returns (should_run, reason) tuple.
        """

    @abstractmethod
    def execute(self, signal: Any, profile: Any, context: dict[str, Any]) -> StepResult:
        """Execute the enrichment step and return result."""
