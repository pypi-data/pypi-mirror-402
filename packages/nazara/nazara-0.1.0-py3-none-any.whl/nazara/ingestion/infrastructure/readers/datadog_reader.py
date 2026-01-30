import json
from datetime import datetime
from typing import Any, ClassVar

from django.utils import timezone

from nazara.ingestion.infrastructure.readers.base import BaseSignalReader
from nazara.shared.domain.dtos.signal_data import TechnicalEventData
from nazara.shared.domain.value_objects.types import AuthType, IngestionMode, OutputType
from nazara.signals.application.issue_key_extractor import IssueKeyExtractor

# Datadog-specific mappings
DD_MONITOR_TYPE_MAP: dict[str, str] = {
    "metric alert": "metric_anomaly",
    "query alert": "metric_anomaly",
    "service check": "alert",
    "event alert": "alert",
    "log alert": "log_pattern",
    "apm": "error",
    "trace-analytics alert": "error",
    "composite": "alert",
    "synthetics alert": "alert",
    "rum alert": "error",
    "slo alert": "alert",
    "error tracking alert": "error",
}

DD_STATE_SEVERITY_MAP: dict[str, str] = {
    "Alert": "critical",
    "Warn": "high",
    "No Data": "medium",
    "OK": "info",
}

DD_PRIORITY_SEVERITY_MAP: dict[str, str] = {
    "p1": "critical",
    "p2": "high",
    "p3": "medium",
    "p4": "low",
    "p5": "info",
    "low": "info",
    "normal": "medium",
    "high": "high",
}


class DatadogReader(BaseSignalReader[TechnicalEventData]):
    ingestor_type: ClassVar[str] = "datadog_event"
    output_type: ClassVar[OutputType] = OutputType.TECHNICAL_EVENT
    display_name: ClassVar[str] = "Datadog"
    description: ClassVar[str] = "Ingest monitors, APM errors, and events from Datadog"
    supported_modes: ClassVar[list[IngestionMode]] = [IngestionMode.WEBHOOK, IngestionMode.POLLING]
    supported_auth_types: ClassVar[list[AuthType]] = [AuthType.API_TOKEN]
    filter_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "sources": {
                "type": "array",
                "items": {"type": "string", "enum": ["monitors", "spans", "events"]},
                "default": ["monitors", "spans", "events"],
            },
            "services": {"type": "array", "items": {"type": "string"}},
            "tags": {"type": "array", "items": {"type": "string"}},
            "monitor_tags": {"type": "array", "items": {"type": "string"}},
            "env": {"type": "string"},
            "app_key": {"type": "string"},
        },
    }
    requires_package: ClassVar[str | None] = "datadog-api-client"

    def __init__(self) -> None:
        self._extractor = IssueKeyExtractor()

    def get_source_system(self) -> str:
        return "datadog"

    def validate_payload(self, payload: dict[str, Any]) -> bool:
        if not super().validate_payload(payload):
            return False
        return bool(
            payload.get("alert_type")
            or payload.get("event_type")
            or payload.get("id")
            or payload.get("monitor_id")
            or payload.get("trace_id")
        )

    def parse_payload(self, raw_payload: dict[str, Any]) -> TechnicalEventData:
        if "alert_type" in raw_payload or "monitor_id" in raw_payload:
            return self._parse_monitor_alert(raw_payload)
        elif "trace_id" in raw_payload or "span_id" in raw_payload:
            return self._parse_span(raw_payload)
        elif "event_type" in raw_payload or "title" in raw_payload:
            return self._parse_event(raw_payload)
        else:
            return self._parse_generic(raw_payload)

    def _parse_monitor_alert(self, raw: dict[str, Any]) -> TechnicalEventData:
        monitor_id = raw.get("monitor_id", "")
        alert_type = raw.get("alert_type", "")
        alert_status = raw.get("alert_status", "")

        tags = self._parse_tags(raw.get("tags", ""))
        service, environment = self._extract_service_env(tags)

        severity = DD_PRIORITY_SEVERITY_MAP.get(raw.get("priority", "").lower(), "medium")
        if alert_status == "Recovered":
            severity = "info"

        event_type = "error" if "error" in alert_type.lower() else "alert"
        external_id = f"monitor:{monitor_id}" if monitor_id else str(timezone.now().timestamp())

        # Derive category from alert type or monitor type
        category = alert_type.lower().replace(" ", "_") if alert_type else "monitor_alert"

        return self._with_issue_key(
            TechnicalEventData(
                provider="datadog",
                issue_key="",
                source_system=self.get_source_system(),
                source_identifier=external_id,
                event_type=event_type,
                title=raw.get("title") or raw.get("monitor_name") or f"Datadog Alert: {alert_type}",
                description=raw.get("body", ""),
                severity=severity,
                service=service,
                environment=environment,
                category=category,
                external_id=external_id,
                source_url=raw.get("url"),
                host=raw.get("hostname"),
                occurred_at=self._parse_timestamp(raw.get("date")) or timezone.now(),
                error_type=alert_type if event_type == "error" else None,
                error_message=raw.get("body") if event_type == "error" else None,
                error_fingerprint=f"dd:{monitor_id}" if monitor_id else None,
                tags=tuple(["datadog"] + tags),
                raw_payload=raw,
            )
        )

    def _parse_span(self, raw: dict[str, Any]) -> TechnicalEventData:
        # Handle nested attributes from API
        attrs = raw.get("attributes", {})
        if attrs:
            raw = {**raw, **attrs}

        trace_id = raw.get("trace_id", "")
        span_id = raw.get("span_id", "")
        service = raw.get("service", "unknown")
        resource = raw.get("resource_name", raw.get("resource", ""))
        operation = raw.get("operation_name", raw.get("name", ""))
        env = raw.get("env", "production")

        meta = raw.get("meta", {})
        error_msg = raw.get("error.message", meta.get("error.msg", ""))
        error_type = raw.get("error.type", meta.get("error.type", ""))
        error_stack = raw.get("error.stack", meta.get("error.stack", ""))
        host = raw.get("host", meta.get("host", ""))

        external_id = f"trace:{trace_id}:span:{span_id}" if span_id else f"trace:{trace_id}"

        # Category for APM errors: use error_type or default to "apm_error"
        category = error_type.lower().replace(" ", "_") if error_type else "apm_error"

        return self._with_issue_key(
            TechnicalEventData(
                provider="datadog",
                issue_key="",
                source_system=self.get_source_system(),
                source_identifier=external_id,
                event_type="error",
                title=f"[APM Error] {service}: {resource or operation}",
                description=error_msg or f"Error in {operation}",
                severity="high",
                service=service,
                environment=env,
                category=category,
                external_id=external_id,
                source_url=f"https://app.datadoghq.com/apm/trace/{trace_id}" if trace_id else None,
                host=host or None,
                transaction=resource or operation or None,
                release=raw.get("version"),
                occurred_at=self._parse_timestamp(raw.get("timestamp", raw.get("start")))
                or timezone.now(),
                error_type=error_type or None,
                error_message=error_msg or None,
                error_stacktrace=error_stack or None,
                error_fingerprint=f"dd:apm:{service}:{error_type}" if error_type else None,
                tags=("datadog", "apm", f"service:{service}", f"env:{env}"),
                raw_payload=raw,
            )
        )

    def _parse_event(self, raw: dict[str, Any]) -> TechnicalEventData:
        event_id = str(raw.get("id", timezone.now().timestamp()))
        event_type_str = raw.get("event_type", "")

        tags = raw.get("tags", [])
        if isinstance(tags, str):
            tags = tags.split(",")
        service, environment = self._extract_service_env(tags)

        # Map event type
        event_type = "alert"
        if "error" in event_type_str.lower() or "exception" in event_type_str.lower():
            event_type = "error"
        elif "deploy" in event_type_str.lower():
            event_type = "deployment"

        severity = DD_PRIORITY_SEVERITY_MAP.get(raw.get("priority", "normal").lower(), "medium")

        # Category from event type string
        category = event_type_str.lower().replace(" ", "_") if event_type_str else event_type

        return self._with_issue_key(
            TechnicalEventData(
                provider="datadog",
                issue_key="",
                source_system=self.get_source_system(),
                source_identifier=event_id,
                event_type=event_type,
                title=raw.get("title", ""),
                description=raw.get("text", ""),
                severity=severity,
                service=service,
                environment=environment,
                category=category,
                external_id=event_id,
                source_url=raw.get("url"),
                host=raw.get("host"),
                occurred_at=self._parse_timestamp(raw.get("date_happened")) or timezone.now(),
                tags=tuple(["datadog"] + list(tags)),
                raw_payload=raw,
            )
        )

    def _parse_generic(self, raw: dict[str, Any]) -> TechnicalEventData:
        now = timezone.now()
        external_id = str(now.timestamp())

        return self._with_issue_key(
            TechnicalEventData(
                provider="datadog",
                issue_key="",
                source_system=self.get_source_system(),
                source_identifier=external_id,
                event_type="alert",
                title=raw.get("title", "Datadog Event"),
                description=str(raw),
                severity="medium",
                service="unknown",
                environment="production",
                category="generic",
                external_id=external_id,
                occurred_at=now,
                tags=("datadog",),
                raw_payload=raw,
            )
        )

    def _with_issue_key(self, dto: TechnicalEventData) -> TechnicalEventData:
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

    def _parse_tags(self, tags: str | list[str]) -> list[str]:
        if isinstance(tags, str):
            return [t.strip() for t in tags.split(",") if t.strip()]
        return list(tags) if tags else []

    def _extract_service_env(self, tags: list[str]) -> tuple[str, str]:
        service = "unknown"
        environment = "production"
        for tag in tags:
            if isinstance(tag, str):
                if tag.startswith("service:"):
                    service = tag.split(":", 1)[1]
                elif tag.startswith("env:"):
                    environment = tag.split(":", 1)[1]
        return service, environment

    def fetch_updates(
        self,
        credentials: str,
        filters: dict[str, Any],
        cursor: str | None,
        since: datetime | None,
    ) -> tuple[list[TechnicalEventData], str | None]:
        try:
            from datadog_api_client import ApiClient, Configuration
        except ImportError as e:
            raise ImportError(
                "datadog-api-client package required. Install: pip install datadog-api-client"
            ) from e

        # Parse credentials
        if ":" in credentials:
            api_key, app_key = credentials.split(":", 1)
        else:
            api_key = credentials
            app_key = filters.get("app_key", "")

        configuration = Configuration()
        configuration.api_key["apiKeyAuth"] = api_key
        configuration.api_key["appKeyAuth"] = app_key

        cursor_data = {}
        if cursor:
            try:
                cursor_data = json.loads(cursor)
            except json.JSONDecodeError:
                cursor_data = {"events": cursor}

        sources = filters.get("sources", ["monitors", "spans", "events"])
        if isinstance(sources, str):
            sources = [s.strip() for s in sources.split(",")]

        results: list[TechnicalEventData] = []
        new_cursor_data: dict[str, str] = {}
        end_time = int(timezone.now().timestamp())

        with ApiClient(configuration) as api_client:
            if "monitors" in sources:
                results.extend(self._fetch_monitors(api_client, filters))
                new_cursor_data["monitors"] = str(end_time)

            if "spans" in sources:
                spans, spans_cursor = self._fetch_spans(
                    api_client, filters, cursor_data.get("spans"), since
                )
                results.extend(spans)
                new_cursor_data["spans"] = spans_cursor or str(end_time)

            if "events" in sources:
                events, events_cursor = self._fetch_events(
                    api_client, filters, cursor_data.get("events"), since
                )
                results.extend(events)
                new_cursor_data["events"] = events_cursor or str(end_time)

        return results, json.dumps(new_cursor_data)

    def _fetch_monitors(self, api_client: Any, filters: dict[str, Any]) -> list[TechnicalEventData]:
        from datadog_api_client.v1.api.monitors_api import MonitorsApi

        monitors_api = MonitorsApi(api_client)
        kwargs: dict[str, Any] = {"group_states": "alert,warn"}

        monitor_tags = filters.get("monitor_tags", [])
        if monitor_tags:
            kwargs["monitor_tags"] = (
                ",".join(monitor_tags) if isinstance(monitor_tags, list) else monitor_tags
            )

        tags = filters.get("tags", [])
        if tags:
            kwargs["tags"] = ",".join(tags) if isinstance(tags, list) else tags

        results: list[TechnicalEventData] = []
        try:
            response = monitors_api.list_monitors(**kwargs)
            for monitor in response:
                monitor_dict = monitor.to_dict() if hasattr(monitor, "to_dict") else monitor
                if monitor_dict.get("overall_state") in ("Alert", "Warn", "No Data"):
                    results.append(self._parse_monitor_state(monitor_dict))
        except Exception:
            pass  # Log but don't fail

        return results

    def _parse_monitor_state(self, raw: dict[str, Any]) -> TechnicalEventData:
        monitor_id = raw.get("id", "")
        monitor_type = raw.get("type", "")
        overall_state = raw.get("overall_state", "")

        tags = raw.get("tags", [])
        service, environment = self._extract_service_env(tags)

        severity = DD_STATE_SEVERITY_MAP.get(overall_state, "medium")
        event_type = DD_MONITOR_TYPE_MAP.get(monitor_type.lower(), "alert")
        external_id = f"monitor:{monitor_id}"

        # Category from monitor type
        category = monitor_type.lower().replace(" ", "_") if monitor_type else "monitor"

        return self._with_issue_key(
            TechnicalEventData(
                provider="datadog",
                issue_key="",
                source_system=self.get_source_system(),
                source_identifier=external_id,
                event_type=event_type,
                title=f"[{overall_state}] {raw.get('name', '')}",
                description=raw.get("message", raw.get("query", "")),
                severity=severity,
                service=service,
                environment=environment,
                category=category,
                external_id=external_id,
                source_url=f"https://app.datadoghq.com/monitors/{monitor_id}",
                occurred_at=timezone.now(),
                error_type=monitor_type or None,
                error_message=raw.get("message") or None,
                error_fingerprint=f"dd:monitor:{monitor_id}",
                tags=tuple(
                    ["datadog", f"monitor_type:{monitor_type}", f"state:{overall_state}"] + tags
                ),
                raw_payload=raw,
            )
        )

    def _fetch_spans(
        self,
        api_client: Any,
        filters: dict[str, Any],
        cursor: str | None,
        since: datetime | None,
    ) -> tuple[list[TechnicalEventData], str | None]:
        from datadog_api_client.v2.api.spans_api import SpansApi
        from datadog_api_client.v2.model.spans_list_request import SpansListRequest
        from datadog_api_client.v2.model.spans_list_request_attributes import (
            SpansListRequestAttributes,
        )
        from datadog_api_client.v2.model.spans_list_request_data import SpansListRequestData
        from datadog_api_client.v2.model.spans_list_request_page import SpansListRequestPage
        from datadog_api_client.v2.model.spans_list_request_type import SpansListRequestType
        from datadog_api_client.v2.model.spans_query_filter import SpansQueryFilter
        from datadog_api_client.v2.model.spans_sort import SpansSort

        spans_api = SpansApi(api_client)

        from_time = cursor or (since.strftime("%Y-%m-%dT%H:%M:%SZ") if since else "now-1h")

        query_parts = ["status:error"]
        services = filters.get("services", [])
        if services:
            if isinstance(services, list) and services:
                query_parts.append(f"({' OR '.join(f'service:{s}' for s in services)})")
            elif isinstance(services, str):
                query_parts.append(f"service:{services}")
        env = filters.get("env")
        if env:
            query_parts.append(f"env:{env}")

        results: list[TechnicalEventData] = []
        new_cursor = cursor

        try:
            body = SpansListRequest(
                data=SpansListRequestData(
                    attributes=SpansListRequestAttributes(
                        filter=SpansQueryFilter(
                            query=" ".join(query_parts), _from=from_time, to="now"
                        ),
                        page=SpansListRequestPage(limit=100),
                        sort=SpansSort.TIMESTAMP_ASCENDING,
                    ),
                    type=SpansListRequestType.SEARCH_REQUEST,
                )
            )
            response = spans_api.list_spans(body=body)
            for span in response.data or []:
                span_dict = span.to_dict() if hasattr(span, "to_dict") else span
                results.append(self._parse_span(span_dict))
            new_cursor = str(int(timezone.now().timestamp()))
        except Exception:
            pass

        return results, new_cursor

    def _fetch_events(
        self,
        api_client: Any,
        filters: dict[str, Any],
        cursor: str | None,
        since: datetime | None,
    ) -> tuple[list[TechnicalEventData], str | None]:
        from datadog_api_client.v1.api.events_api import EventsApi

        events_api = EventsApi(api_client)

        start_time = (
            int(cursor)
            if cursor
            else (int(since.timestamp()) if since else int(timezone.now().timestamp()) - 3600)
        )
        end_time = int(timezone.now().timestamp())

        kwargs: dict[str, Any] = {"start": start_time, "end": end_time}
        tags = filters.get("tags", [])
        if tags:
            kwargs["tags"] = ",".join(tags) if isinstance(tags, list) else tags

        results: list[TechnicalEventData] = []
        try:
            response = events_api.list_events(**kwargs)
            for event in response.events or []:
                event_dict = event.to_dict() if hasattr(event, "to_dict") else vars(event)
                results.append(self._parse_event(event_dict))
        except Exception:
            pass

        return results, str(end_time)
