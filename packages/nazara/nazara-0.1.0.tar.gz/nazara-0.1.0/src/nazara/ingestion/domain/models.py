from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from django.utils import timezone

from nazara.shared.event_bus.contracts import HasDomainEventsMixin
from nazara.shared.infrastructure.django.models import BaseModel

if TYPE_CHECKING:
    from django.db.models import QuerySet


class IngestorTypeChoices(models.TextChoices):
    INCIDENT_IO_INCIDENT = "incident_io_incident", "Incident.io Incident"
    SENTRY_EVENT = "sentry_event", "Sentry Event"
    DATADOG_EVENT = "datadog_event", "Datadog Event"
    INTERCOM_CASE = "intercom_case", "Intercom Case"


class AuthTypeChoices(models.TextChoices):
    OAUTH = "oauth", "OAuth"
    API_TOKEN = "api_token", "API Token"
    WEBHOOK_SECRET = "webhook_secret", "Webhook Secret"


class IngestionModeChoices(models.TextChoices):
    WEBHOOK = "webhook", "Webhook"
    POLLING = "polling", "Polling"
    HYBRID = "hybrid", "Hybrid"


class RunStatusChoices(models.TextChoices):
    RUNNING = "running", "Running"
    SUCCESS = "success", "Success"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"


class IngestorConfig(HasDomainEventsMixin, BaseModel):
    """
    Aggregate root for ingestor configurations.

    Represents how Nazara connects to and reads data from an external source.
    Contains authentication, filtering, scheduling, and state information.
    """

    name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional custom name (auto: type/account)",
    )
    ingestor_type = models.CharField(
        max_length=50,
        choices=IngestorTypeChoices.choices,
        db_index=True,
        help_text="Type of data this ingestor handles",
    )
    enabled = models.BooleanField(
        default=True, db_index=True, help_text="Whether this ingestor is active"
    )

    auth_type = models.CharField(
        max_length=50,
        choices=AuthTypeChoices.choices,
        default=AuthTypeChoices.API_TOKEN,
        help_text="Authentication method used",
    )
    secret_ref = models.CharField(
        max_length=500,
        help_text="Reference to secret in secrets manager (e.g., vault path, env var name)",
    )
    external_account_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="External account/workspace ID if applicable",
    )

    ingestion_mode = models.CharField(
        max_length=20,
        choices=IngestionModeChoices.choices,
        default=IngestionModeChoices.POLLING,
        help_text="How data is ingested (webhook, polling, or both)",
    )

    filters = models.JSONField(
        default=dict,
        blank=True,
        help_text="Source-specific filter configuration (channels, projects, etc.)",
    )

    cursor = models.TextField(
        blank=True,
        null=True,
        help_text="Current cursor/watermark position for incremental fetching",
    )
    since = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Initial baseline datetime for backfills",
    )
    last_success_at = models.DateTimeField(
        blank=True,
        null=True,
        db_index=True,
        help_text="Timestamp of last successful ingestion",
    )
    last_error_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Timestamp of last error",
    )
    error_count = models.PositiveIntegerField(
        default=0,
        help_text="Consecutive error count",
    )
    last_error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Most recent error message",
    )

    poll_interval_seconds = models.PositiveIntegerField(
        default=300,
        help_text="Interval between polling cycles in seconds (minimum 60)",
    )

    class Meta:
        app_label = "nazara_ingestion"
        db_table = "nazara_ingestor_config"
        verbose_name = "Ingestor Configuration"
        verbose_name_plural = "Ingestor Configurations"
        ordering = ["ingestor_type", "external_account_id"]
        indexes = [
            models.Index(fields=["enabled", "ingestion_mode"]),
            models.Index(fields=["ingestor_type"]),
        ]

    @property
    def display_name(self) -> str:
        if self.name:
            return self.name
        if self.external_account_id:
            return f"{self.ingestor_type}/{self.external_account_id}"
        return self.ingestor_type

    def save(self, *args, **kwargs) -> None:
        if not self.name:
            if self.external_account_id:
                self.name = f"{self.ingestor_type}/{self.external_account_id}"
            else:
                self.name = self.ingestor_type
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        status = "enabled" if self.enabled else "disabled"
        return f"{self.display_name} ({status})"

    def enable(self) -> None:
        self.enabled = True
        self._touch()

    def disable(self) -> None:
        self.enabled = False
        self._touch()

    def update_cursor(self, new_cursor: str | None) -> None:
        self.cursor = new_cursor
        self.last_success_at = timezone.now()
        self.error_count = 0
        self.last_error_message = None
        self._touch()

    def record_error(self, error_message: str) -> None:
        self.last_error_at = timezone.now()
        self.error_count += 1
        self.last_error_message = error_message
        self._touch()

    def reset_cursor(self) -> None:
        self.cursor = None
        self.error_count = 0
        self.last_error_message = None
        self._touch()

    def update_filters(self, filters: dict) -> None:
        self.filters = filters
        self._touch()

    def update_schedule(self, poll_interval_seconds: int) -> None:
        if poll_interval_seconds < 60:
            raise ValueError("Poll interval must be at least 60 seconds")
        self.poll_interval_seconds = poll_interval_seconds
        self._touch()

    def _touch(self) -> None:
        self.updated_at = timezone.now()
        self.version += 1

    def get_run_history(self, limit: int = 50) -> QuerySet[IngestorRun]:
        return self.runs.order_by("-started_at")[:limit]

    def start_run(self) -> IngestorRun:
        """
        Start a new ingestion run for this configuration.

        Raises ValueError if configuration is disabled.
        Creates, saves, and returns IngestorRun in RUNNING status.
        """
        if not self.enabled:
            raise ValueError(f"Cannot start run: configuration '{self.display_name}' is disabled")
        run = IngestorRun.start(config=self, cursor_before=self.cursor)
        run.save()
        return run

    def complete_run(
        self,
        run: IngestorRun,
        items_processed: int,
        items_created: int,
        items_updated: int,
        items_skipped: int,
        cursor_after: str | None,
    ) -> None:
        run.complete(
            items_processed=items_processed,
            items_created=items_created,
            items_updated=items_updated,
            items_skipped=items_skipped,
            cursor_after=cursor_after,
        )
        run.save()
        self.update_cursor(cursor_after)
        self.save()

    def fail_run(self, run: IngestorRun, error_message: str) -> None:
        run.fail(error_message)
        run.save()
        self.record_error(error_message)
        self.save()

    @property
    def is_due_for_polling(self) -> bool:
        if not self.enabled:
            return False
        if self.ingestion_mode == IngestionModeChoices.WEBHOOK:
            return False
        if self.last_success_at is None:
            return True
        elapsed = (timezone.now() - self.last_success_at).total_seconds()
        return elapsed >= self.poll_interval_seconds

    @property
    def is_healthy(self) -> bool:
        # Threshold: fewer than 5 consecutive errors
        return self.error_count < 5

    @property
    def is_failing(self) -> bool:
        # Threshold: 5 or more consecutive errors
        return self.error_count >= 5


class IngestorRun(BaseModel):
    """
    Supporting entity for ingestor execution history.

    Tracks execution metrics and status for observability
    and debugging purposes. This is append-only / read-mostly.
    """

    config = models.ForeignKey(
        IngestorConfig,
        on_delete=models.CASCADE,
        related_name="runs",
        help_text="The ingestor configuration that was executed",
    )

    started_at = models.DateTimeField(
        db_index=True,
        help_text="When the run started",
    )
    finished_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the run finished (null if still running)",
    )

    status = models.CharField(
        max_length=20,
        choices=RunStatusChoices.choices,
        default=RunStatusChoices.RUNNING,
        db_index=True,
        help_text="Current status of the run",
    )

    items_processed = models.PositiveIntegerField(
        default=0,
        help_text="Total items processed in this run",
    )
    items_created = models.PositiveIntegerField(
        default=0,
        help_text="New items created in this run",
    )
    items_updated = models.PositiveIntegerField(
        default=0,
        help_text="Existing items updated in this run",
    )
    items_skipped = models.PositiveIntegerField(
        default=0,
        help_text="Items skipped (unchanged content hash)",
    )

    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error message if the run failed",
    )

    cursor_before = models.TextField(
        blank=True,
        null=True,
        help_text="Cursor value before this run",
    )
    cursor_after = models.TextField(
        blank=True,
        null=True,
        help_text="Cursor value after this run (on success)",
    )

    class Meta:
        app_label = "nazara_ingestion"
        db_table = "nazara_ingestor_run"
        verbose_name = "Ingestor Run"
        verbose_name_plural = "Ingestor Runs"
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["config", "-started_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"{self.config.name} - {self.started_at.isoformat()} [{self.status}]"

    @classmethod
    def start(cls, config: IngestorConfig, cursor_before: str | None = None) -> IngestorRun:
        return cls(
            config=config,
            started_at=timezone.now(),
            cursor_before=cursor_before,
            status=RunStatusChoices.RUNNING,
        )

    def complete(
        self,
        items_processed: int,
        items_created: int,
        items_updated: int,
        items_skipped: int,
        cursor_after: str | None,
    ) -> None:
        self.finished_at = timezone.now()
        self.status = RunStatusChoices.SUCCESS
        self.items_processed = items_processed
        self.items_created = items_created
        self.items_updated = items_updated
        self.items_skipped = items_skipped
        self.cursor_after = cursor_after

    def fail(self, error_message: str) -> None:
        self.finished_at = timezone.now()
        self.status = RunStatusChoices.FAILED
        self.error_message = error_message

    def cancel(self) -> None:
        self.finished_at = timezone.now()
        self.status = RunStatusChoices.CANCELLED

    @property
    def duration_seconds(self) -> float | None:
        if self.finished_at is None:
            return None
        return (self.finished_at - self.started_at).total_seconds()

    @property
    def is_complete(self) -> bool:
        return self.status in (
            RunStatusChoices.SUCCESS,
            RunStatusChoices.FAILED,
            RunStatusChoices.CANCELLED,
        )

    @property
    def is_successful(self) -> bool:
        return self.status == RunStatusChoices.SUCCESS
