import pytest

from nazara.ingestion.infrastructure.readers.sentry_reader import SentryReader


@pytest.fixture
def reader():
    return SentryReader()


@pytest.fixture
def event_payload():
    return {
        "event": {
            "event_id": "abc123def456",
            "project": "api-gateway",
            "level": "error",
            "timestamp": 1704067200,
            "transaction": "POST /api/users",
            "release": "v2.3.1",
            "exception": {
                "values": [
                    {
                        "type": "ValueError",
                        "value": "Invalid user input",
                        "stacktrace": {
                            "frames": [
                                {
                                    "filename": "handlers.py",
                                    "lineno": 42,
                                    "function": "handle_request",
                                },
                                {
                                    "filename": "validators.py",
                                    "lineno": 15,
                                    "function": "validate_input",
                                },
                            ]
                        },
                    }
                ]
            },
            "tags": [
                ["environment", "production"],
                ["server_name", "web-01"],
                ["browser", "Chrome"],
            ],
            "fingerprint": ["{{ default }}", "ValueError"],
        },
        "url": "https://sentry.io/issues/12345",
    }


@pytest.fixture
def issue_payload():
    return {
        "data": {
            "issue": {
                "id": "issue_789",
                "title": "ValueError: Invalid user input",
                "level": "error",
                "firstSeen": "2024-01-01T00:00:00Z",
                "permalink": "https://sentry.io/issues/789",
                "culprit": "handlers.handle_request",
                "project": {"slug": "billing-service"},
                "metadata": {
                    "type": "ValueError",
                    "value": "Invalid user input",
                },
            }
        },
        "action": "created",
    }


@pytest.fixture
def generic_payload():
    return {
        "action": "alert_triggered",
        "data": {"message": "Threshold exceeded"},
        "url": "https://sentry.io/alerts/123",
    }


def test_reader_should_return_sentry_as_source_system(reader):
    assert reader.get_source_system() == "sentry"


@pytest.mark.parametrize(
    "payload,expected",
    [
        ({"event": {"event_id": "123"}}, True),
        ({"data": {"issue": {"id": "456"}}}, True),
        ({"action": "alert_triggered"}, True),
        ({}, False),
        ({"random_field": "value"}, False),
        (None, False),
    ],
)
def test_validate_payload_should_detect_valid_payloads(reader, payload, expected):
    assert reader.validate_payload(payload) is expected


def test_parse_event_should_extract_source_system(reader, event_payload):
    result = reader.parse_payload(event_payload)
    assert result.source_system == "sentry"


def test_parse_event_should_extract_source_identifier(reader, event_payload):
    result = reader.parse_payload(event_payload)
    assert result.source_identifier == "abc123def456"


def test_parse_event_should_build_title_from_exception(reader, event_payload):
    result = reader.parse_payload(event_payload)
    assert result.title == "ValueError: Invalid user input"


def test_parse_event_should_extract_description(reader, event_payload):
    result = reader.parse_payload(event_payload)
    assert result.description == "Invalid user input"


def test_parse_event_should_set_event_type_as_error(reader, event_payload):
    result = reader.parse_payload(event_payload)
    assert result.event_type == "error"


def test_parse_event_should_extract_error_type(reader, event_payload):
    result = reader.parse_payload(event_payload)
    assert result.error_type == "ValueError"


def test_parse_event_should_extract_error_message(reader, event_payload):
    result = reader.parse_payload(event_payload)
    assert result.error_message == "Invalid user input"


def test_parse_event_should_build_stacktrace(reader, event_payload):
    result = reader.parse_payload(event_payload)
    assert "handlers.py:42 in handle_request" in result.error_stacktrace
    assert "validators.py:15 in validate_input" in result.error_stacktrace


def test_parse_event_should_extract_environment_from_tags(reader, event_payload):
    result = reader.parse_payload(event_payload)
    assert result.environment == "production"


def test_parse_event_should_extract_host_from_tags(reader, event_payload):
    result = reader.parse_payload(event_payload)
    assert result.host == "web-01"


def test_parse_event_should_extract_transaction(reader, event_payload):
    result = reader.parse_payload(event_payload)
    assert result.transaction == "POST /api/users"


def test_parse_event_should_extract_release(reader, event_payload):
    result = reader.parse_payload(event_payload)
    assert result.release == "v2.3.1"


def test_parse_event_should_extract_source_url(reader, event_payload):
    result = reader.parse_payload(event_payload)
    assert result.source_url == "https://sentry.io/issues/12345"


@pytest.mark.parametrize(
    "level,expected_severity",
    [
        ("fatal", "critical"),
        ("error", "high"),
        ("warning", "medium"),
        ("info", "low"),
        ("debug", "info"),
    ],
)
def test_parse_event_should_map_level_to_severity(reader, level, expected_severity):
    payload = {
        "event": {
            "event_id": "test123",
            "level": level,
            "exception": {"values": [{}]},
            "tags": [],
        }
    }
    result = reader.parse_payload(payload)
    assert result.severity == expected_severity


def test_parse_issue_should_extract_source_identifier(reader, issue_payload):
    result = reader.parse_payload(issue_payload)
    assert result.source_identifier == "issue_789"


def test_parse_issue_should_extract_title(reader, issue_payload):
    result = reader.parse_payload(issue_payload)
    assert result.title == "ValueError: Invalid user input"


def test_parse_issue_should_extract_service_from_project(reader, issue_payload):
    result = reader.parse_payload(issue_payload)
    assert result.service == "billing-service"


def test_parse_issue_should_extract_source_url(reader, issue_payload):
    result = reader.parse_payload(issue_payload)
    assert result.source_url == "https://sentry.io/issues/789"


def test_parse_issue_should_extract_error_type_from_metadata(reader, issue_payload):
    result = reader.parse_payload(issue_payload)
    assert result.error_type == "ValueError"


def test_parse_issue_should_extract_error_message_from_metadata(reader, issue_payload):
    result = reader.parse_payload(issue_payload)
    assert result.error_message == "Invalid user input"


def test_parse_generic_should_handle_alert_payload(reader, generic_payload):
    result = reader.parse_payload(generic_payload)
    assert result.source_system == "sentry"
    assert result.title == "alert_triggered"
    assert result.event_type == "alert"


def test_parse_generic_should_extract_source_url(reader, generic_payload):
    result = reader.parse_payload(generic_payload)
    assert result.source_url == "https://sentry.io/alerts/123"


def test_parse_event_should_include_sentry_tag(reader, event_payload):
    result = reader.parse_payload(event_payload)
    assert "sentry" in result.tags


def test_parse_issue_should_include_action_tag(reader, issue_payload):
    result = reader.parse_payload(issue_payload)
    assert "action:created" in result.tags


def test_parse_payload_should_preserve_raw_payload(reader, event_payload):
    result = reader.parse_payload(event_payload)
    assert "event" in result.raw_payload


def test_parse_payload_should_generate_issue_key(reader, event_payload):
    result = reader.parse_payload(event_payload)
    assert result.issue_key != ""


def test_parse_event_should_handle_missing_exception(reader):
    payload = {
        "event": {
            "event_id": "test123",
            "level": "error",
            "tags": [],
        }
    }
    result = reader.parse_payload(payload)
    assert result.source_identifier == "test123"
    assert result.title == ": "


def test_parse_event_should_handle_empty_stacktrace(reader):
    payload = {
        "event": {
            "event_id": "test123",
            "level": "error",
            "exception": {"values": [{"type": "Error", "value": "msg"}]},
            "tags": [],
        }
    }
    result = reader.parse_payload(payload)
    assert result.error_stacktrace is None or result.error_stacktrace == ""
