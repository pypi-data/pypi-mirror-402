from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from nazara.signals.domain.models import Incident


class IncidentRepository(ABC):
    """
    Abstract repository for Incident aggregate.

    This port defines how the domain interacts with persistence.
    Returns Django models directly (no mapping layer).
    """

    @abstractmethod
    def save(self, incident: "Incident") -> "tuple[Incident, bool]":
        """
        Persist an incident with content hash change detection.

        Computes content hash and compares with existing. Only performs
        database write if content has actually changed.

        Args:
            incident: The Incident to save

        Returns:
            Tuple of (Incident, was_saved) where was_saved indicates
            if a database write occurred (False if skipped due to same hash)
        """
        ...

    @abstractmethod
    def get(self, incident_id: UUID) -> "Incident | None":
        """
        Retrieve an incident by its ID.

        Args:
            incident_id: The unique identifier

        Returns:
            The Incident if found, None otherwise
        """
        ...

    @abstractmethod
    def delete(self, incident_id: UUID) -> bool:
        """
        Delete an incident.

        Args:
            incident_id: The incident identifier to delete

        Returns:
            True if deleted, False if not found
        """
        ...

    @abstractmethod
    def count(
        self,
        status: str | None = None,
        severity: str | None = None,
    ) -> int:
        """
        Count incidents matching criteria.

        Args:
            status: Optional status filter
            severity: Optional severity filter

        Returns:
            Count of matching incidents
        """
        ...

    @abstractmethod
    def get_by_source(
        self,
        source_system: str,
        source_identifier: str,
    ) -> "Incident | None":
        """
        Find an incident by its source system and identifier.

        Args:
            source_system: The source system (e.g., "incident_io")
            source_identifier: The external identifier

        Returns:
            The Incident if found, None otherwise
        """
        ...
