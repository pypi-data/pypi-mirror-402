from datetime import UTC, datetime, timedelta
from uuid import UUID

from nazara.ingestion.domain.contracts.ingestor_repository import IngestorConfigRepository
from nazara.ingestion.domain.models import IngestionModeChoices, IngestorConfig


class DjangoIngestorConfigRepository(IngestorConfigRepository):
    """
    Django ORM implementation for IngestorConfig persistence.

    Returns Django model instances directly.
    """

    def get(self, config_id: UUID) -> IngestorConfig | None:
        return IngestorConfig.objects.filter(pk=config_id).first()

    def list_due_for_polling(self, as_of: datetime | None = None) -> list[IngestorConfig]:
        """List configs that are due for their next polling cycle."""
        if as_of is None:
            as_of = datetime.now(UTC)

        # Get configs where:
        # - enabled = True
        # - ingestion_mode in (polling, hybrid)
        # - last_success_at is null OR last_success_at + interval <= now
        queryset = IngestorConfig.objects.filter(
            enabled=True,
            ingestion_mode__in=[
                IngestionModeChoices.POLLING,
                IngestionModeChoices.HYBRID,
            ],
        )

        results = []
        for model in queryset:
            if model.last_success_at is None:
                # Never run, so it's due
                results.append(model)
            else:
                next_run = model.last_success_at + timedelta(seconds=model.poll_interval_seconds)
                if next_run <= as_of:
                    results.append(model)

        return results

    def save(self, config: IngestorConfig) -> IngestorConfig:
        config.save()
        return config

    def delete(self, config_id: UUID) -> bool:
        deleted, _ = IngestorConfig.objects.filter(pk=config_id).delete()
        return deleted > 0
