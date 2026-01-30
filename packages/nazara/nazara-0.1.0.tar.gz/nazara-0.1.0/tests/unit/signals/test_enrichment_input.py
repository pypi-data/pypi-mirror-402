import uuid
from datetime import UTC, datetime

from nazara.shared.enrichment_input import EnrichmentInput, SupportsEnrichment
from nazara.signals.domain.models import CustomerCase, Incident, TechnicalIssue


def test_incident_to_enrichment_input_should_include_basic_fields():
    incident = Incident(
        id=uuid.uuid4(),
        title="Database outage",
        description="Primary DB unreachable",
        severity="critical",
        status="investigating",
        source_system="pagerduty",
        source_identifier="INC-123",
    )

    result = incident.to_enrichment_input()

    assert isinstance(result, EnrichmentInput)
    assert result.signal_type == "Incident"
    assert result.signal_id == incident.id
    assert result.title == "Database outage"
    assert "Primary DB unreachable" in result.content
    assert result.metadata["severity"] == "critical"
    assert result.metadata["status"] == "investigating"
    assert result.metadata["source_system"] == "pagerduty"


def test_incident_to_enrichment_input_should_include_impact_description():
    incident = Incident(
        id=uuid.uuid4(),
        title="API outage",
        description="API returning 503",
        impact_description="All customers unable to checkout",
        severity="critical",
        source_system="incidentio",
        source_identifier="INC-456",
    )

    result = incident.to_enrichment_input()

    assert "Impact: All customers unable to checkout" in result.content


def test_incident_to_enrichment_input_should_include_root_cause_description():
    incident = Incident(
        id=uuid.uuid4(),
        title="Memory leak",
        description="Service crashing",
        root_cause_description="Memory leak in cache module",
        severity="high",
        source_system="pagerduty",
        source_identifier="INC-789",
    )

    result = incident.to_enrichment_input()

    assert "Root Cause: Memory leak in cache module" in result.content


def test_incident_to_enrichment_input_should_include_timeline_summary():
    incident = Incident(
        id=uuid.uuid4(),
        title="Outage",
        description="Service down",
        timeline=[
            {"timestamp": "2024-01-15T10:00:00", "description": "Alert triggered"},
            {"timestamp": "2024-01-15T10:05:00", "description": "Team notified"},
            {"timestamp": "2024-01-15T10:10:00", "description": "Investigation started"},
            {"timestamp": "2024-01-15T10:15:00", "description": "Root cause found"},
            {"timestamp": "2024-01-15T10:20:00", "description": "Fix deployed"},
            {"timestamp": "2024-01-15T10:25:00", "description": "Monitoring"},
        ],
        severity="high",
        source_system="pagerduty",
        source_identifier="INC-999",
    )

    result = incident.to_enrichment_input()

    assert "Timeline (6 entries, showing last 5):" in result.content
    assert "Team notified" in result.content
    assert "Monitoring" in result.content


def test_incident_to_enrichment_input_should_include_affected_services():
    incident = Incident(
        id=uuid.uuid4(),
        title="Outage",
        description="Multiple services affected",
        affected_services=["api", "web", "worker"],
        severity="critical",
        source_system="pagerduty",
        source_identifier="INC-001",
    )

    result = incident.to_enrichment_input()

    assert result.metadata["affected_services"] == ["api", "web", "worker"]


def test_incident_to_enrichment_input_should_include_affected_regions():
    incident = Incident(
        id=uuid.uuid4(),
        title="Regional outage",
        description="US-East affected",
        affected_regions=["us-east-1", "us-east-2"],
        severity="critical",
        source_system="pagerduty",
        source_identifier="INC-002",
    )

    result = incident.to_enrichment_input()

    assert result.metadata["affected_regions"] == ["us-east-1", "us-east-2"]


def test_incident_to_enrichment_input_should_include_category():
    incident = Incident(
        id=uuid.uuid4(),
        title="Outage",
        description="Service down",
        category="infrastructure",
        severity="high",
        source_system="pagerduty",
        source_identifier="INC-003",
    )

    result = incident.to_enrichment_input()

    assert result.metadata["category"] == "infrastructure"


def test_incident_to_enrichment_input_should_include_tags_in_context():
    incident = Incident(
        id=uuid.uuid4(),
        title="Outage",
        description="Service down",
        tags=["database", "critical", "customer-impact"],
        severity="high",
        source_system="pagerduty",
        source_identifier="INC-004",
    )

    result = incident.to_enrichment_input()

    assert result.context["tags"] == ["database", "critical", "customer-impact"]


def test_incident_to_enrichment_input_should_include_timestamps_in_context():
    started = datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC)
    ended = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)

    incident = Incident(
        id=uuid.uuid4(),
        title="Outage",
        description="Service down",
        started_at=started,
        ended_at=ended,
        severity="high",
        source_system="pagerduty",
        source_identifier="INC-005",
    )

    result = incident.to_enrichment_input()

    assert "started_at" in result.context
    assert "ended_at" in result.context


def test_customer_case_to_enrichment_input_should_include_basic_fields():
    case = CustomerCase(
        id=uuid.uuid4(),
        title="Cannot login",
        description="User reports login issues",
        customer_id="cust-123",
        severity="high",
        status="open",
        priority=1,
        source_system="intercom",
        source_identifier="CASE-123",
    )

    result = case.to_enrichment_input()

    assert isinstance(result, EnrichmentInput)
    assert result.signal_type == "CustomerCase"
    assert result.signal_id == case.id
    assert result.title == "Cannot login"
    assert "User reports login issues" in result.content
    assert result.metadata["severity"] == "high"
    assert result.metadata["status"] == "open"
    assert result.metadata["priority"] == 1


def test_customer_case_to_enrichment_input_should_include_conversation():
    case = CustomerCase(
        id=uuid.uuid4(),
        title="Billing issue",
        description="Overcharged",
        customer_id="cust-456",
        conversation=[
            {"author": "Customer", "body": "I was charged twice"},
            {"author": "Agent", "body": "Let me check your account"},
            {"author": "Customer", "body": "Please refund ASAP"},
        ],
        severity="medium",
        source_system="zendesk",
        source_identifier="CASE-456",
    )

    result = case.to_enrichment_input()

    assert "Conversation (3 messages, showing last 10):" in result.content
    assert "[Customer]: I was charged twice" in result.content
    assert "[Agent]: Let me check your account" in result.content
    assert "[Customer]: Please refund ASAP" in result.content


def test_customer_case_to_enrichment_input_should_truncate_long_messages():
    long_message = "x" * 600  # Longer than 500 char limit
    case = CustomerCase(
        id=uuid.uuid4(),
        title="Issue",
        description="Problem",
        customer_id="cust-789",
        conversation=[{"author": "Customer", "body": long_message}],
        severity="low",
        source_system="intercom",
        source_identifier="CASE-789",
    )

    result = case.to_enrichment_input()

    assert "x" * 500 + "..." in result.content
    assert "x" * 600 not in result.content


def test_customer_case_to_enrichment_input_should_show_last_10_messages():
    case = CustomerCase(
        id=uuid.uuid4(),
        title="Long thread",
        description="Many messages",
        customer_id="cust-999",
        conversation=[{"author": f"User{i}", "body": f"Message {i}"} for i in range(15)],
        severity="low",
        source_system="intercom",
        source_identifier="CASE-999",
    )

    result = case.to_enrichment_input()

    assert "Conversation (15 messages, showing last 10):" in result.content
    assert "[User5]: Message 5" in result.content
    assert "[User14]: Message 14" in result.content
    assert "[User0]: Message 0" not in result.content


def test_customer_case_to_enrichment_input_should_exclude_customer_pii():
    case = CustomerCase(
        id=uuid.uuid4(),
        title="Issue",
        description="Problem",
        customer_id="cust-pii",
        customer_email="secret@example.com",
        customer_name="John Secret",
        severity="low",
        source_system="intercom",
        source_identifier="CASE-PII",
    )

    result = case.to_enrichment_input()

    assert "customer_id" not in result.metadata
    assert "customer_email" not in result.metadata
    assert "customer_name" not in result.metadata
    assert "cust-pii" not in result.content
    assert "secret@example.com" not in result.content
    assert "John Secret" not in result.content


def test_customer_case_to_enrichment_input_should_include_category():
    case = CustomerCase(
        id=uuid.uuid4(),
        title="Billing",
        description="Overcharge",
        customer_id="cust-cat",
        category="billing",
        severity="medium",
        source_system="intercom",
        source_identifier="CASE-CAT",
    )

    result = case.to_enrichment_input()

    assert result.metadata["category"] == "billing"


def test_customer_case_to_enrichment_input_should_include_total_messages_in_context():
    case = CustomerCase(
        id=uuid.uuid4(),
        title="Thread",
        description="Messages",
        customer_id="cust-cnt",
        conversation=[{"author": "User", "body": f"Msg {i}"} for i in range(25)],
        severity="low",
        source_system="intercom",
        source_identifier="CASE-CNT",
    )

    result = case.to_enrichment_input()

    assert result.context["total_messages"] == 25


def test_technical_issue_to_enrichment_input_should_include_basic_fields():
    issue = TechnicalIssue(
        id=uuid.uuid4(),
        title="NullPointerException",
        last_message="Error at UserService.java:42",
        provider="sentry",
        issue_key="SENTRY-123",
        environment="production",
        service="api-gateway",
        severity="high",
        status="active",
        occurrences_total=150,
    )

    result = issue.to_enrichment_input()

    assert isinstance(result, EnrichmentInput)
    assert result.signal_type == "TechnicalIssue"
    assert result.signal_id == issue.id
    assert result.title == "NullPointerException"
    assert "Error at UserService.java:42" in result.content
    assert result.metadata["severity"] == "high"
    assert result.metadata["status"] == "active"
    assert result.metadata["environment"] == "production"
    assert result.metadata["service"] == "api-gateway"
    assert result.metadata["provider"] == "sentry"
    assert result.metadata["occurrences_total"] == 150


def test_technical_issue_to_enrichment_input_should_include_sample_payload():
    issue = TechnicalIssue(
        id=uuid.uuid4(),
        title="Error",
        last_message="Something went wrong",
        provider="sentry",
        issue_key="SENTRY-456",
        environment="staging",
        service="worker",
        sample_payload={
            "error": "NullPointer",
            "stack": ["frame1", "frame2"],
        },
    )

    result = issue.to_enrichment_input()

    assert "Sample Payload:" in result.content
    assert "NullPointer" in result.content


def test_technical_issue_to_enrichment_input_should_truncate_large_sample_payload():
    large_payload = {"data": "x" * 3000}  # Larger than 2KB
    issue = TechnicalIssue(
        id=uuid.uuid4(),
        title="Error",
        last_message="Big payload",
        provider="datadog",
        issue_key="DD-789",
        environment="production",
        service="api",
        sample_payload=large_payload,
    )

    result = issue.to_enrichment_input()

    assert "Sample Payload:" in result.content
    assert "[truncated]" in result.content


def test_technical_issue_to_enrichment_input_should_fallback_title_when_none():
    issue = TechnicalIssue(
        id=uuid.uuid4(),
        title=None,
        last_message="Error occurred",
        provider="newrelic",
        issue_key="NR-001",
        environment="production",
        service="web",
    )

    result = issue.to_enrichment_input()

    assert result.title == "newrelic:NR-001"


def test_technical_issue_to_enrichment_input_should_include_category():
    issue = TechnicalIssue(
        id=uuid.uuid4(),
        title="DB Error",
        last_message="Connection timeout",
        provider="sentry",
        issue_key="SENTRY-CAT",
        environment="production",
        service="api",
        category="database",
    )

    result = issue.to_enrichment_input()

    assert result.metadata["category"] == "database"


def test_technical_issue_to_enrichment_input_should_include_timestamps_in_context():
    first_seen = datetime(2024, 1, 10, 8, 0, 0, tzinfo=UTC)
    last_seen = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)

    issue = TechnicalIssue(
        id=uuid.uuid4(),
        title="Recurring Error",
        last_message="Still happening",
        provider="sentry",
        issue_key="SENTRY-TIME",
        environment="production",
        service="api",
        first_seen_at=first_seen,
        last_seen_at=last_seen,
    )

    result = issue.to_enrichment_input()

    assert "first_seen_at" in result.context
    assert "last_seen_at" in result.context


def test_incident_should_implement_supports_enrichment_protocol():
    incident = Incident(
        id=uuid.uuid4(),
        title="Test",
        description="Test",
        severity="low",
        source_system="test",
        source_identifier="test-1",
    )

    assert isinstance(incident, SupportsEnrichment)


def test_customer_case_should_implement_supports_enrichment_protocol():
    case = CustomerCase(
        id=uuid.uuid4(),
        title="Test",
        description="Test",
        customer_id="test",
        severity="low",
        source_system="test",
        source_identifier="test-2",
    )

    assert isinstance(case, SupportsEnrichment)


def test_technical_issue_should_implement_supports_enrichment_protocol():
    issue = TechnicalIssue(
        id=uuid.uuid4(),
        title="Test",
        provider="test",
        issue_key="test-3",
        environment="test",
        service="test",
    )

    assert isinstance(issue, SupportsEnrichment)
