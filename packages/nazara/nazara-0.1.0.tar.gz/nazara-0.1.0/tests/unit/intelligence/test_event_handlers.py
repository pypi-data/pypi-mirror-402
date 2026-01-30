from unittest.mock import patch
from uuid import uuid4

import pytest

from nazara.shared.event_bus.registry import EVENTS_MAP, clear_registry
from nazara.signals.domain.events import SignalCreatedEvent, SignalUpdatedEvent


@pytest.fixture(autouse=True)
def clean_registry():
    clear_registry()
    # Re-import to trigger registration
    import importlib

    import nazara.intelligence.application.event_handlers
    import nazara.signals.domain.events

    importlib.reload(nazara.signals.domain.events)
    importlib.reload(nazara.intelligence.application.event_handlers)
    yield
    clear_registry()


@pytest.mark.parametrize(
    "event_name,handler_name",
    [
        ("SignalCreatedEvent", "handle_signal_created"),
        ("SignalUpdatedEvent", "handle_signal_updated"),
    ],
)
def test_signal_handler_should_be_registered(event_name, handler_name):
    assert event_name in EVENTS_MAP
    handlers = EVENTS_MAP[event_name]
    handler_names = [h.__name__ for h in handlers]
    assert handler_name in handler_names


@pytest.mark.parametrize(
    "signal_type,task_name",
    [
        ("Incident", "enrich_incident_task"),
        ("CustomerCase", "enrich_customer_case_task"),
        ("TechnicalIssue", "enrich_technical_issue_task"),
    ],
)
def test_handle_signal_created_should_enqueue_correct_task(signal_type, task_name):
    from nazara.intelligence.application.event_handlers import handle_signal_created

    with patch(f"nazara.intelligence.infrastructure.messaging.tasks.{task_name}") as mock_task:
        signal_id = uuid4()
        event = SignalCreatedEvent(signal_type=signal_type, signal_id=signal_id)

        handle_signal_created(event)

        # The task is called with the appropriate id parameter name
        id_param_name = {
            "Incident": "incident_id",
            "CustomerCase": "case_id",
            "TechnicalIssue": "issue_id",
        }[signal_type]
        mock_task.delay.assert_called_once_with(**{id_param_name: str(signal_id)})


@pytest.mark.parametrize(
    "changed_fields,should_trigger",
    [
        (("title", "status"), True),
        (("status", "severity"), False),
        (("description",), True),
        (("summary",), True),
    ],
)
def test_handle_signal_updated_should_trigger_enrichment_when_content_changes(
    changed_fields, should_trigger
):
    from nazara.intelligence.application.event_handlers import handle_signal_updated

    with patch(
        "nazara.intelligence.infrastructure.messaging.tasks.enrich_incident_task"
    ) as mock_task:
        signal_id = uuid4()
        event = SignalUpdatedEvent(
            signal_type="Incident",
            signal_id=signal_id,
            changed_fields=changed_fields,
        )

        handle_signal_updated(event)

        if should_trigger:
            mock_task.delay.assert_called_once_with(
                incident_id=str(signal_id),
                force=True,
            )
        else:
            mock_task.delay.assert_not_called()
