"""Shared kernel dependency injection container.

This module provides the SharedContainer which manages shared infrastructure
dependencies used across all bounded contexts, including secret resolution
and event bus.
"""

from dependency_injector import containers, providers

from nazara.shared.event_bus.provider import get_event_bus
from nazara.shared.infrastructure.secrets.resolvers import (
    DictSecretResolver,
    EnvSecretResolver,
    JSONSecretResolver,
)


class SharedContainer(containers.DeclarativeContainer):
    """
    Container for shared kernel dependencies.

    Provides secret resolution infrastructure that other contexts depend on.
    Uses a Selector pattern to choose the resolver implementation based on
    configuration.

    Configuration:
        secrets.resolver_type: "json" | "env" | "dict"
        secrets.file_path: Path to JSON secrets file (for json resolver)
        secrets.env_prefix: Prefix for env vars (for env resolver)
        secrets.dict_secrets: Dict of secrets (for dict resolver, testing)

    Example:
        container = SharedContainer()
        container.config.from_dict({
            "secrets": {
                "resolver_type": "json",
                "file_path": "/path/to/secrets.json",
            }
        })
        resolver = container.secret_resolver()
    """

    config = providers.Configuration()

    # Secret resolver implementations (private, selected via Selector)
    _json_secret_resolver = providers.Singleton(
        JSONSecretResolver,
        secrets_file=config.secrets.file_path,
    )

    _env_secret_resolver = providers.Singleton(
        EnvSecretResolver,
        prefix=config.secrets.env_prefix,
    )

    _dict_secret_resolver = providers.Singleton(
        DictSecretResolver,
        secrets=config.secrets.dict_secrets,
    )

    # Public selector for secret resolver based on config
    secret_resolver = providers.Selector(
        config.secrets.resolver_type,
        json=_json_secret_resolver,
        env=_env_secret_resolver,
        dict=_dict_secret_resolver,
    )

    # Event bus provider (Singleton - stateless)
    # Uses get_event_bus() factory which respects Django settings
    event_bus = providers.Singleton(get_event_bus)
