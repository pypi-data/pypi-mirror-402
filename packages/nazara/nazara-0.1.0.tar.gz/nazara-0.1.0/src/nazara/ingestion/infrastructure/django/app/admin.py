from __future__ import annotations

from typing import Any

from django.contrib import admin, messages
from django.db.models import JSONField, QuerySet
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import redirect
from django.utils.html import format_html
from django_admin_inline_paginator_plus.admin import TabularInlinePaginated
from django_json_widget.widgets import JSONEditorWidget

from nazara.ingestion.infrastructure.django.app.models import (
    IngestorConfigModel,
    IngestorRunModel,
)


@admin.display(description="Health")
def health_status_badge(obj: IngestorConfigModel) -> str:
    if not obj.enabled:
        color = "#6c757d"  # Gray for disabled
        status = "DISABLED"
    elif obj.error_count >= 5:
        color = "#dc3545"  # Red for failing
        status = "FAILING"
    elif obj.error_count > 0:
        color = "#fd7e14"  # Orange for warnings
        status = "WARNING"
    else:
        color = "#28a745"  # Green for healthy
        status = "HEALTHY"

    return format_html(
        '<span style="background-color: {}; color: white; padding: 2px 8px; '
        'border-radius: 4px; font-size: 11px;">{}</span>',
        color,
        status,
    )


class IngestorRunInline(TabularInlinePaginated):
    model = IngestorRunModel
    fk_name = "config"
    per_page = 20
    ordering = ["-started_at"]
    fields = [
        "started_at",
        "status_badge",
        "results_display",
        "duration_display",
        "error_display",
    ]
    readonly_fields = [
        "started_at",
        "status_badge",
        "results_display",
        "duration_display",
        "error_display",
    ]

    def has_add_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return True

    @admin.display(description="Status")
    def status_badge(self, obj: IngestorRunModel) -> str:
        colors = {
            "running": "#17a2b8",  # Blue
            "success": "#28a745",  # Green
            "failed": "#dc3545",  # Red
            "cancelled": "#6c757d",  # Gray
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 4px; font-size: 11px;">{}</span>',
            color,
            obj.status.upper(),
        )

    @admin.display(description="Results")
    def results_display(self, obj: IngestorRunModel) -> str:
        # Format: "10 (+5/~3/=2)" = 10 processed, 5 created, 3 updated, 2 skipped
        return f"{obj.items_processed} (+{obj.items_created}/~{obj.items_updated}/={obj.items_skipped})"

    @admin.display(description="Duration")
    def duration_display(self, obj: IngestorRunModel) -> str:
        if obj.finished_at is None:
            return "Running..."
        duration = (obj.finished_at - obj.started_at).total_seconds()
        if duration < 60:
            return f"{duration:.1f}s"
        elif duration < 3600:
            return f"{duration / 60:.1f}m"
        else:
            return f"{duration / 3600:.1f}h"

    @admin.display(description="Error")
    def error_display(self, obj: IngestorRunModel) -> str:
        if not obj.error_message:
            return "-"
        return format_html(
            '<code style="font-size:11px;">{}</code>',
            obj.error_message,
        )


@admin.register(IngestorConfigModel)
class IngestorConfigAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    """
    Admin for IngestorConfig - editable configuration for data sources.

    Includes custom actions:
    - Test Connection
    - Sync Now
    - Reset Cursor (privileged)
    """

    inlines = [IngestorRunInline]

    list_display = [
        "display_name_column",
        "ingestor_type",
        health_status_badge,
        "ingestion_mode",
        "last_success_at",
        "error_count",
        "run_count",
    ]
    list_filter = ["enabled", "ingestor_type", "ingestion_mode", "auth_type"]
    search_fields = ["name", "secret_ref", "external_account_id"]
    ordering = ["-created_at"]
    formfield_overrides = {
        JSONField: {
            "widget": JSONEditorWidget(
                width="100%",
                height="300px",
                options={"mode": "code", "modes": ["code", "tree"]},
            )
        },
    }

    readonly_fields = [
        "id",
        "cursor",
        "last_success_at",
        "last_error_at",
        "error_count",
        "last_error_message",
        "created_at",
        "updated_at",
        "version",
    ]

    fieldsets = [
        (
            "Identity",
            {
                "fields": ["id", "name", "ingestor_type", "enabled"],
                "description": "Name is optional (auto-generated as type/account if blank).",
            },
        ),
        (
            "Authentication",
            {
                "fields": ["auth_type", "secret_ref", "external_account_id"],
                "description": "Secret reference points to your secrets manager. Never store actual secrets here.",
                "classes": [],
            },
        ),
        (
            "Mode & Schedule",
            {
                "fields": ["ingestion_mode", "poll_interval_seconds", "since"],
                "classes": [],
            },
        ),
        (
            "Filters",
            {
                "fields": ["filters"],
                "description": "Source-specific configuration (JSON). See documentation for filter schema.",
                "classes": [],
            },
        ),
        (
            "State (Read-Only)",
            {
                "fields": [
                    "cursor",
                    "last_success_at",
                    "last_error_at",
                    "error_count",
                    "last_error_message",
                ],
                "classes": ["collapse"],
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

    actions = ["enable_selected", "disable_selected", "sync_now_action"]

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

    @admin.display(description="Name")
    def display_name_column(self, obj: IngestorConfigModel) -> str:
        return obj.display_name

    @admin.display(description="Runs")
    def run_count(self, obj: IngestorConfigModel) -> str:
        count = obj.runs.count()
        return format_html('<span style="font-weight: bold;">{}</span>', count)

    @admin.action(description="Enable selected")
    def enable_selected(
        self, request: HttpRequest, queryset: QuerySet[IngestorConfigModel]
    ) -> None:
        count = queryset.update(enabled=True)
        self.message_user(request, f"Enabled {count} ingestor(s).")

    @admin.action(description="Disable selected")
    def disable_selected(
        self, request: HttpRequest, queryset: QuerySet[IngestorConfigModel]
    ) -> None:
        count = queryset.update(enabled=False)
        self.message_user(request, f"Disabled {count} ingestor(s).")

    @admin.action(description="Run selected")
    def sync_now_action(
        self, request: HttpRequest, queryset: QuerySet[IngestorConfigModel]
    ) -> None:
        from nazara.ingestion.infrastructure.messaging.tasks import run_ingestor_task

        count = 0
        for config in queryset:
            if config.enabled:
                run_ingestor_task.delay(str(config.id))
                count += 1

        self.message_user(
            request,
            f"Queued {count} ingestor(s) for immediate sync. Check run history for results.",
        )

    def get_urls(self) -> list[Any]:
        from django.urls import path

        urls = super().get_urls()
        custom_urls = [
            path(
                "<uuid:pk>/test-connection/",
                self.admin_site.admin_view(self.test_connection_view),
                name="ingestor-test-connection",
            ),
            path(
                "<uuid:pk>/sync-now/",
                self.admin_site.admin_view(self.sync_now_view),
                name="ingestor-sync-now",
            ),
            path(
                "<uuid:pk>/reset-cursor/",
                self.admin_site.admin_view(self.reset_cursor_view),
                name="ingestor-reset-cursor",
            ),
        ]
        return custom_urls + urls

    def test_connection_view(self, request: HttpRequest, pk: Any) -> HttpResponseRedirect:
        from uuid import UUID

        from nazara.containers import get_container

        container = get_container()
        ingestion = container.ingestion.run_ingestion()

        try:
            success, message = ingestion.test_connection(UUID(str(pk)))
            if success:
                messages.success(request, f"✓ {message}")
            else:
                messages.error(request, f"✗ {message}")
        except Exception as e:
            messages.error(request, f"✗ Connection test failed: {e}")

        return redirect("admin:nazara_ingestion_ingestorconfig_change", pk)

    def sync_now_view(self, request: HttpRequest, pk: Any) -> HttpResponseRedirect:
        from nazara.ingestion.infrastructure.messaging.tasks import run_ingestor_task

        config = self.get_object(request, pk)
        if config and config.enabled:
            run_ingestor_task.delay(str(pk))
            messages.success(
                request,
                f"Sync queued for '{config.name}'. Check run history for results.",
            )
        else:
            messages.error(request, "Cannot sync: ingestor is disabled or not found.")

        return redirect("admin:nazara_ingestion_ingestorconfig_change", pk)

    def reset_cursor_view(self, request: HttpRequest, pk: Any) -> HttpResponseRedirect:
        config = self.get_object(request, pk)
        if config:
            if not request.user.is_superuser:
                messages.error(
                    request,
                    "Only superusers can reset ingestor cursors.",
                )
            else:
                config.reset_cursor()
                config.save()
                messages.warning(
                    request,
                    f"Cursor reset for '{config.name}'. Next sync will re-ingest historical data.",
                )
        else:
            messages.error(request, "Ingestor configuration not found.")

        return redirect("admin:nazara_ingestion_ingestorconfig_change", pk)

    def change_view(
        self,
        request: HttpRequest,
        object_id: str,
        form_url: str = "",
        extra_context: dict[str, Any] | None = None,
    ) -> Any:
        extra_context = extra_context or {}
        extra_context["show_ingestor_actions"] = True
        return super().change_view(request, object_id, form_url, extra_context)
