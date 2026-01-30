import pytest
from django.utils import timezone

from nazara.shared.domain.dtos.signal_data import IncidentData
from nazara.shared.domain.value_objects.types import ProcessingResult


@pytest.mark.django_db
def test_from_data_should_create_and_update_incident(create_incident):
    source_id = f"test_{timezone.now().timestamp()}"
    now = timezone.now()
    dto = IncidentData(
        source_system="incident_io",
        source_identifier=source_id,
        source_url="https://example.com/incident/1",
        title="Integration Test Incident",
        description="Testing create/update",
        status="investigating",
        severity="high",
        affected_services=("test-service",),
        started_at=now,
        tags=("test",),
        timeline=(
            {
                "timestamp": now.isoformat(),
                "description": "Created",
                "author": "Test",
            },
        ),
    )

    result1 = create_incident.from_data(dto)
    assert result1 == ProcessingResult.CREATED

    dto2 = IncidentData(
        source_system="incident_io",
        source_identifier=source_id,
        source_url="https://example.com/incident/1",
        title="Integration Test Incident",
        description="Testing create/update",
        status="resolved",
        severity="high",
        affected_services=("test-service",),
        started_at=now,
        tags=("test",),
        timeline=(
            {
                "timestamp": now.isoformat(),
                "description": "Created",
                "author": "Test",
            },
        ),
    )
    result2 = create_incident.from_data(dto2)
    assert result2 == ProcessingResult.UPDATED


@pytest.mark.django_db
def test_from_data_should_skip_duplicate_content(create_incident):
    source_id = f"dedup_test_{timezone.now().timestamp()}"
    dto = IncidentData(
        source_system="incident_io",
        source_identifier=source_id,
        title="Dedup Test",
        description="Testing deduplication",
        status="open",
        severity="medium",
    )

    result1 = create_incident.from_data(dto)
    result2 = create_incident.from_data(dto)
    result3 = create_incident.from_data(dto)

    assert result1 == ProcessingResult.CREATED
    assert result2 == ProcessingResult.SKIPPED
    assert result3 == ProcessingResult.SKIPPED
