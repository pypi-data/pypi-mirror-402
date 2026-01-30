from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from nazara.ingestion.domain.models import IngestorConfig


class IngestorConfigRepository(ABC):
    """
    Repository interface for IngestorConfig persistence.

    Returns Django models directly (no mapping layer).
    """

    @abstractmethod
    def get(self, config_id: UUID) -> "IngestorConfig | None": ...

    @abstractmethod
    def list_due_for_polling(self, as_of: datetime | None = None) -> "list[IngestorConfig]": ...

    @abstractmethod
    def save(self, config: "IngestorConfig") -> "IngestorConfig": ...

    @abstractmethod
    def delete(self, config_id: UUID) -> bool: ...
