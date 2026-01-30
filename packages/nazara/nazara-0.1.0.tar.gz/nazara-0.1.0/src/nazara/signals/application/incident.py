import logging
from datetime import UTC, datetime
from typing import Any

from django.db import transaction
from django.utils import timezone

from nazara.shared.domain.dtos.signal_data import IncidentData
from nazara.shared.domain.value_objects.types import ProcessingResult
from nazara.shared.event_bus.contracts import EventBus
from nazara.signals.domain.contracts.incident_repository import IncidentRepository
from nazara.signals.domain.models import SeverityChoices, StatusChoices

logger = logging.getLogger(__name__)


class CreateIncident:
    """
    Application service for creating incidents.

    This service bridges the ingestion bounded context and the signals bounded
    context for Incident entities. It can be used from any entry point
    (ingestion, admin, API) to create or update incidents.

    Uses the domain events pattern:
    - Service calls domain methods which register events
    - Service publishes events after transaction commits via on_commit
    """

    def __init__(
        self,
        incident_repo: IncidentRepository,
        event_bus: EventBus,
    ) -> None:
        self._incident_repo = incident_repo
        self._event_bus = event_bus

    def from_data(self, data: IncidentData) -> ProcessingResult:
        """
        Create or update an Incident from an IncidentData DTO.

        If incident exists: apply changes via domain method, merge timeline.
        If new: create incident via factory method.
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

            model_data = self._dto_to_model_data(data)
            existing = self._incident_repo.get_by_source(data.source_system, data.source_identifier)

            if existing:
                model_data["timeline"] = self._merge_timelines(
                    existing_timeline=existing.timeline or [],
                    new_timeline=list(data.timeline),
                )
                model_data.pop("created_at", None)

                update_data = {
                    k: v
                    for k, v in model_data.items()
                    if k not in ("source_system", "source_identifier")
                }
                existing.apply_changes(**update_data)
                incident, was_saved = self._incident_repo.save(existing)

                if was_saved:
                    logger.debug(
                        f"Updated incident: {incident.id} ({data.source_system}:{data.source_identifier})"
                    )
                    result = ProcessingResult.UPDATED
                else:
                    logger.debug(
                        f"Incident unchanged: {incident.id} ({data.source_system}:{data.source_identifier})"
                    )
                    result = ProcessingResult.SKIPPED
            else:
                from nazara.signals.domain.models import Incident

                incident = Incident.create(**model_data)
                incident, was_saved = self._incident_repo.save(incident)
                result = ProcessingResult.CREATED
                logger.info(
                    f"Created incident: {incident.id} ({data.source_system}:{data.source_identifier})"
                )

            if was_saved:
                transaction.on_commit(lambda i=incident: i.publish_domain_events(self._event_bus))

            return result

        except Exception as e:
            logger.error(f"Failed to create incident from data: {e}", exc_info=True)
            return ProcessingResult.FAILED

    def _dto_to_model_data(self, data: IncidentData) -> dict[str, object]:
        status = self._map_status(data.status)
        severity = self._map_severity(data.severity)

        started_at = data.started_at
        if started_at and timezone.is_naive(started_at):
            started_at = timezone.make_aware(started_at, UTC)

        ended_at = data.ended_at
        if ended_at and timezone.is_naive(ended_at):
            ended_at = timezone.make_aware(ended_at, UTC)

        timeline_data = []
        for entry in data.timeline:
            if isinstance(entry, dict):
                ts = entry.get("timestamp")
                if isinstance(ts, datetime):
                    ts = ts.isoformat()
                timeline_data.append(
                    {
                        "timestamp": ts or timezone.now().isoformat(),
                        "description": entry.get("description", ""),
                        "author": entry.get("author"),
                    }
                )

        return {
            "title": (data.title or "")[:500],
            "description": (data.description or "")[:5000],
            "status": status,
            "severity": severity,
            "category": data.category,
            "source_system": data.source_system,
            "source_identifier": data.source_identifier,
            "source_url": data.source_url,
            "started_at": started_at,
            "ended_at": ended_at,
            "affected_services": list(data.affected_services),
            "affected_regions": list(data.affected_regions),
            "timeline": timeline_data,
            "tags": list(data.tags),
            "raw_data": dict(data.raw_payload),
        }

    def _merge_timelines(
        self,
        existing_timeline: list[dict[str, Any]],
        new_timeline: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Merge existing timeline entries with new ones, deduplicating by timestamp + description."""
        merged: dict[str, dict[str, Any]] = {}

        for entry in existing_timeline:
            if isinstance(entry, dict):
                ts = entry.get("timestamp", "")
                desc = entry.get("description", "")[:50]
                key = f"{ts}:{desc}"
                merged[key] = {
                    "timestamp": ts,
                    "description": entry.get("description", ""),
                    "author": entry.get("author"),
                }

        for entry in new_timeline:
            if isinstance(entry, dict):
                ts = entry.get("timestamp")
                if isinstance(ts, datetime):
                    ts = ts.isoformat()
                desc = entry.get("description", "")[:50]
                key = f"{ts}:{desc}"
                if key not in merged:
                    merged[key] = {
                        "timestamp": ts,
                        "description": entry.get("description", ""),
                        "author": entry.get("author"),
                    }

        result = sorted(merged.values(), key=lambda x: x.get("timestamp", ""))
        return result

    def _map_status(self, status_str: str) -> str:
        status_map = {
            "open": StatusChoices.OPEN,
            "investigating": StatusChoices.INVESTIGATING,
            "identified": StatusChoices.IDENTIFIED,
            "monitoring": StatusChoices.MONITORING,
            "resolved": StatusChoices.RESOLVED,
            "closed": StatusChoices.CLOSED,
        }
        return status_map.get(status_str.lower(), StatusChoices.OPEN)

    def _map_severity(self, severity_str: str) -> str:
        severity_map = {
            "critical": SeverityChoices.CRITICAL,
            "high": SeverityChoices.HIGH,
            "medium": SeverityChoices.MEDIUM,
            "low": SeverityChoices.LOW,
            "info": SeverityChoices.INFO,
        }
        return severity_map.get(severity_str.lower(), SeverityChoices.MEDIUM)
