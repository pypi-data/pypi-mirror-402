from dependency_injector import containers, providers

from nazara.intelligence.application.enrichers.embedding import GenerateEmbedding
from nazara.intelligence.application.enrichers.summary import GenerateSummary
from nazara.intelligence.application.enrichment import (
    EnrichCustomerCase,
    EnrichIncident,
    EnrichTechnicalIssue,
)
from nazara.intelligence.domain.contracts.llm import LLMConnector
from nazara.intelligence.infrastructure.llm.anthropic_connector import (
    AnthropicConnector,
)
from nazara.intelligence.infrastructure.llm.openai_connector import (
    OpenAIConnector,
)
from nazara.intelligence.infrastructure.persistence.repositories.enrichment_record_repository import (
    DjangoEnrichmentRecordRepository,
)
from nazara.shared.domain.contracts.secrets import SecretResolver


class NoLLMConfigError(Exception):
    pass


def _resolve_connector(secret_resolver: SecretResolver, capability: str) -> LLMConnector | None:
    from nazara.intelligence.domain.models import LLMProviderConfig

    config = (
        LLMProviderConfig.objects.filter(
            enabled=True,
            capabilities__contains=[capability],
        )
        .order_by("priority")
        .first()
    )

    if config is None:
        return None

    api_key = secret_resolver.resolve(config.secret_ref)

    if config.provider == "openai":
        return OpenAIConnector(
            api_key=api_key,
            model=config.model,
            max_tokens=config.max_tokens,
            base_url=config.base_url or None,
            timeout=float(config.timeout_seconds),
        )
    elif config.provider == "anthropic":
        return AnthropicConnector(
            api_key=api_key,
            model=config.model,
            max_tokens=config.max_tokens,
            base_url=config.base_url or None,
            timeout=float(config.timeout_seconds),
        )
    else:
        raise NoLLMConfigError(f"Unknown provider: {config.provider}")


class IntelligenceContainer(containers.DeclarativeContainer):
    shared = providers.DependenciesContainer()

    summary_connector = providers.Callable(
        _resolve_connector,
        secret_resolver=shared.secret_resolver,
        capability="summary",
    )

    embedding_connector = providers.Callable(
        _resolve_connector,
        secret_resolver=shared.secret_resolver,
        capability="embedding",
    )

    # Steps as Factory providers
    summary_step = providers.Factory(
        GenerateSummary,
        connector=summary_connector,
    )

    embedding_step = providers.Factory(
        GenerateEmbedding,
        connector=embedding_connector,
    )

    # Shared steps dict (reused by all 3 services)
    _steps = providers.Dict(
        {
            "summary": summary_step,
            "embedding": embedding_step,
        }
    )

    # Repositories
    enrichment_record_repository = providers.Singleton(DjangoEnrichmentRecordRepository)

    # THREE signal-specific services
    enrich_incident = providers.Factory(
        EnrichIncident,
        steps=_steps,
        enrichment_repository=enrichment_record_repository,
    )

    enrich_customer_case = providers.Factory(
        EnrichCustomerCase,
        steps=_steps,
        enrichment_repository=enrichment_record_repository,
    )

    enrich_technical_issue = providers.Factory(
        EnrichTechnicalIssue,
        steps=_steps,
        enrichment_repository=enrichment_record_repository,
    )
