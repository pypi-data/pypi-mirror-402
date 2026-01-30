from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from nazara.shared.domain.dtos.signal_data import IncidentData
from nazara.shared.domain.value_objects.types import ProcessingResult
from nazara.signals.application.incident import CreateIncident
from nazara.signals.domain.models import Incident, SeverityChoices, StatusChoices


@pytest.fixture
def mock_incident_repo():
    return MagicMock()


@pytest.fixture
def sample_dto():
    return IncidentData(
        source_system="incident_io",
        source_identifier="inc_123",
        source_url="https://app.incident.io/org/incidents/inc_123",
        title="Database connection failure",
        description="Production DB is unreachable",
        status="investigating",
        severity="critical",
        affected_services=("api-gateway", "user-service"),
        affected_regions=("us-east-1",),
        started_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC),
        tags=("incident_io", "production"),
        timeline=(
            {
                "timestamp": "2024-01-15T10:30:00Z",
                "description": "Incident created",
                "author": "System",
            },
        ),
        raw_payload={"id": "inc_123"},
    )


@patch("nazara.signals.application.incident.transaction")
def test_from_data_should_create_new_incident(
    mock_tx, mock_incident_repo, spy_event_bus, sample_dto
):
    service = CreateIncident(incident_repo=mock_incident_repo, event_bus=spy_event_bus)
    mock_incident_repo.get_by_source.return_value = None
    mock_incident_repo.save.return_value = (
        Incident(title="Database connection failure"),
        True,
    )

    result = service.from_data(sample_dto)

    assert result == ProcessingResult.CREATED
    mock_incident_repo.get_by_source.assert_called_once_with("incident_io", "inc_123")
    mock_incident_repo.save.assert_called_once()
    mock_tx.on_commit.assert_called_once()


@patch("nazara.signals.application.incident.transaction")
def test_from_data_should_update_existing_incident(
    mock_tx, mock_incident_repo, spy_event_bus, sample_dto
):
    service = CreateIncident(incident_repo=mock_incident_repo, event_bus=spy_event_bus)
    existing_incident = Incident(
        title="Database connection failure",
        timeline=[
            {
                "timestamp": datetime(2024, 1, 15, 10, 0, 0).isoformat(),
                "description": "Initial alert",
                "author": "Monitor",
            }
        ],
    )
    mock_incident_repo.get_by_source.return_value = existing_incident
    mock_incident_repo.save.return_value = (existing_incident, True)

    result = service.from_data(sample_dto)

    assert result == ProcessingResult.UPDATED
    mock_incident_repo.save.assert_called_once()


@patch("nazara.signals.application.incident.transaction")
def test_from_data_should_merge_timeline(mock_tx, mock_incident_repo, spy_event_bus):
    service = CreateIncident(incident_repo=mock_incident_repo, event_bus=spy_event_bus)
    existing_incident = Incident(
        title="Test",
        timeline=[
            {
                "timestamp": datetime(2024, 1, 15, 10, 0, 0).isoformat(),
                "description": "First entry",
                "author": "System",
            },
        ],
    )
    mock_incident_repo.get_by_source.return_value = existing_incident
    mock_incident_repo.save.return_value = (existing_incident, True)

    dto = IncidentData(
        source_system="incident_io",
        source_identifier="inc_123",
        title="Test",
        description="Test incident",
        timeline=(
            {
                "timestamp": "2024-01-15T11:00:00Z",
                "description": "Second entry",
                "author": "User",
            },
        ),
    )

    service.from_data(dto)

    mock_incident_repo.save.assert_called_once()
    saved_incident = mock_incident_repo.save.call_args[0][0]
    assert len(saved_incident.timeline) == 2


@patch("nazara.signals.application.incident.transaction")
def test_from_data_should_return_failed_when_missing_source_identity(
    mock_tx, mock_incident_repo, spy_event_bus
):
    service = CreateIncident(incident_repo=mock_incident_repo, event_bus=spy_event_bus)
    dto = IncidentData(
        source_system="",
        source_identifier="",
        title="Test",
        description="Test",
    )

    result = service.from_data(dto)

    assert result == ProcessingResult.FAILED
    mock_incident_repo.get_by_source.assert_not_called()


@pytest.mark.parametrize(
    "status_str,expected_status",
    [
        ("open", StatusChoices.OPEN),
        ("investigating", StatusChoices.INVESTIGATING),
        ("identified", StatusChoices.IDENTIFIED),
        ("monitoring", StatusChoices.MONITORING),
        ("resolved", StatusChoices.RESOLVED),
        ("closed", StatusChoices.CLOSED),
        ("OPEN", StatusChoices.OPEN),
        ("unknown", StatusChoices.OPEN),
    ],
)
def test_map_status_should_return_correct_status(
    mock_incident_repo, spy_event_bus, status_str, expected_status
):
    service = CreateIncident(incident_repo=mock_incident_repo, event_bus=spy_event_bus)
    result = service._map_status(status_str)
    assert result == expected_status


@pytest.mark.parametrize(
    "severity_str,expected_severity",
    [
        ("critical", SeverityChoices.CRITICAL),
        ("high", SeverityChoices.HIGH),
        ("medium", SeverityChoices.MEDIUM),
        ("low", SeverityChoices.LOW),
        ("info", SeverityChoices.INFO),
        ("CRITICAL", SeverityChoices.CRITICAL),
        ("unknown", SeverityChoices.MEDIUM),
    ],
)
def test_map_severity_should_return_correct_severity(
    mock_incident_repo, spy_event_bus, severity_str, expected_severity
):
    service = CreateIncident(incident_repo=mock_incident_repo, event_bus=spy_event_bus)
    result = service._map_severity(severity_str)
    assert result == expected_severity


@patch("nazara.signals.application.incident.transaction")
def test_from_data_should_return_failed_when_exception_occurs(
    mock_tx, mock_incident_repo, spy_event_bus, sample_dto
):
    service = CreateIncident(incident_repo=mock_incident_repo, event_bus=spy_event_bus)
    mock_incident_repo.get_by_source.side_effect = Exception("Database error")

    result = service.from_data(sample_dto)

    assert result == ProcessingResult.FAILED


def test_dto_to_model_data_should_extract_all_fields(mock_incident_repo, spy_event_bus, sample_dto):
    service = CreateIncident(incident_repo=mock_incident_repo, event_bus=spy_event_bus)
    data = service._dto_to_model_data(sample_dto)

    assert data["title"] == "Database connection failure"
    assert data["description"] == "Production DB is unreachable"
    assert data["status"] == "investigating"
    assert data["severity"] == "critical"
    assert data["source_system"] == "incident_io"
    assert data["source_identifier"] == "inc_123"
    assert data["affected_services"] == ["api-gateway", "user-service"]
    assert data["tags"] == ["incident_io", "production"]


def test_dto_to_model_data_should_truncate_title(mock_incident_repo, spy_event_bus):
    service = CreateIncident(incident_repo=mock_incident_repo, event_bus=spy_event_bus)
    long_title = "A" * 600
    dto = IncidentData(
        source_system="test",
        source_identifier="123",
        title=long_title,
        description="Test",
    )

    data = service._dto_to_model_data(dto)

    assert len(data["title"]) == 500


def test_dto_to_model_data_should_truncate_description(mock_incident_repo, spy_event_bus):
    service = CreateIncident(incident_repo=mock_incident_repo, event_bus=spy_event_bus)
    long_description = "B" * 6000
    dto = IncidentData(
        source_system="test",
        source_identifier="123",
        title="Test",
        description=long_description,
    )

    data = service._dto_to_model_data(dto)

    assert len(data["description"]) == 5000


@patch("nazara.signals.application.incident.transaction")
def test_from_data_should_skip_unchanged_incident(
    mock_tx, mock_incident_repo, spy_event_bus, sample_dto
):
    service = CreateIncident(incident_repo=mock_incident_repo, event_bus=spy_event_bus)
    existing_incident = Incident(
        title="Database connection failure",
        timeline=[],
    )
    mock_incident_repo.get_by_source.return_value = existing_incident
    mock_incident_repo.save.return_value = (existing_incident, False)

    result = service.from_data(sample_dto)

    assert result == ProcessingResult.SKIPPED
    mock_incident_repo.save.assert_called_once()
    mock_tx.on_commit.assert_not_called()
