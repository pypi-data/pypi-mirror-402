import pytest

from nazara.ingestion.infrastructure.readers.datadog_reader import DatadogReader


@pytest.fixture
def reader():
    return DatadogReader()


@pytest.fixture
def monitor_alert_payload():
    return {
        "alert_type": "error",
        "alert_status": "Triggered",
        "monitor_id": "12345",
        "monitor_name": "High CPU Usage",
        "title": "CPU Alert",
        "body": "CPU usage exceeded 90%",
        "priority": "p1",
        "tags": "service:api-gateway,env:production",
        "hostname": "web-01",
        "url": "https://app.datadoghq.com/monitors/12345",
        "date": 1704067200,
    }


@pytest.fixture
def span_payload():
    return {
        "trace_id": "abc123",
        "span_id": "def456",
        "service": "user-service",
        "resource_name": "GET /users",
        "operation_name": "http.request",
        "env": "staging",
        "error.message": "Connection timeout",
        "error.type": "TimeoutError",
        "error.stack": "at connect() line 42",
        "host": "app-server-01",
        "timestamp": 1704067200,
    }


@pytest.fixture
def event_payload():
    return {
        "id": "event_789",
        "event_type": "deployment",
        "title": "Deployed v2.3.1",
        "text": "New version deployed to production",
        "priority": "normal",
        "tags": ["service:billing", "env:production"],
        "host": "deploy-host",
        "url": "https://app.datadoghq.com/event/789",
        "date_happened": 1704067200,
    }


def test_reader_should_return_datadog_as_source_system(reader):
    assert reader.get_source_system() == "datadog"


@pytest.mark.parametrize(
    "payload,expected",
    [
        ({"alert_type": "error"}, True),
        ({"event_type": "deployment"}, True),
        ({"monitor_id": "123"}, True),
        ({"trace_id": "abc"}, True),
        ({"id": "event_1"}, True),
        ({}, False),
        ({"random_field": "value"}, False),
        (None, False),
    ],
)
def test_validate_payload_should_detect_valid_payloads(reader, payload, expected):
    assert reader.validate_payload(payload) is expected


def test_parse_monitor_alert_should_extract_source_system(reader, monitor_alert_payload):
    result = reader.parse_payload(monitor_alert_payload)
    assert result.source_system == "datadog"


def test_parse_monitor_alert_should_extract_source_identifier(reader, monitor_alert_payload):
    result = reader.parse_payload(monitor_alert_payload)
    assert result.source_identifier == "monitor:12345"


def test_parse_monitor_alert_should_extract_title(reader, monitor_alert_payload):
    result = reader.parse_payload(monitor_alert_payload)
    assert result.title == "CPU Alert"


def test_parse_monitor_alert_should_extract_description(reader, monitor_alert_payload):
    result = reader.parse_payload(monitor_alert_payload)
    assert result.description == "CPU usage exceeded 90%"


def test_parse_monitor_alert_should_map_severity_from_priority(reader, monitor_alert_payload):
    result = reader.parse_payload(monitor_alert_payload)
    assert result.severity == "critical"


def test_parse_monitor_alert_should_extract_service_from_tags(reader, monitor_alert_payload):
    result = reader.parse_payload(monitor_alert_payload)
    assert result.service == "api-gateway"


def test_parse_monitor_alert_should_extract_environment_from_tags(reader, monitor_alert_payload):
    result = reader.parse_payload(monitor_alert_payload)
    assert result.environment == "production"


def test_parse_monitor_alert_should_extract_host(reader, monitor_alert_payload):
    result = reader.parse_payload(monitor_alert_payload)
    assert result.host == "web-01"


def test_parse_monitor_alert_should_extract_source_url(reader, monitor_alert_payload):
    result = reader.parse_payload(monitor_alert_payload)
    assert result.source_url == "https://app.datadoghq.com/monitors/12345"


def test_parse_monitor_alert_should_set_info_severity_when_recovered(reader):
    payload = {
        "alert_type": "error",
        "alert_status": "Recovered",
        "monitor_id": "123",
    }
    result = reader.parse_payload(payload)
    assert result.severity == "info"


def test_parse_span_should_extract_source_identifier(reader, span_payload):
    result = reader.parse_payload(span_payload)
    assert result.source_identifier == "trace:abc123:span:def456"


def test_parse_span_should_set_event_type_as_error(reader, span_payload):
    result = reader.parse_payload(span_payload)
    assert result.event_type == "error"


def test_parse_span_should_build_apm_title(reader, span_payload):
    result = reader.parse_payload(span_payload)
    assert result.title == "[APM Error] user-service: GET /users"


def test_parse_span_should_extract_error_message(reader, span_payload):
    result = reader.parse_payload(span_payload)
    assert result.error_message == "Connection timeout"


def test_parse_span_should_extract_error_type(reader, span_payload):
    result = reader.parse_payload(span_payload)
    assert result.error_type == "TimeoutError"


def test_parse_span_should_extract_service(reader, span_payload):
    result = reader.parse_payload(span_payload)
    assert result.service == "user-service"


def test_parse_span_should_extract_environment(reader, span_payload):
    result = reader.parse_payload(span_payload)
    assert result.environment == "staging"


def test_parse_span_should_build_apm_source_url(reader, span_payload):
    result = reader.parse_payload(span_payload)
    assert result.source_url == "https://app.datadoghq.com/apm/trace/abc123"


def test_parse_event_should_extract_source_identifier(reader, event_payload):
    result = reader.parse_payload(event_payload)
    assert result.source_identifier == "event_789"


def test_parse_event_should_extract_title(reader, event_payload):
    result = reader.parse_payload(event_payload)
    assert result.title == "Deployed v2.3.1"


def test_parse_event_should_extract_description(reader, event_payload):
    result = reader.parse_payload(event_payload)
    assert result.description == "New version deployed to production"


def test_parse_event_should_map_event_type_for_deployment(reader, event_payload):
    result = reader.parse_payload(event_payload)
    assert result.event_type == "deployment"


def test_parse_event_should_extract_service_from_tags(reader, event_payload):
    result = reader.parse_payload(event_payload)
    assert result.service == "billing"


def test_parse_event_should_include_datadog_tag(reader, event_payload):
    result = reader.parse_payload(event_payload)
    assert "datadog" in result.tags


def test_parse_generic_should_handle_unknown_payload(reader):
    payload = {"unknown": "data", "title": "Some Alert"}
    result = reader.parse_payload(payload)
    assert result.source_system == "datadog"
    assert result.title == "Some Alert"
    assert result.event_type == "alert"


@pytest.mark.parametrize(
    "priority,expected_severity",
    [
        ("p1", "critical"),
        ("p2", "high"),
        ("p3", "medium"),
        ("p4", "low"),
        ("p5", "info"),
        ("high", "high"),
        ("normal", "medium"),
        ("low", "info"),
    ],
)
def test_parse_monitor_alert_should_map_priority_to_severity(reader, priority, expected_severity):
    payload = {
        "alert_type": "metric",
        "monitor_id": "123",
        "priority": priority,
    }
    result = reader.parse_payload(payload)
    assert result.severity == expected_severity


def test_parse_payload_should_preserve_raw_payload(reader, monitor_alert_payload):
    result = reader.parse_payload(monitor_alert_payload)
    assert result.raw_payload == monitor_alert_payload


def test_parse_payload_should_set_issue_key(reader, monitor_alert_payload):
    result = reader.parse_payload(monitor_alert_payload)
    assert result.issue_key is not None


def test_parse_span_should_extract_transaction(reader, span_payload):
    result = reader.parse_payload(span_payload)
    assert result.transaction == "GET /users"
