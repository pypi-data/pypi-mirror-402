from unittest.mock import MagicMock
from uuid import uuid4

from nazara.intelligence.application.enrichers.embedding import GenerateEmbedding
from nazara.intelligence.application.enrichers.summary import GenerateSummary
from nazara.intelligence.application.enrichment import EnrichIncident
from nazara.intelligence.domain.contracts.llm import ChatResponse
from nazara.intelligence.domain.models import (
    DomainProfile,
    EnrichmentRecord,
    EnrichmentStatusChoices,
)


def test_enrich_should_return_failed_when_signal_not_found(
    db, active_profile, incident_flow, mock_steps, enrichment_repository
):
    service = EnrichIncident(
        steps=mock_steps,
        enrichment_repository=enrichment_repository,
    )
    result = service.enrich(incident_id=uuid4())

    assert result["status"] == "failed"
    assert "not found" in result["error"].lower()


def test_enrich_should_skip_when_no_matching_flow(
    db, active_profile, enrichment_incident, mock_steps, enrichment_repository
):
    service = EnrichIncident(
        steps=mock_steps,
        enrichment_repository=enrichment_repository,
    )
    result = service.enrich(incident_id=enrichment_incident.id)

    assert result["status"] == "skipped"
    assert result["reason"] == "no_active_flow"


def test_enrich_should_skip_when_no_active_profile(
    db, enrichment_incident, mock_steps, enrichment_repository
):
    DomainProfile.objects.all().delete()

    service = EnrichIncident(
        steps=mock_steps,
        enrichment_repository=enrichment_repository,
    )
    result = service.enrich(incident_id=enrichment_incident.id)

    assert result["status"] == "skipped"
    assert result["reason"] == "no_active_flow"


def test_enrich_should_skip_when_connector_not_configured(
    db, active_profile, incident_flow, enrichment_incident, enrichment_repository
):
    steps = {
        "summary": GenerateSummary(connector=None),
        "embedding": GenerateEmbedding(connector=None),
    }

    service = EnrichIncident(
        steps=steps,
        enrichment_repository=enrichment_repository,
    )
    result = service.enrich(incident_id=enrichment_incident.id)

    assert result["enrichments"]["summary.v1"]["skipped"] == "step unavailable"


def test_enrich_should_execute_summary_step(
    db,
    active_profile,
    incident_flow,
    enrichment_incident,
    mock_steps,
    mock_connector,
    enrichment_repository,
):
    service = EnrichIncident(
        steps=mock_steps,
        enrichment_repository=enrichment_repository,
    )
    result = service.enrich(incident_id=enrichment_incident.id)

    assert result["status"] == "success"
    assert result["enrichments"]["summary.v1"]["status"] == "success"
    mock_connector.chat.assert_called_once()

    record = EnrichmentRecord.objects.get(
        target_id=enrichment_incident.id,
        enrichment_type="summary.v1",
    )
    assert record.status == EnrichmentStatusChoices.SUCCESS
    assert record.result == {"text": "Generated summary"}


def test_enrich_should_skip_when_already_enriched(
    db,
    active_profile,
    incident_flow,
    enrichment_incident,
    mock_steps,
    mock_connector,
    enrichment_repository,
):
    input_hash = mock_steps["summary"].compute_input_hash(
        enrichment_incident,
        {"enrichment_type": "summary.v1", "dependent_outputs": {}},
    )
    EnrichmentRecord.objects.create(
        target_type="Incident",
        target_id=enrichment_incident.id,
        enrichment_type="summary.v1",
        input_hash=input_hash,
        status=EnrichmentStatusChoices.SUCCESS,
        result={"text": "Existing summary"},
    )

    service = EnrichIncident(
        steps=mock_steps,
        enrichment_repository=enrichment_repository,
    )
    result = service.enrich(incident_id=enrichment_incident.id)

    assert result["enrichments"]["summary.v1"]["skipped"] == "already processed with same input"
    mock_connector.chat.assert_not_called()


def test_enrich_should_re_enrich_when_force_is_true(
    db,
    active_profile,
    incident_flow,
    enrichment_incident,
    mock_steps,
    mock_connector,
    enrichment_repository,
):
    input_hash = mock_steps["summary"].compute_input_hash(
        enrichment_incident,
        {"enrichment_type": "summary.v1", "dependent_outputs": {}},
    )
    EnrichmentRecord.objects.create(
        target_type="Incident",
        target_id=enrichment_incident.id,
        enrichment_type="summary.v1",
        input_hash=input_hash,
        status=EnrichmentStatusChoices.SUCCESS,
        result={"text": "Old summary"},
    )

    service = EnrichIncident(
        steps=mock_steps,
        enrichment_repository=enrichment_repository,
    )
    result = service.enrich(incident_id=enrichment_incident.id, force=True)

    assert result["enrichments"]["summary.v1"]["status"] == "success"
    mock_connector.chat.assert_called_once()


def test_enrich_should_record_failure_on_exception(
    db,
    active_profile,
    incident_flow,
    enrichment_incident,
    enrichment_repository,
):
    mock_connector = MagicMock()
    mock_connector.chat.side_effect = Exception("API error")
    mock_connector.embed.side_effect = Exception("Embed API error")
    mock_connector.provider_name = "openai"
    mock_connector.model_name = "gpt-4o-mini"

    steps = {
        "summary": GenerateSummary(connector=mock_connector),
        "embedding": GenerateEmbedding(connector=mock_connector),
    }

    service = EnrichIncident(
        steps=steps,
        enrichment_repository=enrichment_repository,
    )
    result = service.enrich(incident_id=enrichment_incident.id)

    assert result["enrichments"]["summary.v1"]["status"] == "failed"
    assert "API error" in result["enrichments"]["summary.v1"]["error"]

    record = EnrichmentRecord.objects.get(
        target_id=enrichment_incident.id,
        enrichment_type="summary.v1",
    )
    assert record.status == EnrichmentStatusChoices.FAILED
    assert "API error" in record.error


def test_enrich_should_store_result_in_enrichment_record(
    db,
    active_profile,
    incident_flow,
    enrichment_incident,
    mock_steps,
    enrichment_repository,
):
    service = EnrichIncident(
        steps=mock_steps,
        enrichment_repository=enrichment_repository,
    )
    service.enrich(incident_id=enrichment_incident.id)

    record = EnrichmentRecord.objects.get(
        target_id=enrichment_incident.id,
        enrichment_type="summary.v1",
    )
    assert record.result == {"text": "Generated summary"}


def test_enrich_should_execute_both_summary_and_embedding(
    db,
    active_profile,
    incident_flow,
    enrichment_incident,
    mock_steps,
    enrichment_repository,
):
    service = EnrichIncident(
        steps=mock_steps,
        enrichment_repository=enrichment_repository,
    )
    result = service.enrich(incident_id=enrichment_incident.id)

    assert result["status"] == "success"
    assert result["enrichments"]["summary.v1"]["status"] == "success"
    assert result["enrichments"]["embedding.v1"]["status"] == "success"

    summary_record = EnrichmentRecord.objects.get(
        target_id=enrichment_incident.id,
        enrichment_type="summary.v1",
    )
    assert summary_record.result == {"text": "Generated summary"}

    embedding_record = EnrichmentRecord.objects.get(
        target_id=enrichment_incident.id,
        enrichment_type="embedding.v1",
    )
    assert len(embedding_record.embedding) == 1536


def test_enrich_should_pass_summary_to_embedding_step(
    db,
    active_profile,
    incident_flow,
    enrichment_incident,
    mock_connector,
    enrichment_repository,
):
    """Test that embedding receives summary output via dependent_outputs context."""
    from nazara.intelligence.domain.models import EnrichmentFlowStep, InputSourceChoices

    # Update embedding step to use dependent input source
    embedding_step = EnrichmentFlowStep.objects.get(
        flow=incident_flow, enrichment_type="embedding.v1"
    )
    embedding_step.input_source = InputSourceChoices.DEPENDENT
    embedding_step.save()

    steps = {
        "summary": GenerateSummary(connector=mock_connector),
        "embedding": GenerateEmbedding(connector=mock_connector),
    }

    service = EnrichIncident(
        steps=steps,
        enrichment_repository=enrichment_repository,
    )
    service.enrich(incident_id=enrichment_incident.id)

    mock_connector.embed.assert_called_once()
    call_args = mock_connector.embed.call_args

    assert "Generated summary" in call_args[0][0]


def test_enrich_should_execute_steps_in_flow_order(
    db,
    active_profile,
    incident_flow,
    enrichment_incident,
    mock_connector,
    enrichment_repository,
):
    """Test that steps execute in order defined by flow."""
    call_order = []

    def track_chat(*args, **kwargs):
        call_order.append("chat")
        return ChatResponse(content="Generated summary", input_tokens=100, output_tokens=50)

    def track_embed(*args, **kwargs):
        call_order.append("embed")
        from nazara.intelligence.domain.contracts.llm import EmbedResponse

        return EmbedResponse(vector=[0.1] * 1536, input_tokens=25)

    mock_connector.chat.side_effect = track_chat
    mock_connector.embed.side_effect = track_embed

    steps = {
        "summary": GenerateSummary(connector=mock_connector),
        "embedding": GenerateEmbedding(connector=mock_connector),
    }

    service = EnrichIncident(
        steps=steps,
        enrichment_repository=enrichment_repository,
    )
    service.enrich(incident_id=enrichment_incident.id)

    assert call_order == ["chat", "embed"]


def test_enrich_should_use_narrowed_context_in_system_prompt(
    db,
    active_profile,
    incident_flow,
    mock_connector,
    enrichment_repository,
):
    from nazara.intelligence.domain.models import SystemCatalogEntry
    from nazara.signals.domain.models import Incident

    SystemCatalogEntry.objects.create(
        profile=active_profile,
        key="proxy-service",
        label="Proxy Service",
        entry_type="service",
        description="Handles proxy allocation and rotation",
    )

    incident = Incident.objects.create(
        title="Proxy Service Outage",
        description="The proxy-service is returning 500 errors",
        source_system="alertmanager",
        source_identifier="alert-12345",
    )

    steps = {
        "summary": GenerateSummary(connector=mock_connector),
        "embedding": GenerateEmbedding(connector=mock_connector),
    }

    service = EnrichIncident(
        steps=steps,
        enrichment_repository=enrichment_repository,
    )
    service.enrich(incident_id=incident.id)

    mock_connector.chat.assert_called_once()
    call_args = mock_connector.chat.call_args
    system_prompt = call_args[0][0]

    assert "## Relevant Systems" in system_prompt
    assert "Proxy Service" in system_prompt
