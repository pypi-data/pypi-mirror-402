import pytest
from django.test import Client
from django.utils import timezone

from nazara.intelligence.domain.models import DomainProfile


@pytest.fixture
def domain_profile(db):
    DomainProfile.objects.filter(is_active=True).update(is_active=False)
    return DomainProfile.objects.create(
        name="Test Profile",
        description="Test description",
        is_active=False,
    )


@pytest.fixture
def active_profile(db):
    DomainProfile.objects.filter(is_active=True).update(is_active=False)
    return DomainProfile.objects.create(
        name="Active Test Profile",
        description="Active test profile for enrichment",
        is_active=True,
    )


@pytest.fixture
def client() -> Client:
    return Client()


@pytest.fixture
def customer_case(db):
    from nazara.signals.infrastructure.django.app.models import CustomerCaseModel

    return CustomerCaseModel.objects.create(
        customer_id="user_123",
        customer_email="user@example.com",
        customer_name="John Doe",
        title="Connection issues reported",
        description="User reports intermittent connection failures",
        source_system="slack",
        source_identifier="C123456",
        source_url="https://slack.com/archives/C123456",
        started_at=timezone.now(),
        status="open",
        severity="medium",
    )


@pytest.fixture
def incident(db):
    from nazara.signals.infrastructure.django.app.models import IncidentModel

    return IncidentModel.objects.create(
        title="API Gateway Degradation",
        description="Increased latency observed on API gateway",
        source_system="pagerduty",
        source_identifier="INC-123",
        source_url="https://pagerduty.com/incidents/INC-123",
        started_at=timezone.now(),
        status="investigating",
        severity="high",
        affected_services=["api", "web"],
        affected_regions=["us-east-1"],
    )


@pytest.fixture
def technical_event(db):
    from nazara.signals.infrastructure.django.app.models import TechnicalEventModel

    return TechnicalEventModel.objects.create(
        event_type="error",
        title="Database Connection Error",
        description="Connection pool exhausted during peak traffic",
        source_system="sentry",
        source_identifier="SENTRY-456",
        source_url="https://sentry.io/issues/456",
        service="api-gateway",
        environment="production",
        host="api-prod-01",
        started_at=timezone.now(),
        severity="high",
        error_type="DatabaseError",
        error_message="Connection pool exhausted",
        error_fingerprint="db-pool-exhausted-001",
    )


@pytest.fixture
def technical_issue(db):
    from nazara.signals.infrastructure.django.app.models import TechnicalIssueModel

    return TechnicalIssueModel.objects.create(
        provider="sentry",
        issue_key="sentry:123:456",
        environment="production",
        service="api-gateway",
        status="active",
        first_seen_at=timezone.now(),
        last_seen_at=timezone.now(),
        occurrences_total=1,
        title="Database Connection Error",
        last_message="Connection pool exhausted",
        source_url="https://sentry.io/issues/456",
    )


@pytest.fixture
def linked_incident_with_events(db, incident, technical_event, customer_case):
    technical_event.related_incident = incident
    technical_event.save()

    customer_case.related_incident = incident
    customer_case.save()

    return incident


@pytest.fixture(autouse=True)
def media_storage(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
