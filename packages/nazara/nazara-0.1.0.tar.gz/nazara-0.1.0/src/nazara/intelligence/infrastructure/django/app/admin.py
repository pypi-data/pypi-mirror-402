from __future__ import annotations

from typing import Any

from django import forms
from django.contrib import admin, messages
from django.db import models
from django.http import HttpRequest, HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django_select2.forms import Select2MultipleWidget

from nazara.intelligence.domain.model_registry import get_all_model_choices_grouped
from nazara.intelligence.domain.models import LLMCapabilityChoices
from nazara.intelligence.infrastructure.django.app.models import (
    DomainCategory,
    DomainProfile,
    EnrichmentFlow,
    EnrichmentFlowStep,
    EnrichmentRecord,
    EnrichmentStatusChoices,
    GlossaryTerm,
    LLMProviderConfig,
    OperationalPolicy,
    SeverityLevel,
    SystemCatalogEntry,
)


class CompactInlineMixin:
    formfield_overrides = {
        models.TextField: {"widget": forms.Textarea(attrs={"rows": 2, "cols": 40})},
        models.JSONField: {"widget": forms.Textarea(attrs={"rows": 2, "cols": 30})},
    }


class DomainCategoryInline(CompactInlineMixin, admin.TabularInline):  # type: ignore[type-arg, misc]
    model = DomainCategory
    extra = 1
    fields = ["key", "label", "description"]
    classes: list[str] = []
    verbose_name = "Category"
    verbose_name_plural = "Business Categories"


class SeverityLevelInline(CompactInlineMixin, admin.TabularInline):  # type: ignore[type-arg, misc]
    model = SeverityLevel
    extra = 0
    fields = ["key", "label", "rank", "description"]
    ordering = ["rank"]
    classes: list[str] = []
    verbose_name = "Severity"
    verbose_name_plural = "Severity Levels"


class SystemCatalogEntryInline(CompactInlineMixin, admin.TabularInline):  # type: ignore[type-arg, misc]
    model = SystemCatalogEntry
    extra = 1
    fields = ["key", "label", "entry_type", "description"]
    ordering = ["entry_type", "label"]
    classes: list[str] = []
    verbose_name = "System"
    verbose_name_plural = "System Catalog"


class GlossaryTermInlineForm(forms.ModelForm):  # type: ignore[type-arg]
    """Form that displays aliases as comma-separated text instead of raw JSON."""

    aliases = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Separate with commas"}),
        help_text="Enter aliases separated by commas",
    )

    class Meta:
        model = GlossaryTerm
        fields = ["term", "definition", "aliases"]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Convert list to comma-separated string for display
        if self.instance.pk and self.instance.aliases:
            self.initial["aliases"] = ", ".join(self.instance.aliases)

    def clean_aliases(self) -> list[str]:
        """Convert comma-separated string back to list."""
        value = self.cleaned_data.get("aliases", "")
        if not value or not value.strip():
            return []
        # Split by comma, strip whitespace, filter empty strings
        return [alias.strip() for alias in value.split(",") if alias.strip()]


class GlossaryTermInline(CompactInlineMixin, admin.TabularInline):  # type: ignore[type-arg, misc]
    model = GlossaryTerm
    form = GlossaryTermInlineForm
    extra = 1
    fields = ["term", "definition", "aliases"]
    ordering = ["term"]
    classes: list[str] = []
    verbose_name = "Term"
    verbose_name_plural = "Glossary"


class OperationalPolicyInline(CompactInlineMixin, admin.TabularInline):  # type: ignore[type-arg, misc]
    model = OperationalPolicy
    extra = 1
    fields = ["key", "statement"]
    ordering = ["key"]
    classes: list[str] = []
    verbose_name = "Policy"
    verbose_name_plural = "Operational Policies"


@admin.register(DomainProfile)
class DomainProfileAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    ordering = ["-created_at"]
    list_display = [
        "name",
        "is_active_badge",
        "activate_link",
        "category_count",
        "flow_count",
        "updated_at",
    ]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "created_at", "updated_at", "version"]

    inlines = [
        DomainCategoryInline,
        SeverityLevelInline,
        SystemCatalogEntryInline,
        GlossaryTermInline,
        OperationalPolicyInline,
    ]

    fieldsets = [
        (
            "Profile Information",
            {
                "fields": ["id", "name", "description", "is_active"],
            },
        ),
        (
            "System",
            {
                "fields": ["created_at", "updated_at", "version"],
                "classes": ["collapse"],
            },
        ),
    ]

    @admin.display(description="Status")
    def is_active_badge(self, obj: DomainProfile) -> str:
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 2px 8px; '
                'border-radius: 4px; font-size: 11px;">ACTIVE</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 2px 8px; '
            'border-radius: 4px; font-size: 11px;">INACTIVE</span>'
        )

    @admin.display(description="Categories")
    def category_count(self, obj: DomainProfile) -> int:
        return obj.categories.count()

    @admin.display(description="Flows")
    def flow_count(self, obj: DomainProfile) -> int:
        return obj.enrichment_flows.count()

    @admin.display(description="Action")
    def activate_link(self, obj: DomainProfile) -> str:
        if obj.is_active:
            return "—"
        url = reverse("admin:nazara_intelligence_domainprofile_activate", args=[obj.pk])
        return format_html('<a href="{}">Activate</a>', url)

    def get_urls(self) -> list[Any]:
        from django.urls import path

        urls = super().get_urls()
        custom_urls = [
            path(
                "<uuid:pk>/activate/",
                self.admin_site.admin_view(self.activate_view),
                name="nazara_intelligence_domainprofile_activate",
            ),
        ]
        return custom_urls + urls

    def activate_view(self, request: HttpRequest, pk: Any) -> HttpResponseRedirect:
        profile = self.get_object(request, pk)
        if profile is None:
            self.message_user(request, "Profile not found.", messages.ERROR)
        else:
            profile.activate()
            profile.save()
            self.message_user(request, f"Activated profile: {profile.name}", messages.SUCCESS)
        return HttpResponseRedirect(reverse("admin:nazara_intelligence_domainprofile_changelist"))

    def save_related(self, request: HttpRequest, form: Any, formsets: Any, change: bool) -> None:
        """
        After saving inlines (categories, severities, services), emit event
        to reconcile EnrichmentFlow filters.
        """
        super().save_related(request, form, formsets, change)

        # Emit event to trigger filter reconciliation (async via Celery in production)
        from nazara.intelligence.domain.events import DomainProfileUpdatedEvent
        from nazara.shared.event_bus.provider import get_event_bus

        event = DomainProfileUpdatedEvent(profile_id=form.instance.id)
        get_event_bus().publish(event)

        self.message_user(
            request,
            "EnrichmentFlow filter reconciliation triggered. "
            "Any orphaned filter values will be automatically removed.",
            messages.INFO,
        )


class LLMProviderConfigForm(forms.ModelForm):  # type: ignore[type-arg]
    capabilities = forms.MultipleChoiceField(
        choices=LLMCapabilityChoices.choices,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select the capabilities this provider supports.",
    )

    model = forms.ChoiceField(
        choices=[],  # Populated dynamically in __init__
        help_text="Select the model for this provider.",
    )

    class Meta:
        model = LLMProviderConfig
        fields = [
            "name",
            "model",
            "secret_ref",
            "capabilities",
            "enabled",
            "priority",
            "base_url",
            "timeout_seconds",
            "max_tokens",
        ]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Pre-select existing capabilities when editing
        if self.instance.pk and self.instance.capabilities:
            self.initial["capabilities"] = self.instance.capabilities

        # Set model choices (grouped by provider)
        self.fields["model"].choices = get_all_model_choices_grouped()  # type: ignore[attr-defined]

        # If editing, ensure current model is in choices even if not in registry
        if self.instance.pk and self.instance.model:
            current_model = self.instance.model
            all_models = [m for _, models in get_all_model_choices_grouped() for m, _ in models]
            if current_model not in all_models:
                # Add current model to allow editing legacy configs
                self.fields["model"].choices = [  # type: ignore[attr-defined]
                    ("Current", [(current_model, f"{current_model} (legacy)")])
                ] + list(get_all_model_choices_grouped())

    def clean_capabilities(self) -> list[str]:
        return list(self.cleaned_data.get("capabilities", []))


@admin.register(LLMProviderConfig)
class LLMProviderConfigAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    form = LLMProviderConfigForm
    ordering = ["-created_at"]

    list_display = [
        "display_name_column",
        "priority",
        "enabled_badge",
        "capabilities_display",
        "timeout_seconds",
        "updated_at",
    ]
    list_filter = ["enabled", "created_at"]
    search_fields = ["name", "model", "secret_ref"]
    readonly_fields = ["id", "created_at", "updated_at", "version"]

    fieldsets = [
        (
            "Model Configuration",
            {
                "fields": ["id", "name", "model", "priority", "enabled"],
                "description": "Name is optional (auto-generated as provider/model if blank).",
            },
        ),
        (
            "Authentication",
            {
                "fields": ["secret_ref", "base_url"],
                "description": "Secret reference is resolved at runtime via SecretResolver.",
                "classes": [],
            },
        ),
        (
            "Capabilities",
            {
                "fields": ["capabilities"],
                "description": "Select which capabilities this provider supports.",
                "classes": [],
            },
        ),
        (
            "Configuration",
            {
                "fields": ["timeout_seconds", "max_tokens"],
                "classes": [],
            },
        ),
        (
            "System",
            {
                "fields": ["created_at", "updated_at", "version"],
                "classes": [],
            },
        ),
    ]

    @admin.display(description="Name")
    def display_name_column(self, obj: LLMProviderConfig) -> str:
        return obj.display_name

    @admin.display(description="Status")
    def enabled_badge(self, obj: LLMProviderConfig) -> str:
        if obj.enabled:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 2px 8px; '
                'border-radius: 4px; font-size: 11px;">ENABLED</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 2px 8px; '
            'border-radius: 4px; font-size: 11px;">DISABLED</span>'
        )

    @admin.display(description="Capabilities")
    def capabilities_display(self, obj: LLMProviderConfig) -> str:
        caps = obj.capabilities or []
        if not caps:
            return "-"
        badges = []
        for cap in caps:
            color = "#17a2b8" if cap == "summary" else "#6610f2"
            badges.append(
                f'<span style="background-color: {color}; color: white; padding: 2px 6px; '
                f'border-radius: 4px; font-size: 10px; margin-right: 4px;">{cap}</span>'
            )
        return format_html("".join(badges))

    def get_actions(  # type: ignore[override]
        self, request: HttpRequest
    ) -> dict[str, tuple[Any, str, str]]:
        actions = super().get_actions(request)
        if "delete_selected" in actions and actions["delete_selected"] is not None:
            delete_action = actions["delete_selected"]
            actions["delete_selected"] = (
                delete_action[0],
                delete_action[1],
                "Delete selected",
            )
        return actions  # type: ignore[return-value]


class EnrichmentFlowForm(forms.ModelForm):  # type: ignore[type-arg]
    """Form with Select2 widgets for filter fields."""

    category_filter = forms.MultipleChoiceField(
        choices=[],
        required=False,
        widget=Select2MultipleWidget(attrs={"data-placeholder": "Select categories..."}),
        help_text="Leave empty to match all categories",
    )
    severity_filter = forms.MultipleChoiceField(
        choices=[],
        required=False,
        widget=Select2MultipleWidget(attrs={"data-placeholder": "Select severities..."}),
        help_text="Leave empty to match all severities",
    )
    service_filter = forms.MultipleChoiceField(
        choices=[],
        required=False,
        widget=Select2MultipleWidget(attrs={"data-placeholder": "Select services..."}),
        help_text="Leave empty to match all services",
    )

    class Meta:
        model = EnrichmentFlow
        fields = [
            "profile",
            "target_type",
            "name",
            "priority",
            "enabled",
            "category_filter",
            "severity_filter",
            "service_filter",
        ]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        profile = self.instance.profile if self.instance.pk else None

        if profile and profile.pk:
            # Populate choices from the selected profile
            self._category_choices = list(profile.categories.values_list("key", "label"))
            self._severity_choices = list(
                profile.severities.order_by("rank").values_list("key", "label")
            )
            self._service_choices = list(
                profile.systems.filter(entry_type="service").values_list("key", "label")
            )

            self.fields["category_filter"].choices = self._category_choices  # type: ignore[attr-defined]
            self.fields["severity_filter"].choices = self._severity_choices  # type: ignore[attr-defined]
            self.fields["service_filter"].choices = self._service_choices  # type: ignore[attr-defined]

            # Pre-select existing values
            if self.instance.category_filter:
                self.initial["category_filter"] = self.instance.category_filter
            if self.instance.severity_filter:
                self.initial["severity_filter"] = self.instance.severity_filter
            if self.instance.service_filter:
                self.initial["service_filter"] = self.instance.service_filter
        else:
            # No profile selected yet - show empty with help text
            self.fields[
                "category_filter"
            ].help_text = "Select a profile first to see available categories"
            self.fields[
                "severity_filter"
            ].help_text = "Select a profile first to see available severities"
            self.fields[
                "service_filter"
            ].help_text = "Select a profile first to see available services"

    def clean_category_filter(self) -> list[str]:
        """Convert widget selection to list for JSONField storage."""
        return list(self.cleaned_data.get("category_filter", []))

    def clean_severity_filter(self) -> list[str]:
        """Convert widget selection to list for JSONField storage."""
        return list(self.cleaned_data.get("severity_filter", []))

    def clean_service_filter(self) -> list[str]:
        """Convert widget selection to list for JSONField storage."""
        return list(self.cleaned_data.get("service_filter", []))


class EnrichmentFlowStepInline(admin.TabularInline):  # type: ignore[type-arg]
    model = EnrichmentFlowStep
    extra = 1
    ordering = ["order"]
    fields = ["order", "enrichment_type", "input_source"]


@admin.register(EnrichmentFlow)
class EnrichmentFlowAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    form = EnrichmentFlowForm
    ordering = ["profile", "target_type", "-priority"]
    list_display = [
        "name",
        "target_type",
        "profile_name",
        "priority",
        "enabled_badge",
        "filters_display",
        "step_count",
        "updated_at",
    ]
    list_filter = ["target_type", "enabled", "profile"]
    search_fields = ["profile__name", "name"]
    inlines = [EnrichmentFlowStepInline]
    readonly_fields = ["id", "created_at", "updated_at", "version"]

    fieldsets = [
        (
            "Flow Configuration",
            {
                "fields": ["id", "profile", "target_type", "name", "priority", "enabled"],
            },
        ),
        (
            "Routing Filters",
            {
                "fields": ["category_filter", "severity_filter", "service_filter"],
                "description": "Empty filter matches all signals. Non-empty filters use OR logic within, AND logic across.",
            },
        ),
        (
            "System",
            {
                "fields": ["created_at", "updated_at", "version"],
                "classes": ["collapse"],
            },
        ),
    ]

    @admin.display(description="Profile")
    def profile_name(self, obj: EnrichmentFlow) -> str:
        return obj.profile.name

    @admin.display(description="Status")
    def enabled_badge(self, obj: EnrichmentFlow) -> str:
        if obj.enabled:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 2px 8px; '
                'border-radius: 4px; font-size: 11px;">ENABLED</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 2px 8px; '
            'border-radius: 4px; font-size: 11px;">DISABLED</span>'
        )

    @admin.display(description="Filters")
    def filters_display(self, obj: EnrichmentFlow) -> str:
        parts = []
        if obj.category_filter:
            parts.append(
                f"cat={','.join(obj.category_filter[:2])}{'...' if len(obj.category_filter) > 2 else ''}"
            )
        if obj.severity_filter:
            parts.append(
                f"sev={','.join(obj.severity_filter[:2])}{'...' if len(obj.severity_filter) > 2 else ''}"
            )
        if obj.service_filter:
            parts.append(
                f"svc={','.join(obj.service_filter[:2])}{'...' if len(obj.service_filter) > 2 else ''}"
            )
        if not parts:
            return format_html('<span style="color: #6c757d; font-style: italic;">catch-all</span>')
        return "; ".join(parts)

    @admin.display(description="Steps")
    def step_count(self, obj: EnrichmentFlow) -> int:
        return obj.flow_steps.count()


@admin.register(EnrichmentRecord)
class EnrichmentRecordAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    ordering = ["-created_at"]
    list_display = [
        "target_display",
        "enrichment_type_badge",
        "status_badge",
        "attempts",
        "duration_display",
        "created_at",
    ]
    list_filter = ["status", "enrichment_type", "target_type", "created_at"]
    search_fields = ["target_id", "input_hash", "error"]
    readonly_fields = [
        "id",
        "target_type",
        "target_id",
        "enrichment_type",
        "input_hash",
        "status",
        "error",
        "attempts",
        "duration_ms",
        "result_preview",
        "embedding_preview",
        "signal_link",
        "created_at",
        "updated_at",
        "version",
    ]
    date_hierarchy = "created_at"

    fieldsets = [
        (
            "Target",
            {
                "fields": ["id", "target_type", "target_id", "signal_link"],
            },
        ),
        (
            "Enrichment",
            {
                "fields": ["enrichment_type", "input_hash", "attempts"],
            },
        ),
        (
            "Result",
            {
                "fields": ["status", "error", "duration_ms", "result_preview", "embedding_preview"],
            },
        ),
        (
            "System",
            {
                "fields": ["created_at", "updated_at", "version"],
                "classes": [],
            },
        ),
    ]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(
        self, request: HttpRequest, obj: EnrichmentRecord | None = None
    ) -> bool:
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: EnrichmentRecord | None = None
    ) -> bool:
        return True

    @admin.display(description="Target")
    def target_display(self, obj: EnrichmentRecord) -> str:
        short_id = str(obj.target_id)[:8]
        return f"{obj.target_type}:{short_id}..."

    @admin.display(description="Type")
    def enrichment_type_badge(self, obj: EnrichmentRecord) -> str:
        enrichment_type = obj.enrichment_type
        base_type = enrichment_type.split(".")[0]
        color = "#17a2b8" if base_type == "summary" else "#6610f2"
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 4px; font-size: 10px;">{}</span>',
            color,
            enrichment_type,
        )

    @admin.display(description="Status")
    def status_badge(self, obj: EnrichmentRecord) -> str:
        if obj.status == EnrichmentStatusChoices.SUCCESS:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 2px 8px; '
                'border-radius: 4px; font-size: 11px;">SUCCESS</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 2px 8px; '
            'border-radius: 4px; font-size: 11px;">FAILED</span>'
        )

    @admin.display(description="Duration")
    def duration_display(self, obj: EnrichmentRecord) -> str:
        if obj.duration_ms is None:
            return "-"
        if obj.duration_ms < 1000:
            return f"{obj.duration_ms}ms"
        return f"{obj.duration_ms / 1000:.1f}s"

    @admin.display(description="Signal")
    def signal_link(self, obj: EnrichmentRecord) -> str:
        target_type_map = {
            "Incident": "incident",
            "CustomerCase": "customercase",
            "TechnicalIssue": "technicalissue",
        }
        model_name = target_type_map.get(obj.target_type)
        if not model_name:
            return f"{obj.target_type}:{obj.target_id}"
        url = reverse(f"admin:nazara_signals_{model_name}_change", args=[obj.target_id])
        return format_html(
            '<a href="{}">{}: {}</a>',
            url,
            obj.target_type,
            str(obj.target_id)[:8] + "...",
        )

    @admin.display(description="Result")
    def result_preview(self, obj: EnrichmentRecord) -> str:
        if not obj.result:
            return "-"
        text = obj.result.get("text", "")
        if not text:
            import json

            return format_html(
                '<pre style="background:#f5f5f5;padding:10px;border-radius:4px;'
                'max-height:400px;overflow:auto;font-size:12px;white-space:pre-wrap">{}</pre>',
                json.dumps(obj.result, indent=2, ensure_ascii=False),
            )
        return format_html(
            '<div style="background:#f5f5f5;padding:10px;border-radius:4px;'
            'max-height:400px;overflow:auto;font-size:13px;line-height:1.5">{}</div>',
            text,
        )

    @admin.display(description="Embedding")
    def embedding_preview(self, obj: EnrichmentRecord) -> str:
        if obj.embedding is None:
            return "-"
        embedding_list = list(obj.embedding)
        if not embedding_list:
            return "-"
        length = len(embedding_list)
        preview = embedding_list[:5] if length > 5 else embedding_list
        preview_str = ", ".join(f"{v:.4f}" for v in preview)
        if length > 5:
            preview_str += f", ... ({length} dimensions)"
        return format_html(
            '<code style="background:#f5f5f5;padding:4px 8px;border-radius:4px;">[{}]</code>',
            preview_str,
        )
