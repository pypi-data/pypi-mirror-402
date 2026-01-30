from uuid import uuid4

import pytest

from nazara.shared.event_bus.registry import EVENT_CLASSES, clear_registry
from nazara.signals.domain.events import SignalCreatedEvent, SignalUpdatedEvent


@pytest.fixture(autouse=True)
def clean_registry():
    clear_registry()
    # Re-import to trigger registration
    import importlib

    import nazara.signals.domain.events

    importlib.reload(nazara.signals.domain.events)
    yield
    clear_registry()


@pytest.mark.parametrize(
    "event_class",
    [SignalCreatedEvent, SignalUpdatedEvent],
)
def test_signal_event_should_be_registered_in_event_classes(event_class):
    assert event_class.__name__ in EVENT_CLASSES
    assert EVENT_CLASSES[event_class.__name__].__name__ == event_class.__name__


def test_signal_created_event_should_serialize_and_deserialize():
    signal_id = uuid4()
    event = SignalCreatedEvent(signal_type="Incident", signal_id=signal_id)

    data = event.to_dict()
    restored = SignalCreatedEvent.from_dict(data)

    assert restored.signal_type == "Incident"
    assert restored.signal_id == signal_id
    assert restored.id == event.id
    assert restored.occurred_on == event.occurred_on


def test_signal_updated_event_should_serialize_and_deserialize():
    signal_id = uuid4()
    event = SignalUpdatedEvent(
        signal_type="TechnicalIssue",
        signal_id=signal_id,
        changed_fields=("title", "description"),
    )

    data = event.to_dict()
    restored = SignalUpdatedEvent.from_dict(data)

    assert restored.signal_type == "TechnicalIssue"
    assert restored.signal_id == signal_id
    assert restored.changed_fields == ("title", "description")


@pytest.mark.parametrize(
    "event_class,kwargs",
    [
        (SignalCreatedEvent, {"signal_type": "CustomerCase", "signal_id": uuid4()}),
        (
            SignalUpdatedEvent,
            {"signal_type": "Incident", "signal_id": uuid4(), "changed_fields": ("status",)},
        ),
    ],
)
def test_signal_event_should_return_correct_event_type(event_class, kwargs):
    event = event_class(**kwargs)
    assert event.event_type() == event_class.__name__


def test_signal_events_should_be_immutable():
    event = SignalCreatedEvent(signal_type="Incident", signal_id=uuid4())

    with pytest.raises(AttributeError):
        event.signal_type = "CustomerCase"  # type: ignore[misc]
