from abc import abstractmethod
from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

from nazara.ingestion.domain.contracts.signal_reader import SignalReader

# Common mappings shared across readers
SEVERITY_MAP: dict[str, str] = {
    "critical": "critical",
    "sev0": "critical",
    "p0": "critical",
    "high": "high",
    "major": "high",
    "sev1": "high",
    "p1": "high",
    "medium": "medium",
    "minor": "medium",
    "sev2": "medium",
    "p2": "medium",
    "low": "low",
    "cosmetic": "low",
    "sev3": "low",
    "p3": "low",
    "info": "info",
}

STATUS_MAP: dict[str, str] = {
    "open": "open",
    "triage": "open",
    "active": "investigating",
    "investigating": "investigating",
    "identified": "identified",
    "monitoring": "monitoring",
    "paused": "monitoring",
    "snoozed": "monitoring",
    "resolved": "resolved",
    "closed": "resolved",  # Most sources use "closed" to mean "resolved"
    "declined": "closed",
    "merged": "closed",
    "canceled": "closed",
}

# TypeVar for the output data type
T = TypeVar("T")


class BaseSignalReader(SignalReader[T], Generic[T]):
    """
    Base implementation for signal readers.

    Provides common functionality for all source system adapters.

    Type Parameter:
        T: The output DTO type (e.g., TechnicalEventData, CustomerCaseData, IncidentData)
    """

    @abstractmethod
    def get_source_system(self) -> str: ...

    def validate_payload(self, payload: dict[str, Any]) -> bool:
        """
        Validate that a payload has required fields.

        Default implementation checks for non-empty dict.
        Subclasses should override for specific validation.
        """
        return bool(payload) and isinstance(payload, dict)

    @abstractmethod
    def parse_payload(self, raw_payload: dict[str, Any]) -> T: ...

    def fetch_updates(
        self,
        credentials: str,
        filters: dict[str, Any],
        cursor: str | None,
        since: datetime | None,
    ) -> tuple[list[T], str | None]:
        """
        Fetch updates from the source system (polling mode).

        Default implementation raises NotImplementedError.
        Subclasses should override if they support polling.
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not support polling mode")

    def _sanitize_string(self, value: str | None) -> str | None:
        """
        Remove NUL (0x00) characters from strings.

        PostgreSQL text fields cannot contain NUL characters,
        so we strip them from external data.
        """
        if value is None:
            return None
        if isinstance(value, str):
            return value.replace("\x00", "")
        return value

    def _sanitize_data(self, data: Any) -> Any:
        """
        Recursively sanitize data by removing NUL characters from strings.

        Handles nested dicts, lists, and string values.
        """
        if isinstance(data, str):
            return self._sanitize_string(data)
        elif isinstance(data, dict):
            return {k: self._sanitize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
        else:
            return data

    def _safe_get(
        self,
        data: dict[str, Any],
        *keys: str,
        default: Any = None,
    ) -> Any:
        result = data
        for key in keys:
            if isinstance(result, dict):
                result = result.get(key, default)
            else:
                return default
        return result if result is not None else default

    def _parse_timestamp(self, value: Any) -> datetime | None:
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, (int, float)):
            # Handle nanoseconds (Datadog) vs seconds
            if value > 1e12:
                value = value / 1e9
            return datetime.fromtimestamp(value, tz=UTC)
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                try:
                    return datetime.fromtimestamp(float(value), tz=UTC)
                except ValueError:
                    pass
        return None

    def _map_severity(self, value: str | None, default: str = "medium") -> str:
        if not value:
            return default
        return SEVERITY_MAP.get(value.lower(), default)

    def _map_status(self, value: str | None, default: str = "open") -> str:
        if not value:
            return default
        return STATUS_MAP.get(value.lower(), default)
