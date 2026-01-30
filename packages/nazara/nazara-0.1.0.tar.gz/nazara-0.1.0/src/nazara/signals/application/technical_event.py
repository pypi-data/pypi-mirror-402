import logging
from datetime import UTC

from django.db import transaction
from django.utils import timezone

from nazara.shared.domain.dtos.signal_data import TechnicalEventData
from nazara.shared.domain.value_objects.types import ProcessingResult
from nazara.shared.event_bus.contracts import EventBus
from nazara.signals.domain.contracts.technical_issue_repository import (
    TechnicalIssueRepository,
)
from nazara.signals.domain.events import SignalUpdatedEvent
from nazara.signals.domain.models import (
    EventTypeChoices,
    IssueStatusChoices,
    SeverityChoices,
    TechnicalEvent,
    TechnicalIssue,
)

logger = logging.getLogger(__name__)


class CreateTechnicalEvent:
    """
    Application service for creating technical events through the aggregate pattern.

    This service bridges the ingestion bounded context and signals bounded context.
    TechnicalIssue is the aggregate root - TechnicalEvent entities are persisted
    through the issue repository as part of the aggregate.

    Flow:
    1. Create TechnicalEvent entity (not persisted yet)
    2. Find TechnicalIssue by identity (provider, issue_key, environment, service)
    3. If found: add event to existing issue
    4. If not found: create new issue with the event
    5. Save issue (persists events atomically, handles duplicates)
    6. Publish domain events after transaction commit

    Uses the domain events pattern:
    - Aggregate methods register domain events
    - Service publishes events after transaction commits via on_commit
    """

    def __init__(
        self,
        issue_repo: TechnicalIssueRepository,
        event_bus: EventBus,
    ) -> None:
        self._issue_repo = issue_repo
        self._event_bus = event_bus

    def from_data(self, data: TechnicalEventData) -> ProcessingResult:
        """
        Ingest a TechnicalEvent through the aggregate pattern.

        Returns:
            ProcessingResult indicating what happened (CREATED, UPDATED, SKIPPED, FAILED)
        """
        try:
            event = self._dto_to_event(data)

            issue = self._issue_repo.get_by_identity(
                provider=data.provider,
                issue_key=data.issue_key,
                environment=data.environment,
                service=data.service,
            )

            is_new_issue = issue is None

            if issue is None:
                occurred_at = data.occurred_at or timezone.now()
                severity = self._map_severity(data.severity)
                issue = TechnicalIssue.create(
                    provider=data.provider,
                    issue_key=data.issue_key,
                    environment=data.environment,
                    service=data.service,
                    severity=severity,
                    category=data.category,
                    status=IssueStatusChoices.ACTIVE,
                    first_seen_at=occurred_at,
                    last_seen_at=occurred_at,
                    occurrences_total=1,
                    title=event.title,
                    last_message=event.error_message,
                    source_url=event.source_url,
                    sample_payload=event.raw_data,
                    events=[event],
                )
            else:
                issue.add_technical_event(event)

            issue, events_saved = self._issue_repo.save(issue)

            if events_saved == 0 and not is_new_issue:
                logger.debug(
                    f"Duplicate event skipped: {event.source_system}:{event.source_identifier}"
                )
                return ProcessingResult.SKIPPED

            if not is_new_issue and events_saved > 0:
                issue.register_domain_event(
                    SignalUpdatedEvent(
                        signal_type=issue.SIGNAL_TYPE,
                        signal_id=issue.id,
                        changed_fields=("occurrences_total", "last_seen_at"),
                    )
                )

            transaction.on_commit(lambda i=issue: i.publish_domain_events(self._event_bus))

            if is_new_issue:
                logger.info(f"Created new issue: {issue.id} ({data.provider}:{data.issue_key})")
                return ProcessingResult.CREATED
            else:
                logger.debug(f"Updated issue: {issue.id} (count: {issue.occurrences_total})")
                return ProcessingResult.UPDATED

        except Exception as e:
            logger.error(f"Failed to create event from payload: {e}", exc_info=True)
            return ProcessingResult.FAILED

    def _dto_to_event(self, data: TechnicalEventData) -> TechnicalEvent:
        event_type = self._map_event_type(data.event_type)
        severity = self._map_severity(data.severity)

        occurred_at = data.occurred_at or timezone.now()
        if timezone.is_naive(occurred_at):
            occurred_at = timezone.make_aware(occurred_at, UTC)

        tags = list(data.tags) if data.tags else []

        event = TechnicalEvent(
            provider=data.provider,
            external_id=data.external_id,
            dedupe_hash=None,
            event_type=event_type,
            title=(data.title or "Untitled Event")[:500],
            description=(data.description or "")[:5000],
            severity=severity,
            source_system=data.source_system,
            source_identifier=data.source_identifier,
            source_url=data.source_url,
            service=data.service,
            environment=data.environment,
            host=data.host,
            transaction=data.transaction,
            release=data.release,
            occurred_at=occurred_at,
            started_at=occurred_at,
            ended_at=None,
            tags=tags,
            raw_data=data.raw_payload,
        )

        if data.error_type or data.error_message:
            event.set_error_info(
                error_type=data.error_type,
                message=data.error_message,
                stacktrace=data.error_stacktrace,
                fingerprint=data.error_fingerprint,
            )

        return event

    def _map_event_type(self, type_str: str) -> str:
        type_map = {
            "error": EventTypeChoices.ERROR,
            "exception": EventTypeChoices.EXCEPTION,
            "alert": EventTypeChoices.ALERT,
            "metric_anomaly": EventTypeChoices.METRIC_ANOMALY,
            "log_pattern": EventTypeChoices.LOG_PATTERN,
            "deployment": EventTypeChoices.DEPLOYMENT,
            "configuration_change": EventTypeChoices.CONFIGURATION_CHANGE,
        }
        return type_map.get(type_str.lower(), EventTypeChoices.ALERT)

    def _map_severity(self, severity_str: str) -> str:
        severity_map = {
            "critical": SeverityChoices.CRITICAL,
            "high": SeverityChoices.HIGH,
            "medium": SeverityChoices.MEDIUM,
            "low": SeverityChoices.LOW,
            "info": SeverityChoices.INFO,
        }
        return severity_map.get(severity_str.lower(), SeverityChoices.MEDIUM)
