from __future__ import annotations

import json
from typing import Any

from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html
from django_admin_inline_paginator_plus.admin import TabularInlinePaginated

from nazara.signals.infrastructure.django.app.models import (
    CustomerCaseModel,
    IncidentModel,
    IssueStatusChoices,
    SeverityChoices,
    TechnicalEventModel,
    TechnicalIssueModel,
)


@admin.action(description="Reenrich selected")
def reenrich_selected(
    modeladmin: admin.ModelAdmin[Any],
    request: HttpRequest,
    queryset: QuerySet[Any],
) -> None:
    """
    Admin action to re-enrich selected signals.

    Queues Celery tasks with force=True to regenerate AI summaries
    even if they already exist.
    """
    from nazara.intelligence.infrastructure.messaging.tasks import (
        enrich_customer_case_task,
        enrich_incident_task,
        enrich_technical_issue_task,
    )

    model_name = queryset.model.__name__

    task_map = {
        "Incident": enrich_incident_task,
        "IncidentModel": enrich_incident_task,
        "CustomerCase": enrich_customer_case_task,
        "CustomerCaseModel": enrich_customer_case_task,
        "TechnicalIssue": enrich_technical_issue_task,
        "TechnicalIssueModel": enrich_technical_issue_task,
    }
    task = task_map.get(model_name)

    if not task:
        modeladmin.message_user(
            request,
            f"Unknown model type: {model_name}",
            messages.ERROR,
        )
        return

    id_param_map = {
        "Incident": "incident_id",
        "IncidentModel": "incident_id",
        "CustomerCase": "case_id",
        "CustomerCaseModel": "case_id",
        "TechnicalIssue": "issue_id",
        "TechnicalIssueModel": "issue_id",
    }
    id_param = id_param_map[model_name]

    target_type = model_name.replace("Model", "")

    count = 0
    for obj in queryset:
        task.delay(**{id_param: str(obj.id), "force": True})
        count += 1

    modeladmin.message_user(
        request,
        f"Queued {count} {target_type}(s) for re-enrichment.",
        messages.SUCCESS,
    )


class ReadOnlyDeleteAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    """Base admin class: read-only with delete capability."""

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return True

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


class SeverityFilter(admin.SimpleListFilter):
    """Filter for severity levels with color indicators."""

    title = "Severity"
    parameter_name = "severity"

    def lookups(
        self, request: HttpRequest, model_admin: admin.ModelAdmin[Any]
    ) -> list[tuple[str, str]]:
        return list(SeverityChoices.choices)

    def queryset(self, request: HttpRequest, queryset: QuerySet[Any]) -> QuerySet[Any]:
        if self.value():
            return queryset.filter(severity=self.value())
        return queryset


@admin.display(description="Severity")
def severity_badge(obj: Any) -> str:
    """Render severity as a colored badge."""
    colors = {
        SeverityChoices.CRITICAL: "#dc3545",
        SeverityChoices.HIGH: "#fd7e14",
        SeverityChoices.MEDIUM: "#ffc107",
        SeverityChoices.LOW: "#28a745",
        SeverityChoices.INFO: "#17a2b8",
    }
    color = colors.get(obj.severity, "#6c757d")
    return format_html(
        '<span style="background-color: {}; color: white; padding: 2px 8px; '
        'border-radius: 4px; font-size: 11px;">{}</span>',
        color,
        obj.severity.upper(),
    )


@admin.register(CustomerCaseModel)
class CustomerCaseAdmin(ReadOnlyDeleteAdmin):
    """Read-only admin for CustomerCase with delete capability."""

    actions = [reenrich_selected]
    ordering = ["-started_at"]
    list_display = [
        "title",
        severity_badge,
        "category",
        "status",
        "source_system",
        "started_at",
        "is_linked",
    ]
    list_filter = [SeverityFilter, "status", "category", "source_system", "created_at"]
    search_fields = [
        "title",
        "description",
        "customer_id",
        "customer_email",
        "source_identifier",
    ]
    date_hierarchy = "created_at"
    readonly_fields = [
        "tags_display",
        "metadata_display",
        "raw_data_display",
        "conversation_display",
        "enrichment_links",
    ]

    fieldsets = [
        (
            "Case Information",
            {
                "fields": ["id", "title", "description", "status", "severity", "category"],
            },
        ),
        (
            "Customer",
            {
                "fields": ["customer_id", "customer_email", "customer_name"],
            },
        ),
        (
            "Source",
            {
                "fields": ["source_system", "source_identifier", "source_url"],
            },
        ),
        (
            "Timeline",
            {
                "fields": ["started_at", "ended_at"],
            },
        ),
        (
            "AI Analysis",
            {
                "fields": ["enrichment_links"],
            },
        ),
        (
            "Relations & Metadata",
            {
                "fields": ["related_incident", "tags_display", "metadata_display"],
            },
        ),
        (
            "Raw Data",
            {
                "fields": ["raw_data_display", "conversation_display"],
                "classes": ["collapse"],
            },
        ),
        (
            "System",
            {
                "fields": ["created_at", "updated_at", "version"],
            },
        ),
    ]

    @admin.display(description="Linked", boolean=True)
    def is_linked(self, obj: CustomerCaseModel) -> bool:
        return obj.related_incident is not None

    @admin.display(description="Tags")
    def tags_display(self, obj: CustomerCaseModel) -> str:
        if not obj.tags:
            return "-"
        badges = [
            f'<span style="background:#17a2b8;color:white;padding:3px 10px;'
            f'border-radius:12px;margin:2px;display:inline-block;font-size:12px">{tag}</span>'
            for tag in obj.tags
        ]
        return format_html("".join(badges))

    @admin.display(description="Metadata")
    def metadata_display(self, obj: CustomerCaseModel) -> str:
        if not obj.metadata:
            return "-"
        rows = [
            f'<tr><td style="padding:4px 12px 4px 0;font-weight:600;color:#555">{k}</td>'
            f'<td style="padding:4px 0">{v}</td></tr>'
            for k, v in obj.metadata.items()
        ]
        return format_html(
            f'<table style="width:100%;border-collapse:collapse;margin:4px 0">{"".join(rows)}</table>'
        )

    @admin.display(description="Raw Data")
    def raw_data_display(self, obj: CustomerCaseModel) -> str:
        if not obj.raw_data:
            return "-"
        formatted = json.dumps(obj.raw_data, indent=2, ensure_ascii=False)
        return format_html(
            '<pre style="background:#f5f5f5;padding:10px;border-radius:4px;'
            'max-height:400px;overflow:auto;font-size:12px;white-space:pre-wrap">{}</pre>',
            formatted,
        )

    @admin.display(description="Conversation")
    def conversation_display(self, obj: CustomerCaseModel) -> str:
        if not obj.conversation:
            return "-"
        formatted = json.dumps(obj.conversation, indent=2, ensure_ascii=False)
        return format_html(
            '<pre style="background:#f5f5f5;padding:10px;border-radius:4px;'
            'max-height:400px;overflow:auto;font-size:12px;white-space:pre-wrap">{}</pre>',
            formatted,
        )

    @admin.display(description="Enrichments")
    def enrichment_links(self, obj: CustomerCaseModel) -> str:
        from django.urls import reverse

        from nazara.intelligence.domain.models import EnrichmentRecord

        records = EnrichmentRecord.objects.filter(
            target_type="CustomerCase",
            target_id=obj.id,
        )
        if not records.exists():
            return "No enrichments"

        links = []
        for r in records:
            url = reverse("admin:nazara_intelligence_enrichmentrecord_change", args=[r.id])
            status_icon = "✅" if r.status == "success" else "❌"
            links.append(f'<a href="{url}">{status_icon} {r.enrichment_type}</a>')
        return format_html("<br>".join(links))


@admin.register(IncidentModel)
class IncidentAdmin(ReadOnlyDeleteAdmin):
    """Read-only admin for Incident with delete capability."""

    actions = [reenrich_selected]
    ordering = ["-started_at"]
    list_display = [
        "title",
        severity_badge,
        "category",
        "status",
        "affected_services_display",
        "started_at",
        "case_count",
        "event_count",
    ]
    list_filter = [SeverityFilter, "status", "category", "source_system", "created_at"]
    search_fields = [
        "title",
        "description",
        "source_identifier",
        "root_cause_description",
    ]
    date_hierarchy = "created_at"
    readonly_fields = ["tags_display", "raw_data_display", "enrichment_links"]

    fieldsets = [
        (
            "Incident Information",
            {
                "fields": ["id", "title", "description", "status", "severity", "category"],
            },
        ),
        (
            "Source",
            {
                "fields": ["source_system", "source_identifier", "source_url"],
            },
        ),
        (
            "Timeline",
            {
                "fields": ["started_at", "ended_at", "timeline"],
            },
        ),
        (
            "Impact",
            {
                "fields": [
                    "affected_services",
                    "affected_users_count",
                    "affected_regions",
                    "impact_description",
                ],
            },
        ),
        (
            "Root Cause",
            {
                "fields": [
                    "root_cause_description",
                    "root_cause_category",
                    "root_cause_identified_at",
                ],
            },
        ),
        (
            "AI Analysis",
            {
                "fields": ["enrichment_links"],
            },
        ),
        (
            "Metadata",
            {
                "fields": ["tags_display"],
            },
        ),
        (
            "Raw Data",
            {
                "fields": ["raw_data_display"],
                "classes": ["collapse"],
            },
        ),
        (
            "System",
            {
                "fields": ["created_at", "updated_at", "version"],
            },
        ),
    ]

    @admin.display(description="Services")
    def affected_services_display(self, obj: IncidentModel) -> str:
        services = obj.affected_services or []
        if not services:
            return "-"
        return ", ".join(services[:3]) + ("..." if len(services) > 3 else "")

    @admin.display(description="Tags")
    def tags_display(self, obj: IncidentModel) -> str:
        if not obj.tags:
            return "-"
        badges = [
            f'<span style="background:#17a2b8;color:white;padding:3px 10px;'
            f'border-radius:12px;margin:2px;display:inline-block;font-size:12px">{tag}</span>'
            for tag in obj.tags
        ]
        return format_html("".join(badges))

    @admin.display(description="Raw Data")
    def raw_data_display(self, obj: IncidentModel) -> str:
        if not obj.raw_data:
            return "-"
        formatted = json.dumps(obj.raw_data, indent=2, ensure_ascii=False)
        return format_html(
            '<pre style="background:#f5f5f5;padding:10px;border-radius:4px;'
            'max-height:400px;overflow:auto;font-size:12px;white-space:pre-wrap">{}</pre>',
            formatted,
        )

    @admin.display(description="Cases")
    def case_count(self, obj: IncidentModel) -> str:
        count = obj.customer_cases.count()
        return format_html('<span style="font-weight: bold;">{}</span>', count)

    @admin.display(description="Events")
    def event_count(self, obj: IncidentModel) -> str:
        count = obj.technical_events.count()
        return format_html('<span style="font-weight: bold;">{}</span>', count)

    @admin.display(description="Enrichments")
    def enrichment_links(self, obj: IncidentModel) -> str:
        from django.urls import reverse

        from nazara.intelligence.domain.models import EnrichmentRecord

        records = EnrichmentRecord.objects.filter(
            target_type="Incident",
            target_id=obj.id,
        )
        if not records.exists():
            return "No enrichments"

        links = []
        for r in records:
            url = reverse("admin:nazara_intelligence_enrichmentrecord_change", args=[r.id])
            status_icon = "✅" if r.status == "success" else "❌"
            links.append(f'<a href="{url}">{status_icon} {r.enrichment_type}</a>')
        return format_html("<br>".join(links))


class TechnicalEventInline(TabularInlinePaginated):
    """Paginated inline for TechnicalEvent within TechnicalIssue."""

    model = TechnicalEventModel
    fk_name = "issue"
    per_page = 20
    ordering = ["-occurred_at"]
    fields = [
        "occurred_at",
        "event_type",
        "title",
        "severity",
        "source_system",
        "occurrence_count",
    ]
    readonly_fields = fields

    def has_add_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False


@admin.display(description="Status")
def status_badge(obj: Any) -> str:
    """Render status as a colored badge."""
    colors = {
        IssueStatusChoices.ACTIVE: "#dc3545",
        IssueStatusChoices.RESOLVED: "#28a745",
    }
    color = colors.get(obj.status, "#6c757d")
    return format_html(
        '<span style="background-color: {}; color: white; padding: 2px 8px; '
        'border-radius: 4px; font-size: 11px;">{}</span>',
        color,
        obj.status.upper(),
    )


@admin.register(TechnicalIssueModel)
class TechnicalIssueAdmin(ReadOnlyDeleteAdmin):
    """
    Read-only admin for TechnicalIssue (aggregate root).

    This is the primary view for managing issues. Issues represent
    stable technical problems that persist longer than raw events.
    """

    actions = [reenrich_selected]
    inlines = [TechnicalEventInline]
    ordering = ["-last_seen_at"]
    list_display = [
        "title_display",
        "provider",
        status_badge,
        severity_badge,
        "category",
        "service",
        "environment",
        "event_count",
        "occurrences_display",
        "first_seen_at",
        "last_seen_at",
    ]
    list_filter = [
        "status",
        SeverityFilter,
        "category",
        "provider",
        "service",
        "environment",
        "created_at",
    ]
    search_fields = [
        "title",
        "issue_key",
        "last_message",
        "service",
    ]
    date_hierarchy = "last_seen_at"
    readonly_fields = ["sample_payload_display", "enrichment_links"]

    fieldsets = [
        (
            "Issue Identity",
            {
                "fields": ["id", "provider", "issue_key", "environment", "service"],
            },
        ),
        (
            "Status & Classification",
            {
                "fields": ["status", "severity", "category", "occurrences_total"],
            },
        ),
        (
            "Timeline",
            {
                "fields": ["first_seen_at", "last_seen_at"],
            },
        ),
        (
            "Details",
            {
                "fields": ["title", "last_message", "source_url", "sample_payload_display"],
            },
        ),
        (
            "AI Analysis",
            {
                "fields": ["enrichment_links"],
            },
        ),
        (
            "System",
            {
                "fields": ["created_at", "updated_at"],
            },
        ),
    ]

    @admin.display(description="Title")
    def title_display(self, obj: TechnicalIssueModel) -> str:
        return obj.title or f"{obj.provider}:{obj.issue_key[:30]}..."

    @admin.display(description="Events")
    def event_count(self, obj: TechnicalIssueModel) -> str:
        count = obj.events.count()
        return format_html('<span style="font-weight: bold;">{}</span>', count)

    @admin.display(description="Occurrences")
    def occurrences_display(self, obj: TechnicalIssueModel) -> str:
        return format_html('<span style="font-weight: bold;">{}</span>', obj.occurrences_total)

    @admin.display(description="Sample Payload")
    def sample_payload_display(self, obj: TechnicalIssueModel) -> str:
        if not obj.sample_payload:
            return "-"
        formatted = json.dumps(obj.sample_payload, indent=2, ensure_ascii=False)
        return format_html(
            '<pre style="background:#f5f5f5;padding:10px;border-radius:4px;'
            'max-height:400px;overflow:auto;font-size:12px;white-space:pre-wrap">{}</pre>',
            formatted,
        )

    @admin.display(description="Enrichments")
    def enrichment_links(self, obj: TechnicalIssueModel) -> str:
        from django.urls import reverse

        from nazara.intelligence.domain.models import EnrichmentRecord

        records = EnrichmentRecord.objects.filter(
            target_type="TechnicalIssue",
            target_id=obj.id,
        )
        if not records.exists():
            return "No enrichments"

        links = []
        for r in records:
            url = reverse("admin:nazara_intelligence_enrichmentrecord_change", args=[r.id])
            status_icon = "✅" if r.status == "success" else "❌"
            links.append(f'<a href="{url}">{status_icon} {r.enrichment_type}</a>')
        return format_html("<br>".join(links))


# NOTE: TechnicalEventModel is hidden from admin by default.
# Uncomment the registration below for debugging purposes only.
# Raw events have short retention and should be accessed via issues.


# @admin.register(TechnicalEventModel)
class TechnicalEventAdmin(ReadOnlyDeleteAdmin):
    """
    Read-only admin for TechnicalEvent (raw events).

    NOTE: This admin is NOT registered by default. Raw events are
    transient data with short retention (14 days). Use the
    TechnicalIssue admin for day-to-day operations.

    To enable for debugging, uncomment the @admin.register decorator.
    """

    list_display = [
        "title",
        "event_type",
        severity_badge,
        "provider",
        "service",
        "environment",
        "occurrence_count",
        "occurred_at",
        "issue_link",
    ]
    list_filter = [
        SeverityFilter,
        "event_type",
        "provider",
        "service",
        "environment",
    ]
    search_fields = [
        "title",
        "description",
        "error_type",
        "error_message",
        "error_fingerprint",
        "source_identifier",
        "external_id",
    ]
    date_hierarchy = "created_at"

    fieldsets = [
        (
            "Event Information",
            {
                "fields": ["id", "event_type", "title", "description", "severity"],
            },
        ),
        (
            "Provider & Grouping",
            {
                "fields": ["provider", "external_id", "dedupe_hash", "issue"],
            },
        ),
        (
            "Source",
            {
                "fields": ["source_system", "source_identifier", "source_url"],
            },
        ),
        (
            "Context",
            {
                "fields": ["service", "environment", "host", "transaction", "release"],
            },
        ),
        (
            "Timeline",
            {
                "fields": ["occurred_at", "started_at", "ended_at", "occurrence_count"],
            },
        ),
        (
            "Error Details",
            {
                "fields": [
                    "error_type",
                    "error_message",
                    "error_stacktrace",
                    "error_fingerprint",
                ],
            },
        ),
        (
            "Metric Details",
            {
                "fields": [
                    "metric_name",
                    "metric_value",
                    "metric_threshold",
                    "metric_unit",
                ],
            },
        ),
        (
            "Relations & Metadata",
            {
                "fields": ["related_incident", "tags", "raw_data"],
            },
        ),
        (
            "System",
            {
                "fields": ["created_at", "updated_at"],
            },
        ),
    ]

    @admin.display(description="Issue")
    def issue_link(self, obj: TechnicalEventModel) -> str:
        if obj.issue:
            return format_html(
                '<a href="/admin/nazara_signals/technicalissuemodel/{}/change/">{}</a>',
                obj.issue.id,
                obj.issue.title or str(obj.issue.id)[:8],
            )
        return "-"
