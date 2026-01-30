from dependency_injector import containers, providers

from nazara.signals.application.customer_case import CreateCustomerCase
from nazara.signals.application.incident import CreateIncident
from nazara.signals.application.technical_event import CreateTechnicalEvent
from nazara.signals.infrastructure.persistence.repositories.customer_case_repository import (
    DjangoCustomerCaseRepository,
)
from nazara.signals.infrastructure.persistence.repositories.incident_repository import (
    DjangoIncidentRepository,
)
from nazara.signals.infrastructure.persistence.repositories.technical_issue_repository import (
    DjangoTechnicalIssueRepository,
)


class SignalsContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    shared = providers.DependenciesContainer()

    # Repositories
    issue_repository = providers.Singleton(DjangoTechnicalIssueRepository)
    incident_repository = providers.Singleton(DjangoIncidentRepository)
    customer_case_repository = providers.Singleton(DjangoCustomerCaseRepository)

    # Application Services
    create_technical_event = providers.Factory(
        CreateTechnicalEvent,
        issue_repo=issue_repository,
        event_bus=shared.event_bus,
    )

    create_incident = providers.Factory(
        CreateIncident,
        incident_repo=incident_repository,
        event_bus=shared.event_bus,
    )

    create_customer_case = providers.Factory(
        CreateCustomerCase,
        case_repo=customer_case_repository,
        event_bus=shared.event_bus,
    )
