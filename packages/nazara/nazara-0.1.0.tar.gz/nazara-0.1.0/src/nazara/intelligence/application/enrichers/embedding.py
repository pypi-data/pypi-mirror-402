import logging
from typing import Any

from nazara.intelligence.application.enrichers.base import LLMEnrichmentStep, _hash_content
from nazara.intelligence.domain.contracts.step import StepResult
from nazara.intelligence.domain.step_registry import register_step

logger = logging.getLogger(__name__)


@register_step("embedding")
class GenerateEmbedding(LLMEnrichmentStep):
    """
    Generates embeddings for signals using LLM.

    Flexible input strategy based on flow step configuration:
    - input_source="dependent": Use summary from previous step (preferred for quality)
    - input_source="raw": Use signal's raw title + description directly
    """

    @property
    def key(self) -> str:
        return "embedding"

    @property
    def produces(self) -> str:
        return "embedding"

    def compute_input_hash(self, signal: Any, context: dict[str, Any]) -> str:
        canonical_text = self._build_canonical_text(signal, context)
        enrichment_type = context.get("enrichment_type", "embedding.v1")
        return _hash_content(canonical_text, enrichment_type)

    def execute(self, signal: Any, profile: Any, context: dict[str, Any]) -> StepResult:
        if self._connector is None:
            return StepResult(success=False, error="No LLM connector configured")

        canonical_text = self._build_canonical_text(signal, context)

        if not canonical_text.strip():
            return StepResult(success=False, error="No content available to embed")

        try:
            response = self._connector.embed(canonical_text)
            logger.info(f"Generated embedding for {signal.id}: dim={len(response.vector)}")
            return StepResult(success=True, embedding=response.vector)
        except Exception as e:
            logger.error(f"Embedding generation failed for {signal.id}: {e}")
            return StepResult(success=False, error=str(e))

    def _build_canonical_text(self, signal: Any, context: dict[str, Any]) -> str:
        """
        Build text for embedding based on input_source configuration.

        - "dependent": Use summary from previous step (preferred for quality)
        - "raw": Use signal's enrichment input content (includes all relevant fields)
        """
        input_source = context.get("input_source", "dependent")
        enrichment_input = signal.to_enrichment_input()

        if input_source == "dependent":
            dependent_outputs: dict[str, Any] = context.get("dependent_outputs", {})
            for key, output in dependent_outputs.items():
                if key.startswith("summary."):
                    summary_text = output.get("text", "")
                    if summary_text:
                        return f"{enrichment_input.title}\n\n{summary_text}"
            # Fall back to raw if no summary available

        return f"{enrichment_input.title}\n\n{enrichment_input.content}"
