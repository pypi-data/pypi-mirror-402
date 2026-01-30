from collections.abc import Callable
from typing import TYPE_CHECKING, Any
from uuid import UUID

from django.utils import timezone

from nazara.ingestion.domain.contracts.ingestor_repository import IngestorConfigRepository
from nazara.ingestion.domain.contracts.signal_reader import SignalReader
from nazara.ingestion.domain.models import IngestorConfig, IngestorRun
from nazara.shared.domain.contracts.secrets import SecretNotFoundError, SecretResolver
from nazara.shared.domain.value_objects.types import IngestorType, OutputType, ProcessingResult

if TYPE_CHECKING:
    from nazara.signals.application.customer_case import CreateCustomerCase
    from nazara.signals.application.incident import CreateIncident
    from nazara.signals.application.technical_event import CreateTechnicalEvent


class RunIngestion:
    """
    Orchestrates the execution of ingestor configurations.

    Responsibilities:
    - Execute ingestion cycles (polling mode)
    - Test external connections
    - Reset cursors (privileged operation)
    - Track run history and metrics
    """

    def __init__(
        self,
        config_repo: IngestorConfigRepository,
        secret_resolver: SecretResolver,
        readers: dict[IngestorType, type[SignalReader]],
        create_technical_event: "CreateTechnicalEvent",
        create_incident: "CreateIncident",
        create_customer_case: "CreateCustomerCase",
    ) -> None:
        self._config_repo = config_repo
        self._secret_resolver = secret_resolver
        self._readers = readers
        self._services: dict[OutputType, Callable[[Any], Any]] = {
            OutputType.TECHNICAL_EVENT: create_technical_event.from_data,
            OutputType.INCIDENT: create_incident.from_data,
            OutputType.CUSTOMER_CASE: create_customer_case.from_data,
        }

    def execute(self, config_id: UUID) -> IngestorRun:
        # 1. Load configuration
        config = self._config_repo.get(config_id)
        if not config:
            raise ValueError(f"Ingestor configuration not found: {config_id}")

        # 2. Start run tracking (aggregate creates, saves, and enforces invariants)
        run = config.start_run()

        try:
            # 3. Resolve credentials
            credentials = self._secret_resolver.resolve(config.secret_ref)

            # 4. Get appropriate reader
            reader_class = self._readers.get(config.ingestor_type)
            if not reader_class:
                raise ValueError(f"No reader registered for type: {config.ingestor_type}")

            reader = reader_class()

            # 5. Fetch updates (polling mode)
            payloads, new_cursor = reader.fetch_updates(
                credentials=credentials,
                filters=config.filters,
                cursor=config.cursor,
                since=config.since,
            )

            # 6. Process payloads and track accurate metrics
            items_created = 0
            items_updated = 0
            items_skipped = 0
            service_fn = self._services.get(reader_class.output_type)

            for payload in payloads:
                if service_fn:
                    result = service_fn(payload)
                    if result == ProcessingResult.CREATED:
                        items_created += 1
                    elif result == ProcessingResult.UPDATED:
                        items_updated += 1
                    elif result == ProcessingResult.SKIPPED:
                        items_skipped += 1
                    # FAILED results are not counted in any metric
                else:
                    items_created += 1

            # 7. Complete run (aggregate updates run + cursor + saves both)
            config.complete_run(
                run=run,
                items_processed=len(payloads),
                items_created=items_created,
                items_updated=items_updated,
                items_skipped=items_skipped,
                cursor_after=new_cursor,
            )

        except Exception as e:
            # Aggregate updates run + error state + saves both
            config.fail_run(run, str(e))

        return run

    def test_connection(self, config_id: UUID) -> tuple[bool, str]:
        config = self._config_repo.get(config_id)
        if not config:
            return False, f"Configuration not found: {config_id}"

        try:
            credentials = self._secret_resolver.resolve(config.secret_ref)

            reader_class = self._readers.get(config.ingestor_type)
            if not reader_class:
                return False, f"No reader registered for type: {config.ingestor_type}"

            reader = reader_class()

            # Try a minimal fetch (no cursor, just validate connection)
            # This will fail early if credentials are invalid
            payloads, _ = reader.fetch_updates(
                credentials=credentials,
                filters=config.filters,
                cursor=None,
                since=timezone.now(),  # Very recent to minimize data
            )

            return True, "API connection verified. Credentials are valid."

        except SecretNotFoundError as e:
            return False, f"Secret not found: {e.secret_ref}"
        except NotImplementedError:
            # Reader doesn't support polling, but connection might work for webhooks
            return True, "Connection test skipped (webhook-only mode)"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    def reset_cursor(self, config_id: UUID) -> None:
        config = self._config_repo.get(config_id)
        if not config:
            raise ValueError(f"Ingestor configuration not found: {config_id}")

        config.reset_cursor()
        self._config_repo.save(config)

    def get_run_history(self, config_id: UUID, limit: int = 50) -> list[IngestorRun]:
        config = self._config_repo.get(config_id)
        if not config:
            return []
        return list(config.get_run_history(limit=limit))

    def get_due_configs(self) -> list[IngestorConfig]:
        return self._config_repo.list_due_for_polling()


def get_default_readers() -> dict[IngestorType, type[SignalReader]]:
    from nazara.ingestion.infrastructure.readers.datadog_reader import DatadogReader
    from nazara.ingestion.infrastructure.readers.incident_io_reader import IncidentIoReader
    from nazara.ingestion.infrastructure.readers.intercom_reader import IntercomReader
    from nazara.ingestion.infrastructure.readers.sentry_reader import SentryReader

    return {
        IngestorType.INCIDENT_IO_INCIDENT: IncidentIoReader,
        IngestorType.SENTRY_EVENT: SentryReader,
        IngestorType.DATADOG_EVENT: DatadogReader,
        IngestorType.INTERCOM_CASE: IntercomReader,
    }
