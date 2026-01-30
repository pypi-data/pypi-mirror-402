from datetime import UTC, datetime, timedelta
from unittest import mock

import pytest

from nazara.shared.event_bus.contracts import DomainEvent, EventBus


class SpyEventBus(EventBus):
    """Test event bus that records published events for assertions."""

    def __init__(self) -> None:
        self.published_events: list[DomainEvent] = []

    def publish(self, *domain_events: DomainEvent) -> None:
        self.published_events.extend(domain_events)

    def clear(self) -> None:
        self.published_events.clear()


@pytest.fixture
def spy_event_bus():
    return SpyEventBus()


@pytest.fixture
def time_window():
    now = datetime.now(UTC)
    return {
        "start": now - timedelta(hours=1),
        "end": now + timedelta(hours=1),
    }


@pytest.fixture
def di_container():
    from nazara.containers import ApplicationContainer

    container = ApplicationContainer()
    container.shared.config.from_dict(
        {
            "secrets": {
                "resolver_type": "dict",
                "file_path": None,
                "env_prefix": "TEST_",
                "dict_secrets": {
                    "test_secret": "test_value",
                    "sentry_api_key": "test-sentry-key",
                    "incident_io_api_key": "test-incident-io-key",
                },
            }
        }
    )
    return container


@pytest.fixture
def di_container_with_mocks(di_container):
    with di_container.signals.event_repository.override(mock.Mock()):
        with di_container.signals.issue_repository.override(mock.Mock()):
            with di_container.signals.incident_repository.override(mock.Mock()):
                with di_container.ingestion.config_repository.override(mock.Mock()):
                    yield di_container


@pytest.fixture
def reset_global_container():
    from nazara.containers import reset_container

    yield
    reset_container()
