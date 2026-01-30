from typing import Literal

from nazara.shared.event_bus.contracts import EventBus

EventBusDriver = Literal["celery", "in-memory"]


def get_event_bus(driver: EventBusDriver | None = None) -> EventBus:
    """
    Factory function for EventBus instances.

    Args:
        driver: Explicit driver selection. If None, uses Django settings.
            - "celery": Production async delivery via Celery
            - "in-memory": Synchronous delivery for testing

    Returns:
        EventBus instance appropriate for the environment.

    Example:
        # Production (uses settings)
        bus = get_event_bus()
        bus.publish(SomeEvent(...))

        # Testing (explicit in-memory)
        bus = get_event_bus("in-memory")
        bus.publish(SomeEvent(...))
    """
    if driver is None:
        from django.conf import settings

        driver = getattr(settings, "EVENT_BUS_DRIVER", "celery")

    if driver == "in-memory":
        from nazara.shared.event_bus.adapters import InMemorySynchronousEventBus
        from nazara.shared.event_bus.registry import EVENTS_MAP

        return InMemorySynchronousEventBus(EVENTS_MAP)

    # Default to Celery
    from nazara.shared.event_bus.adapters import CeleryAsyncEventBus

    return CeleryAsyncEventBus()
