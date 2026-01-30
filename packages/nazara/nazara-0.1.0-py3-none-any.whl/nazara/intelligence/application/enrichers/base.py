import hashlib
from abc import ABC
from typing import Any

from nazara.intelligence.domain.contracts.llm import LLMConnector
from nazara.intelligence.domain.contracts.step import EnrichmentStep


def _hash_content(*parts: str) -> str:
    content = "|".join(str(p) for p in parts)
    return hashlib.sha256(content.encode()).hexdigest()


class BaseEnrichmentStep(EnrichmentStep, ABC):
    """
    Base class providing common Step Protocol logic.

    Subclasses implement: key, produces, uses_llm, is_available,
                          compute_input_hash, execute
    Optionally override: requires (for dependencies)
    """

    def should_run(
        self, signal: Any, record: Any, context: dict[str, Any], force: bool = False
    ) -> tuple[bool, str]:
        if force:
            return True, "forced"

        if record is None:
            return True, "no existing record"

        current_hash = self.compute_input_hash(signal, context)
        if record.input_hash != current_hash:
            return True, "input changed"

        if self.produces == "result" and not record.result:
            return True, "no result stored"

        if self.produces == "embedding" and not record.embedding:
            return True, "no embedding stored"

        return False, "already processed with same input"


class LLMEnrichmentStep(BaseEnrichmentStep, ABC):
    """
    Base class for enrichment steps that use an LLM connector.

    Provides common connector handling:
    - __init__ with connector parameter
    - is_available() checks connector presence
    - uses_llm property returns True

    Subclasses implement: key, produces, compute_input_hash, execute
    """

    def __init__(self, connector: LLMConnector | None) -> None:
        self._connector = connector

    @property
    def uses_llm(self) -> bool:
        return True

    def is_available(self) -> bool:
        return self._connector is not None
