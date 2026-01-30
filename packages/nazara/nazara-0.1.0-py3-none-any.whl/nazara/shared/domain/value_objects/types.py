from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Status(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    IDENTIFIED = "identified"
    MONITORING = "monitoring"
    RESOLVED = "resolved"
    CLOSED = "closed"


class EventType(str, Enum):
    ERROR = "error"
    EXCEPTION = "exception"
    METRIC_ANOMALY = "metric_anomaly"
    LOG_PATTERN = "log_pattern"
    ALERT = "alert"
    DEPLOYMENT = "deployment"
    CONFIGURATION_CHANGE = "configuration_change"


class IngestorType(str, Enum):
    INCIDENT_IO_INCIDENT = "incident_io_incident"
    SENTRY_EVENT = "sentry_event"
    DATADOG_EVENT = "datadog_event"
    INTERCOM_CASE = "intercom_case"


class AuthType(str, Enum):
    OAUTH = "oauth"
    API_TOKEN = "api_token"
    WEBHOOK_SECRET = "webhook_secret"


class IngestionMode(str, Enum):
    WEBHOOK = "webhook"
    POLLING = "polling"
    HYBRID = "hybrid"


class RunStatus(str, Enum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OutputType(str, Enum):
    TECHNICAL_EVENT = "technical_event"
    TECHNICAL_ISSUE = "technical_issue"
    INCIDENT = "incident"
    CUSTOMER_CASE = "customer_case"


class ProcessingResult(str, Enum):
    CREATED = "created"
    UPDATED = "updated"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass(frozen=True)
class SourceInfo:
    system: str  # e.g., "slack", "sentry", "pagerduty"
    identifier: str  # External ID in the source system
    url: str | None = None  # Link back to source

    def __post_init__(self) -> None:
        if not self.system:
            raise ValueError("Source system cannot be empty")
        if not self.identifier:
            raise ValueError("Source identifier cannot be empty")


@dataclass(frozen=True)
class TimeRange:
    started_at: datetime
    ended_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.ended_at and self.ended_at < self.started_at:
            raise ValueError("End time cannot be before start time")

    @property
    def is_ongoing(self) -> bool:
        return self.ended_at is None

    @property
    def duration_seconds(self) -> float | None:
        if self.ended_at is None:
            return None
        return (self.ended_at - self.started_at).total_seconds()
