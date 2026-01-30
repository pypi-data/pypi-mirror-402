from nazara.shared.event_bus.contracts import DomainEvent, EventHandler, EventName

# Map event names to their classes (for deserialization in Celery tasks)
EVENT_CLASSES: dict[EventName, type[DomainEvent]] = {}

# Map event names to their handlers
EVENTS_MAP: dict[EventName, list[EventHandler[DomainEvent]]] = {}


def register_event(event_cls: type[DomainEvent]) -> type[DomainEvent]:
    """
    Decorator to register an event class for deserialization.

    This enables the Celery task to reconstruct event objects from
    their dictionary representation.

    Usage:
        @register_event
        @dataclass(frozen=True, kw_only=True)
        class MyEvent(DomainEvent):
            some_field: str

    Args:
        event_cls: The event class to register.

    Returns:
        The same event class (unchanged).
    """
    EVENT_CLASSES[event_cls.__name__] = event_cls
    return event_cls


def register_handler(event_type: str, handler: EventHandler[DomainEvent]) -> None:
    """
    Register a handler for an event type.

    Multiple handlers can be registered for the same event type.
    Handlers are called in registration order.

    Args:
        event_type: The event class name (e.g., "SignalCreatedEvent").
        handler: A callable that accepts the event as its only argument.

    Example:
        def handle_signal_created(event: SignalCreatedEvent) -> None:
            # ... handle the event ...

        register_handler("SignalCreatedEvent", handle_signal_created)
    """
    if event_type not in EVENTS_MAP:
        EVENTS_MAP[event_type] = []
    EVENTS_MAP[event_type].append(handler)


def clear_registry() -> None:
    """
    Clear all registered events and handlers.

    Primarily useful for testing to ensure a clean state between tests.
    """
    EVENT_CLASSES.clear()
    EVENTS_MAP.clear()
