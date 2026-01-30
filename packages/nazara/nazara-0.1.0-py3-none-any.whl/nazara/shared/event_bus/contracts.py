from abc import ABC, abstractmethod
from collections import deque
from collections.abc import Callable
from dataclasses import asdict, dataclass, field, fields, is_dataclass
from datetime import UTC, datetime
from typing import Any, TypeVar
from uuid import UUID, uuid4

E = TypeVar("E", bound="DomainEvent")

EventHandler = Callable[[E], None]
EventName = str


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    """
    Base class for all domain events.

    Immutable (frozen) to ensure events are not modified after creation.
    Provides serialization/deserialization for Celery task transport.

    Attributes:
        id: Unique identifier for this event instance.
        occurred_on: Timestamp when the event was created.
    """

    id: UUID = field(default_factory=uuid4)
    occurred_on: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize event for task queue transport.

        Returns:
            Dictionary representation of the event with all fields.

        Raises:
            TypeError: If the event class is not a dataclass.
        """
        if not is_dataclass(self):
            raise TypeError(f"{type(self).__name__} must be a dataclass")
        return asdict(self)

    @classmethod
    def from_dict(cls: type[E], data: dict[str, Any]) -> E:
        """
        Deserialize event from task queue.

        Args:
            data: Dictionary containing event field values.

        Returns:
            Reconstructed event instance.

        Raises:
            TypeError: If the event class is not a dataclass.
        """
        if not is_dataclass(cls):
            raise TypeError(f"{cls.__name__} must be a dataclass")
        field_names = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in field_names})

    def event_type(self) -> EventName:
        """
        Return the event class name for registry lookup.

        Returns:
            The class name as the event type identifier.
        """
        return self.__class__.__name__


class EventBus(ABC):
    """
    Abstract event bus interface.

    Implementations determine delivery mechanism:
    - InMemorySynchronousEventBus: for testing
    - CeleryAsyncEventBus: for production async delivery
    """

    @abstractmethod
    def publish(self, *domain_events: DomainEvent) -> None:
        """
        Publish one or more domain events.

        Args:
            domain_events: Events to publish to registered handlers.
        """
        ...


class HasDomainEventsMixin:
    """
    Mixin for entities that produce domain events.

    Events are collected during business operations and published
    after successful persistence via publish_domain_events().

    Usage:
        class MyAggregate(HasDomainEventsMixin, BaseModel):
            def do_something(self):
                # ... business logic ...
                self.register_domain_event(SomethingHappened(...))

        # After saving:
        aggregate.publish_domain_events(event_bus)
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._domain_events: deque[DomainEvent] = deque()

    def register_domain_event(self, event: DomainEvent) -> None:
        """
        Queue an event to be published after persistence.

        Args:
            event: The domain event to queue.
        """
        self._domain_events.append(event)

    def publish_domain_events(self, event_bus: EventBus) -> None:
        """
        Publish all queued events and clear the queue.

        Args:
            event_bus: The event bus to publish events to.
        """
        event_bus.publish(*list(self._domain_events))
        self._domain_events.clear()
