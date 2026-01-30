from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime
from typing import Any

from django.db import models
from django.utils import timezone

from nazara.shared.enrichment_input import EnrichmentInput
from nazara.shared.event_bus.contracts import HasDomainEventsMixin
from nazara.shared.infrastructure.django.models import BaseModel
from nazara.signals.domain.events import SignalCreatedEvent, SignalUpdatedEvent


class SeverityChoices(models.TextChoices):
    CRITICAL = "critical", "Critical"
    HIGH = "high", "High"
    MEDIUM = "medium", "Medium"
    LOW = "low", "Low"
    INFO = "info", "Info"


class StatusChoices(models.TextChoices):
    OPEN = "open", "Open"
    INVESTIGATING = "investigating", "Investigating"
    IDENTIFIED = "identified", "Identified"
    MONITORING = "monitoring", "Monitoring"
    RESOLVED = "resolved", "Resolved"
    CLOSED = "closed", "Closed"


class EventTypeChoices(models.TextChoices):
    ERROR = "error", "Error"
    EXCEPTION = "exception", "Exception"
    METRIC_ANOMALY = "metric_anomaly", "Metric Anomaly"
    LOG_PATTERN = "log_pattern", "Log Pattern"
    ALERT = "alert", "Alert"
    DEPLOYMENT = "deployment", "Deployment"
    CONFIGURATION_CHANGE = "configuration_change", "Configuration Change"


class PriorityChoices(models.IntegerChoices):
    URGENT = 0, "Urgent"  # P0 - Drop everything, SLA critical
    HIGH = 1, "High"  # P1 - Handle today
    NORMAL = 2, "Normal"  # P2 - Handle this week
    LOW = 3, "Low"  # P3 - When available


class IssueStatusChoices(models.TextChoices):
    ACTIVE = "active", "Active"
    RESOLVED = "resolved", "Resolved"


class Incident(HasDomainEventsMixin, BaseModel):
    """
    Aggregate root for production incidents.

    Represents a system-wide or high-impact failure.
    Contains timelines, severity, impact and root-cause context.
    """

    SIGNAL_TYPE = "Incident"

    # Incident details
    title = models.CharField(max_length=500)
    description = models.TextField()
    status = models.CharField(
        max_length=20, choices=StatusChoices.choices, default=StatusChoices.INVESTIGATING
    )
    severity = models.CharField(
        max_length=20, choices=SeverityChoices.choices, default=SeverityChoices.HIGH
    )
    category = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        help_text="Incident category/type from source system",
    )

    # Source information
    source_system = models.CharField(max_length=100, db_index=True)
    source_identifier = models.CharField(max_length=255)
    source_url = models.URLField(blank=True, null=True)

    # Time tracking
    started_at = models.DateTimeField(db_index=True, null=True, blank=True)
    ended_at = models.DateTimeField(blank=True, null=True)

    # Impact
    affected_services = models.JSONField(default=list, blank=True)
    affected_users_count = models.PositiveIntegerField(null=True, blank=True)
    affected_regions = models.JSONField(default=list, blank=True)
    impact_description = models.TextField(blank=True, null=True)

    # Root cause
    root_cause_description = models.TextField(blank=True, null=True)
    root_cause_category = models.CharField(max_length=100, blank=True, null=True)
    root_cause_identified_at = models.DateTimeField(blank=True, null=True)

    # Timeline (JSON array of {timestamp, description, author})
    timeline = models.JSONField(default=list, blank=True)

    # Metadata
    tags = models.JSONField(default=list, blank=True)

    # Raw data from source system
    raw_data = models.JSONField(default=dict, blank=True)

    # Content hash for change detection
    content_hash = models.CharField(max_length=64, blank=True, null=True, db_index=True)

    class Meta:
        app_label = "nazara_signals"
        db_table = "nazara_incident"
        verbose_name = "Incident"
        verbose_name_plural = "Incidents"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "severity"]),
            models.Index(fields=["source_system", "source_identifier"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["source_system", "source_identifier"],
                name="unique_incident_source",
            ),
        ]

    def __str__(self) -> str:
        return self.title

    @classmethod
    def create(cls, **kwargs: Any) -> Incident:
        """
        Factory method to create a new Incident.

        Registers SignalCreatedEvent at the moment of creation.
        """
        instance = cls(**kwargs)
        instance.register_domain_event(
            SignalCreatedEvent(signal_type=cls.SIGNAL_TYPE, signal_id=instance.id)
        )
        return instance

    def apply_changes(self, **updates: Any) -> tuple[str, ...]:
        """
        Apply field updates and register SignalUpdatedEvent if any fields changed.

        Returns:
            Tuple of changed field names.
        """
        changed_fields: list[str] = []
        for field, value in updates.items():
            current = getattr(self, field, None)
            if current != value:
                setattr(self, field, value)
                changed_fields.append(field)

        if changed_fields:
            self._touch()
            self.register_domain_event(
                SignalUpdatedEvent(
                    signal_type=self.SIGNAL_TYPE,
                    signal_id=self.id,
                    changed_fields=tuple(changed_fields),
                )
            )

        return tuple(changed_fields)

    def add_timeline_entry(
        self,
        description: str,
        timestamp: datetime | None = None,
        author: str | None = None,
    ) -> None:
        entry = {
            "timestamp": (timestamp or timezone.now()).isoformat(),
            "description": description,
            "author": author,
        }
        if self.timeline is None:
            self.timeline = []
        self.timeline.append(entry)
        self.timeline.sort(key=lambda e: e.get("timestamp", ""))
        self._touch()

    def update_status(self, new_status: str) -> None:
        old_status = self.status
        self.status = new_status
        self.add_timeline_entry(f"Status changed from {old_status} to {new_status}")

    def set_root_cause(
        self,
        description: str,
        category: str | None = None,
    ) -> None:
        self.root_cause_description = description
        self.root_cause_category = category
        self.root_cause_identified_at = timezone.now()
        self.add_timeline_entry(f"Root cause identified: {description}")

    def resolve(self, ended_at: datetime | None = None) -> None:
        self.status = StatusChoices.RESOLVED
        self.ended_at = ended_at or timezone.now()
        self.add_timeline_entry("Incident resolved")

    def add_affected_service(self, service: str) -> None:
        if self.affected_services is None:
            self.affected_services = []
        if service not in self.affected_services:
            self.affected_services.append(service)
            self._touch()

    def set_impact(
        self,
        description: str,
        affected_users: int | None = None,
    ) -> None:
        self.impact_description = description
        self.affected_users_count = affected_users
        self._touch()

    def _touch(self) -> None:
        self.updated_at = timezone.now()
        self.version += 1

    def compute_content_hash(self) -> str:
        """
        Compute a hash of content fields for change detection.

        Used to prevent unnecessary database updates when the same
        data is ingested multiple times.
        """
        content = {
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "severity": self.severity,
            "source_url": self.source_url,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "affected_services": self.affected_services,
            "affected_users_count": self.affected_users_count,
            "affected_regions": self.affected_regions,
            "impact_description": self.impact_description,
            "root_cause_description": self.root_cause_description,
            "root_cause_category": self.root_cause_category,
            "root_cause_identified_at": (
                self.root_cause_identified_at.isoformat() if self.root_cause_identified_at else None
            ),
            "timeline": self.timeline,
            "tags": self.tags,
        }
        serialized = json.dumps(content, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()

    @property
    def is_ongoing(self) -> bool:
        return self.ended_at is None

    @property
    def duration_seconds(self) -> float | None:
        if not self.started_at:
            return None
        end = self.ended_at or timezone.now()
        return (end - self.started_at).total_seconds()

    def to_enrichment_input(self) -> EnrichmentInput:
        """
        Build enrichment input with all relevant incident data.

        Content includes:
        - description (primary)
        - impact_description (if present)
        - root_cause_description (if present)
        - timeline summary (count + last 5 entries)

        Metadata includes:
        - severity, status, category, source_system
        - affected_services, affected_regions, affected_users_count

        Context includes:
        - tags, started_at, ended_at
        """
        # Build rich content
        content_parts = [self.description]

        if self.impact_description:
            content_parts.append(f"Impact: {self.impact_description}")

        if self.root_cause_description:
            content_parts.append(f"Root Cause: {self.root_cause_description}")

        # Add timeline summary (count + last 5 entries)
        if self.timeline:
            timeline_lines = [f"Timeline ({len(self.timeline)} entries, showing last 5):"]
            for entry in self.timeline[-5:]:
                timestamp = entry.get("timestamp", "")
                description = entry.get("description", "")
                if description:
                    timeline_lines.append(f"- {timestamp}: {description}")
            content_parts.append("\n".join(timeline_lines))

        # Build metadata (convert enums to strings for consistent hashing)
        severity = self.severity.value if hasattr(self.severity, "value") else self.severity
        status = self.status.value if hasattr(self.status, "value") else self.status
        metadata: dict[str, Any] = {
            "severity": severity,
            "status": status,
            "source_system": self.source_system,
        }

        if self.category:
            metadata["category"] = self.category

        if self.affected_services:
            metadata["affected_services"] = self.affected_services

        if self.affected_regions:
            metadata["affected_regions"] = self.affected_regions

        if self.affected_users_count is not None:
            metadata["affected_users_count"] = self.affected_users_count

        # Build context
        context: dict[str, Any] = {}

        if self.tags:
            context["tags"] = self.tags

        if self.started_at:
            context["started_at"] = self.started_at.isoformat()

        if self.ended_at:
            context["ended_at"] = self.ended_at.isoformat()

        return EnrichmentInput(
            signal_type=self.SIGNAL_TYPE,
            signal_id=self.id,
            title=self.title,
            content="\n\n".join(content_parts),
            metadata=metadata,
            context=context,
        )


class CustomerCase(HasDomainEventsMixin, BaseModel):
    """
    Aggregate root for customer support cases.

    Represents a problem experienced by an individual user.
    Contains symptoms, context, and lifecycle information.
    """

    SIGNAL_TYPE = "CustomerCase"

    # Customer information
    customer_id = models.CharField(max_length=255, db_index=True)
    customer_email = models.EmailField(blank=True, null=True)
    customer_name = models.CharField(max_length=255, blank=True)

    # Case details
    title = models.CharField(max_length=500)
    description = models.TextField()
    status = models.CharField(
        max_length=20, choices=StatusChoices.choices, default=StatusChoices.OPEN
    )
    severity = models.CharField(
        max_length=20, choices=SeverityChoices.choices, default=SeverityChoices.MEDIUM
    )
    priority = models.IntegerField(
        choices=PriorityChoices.choices,
        default=PriorityChoices.NORMAL,
        db_index=True,
        help_text="Response urgency (0=urgent, 3=low)",
    )
    category = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        help_text="Case category/issue type from source system",
    )

    # Source information
    source_system = models.CharField(max_length=100, db_index=True)
    source_identifier = models.CharField(max_length=255)
    source_url = models.URLField(blank=True, null=True)

    # Time tracking
    started_at = models.DateTimeField(db_index=True, null=True, blank=True)
    ended_at = models.DateTimeField(blank=True, null=True)

    # Relations
    related_incident = models.ForeignKey(
        Incident,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customer_cases",
    )

    # Metadata
    tags = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    # Raw data and conversation
    raw_data = models.JSONField(default=dict, blank=True)
    conversation = models.JSONField(default=list, blank=True)

    # Content hash for change detection
    content_hash = models.CharField(max_length=64, blank=True, null=True, db_index=True)

    class Meta:
        app_label = "nazara_signals"
        db_table = "nazara_customer_case"
        verbose_name = "Customer Case"
        verbose_name_plural = "Customer Cases"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "severity"]),
            models.Index(fields=["source_system", "source_identifier"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["source_system", "source_identifier"],
                name="unique_customer_case_source",
            ),
        ]

    def __str__(self) -> str:
        return self.title

    @classmethod
    def create(cls, **kwargs: Any) -> CustomerCase:
        """
        Factory method to create a new CustomerCase.

        Registers SignalCreatedEvent at the moment of creation.
        """
        instance = cls(**kwargs)
        instance.register_domain_event(
            SignalCreatedEvent(signal_type=cls.SIGNAL_TYPE, signal_id=instance.id)
        )
        return instance

    def apply_changes(self, **updates: Any) -> tuple[str, ...]:
        """
        Apply field updates and register SignalUpdatedEvent if any fields changed.

        Returns:
            Tuple of changed field names.
        """
        changed_fields: list[str] = []
        for field, value in updates.items():
            current = getattr(self, field, None)
            if current != value:
                setattr(self, field, value)
                changed_fields.append(field)

        if changed_fields:
            self._touch()
            self.register_domain_event(
                SignalUpdatedEvent(
                    signal_type=self.SIGNAL_TYPE,
                    signal_id=self.id,
                    changed_fields=tuple(changed_fields),
                )
            )

        return tuple(changed_fields)

    def link_to_incident(self, incident: Incident) -> None:
        self.related_incident = incident
        self._touch()

    def unlink_from_incident(self) -> None:
        self.related_incident = None
        self._touch()

    def update_status(self, new_status: str) -> None:
        self.status = new_status
        self._touch()

    def resolve(self, ended_at: datetime | None = None) -> None:
        self.status = StatusChoices.RESOLVED
        self.ended_at = ended_at or timezone.now()
        self._touch()

    def _touch(self) -> None:
        self.updated_at = timezone.now()
        self.version += 1

    @property
    def is_linked(self) -> bool:
        return self.related_incident_id is not None

    @property
    def is_open(self) -> bool:
        return self.status in (
            StatusChoices.OPEN,
            StatusChoices.INVESTIGATING,
            StatusChoices.IDENTIFIED,
        )

    def compute_content_hash(self) -> str:
        """
        Compute a hash of content fields for change detection.

        Used to prevent unnecessary database updates when the same
        data is ingested multiple times.
        """
        content = {
            "customer_id": self.customer_id,
            "customer_email": self.customer_email,
            "customer_name": self.customer_name,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "severity": self.severity,
            "priority": self.priority,
            "source_url": self.source_url,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "tags": self.tags,
            "metadata": self.metadata,
            "conversation": self.conversation,
        }
        serialized = json.dumps(content, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()

    def to_enrichment_input(self) -> EnrichmentInput:
        """
        Build enrichment input with all relevant case data.

        Content includes:
        - description (primary)
        - conversation thread (last 10 messages, 500 char limit each)

        Metadata includes:
        - severity, status, priority, category, source_system
        - No PII (customer_id, customer_email, customer_name excluded)

        Context includes:
        - tags, started_at, ended_at, total_messages
        """
        # Build rich content
        content_parts = [self.description]

        if self.conversation:
            formatted_conversation = self._format_conversation_for_enrichment()
            if formatted_conversation:
                total = len(self.conversation)
                header = f"Conversation ({total} messages, showing last 10):"
                content_parts.append(f"{header}\n{formatted_conversation}")

        # Build metadata (no PII, convert enums to strings for consistent hashing)
        severity = self.severity.value if hasattr(self.severity, "value") else self.severity
        status = self.status.value if hasattr(self.status, "value") else self.status
        priority = self.priority.value if hasattr(self.priority, "value") else self.priority
        metadata: dict[str, Any] = {
            "severity": severity,
            "status": status,
            "priority": priority,
            "source_system": self.source_system,
        }

        if self.category:
            metadata["category"] = self.category

        # Build context
        context: dict[str, Any] = {}

        if self.tags:
            context["tags"] = self.tags

        if self.started_at:
            context["started_at"] = self.started_at.isoformat()

        if self.ended_at:
            context["ended_at"] = self.ended_at.isoformat()

        if self.conversation:
            context["total_messages"] = len(self.conversation)

        return EnrichmentInput(
            signal_type=self.SIGNAL_TYPE,
            signal_id=self.id,
            title=self.title,
            content="\n\n".join(content_parts),
            metadata=metadata,
            context=context,
        )

    def _format_conversation_for_enrichment(self) -> str:
        """
        Format conversation entries for enrichment context.

        Returns last 10 messages with author labels, truncating
        individual messages to 500 characters.
        """
        if not self.conversation:
            return ""

        lines = []
        for entry in self.conversation[-10:]:  # Last 10 messages
            author = entry.get("author", "Unknown")
            body = entry.get("body", "")
            if body:
                # Truncate long messages
                if len(body) > 500:
                    body = body[:500] + "..."
                lines.append(f"[{author}]: {body}")

        return "\n".join(lines)


class TechnicalIssue(HasDomainEventsMixin, BaseModel):
    """
    Aggregate root for technical issues.

    Represents a stable technical issue (Sentry issue, Datadog monitor, etc.)
    that lives longer than raw events. This is the correct unit for
    correlation, AI enrichment, and embeddings.
    """

    SIGNAL_TYPE = "TechnicalIssue"

    # Issue identity (unique constraint)
    provider = models.CharField(max_length=50, db_index=True)  # sentry, datadog, newrelic
    issue_key = models.CharField(max_length=500)  # e.g., sentry:{project_id}:{issue_id}
    environment = models.CharField(max_length=50, db_index=True, default="unknown")
    service = models.CharField(max_length=255, db_index=True, default="unknown")
    severity = models.CharField(
        max_length=20,
        choices=SeverityChoices.choices,
        default=SeverityChoices.MEDIUM,
        db_index=True,
    )
    category = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        help_text="Issue category derived from service or error type",
    )

    # Lifecycle
    status = models.CharField(
        max_length=20,
        choices=IssueStatusChoices.choices,
        default=IssueStatusChoices.ACTIVE,
        db_index=True,
    )
    first_seen_at = models.DateTimeField(null=True, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True, db_index=True)

    # Counters
    occurrences_total = models.PositiveIntegerField(default=0)

    # Convenience fields
    title = models.CharField(max_length=500, blank=True, null=True)
    last_message = models.TextField(blank=True, null=True)
    source_url = models.URLField(blank=True, null=True)
    sample_payload = models.JSONField(blank=True, null=True)

    # Content hash for change detection
    content_hash = models.CharField(max_length=64, blank=True, null=True, db_index=True)

    class Meta:
        app_label = "nazara_signals"
        db_table = "nazara_technical_issue"
        verbose_name = "Technical Issue"
        verbose_name_plural = "Technical Issues"
        ordering = ["-last_seen_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "issue_key", "environment", "service"],
                name="unique_issue_identity",
            ),
        ]
        indexes = [
            models.Index(fields=["provider", "environment", "service", "status"]),
            models.Index(fields=["last_seen_at"]),
            models.Index(fields=["occurrences_total"]),
        ]

    def __str__(self) -> str:
        return self.title or f"{self.provider}:{self.issue_key}"

    @classmethod
    def create(cls, **kwargs: Any) -> TechnicalIssue:
        # Extract events from kwargs (not a model field)
        events = kwargs.pop("events", [])

        instance = cls(**kwargs)

        # Initialize pending events tracking
        instance._pending_events = []

        # Link events to this issue if provided
        for event in events:
            event.issue = instance
        instance._pending_events = list(events)

        instance.register_domain_event(
            SignalCreatedEvent(signal_type=cls.SIGNAL_TYPE, signal_id=instance.id)
        )
        return instance

    def apply_changes(self, **updates: Any) -> tuple[str, ...]:
        changed_fields: list[str] = []
        for field, value in updates.items():
            current = getattr(self, field, None)
            if current != value:
                setattr(self, field, value)
                changed_fields.append(field)

        if changed_fields:
            self._touch()
            self.register_domain_event(
                SignalUpdatedEvent(
                    signal_type=self.SIGNAL_TYPE,
                    signal_id=self.id,
                    changed_fields=tuple(changed_fields),
                )
            )

        return tuple(changed_fields)

    def add_technical_event(self, event: TechnicalEvent) -> None:
        """
        Stage a TechnicalEvent for persistence within this aggregate.

        This method:
        - Links the event to this issue
        - Tracks the event for atomic persistence
        - Updates timestamps based on event's occurred_at
        - Updates convenience fields with latest event data
        - Does NOT increment occurrences_total (deferred to repository)

        The counter is updated by the repository AFTER confirming the event
        was actually saved (not a duplicate).

        Args:
            event: The TechnicalEvent entity to add to this issue.
        """
        # Initialize _pending_events if not already done (for existing instances)
        if not hasattr(self, "_pending_events"):
            self._pending_events = []

        # Link event to this issue
        event.issue = self

        # Track for persistence
        self._pending_events.append(event)

        # Update timestamps
        if event.occurred_at:
            if self.first_seen_at is None or event.occurred_at < self.first_seen_at:
                self.first_seen_at = event.occurred_at

            if self.last_seen_at is None or event.occurred_at > self.last_seen_at:
                self.last_seen_at = event.occurred_at

        # Ensure active status
        self.status = IssueStatusChoices.ACTIVE

        # Update convenience fields with latest event data
        if event.title:
            self.title = event.title
        if event.error_message:
            self.last_message = event.error_message
        if event.source_url:
            self.source_url = event.source_url
        if event.raw_data:
            self.sample_payload = event.raw_data

        self._touch()

    def get_pending_events(self) -> list[TechnicalEvent]:
        if not hasattr(self, "_pending_events"):
            self._pending_events = []
        return self._pending_events.copy()

    def clear_pending_events(self) -> None:
        if hasattr(self, "_pending_events"):
            self._pending_events.clear()

    def record_occurrence(
        self,
        occurred_at: datetime,
        title: str | None = None,
        message: str | None = None,
        source_url: str | None = None,
        sample_payload: dict[str, Any] | None = None,
    ) -> None:
        """
        Record a new occurrence of this issue.

        Updates counters and timestamps. Call this when a new raw event
        is successfully inserted that belongs to this issue.
        """
        # Set first_seen_at only once
        if self.first_seen_at is None:
            self.first_seen_at = occurred_at

        # Update last_seen_at to the latest occurrence
        if self.last_seen_at is None or occurred_at > self.last_seen_at:
            self.last_seen_at = occurred_at

        # Increment counter
        self.occurrences_total += 1

        # Update convenience fields with latest values
        if title:
            self.title = title
        if message:
            self.last_message = message
        if source_url:
            self.source_url = source_url
        if sample_payload:
            self.sample_payload = sample_payload

        # Ensure active status
        self.status = IssueStatusChoices.ACTIVE
        self._touch()

    def resolve(self) -> None:
        self.status = IssueStatusChoices.RESOLVED
        self._touch()

    def reactivate(self) -> None:
        self.status = IssueStatusChoices.ACTIVE
        self._touch()

    def _touch(self) -> None:
        self.updated_at = timezone.now()

    @property
    def is_active(self) -> bool:
        return self.status == IssueStatusChoices.ACTIVE

    @property
    def is_resolved(self) -> bool:
        return self.status == IssueStatusChoices.RESOLVED

    @property
    def identity_tuple(self) -> tuple[str, str, str, str]:
        return self.provider, self.issue_key, self.environment, self.service

    def compute_content_hash(self) -> str:
        """
        Compute a hash of content fields for change detection.

        Used to prevent unnecessary database updates when the same
        data is ingested multiple times.
        """
        content = {
            "status": self.status,
            "title": self.title,
            "last_message": self.last_message,
            "source_url": self.source_url,
            "sample_payload": self.sample_payload,
        }
        serialized = json.dumps(content, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()

    def to_enrichment_input(self) -> EnrichmentInput:
        """
        Build enrichment input with all relevant issue data.

        Content includes:
        - last_message (error details)
        - sample_payload (truncated if >2KB)

        Metadata includes:
        - severity, status, category
        - environment, service, provider
        - occurrences_total

        Context includes:
        - first_seen_at, last_seen_at
        """
        # Build rich content
        content_parts = []

        if self.last_message:
            content_parts.append(self.last_message)

        # Add sample payload if available
        if self.sample_payload:
            formatted_payload = self._format_sample_payload_for_enrichment()
            if formatted_payload:
                content_parts.append(f"Sample Payload:\n{formatted_payload}")

        # Build metadata (convert enums to strings for consistent hashing)
        severity = self.severity.value if hasattr(self.severity, "value") else self.severity
        status = self.status.value if hasattr(self.status, "value") else self.status
        metadata: dict[str, Any] = {
            "severity": severity,
            "status": status,
            "environment": self.environment,
            "service": self.service,
            "provider": self.provider,
            "occurrences_total": self.occurrences_total,
        }

        if self.category:
            metadata["category"] = self.category

        # Build context
        context: dict[str, Any] = {}

        if self.first_seen_at:
            context["first_seen_at"] = self.first_seen_at.isoformat()

        if self.last_seen_at:
            context["last_seen_at"] = self.last_seen_at.isoformat()

        return EnrichmentInput(
            signal_type=self.SIGNAL_TYPE,
            signal_id=self.id,
            title=self.title or f"{self.provider}:{self.issue_key}",
            content="\n\n".join(content_parts) if content_parts else self.title or "",
            metadata=metadata,
            context=context,
        )

    def _format_sample_payload_for_enrichment(self) -> str:
        """
        Format sample_payload for enrichment context.

        Truncates to 2KB if larger to avoid token bloat.
        """
        if not self.sample_payload:
            return ""

        payload_str = json.dumps(self.sample_payload, indent=2, default=str)

        if len(payload_str) > 2000:
            return payload_str[:2000] + "\n... [truncated]"

        return payload_str


class TechnicalEvent(HasDomainEventsMixin, BaseModel):
    """
    Raw technical event (supporting entity).

    Represents a single occurrence of machine-level evidence: errors,
    anomalies, spikes, warnings. This is the raw event that belongs
    to a TechnicalIssue (the aggregate root).

    Raw events have short retention (e.g., 14 days) while issues persist
    for longer-term analysis and AI enrichment.

    Note: TechnicalEvent is a supporting entity, not an aggregate root.
    It has HasDomainEventsMixin for future event capabilities but does
    not currently emit SignalCreatedEvent (enrichment targets TechnicalIssue).
    """

    # Provider and deduplication
    provider = models.CharField(max_length=50, db_index=True, default="")
    external_id = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )  # Provider's event ID
    dedupe_hash = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )  # Hash-based deduplication

    # Issue relationship (nullable FK)
    issue = models.ForeignKey(
        TechnicalIssue,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )

    # Event details
    event_type = models.CharField(max_length=30, choices=EventTypeChoices.choices)
    title = models.CharField(max_length=500)
    description = models.TextField()
    severity = models.CharField(
        max_length=20, choices=SeverityChoices.choices, default=SeverityChoices.MEDIUM
    )

    # Source information (kept for backward compatibility)
    source_system = models.CharField(max_length=100, db_index=True)
    source_identifier = models.CharField(max_length=255)
    source_url = models.URLField(blank=True, null=True)

    # Context
    service = models.CharField(max_length=255, db_index=True)
    environment = models.CharField(max_length=50, db_index=True, default="production")
    host = models.CharField(max_length=255, blank=True, null=True)
    transaction = models.CharField(max_length=500, blank=True, null=True)
    release = models.CharField(max_length=100, blank=True, null=True)

    # Time tracking
    occurred_at = models.DateTimeField(db_index=True, null=True, blank=True)  # When event occurred
    started_at = models.DateTimeField(null=True, blank=True)  # Deprecated: use occurred_at
    ended_at = models.DateTimeField(blank=True, null=True)
    occurrence_count = models.PositiveIntegerField(default=1)

    # Error details
    error_type = models.CharField(max_length=255, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    error_stacktrace = models.TextField(blank=True, null=True)
    error_fingerprint = models.CharField(max_length=255, blank=True, null=True, db_index=True)

    # Metric details
    metric_name = models.CharField(max_length=255, blank=True, null=True)
    metric_value = models.FloatField(blank=True, null=True)
    metric_threshold = models.FloatField(blank=True, null=True)
    metric_unit = models.CharField(max_length=50, blank=True, null=True)

    # Raw data
    raw_data = models.JSONField(blank=True, null=True)

    # Relations
    related_incident = models.ForeignKey(
        Incident,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="technical_events",
    )

    # Metadata
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        app_label = "nazara_signals"
        db_table = "nazara_technical_event"
        verbose_name = "Technical Event"
        verbose_name_plural = "Technical Events"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["source_system", "source_identifier"],
                name="unique_event_source",
            ),
        ]
        indexes = [
            models.Index(fields=["event_type", "severity"]),
            models.Index(fields=["service", "environment"]),
            models.Index(fields=["provider", "external_id"]),
            models.Index(fields=["issue", "occurred_at"]),
        ]

    def __str__(self) -> str:
        return self.title

    def link_to_issue(self, issue_id: uuid.UUID) -> None:
        self.issue_id = issue_id
        self._touch()

    def unlink_from_issue(self) -> None:
        self.issue = None
        self._touch()

    def link_to_incident(self, incident: Incident) -> None:
        self.related_incident = incident
        self._touch()

    def unlink_from_incident(self) -> None:
        self.related_incident = None
        self._touch()

    def increment_occurrence(self) -> None:
        self.occurrence_count += 1
        self._touch()

    def set_error_info(
        self,
        error_type: str | None = None,
        message: str | None = None,
        stacktrace: str | None = None,
        fingerprint: str | None = None,
    ) -> None:
        self.error_type = error_type
        self.error_message = message
        self.error_stacktrace = stacktrace
        self.error_fingerprint = fingerprint
        self._touch()

    def set_metric_info(
        self,
        name: str,
        value: float,
        threshold: float | None = None,
        unit: str | None = None,
    ) -> None:
        self.metric_name = name
        self.metric_value = value
        self.metric_threshold = threshold
        self.metric_unit = unit
        self._touch()

    def set_summary(self, summary: str) -> None:
        self.summary = summary
        self._touch()

    def set_embedding(self, embedding: list[float]) -> None:
        self.embedding = embedding
        self._touch()

    def _touch(self) -> None:
        self.updated_at = timezone.now()
        self.version += 1

    @property
    def is_linked_to_issue(self) -> bool:
        return self.issue_id is not None

    @property
    def is_linked(self) -> bool:
        return self.related_incident_id is not None

    @property
    def is_error(self) -> bool:
        return self.event_type in (EventTypeChoices.ERROR, EventTypeChoices.EXCEPTION)

    @property
    def is_metric(self) -> bool:
        return self.event_type == EventTypeChoices.METRIC_ANOMALY
