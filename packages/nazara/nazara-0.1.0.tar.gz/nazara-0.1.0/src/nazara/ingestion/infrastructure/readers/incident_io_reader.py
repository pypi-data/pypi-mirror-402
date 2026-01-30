from datetime import datetime
from typing import Any, ClassVar

from nazara.ingestion.infrastructure.readers.base import BaseSignalReader
from nazara.shared.domain.dtos.signal_data import IncidentData
from nazara.shared.domain.value_objects.types import AuthType, IngestionMode, OutputType


class IncidentIoReader(BaseSignalReader[IncidentData]):
    ingestor_type: ClassVar[str] = "incident_io_incident"
    output_type: ClassVar[OutputType] = OutputType.INCIDENT
    display_name: ClassVar[str] = "Incident.io"
    description: ClassVar[str] = "Ingest incidents from Incident.io"
    supported_modes: ClassVar[list[IngestionMode]] = [
        IngestionMode.WEBHOOK,
        IngestionMode.POLLING,
        IngestionMode.HYBRID,
    ]
    supported_auth_types: ClassVar[list[AuthType]] = [
        AuthType.API_TOKEN,
        AuthType.WEBHOOK_SECRET,
    ]
    filter_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "page_size": {"type": "integer", "minimum": 1, "maximum": 100, "default": 50},
        },
    }
    requires_package: ClassVar[str | None] = "python-incidentio-client"

    def get_source_system(self) -> str:
        return "incident_io"

    def validate_payload(self, payload: dict[str, Any]) -> bool:
        if not super().validate_payload(payload):
            return False
        return bool(payload.get("event_type") or payload.get("incident"))

    def parse_payload(self, raw_payload: dict[str, Any]) -> IncidentData:
        # Extract incident object from various formats
        if "incident" in raw_payload:
            incident = raw_payload["incident"]
        else:
            incident = raw_payload

        event_type = raw_payload.get("event_type")
        tags = ["incident_io"]
        if event_type:
            tags.append(f"event:{event_type}")

        # Extract nested fields
        status_category = self._safe_get(incident, "incident_status", "category", default="triage")
        severity_name = self._safe_get(incident, "severity", "name", default="")
        incident_type = self._safe_get(incident, "incident_type", "name")
        mode = incident.get("mode")

        if incident_type:
            tags.append(f"type:{incident_type}")
        if severity_name:
            tags.append(f"severity:{severity_name}")
        if mode:
            tags.append(f"mode:{mode}")

        # Build permalink
        incident_id = incident.get("id", "")
        permalink = incident.get("permalink", "")
        if not permalink and incident_id:
            org_slug = self._safe_get(incident, "organisation", "slug", default="")
            if org_slug:
                permalink = f"https://app.incident.io/{org_slug}/incidents/{incident_id}"

        # Extract timeline
        timeline = tuple(
            {
                "timestamp": self._parse_timestamp(u.get("created_at")),
                "description": u.get("message", ""),
                "author": self._safe_get(u, "updater", "name", default="system"),
            }
            for u in incident.get("incident_updates", [])
        )

        # Extract affected services from custom fields
        affected_services: list[str] = []
        for field in incident.get("custom_field_values", []):
            field_name = self._safe_get(field, "custom_field", "name", default="").lower()
            if "service" in field_name or "component" in field_name:
                for val in field.get("values", []):
                    if isinstance(val, dict):
                        affected_services.append(val.get("label", val.get("value", "")))
                    else:
                        affected_services.append(str(val))

        status = self._map_status(status_category)
        started_at = self._parse_timestamp(incident.get("created_at"))
        ended_at = None
        if status in ("resolved", "closed"):
            ended_at = self._parse_timestamp(incident.get("resolved_at"))

        return IncidentData(
            source_system=self.get_source_system(),
            source_identifier=str(incident_id),
            title=incident.get("name", ""),
            description=incident.get("summary", ""),
            status=status,
            severity=self._map_severity(severity_name),
            category=incident_type,
            source_url=permalink or None,
            started_at=started_at,
            ended_at=ended_at,
            affected_services=tuple(affected_services),
            affected_regions=(),
            timeline=timeline,
            tags=tuple(tags),
            raw_payload=raw_payload,
        )

    def fetch_updates(
        self,
        credentials: str,
        filters: dict[str, Any],
        cursor: str | None,
        since: datetime | None,
    ) -> tuple[list[IncidentData], str | None]:
        try:
            from incident_io_client import AuthenticatedClient
            from incident_io_client.api.incidents_v2 import incidents_v2_list
        except ImportError as e:
            raise ImportError(
                "python-incidentio-client package required. Install: pip install python-incidentio-client"
            ) from e

        client = AuthenticatedClient(base_url="https://api.incident.io", token=credentials)
        page_size = filters.get("page_size", 50)

        with client as c:
            response = incidents_v2_list.sync_detailed(
                client=c,
                page_size=page_size,
                after=cursor if cursor else None,
            )

        results: list[IncidentData] = []
        new_cursor = None

        if response.parsed is not None:
            for incident in response.parsed.incidents:
                incident_dict = incident.to_dict() if hasattr(incident, "to_dict") else {}
                results.append(self.parse_payload({"incident": incident_dict}))

            if response.parsed.pagination_meta:
                new_cursor = response.parsed.pagination_meta.after

        return results, new_cursor
