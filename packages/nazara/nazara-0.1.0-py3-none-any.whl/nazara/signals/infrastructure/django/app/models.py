# Re-export all models and choices from domain layer
from nazara.signals.domain.models import (
    CustomerCase,
    EventTypeChoices,
    Incident,
    IssueStatusChoices,
    SeverityChoices,
    StatusChoices,
    TechnicalEvent,
    TechnicalIssue,
)

# Backwards compatibility aliases (old names with "Model" suffix)
IncidentModel = Incident
CustomerCaseModel = CustomerCase
TechnicalIssueModel = TechnicalIssue
TechnicalEventModel = TechnicalEvent

__all__ = [
    # Domain models (new names)
    "Incident",
    "CustomerCase",
    "TechnicalIssue",
    "TechnicalEvent",
    # Choice enumerations
    "SeverityChoices",
    "StatusChoices",
    "EventTypeChoices",
    "IssueStatusChoices",
    # Backwards compatibility aliases
    "IncidentModel",
    "CustomerCaseModel",
    "TechnicalIssueModel",
    "TechnicalEventModel",
]
