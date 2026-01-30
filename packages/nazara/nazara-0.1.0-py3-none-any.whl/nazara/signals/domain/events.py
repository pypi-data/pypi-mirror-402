from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from nazara.shared.event_bus.contracts import DomainEvent
from nazara.shared.event_bus.registry import register_event

SignalType = Literal["Incident", "CustomerCase", "TechnicalIssue"]


@register_event
@dataclass(frozen=True, kw_only=True)
class SignalCreatedEvent(DomainEvent):
    signal_type: SignalType
    signal_id: UUID


@register_event
@dataclass(frozen=True, kw_only=True)
class SignalUpdatedEvent(DomainEvent):
    signal_type: SignalType
    signal_id: UUID
    changed_fields: tuple[str, ...]
