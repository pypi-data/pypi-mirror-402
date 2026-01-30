import logging
from typing import Any

from nazara.intelligence.application.enrichers.base import LLMEnrichmentStep, _hash_content
from nazara.intelligence.domain.context_narrowing import ContextNarrowingService
from nazara.intelligence.domain.contracts.llm import LLMConnector
from nazara.intelligence.domain.contracts.step import StepResult
from nazara.intelligence.domain.prompts import format_enrichment_input, render_prompt
from nazara.intelligence.domain.step_registry import register_step

logger = logging.getLogger(__name__)


@register_step("summary")
class GenerateSummary(LLMEnrichmentStep):
    """
    Generates summaries for signals using LLM.

    Handles all summary versions (summary.v1, summary.v2, etc.) via prompt selection.
    """

    def __init__(self, connector: LLMConnector | None) -> None:
        super().__init__(connector)
        self.narrowing_service = ContextNarrowingService()

    @property
    def key(self) -> str:
        return "summary"

    @property
    def produces(self) -> str:
        return "result"

    def compute_input_hash(self, signal: Any, context: dict[str, Any]) -> str:
        enrichment_input = signal.to_enrichment_input()
        enrichment_type = context.get("enrichment_type", "summary.v1")
        return _hash_content(
            enrichment_input.title,
            enrichment_input.content,
            str(enrichment_input.metadata),
            enrichment_type,
        )

    def execute(self, signal: Any, profile: Any, context: dict[str, Any]) -> StepResult:
        if self._connector is None:
            return StepResult(success=False, error="No LLM connector configured")

        enrichment_type = context["enrichment_type"]
        enrichment_input = signal.to_enrichment_input()

        narrowing = self.narrowing_service.narrow(signal, profile)
        system_prompt = render_prompt(enrichment_type, profile, narrowing)
        user_content = format_enrichment_input(enrichment_input)

        try:
            response = self._connector.chat(system_prompt, user_content)
            logger.info(f"Generated summary for {signal.id}: {response.content[:50]}...")
            return StepResult(success=True, output={"text": response.content})
        except Exception as e:
            logger.error(f"Summary generation failed for {signal.id}: {e}")
            return StepResult(success=False, error=str(e))
