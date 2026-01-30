import pytest

from nazara.shared.domain.value_objects.types import OutputType


def test_output_type_should_have_correct_values():
    assert OutputType.TECHNICAL_EVENT.value == "technical_event"
    assert OutputType.TECHNICAL_ISSUE.value == "technical_issue"
    assert OutputType.INCIDENT.value == "incident"
    assert OutputType.CUSTOMER_CASE.value == "customer_case"


def test_output_type_should_be_created_from_string():
    assert OutputType("technical_event") == OutputType.TECHNICAL_EVENT
    assert OutputType("incident") == OutputType.INCIDENT


def test_output_type_should_raise_when_invalid():
    with pytest.raises(ValueError):
        OutputType("invalid_type")


def test_output_type_should_be_string_enum():
    assert isinstance(OutputType.INCIDENT, str)
    assert OutputType.INCIDENT == "incident"
