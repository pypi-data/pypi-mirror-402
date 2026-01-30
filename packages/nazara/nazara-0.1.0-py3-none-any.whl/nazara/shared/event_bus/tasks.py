from __future__ import annotations

import logging
from typing import Any

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
)
def process_domain_event(
    self: Any,
    event_type: str,
    event_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Celery task that processes domain events.

    1. Deserializes event from dict
    2. Looks up handlers in registry
    3. Executes each handler
    4. Retries on failure (3 attempts, exponential backoff)

    Args:
        self: Celery task instance (bound task).
        event_type: The event class name for registry lookup.
        event_data: Dictionary representation of the event.

    Returns:
        Dict with processing status and handler results.

    Raises:
        Exception: Re-raised to trigger Celery retry on handler failure.
    """
    from nazara.shared.event_bus.registry import EVENT_CLASSES, EVENTS_MAP

    # Reconstruct the event object
    event_cls = EVENT_CLASSES.get(event_type)
    if not event_cls:
        logger.warning(f"Unknown event type: {event_type}")
        return {
            "status": "skipped",
            "reason": f"Unknown event type: {event_type}",
        }

    event = event_cls.from_dict(event_data)

    # Execute all registered handlers
    handlers = EVENTS_MAP.get(event_type, [])
    if not handlers:
        logger.debug(f"No handlers registered for {event_type}")
        return {
            "status": "success",
            "handlers_executed": 0,
            "reason": "No handlers registered",
        }

    executed_handlers: list[str] = []
    for handler in handlers:
        try:
            handler(event)
            executed_handlers.append(handler.__name__)
            logger.info(f"Handler {handler.__name__} processed {event_type}")
        except Exception as e:
            logger.error(
                f"Handler {handler.__name__} failed for {event_type}: {e}",
                exc_info=True,
            )
            # Re-raise to trigger Celery retry
            raise

    return {
        "status": "success",
        "event_type": event_type,
        "handlers_executed": len(executed_handlers),
        "handlers": executed_handlers,
    }
