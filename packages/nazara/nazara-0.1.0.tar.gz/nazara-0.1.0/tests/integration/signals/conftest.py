import pytest

from nazara.signals.application.customer_case import CreateCustomerCase
from nazara.signals.application.incident import CreateIncident
from nazara.signals.infrastructure.persistence.repositories.customer_case_repository import (
    DjangoCustomerCaseRepository,
)
from nazara.signals.infrastructure.persistence.repositories.incident_repository import (
    DjangoIncidentRepository,
)


@pytest.fixture
def customer_case_repo():
    return DjangoCustomerCaseRepository()


@pytest.fixture
def incident_repo():
    return DjangoIncidentRepository()


@pytest.fixture
def create_customer_case(spy_event_bus, customer_case_repo):
    return CreateCustomerCase(
        case_repo=customer_case_repo,
        event_bus=spy_event_bus,
    )


@pytest.fixture
def create_incident(spy_event_bus, incident_repo):
    return CreateIncident(
        incident_repo=incident_repo,
        event_bus=spy_event_bus,
    )
