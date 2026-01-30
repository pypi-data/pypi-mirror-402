import hashlib
from typing import Any

from django.db import models
from pgvector.django import VectorField

from nazara.shared.infrastructure.django.models import BaseModel


class TargetTypeChoices(models.TextChoices):
    INCIDENT = "Incident", "Incident"
    CUSTOMER_CASE = "CustomerCase", "Customer Case"
    TECHNICAL_ISSUE = "TechnicalIssue", "Technical Issue"


class EnrichmentTypeChoices(models.TextChoices):
    SUMMARY_V1 = "summary.v1", "Summary (v1)"
    EMBEDDING_V1 = "embedding.v1", "Embedding (v1)"


class EnrichmentStatusChoices(models.TextChoices):
    SUCCESS = "success", "Success"
    FAILED = "failed", "Failed"


class LLMProviderChoices(models.TextChoices):
    OPENAI = "openai", "OpenAI"
    ANTHROPIC = "anthropic", "Anthropic"


class LLMCapabilityChoices(models.TextChoices):
    SUMMARY = "summary", "Summary Generation"
    EMBEDDING = "embedding", "Embedding Generation"


class InputSourceChoices(models.TextChoices):
    RAW = "raw", "Raw Signal Data"
    DEPENDENT = "dependent", "Previous Step Output"


class DomainProfile(BaseModel):
    """
    Aggregate root for domain configuration.

    Represents how a company/environment interprets operational signals.
    Only one profile can be active at a time.
    """

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=False, db_index=True)

    class Meta:
        app_label = "nazara_intelligence"
        db_table = "nazara_domain_profile"
        verbose_name = "Domain Profile"
        verbose_name_plural = "Domain Profiles"
        ordering = ["-is_active", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["is_active"],
                condition=models.Q(is_active=True),
                name="unique_active_profile",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def activate(self) -> None:
        # Activate this profile, deactivating any other active profile.
        DomainProfile.objects.filter(is_active=True).update(is_active=False)
        self.is_active = True

    def deactivate(self) -> None:
        self.is_active = False

    def get_category_keys(self) -> list[str]:
        return list(self.categories.values_list("key", flat=True))

    def get_severity_keys(self) -> list[str]:
        return list(self.severities.values_list("key", flat=True))

    def is_valid_category(self, key: str) -> bool:
        return self.categories.filter(key=key).exists()

    def is_valid_severity(self, key: str) -> bool:
        return self.severities.filter(key=key).exists()


class DomainCategory(BaseModel):
    """
    Child entity defining classification buckets.

    Examples: payments, networking, authentication, infrastructure.
    Edited only via DomainProfile admin inline.
    """

    profile = models.ForeignKey(
        DomainProfile,
        on_delete=models.CASCADE,
        related_name="categories",
    )
    key = models.CharField(max_length=50)
    label = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        app_label = "nazara_intelligence"
        db_table = "nazara_domain_category"
        verbose_name = "Domain Category"
        verbose_name_plural = "Domain Categories"
        ordering = ["key"]
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "key"],
                name="unique_category_per_profile",
            ),
        ]

    def __str__(self) -> str:
        return self.label


class SeverityLevel(BaseModel):
    """
    Child entity defining semantic meaning and ordering of severity.

    Keys must align with existing enum values (low, medium, high, critical).
    Edited only via DomainProfile admin inline.
    """

    profile = models.ForeignKey(
        DomainProfile,
        on_delete=models.CASCADE,
        related_name="severities",
    )
    key = models.CharField(max_length=50)
    label = models.CharField(max_length=100)
    rank = models.PositiveIntegerField(help_text="Higher = more severe")
    description = models.TextField(blank=True)

    class Meta:
        app_label = "nazara_intelligence"
        db_table = "nazara_severity_level"
        verbose_name = "Severity Level"
        verbose_name_plural = "Severity Levels"
        ordering = ["rank"]
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "key"],
                name="unique_severity_per_profile",
            ),
            models.UniqueConstraint(
                fields=["profile", "rank"],
                name="unique_rank_per_profile",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.label} ({self.rank})"


class EnrichmentFlow(BaseModel):
    """
    Defines an enrichment pipeline configuration with filter-based routing.

    Multiple flows can exist per (profile, target_type) with different filters.
    Signals are routed to the highest-priority matching flow.

    Filter logic:
    - Empty filter = matches all values for that attribute
    - Non-empty filter = signal must have one of the listed values (OR)
    - Cross-filter = AND (must match all non-empty filters)
    """

    profile = models.ForeignKey(
        DomainProfile,
        on_delete=models.CASCADE,
        related_name="enrichment_flows",
    )
    target_type = models.CharField(
        max_length=50,
        choices=TargetTypeChoices.choices,
        help_text="Signal type this flow applies to",
    )
    name = models.CharField(
        max_length=100,
        help_text="Flow name (e.g., 'Default', 'Auth Critical', 'MCP High')",
    )
    priority = models.PositiveIntegerField(
        default=0,
        help_text="Higher priority flows are checked first. Use 0 for catch-all.",
    )
    enabled = models.BooleanField(
        default=True,
        help_text="Disabled flows are skipped during routing",
    )

    # Routing filters (empty = match all)
    category_filter = models.JSONField(
        default=list,
        blank=True,
        help_text="Match signals with these categories (empty = all)",
    )
    severity_filter = models.JSONField(
        default=list,
        blank=True,
        help_text="Match signals with these severities (empty = all)",
    )
    service_filter = models.JSONField(
        default=list,
        blank=True,
        help_text="Match signals from these services (empty = all)",
    )

    class Meta:
        app_label = "nazara_intelligence"
        db_table = "nazara_enrichment_flow"
        verbose_name = "Enrichment Flow"
        verbose_name_plural = "Enrichment Flows"
        ordering = ["profile", "target_type", "-priority"]
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "target_type", "name"],
                name="unique_flow_name_per_profile_target",
            ),
            models.UniqueConstraint(
                fields=["profile", "target_type", "priority"],
                name="unique_priority_per_profile_target",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.target_type} → {self.name}"

    def _format_filters(self) -> str:
        """Format active filters for display."""
        parts = []
        if self.category_filter:
            parts.append(f"cat={','.join(self.category_filter)}")
        if self.severity_filter:
            parts.append(f"sev={','.join(self.severity_filter)}")
        if self.service_filter:
            parts.append(f"svc={','.join(self.service_filter)}")
        return "; ".join(parts)

    def matches(
        self,
        category: str | None = None,
        severity: str | None = None,
        service: str | None = None,
    ) -> bool:
        """
        Check if a signal matches this flow's filters.

        Empty filter = matches all values for that attribute.
        All non-empty filters must match (AND logic).
        """
        if not self.enabled:
            return False
        if self.category_filter and category not in self.category_filter:
            return False
        if self.severity_filter and severity not in self.severity_filter:
            return False
        if self.service_filter and service not in self.service_filter:
            return False
        return True

    def _filters_overlap(self, other: "EnrichmentFlow") -> bool:
        """Check if this flow's filters could match the same signal as another flow."""

        # Empty filter matches everything, so overlaps with any other filter
        def could_overlap(filter1: list[str], filter2: list[str]) -> bool:
            if not filter1 or not filter2:
                return True  # Empty matches all
            return bool(set(filter1) & set(filter2))

        return (
            could_overlap(self.category_filter, other.category_filter)
            and could_overlap(self.severity_filter, other.severity_filter)
            and could_overlap(self.service_filter, other.service_filter)
        )

    def clean(self) -> None:
        import logging

        from django.core.exceptions import ValidationError

        logger = logging.getLogger(__name__)

        # Check for overlapping flows at same priority (would be caught by constraint,
        # but we provide a better error message)
        same_priority = EnrichmentFlow.objects.filter(
            profile=self.profile,
            target_type=self.target_type,
            priority=self.priority,
        ).exclude(pk=self.pk)

        if same_priority.exists():
            existing = same_priority.first()
            raise ValidationError(
                {
                    "priority": (
                        f"Priority {self.priority} is already used by flow "
                        f"'{existing.name if existing else 'unknown'}'. "
                        f"Each flow must have a unique priority."
                    )
                }
            )

        # Warn about potential filter overlaps with other flows
        other_flows = EnrichmentFlow.objects.filter(
            profile=self.profile,
            target_type=self.target_type,
            enabled=True,
        ).exclude(pk=self.pk)

        for other in other_flows:
            if self._filters_overlap(other):
                # Log warning but don't block - priority handles precedence
                logger.warning(
                    f"Flow '{self.name}' (priority={self.priority}) has overlapping "
                    f"filters with '{other.name}' (priority={other.priority}). "
                    f"Higher priority flow will take precedence."
                )

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def get_ordered_steps(self) -> list[str]:
        return list(self.flow_steps.order_by("order").values_list("enrichment_type", flat=True))


class EnrichmentFlowStep(BaseModel):
    """
    Individual step within an EnrichmentFlow.

    Defines the enrichment_type and its execution order within the flow.
    Displayed as inline in Django admin for easy configuration.
    """

    flow = models.ForeignKey(
        EnrichmentFlow,
        on_delete=models.CASCADE,
        related_name="flow_steps",
    )
    enrichment_type = models.CharField(
        max_length=50,
        choices=EnrichmentTypeChoices.choices,
        help_text="Enrichment to execute",
    )
    order = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Execution order (lower = earlier). Leave blank to auto-assign.",
    )
    input_source = models.CharField(
        max_length=20,
        choices=InputSourceChoices.choices,
        default=InputSourceChoices.RAW,
        help_text="Where this step gets its input: raw signal data or output from previous steps",
    )

    class Meta:
        app_label = "nazara_intelligence"
        db_table = "nazara_enrichment_flow_step"
        verbose_name = "Flow Step"
        verbose_name_plural = "Flow Steps"
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["flow", "enrichment_type"],
                name="unique_step_per_flow",
            ),
        ]

    def __str__(self) -> str:
        order = self.order if self.order is not None else "?"
        return f"{order}. {self.enrichment_type}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self._state.adding and self.order is None:
            max_order = (
                EnrichmentFlowStep.objects.filter(flow=self.flow)
                .aggregate(models.Max("order"))
                .get("order__max")
            )
            self.order = (max_order + 1) if max_order is not None else 0
        super().save(*args, **kwargs)


class SystemTypeChoices(models.TextChoices):
    SERVICE = "service", "Internal Service"
    INFRASTRUCTURE = "infra", "Shared Infrastructure"
    EXTERNAL = "external", "External Dependency"
    COMPONENT = "component", "Logical Component"


class SystemCatalogEntry(BaseModel):
    profile = models.ForeignKey(
        DomainProfile,
        on_delete=models.CASCADE,
        related_name="systems",
    )
    key = models.CharField(max_length=100)
    label = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    entry_type = models.CharField(
        max_length=50,
        choices=SystemTypeChoices.choices,
        default=SystemTypeChoices.SERVICE,
    )

    class Meta:
        app_label = "nazara_intelligence"
        db_table = "nazara_system_catalog_entry"
        verbose_name = "System Catalog Entry"
        verbose_name_plural = "System Catalog Entries"
        ordering = ["entry_type", "label"]
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "key"],
                name="unique_system_per_profile",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.label} ({self.get_entry_type_display()})"


class GlossaryTerm(BaseModel):
    profile = models.ForeignKey(
        DomainProfile,
        on_delete=models.CASCADE,
        related_name="glossary",
    )
    term = models.CharField(max_length=100)
    definition = models.TextField()
    aliases = models.JSONField(default=list, blank=True)

    class Meta:
        app_label = "nazara_intelligence"
        db_table = "nazara_glossary_term"
        verbose_name = "Glossary Term"
        verbose_name_plural = "Glossary Terms"
        ordering = ["term"]
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "term"],
                name="unique_term_per_profile",
            ),
        ]

    def __str__(self) -> str:
        return self.term


class OperationalPolicy(BaseModel):
    profile = models.ForeignKey(
        DomainProfile,
        on_delete=models.CASCADE,
        related_name="operational_policies",
    )
    key = models.CharField(max_length=100)
    statement = models.TextField()

    class Meta:
        app_label = "nazara_intelligence"
        db_table = "nazara_operational_policy"
        verbose_name = "Operational Policy"
        verbose_name_plural = "Operational Policies"
        ordering = ["key"]
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "key"],
                name="unique_operational_policy_per_profile",
            ),
        ]

    def __str__(self) -> str:
        return self.key


class LLMProviderConfig(BaseModel):
    """
    Aggregate root for LLM provider configuration.

    Defines available LLM models. The provider is derived from the model ID
    using the model_registry, ensuring a single source of truth.

    Secrets are resolved via SecretResolver, never stored in DB.

    Model selection is based on:
    1. enabled=True
    2. Has required capability
    3. Ordered by priority (lower number = higher priority)
    """

    name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Optional custom name (auto: provider/model)",
    )
    model = models.CharField(
        max_length=100,
        unique=True,
        help_text="Model identifier (e.g., gpt-4o-mini, claude-3-5-haiku-20241022)",
    )
    secret_ref = models.CharField(
        max_length=255,
        help_text="Reference to API key in secret store",
    )
    capabilities = models.JSONField(
        default=list,
        help_text='List of capabilities: ["summary", "embedding"]',
    )
    enabled = models.BooleanField(default=True, db_index=True)
    priority = models.PositiveIntegerField(
        default=0,
        db_index=True,
        help_text="Selection priority (lower number = higher priority)",
    )

    # Optional configuration
    base_url = models.URLField(
        blank=True,
        help_text="Custom API base URL (for self-hosted or proxy)",
    )
    timeout_seconds = models.PositiveIntegerField(
        default=30,
        help_text="Request timeout in seconds",
    )
    max_tokens = models.PositiveIntegerField(
        default=1024,
        help_text="Maximum tokens for generation",
    )

    class Meta:
        app_label = "nazara_intelligence"
        db_table = "nazara_llm_provider_config"
        verbose_name = "LLM Provider Config"
        verbose_name_plural = "LLM Provider Configs"
        ordering = ["priority", "model"]

    @property
    def provider(self) -> str:
        """Derive provider from model ID using model_registry."""
        from nazara.intelligence.domain.model_registry import get_provider_for_model

        return get_provider_for_model(self.model) or ""

    @property
    def display_name(self) -> str:
        if self.name:
            return self.name
        return f"{self.provider}/{self.model}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.name:
            self.name = f"{self.provider}/{self.model}"
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.display_name

    def clean(self) -> None:
        super().clean()
        from django.core.exceptions import ValidationError

        from nazara.intelligence.domain.model_registry import (
            get_provider_for_model,
            get_valid_models,
            model_supports_capability,
        )

        # Validate model exists in registry
        provider = get_provider_for_model(self.model)
        if not provider:
            all_models = []
            for prov in ["openai", "anthropic"]:
                all_models.extend(get_valid_models(prov))
            raise ValidationError(
                {
                    "model": f"'{self.model}' is not a valid model. "
                    f"Valid options: {', '.join(sorted(all_models))}"
                }
            )

        # Validate capabilities
        valid_capabilities = {c.value for c in LLMCapabilityChoices}
        for cap in self.capabilities or []:
            if cap not in valid_capabilities:
                raise ValidationError(
                    {
                        "capabilities": f"Invalid capability: '{cap}'. "
                        f"Valid options: {', '.join(sorted(valid_capabilities))}"
                    }
                )

        # Validate model supports selected capabilities
        for cap in self.capabilities or []:
            if not model_supports_capability(provider, self.model, cap):
                raise ValidationError(
                    {"capabilities": f"Model '{self.model}' does not support '{cap}' capability."}
                )

    def has_capability(self, capability: str) -> bool:
        return capability in self.capabilities

    def can_generate_summary(self) -> bool:
        return self.enabled and self.has_capability(LLMCapabilityChoices.SUMMARY)

    def can_generate_embedding(self) -> bool:
        return self.enabled and self.has_capability(LLMCapabilityChoices.EMBEDDING)


class EnrichmentRecord(BaseModel):
    """
    Stores enrichment data for signals.

    One record per (target_type, target_id, enrichment_type).
    Contains both metadata and the actual enrichment result.

    Used for:
    - Storing enrichment outputs (result, embedding)
    - Idempotency via input_hash comparison
    - Retry tracking via attempts count
    - Operational metadata (duration)
    """

    target_type = models.CharField(max_length=50, choices=TargetTypeChoices.choices)
    target_id = models.UUIDField(db_index=True)
    enrichment_type = models.CharField(max_length=50, choices=EnrichmentTypeChoices.choices)
    input_hash = models.CharField(
        max_length=64,
        db_index=True,
        help_text="SHA-256 hash of input content for idempotency",
    )
    status = models.CharField(
        max_length=20,
        choices=EnrichmentStatusChoices.choices,
    )
    error = models.TextField(blank=True, help_text="Error message if status=failed")
    attempts = models.PositiveIntegerField(
        default=0,
        help_text="Number of enrichment attempts",
    )

    # Operational metadata
    duration_ms = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Execution duration in milliseconds",
    )

    # Enrichment results
    result = models.JSONField(
        null=True,
        blank=True,
        help_text="Structured result for text enrichments (e.g., summary)",
    )
    embedding = VectorField(
        dimensions=1536,
        null=True,
        blank=True,
        help_text="Vector embedding for similarity search",
    )

    class Meta:
        app_label = "nazara_intelligence"
        db_table = "nazara_enrichment_record"
        verbose_name = "Enrichment Record"
        verbose_name_plural = "Enrichment Records"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["target_type", "target_id"]),
            models.Index(fields=["enrichment_type", "input_hash"]),
            models.Index(fields=["status", "created_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["target_type", "target_id", "enrichment_type"],
                name="one_record_per_signal_enrichment",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.target_type}:{self.target_id} - {self.enrichment_type} ({self.status})"

    @staticmethod
    def compute_input_hash(
        title: str,
        description: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        content = f"{title}|{description}|{context or {}}"
        return hashlib.sha256(content.encode()).hexdigest()
