from unittest.mock import MagicMock

import pytest

from nazara.intelligence.domain.context_narrowing import (
    MAX_CATEGORIES,
    MAX_GLOSSARY,
    MAX_POLICIES,
    MAX_SYSTEMS,
    ContextNarrowingService,
    NarrowingResult,
    SignalText,
    build_narrowed_context,
    extract_signal_text,
    match_categories,
    match_glossary,
    match_policies,
    match_systems,
)


def _make_mock_queryset(items: list):
    mock_qs = MagicMock()
    mock_qs.all.return_value = mock_qs
    mock_qs.order_by.return_value = mock_qs
    mock_qs.__iter__ = lambda self: iter(items)
    mock_qs.__len__ = lambda self: len(items)
    return mock_qs


def _make_mock_profile(
    systems: list | None = None,
    categories: list | None = None,
    glossary: list | None = None,
    policies: list | None = None,
    severities: list | None = None,
):
    mock = MagicMock()
    mock.systems = _make_mock_queryset(systems or [])
    mock.categories = _make_mock_queryset(categories or [])
    mock.glossary = _make_mock_queryset(glossary or [])
    mock.operational_policies = _make_mock_queryset(policies or [])
    mock.severities = _make_mock_queryset(severities or [])
    return mock


def _make_mock_incident(
    title: str = "Test Incident",
    description: str = "Test description",
    affected_services: list[str] | None = None,
    source_system: str = "incident_io",
    severity: str = "high",
    status: str = "open",
    impact_description: str | None = None,
    root_cause_description: str | None = None,
    tags: list[str] | None = None,
):
    mock = MagicMock()
    mock.SIGNAL_TYPE = "Incident"
    mock.title = title
    mock.description = description
    mock.affected_services = affected_services or []
    mock.source_system = source_system
    mock.severity = severity
    mock.status = status
    mock.impact_description = impact_description
    mock.root_cause_description = root_cause_description
    mock.tags = tags or []
    return mock


def _make_mock_customer_case(
    title: str = "Test Case",
    description: str = "Test description",
    source_system: str = "intercom",
    tags: list[str] | None = None,
):
    mock = MagicMock()
    mock.SIGNAL_TYPE = "CustomerCase"
    mock.title = title
    mock.description = description
    mock.source_system = source_system
    mock.tags = tags or []
    return mock


def _make_mock_technical_issue(
    title: str = "Test Issue",
    last_message: str = "Error occurred",
    provider: str = "sentry",
    service: str = "proxyauth",
    environment: str = "production",
    status: str = "active",
):
    mock = MagicMock()
    mock.SIGNAL_TYPE = "TechnicalIssue"
    mock.title = title
    mock.last_message = last_message
    mock.provider = provider
    mock.service = service
    mock.environment = environment
    mock.status = status
    return mock


def _make_mock_system(
    key: str,
    label: str,
    entry_type: str = "service",
    description: str = "",
):
    mock = MagicMock()
    mock.key = key
    mock.label = label
    mock.entry_type = entry_type
    mock.description = description
    mock.get_entry_type_display.return_value = entry_type.title()
    return mock


def _make_mock_category(key: str, label: str, description: str = ""):
    mock = MagicMock()
    mock.key = key
    mock.label = label
    mock.description = description
    return mock


def _make_mock_severity(key: str, label: str, rank: int, description: str = ""):
    mock = MagicMock()
    mock.key = key
    mock.label = label
    mock.rank = rank
    mock.description = description
    return mock


def _make_mock_glossary_term(
    term: str, definition: str = "Definition", aliases: list[str] | None = None
):
    mock = MagicMock()
    mock.term = term
    mock.definition = definition
    mock.aliases = aliases or []
    return mock


def _make_mock_policy(key: str, statement: str):
    mock = MagicMock()
    mock.key = key
    mock.statement = statement
    return mock


# extract_signal_text tests


def test_extract_signal_text_should_extract_from_incident():
    signal = _make_mock_incident(
        title="Redis connection failure",
        description="Multiple services are experiencing timeouts",
        affected_services=["billing-api", "proxyauth"],
        source_system="incident_io",
        impact_description="Payment processing delayed",
        root_cause_description="Redis cluster memory exhausted",
        tags=["infrastructure", "critical"],
    )

    result = extract_signal_text(signal)

    assert result.title == "Redis connection failure"
    assert result.description == "Multiple services are experiencing timeouts"
    assert result.services == ("billing-api", "proxyauth")
    assert result.source_system == "incident_io"
    assert "redis" in result.full_text
    assert "billing-api" in result.full_text
    assert "infrastructure" in result.full_text


def test_extract_signal_text_should_extract_from_customer_case():
    signal = _make_mock_customer_case(
        title="Cannot connect to proxy",
        description="Getting 402 errors on all requests",
        source_system="intercom",
        tags=["bandwidth", "billing"],
    )

    result = extract_signal_text(signal)

    assert result.title == "Cannot connect to proxy"
    assert result.source_system == "intercom"
    assert result.services == ()
    assert "402" in result.full_text
    assert "bandwidth" in result.full_text


def test_extract_signal_text_should_extract_from_technical_issue():
    signal = _make_mock_technical_issue(
        title="ConnectionError: Redis timeout",
        last_message="Connection to redis://localhost:6379 timed out",
        provider="sentry",
        service="proxyauth",
        environment="production",
    )

    result = extract_signal_text(signal)

    assert result.title == "ConnectionError: Redis timeout"
    assert result.description == "Connection to redis://localhost:6379 timed out"
    assert result.source_system == "sentry"
    assert result.services == ("proxyauth",)
    assert "redis" in result.full_text
    assert "production" in result.full_text


def test_extract_signal_text_should_handle_none_values():
    signal = _make_mock_incident(
        title="Test",
        description="",
        affected_services=None,
        impact_description=None,
        root_cause_description=None,
        tags=None,
    )

    result = extract_signal_text(signal)

    assert result.title == "Test"
    assert result.services == ()


def test_extract_signal_text_should_raise_for_unknown_signal_type():
    mock = MagicMock()
    mock.SIGNAL_TYPE = "UnknownType"

    with pytest.raises(ValueError, match="Unknown signal type"):
        extract_signal_text(mock)


# match_systems tests


def test_match_systems_should_match_explicit_services():
    systems = [
        _make_mock_system("redis", "Redis Cluster", "infra"),
        _make_mock_system("proxyauth", "Proxy Auth", "service"),
    ]
    signal_text = SignalText(
        title="Test",
        description="",
        services=("proxyauth",),
        source_system="incident_io",
        full_text="test proxyauth issue",
    )

    result = match_systems(signal_text, systems)

    assert len(result) == 1
    assert result[0].key == "proxyauth"


def test_match_systems_should_match_source_system():
    systems = [
        _make_mock_system("sentry", "Sentry", "external"),
        _make_mock_system("proxyauth", "Proxy Auth", "service"),
    ]
    signal_text = SignalText(
        title="Test",
        description="",
        services=(),
        source_system="sentry",
        full_text="test issue",
    )

    result = match_systems(signal_text, systems)

    assert len(result) == 1
    assert result[0].key == "sentry"


def test_match_systems_should_match_key_in_text():
    systems = [
        _make_mock_system("redis", "Redis Cluster", "infra"),
        _make_mock_system("postgresql", "PostgreSQL", "infra"),
    ]
    signal_text = SignalText(
        title="Redis connection error",
        description="",
        services=(),
        source_system="incident_io",
        full_text="redis connection error timeout",
    )

    result = match_systems(signal_text, systems)

    assert len(result) == 1
    assert result[0].key == "redis"


def test_match_systems_should_match_label_in_text():
    systems = [_make_mock_system("proxycontrolpanel", "Proxy Control Panel", "service")]
    signal_text = SignalText(
        title="Issue with proxy control panel",
        description="",
        services=(),
        source_system="incident_io",
        full_text="issue with proxy control panel not loading",
    )

    result = match_systems(signal_text, systems)

    assert len(result) == 1
    assert result[0].key == "proxycontrolpanel"


def test_match_systems_should_respect_max_systems_limit():
    systems = [_make_mock_system(f"sys{i}", f"System {i}", "service") for i in range(15)]
    signal_text = SignalText(
        title="All systems issue",
        description="",
        services=(),
        source_system="incident_io",
        full_text=" ".join(f"sys{i}" for i in range(15)),
    )

    result = match_systems(signal_text, systems)

    assert len(result) <= MAX_SYSTEMS


def test_match_systems_should_prioritize_by_score_then_entry_type():
    systems = [
        _make_mock_system("redis", "Redis", "infra"),
        _make_mock_system("proxyauth", "Proxy Auth", "service"),
    ]
    signal_text = SignalText(
        title="Test",
        description="",
        services=(),
        source_system="incident_io",
        full_text="redis proxyauth issue",
    )

    result = match_systems(signal_text, systems)

    assert len(result) == 2
    assert result[0].entry_type == "service"
    assert result[1].entry_type == "infra"


# match_categories tests


def test_match_categories_should_match_infrastructure_when_infra_system_present():
    categories = [
        _make_mock_category("infrastructure", "Infrastructure", "Database, Redis"),
        _make_mock_category("billing", "Billing", "Payments, invoices"),
    ]
    systems = (_make_mock_system("redis", "Redis", "infra"),)
    signal_text = SignalText(
        title="Test", description="", services=(), source_system="", full_text="test"
    )

    result = match_categories(signal_text, categories, systems)

    assert len(result) == 1
    assert result[0].key == "infrastructure"


def test_match_categories_should_match_system_key_in_description():
    categories = [
        _make_mock_category("authentication", "Authentication", "Auth failures, proxyauth issues"),
    ]
    systems = (_make_mock_system("proxyauth", "Proxy Auth", "service"),)
    signal_text = SignalText(
        title="Test", description="", services=(), source_system="", full_text="test"
    )

    result = match_categories(signal_text, categories, systems)

    assert len(result) == 1
    assert result[0].key == "authentication"


def test_match_categories_should_match_text_keywords_in_description():
    categories = [
        _make_mock_category(
            "billing",
            "Billing",
            "Subscriptions invoices payment methods refunds Stripe PayPal integration",
        ),
    ]
    systems = ()
    signal_text = SignalText(
        title="Payment failed",
        description="",
        services=(),
        source_system="",
        full_text="payment stripe invoice subscription failed",
    )

    result = match_categories(signal_text, categories, systems)

    assert len(result) == 1
    assert result[0].key == "billing"


def test_match_categories_should_respect_max_categories_limit():
    categories = [
        _make_mock_category(f"cat{i}", f"Category {i}", f"keyword{i} testing") for i in range(10)
    ]
    systems = ()
    signal_text = SignalText(
        title="Test",
        description="",
        services=(),
        source_system="",
        full_text=" ".join(f"keyword{i} testing" for i in range(10)),
    )

    result = match_categories(signal_text, categories, systems)

    assert len(result) <= MAX_CATEGORIES


# match_glossary tests


def test_match_glossary_should_match_exact_term():
    glossary = [_make_mock_glossary_term("PAG", "Proxy Allocation Group")]
    signal_text = SignalText(
        title="PAG allocation failed",
        description="",
        services=(),
        source_system="",
        full_text="pag allocation failed for user",
    )

    result = match_glossary(signal_text, glossary)

    assert len(result) == 1
    assert result[0].term == "PAG"


def test_match_glossary_should_match_alias():
    glossary = [
        _make_mock_glossary_term(
            "bandwidth", "Data transfer limit", aliases=["data transfer", "BW"]
        )
    ]
    signal_text = SignalText(
        title="Data transfer limit exceeded",
        description="",
        services=(),
        source_system="",
        full_text="data transfer limit exceeded for subscription",
    )

    result = match_glossary(signal_text, glossary)

    assert len(result) == 1
    assert result[0].term == "bandwidth"


def test_match_glossary_should_use_word_boundary_for_short_terms():
    glossary = [_make_mock_glossary_term("402", "Payment Required error")]
    signal_text = SignalText(
        title="Error 402 on requests",
        description="",
        services=(),
        source_system="",
        full_text="error 402 on requests",
    )

    result = match_glossary(signal_text, glossary)

    assert len(result) == 1
    assert result[0].term == "402"


def test_match_glossary_should_not_match_short_term_embedded_in_word():
    glossary = [_make_mock_glossary_term("402", "Payment Required error")]
    signal_text = SignalText(
        title="Error code 14025",
        description="",
        services=(),
        source_system="",
        full_text="error code 14025 returned",
    )

    result = match_glossary(signal_text, glossary)

    assert len(result) == 0


def test_match_glossary_should_respect_max_glossary_limit():
    glossary = [_make_mock_glossary_term(f"term{i}", f"Definition {i}") for i in range(20)]
    signal_text = SignalText(
        title="Test",
        description="",
        services=(),
        source_system="",
        full_text=" ".join(f"term{i}" for i in range(20)),
    )

    result = match_glossary(signal_text, glossary)

    assert len(result) <= MAX_GLOSSARY


# match_policies tests


def test_match_policies_should_match_category_key_in_policy_key():
    policies = [
        _make_mock_policy("billing-priority", "Billing issues are high priority"),
        _make_mock_policy("security-first", "Security issues require immediate attention"),
    ]
    categories = (_make_mock_category("billing", "Billing"),)
    glossary = ()
    signal_text = SignalText(
        title="Test", description="", services=(), source_system="", full_text="test"
    )

    result = match_policies(signal_text, policies, categories, glossary)

    assert len(result) == 1
    assert result[0].key == "billing-priority"


def test_match_policies_should_match_glossary_term_in_policy_key():
    policies = [
        _make_mock_policy("402-bandwidth-shared", "402 errors can affect multiple plans"),
    ]
    categories = ()
    glossary = (_make_mock_glossary_term("402", "Payment Required"),)
    signal_text = SignalText(
        title="Test", description="", services=(), source_system="", full_text="test"
    )

    result = match_policies(signal_text, policies, categories, glossary)

    assert len(result) == 1
    assert result[0].key == "402-bandwidth-shared"


def test_match_policies_should_respect_max_policies_limit():
    policies = [
        _make_mock_policy(f"cat{i}-policy", "Statement with keyword testing pattern")
        for i in range(10)
    ]
    categories = tuple(_make_mock_category(f"cat{i}", f"Category {i}") for i in range(10))
    glossary = ()
    signal_text = SignalText(
        title="Test", description="", services=(), source_system="", full_text="test"
    )

    result = match_policies(signal_text, policies, categories, glossary)

    assert len(result) <= MAX_POLICIES


# ContextNarrowingService tests


def test_narrow_should_return_empty_for_empty_profile():
    service = ContextNarrowingService()
    signal = _make_mock_incident()
    profile = _make_mock_profile()

    result = service.narrow(signal, profile)

    assert result.systems == ()
    assert result.categories == ()
    assert result.glossary == ()
    assert result.policies == ()
    assert result.severities == ()


def test_narrow_should_match_system_from_text():
    service = ContextNarrowingService()
    signal = _make_mock_incident(
        title="Redis connection timeout",
        description="Services are timing out connecting to Redis",
    )
    redis_system = _make_mock_system("redis", "Redis Cluster", "infra")
    profile = _make_mock_profile(systems=[redis_system])

    result = service.narrow(signal, profile)

    assert len(result.systems) == 1
    assert result.systems[0].key == "redis"


def test_narrow_should_include_all_severities():
    service = ContextNarrowingService()
    signal = _make_mock_incident()
    severities = [
        _make_mock_severity("critical", "Critical", 100),
        _make_mock_severity("high", "High", 75),
        _make_mock_severity("medium", "Medium", 50),
        _make_mock_severity("low", "Low", 25),
    ]
    profile = _make_mock_profile(severities=severities)

    result = service.narrow(signal, profile)

    assert len(result.severities) == 4


def test_narrow_should_build_narrowing_meta():
    service = ContextNarrowingService()
    signal = _make_mock_incident(
        source_system="incident_io",
        severity="critical",
        status="investigating",
    )
    systems = [_make_mock_system("redis", "Redis", "infra")]
    profile = _make_mock_profile(systems=systems)

    result = service.narrow(signal, profile)

    assert result.meta is not None
    assert result.meta.signal_type == "Incident"
    assert result.meta.source_system == "incident_io"
    assert result.meta.severity == "critical"
    assert result.meta.status == "investigating"
    assert result.meta.total_systems == 1


def test_narrow_should_handle_technical_issue():
    service = ContextNarrowingService()
    signal = _make_mock_technical_issue(
        title="ConnectionError in proxyauth",
        last_message="Connection refused",
        provider="sentry",
        service="proxyauth",
        environment="production",
        status="active",
    )
    proxyauth = _make_mock_system("proxyauth", "Proxy Auth", "service")
    profile = _make_mock_profile(systems=[proxyauth])

    result = service.narrow(signal, profile)

    assert len(result.systems) == 1
    assert result.systems[0].key == "proxyauth"
    assert result.meta.environment == "production"


# build_narrowed_context tests


def test_build_narrowed_context_should_return_empty_for_empty_result():
    result = NarrowingResult()

    context = build_narrowed_context(result)

    assert context == ""


def test_build_narrowed_context_should_format_categories_section():
    category = _make_mock_category("infrastructure", "Infrastructure", "Database and Redis")
    result = NarrowingResult(categories=(category,))

    context = build_narrowed_context(result)

    assert "## Relevant Categories" in context
    assert "**Infrastructure**" in context
    assert "Database and Redis" in context


def test_build_narrowed_context_should_format_severities_section():
    severity = _make_mock_severity("critical", "Critical", 100, "Service outage")
    result = NarrowingResult(severities=(severity,))

    context = build_narrowed_context(result)

    assert "## Severity Levels" in context
    assert "**Critical**" in context
    assert "Service outage" in context


def test_build_narrowed_context_should_format_systems_section():
    system = _make_mock_system("redis", "Redis Cluster", "infra", "Cache layer")
    result = NarrowingResult(systems=(system,))

    context = build_narrowed_context(result)

    assert "## Relevant Systems" in context
    assert "**Redis Cluster**" in context
    assert "Infra" in context
    assert "Cache layer" in context


def test_build_narrowed_context_should_format_glossary_section():
    term = _make_mock_glossary_term("PAG", "Proxy Allocation Group", ["allocation group"])
    result = NarrowingResult(glossary=(term,))

    context = build_narrowed_context(result)

    assert "## Key Terminology" in context
    assert "**PAG**" in context
    assert "allocation group" in context
    assert "Proxy Allocation Group" in context


def test_build_narrowed_context_should_format_policies_section():
    policy = _make_mock_policy("billing-priority", "Billing issues are high priority")
    result = NarrowingResult(policies=(policy,))

    context = build_narrowed_context(result)

    assert "## Operational Context" in context
    assert "Billing issues are high priority" in context


def test_build_narrowed_context_should_format_all_sections():
    result = NarrowingResult(
        categories=(_make_mock_category("infra", "Infrastructure", "Desc"),),
        severities=(_make_mock_severity("high", "High", 75, "Major issue"),),
        systems=(_make_mock_system("redis", "Redis", "infra", "Cache"),),
        glossary=(_make_mock_glossary_term("PAG", "Group", []),),
        policies=(_make_mock_policy("billing", "Statement"),),
    )

    context = build_narrowed_context(result)

    assert "## Relevant Categories" in context
    assert "## Severity Levels" in context
    assert "## Relevant Systems" in context
    assert "## Key Terminology" in context
    assert "## Operational Context" in context
    assert context.endswith("\n")
