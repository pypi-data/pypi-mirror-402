from dataclasses import dataclass
from uuid import UUID

from nazara.shared.event_bus.contracts import DomainEvent
from nazara.shared.event_bus.registry import register_event


@register_event
@dataclass(frozen=True, kw_only=True)
class DomainProfileUpdatedEvent(DomainEvent):
    """
    Emitted when a DomainProfile's child entities are modified.

    Used to trigger reconciliation of EnrichmentFlow filters
    against the profile's current categories, severities, and services.
    """

    profile_id: UUID
