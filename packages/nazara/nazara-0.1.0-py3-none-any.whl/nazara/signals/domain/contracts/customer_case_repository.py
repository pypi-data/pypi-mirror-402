from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from nazara.signals.domain.models import CustomerCase


class CustomerCaseRepository(ABC):
    """
    Abstract repository for CustomerCase aggregate.

    This port defines how the domain interacts with persistence.
    Returns Django models directly (no mapping layer).
    """

    @abstractmethod
    def save(self, case: "CustomerCase") -> "tuple[CustomerCase, bool]":
        """
        Persist a customer case with content hash change detection.

        Computes content hash and compares with existing. Only performs
        database write if content has actually changed.

        Args:
            case: The CustomerCase to save

        Returns:
            Tuple of (CustomerCase, was_saved) where was_saved indicates
            if a database write occurred (False if skipped due to same hash)
        """
        ...

    @abstractmethod
    def delete(self, case_id: UUID) -> bool:
        """
        Delete a customer case.

        Args:
            case_id: The case identifier to delete

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
        Count cases matching criteria.

        Args:
            status: Optional status filter
            severity: Optional severity filter

        Returns:
            Count of matching cases
        """
        ...

    @abstractmethod
    def get_by_source(
        self,
        source_system: str,
        source_identifier: str,
    ) -> "CustomerCase | None":
        """
        Find a customer case by its source system and identifier.

        Args:
            source_system: The source system (e.g., "intercom")
            source_identifier: The external identifier

        Returns:
            The CustomerCase if found, None otherwise
        """
        ...
