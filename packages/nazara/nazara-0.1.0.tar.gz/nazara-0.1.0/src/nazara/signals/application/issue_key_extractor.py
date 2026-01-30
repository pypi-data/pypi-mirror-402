import hashlib
from dataclasses import dataclass
from typing import Any


@dataclass
class IssueIdentity:
    """Identity tuple for a TechnicalIssue."""

    provider: str
    issue_key: str
    environment: str
    service: str
    title: str | None = None
    message: str | None = None
    source_url: str | None = None


class IssueKeyExtractor:
    """
    Extract issue identity from ingestion payloads.

    Supports provider-specific extraction logic:
    - Sentry: sentry:{project_id}:{issue_id}
    - Datadog: datadog:monitor:{monitor_id}, datadog:apm:{service}:{signature}, etc.
    - Generic: Uses error fingerprint or title hash
    """

    def extract_from_payload(self, payload: dict[str, Any]) -> IssueIdentity | None:
        """
        Extract issue identity from an ingestion payload.

        Args:
            payload: Normalized payload dict from ingestor

        Returns:
            IssueIdentity if extraction succeeds, None otherwise
        """
        provider = payload.get("provider", "unknown")
        environment = payload.get("environment", "unknown")
        service = payload.get("service", "unknown")
        raw_data = payload.get("raw_payload", {})

        issue_key = self._compute_issue_key(
            provider=provider,
            service=service,
            title=payload.get("title"),
            raw_data=raw_data,
            error_fingerprint=payload.get("error_fingerprint"),
            source_identifier=payload.get("source_identifier"),
        )

        if not issue_key:
            return None

        return IssueIdentity(
            provider=provider,
            issue_key=issue_key,
            environment=environment,
            service=service,
            title=payload.get("title"),
            message=payload.get("error_message") or payload.get("description"),
            source_url=payload.get("source_url"),
        )

    def _compute_issue_key(
        self,
        provider: str,
        service: str,
        title: str | None,
        raw_data: dict[str, Any],
        error_fingerprint: str | None = None,
        source_identifier: str | None = None,
    ) -> str | None:
        if provider == "sentry":
            return self._compute_sentry_issue_key(
                raw_data=raw_data,
                service=service,
                title=title,
                error_fingerprint=error_fingerprint,
                source_identifier=source_identifier,
            )
        elif provider == "datadog":
            return self._compute_datadog_issue_key(
                raw_data=raw_data,
                service=service,
                title=title,
            )
        else:
            return self._compute_generic_issue_key(
                provider=provider,
                service=service,
                title=title,
                raw_data=raw_data,
                error_fingerprint=error_fingerprint,
            )

    def _compute_sentry_issue_key(
        self,
        raw_data: dict[str, Any],
        service: str,
        title: str | None,
        error_fingerprint: str | None = None,
        source_identifier: str | None = None,
    ) -> str | None:
        """
        Compute Sentry issue key.

        Format: sentry:{project_id}:{issue_id}
        Fallback: sentry:{project_slug}:{fingerprint}
        """
        project_id = raw_data.get("project_id") or raw_data.get("project", {}).get("id")
        issue_id = raw_data.get("issue_id") or raw_data.get("groupID") or raw_data.get("id")

        if project_id and issue_id:
            return f"sentry:{project_id}:{issue_id}"

        if source_identifier:
            parts = source_identifier.split(":")
            if len(parts) >= 3 and parts[0] == "sentry":
                return source_identifier

        fingerprint = error_fingerprint or self._get_fingerprint_from_raw(raw_data)
        if fingerprint:
            project_slug = raw_data.get("project", {}).get("slug") or service
            return f"sentry:{project_slug}:{fingerprint}"

        return self._generate_fallback_key("sentry", title, service)

    def _compute_datadog_issue_key(
        self,
        raw_data: dict[str, Any],
        service: str,
        title: str | None,
    ) -> str | None:
        """
        Compute Datadog issue key.

        Formats:
        - Monitor: datadog:monitor:{monitor_id}
        - APM: datadog:apm:{service}:{error_signature}
        - Event: datadog:event:{aggregation_key}
        """
        monitor_id = raw_data.get("monitor_id")
        if monitor_id:
            return f"datadog:monitor:{monitor_id}"

        span_data = raw_data.get("span", {})
        if span_data:
            svc = span_data.get("service", service)
            error_type = span_data.get("error_type") or span_data.get("resource", "unknown")
            return f"datadog:apm:{svc}:{error_type}"

        if raw_data.get("trace_id") or raw_data.get("span_id"):
            error_type = raw_data.get("error.type") or raw_data.get("resource_name", "unknown")
            return f"datadog:apm:{service}:{error_type}"

        aggregation_key = raw_data.get("aggregation_key")
        if aggregation_key:
            return f"datadog:event:{aggregation_key}"

        event_type = raw_data.get("event_type")
        if event_type:
            return f"datadog:event:{event_type}"

        return self._generate_fallback_key("datadog", title, service)

    def _compute_generic_issue_key(
        self,
        provider: str,
        service: str,
        title: str | None,
        raw_data: dict[str, Any],
        error_fingerprint: str | None = None,
    ) -> str | None:
        """Compute issue key for unknown/generic providers."""
        fingerprint = error_fingerprint or self._get_fingerprint_from_raw(raw_data)
        if fingerprint:
            return f"{provider}:{service}:{fingerprint}"

        return self._generate_fallback_key(provider or "generic", title, service)

    def _get_fingerprint_from_raw(self, raw_data: dict[str, Any]) -> str | None:
        fingerprint = raw_data.get("fingerprint")
        if fingerprint:
            if isinstance(fingerprint, list):
                return "-".join(str(f) for f in fingerprint)
            return str(fingerprint)
        return None

    def _generate_fallback_key(
        self,
        provider: str,
        title: str | None,
        service: str,
    ) -> str | None:
        """Generate a fallback issue key by hashing title + service."""
        if not title:
            return None

        key_input = f"{title}:{service}"
        hash_value = hashlib.md5(key_input.encode()).hexdigest()[:12]
        return f"{provider}:hash:{hash_value}"
