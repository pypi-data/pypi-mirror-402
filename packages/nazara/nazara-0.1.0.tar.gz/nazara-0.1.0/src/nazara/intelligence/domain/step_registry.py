from collections.abc import Callable

from nazara.intelligence.domain.contracts.step import EnrichmentStep

STEP_REGISTRY: dict[str, type[EnrichmentStep]] = {}


def register_step(key: str) -> Callable[[type[EnrichmentStep]], type[EnrichmentStep]]:
    """
    Decorator to register a step class in the registry.

    Usage:
        @register_step("summary")
        class GenerateSummary(EnrichmentStep):
            ...
    """

    def decorator(cls: type[EnrichmentStep]) -> type[EnrichmentStep]:
        STEP_REGISTRY[key] = cls
        return cls

    return decorator


def get_step_class(key: str) -> type[EnrichmentStep] | None:
    """Get step class by base key (e.g., 'summary' not 'summary.v1')."""
    return STEP_REGISTRY.get(key)


def list_step_keys() -> list[str]:
    """List all registered step keys."""
    return list(STEP_REGISTRY.keys())


def clear_registry() -> None:
    """Clear registry (for testing)."""
    STEP_REGISTRY.clear()
