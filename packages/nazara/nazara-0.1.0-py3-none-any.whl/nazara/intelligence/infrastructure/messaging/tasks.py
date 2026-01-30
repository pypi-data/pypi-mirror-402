from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from celery import Task, shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
)
def enrich_incident_task(
    self: Task[Any, Any],
    incident_id: str,
    force: bool = False,
) -> dict[str, Any]:
    from nazara.containers import get_container

    logger.info(f"Enriching Incident:{incident_id} (force={force})")

    container = get_container()
    service = container.intelligence.enrich_incident()
    result: dict[str, Any] = service.enrich(
        incident_id=UUID(incident_id),
        force=force,
    )

    logger.info(f"Enrichment complete for Incident:{incident_id}: {result}")
    return result


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
)
def enrich_customer_case_task(
    self: Task[Any, Any],
    case_id: str,
    force: bool = False,
) -> dict[str, Any]:
    from nazara.containers import get_container

    logger.info(f"Enriching CustomerCase:{case_id} (force={force})")

    container = get_container()
    service = container.intelligence.enrich_customer_case()
    result: dict[str, Any] = service.enrich(
        case_id=UUID(case_id),
        force=force,
    )

    logger.info(f"Enrichment complete for CustomerCase:{case_id}: {result}")
    return result


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
)
def enrich_technical_issue_task(
    self: Task[Any, Any],
    issue_id: str,
    force: bool = False,
) -> dict[str, Any]:
    from nazara.containers import get_container

    logger.info(f"Enriching TechnicalIssue:{issue_id} (force={force})")

    container = get_container()
    service = container.intelligence.enrich_technical_issue()
    result: dict[str, Any] = service.enrich(
        issue_id=UUID(issue_id),
        force=force,
    )

    logger.info(f"Enrichment complete for TechnicalIssue:{issue_id}: {result}")
    return result
