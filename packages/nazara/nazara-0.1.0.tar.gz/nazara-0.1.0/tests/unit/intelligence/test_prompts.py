from unittest.mock import MagicMock

import pytest

from nazara.intelligence.domain.prompts import (
    PromptNotFoundError,
    build_organizational_context,
    format_user_content,
    list_prompts,
    load_prompt,
    render_prompt,
)


def _make_mock_queryset(items: list):
    mock_qs = MagicMock()
    mock_qs.exists.return_value = len(items) > 0
    mock_qs.__iter__ = lambda self: iter(items)
    return mock_qs


def _make_empty_profile():
    mock_profile = MagicMock()
    mock_profile.categories.all.return_value = _make_mock_queryset([])
    mock_profile.severities.all.return_value = _make_mock_queryset([])
    mock_profile.systems.all.return_value = _make_mock_queryset([])
    mock_profile.glossary.all.return_value = _make_mock_queryset([])
    mock_profile.operational_policies.all.return_value = _make_mock_queryset([])
    return mock_profile


def test_load_prompt_should_load_existing_prompt():
    result = load_prompt("summary.v1")

    assert "expert at summarizing" in result
    assert "{organizational_context}" in result


def test_load_prompt_should_raise_error_for_missing_prompt():
    with pytest.raises(PromptNotFoundError) as exc_info:
        load_prompt("nonexistent.v1")

    assert "not found" in str(exc_info.value)


def test_load_prompt_should_cache_loaded_prompts():
    load_prompt.cache_clear()
    result1 = load_prompt("summary.v1")
    result2 = load_prompt("summary.v1")

    assert result1 is result2


def test_list_prompts_should_return_available_prompts():
    result = list_prompts()

    assert "summary.v1" in result


@pytest.mark.parametrize("profile", [None, "empty"])
def test_render_prompt_should_remove_placeholder_without_context(profile):
    if profile == "empty":
        profile = _make_empty_profile()

    result = render_prompt("summary.v1", profile=profile)

    assert "expert at summarizing" in result
    assert "{organizational_context}" not in result


def test_render_prompt_should_inject_organizational_context():
    mock_system = MagicMock()
    mock_system.label = "Proxy Service"
    mock_system.get_entry_type_display.return_value = "Internal Service"
    mock_system.description = "Handles proxy allocation"

    mock_profile = _make_empty_profile()
    mock_profile.systems.all.return_value = _make_mock_queryset([mock_system])

    result = render_prompt("summary.v1", profile=mock_profile)

    assert "## Known Systems" in result
    assert "Proxy Service" in result


def test_build_organizational_context_should_return_empty_for_empty_profile():
    result = build_organizational_context(_make_empty_profile())

    assert result == ""


@pytest.mark.parametrize(
    "section_type,mock_attr,expected_header",
    [
        ("categories", "categories", "## Business Categories"),
        ("severities", "severities", "## Severity Levels"),
        ("systems", "systems", "## Known Systems"),
        ("glossary", "glossary", "## Terminology"),
        ("policies", "operational_policies", "## Operational Priorities"),
    ],
)
def test_build_organizational_context_should_format_section(
    section_type, mock_attr, expected_header
):
    mock_item = MagicMock()
    if section_type == "categories":
        mock_item.label = "Proxy Allocation"
        mock_item.description = "Proxy assignment and IP allocation"
    elif section_type == "severities":
        mock_item.label = "Critical"
        mock_item.description = "Service outage, all customers affected"
    elif section_type == "systems":
        mock_item.label = "Test System"
        mock_item.get_entry_type_display.return_value = "Service"
        mock_item.description = "Description"
    elif section_type == "glossary":
        mock_item.term = "test_term"
        mock_item.definition = "Definition"
        mock_item.aliases = []
    else:
        mock_item.statement = "Policy statement"

    mock_profile = _make_empty_profile()
    getattr(mock_profile, mock_attr).all.return_value = _make_mock_queryset([mock_item])

    result = build_organizational_context(mock_profile)

    assert expected_header in result


def test_format_user_content_should_format_title_and_description():
    result = format_user_content(title="Test Title", description="Test Description")

    assert "Title: Test Title" in result
    assert "Description: Test Description" in result


def test_format_user_content_should_format_metadata():
    result = format_user_content(
        title="Issue",
        description="Desc",
        metadata={"severity": "critical", "affected_services": ["svc1", "svc2"]},
    )

    assert "Signal Metadata:" in result
    assert "Severity: critical" in result
    assert "Affected Services: svc1, svc2" in result


@pytest.mark.parametrize(
    "metadata,should_have_metadata_section",
    [
        ({}, False),
        ({"status": None}, False),
        ({"severity": "high"}, True),
    ],
)
def test_format_user_content_metadata_edge_cases(metadata, should_have_metadata_section):
    result = format_user_content(title="Issue", description="Desc", metadata=metadata)

    assert ("Signal Metadata:" in result) == should_have_metadata_section


def test_render_prompt_should_use_narrowed_context_when_provided():
    from nazara.intelligence.domain.context_narrowing import (
        NarrowingMeta,
        NarrowingResult,
    )

    mock_system = MagicMock()
    mock_system.label = "Proxy Service"
    mock_system.get_entry_type_display.return_value = "Internal Service"
    mock_system.description = "Handles proxy allocation"

    narrowing = NarrowingResult(
        systems=(mock_system,),
        categories=(),
        glossary=(),
        policies=(),
        severities=(),
        meta=NarrowingMeta(
            signal_type="Incident",
            source_system="jira",
            environment=None,
            severity=None,
            status=None,
            total_systems=10,
            total_categories=5,
            total_glossary=20,
            total_policies=3,
            selected_systems=1,
            selected_categories=0,
            selected_glossary=0,
            selected_policies=0,
        ),
    )

    result = render_prompt("summary.v1", narrowing=narrowing)

    assert "## Relevant Systems" in result
    assert "Proxy Service" in result
    assert "{organizational_context}" not in result


def test_render_prompt_narrowing_takes_precedence_over_profile():
    from nazara.intelligence.domain.context_narrowing import (
        NarrowingMeta,
        NarrowingResult,
    )

    mock_profile = _make_empty_profile()
    mock_system = MagicMock()
    mock_system.label = "Profile System"
    mock_system.get_entry_type_display.return_value = "Service"
    mock_system.description = "From profile"
    mock_profile.systems.all.return_value = _make_mock_queryset([mock_system])

    narrowing = NarrowingResult(
        systems=(),
        categories=(),
        glossary=(),
        policies=(),
        severities=(),
        meta=NarrowingMeta(
            signal_type="Incident",
            source_system="jira",
            environment=None,
            severity=None,
            status=None,
            total_systems=10,
            total_categories=5,
            total_glossary=20,
            total_policies=3,
            selected_systems=0,
            selected_categories=0,
            selected_glossary=0,
            selected_policies=0,
        ),
    )

    result = render_prompt("summary.v1", profile=mock_profile, narrowing=narrowing)

    assert "Profile System" not in result
    assert "{organizational_context}" not in result
