import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from nazara.intelligence.domain.models import (
    EnrichmentFlow,
    EnrichmentFlowStep,
    EnrichmentTypeChoices,
    InputSourceChoices,
    TargetTypeChoices,
)
from nazara.intelligence.domain.step_registry import clear_registry, register_step


@pytest.fixture(autouse=True)
def setup_step_registry():
    from typing import Any, ClassVar

    from nazara.intelligence.domain.contracts.step import EnrichmentStep, StepResult

    @register_step("summary")
    class MockSummaryStep(EnrichmentStep):
        requires: ClassVar[list[str]] = []

        @property
        def key(self) -> str:
            return "summary"

        @property
        def produces(self) -> str:
            return "result"

        @property
        def uses_llm(self) -> bool:
            return True

        def is_available(self) -> bool:
            return True

        def compute_input_hash(self, signal: Any, context: dict[str, Any]) -> str:
            return "hash"

        def should_run(
            self, signal: Any, record: Any, context: dict[str, Any], force: bool = False
        ) -> tuple[bool, str]:
            return True, "test"

        def execute(self, signal: Any, profile: Any, context: dict[str, Any]) -> StepResult:
            return StepResult(success=True, output={"text": "test"})

    @register_step("embedding")
    class MockEmbeddingStep(EnrichmentStep):
        requires: ClassVar[list[str]] = []

        @property
        def key(self) -> str:
            return "embedding"

        @property
        def produces(self) -> str:
            return "embedding"

        @property
        def uses_llm(self) -> bool:
            return True

        def is_available(self) -> bool:
            return True

        def compute_input_hash(self, signal: Any, context: dict[str, Any]) -> str:
            return "hash"

        def should_run(
            self, signal: Any, record: Any, context: dict[str, Any], force: bool = False
        ) -> tuple[bool, str]:
            return True, "test"

        def execute(self, signal: Any, profile: Any, context: dict[str, Any]) -> StepResult:
            return StepResult(success=True, embedding=[0.1] * 1536)

    yield
    clear_registry()


@pytest.mark.django_db
def test_flow_should_be_created_with_required_fields(domain_profile):
    flow = EnrichmentFlow.objects.create(
        profile=domain_profile,
        target_type=TargetTypeChoices.INCIDENT,
        name="Default",
    )

    assert flow.id is not None
    assert flow.profile == domain_profile
    assert flow.target_type == "Incident"
    assert flow.name == "Default"
    assert flow.enabled is True
    assert flow.priority == 0


@pytest.mark.django_db
def test_flow_should_display_str_with_target_type_and_name(domain_profile):
    flow = EnrichmentFlow.objects.create(
        profile=domain_profile,
        target_type=TargetTypeChoices.INCIDENT,
        name="Default",
        enabled=False,
    )

    assert str(flow) == "Incident → Default"


@pytest.mark.django_db
def test_flow_should_display_str_ignoring_filters(domain_profile):
    flow = EnrichmentFlow.objects.create(
        profile=domain_profile,
        target_type=TargetTypeChoices.INCIDENT,
        name="Filtered",
        enabled=True,
        category_filter=["infrastructure"],
    )

    assert str(flow) == "Incident → Filtered"


@pytest.mark.django_db
def test_flow_should_enforce_unique_name_per_profile_target(domain_profile):
    EnrichmentFlow.objects.create(
        profile=domain_profile,
        target_type=TargetTypeChoices.INCIDENT,
        name="Default",
    )

    with pytest.raises(ValidationError):
        EnrichmentFlow.objects.create(
            profile=domain_profile,
            target_type=TargetTypeChoices.INCIDENT,
            name="Default",
        )


@pytest.mark.django_db
def test_flow_should_allow_same_name_different_target(domain_profile):
    flow1 = EnrichmentFlow.objects.create(
        profile=domain_profile,
        target_type=TargetTypeChoices.INCIDENT,
        name="Default",
    )
    flow2 = EnrichmentFlow.objects.create(
        profile=domain_profile,
        target_type=TargetTypeChoices.CUSTOMER_CASE,
        name="Default",
    )

    assert flow1.name == flow2.name
    assert flow1.target_type != flow2.target_type


@pytest.mark.django_db
def test_flow_should_enforce_unique_priority_per_profile_target(domain_profile):
    EnrichmentFlow.objects.create(
        profile=domain_profile,
        target_type=TargetTypeChoices.INCIDENT,
        name="Flow 1",
        priority=10,
    )

    with pytest.raises(ValidationError) as exc_info:
        EnrichmentFlow.objects.create(
            profile=domain_profile,
            target_type=TargetTypeChoices.INCIDENT,
            name="Flow 2",
            priority=10,
        )

    assert "priority" in str(exc_info.value)


@pytest.mark.django_db
def test_flow_should_allow_different_priorities_same_target(domain_profile):
    flow1 = EnrichmentFlow.objects.create(
        profile=domain_profile,
        target_type=TargetTypeChoices.INCIDENT,
        name="Flow 1",
        priority=10,
    )
    flow2 = EnrichmentFlow.objects.create(
        profile=domain_profile,
        target_type=TargetTypeChoices.INCIDENT,
        name="Flow 2",
        priority=5,
    )

    assert flow1.priority == 10
    assert flow2.priority == 5


@pytest.mark.django_db
def test_flow_should_allow_same_priority_different_targets(domain_profile):
    flow1 = EnrichmentFlow.objects.create(
        profile=domain_profile,
        target_type=TargetTypeChoices.INCIDENT,
        name="Default",
        priority=10,
    )
    flow2 = EnrichmentFlow.objects.create(
        profile=domain_profile,
        target_type=TargetTypeChoices.CUSTOMER_CASE,
        name="Default",
        priority=10,
    )

    assert flow1.priority == flow2.priority
    assert flow1.target_type != flow2.target_type


@pytest.mark.django_db
def test_flow_should_return_ordered_steps(domain_profile):
    flow = EnrichmentFlow.objects.create(
        profile=domain_profile,
        target_type=TargetTypeChoices.INCIDENT,
        name="Default",
    )
    EnrichmentFlowStep.objects.create(
        flow=flow,
        enrichment_type=EnrichmentTypeChoices.EMBEDDING_V1,
        order=2,
    )
    EnrichmentFlowStep.objects.create(
        flow=flow,
        enrichment_type=EnrichmentTypeChoices.SUMMARY_V1,
        order=1,
    )

    ordered_steps = flow.get_ordered_steps()

    assert ordered_steps == ["summary.v1", "embedding.v1"]


@pytest.mark.django_db
def test_flow_step_should_be_created_with_required_fields(domain_profile):
    flow = EnrichmentFlow.objects.create(
        profile=domain_profile,
        target_type=TargetTypeChoices.INCIDENT,
        name="Default",
    )
    step = EnrichmentFlowStep.objects.create(
        flow=flow,
        enrichment_type=EnrichmentTypeChoices.SUMMARY_V1,
        order=1,
    )

    assert step.id is not None
    assert step.flow == flow
    assert step.enrichment_type == "summary.v1"
    assert step.order == 1


@pytest.mark.django_db
def test_flow_step_should_display_str_representation(domain_profile):
    flow = EnrichmentFlow.objects.create(
        profile=domain_profile,
        target_type=TargetTypeChoices.INCIDENT,
        name="Default",
    )
    step = EnrichmentFlowStep.objects.create(
        flow=flow,
        enrichment_type=EnrichmentTypeChoices.SUMMARY_V1,
        order=1,
    )

    assert "1" in str(step)
    assert "summary.v1" in str(step)


@pytest.mark.django_db
def test_flow_step_should_enforce_unique_type_per_flow(domain_profile):
    flow = EnrichmentFlow.objects.create(
        profile=domain_profile,
        target_type=TargetTypeChoices.INCIDENT,
        name="Default",
    )
    EnrichmentFlowStep.objects.create(
        flow=flow,
        enrichment_type=EnrichmentTypeChoices.SUMMARY_V1,
        order=1,
    )

    with pytest.raises(IntegrityError):
        EnrichmentFlowStep.objects.create(
            flow=flow,
            enrichment_type=EnrichmentTypeChoices.SUMMARY_V1,
            order=2,
        )


@pytest.mark.django_db
def test_flow_step_should_allow_same_type_in_different_flows(domain_profile):
    flow1 = EnrichmentFlow.objects.create(
        profile=domain_profile,
        target_type=TargetTypeChoices.INCIDENT,
        name="Flow 1",
        priority=10,
    )
    flow2 = EnrichmentFlow.objects.create(
        profile=domain_profile,
        target_type=TargetTypeChoices.INCIDENT,
        name="Flow 2",
        priority=5,
    )

    step1 = EnrichmentFlowStep.objects.create(
        flow=flow1,
        enrichment_type=EnrichmentTypeChoices.SUMMARY_V1,
        order=1,
    )
    step2 = EnrichmentFlowStep.objects.create(
        flow=flow2,
        enrichment_type=EnrichmentTypeChoices.SUMMARY_V1,
        order=1,
    )

    assert step1.enrichment_type == step2.enrichment_type
    assert step1.flow != step2.flow


@pytest.mark.django_db
def test_flow_should_allow_embedding_only_configuration(domain_profile):
    flow = EnrichmentFlow.objects.create(
        profile=domain_profile,
        target_type=TargetTypeChoices.INCIDENT,
        name="Default",
    )
    EnrichmentFlowStep.objects.create(
        flow=flow,
        enrichment_type=EnrichmentTypeChoices.EMBEDDING_V1,
        order=1,
    )

    # Should not raise ValidationError - any step order is valid
    flow.save()

    assert flow.flow_steps.count() == 1


@pytest.mark.django_db
def test_flow_should_allow_any_step_order(domain_profile):
    flow = EnrichmentFlow.objects.create(
        profile=domain_profile,
        target_type=TargetTypeChoices.INCIDENT,
        name="Default",
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

    flow.save()

    assert flow.flow_steps.count() == 2


@pytest.mark.django_db
def test_flow_step_should_be_deleted_with_flow(domain_profile):
    flow = EnrichmentFlow.objects.create(
        profile=domain_profile,
        target_type=TargetTypeChoices.INCIDENT,
        name="Default",
    )
    EnrichmentFlowStep.objects.create(
        flow=flow,
        enrichment_type=EnrichmentTypeChoices.SUMMARY_V1,
        order=1,
    )

    step_count_before = EnrichmentFlowStep.objects.count()
    flow.delete()
    step_count_after = EnrichmentFlowStep.objects.count()

    assert step_count_before == 1
    assert step_count_after == 0


@pytest.mark.django_db
def test_flow_should_be_deleted_with_profile(domain_profile):
    _flow = EnrichmentFlow.objects.create(
        profile=domain_profile,
        target_type=TargetTypeChoices.INCIDENT,
        name="Default",
    )

    flow_count_before = EnrichmentFlow.objects.count()
    domain_profile.delete()
    flow_count_after = EnrichmentFlow.objects.count()

    assert flow_count_before == 1
    assert flow_count_after == 0


@pytest.mark.django_db
def test_flow_step_should_auto_increment_order_starting_at_zero(domain_profile):
    flow = EnrichmentFlow.objects.create(
        profile=domain_profile,
        target_type=TargetTypeChoices.INCIDENT,
        name="Default",
    )

    step1 = EnrichmentFlowStep.objects.create(
        flow=flow,
        enrichment_type=EnrichmentTypeChoices.SUMMARY_V1,
    )
    step2 = EnrichmentFlowStep.objects.create(
        flow=flow,
        enrichment_type=EnrichmentTypeChoices.EMBEDDING_V1,
    )

    assert step1.order == 0
    assert step2.order == 1


@pytest.mark.django_db
def test_flow_step_should_respect_explicit_order_including_zero(domain_profile):
    flow = EnrichmentFlow.objects.create(
        profile=domain_profile,
        target_type=TargetTypeChoices.INCIDENT,
        name="Default",
    )

    step = EnrichmentFlowStep.objects.create(
        flow=flow,
        enrichment_type=EnrichmentTypeChoices.SUMMARY_V1,
        order=0,
    )

    assert step.order == 0


@pytest.mark.django_db
def test_flow_step_should_respect_explicit_order(domain_profile):
    flow = EnrichmentFlow.objects.create(
        profile=domain_profile,
        target_type=TargetTypeChoices.INCIDENT,
        name="Default",
    )

    step = EnrichmentFlowStep.objects.create(
        flow=flow,
        enrichment_type=EnrichmentTypeChoices.SUMMARY_V1,
        order=10,
    )

    assert step.order == 10


@pytest.mark.django_db
def test_flow_step_should_default_to_raw_input_source(domain_profile):
    flow = EnrichmentFlow.objects.create(
        profile=domain_profile,
        target_type=TargetTypeChoices.INCIDENT,
        name="Default",
    )

    step = EnrichmentFlowStep.objects.create(
        flow=flow,
        enrichment_type=EnrichmentTypeChoices.EMBEDDING_V1,
    )

    assert step.input_source == InputSourceChoices.RAW


@pytest.mark.django_db
def test_flow_step_should_allow_raw_input_source(domain_profile):
    flow = EnrichmentFlow.objects.create(
        profile=domain_profile,
        target_type=TargetTypeChoices.INCIDENT,
        name="Default",
    )

    step = EnrichmentFlowStep.objects.create(
        flow=flow,
        enrichment_type=EnrichmentTypeChoices.EMBEDDING_V1,
        input_source=InputSourceChoices.RAW,
    )

    assert step.input_source == InputSourceChoices.RAW


@pytest.mark.django_db
def test_flow_step_should_allow_dependent_input_source(domain_profile):
    flow = EnrichmentFlow.objects.create(
        profile=domain_profile,
        target_type=TargetTypeChoices.INCIDENT,
        name="Default",
    )

    step = EnrichmentFlowStep.objects.create(
        flow=flow,
        enrichment_type=EnrichmentTypeChoices.EMBEDDING_V1,
        input_source=InputSourceChoices.DEPENDENT,
    )

    assert step.input_source == InputSourceChoices.DEPENDENT


@pytest.mark.django_db
def test_flow_should_match_when_filters_empty(domain_profile):
    flow = EnrichmentFlow.objects.create(
        profile=domain_profile,
        target_type=TargetTypeChoices.INCIDENT,
        name="Catch-All",
        priority=0,
        enabled=True,
    )

    assert flow.matches(category="infrastructure", severity="high", service="api") is True
    assert flow.matches(category=None, severity=None, service=None) is True


@pytest.mark.django_db
def test_flow_should_match_when_category_in_filter(domain_profile):
    flow = EnrichmentFlow.objects.create(
        profile=domain_profile,
        target_type=TargetTypeChoices.INCIDENT,
        name="Infra Only",
        category_filter=["infrastructure", "networking"],
        enabled=True,
    )

    assert flow.matches(category="infrastructure") is True
    assert flow.matches(category="networking") is True
    assert flow.matches(category="authentication") is False


@pytest.mark.django_db
def test_flow_should_match_when_severity_in_filter(domain_profile):
    flow = EnrichmentFlow.objects.create(
        profile=domain_profile,
        target_type=TargetTypeChoices.INCIDENT,
        name="Critical Only",
        severity_filter=["critical", "high"],
        enabled=True,
    )

    assert flow.matches(severity="critical") is True
    assert flow.matches(severity="high") is True
    assert flow.matches(severity="low") is False


@pytest.mark.django_db
def test_flow_should_match_when_service_in_filter(domain_profile):
    flow = EnrichmentFlow.objects.create(
        profile=domain_profile,
        target_type=TargetTypeChoices.INCIDENT,
        name="API Only",
        service_filter=["api-gateway", "auth-service"],
        enabled=True,
    )

    assert flow.matches(service="api-gateway") is True
    assert flow.matches(service="auth-service") is True
    assert flow.matches(service="database") is False


@pytest.mark.django_db
def test_flow_should_require_all_filters_to_match(domain_profile):
    flow = EnrichmentFlow.objects.create(
        profile=domain_profile,
        target_type=TargetTypeChoices.INCIDENT,
        name="Specific Flow",
        category_filter=["infrastructure"],
        severity_filter=["critical"],
        service_filter=["api-gateway"],
        enabled=True,
    )

    # All filters match
    assert (
        flow.matches(category="infrastructure", severity="critical", service="api-gateway") is True
    )

    # One filter doesn't match
    assert (
        flow.matches(category="authentication", severity="critical", service="api-gateway") is False
    )
    assert flow.matches(category="infrastructure", severity="low", service="api-gateway") is False
    assert flow.matches(category="infrastructure", severity="critical", service="database") is False


@pytest.mark.django_db
def test_flow_should_not_match_when_disabled(domain_profile):
    flow = EnrichmentFlow.objects.create(
        profile=domain_profile,
        target_type=TargetTypeChoices.INCIDENT,
        name="Disabled Flow",
        enabled=False,
    )

    assert flow.matches(category="infrastructure", severity="high", service="api") is False


@pytest.mark.django_db
def test_flow_should_match_empty_filter_with_any_value(domain_profile):
    flow = EnrichmentFlow.objects.create(
        profile=domain_profile,
        target_type=TargetTypeChoices.INCIDENT,
        name="Partial Filters",
        category_filter=["infrastructure"],
        # severity_filter and service_filter are empty (match all)
        enabled=True,
    )

    assert flow.matches(category="infrastructure", severity="critical", service="api") is True
    assert flow.matches(category="infrastructure", severity=None, service=None) is True
    assert flow.matches(category="authentication", severity="critical", service="api") is False
