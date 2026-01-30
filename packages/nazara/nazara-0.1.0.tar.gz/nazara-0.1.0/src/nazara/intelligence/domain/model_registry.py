"""
LLM Model Registry - Single source of truth for provider models.

This module defines all supported LLM models, their capabilities, and
metadata. All other modules should import from here to avoid duplication.

Usage:
    from nazara.intelligence.domain.model_registry import (
        get_valid_models,
        get_default_model,
        get_embedding_dimension,
        get_model_choices,
    )

    # Get valid models for a provider
    models = get_valid_models("openai")  # ["gpt-4o", "gpt-4o-mini", ...]

    # Get default model for capability
    model = get_default_model("openai", "summary")  # "gpt-4o-mini"

    # Get embedding dimension
    dim = get_embedding_dimension("openai", "text-embedding-3-small")  # 1536
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class ModelSpec:
    """
    Specification for an LLM model.

    Attributes:
        id: Model identifier (e.g., "gpt-4o-mini")
        label: Human-readable label (e.g., "GPT-4o Mini")
        capabilities: Set of capabilities ("summary", "embedding")
        embedding_dim: Embedding dimension (only for embedding models)
        is_default: Whether this is the default for its capability
    """

    id: str
    label: str
    capabilities: frozenset[str]
    embedding_dim: int | None = None
    is_default: bool = False


OPENAI_MODELS: dict[str, ModelSpec] = {
    # Chat/Summary models
    "gpt-4o": ModelSpec(
        id="gpt-4o",
        label="GPT-4o",
        capabilities=frozenset(["summary"]),
    ),
    "gpt-4o-mini": ModelSpec(
        id="gpt-4o-mini",
        label="GPT-4o Mini",
        capabilities=frozenset(["summary"]),
        is_default=True,
    ),
    "gpt-4-turbo": ModelSpec(
        id="gpt-4-turbo",
        label="GPT-4 Turbo",
        capabilities=frozenset(["summary"]),
    ),
    # Embedding models
    "text-embedding-3-small": ModelSpec(
        id="text-embedding-3-small",
        label="Embedding 3 Small",
        capabilities=frozenset(["embedding"]),
        embedding_dim=1536,
        is_default=True,
    ),
    "text-embedding-3-large": ModelSpec(
        id="text-embedding-3-large",
        label="Embedding 3 Large",
        capabilities=frozenset(["embedding"]),
        embedding_dim=3072,
    ),
    "text-embedding-ada-002": ModelSpec(
        id="text-embedding-ada-002",
        label="Embedding Ada 002 (Legacy)",
        capabilities=frozenset(["embedding"]),
        embedding_dim=1536,
    ),
}

ANTHROPIC_MODELS: dict[str, ModelSpec] = {
    "claude-3-5-sonnet-20241022": ModelSpec(
        id="claude-3-5-sonnet-20241022",
        label="Claude 3.5 Sonnet",
        capabilities=frozenset(["summary"]),
    ),
    "claude-3-5-haiku-20241022": ModelSpec(
        id="claude-3-5-haiku-20241022",
        label="Claude 3.5 Haiku",
        capabilities=frozenset(["summary"]),
        is_default=True,
    ),
    "claude-3-opus-20240229": ModelSpec(
        id="claude-3-opus-20240229",
        label="Claude 3 Opus",
        capabilities=frozenset(["summary"]),
    ),
    "claude-3-sonnet-20240229": ModelSpec(
        id="claude-3-sonnet-20240229",
        label="Claude 3 Sonnet",
        capabilities=frozenset(["summary"]),
    ),
    "claude-3-haiku-20240307": ModelSpec(
        id="claude-3-haiku-20240307",
        label="Claude 3 Haiku",
        capabilities=frozenset(["summary"]),
    ),
}

PROVIDER_MODELS: dict[str, dict[str, ModelSpec]] = {
    "openai": OPENAI_MODELS,
    "anthropic": ANTHROPIC_MODELS,
}


def get_valid_models(provider: str) -> list[str]:
    """
    Get list of valid model IDs for a provider.

    Args:
        provider: Provider key (e.g., "openai", "anthropic")

    Returns:
        List of valid model IDs
    """
    return list(PROVIDER_MODELS.get(provider, {}).keys())


def get_model_spec(provider: str, model: str) -> ModelSpec | None:
    """
    Get full model specification.

    Args:
        provider: Provider key
        model: Model ID

    Returns:
        ModelSpec if found, None otherwise
    """
    return PROVIDER_MODELS.get(provider, {}).get(model)


def is_valid_model(provider: str, model: str) -> bool:
    """
    Check if a model is valid for a provider.

    Args:
        provider: Provider key
        model: Model ID

    Returns:
        True if valid, False otherwise
    """
    return model in PROVIDER_MODELS.get(provider, {})


def get_default_model(provider: str, capability: str) -> str | None:
    """
    Get default model for a provider and capability.

    Args:
        provider: Provider key
        capability: Capability ("summary" or "embedding")

    Returns:
        Default model ID, or None if not found
    """
    models = PROVIDER_MODELS.get(provider, {})
    # First, look for explicit default
    for model_id, spec in models.items():
        if capability in spec.capabilities and spec.is_default:
            return model_id
    # Fall back to first model with capability
    for model_id, spec in models.items():
        if capability in spec.capabilities:
            return model_id
    return None


def get_embedding_dimension(provider: str, model: str) -> int | None:
    """
    Get embedding dimension for a model.

    Args:
        provider: Provider key
        model: Model ID

    Returns:
        Embedding dimension, or None if not an embedding model
    """
    spec = get_model_spec(provider, model)
    return spec.embedding_dim if spec else None


def get_model_choices(provider: str | None = None) -> list[tuple[str, str]]:
    """
    Get model choices for Django form/admin.

    Args:
        provider: Optional provider to filter by. If None, returns all models
                  grouped by provider.

    Returns:
        List of (value, label) tuples for form choices
    """
    if provider:
        models = PROVIDER_MODELS.get(provider, {})
        return [(model_id, spec.label) for model_id, spec in models.items()]

    # Return all models with provider prefix in label
    choices = []
    for prov, models in PROVIDER_MODELS.items():
        for model_id, spec in models.items():
            choices.append((model_id, f"{prov.title()}: {spec.label}"))
    return choices


def get_all_model_choices_grouped() -> list[tuple[str, list[tuple[str, str]]]]:
    """
    Get model choices grouped by provider for Django optgroup.

    Returns:
        List of (provider_label, [(model_id, model_label), ...]) tuples
    """
    grouped = []
    for provider, models in PROVIDER_MODELS.items():
        provider_label = provider.title()
        model_choices = [(model_id, spec.label) for model_id, spec in models.items()]
        grouped.append((provider_label, model_choices))
    return grouped


def get_provider_for_model(model: str) -> str | None:
    """
    Get the provider for a given model ID.

    This is the inverse lookup of PROVIDER_MODELS - given a model ID,
    find which provider it belongs to.

    Args:
        model: Model ID (e.g., "gpt-4o-mini", "claude-3-5-haiku-20241022")

    Returns:
        Provider key (e.g., "openai", "anthropic") or None if not found
    """
    for provider, models in PROVIDER_MODELS.items():
        if model in models:
            return provider
    return None


def model_supports_capability(provider: str, model: str, capability: str) -> bool:
    """
    Check if a model supports a specific capability.

    Args:
        provider: Provider key
        model: Model ID
        capability: Capability to check

    Returns:
        True if model supports capability, False otherwise
    """
    spec = get_model_spec(provider, model)
    if spec is None:
        return False
    return capability in spec.capabilities
