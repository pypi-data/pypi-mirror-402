from dependency_injector import containers, providers

from nazara.ingestion.application.ingestion import RunIngestion, get_default_readers
from nazara.ingestion.infrastructure.persistence.repositories.ingestor_config_repository import (
    DjangoIngestorConfigRepository,
)


class IngestionContainer(containers.DeclarativeContainer):
    """
    Container for ingestion bounded context dependencies.

    Provides:
        - IngestorConfig repository
        - RunIngestion for executing ingestion operations
        - Default readers registry for supported ingestor types

    Dependencies:
        - shared: SharedContainer providing secret_resolver
        - signals: SignalsContainer providing signal creation services
    """

    shared = providers.DependenciesContainer()
    signals = providers.DependenciesContainer()

    config = providers.Configuration()

    config_repository = providers.Singleton(DjangoIngestorConfigRepository)

    readers = providers.Factory(get_default_readers)

    run_ingestion = providers.Factory(
        RunIngestion,
        config_repo=config_repository,
        secret_resolver=shared.secret_resolver,
        readers=readers,
        create_technical_event=signals.create_technical_event,
        create_incident=signals.create_incident,
        create_customer_case=signals.create_customer_case,
    )
