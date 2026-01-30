from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from nazara.signals.domain.models import TechnicalIssue


class TechnicalIssueRepository(ABC):
    """
    Abstract repository for TechnicalIssue aggregate.

    This port defines how the domain interacts with persistence.
    Returns Django models directly (no mapping layer).

    TechnicalIssue is the aggregate root - TechnicalEvent entities
    are persisted through this repository as part of the aggregate.
    """

    @abstractmethod
    def save(self, issue: "TechnicalIssue") -> "tuple[TechnicalIssue, int]":
        """
        Persist a technical issue and its pending events atomically.

        This method:
        - Saves the TechnicalIssue aggregate root
        - Saves all pending TechnicalEvent entities
        - Handles duplicate events via IntegrityError (skips silently)
        - Updates occurrences_total based on actually-saved events
        - Clears pending events after successful save

        Args:
            issue: The TechnicalIssue aggregate to save

        Returns:
            Tuple of (TechnicalIssue, events_saved_count)
            - events_saved_count: Number of new events actually persisted
              (excludes duplicates that were skipped)
        """
        ...

    @abstractmethod
    def get_by_identity(
        self,
        provider: str,
        issue_key: str,
        environment: str,
        service: str,
    ) -> "TechnicalIssue | None":
        """
        Find an issue by its composite natural key.

        Args:
            provider: The event provider (e.g., 'sentry', 'datadog')
            issue_key: The provider-specific issue key
            environment: The environment name
            service: The service name

        Returns:
            The TechnicalIssue if found, None otherwise
        """
        ...

    @abstractmethod
    def get(self, issue_id: UUID) -> "TechnicalIssue | None":
        """
        Find an issue by its primary key.

        Args:
            issue_id: The issue UUID

        Returns:
            The TechnicalIssue if found, None otherwise
        """
        ...

    @abstractmethod
    def delete(self, issue_id: UUID) -> bool:
        """
        Delete an issue.

        Note: This cascades to delete linked TechnicalEvent entities.

        Args:
            issue_id: The issue identifier to delete

        Returns:
            True if deleted, False if not found
        """
        ...

    @abstractmethod
    def delete_stale_before(self, before: datetime) -> int:
        """
        Delete all issues with last_seen_at before the given date.

        Used by retention jobs to clean up old issues.

        Args:
            before: Delete issues with last_seen_at before this date

        Returns:
            Number of issues deleted
        """
        ...

    @abstractmethod
    def count(
        self,
        provider: str | None = None,
        environment: str | None = None,
        service: str | None = None,
        status: str | None = None,
    ) -> int:
        """
        Count issues matching criteria.

        Args:
            provider: Optional provider filter
            environment: Optional environment filter
            service: Optional service filter
            status: Optional status filter

        Returns:
            Count of matching issues
        """
        ...
