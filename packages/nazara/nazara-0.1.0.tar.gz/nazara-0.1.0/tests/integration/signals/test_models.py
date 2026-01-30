import pytest
from django.db import IntegrityError

from nazara.signals.infrastructure.django.app.models import TechnicalIssueModel


@pytest.mark.django_db
def test_technical_issue_should_enforce_unique_constraint(technical_issue):
    with pytest.raises(IntegrityError):
        TechnicalIssueModel.objects.create(
            provider="sentry",
            issue_key="sentry:123:456",
            environment="production",
            service="api-gateway",
            status="active",
        )


@pytest.mark.django_db
def test_incident_should_link_to_events_and_cases(linked_incident_with_events):
    incident = linked_incident_with_events
    assert incident.technical_events.count() == 1
    assert incident.customer_cases.count() == 1


@pytest.mark.django_db
def test_technical_event_should_link_to_issue(technical_event, technical_issue):
    technical_event.issue = technical_issue
    technical_event.save()

    technical_issue.refresh_from_db()
    assert technical_issue.events.count() == 1
    assert technical_event.issue_id == technical_issue.id
