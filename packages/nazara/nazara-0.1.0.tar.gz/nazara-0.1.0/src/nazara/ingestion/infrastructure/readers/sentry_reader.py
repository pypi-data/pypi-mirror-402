import re
from datetime import datetime
from typing import Any, ClassVar

from django.utils import timezone

from nazara.ingestion.infrastructure.readers.base import BaseSignalReader
from nazara.shared.domain.dtos.signal_data import TechnicalEventData
from nazara.shared.domain.value_objects.types import AuthType, IngestionMode, OutputType
from nazara.signals.application.issue_key_extractor import IssueKeyExtractor

# Sentry level to severity mapping
SENTRY_SEVERITY_MAP: dict[str, str] = {
    "fatal": "critical",
    "error": "high",
    "warning": "medium",
    "info": "low",
    "debug": "info",
}


class SentryReader(BaseSignalReader[TechnicalEventData]):
    ingestor_type: ClassVar[str] = "sentry_event"
    output_type: ClassVar[OutputType] = OutputType.TECHNICAL_EVENT
    display_name: ClassVar[str] = "Sentry"
    description: ClassVar[str] = "Ingest errors and issues from Sentry"
    supported_modes: ClassVar[list[IngestionMode]] = [IngestionMode.WEBHOOK, IngestionMode.POLLING]
    supported_auth_types: ClassVar[list[AuthType]] = [AuthType.API_TOKEN, AuthType.WEBHOOK_SECRET]
    filter_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "organization_slug": {"type": "string"},
            "project_slugs": {"type": "array", "items": {"type": "string"}},
            "query": {"type": "string", "default": "is:unresolved"},
            "environments": {"type": "array", "items": {"type": "string"}},
            "level": {"type": "string", "enum": ["debug", "info", "warning", "error", "fatal"]},
            "base_url": {"type": "string", "default": "https://sentry.io"},
        },
        "required": ["organization_slug", "project_slugs"],
    }

    def __init__(self) -> None:
        self._extractor = IssueKeyExtractor()

    def get_source_system(self) -> str:
        return "sentry"

    def validate_payload(self, payload: dict[str, Any]) -> bool:
        if not super().validate_payload(payload):
            return False
        return bool(payload.get("event") or payload.get("data") or payload.get("action"))

    def parse_payload(self, raw_payload: dict[str, Any]) -> TechnicalEventData:
        event_data = raw_payload.get("event", {})
        issue = self._safe_get(raw_payload, "data", "issue", default={})

        if event_data:
            return self._parse_event(raw_payload, event_data)
        elif issue:
            return self._parse_issue(raw_payload, issue)
        else:
            return self._parse_generic(raw_payload)

    def _parse_event(
        self, raw_payload: dict[str, Any], event: dict[str, Any]
    ) -> TechnicalEventData:
        exception = self._safe_get(event, "exception", "values", default=[{}])[0]
        error_type = self._sanitize_string(exception.get("type", "")) or ""
        error_message = self._sanitize_string(exception.get("value", "")) or ""

        # Build stacktrace from last 10 frames
        frames = self._safe_get(exception, "stacktrace", "frames", default=[])
        stacktrace = "".join(
            f"  {self._sanitize_string(f.get('filename', '')) or ''}:"
            f"{f.get('lineno', '')} in {self._sanitize_string(f.get('function', '')) or ''}\n"
            for f in frames[-10:]
        )

        tags_dict = {t[0]: t[1] for t in event.get("tags", [])}
        project_id = event.get("project") or tags_dict.get("project_id", "unknown")
        service = (
            tags_dict.get("service", str(project_id) if isinstance(project_id, int) else project_id)
            or "unknown"
        )
        environment = tags_dict.get("environment", "production")

        tags = self._build_tags(raw_payload, tags_dict)
        occurred_at = self._parse_timestamp(event.get("timestamp")) or timezone.now()

        # Category from error type or default to "error"
        category = error_type.lower().replace(" ", "_") if error_type else "error"

        dto = TechnicalEventData(
            provider="sentry",
            issue_key="",  # Will be set below
            source_system=self.get_source_system(),
            source_identifier=event.get("event_id", ""),
            event_type="error",
            title=f"{error_type}: {error_message[:100]}",
            description=error_message,
            severity=SENTRY_SEVERITY_MAP.get(event.get("level", ""), "medium"),
            service=service,
            environment=environment,
            category=category,
            external_id=event.get("event_id"),
            source_url=raw_payload.get("url"),
            host=tags_dict.get("server_name"),
            transaction=event.get("transaction"),
            release=event.get("release"),
            occurred_at=occurred_at,
            error_type=error_type or None,
            error_message=error_message or None,
            error_stacktrace=stacktrace or None,
            error_fingerprint=self._safe_get(event, "fingerprint", default=[""])[0] or None,
            tags=tuple(tags),
            raw_payload=self._sanitize_data(raw_payload),
        )
        return self._with_issue_key(dto)

    def _parse_issue(
        self, raw_payload: dict[str, Any], issue: dict[str, Any]
    ) -> TechnicalEventData:
        metadata = issue.get("metadata", {})
        project = issue.get("project", {})
        title = self._sanitize_string(issue.get("title", "")) or ""
        description = self._sanitize_string(metadata.get("value", issue.get("culprit", ""))) or ""
        error_type = self._sanitize_string(metadata.get("type"))
        error_message = self._sanitize_string(metadata.get("value"))
        issue_id = str(issue.get("id", ""))
        service = project.get("slug", "unknown")

        tags = self._build_tags(raw_payload, {})
        occurred_at = self._parse_timestamp(issue.get("firstSeen")) or timezone.now()

        # Category from error type or default to "issue"
        category = error_type.lower().replace(" ", "_") if error_type else "issue"

        dto = TechnicalEventData(
            provider="sentry",
            issue_key="",
            source_system=self.get_source_system(),
            source_identifier=issue_id,
            event_type="error",
            title=title,
            description=description,
            severity=SENTRY_SEVERITY_MAP.get(issue.get("level", ""), "medium"),
            service=service,
            environment="production",
            category=category,
            external_id=issue_id,
            source_url=issue.get("permalink"),
            occurred_at=occurred_at,
            error_type=error_type,
            error_message=error_message,
            error_fingerprint=issue_id,
            tags=tuple(tags),
            raw_payload=self._sanitize_data(raw_payload),
        )
        return self._with_issue_key(dto)

    def _parse_generic(self, raw_payload: dict[str, Any]) -> TechnicalEventData:
        now = timezone.now()
        dto = TechnicalEventData(
            provider="sentry",
            issue_key="",
            source_system=self.get_source_system(),
            source_identifier=str(now.timestamp()),
            event_type="alert",
            title=raw_payload.get("action", "Sentry Alert"),
            description=str(raw_payload.get("data", {})),
            severity="medium",
            service="unknown",
            environment="production",
            category="alert",
            external_id=str(now.timestamp()),
            source_url=raw_payload.get("url"),
            occurred_at=now,
            tags=("sentry", "webhook"),
            raw_payload=self._sanitize_data(raw_payload),
        )
        return self._with_issue_key(dto)

    def _with_issue_key(self, dto: TechnicalEventData) -> TechnicalEventData:
        # Extract issue_key using centralized extractor
        payload_dict = {
            "provider": dto.provider,
            "external_id": dto.external_id,
            "source_system": dto.source_system,
            "source_identifier": dto.source_identifier,
            "service": dto.service,
            "environment": dto.environment,
            "error_fingerprint": dto.error_fingerprint,
        }
        identity = self._extractor.extract_from_payload(payload_dict)
        issue_key = identity.issue_key if identity else ""

        # Create new DTO with issue_key (frozen dataclass)
        return TechnicalEventData(
            provider=dto.provider,
            issue_key=issue_key,
            source_system=dto.source_system,
            source_identifier=dto.source_identifier,
            event_type=dto.event_type,
            title=dto.title,
            description=dto.description,
            severity=dto.severity,
            service=dto.service,
            environment=dto.environment,
            category=dto.category,
            external_id=dto.external_id,
            source_url=dto.source_url,
            host=dto.host,
            transaction=dto.transaction,
            release=dto.release,
            occurred_at=dto.occurred_at,
            error_type=dto.error_type,
            error_message=dto.error_message,
            error_stacktrace=dto.error_stacktrace,
            error_fingerprint=dto.error_fingerprint,
            tags=dto.tags,
            raw_payload=dto.raw_payload,
        )

    def _build_tags(self, payload: dict[str, Any], tags_dict: dict[str, str]) -> list[str]:
        tags = ["sentry"]
        action = payload.get("action")
        if action:
            tags.append(f"action:{action}")
        for key in ["environment", "browser", "os"]:
            if key in tags_dict:
                tags.append(f"{key}:{tags_dict[key]}")
        return tags

    def fetch_updates(
        self,
        credentials: str,
        filters: dict[str, Any],
        cursor: str | None,
        since: datetime | None,
    ) -> tuple[list[TechnicalEventData], str | None]:
        organization_slug = filters.get("organization_slug")
        project_slugs = filters.get("project_slugs", [])
        if not organization_slug or not project_slugs:
            raise ValueError("filters.organization_slug and filters.project_slugs are required")

        headers = {"Authorization": f"Bearer {credentials}", "Content-Type": "application/json"}
        all_payloads: list[TechnicalEventData] = []
        last_cursor: str | None = None

        for project_slug in project_slugs:
            payloads, new_cursor = self._fetch_project_issues(
                organization_slug, project_slug, headers, filters, cursor, since
            )
            all_payloads.extend(payloads)
            if new_cursor:
                last_cursor = new_cursor

        return all_payloads, last_cursor

    def _fetch_project_issues(
        self,
        organization_slug: str,
        project_slug: str,
        headers: dict[str, str],
        filters: dict[str, Any],
        cursor: str | None,
        since: datetime | None,
    ) -> tuple[list[TechnicalEventData], str | None]:
        import requests

        base_url = filters.get("base_url", "https://sentry.io")
        url = f"{base_url}/api/0/projects/{organization_slug}/{project_slug}/issues/"

        params: dict[str, Any] = {"statsPeriod": "24h"}

        # Build search query
        query_parts = []
        base_query = filters.get("query", "is:unresolved")
        if base_query:
            query_parts.append(base_query)
        environments = filters.get("environments", [])
        if environments:
            query_parts.append(" ".join(f"environment:{env}" for env in environments))
        level = filters.get("level")
        if level:
            query_parts.append(f"level:{level}")
        if since and not cursor:
            query_parts.append(f"lastSeen:>={since.strftime('%Y-%m-%dT%H:%M:%S')}")
        if query_parts:
            params["query"] = " ".join(query_parts)
        if cursor:
            params["cursor"] = cursor

        results: list[TechnicalEventData] = []
        next_cursor: str | None = None

        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()

            for issue in response.json():
                raw_payload = {"data": {"issue": issue}}
                results.append(self._parse_issue(raw_payload, issue))

            next_cursor = self._extract_cursor(response.headers.get("Link", ""))
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to fetch Sentry issues: {e}") from e

        return results, next_cursor

    def _extract_cursor(self, link_header: str) -> str | None:
        if not link_header:
            return None
        for part in link_header.split(","):
            if 'rel="next"' in part and 'results="true"' in part:
                match = re.search(r'cursor="([^"]+)"', part)
                if match:
                    return match.group(1)
        return None
