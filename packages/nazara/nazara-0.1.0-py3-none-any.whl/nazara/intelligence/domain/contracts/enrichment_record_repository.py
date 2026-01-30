from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from nazara.intelligence.domain.models import EnrichmentRecord


class EnrichmentRecordRepository(ABC):
    """
    Abstract repository for EnrichmentRecord.

    This port defines how the domain interacts with enrichment persistence.
    One record per (target_type, target_id, enrichment_type).
    """

    @abstractmethod
    def get(
        self,
        target_type: str,
        target_id: UUID,
        enrichment_type: str,
    ) -> "EnrichmentRecord | None":
        """
        Get one record by full key.

        Args:
            target_type: The signal type (e.g., "Incident")
            target_id: The signal's UUID
            enrichment_type: The enrichment type (e.g., "summary.v1")

        Returns:
            The EnrichmentRecord if found, None otherwise
        """
        ...

    @abstractmethod
    def list(
        self,
        target_type: str,
        target_id: UUID,
        status: str | None = "success",
    ) -> list["EnrichmentRecord"]:
        """
        Get all records for a signal.

        Args:
            target_type: The signal type (e.g., "Incident")
            target_id: The signal's UUID
            status: Optional status filter (default: "success")

        Returns:
            List of matching EnrichmentRecords
        """
        ...

    @abstractmethod
    def save(self, record: "EnrichmentRecord") -> "EnrichmentRecord":
        """
        Save or update an enrichment record.

        Args:
            record: The EnrichmentRecord to persist

        Returns:
            The saved EnrichmentRecord
        """
        ...
