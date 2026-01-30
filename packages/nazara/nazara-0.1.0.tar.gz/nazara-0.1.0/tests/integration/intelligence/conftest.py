from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from nazara.intelligence.application.enrichers.embedding import GenerateEmbedding
from nazara.intelligence.application.enrichers.summary import GenerateSummary
from nazara.intelligence.domain.contracts.llm import ChatResponse, EmbedResponse
from nazara.intelligence.domain.models import (
    EnrichmentRecord,
    EnrichmentStatusChoices,
    EnrichmentTypeChoices,
    LLMProviderConfig,
    TargetTypeChoices,
)
from nazara.intelligence.infrastructure.persistence.repositories.enrichment_record_repository import (
    DjangoEnrichmentRecordRepository,
)


@pytest.fixture
def enrichment_incident(db):
    from nazara.signals.domain.models import Incident

    return Incident.objects.create(
        title="Test Incident",
        description="Test incident description",
        source_system="test",
        source_identifier=str(uuid4()),
    )


@pytest.fixture
def openai_config(db):
    return LLMProviderConfig.objects.create(
        model="gpt-4o-mini",
        secret_ref="OPENAI_API_KEY",
        capabilities=["summary", "embedding"],
        enabled=True,
    )


@pytest.fixture
def mock_connector():
    connector = MagicMock()
    connector.chat.return_value = ChatResponse(
        content="Generated summary",
        input_tokens=100,
        output_tokens=50,
    )
    connector.embed.return_value = EmbedResponse(
        vector=[0.1] * 1536,
        input_tokens=25,
    )
    connector.get_embedding_dimension.return_value = 1536
    connector.provider_name = "openai"
    connector.model_name = "gpt-4o-mini"
    return connector


@pytest.fixture
def mock_generate_summary(mock_connector):
    return GenerateSummary(connector=mock_connector)


@pytest.fixture
def mock_generate_embedding(mock_connector):
    return GenerateEmbedding(connector=mock_connector)


@pytest.fixture
def enrichment_repository():
    return DjangoEnrichmentRecordRepository()


@pytest.fixture
def mock_steps(mock_generate_summary, mock_generate_embedding):
    return {"summary": mock_generate_summary, "embedding": mock_generate_embedding}


@pytest.fixture
def incident_flow(db, active_profile):
    from nazara.intelligence.domain.models import (
        EnrichmentFlow,
        EnrichmentFlowStep,
    )

    flow = EnrichmentFlow.objects.create(
        profile=active_profile,
        target_type=TargetTypeChoices.INCIDENT,
        name="Default",
        priority=0,
        enabled=True,
    )
    EnrichmentFlowStep.objects.create(
        flow=flow,
        enrichment_type=EnrichmentTypeChoices.SUMMARY_V1,
        order=1,
    )
    EnrichmentFlowStep.objects.create(
        flow=flow,
        enrichment_type=EnrichmentTypeChoices.EMBEDDING_V1,
        order=2,
    )
    return flow


@pytest.fixture
def existing_enrichment_record(db, enrichment_incident):
    input_hash = EnrichmentRecord.compute_input_hash(
        enrichment_incident.title, enrichment_incident.description
    )
    record = EnrichmentRecord.objects.create(
        target_type="Incident",
        target_id=enrichment_incident.id,
        enrichment_type="summary.v1",
        input_hash=input_hash,
        status=EnrichmentStatusChoices.SUCCESS,
        result={"text": "Previous summary"},
    )
    return record
