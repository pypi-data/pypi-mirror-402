import logging

from nazara.shared.event_bus.contracts import DomainEvent, EventBus, EventHandler, EventName

logger = logging.getLogger(__name__)


class InMemorySynchronousEventBus(EventBus):
    """
    Synchronous in-memory event bus for testing.

    Executes handlers immediately in the same thread.
    NOT for production use - does not provide async execution or retries.

    Args:
        events_map: Mapping of event type names to their handlers.
    """

    def __init__(self, events_map: dict[EventName, list[EventHandler[DomainEvent]]]) -> None:
        self.events_map = events_map

    def publish(self, *domain_events: DomainEvent) -> None:
        """
        Publish domain events to their respective handlers synchronously.

        Each handler is called in sequence. Failures are logged but do not
        prevent subsequent handlers from executing.

        Args:
            domain_events: One or more domain events to publish.
        """
        for event in domain_events:
            handlers = self.events_map.get(event.event_type(), [])

            if not handlers:
                logger.debug(f"No handlers registered for {event.event_type()}")
                continue

            for handler in handlers:
                try:
                    handler(event)
                    logger.debug(f"Handler {handler.__name__} processed {event.event_type()}")
                except Exception as e:
                    logger.error(
                        f"Handler {handler.__name__} failed for {event.event_type()}: {e}",
                        exc_info=True,
                    )


class CeleryAsyncEventBus(EventBus):
    """
    Asynchronous event bus using Celery.

    Production adapter that:
    - Serializes events to dict for task transport
    - Dispatches to Celery task queue
    - Handles retry/failure via Celery mechanisms

    Events are processed asynchronously by Celery workers.
    """

    def publish(self, *domain_events: DomainEvent) -> None:
        """
        Publish domain events to Celery task queue.

        Each event is serialized and dispatched as a separate Celery task.
        Task execution, retries, and failure handling are managed by Celery.

        Args:
            domain_events: One or more domain events to publish.
        """
        # Import here to avoid circular imports and allow lazy Celery initialization
        from nazara.shared.event_bus.tasks import process_domain_event

        for event in domain_events:
            process_domain_event.delay(
                event_type=event.event_type(),
                event_data=event.to_dict(),
            )
            logger.debug(f"Dispatched {event.event_type()} to Celery queue")
