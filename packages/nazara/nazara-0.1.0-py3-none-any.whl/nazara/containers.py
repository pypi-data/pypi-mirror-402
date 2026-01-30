from __future__ import annotations

import logging
from typing import Any

from dependency_injector import containers, providers

from nazara.ingestion.infrastructure.containers import IngestionContainer
from nazara.intelligence.infrastructure.containers import IntelligenceContainer
from nazara.shared.infrastructure.containers import SharedContainer
from nazara.signals.infrastructure.containers import SignalsContainer

logger = logging.getLogger(__name__)


class ApplicationContainer(containers.DeclarativeContainer):
    """
    Root application container.

    Composes all bounded context containers.

    Container Hierarchy:
        ApplicationContainer
        ├── shared (SharedContainer) - Secret resolvers
        ├── signals (SignalsContainer) - Repositories and services
        ├── intelligence (IntelligenceContainer) - Enrichment use cases
        └── ingestion (IngestionContainer) - Repositories and services
    """

    config = providers.Configuration()

    shared = providers.Container(SharedContainer)
    signals = providers.Container(
        SignalsContainer,
        shared=shared,
    )
    intelligence = providers.Container(
        IntelligenceContainer,
        shared=shared,
    )
    ingestion = providers.Container(
        IngestionContainer,
        shared=shared,
        signals=signals,
    )


_container: ApplicationContainer | None = None


def get_container() -> ApplicationContainer:
    """
    Get the global application container instance.

    This should be called from entry points (tasks, views, commands)
    to access dependencies.

    Returns:
        The initialized ApplicationContainer

    Raises:
        RuntimeError: If container not initialized (Django not ready)

    Example:
        from nazara.containers import get_container

        def my_task():
            container = get_container()
            repo = container.signals.issue_repository()
            issues = repo.get_by_provider("sentry")
    """
    if _container is None:
        raise RuntimeError(
            "DI container not initialized. Ensure Django apps are loaded. "
            "Check that NazaraIngestionConfig.ready() has been called."
        )
    return _container


def init_container(config: dict[str, Any] | None = None) -> ApplicationContainer:
    """
    Initialize the global application container.

    Called by Django AppConfig.ready() to set up DI. Should only be
    called once during application startup.

    Args:
        config: Optional configuration dict to override defaults

    Returns:
        The initialized container instance

    Example:
        # In apps.py:
        class NazaraIngestionConfig(AppConfig):
            def ready(self):
                from nazara.containers import init_container
                init_container()
    """
    global _container

    if _container is not None:
        # Already initialized, return existing
        return _container

    container = ApplicationContainer()

    # Load configuration from Django settings
    try:
        from django.conf import settings

        # Secret resolver configuration
        resolver_type = getattr(settings, "NAZARA_SECRET_RESOLVER_TYPE", "json")
        secrets_file = getattr(settings, "NAZARA_SECRETS_FILE", None)
        env_prefix = getattr(settings, "NAZARA_SECRET_ENV_PREFIX", "NAZARA_")

        container.shared.config.from_dict(
            {
                "secrets": {
                    "resolver_type": resolver_type,
                    "file_path": secrets_file,
                    "env_prefix": env_prefix,
                    "dict_secrets": {},  # For testing only
                }
            }
        )

        # Check for legacy setting and provide backward compatibility
        legacy_resolver = getattr(settings, "NAZARA_SECRET_RESOLVER", None)
        if legacy_resolver is not None:
            import warnings

            from dependency_injector import providers as di_providers

            warnings.warn(
                "NAZARA_SECRET_RESOLVER is deprecated. Use NAZARA_SECRET_RESOLVER_TYPE instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            # Override with legacy resolver for backward compatibility
            container.shared.secret_resolver.override(di_providers.Object(legacy_resolver))

    except ImportError:
        # Django not available, use defaults
        container.shared.config.from_dict(
            {
                "secrets": {
                    "resolver_type": "dict",
                    "file_path": None,
                    "env_prefix": "",
                    "dict_secrets": {},
                }
            }
        )

    # Apply any additional config overrides
    if config:
        container.config.from_dict(config)

    _container = container
    logger.info("Nazara DI container initialized")

    return container


def reset_container() -> None:
    """
    Reset the global container (for testing purposes).

    This clears the global container instance, allowing a fresh
    container to be initialized.
    """
    global _container
    _container = None
