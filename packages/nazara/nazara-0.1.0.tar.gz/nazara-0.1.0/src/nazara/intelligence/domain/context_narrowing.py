from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from nazara.intelligence.domain.models import (
        DomainCategory,
        DomainProfile,
        GlossaryTerm,
        OperationalPolicy,
        SeverityLevel,
        SystemCatalogEntry,
    )
    from nazara.signals.domain.models import CustomerCase, Incident, TechnicalIssue

SCORE_EXPLICIT_SERVICE = 200
SCORE_SOURCE_SYSTEM = 150
SCORE_KEY_MATCH = 100
SCORE_LABEL_MATCH = 80
SCORE_DESCRIPTION_KEYWORD = 50

SCORE_INFRA_SYSTEM = 100
SCORE_SYSTEM_IN_DESC = 80
SCORE_TEXT_IN_DESC = 50

SCORE_TERM_EXACT = 100
SCORE_ALIAS_MATCH = 80

SCORE_CATEGORY_MATCH = 100
SCORE_GLOSSARY_MATCH = 80

MAX_SYSTEMS = 8
MAX_CATEGORIES = 3
MAX_GLOSSARY = 10
MAX_POLICIES = 5

MIN_KEYWORD_LENGTH = 5


@dataclass(frozen=True)
class SignalText:
    title: str
    description: str
    services: tuple[str, ...]
    source_system: str
    full_text: str


@dataclass(frozen=True)
class MatchedEntity:
    entity: DomainCategory | SystemCatalogEntry | GlossaryTerm | OperationalPolicy
    score: int
    match_reason: str


@dataclass(frozen=True)
class NarrowingMeta:
    signal_type: str
    source_system: str
    environment: str | None
    severity: str | None
    status: str | None
    total_systems: int
    total_categories: int
    total_glossary: int
    total_policies: int
    selected_systems: int
    selected_categories: int
    selected_glossary: int
    selected_policies: int


@dataclass
class NarrowingResult:
    systems: tuple[SystemCatalogEntry, ...] = field(default_factory=tuple)
    categories: tuple[DomainCategory, ...] = field(default_factory=tuple)
    glossary: tuple[GlossaryTerm, ...] = field(default_factory=tuple)
    policies: tuple[OperationalPolicy, ...] = field(default_factory=tuple)
    severities: tuple[SeverityLevel, ...] = field(default_factory=tuple)
    meta: NarrowingMeta | None = None


def extract_signal_text(signal: Incident | CustomerCase | TechnicalIssue) -> SignalText:
    signal_type = signal.SIGNAL_TYPE

    if signal_type == "Incident":
        return _extract_incident_text(cast("Incident", signal))
    elif signal_type == "CustomerCase":
        return _extract_customer_case_text(cast("CustomerCase", signal))
    elif signal_type == "TechnicalIssue":
        return _extract_technical_issue_text(cast("TechnicalIssue", signal))
    else:
        raise ValueError(f"Unknown signal type: {signal_type}")


def _extract_incident_text(signal: Incident) -> SignalText:
    title = signal.title or ""
    description = signal.description or ""
    impact = signal.impact_description or ""
    root_cause = signal.root_cause_description or ""
    services = tuple(signal.affected_services or [])
    tags = signal.tags or []
    source_system = signal.source_system or ""

    text_parts = [
        title,
        description,
        impact,
        root_cause,
        " ".join(services),
        " ".join(tags),
    ]
    full_text = " ".join(part for part in text_parts if part).lower()

    return SignalText(
        title=title,
        description=description,
        services=services,
        source_system=source_system,
        full_text=full_text,
    )


def _extract_customer_case_text(signal: CustomerCase) -> SignalText:
    title = signal.title or ""
    description = signal.description or ""
    tags = signal.tags or []
    source_system = signal.source_system or ""

    text_parts = [title, description, " ".join(tags)]
    full_text = " ".join(part for part in text_parts if part).lower()

    return SignalText(
        title=title,
        description=description,
        services=(),
        source_system=source_system,
        full_text=full_text,
    )


def _extract_technical_issue_text(signal: TechnicalIssue) -> SignalText:
    title = signal.title or ""
    last_message = signal.last_message or ""
    service = signal.service or ""
    environment = signal.environment or ""
    provider = signal.provider or ""

    text_parts = [title, last_message, service, environment]
    full_text = " ".join(part for part in text_parts if part).lower()

    return SignalText(
        title=title,
        description=last_message,
        services=(service,) if service and service != "unknown" else (),
        source_system=provider,
        full_text=full_text,
    )


def match_systems(
    signal_text: SignalText,
    systems: list[SystemCatalogEntry],
) -> tuple[SystemCatalogEntry, ...]:
    candidates: list[MatchedEntity] = []
    seen_keys: set[str] = set()

    for service_name in signal_text.services:
        service_lower = service_name.lower()
        for system in systems:
            if system.key in seen_keys:
                continue
            if system.key.lower() == service_lower or system.label.lower() == service_lower:
                candidates.append(
                    MatchedEntity(
                        entity=system,
                        score=SCORE_EXPLICIT_SERVICE,
                        match_reason=f"explicit service: {service_name}",
                    )
                )
                seen_keys.add(system.key)
                break

    source_lower = signal_text.source_system.lower()
    if source_lower:
        for system in systems:
            if system.key in seen_keys:
                continue
            if system.key.lower() == source_lower:
                candidates.append(
                    MatchedEntity(
                        entity=system,
                        score=SCORE_SOURCE_SYSTEM,
                        match_reason=f"source system: {signal_text.source_system}",
                    )
                )
                seen_keys.add(system.key)
                break

    full_text = signal_text.full_text
    for system in systems:
        if system.key in seen_keys:
            continue

        key_lower = system.key.lower()
        label_lower = system.label.lower()

        if _word_in_text(key_lower, full_text):
            candidates.append(
                MatchedEntity(
                    entity=system,
                    score=SCORE_KEY_MATCH,
                    match_reason=f"key '{system.key}' in text",
                )
            )
            seen_keys.add(system.key)
            continue

        if label_lower in full_text:
            candidates.append(
                MatchedEntity(
                    entity=system,
                    score=SCORE_LABEL_MATCH,
                    match_reason=f"label '{system.label}' in text",
                )
            )
            seen_keys.add(system.key)
            continue

        if system.description:
            keywords = _extract_keywords(system.description)
            if any(kw in full_text for kw in keywords):
                candidates.append(
                    MatchedEntity(
                        entity=system,
                        score=SCORE_DESCRIPTION_KEYWORD,
                        match_reason="description keyword match",
                    )
                )
                seen_keys.add(system.key)

    type_priority = {"service": 0, "infra": 1, "external": 2, "component": 3}
    candidates.sort(
        key=lambda m: (
            -m.score,
            type_priority.get(cast("SystemCatalogEntry", m.entity).entry_type, 99),
        )
    )

    return tuple(cast("SystemCatalogEntry", m.entity) for m in candidates[:MAX_SYSTEMS])


def match_categories(
    signal_text: SignalText,
    categories: list[DomainCategory],
    selected_systems: tuple[SystemCatalogEntry, ...],
) -> tuple[DomainCategory, ...]:
    candidates: list[MatchedEntity] = []
    seen_keys: set[str] = set()

    has_infra = any(s.entry_type == "infra" for s in selected_systems)
    if has_infra:
        for category in categories:
            if category.key == "infrastructure":
                candidates.append(
                    MatchedEntity(
                        entity=category,
                        score=SCORE_INFRA_SYSTEM,
                        match_reason="infrastructure system present",
                    )
                )
                seen_keys.add(category.key)
                break

    for category in categories:
        if category.key in seen_keys:
            continue

        desc_lower = (category.description or "").lower()
        if not desc_lower:
            continue

        for system in selected_systems:
            if system.key.lower() in desc_lower or system.label.lower() in desc_lower:
                candidates.append(
                    MatchedEntity(
                        entity=category,
                        score=SCORE_SYSTEM_IN_DESC,
                        match_reason=f"system '{system.key}' in description",
                    )
                )
                seen_keys.add(category.key)
                break

    full_text = signal_text.full_text
    for category in categories:
        if category.key in seen_keys:
            continue

        desc_lower = (category.description or "").lower()
        if not desc_lower:
            continue

        keywords = _extract_keywords(category.description)
        matches = sum(1 for kw in keywords if kw in full_text)
        if matches >= 2:
            candidates.append(
                MatchedEntity(
                    entity=category,
                    score=SCORE_TEXT_IN_DESC + (matches * 5),
                    match_reason=f"{matches} keywords from description",
                )
            )
            seen_keys.add(category.key)

    candidates.sort(key=lambda m: -m.score)
    return tuple(cast("DomainCategory", m.entity) for m in candidates[:MAX_CATEGORIES])


def match_glossary(
    signal_text: SignalText,
    glossary: list[GlossaryTerm],
) -> tuple[GlossaryTerm, ...]:
    candidates: list[MatchedEntity] = []
    seen_terms: set[str] = set()
    full_text = signal_text.full_text

    for term in glossary:
        if term.term in seen_terms:
            continue

        if _term_matches(term.term, full_text):
            candidates.append(
                MatchedEntity(
                    entity=term,
                    score=SCORE_TERM_EXACT,
                    match_reason=f"term '{term.term}' matched",
                )
            )
            seen_terms.add(term.term)
            continue

        for alias in term.aliases or []:
            if _term_matches(alias, full_text):
                candidates.append(
                    MatchedEntity(
                        entity=term,
                        score=SCORE_ALIAS_MATCH,
                        match_reason=f"alias '{alias}' matched",
                    )
                )
                seen_terms.add(term.term)
                break

    candidates.sort(key=lambda m: -m.score)
    return tuple(cast("GlossaryTerm", m.entity) for m in candidates[:MAX_GLOSSARY])


def match_policies(
    signal_text: SignalText,
    policies: list[OperationalPolicy],
    selected_categories: tuple[DomainCategory, ...],
    selected_glossary: tuple[GlossaryTerm, ...],
) -> tuple[OperationalPolicy, ...]:
    candidates: list[MatchedEntity] = []
    seen_keys: set[str] = set()

    for policy in policies:
        if policy.key in seen_keys:
            continue

        policy_key_lower = policy.key.lower()
        for category in selected_categories:
            if category.key.lower() in policy_key_lower:
                candidates.append(
                    MatchedEntity(
                        entity=policy,
                        score=SCORE_CATEGORY_MATCH,
                        match_reason=f"category '{category.key}' in policy key",
                    )
                )
                seen_keys.add(policy.key)
                break

    for policy in policies:
        if policy.key in seen_keys:
            continue

        policy_key_lower = policy.key.lower()
        for term in selected_glossary:
            if term.term.lower() in policy_key_lower:
                candidates.append(
                    MatchedEntity(
                        entity=policy,
                        score=SCORE_GLOSSARY_MATCH,
                        match_reason=f"term '{term.term}' in policy key",
                    )
                )
                seen_keys.add(policy.key)
                break

    full_text = signal_text.full_text
    for policy in policies:
        if policy.key in seen_keys:
            continue

        statement_keywords = _extract_keywords(policy.statement, min_length=6)
        matches = sum(1 for kw in statement_keywords if kw in full_text)
        if matches >= 3:
            candidates.append(
                MatchedEntity(
                    entity=policy,
                    score=matches * 5,
                    match_reason=f"{matches} statement keywords matched",
                )
            )
            seen_keys.add(policy.key)

    candidates.sort(key=lambda m: -m.score)
    return tuple(cast("OperationalPolicy", m.entity) for m in candidates[:MAX_POLICIES])


def _extract_keywords(text: str, min_length: int = MIN_KEYWORD_LENGTH) -> list[str]:
    if not text:
        return []
    words = text.lower().split()
    return [w for w in words if len(w) >= min_length and w.isalpha()]


def _word_in_text(word: str, text: str) -> bool:
    pattern = rf"\b{re.escape(word)}\b"
    return bool(re.search(pattern, text, re.IGNORECASE))


def _term_matches(needle: str, haystack: str) -> bool:
    # Short terms (<=3 chars) require word boundaries to avoid false positives
    if len(needle) <= 3:
        pattern = rf"\b{re.escape(needle)}\b"
        return bool(re.search(pattern, haystack, re.IGNORECASE))
    return needle.lower() in haystack.lower()


class ContextNarrowingService:
    def narrow(
        self,
        signal: Incident | CustomerCase | TechnicalIssue,
        profile: DomainProfile,
    ) -> NarrowingResult:
        signal_text = extract_signal_text(signal)

        # Prefetch to prevent N+1 queries
        all_systems = list(profile.systems.all())
        all_categories = list(profile.categories.all())
        all_glossary = list(profile.glossary.all())
        all_policies = list(profile.operational_policies.all())
        all_severities = tuple(profile.severities.all().order_by("-rank"))

        selected_systems = match_systems(signal_text, all_systems)
        selected_categories = match_categories(signal_text, all_categories, selected_systems)
        selected_glossary = match_glossary(signal_text, all_glossary)
        selected_policies = match_policies(
            signal_text, all_policies, selected_categories, selected_glossary
        )

        meta = self._build_meta(
            signal=signal,
            signal_text=signal_text,
            total_systems=len(all_systems),
            total_categories=len(all_categories),
            total_glossary=len(all_glossary),
            total_policies=len(all_policies),
            selected_systems=len(selected_systems),
            selected_categories=len(selected_categories),
            selected_glossary=len(selected_glossary),
            selected_policies=len(selected_policies),
        )

        return NarrowingResult(
            systems=selected_systems,
            categories=selected_categories,
            glossary=selected_glossary,
            policies=selected_policies,
            severities=all_severities,
            meta=meta,
        )

    def _build_meta(
        self,
        signal: Incident | CustomerCase | TechnicalIssue,
        signal_text: SignalText,
        total_systems: int,
        total_categories: int,
        total_glossary: int,
        total_policies: int,
        selected_systems: int,
        selected_categories: int,
        selected_glossary: int,
        selected_policies: int,
    ) -> NarrowingMeta:
        signal_type = signal.SIGNAL_TYPE
        environment: str | None = None
        severity: str | None = None
        status: str | None = None

        if signal_type == "Incident":
            severity = getattr(signal, "severity", None)
            status = getattr(signal, "status", None)
        elif signal_type == "CustomerCase":
            severity = getattr(signal, "severity", None)
            status = getattr(signal, "status", None)
        elif signal_type == "TechnicalIssue":
            environment = getattr(signal, "environment", None)
            status = getattr(signal, "status", None)

        return NarrowingMeta(
            signal_type=signal_type,
            source_system=signal_text.source_system,
            environment=environment,
            severity=severity,
            status=status,
            total_systems=total_systems,
            total_categories=total_categories,
            total_glossary=total_glossary,
            total_policies=total_policies,
            selected_systems=selected_systems,
            selected_categories=selected_categories,
            selected_glossary=selected_glossary,
            selected_policies=selected_policies,
        )


def build_narrowed_context(result: NarrowingResult) -> str:
    sections: list[str] = []

    if result.categories:
        lines = ["## Relevant Categories"]
        for c in result.categories:
            desc = f": {c.description}" if c.description else ""
            lines.append(f"- **{c.label}**{desc}")
        sections.append("\n".join(lines))

    if result.severities:
        lines = ["## Severity Levels"]
        for sev in result.severities:
            desc = f": {sev.description}" if sev.description else ""
            lines.append(f"- **{sev.label}**{desc}")
        sections.append("\n".join(lines))

    if result.systems:
        lines = ["## Relevant Systems"]
        for sys in result.systems:
            desc = f": {sys.description}" if sys.description else ""
            lines.append(f"- **{sys.label}** ({sys.get_entry_type_display()}){desc}")
        sections.append("\n".join(lines))

    if result.glossary:
        lines = ["## Key Terminology"]
        for t in result.glossary:
            aliases = f" (also: {', '.join(t.aliases)})" if t.aliases else ""
            lines.append(f"- **{t.term}**{aliases}: {t.definition}")
        sections.append("\n".join(lines))

    if result.policies:
        lines = ["## Operational Context"]
        for p in result.policies:
            lines.append(f"- {p.statement}")
        sections.append("\n".join(lines))

    if not sections:
        return ""

    return "\n\n".join(sections) + "\n"
