from dataclasses import dataclass
from datetime import UTC, datetime
from unittest.mock import Mock, patch
from uuid import UUID, uuid4

import pytest

from nazara.shared.event_bus.adapters import CeleryAsyncEventBus, InMemorySynchronousEventBus
from nazara.shared.event_bus.contracts import DomainEvent, EventBus, HasDomainEventsMixin
from nazara.shared.event_bus.provider import get_event_bus
from nazara.shared.event_bus.registry import (
    EVENT_CLASSES,
    EVENTS_MAP,
    clear_registry,
    register_event,
    register_handler,
)


@dataclass(frozen=True, kw_only=True)
class SampleEvent(DomainEvent):
    message: str
    sequence: int


@dataclass(frozen=True, kw_only=True)
class AnotherSampleEvent(DomainEvent):
    data: str


@pytest.fixture(autouse=True)
def clean_registry():
    clear_registry()
    yield
    clear_registry()


def test_domain_event_should_have_auto_generated_id():
    event = SampleEvent(message="test", sequence=1)

    assert isinstance(event.id, UUID)


def test_domain_event_should_have_auto_generated_timestamp():
    before = datetime.now(UTC)
    event = SampleEvent(message="test", sequence=1)
    after = datetime.now(UTC)

    assert before <= event.occurred_on <= after


def test_domain_event_should_be_immutable():
    event = SampleEvent(message="test", sequence=1)

    with pytest.raises(AttributeError):
        event.message = "changed"  # type: ignore[misc]


def test_domain_event_should_return_class_name_as_event_type():
    event = SampleEvent(message="test", sequence=1)

    assert event.event_type() == "SampleEvent"


def test_domain_event_should_serialize_to_dict():
    event_id = uuid4()
    occurred_on = datetime.now(UTC)
    event = SampleEvent(
        id=event_id,
        occurred_on=occurred_on,
        message="hello",
        sequence=42,
    )

    result = event.to_dict()

    assert result["id"] == event_id
    assert result["occurred_on"] == occurred_on
    assert result["message"] == "hello"
    assert result["sequence"] == 42


def test_domain_event_should_deserialize_from_dict():
    event_id = uuid4()
    occurred_on = datetime.now(UTC)
    data = {
        "id": event_id,
        "occurred_on": occurred_on,
        "message": "restored",
        "sequence": 99,
    }

    event = SampleEvent.from_dict(data)

    assert event.id == event_id
    assert event.occurred_on == occurred_on
    assert event.message == "restored"
    assert event.sequence == 99


def test_domain_event_should_ignore_extra_fields_when_deserializing():
    data = {
        "id": uuid4(),
        "occurred_on": datetime.now(UTC),
        "message": "test",
        "sequence": 1,
        "extra_field": "should be ignored",
    }

    event = SampleEvent.from_dict(data)

    assert event.message == "test"
    assert not hasattr(event, "extra_field")


def test_domain_event_should_survive_serialization_roundtrip():
    original = SampleEvent(message="roundtrip", sequence=123)

    data = original.to_dict()
    restored = SampleEvent.from_dict(data)

    assert restored.id == original.id
    assert restored.occurred_on == original.occurred_on
    assert restored.message == original.message
    assert restored.sequence == original.sequence


def test_register_event_should_add_to_event_classes():
    register_event(SampleEvent)

    assert "SampleEvent" in EVENT_CLASSES
    assert EVENT_CLASSES["SampleEvent"] is SampleEvent


def test_register_event_should_work_as_decorator():
    @register_event
    @dataclass(frozen=True, kw_only=True)
    class DecoratedEvent(DomainEvent):
        value: str

    assert "DecoratedEvent" in EVENT_CLASSES


def test_register_handler_should_add_to_events_map():
    handler = Mock()

    register_handler("SampleEvent", handler)

    assert "SampleEvent" in EVENTS_MAP
    assert handler in EVENTS_MAP["SampleEvent"]


def test_register_handler_should_allow_multiple_handlers_for_same_event():
    handler1 = Mock()
    handler2 = Mock()

    register_handler("SampleEvent", handler1)
    register_handler("SampleEvent", handler2)

    assert len(EVENTS_MAP["SampleEvent"]) == 2
    assert handler1 in EVENTS_MAP["SampleEvent"]
    assert handler2 in EVENTS_MAP["SampleEvent"]


def test_clear_registry_should_remove_all_events_and_handlers():
    register_event(SampleEvent)
    register_handler("SampleEvent", Mock())

    clear_registry()

    assert len(EVENT_CLASSES) == 0
    assert len(EVENTS_MAP) == 0


def test_in_memory_bus_should_call_registered_handler():
    handler = Mock()
    handler.__name__ = "test_handler"
    bus = InMemorySynchronousEventBus({"SampleEvent": [handler]})
    event = SampleEvent(message="test", sequence=1)

    bus.publish(event)

    handler.assert_called_once_with(event)


def test_in_memory_bus_should_call_multiple_handlers_in_order():
    handler1 = Mock()
    handler1.__name__ = "handler1"
    handler2 = Mock()
    handler2.__name__ = "handler2"
    bus = InMemorySynchronousEventBus({"SampleEvent": [handler1, handler2]})
    event = SampleEvent(message="test", sequence=1)

    bus.publish(event)

    handler1.assert_called_once_with(event)
    handler2.assert_called_once_with(event)


def test_in_memory_bus_should_handle_multiple_events():
    handler1 = Mock()
    handler1.__name__ = "handler1"
    handler2 = Mock()
    handler2.__name__ = "handler2"
    bus = InMemorySynchronousEventBus(
        {
            "SampleEvent": [handler1],
            "AnotherSampleEvent": [handler2],
        }
    )
    event1 = SampleEvent(message="first", sequence=1)
    event2 = AnotherSampleEvent(data="second")

    bus.publish(event1, event2)

    handler1.assert_called_once_with(event1)
    handler2.assert_called_once_with(event2)


def test_in_memory_bus_should_not_raise_when_no_handlers_registered():
    bus = InMemorySynchronousEventBus({})
    event = SampleEvent(message="test", sequence=1)

    bus.publish(event)  # Should not raise


def test_in_memory_bus_should_log_error_when_handler_fails():
    failing_handler = Mock(side_effect=Exception("Handler failed"))
    failing_handler.__name__ = "failing_handler"
    success_handler = Mock()
    success_handler.__name__ = "success_handler"
    bus = InMemorySynchronousEventBus(
        {
            "SampleEvent": [failing_handler, success_handler],
        }
    )
    event = SampleEvent(message="test", sequence=1)

    with patch("nazara.shared.event_bus.adapters.logger") as mock_logger:
        bus.publish(event)

    failing_handler.assert_called_once_with(event)
    success_handler.assert_called_once_with(event)
    mock_logger.error.assert_called_once()


def test_celery_bus_should_dispatch_to_celery_task():
    bus = CeleryAsyncEventBus()
    event = SampleEvent(message="async", sequence=42)

    with patch("nazara.shared.event_bus.tasks.process_domain_event") as mock_task:
        bus.publish(event)

    mock_task.delay.assert_called_once_with(
        event_type="SampleEvent",
        event_data=event.to_dict(),
    )


def test_celery_bus_should_dispatch_each_event_separately():
    bus = CeleryAsyncEventBus()
    event1 = SampleEvent(message="first", sequence=1)
    event2 = AnotherSampleEvent(data="second")

    with patch("nazara.shared.event_bus.tasks.process_domain_event") as mock_task:
        bus.publish(event1, event2)

    assert mock_task.delay.call_count == 2


def test_mixin_should_queue_event_for_later_publishing():
    class TestAggregate(HasDomainEventsMixin):
        pass

    aggregate = TestAggregate()
    event = SampleEvent(message="queued", sequence=1)

    aggregate.register_domain_event(event)

    assert len(aggregate._domain_events) == 1
    assert aggregate._domain_events[0] == event


def test_mixin_should_allow_multiple_events_to_be_queued():
    class TestAggregate(HasDomainEventsMixin):
        pass

    aggregate = TestAggregate()
    event1 = SampleEvent(message="first", sequence=1)
    event2 = SampleEvent(message="second", sequence=2)

    aggregate.register_domain_event(event1)
    aggregate.register_domain_event(event2)

    assert len(aggregate._domain_events) == 2


def test_mixin_should_publish_all_events_to_bus():
    class TestAggregate(HasDomainEventsMixin):
        pass

    aggregate = TestAggregate()
    event1 = SampleEvent(message="first", sequence=1)
    event2 = SampleEvent(message="second", sequence=2)
    aggregate.register_domain_event(event1)
    aggregate.register_domain_event(event2)

    mock_bus = Mock(spec=EventBus)
    aggregate.publish_domain_events(mock_bus)

    mock_bus.publish.assert_called_once_with(event1, event2)


def test_mixin_should_clear_queue_after_publishing():
    class TestAggregate(HasDomainEventsMixin):
        pass

    aggregate = TestAggregate()
    aggregate.register_domain_event(SampleEvent(message="test", sequence=1))

    mock_bus = Mock(spec=EventBus)
    aggregate.publish_domain_events(mock_bus)

    assert len(aggregate._domain_events) == 0


def test_get_event_bus_should_return_in_memory_bus_when_specified():
    bus = get_event_bus("in-memory")

    assert isinstance(bus, InMemorySynchronousEventBus)


def test_get_event_bus_should_return_celery_bus_when_specified():
    bus = get_event_bus("celery")

    assert isinstance(bus, CeleryAsyncEventBus)


def test_get_event_bus_should_use_settings_when_driver_not_specified(settings):
    settings.EVENT_BUS_DRIVER = "in-memory"

    bus = get_event_bus()

    assert isinstance(bus, InMemorySynchronousEventBus)


def test_get_event_bus_should_default_to_celery_when_setting_missing(settings):
    if hasattr(settings, "EVENT_BUS_DRIVER"):
        delattr(settings, "EVENT_BUS_DRIVER")

    bus = get_event_bus()

    assert isinstance(bus, CeleryAsyncEventBus)
