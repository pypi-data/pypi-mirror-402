from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class TechnicalEventData:
    # Identity (required)
    provider: str
    issue_key: str
    source_system: str
    source_identifier: str

    # Event details (required)
    event_type: str
    title: str
    description: str
    severity: str
    service: str
    environment: str
    category: str | None = None

    # Optional context
    external_id: str | None = None
    source_url: str | None = None
    host: str | None = None
    transaction: str | None = None
    release: str | None = None
    occurred_at: datetime | None = None

    # Optional error details
    error_type: str | None = None
    error_message: str | None = None
    error_stacktrace: str | None = None
    error_fingerprint: str | None = None

    # Metadata
    tags: tuple[str, ...] = ()
    raw_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CustomerCaseData:
    # Identity (required)
    source_system: str
    source_identifier: str
    customer_id: str

    # Case details (required)
    title: str
    description: str

    # Optional with defaults
    status: str = "open"
    severity: str = "medium"
    priority: int = 2
    category: str | None = None

    # Optional customer info
    customer_email: str | None = None
    customer_name: str | None = None
    source_url: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None

    # Metadata
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    conversation: tuple[dict[str, Any], ...] = ()
    raw_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class IncidentData:
    # Identity (required)
    source_system: str
    source_identifier: str

    # Incident details (required)
    title: str
    description: str

    # Optional with defaults
    status: str = "open"
    severity: str = "high"
    category: str | None = None

    # Optional
    source_url: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None

    # Optional impact
    affected_services: tuple[str, ...] = ()
    affected_regions: tuple[str, ...] = ()
    timeline: tuple[dict[str, Any], ...] = ()

    # Metadata
    tags: tuple[str, ...] = ()
    raw_payload: dict[str, Any] = field(default_factory=dict)
