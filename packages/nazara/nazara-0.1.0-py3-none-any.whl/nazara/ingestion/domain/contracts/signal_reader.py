from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, ClassVar, Generic, TypeVar

from nazara.shared.domain.dtos.signal_data import (
    CustomerCaseData,
    IncidentData,
    TechnicalEventData,
)
from nazara.shared.domain.value_objects.types import AuthType, IngestionMode, OutputType

SignalData = TechnicalEventData | CustomerCaseData | IncidentData
T = TypeVar("T", bound=SignalData)


class SignalReader(ABC, Generic[T]):
    """
    Port for reading signals from external sources.

    This is the inbound port that external adapters implement
    to bring data into Nazara from various sources.

    Type Parameter:
        T: The output DTO type (e.g., TechnicalEventData, CustomerCaseData, IncidentData)

    Class-level metadata (must be defined by subclasses):
        ingestor_type: Unique identifier for this reader type
        output_type: The entity type this reader produces
        display_name: Human-readable name for UI display
        description: Brief description of what this reader does
        supported_modes: List of supported ingestion modes
        supported_auth_types: List of supported authentication types
        filter_schema: JSON Schema for the filters configuration
        requires_package: Optional package dependency for this reader
    """

    # Identity metadata (MUST be overridden by subclasses)
    ingestor_type: ClassVar[str]
    output_type: ClassVar[OutputType]

    # Display metadata (MUST be overridden by subclasses)
    display_name: ClassVar[str]
    description: ClassVar[str]

    # Capability metadata (MUST be overridden by subclasses)
    supported_modes: ClassVar[list[IngestionMode]]
    supported_auth_types: ClassVar[list[AuthType]]

    # Configuration metadata (MUST be overridden by subclasses)
    filter_schema: ClassVar[dict[str, Any]]

    # Optional metadata
    requires_package: ClassVar[str | None] = None

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        """
        Get reader metadata for API/UI consumption.

        Returns:
            Dictionary with all reader metadata
        """
        return {
            "ingestor_type": cls.ingestor_type,
            "output_type": cls.output_type.value,
            "display_name": cls.display_name,
            "description": cls.description,
            "supported_modes": [m.value for m in cls.supported_modes],
            "supported_auth_types": [a.value for a in cls.supported_auth_types],
            "filter_schema": cls.filter_schema,
            "requires_package": cls.requires_package,
        }

    @abstractmethod
    def get_source_system(self) -> str:
        """
        Get the name of the source system.

        Returns:
            Source system identifier (e.g., "slack", "sentry")
        """
        ...

    @abstractmethod
    def parse_payload(self, raw_payload: dict[str, Any]) -> T:
        """
        Parse a raw webhook/API payload into a typed DTO.

        Args:
            raw_payload: The raw payload from the source

        Returns:
            Typed DTO ready for ingestion service
        """
        ...

    @abstractmethod
    def validate_payload(self, payload: dict[str, Any]) -> bool:
        """
        Validate that a payload has required fields.

        Args:
            payload: The payload to validate

        Returns:
            True if valid, False otherwise
        """
        ...

    def fetch_updates(
        self,
        credentials: str,
        filters: dict[str, Any],
        cursor: str | None,
        since: datetime | None,
    ) -> tuple[list[T], str | None]:
        """
        Fetch updates from the external API (polling mode).

        This method is optional - only readers that support polling
        need to implement it. Default raises NotImplementedError.

        Args:
            credentials: Resolved secret/API key
            filters: Source-specific filter configuration
            cursor: Current cursor/watermark position
            since: Baseline datetime for initial fetch

        Returns:
            Tuple of (list of typed DTOs, new cursor value)

        Raises:
            NotImplementedError: If polling is not supported
        """
        raise NotImplementedError(
            f"{self.get_source_system()} reader does not support polling mode"
        )
