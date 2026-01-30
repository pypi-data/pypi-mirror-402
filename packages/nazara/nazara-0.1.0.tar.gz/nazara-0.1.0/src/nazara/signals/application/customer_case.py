import logging
from datetime import UTC

from django.db import transaction
from django.utils import timezone

from nazara.shared.domain.dtos.signal_data import CustomerCaseData
from nazara.shared.domain.value_objects.types import ProcessingResult
from nazara.shared.event_bus.contracts import EventBus
from nazara.signals.domain.contracts.customer_case_repository import CustomerCaseRepository
from nazara.signals.domain.models import PriorityChoices, SeverityChoices, StatusChoices

logger = logging.getLogger(__name__)


def _map_priority(priority: int | str) -> int:
    if isinstance(priority, int):
        if 0 <= priority <= 3:
            return priority
        return PriorityChoices.NORMAL

    priority_map = {
        "urgent": PriorityChoices.URGENT,
        "high": PriorityChoices.HIGH,
        "normal": PriorityChoices.NORMAL,
        "low": PriorityChoices.LOW,
    }
    return priority_map.get(str(priority).lower(), PriorityChoices.NORMAL)


def _map_severity(severity_str: str) -> str:
    severity_map = {
        "critical": SeverityChoices.CRITICAL,
        "high": SeverityChoices.HIGH,
        "medium": SeverityChoices.MEDIUM,
        "low": SeverityChoices.LOW,
        "info": SeverityChoices.INFO,
    }
    return severity_map.get(severity_str.lower(), SeverityChoices.MEDIUM)


def _map_status(status_str: str) -> str:
    status_map = {
        "open": StatusChoices.OPEN,
        "investigating": StatusChoices.INVESTIGATING,
        "identified": StatusChoices.IDENTIFIED,
        "monitoring": StatusChoices.MONITORING,
        "resolved": StatusChoices.RESOLVED,
        "closed": StatusChoices.CLOSED,
    }
    return status_map.get(status_str.lower(), StatusChoices.OPEN)


def _dto_to_model_data(data: CustomerCaseData) -> dict[str, object]:
    status = _map_status(data.status)
    severity = _map_severity(data.severity)
    priority = _map_priority(data.priority)

    started_at = data.started_at
    if started_at and timezone.is_naive(started_at):
        started_at = timezone.make_aware(started_at, UTC)

    ended_at = data.ended_at
    if ended_at and timezone.is_naive(ended_at):
        ended_at = timezone.make_aware(ended_at, UTC)

    return {
        "customer_id": data.customer_id or "",
        "customer_email": data.customer_email,
        "customer_name": data.customer_name or "",
        "title": (data.title or "")[:500],
        "description": (data.description or "")[:5000],
        "status": status,
        "severity": severity,
        "priority": priority,
        "category": data.category,
        "source_system": data.source_system,
        "source_identifier": data.source_identifier,
        "source_url": data.source_url,
        "started_at": started_at,
        "ended_at": ended_at,
        "tags": list(data.tags),
        "metadata": dict(data.metadata),
        "raw_data": dict(data.raw_payload),
        "conversation": list(data.conversation),
    }


class CreateCustomerCase:
    """
    Application service for creating customer cases.

    This service bridges the ingestion bounded context and the signals bounded
    context for CustomerCase entities. It can be used from any entry point
    (ingestion, admin, API) to create or update customer cases.

    Uses the domain events pattern:
    - Service calls domain methods which register events
    - Service publishes events after transaction commits via on_commit
    """

    def __init__(
        self,
        case_repo: CustomerCaseRepository,
        event_bus: EventBus,
    ) -> None:
        self._case_repo = case_repo
        self._event_bus = event_bus

    def from_data(self, data: CustomerCaseData) -> ProcessingResult:
        """
        Create or update a CustomerCase from a CustomerCaseData DTO.

        If case exists: apply changes via domain method.
        If new: create case via factory method.
        Skips database write if content unchanged (via content hash).

        Returns:
            ProcessingResult indicating what happened (CREATED, UPDATED, SKIPPED, FAILED)
        """
        try:
            if not data.source_system or not data.source_identifier:
                logger.warning(
                    f"Missing source identity in data: "
                    f"system={data.source_system}, id={data.source_identifier}"
                )
                return ProcessingResult.FAILED

            model_data = _dto_to_model_data(data)
            existing = self._case_repo.get_by_source(data.source_system, data.source_identifier)

            if existing:
                update_data = {
                    k: v
                    for k, v in model_data.items()
                    if k not in ("source_system", "source_identifier")
                }
                existing.apply_changes(**update_data)
                case, was_saved = self._case_repo.save(existing)

                if was_saved:
                    logger.debug(
                        f"Updated customer case: {case.id} ({data.source_system}:{data.source_identifier})"
                    )
                    result = ProcessingResult.UPDATED
                else:
                    logger.debug(
                        f"Customer case unchanged: {case.id} ({data.source_system}:{data.source_identifier})"
                    )
                    result = ProcessingResult.SKIPPED
            else:
                from nazara.signals.domain.models import CustomerCase

                case = CustomerCase.create(**model_data)
                case, was_saved = self._case_repo.save(case)
                result = ProcessingResult.CREATED
                logger.info(
                    f"Created customer case: {case.id} ({data.source_system}:{data.source_identifier})"
                )

            if was_saved:
                transaction.on_commit(lambda c=case: c.publish_domain_events(self._event_bus))

            return result

        except Exception as e:
            logger.error(f"Failed to create customer case from data: {e}", exc_info=True)
            return ProcessingResult.FAILED
