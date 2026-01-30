from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any
from uuid import UUID

from celery import Task, shared_task

if TYPE_CHECKING:
    from nazara.ingestion.application.ingestion import RunIngestion

logger = logging.getLogger(__name__)


def _get_run_ingestion() -> RunIngestion:
    from nazara.containers import get_container

    container = get_container()
    return container.ingestion.run_ingestion()


@shared_task(bind=True, max_retries=3)
def run_ingestor_task(self: Task[Any, Any], config_id: str) -> dict[str, Any]:
    try:
        ingestion = _get_run_ingestion()
        result = ingestion.execute(UUID(config_id))

        logger.info(
            f"Ingestor {config_id} completed: "
            f"status={result.status}, items={result.items_processed}"
        )

        return {
            "config_id": config_id,
            "run_id": str(result.id),
            "status": result.status,  # CharField already stores string value
            "items_processed": result.items_processed,
            "items_created": result.items_created,
            "items_updated": result.items_updated,
            "items_skipped": result.items_skipped,
            "duration_seconds": result.duration_seconds,
        }

    except Exception as exc:
        logger.error(f"Failed to run ingestor {config_id}: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2**self.request.retries)) from exc


@shared_task
def poll_all_ingestors_task() -> dict[str, Any]:
    try:
        from nazara.containers import get_container

        container = get_container()
        config_repo = container.ingestion.config_repository()
        due_configs = config_repo.list_due_for_polling()

        triggered_count = 0
        for config in due_configs:
            run_ingestor_task.delay(str(config.id))
            triggered_count += 1
            logger.info(f"Queued ingestor for polling: {config.display_name} ({config.id})")

        logger.info(f"Polling check complete: {triggered_count} ingestors queued")

        return {
            "triggered": triggered_count,
            "configs": [str(c.id) for c in due_configs],
        }

    except Exception as exc:
        logger.error(f"Failed to poll ingestors: {exc}")
        return {"error": str(exc), "triggered": 0}
