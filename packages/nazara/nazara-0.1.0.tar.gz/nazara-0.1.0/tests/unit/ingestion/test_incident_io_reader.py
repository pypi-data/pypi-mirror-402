import pytest

from nazara.ingestion.infrastructure.readers.incident_io_reader import IncidentIoReader


@pytest.fixture
def reader():
    return IncidentIoReader()


def test_reader_should_return_incident_io_as_source_system(reader):
    assert reader.get_source_system() == "incident_io"


@pytest.mark.parametrize(
    "payload,expected",
    [
        ({"event_type": "incident.created"}, True),
        ({"incident": {"id": "123"}}, True),
        ({}, False),
        ({"random_field": "value"}, False),
    ],
)
def test_reader_should_validate_payload_correctly(reader, payload, expected):
    assert reader.validate_payload(payload) is expected


def test_reader_should_parse_webhook_payload(reader):
    payload = {
        "event_type": "incident.created",
        "incident": {
            "id": "inc_123",
            "name": "Database connection failure",
            "summary": "Production DB is unreachable",
            "incident_status": {"category": "active"},
            "severity": {"name": "critical"},
            "created_at": "2024-01-15T10:30:00Z",
            "permalink": "https://app.incident.io/org/incidents/inc_123",
        },
    }

    result = reader.parse_payload(payload)

    assert result.source_system == "incident_io"
    assert result.source_identifier == "inc_123"
    assert result.title == "Database connection failure"
    assert result.description == "Production DB is unreachable"
    assert result.status == "investigating"
    assert result.severity == "critical"
    assert "event:incident.created" in result.tags


def test_reader_should_parse_direct_incident_payload(reader):
    payload = {
        "incident": {
            "id": "inc_456",
            "name": "API Gateway Timeout",
            "summary": "High latency on API calls",
            "incident_status": {"category": "triage"},
            "severity": {"name": "major"},
            "created_at": "2024-01-15T11:00:00Z",
        },
    }

    result = reader.parse_payload(payload)

    assert result.source_identifier == "inc_456"
    assert result.title == "API Gateway Timeout"
    assert result.status == "open"
    assert result.severity == "high"


def test_reader_should_parse_api_response_format(reader):
    payload = {
        "id": "inc_789",
        "name": "Cache Failure",
        "summary": "Redis cluster is down",
        "incident_status": {"category": "closed"},
        "severity": {"name": "minor"},
        "created_at": "2024-01-15T12:00:00Z",
        "resolved_at": "2024-01-15T14:00:00Z",
    }

    result = reader.parse_payload(payload)

    assert result.source_identifier == "inc_789"
    assert result.status == "resolved"
    assert result.severity == "medium"
    assert result.ended_at is not None


@pytest.mark.parametrize(
    "incident_status,expected_status",
    [
        ("triage", "open"),
        ("active", "investigating"),
        ("paused", "monitoring"),
        ("closed", "resolved"),
        ("declined", "closed"),
        ("merged", "closed"),
        ("canceled", "closed"),
        ("unknown", "open"),
    ],
)
def test_reader_should_map_status_correctly(reader, incident_status, expected_status):
    payload = {
        "incident": {
            "id": "test",
            "name": "Test",
            "incident_status": {"category": incident_status},
        },
    }
    result = reader.parse_payload(payload)
    assert result.status == expected_status


@pytest.mark.parametrize(
    "severity_name,expected_severity",
    [
        ("critical", "critical"),
        ("sev0", "critical"),
        ("p0", "critical"),
        ("major", "high"),
        ("sev1", "high"),
        ("p1", "high"),
        ("minor", "medium"),
        ("sev2", "medium"),
        ("p2", "medium"),
        ("cosmetic", "low"),
        ("sev3", "low"),
        ("p3", "low"),
        ("unknown", "medium"),
    ],
)
def test_reader_should_map_severity_correctly(reader, severity_name, expected_severity):
    payload = {
        "incident": {
            "id": "test",
            "name": "Test",
            "severity": {"name": severity_name},
        },
    }
    result = reader.parse_payload(payload)
    assert result.severity == expected_severity


def test_reader_should_extract_timeline(reader):
    payload = {
        "incident": {
            "id": "inc_timeline",
            "name": "Test Incident",
            "incident_updates": [
                {
                    "created_at": "2024-01-15T10:00:00Z",
                    "message": "Investigating the issue",
                    "updater": {"name": "John Doe"},
                },
                {
                    "created_at": "2024-01-15T11:00:00Z",
                    "message": "Root cause identified",
                    "updater": {"name": "Jane Smith"},
                },
            ],
        },
    }

    result = reader.parse_payload(payload)

    assert len(result.timeline) == 2
    assert result.timeline[0]["description"] == "Investigating the issue"
    assert result.timeline[0]["author"] == "John Doe"


def test_reader_should_extract_affected_services(reader):
    payload = {
        "incident": {
            "id": "inc_services",
            "name": "Multi-service Outage",
            "custom_field_values": [
                {
                    "custom_field": {"name": "Affected Services"},
                    "values": [
                        {"label": "api-gateway"},
                        {"label": "user-service"},
                    ],
                },
            ],
        },
    }

    result = reader.parse_payload(payload)

    assert "api-gateway" in result.affected_services
    assert "user-service" in result.affected_services


def test_reader_should_extract_tags(reader):
    payload = {
        "incident": {
            "id": "inc_tags",
            "name": "Test",
            "incident_type": {"name": "Security"},
            "severity": {"name": "critical"},
            "mode": "real",
        },
    }

    result = reader.parse_payload(payload)

    assert "incident_io" in result.tags
    assert "type:Security" in result.tags
    assert "severity:critical" in result.tags
    assert "mode:real" in result.tags


def test_reader_should_preserve_raw_payload(reader):
    payload = {
        "event_type": "incident.updated",
        "incident": {"id": "inc_raw", "name": "Test"},
    }

    result = reader.parse_payload(payload)

    assert result.raw_payload == payload
