from uuid import uuid4

import pytest
from django.db import IntegrityError

from nazara.intelligence.domain.models import (
    DomainCategory,
    DomainProfile,
    EnrichmentRecord,
    EnrichmentStatusChoices,
    LLMProviderConfig,
    SeverityLevel,
)


@pytest.mark.django_db
def test_profile_should_be_created_with_required_fields():
    profile = DomainProfile.objects.create(name="Test")

    assert profile.id is not None
    assert profile.name == "Test"
    assert profile.is_active is False


@pytest.mark.django_db
def test_profile_should_enforce_unique_name(domain_profile):
    with pytest.raises(IntegrityError):
        DomainProfile.objects.create(name="Test Profile")


@pytest.mark.django_db
def test_profile_should_allow_only_one_active(active_profile):
    profile2 = DomainProfile.objects.create(name="Another", is_active=False)
    profile2.activate()
    profile2.save()

    active_profile.refresh_from_db()
    assert active_profile.is_active is False
    assert profile2.is_active is True


@pytest.mark.django_db
def test_profile_should_deactivate(active_profile):
    active_profile.deactivate()
    active_profile.save()
    active_profile.refresh_from_db()

    assert active_profile.is_active is False


@pytest.mark.django_db
def test_profile_should_get_category_keys(domain_profile):
    DomainCategory.objects.create(profile=domain_profile, key="payments", label="Payments")
    DomainCategory.objects.create(profile=domain_profile, key="network", label="Network")

    keys = domain_profile.get_category_keys()

    assert "payments" in keys
    assert "network" in keys
    assert len(keys) == 2


@pytest.mark.django_db
def test_profile_should_validate_category_key(domain_profile):
    DomainCategory.objects.create(profile=domain_profile, key="payments", label="Payments")

    assert domain_profile.is_valid_category("payments") is True
    assert domain_profile.is_valid_category("invalid") is False


@pytest.mark.django_db
def test_profile_should_validate_severity_key(domain_profile):
    SeverityLevel.objects.create(profile=domain_profile, key="high", label="High", rank=3)

    assert domain_profile.is_valid_severity("high") is True
    assert domain_profile.is_valid_severity("invalid") is False


@pytest.mark.django_db
def test_category_should_be_created(domain_profile):
    category = DomainCategory.objects.create(
        profile=domain_profile,
        key="payments",
        label="Payments",
        description="Payment related issues",
    )

    assert category.key == "payments"
    assert category.label == "Payments"
    assert str(category) == "Payments"


@pytest.mark.django_db
def test_category_should_enforce_unique_key_per_profile(domain_profile):
    DomainCategory.objects.create(profile=domain_profile, key="payments", label="Payments")

    with pytest.raises(IntegrityError):
        DomainCategory.objects.create(profile=domain_profile, key="payments", label="Payments 2")


@pytest.mark.django_db
def test_category_should_allow_same_key_in_different_profiles(domain_profile):
    profile2 = DomainProfile.objects.create(name="Profile 2")

    cat1 = DomainCategory.objects.create(profile=domain_profile, key="payments", label="Payments")
    cat2 = DomainCategory.objects.create(profile=profile2, key="payments", label="Payments")

    assert cat1.key == cat2.key
    assert cat1.profile != cat2.profile


@pytest.mark.django_db
def test_severity_should_be_created(domain_profile):
    severity = SeverityLevel.objects.create(
        profile=domain_profile,
        key="critical",
        label="Critical",
        rank=4,
        description="Critical severity",
    )

    assert severity.key == "critical"
    assert severity.rank == 4
    assert str(severity) == "Critical (4)"


@pytest.mark.django_db
def test_severity_should_enforce_unique_rank_per_profile(domain_profile):
    SeverityLevel.objects.create(profile=domain_profile, key="high", label="High", rank=3)

    with pytest.raises(IntegrityError):
        SeverityLevel.objects.create(
            profile=domain_profile, key="critical", label="Critical", rank=3
        )


@pytest.mark.django_db
def test_llm_config_should_be_created():
    config = LLMProviderConfig.objects.create(
        model="gpt-4o-mini",
        secret_ref="OPENAI_API_KEY",
        capabilities=["summary", "embedding"],
        enabled=True,
    )

    assert config.provider == "openai"
    assert config.model == "gpt-4o-mini"
    assert config.enabled is True


@pytest.mark.django_db
def test_llm_config_should_derive_provider_from_model():
    openai_config = LLMProviderConfig.objects.create(
        model="gpt-4o-mini",
        secret_ref="OPENAI_API_KEY",
        capabilities=["summary"],
    )
    anthropic_config = LLMProviderConfig.objects.create(
        model="claude-3-5-haiku-20241022",
        secret_ref="ANTHROPIC_API_KEY",
        capabilities=["summary"],
    )

    assert openai_config.provider == "openai"
    assert anthropic_config.provider == "anthropic"


@pytest.mark.django_db
def test_llm_config_should_check_capability():
    config = LLMProviderConfig.objects.create(
        model="gpt-4o-mini",
        secret_ref="OPENAI_API_KEY",
        capabilities=["summary"],
    )

    assert config.has_capability("summary") is True
    assert config.has_capability("embedding") is False


@pytest.mark.django_db
def test_llm_config_should_check_summary_capability():
    config = LLMProviderConfig.objects.create(
        model="gpt-4o-mini",
        secret_ref="OPENAI_API_KEY",
        capabilities=["summary"],
        enabled=True,
    )

    assert config.can_generate_summary() is True
    assert config.can_generate_embedding() is False


@pytest.mark.django_db
def test_llm_config_should_return_false_when_disabled():
    config = LLMProviderConfig.objects.create(
        model="gpt-4o-mini",
        secret_ref="OPENAI_API_KEY",
        capabilities=["summary", "embedding"],
        enabled=False,
    )

    assert config.can_generate_summary() is False
    assert config.can_generate_embedding() is False


@pytest.mark.django_db
def test_llm_config_should_derive_display_name_from_provider_model():
    config = LLMProviderConfig.objects.create(
        model="gpt-4o-mini",
        secret_ref="OPENAI_API_KEY",
        capabilities=["summary"],
    )

    assert config.display_name == "openai/gpt-4o-mini"


@pytest.mark.django_db
def test_llm_config_should_use_custom_name_when_set():
    config = LLMProviderConfig.objects.create(
        name="Production Summarizer",
        model="claude-3-5-haiku-20241022",
        secret_ref="ANTHROPIC_API_KEY",
        capabilities=["summary"],
    )

    assert config.display_name == "Production Summarizer"


def test_enrichment_record_should_compute_input_hash():
    hash1 = EnrichmentRecord.compute_input_hash("Title", "Description")
    hash2 = EnrichmentRecord.compute_input_hash("Title", "Description")
    hash3 = EnrichmentRecord.compute_input_hash("Different", "Content")

    assert hash1 == hash2
    assert hash1 != hash3
    assert len(hash1) == 64


@pytest.mark.django_db
def test_enrichment_record_should_store_result():
    target_id = uuid4()
    record = EnrichmentRecord.objects.create(
        target_type="Incident",
        target_id=target_id,
        enrichment_type="summary.v1",
        input_hash="abc123",
        status=EnrichmentStatusChoices.SUCCESS,
        duration_ms=1500,
        result={"text": "Generated summary", "categories": ["network", "outage"]},
    )

    assert record.status == EnrichmentStatusChoices.SUCCESS
    assert record.duration_ms == 1500
    assert record.result["text"] == "Generated summary"
    assert "network" in record.result["categories"]


@pytest.mark.django_db
def test_enrichment_record_should_track_attempts():
    target_id = uuid4()
    record = EnrichmentRecord.objects.create(
        target_type="Incident",
        target_id=target_id,
        enrichment_type="summary.v1",
        input_hash="abc123",
        status=EnrichmentStatusChoices.FAILED,
        attempts=3,
        error="API rate limit exceeded",
    )

    assert record.status == EnrichmentStatusChoices.FAILED
    assert record.attempts == 3
    assert "rate limit" in record.error


@pytest.mark.django_db
def test_enrichment_record_should_enforce_unique_constraint():
    from django.db import IntegrityError

    target_id = uuid4()

    EnrichmentRecord.objects.create(
        target_type="Incident",
        target_id=target_id,
        enrichment_type="summary.v1",
        input_hash="hash1",
        status=EnrichmentStatusChoices.SUCCESS,
    )

    with pytest.raises(IntegrityError):
        EnrichmentRecord.objects.create(
            target_type="Incident",
            target_id=target_id,
            enrichment_type="summary.v1",
            input_hash="hash2",
            status=EnrichmentStatusChoices.SUCCESS,
        )


@pytest.mark.django_db
def test_enrichment_record_should_allow_multiple_enrichment_types():
    target_id = uuid4()

    summary_record = EnrichmentRecord.objects.create(
        target_type="Incident",
        target_id=target_id,
        enrichment_type="summary.v1",
        input_hash="hash123",
        status=EnrichmentStatusChoices.SUCCESS,
        result={"text": "Summary"},
    )

    embedding_record = EnrichmentRecord.objects.create(
        target_type="Incident",
        target_id=target_id,
        enrichment_type="embedding.v1",
        input_hash="hash123",
        status=EnrichmentStatusChoices.SUCCESS,
        embedding=[0.1] * 1536,
    )

    assert summary_record.id != embedding_record.id
    assert EnrichmentRecord.objects.filter(target_id=target_id).count() == 2
