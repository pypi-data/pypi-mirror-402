from typing import Any

import pytest

from nazara.intelligence.domain.contracts.step import EnrichmentStep, StepResult
from nazara.intelligence.domain.step_registry import (
    STEP_REGISTRY,
    clear_registry,
    get_step_class,
    list_step_keys,
    register_step,
)


class MockStep(EnrichmentStep):
    """Minimal step implementation for testing."""

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
        return StepResult(success=True, output={"test": "value"})


@pytest.fixture(autouse=True)
def clean_registry_fixture():
    clear_registry()
    yield
    clear_registry()


def test_register_step_should_add_class_to_registry():
    @register_step("test")
    class TestStep(MockStep):
        pass

    assert "test" in STEP_REGISTRY
    assert STEP_REGISTRY["test"] is TestStep


def test_register_step_should_return_original_class():
    @register_step("decorated")
    class DecoratedStep(MockStep):
        pass

    assert DecoratedStep.__name__ == "DecoratedStep"


def test_register_step_should_allow_multiple_registrations():
    @register_step("step_a")
    class StepA(MockStep):
        pass

    @register_step("step_b")
    class StepB(MockStep):
        pass

    assert STEP_REGISTRY["step_a"] is StepA
    assert STEP_REGISTRY["step_b"] is StepB


def test_get_step_class_should_return_registered_class():
    @register_step("findable")
    class FindableStep(MockStep):
        pass

    result = get_step_class("findable")

    assert result is FindableStep


def test_get_step_class_should_return_none_for_unknown_key():
    result = get_step_class("unknown")

    assert result is None


def test_list_step_keys_should_return_empty_list_initially():
    result = list_step_keys()

    assert result == []


def test_list_step_keys_should_return_all_registered_keys():
    @register_step("key_one")
    class StepOne(MockStep):
        pass

    @register_step("key_two")
    class StepTwo(MockStep):
        pass

    result = list_step_keys()

    assert set(result) == {"key_one", "key_two"}


def test_clear_registry_should_remove_all_entries():
    @register_step("to_clear")
    class ToClearStep(MockStep):
        pass

    assert len(STEP_REGISTRY) > 0

    clear_registry()

    assert len(STEP_REGISTRY) == 0


def test_clear_registry_should_allow_reregistration_with_same_key():
    @register_step("reusable")
    class FirstStep(MockStep):
        pass

    clear_registry()

    @register_step("reusable")
    class SecondStep(MockStep):
        pass

    assert get_step_class("reusable") is SecondStep
