from typing import Any

import pytest

from nazara.intelligence.application.flow_validator import (
    FlowValidationError,
    validate_flow_steps,
)
from nazara.intelligence.domain.contracts.step import EnrichmentStep, StepResult
from nazara.intelligence.domain.step_registry import clear_registry, register_step


class MockStep(EnrichmentStep):
    """Minimal step implementation for testing."""

    requires = []

    @property
    def key(self) -> str:
        return "mock"

    @property
    def produces(self) -> str:
        return "result"

    @property
    def uses_llm(self) -> bool:
        return False

    def is_available(self) -> bool:
        return True

    def compute_input_hash(self, signal: Any, context: dict[str, Any]) -> str:
        return "hash"

    def should_run(
        self, signal: Any, record: Any, context: dict[str, Any], force: bool = False
    ) -> tuple[bool, str]:
        return True, "always"

    def execute(self, signal: Any, profile: Any, context: dict[str, Any]) -> StepResult:
        return StepResult(success=True)


@pytest.fixture(autouse=True)
def clean_registry_fixture():
    clear_registry()
    yield
    clear_registry()


@pytest.fixture
def registered_steps():
    @register_step("summary")
    class SummaryStep(MockStep):
        requires = []

        @property
        def key(self) -> str:
            return "summary"

    @register_step("embedding")
    class EmbeddingStep(MockStep):
        requires = []  # No hard dependencies - input source is configurable

        @property
        def key(self) -> str:
            return "embedding"

    @register_step("triage")
    class TriageStep(MockStep):
        requires = []

        @property
        def key(self) -> str:
            return "triage"

    return {"summary": SummaryStep, "embedding": EmbeddingStep, "triage": TriageStep}


def test_validate_flow_steps_should_return_empty_list_for_valid_order(registered_steps):
    steps = ["summary.v1", "embedding.v1"]

    errors = validate_flow_steps(steps)

    assert errors == []


def test_validate_flow_steps_should_allow_any_order(registered_steps):
    # embedding no longer requires summary - any order is valid
    steps = ["embedding.v1", "summary.v1"]

    errors = validate_flow_steps(steps)

    assert errors == []


def test_validate_flow_steps_should_detect_unknown_step_type(registered_steps):
    steps = ["unknown.v1"]

    errors = validate_flow_steps(steps)

    assert len(errors) == 1
    assert "Unknown step type: unknown.v1" in errors[0]


def test_validate_flow_steps_should_return_empty_for_steps_without_dependencies(
    registered_steps,
):
    steps = ["summary.v1", "triage.v1"]

    errors = validate_flow_steps(steps)

    assert errors == []


def test_validate_flow_steps_should_return_empty_for_empty_list(registered_steps):
    errors = validate_flow_steps([])

    assert errors == []


def test_validate_flow_steps_should_allow_single_step_with_no_dependencies(
    registered_steps,
):
    steps = ["summary.v1"]

    errors = validate_flow_steps(steps)

    assert errors == []


def test_validate_flow_steps_should_handle_version_suffix_correctly(registered_steps):
    # summary.v2 should satisfy embedding's dependency on "summary"
    steps = ["summary.v2", "embedding.v1"]

    errors = validate_flow_steps(steps)

    assert errors == []


def test_validate_flow_steps_should_detect_unknown_step_only(registered_steps):
    # Unknown step should still be detected, embedding has no dependencies
    steps = ["unknown.v1", "embedding.v1"]

    errors = validate_flow_steps(steps)

    assert len(errors) == 1
    assert "Unknown step type" in errors[0]


def test_flow_validation_error_should_contain_error_list():
    errors = ["Error 1", "Error 2"]

    exc = FlowValidationError(errors)

    assert exc.errors == errors
    assert "Error 1" in str(exc)
    assert "Error 2" in str(exc)
