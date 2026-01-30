# Re-export all models and choices from domain layer
from nazara.ingestion.domain.models import (
    AuthTypeChoices,
    IngestionModeChoices,
    IngestorConfig,
    IngestorRun,
    IngestorTypeChoices,
    RunStatusChoices,
)

# Backwards compatibility aliases (old names with "Model" suffix)
IngestorConfigModel = IngestorConfig
IngestorRunModel = IngestorRun

__all__ = [
    # Domain models (new names)
    "IngestorConfig",
    "IngestorRun",
    # Choice enumerations
    "IngestorTypeChoices",
    "AuthTypeChoices",
    "IngestionModeChoices",
    "RunStatusChoices",
    # Backwards compatibility aliases
    "IngestorConfigModel",
    "IngestorRunModel",
]
