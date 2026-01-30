from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)

# Default retention periods
DEFAULT_RAW_EVENT_RETENTION_DAYS = 14
DEFAULT_ISSUE_RETENTION_MONTHS = 9


@shared_task
def cleanup_raw_events_task(retention_days: int | None = None) -> dict[str, Any]:
    """
    Delete raw TechnicalEvent records older than retention period.

    This task implements the raw event TTL policy. Issues are not affected
    by this cleanup - they persist independently.

    Args:
        retention_days: Number of days to retain events (default: 14)

    Returns:
        Dict with deleted count and status
    """
    from nazara.signals.infrastructure.django.app.models import TechnicalEventModel

    retention_days = retention_days or DEFAULT_RAW_EVENT_RETENTION_DAYS
    cutoff = timezone.now() - timedelta(days=retention_days)

    try:
        # Delete events older than cutoff
        deleted_count, _ = TechnicalEventModel.objects.filter(created_at__lt=cutoff).delete()

        logger.info(
            f"Raw event cleanup complete: deleted {deleted_count} events "
            f"older than {retention_days} days"
        )

        return {
            "status": "success",
            "deleted_count": deleted_count,
            "retention_days": retention_days,
            "cutoff_date": cutoff.isoformat(),
        }

    except Exception as e:
        logger.error(f"Raw event cleanup failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "deleted_count": 0,
        }


@shared_task
def cleanup_stale_issues_task(retention_months: int | None = None) -> dict[str, Any]:
    """
    Delete TechnicalIssue records not seen in retention period.

    This task cleans up issues that haven't received new events in a long time.
    Issues are deleted based on last_seen_at, not created_at.

    Args:
        retention_months: Number of months of inactivity before deletion (default: 9)

    Returns:
        Dict with deleted count and status
    """
    from nazara.containers import get_container

    retention_months = retention_months or DEFAULT_ISSUE_RETENTION_MONTHS
    cutoff = timezone.now() - timedelta(days=retention_months * 30)

    try:
        container = get_container()
        issue_repo = container.signals.issue_repository()
        deleted_count = issue_repo.delete_stale_before(cutoff)

        logger.info(
            f"Issue cleanup complete: deleted {deleted_count} issues "
            f"not seen in {retention_months} months"
        )

        return {
            "status": "success",
            "deleted_count": deleted_count,
            "retention_months": retention_months,
            "cutoff_date": cutoff.isoformat(),
        }

    except Exception as e:
        logger.error(f"Issue cleanup failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "deleted_count": 0,
        }


@shared_task
def cleanup_all_stale_data_task() -> dict[str, Any]:
    """
    Combined cleanup task for both raw events and issues.

    This is a convenience task that runs both cleanup operations.
    Can be scheduled as a single daily job.

    Returns:
        Dict with combined results
    """
    raw_result = cleanup_raw_events_task()
    issue_result = cleanup_stale_issues_task()

    total_deleted = raw_result.get("deleted_count", 0) + issue_result.get("deleted_count", 0)

    return {
        "status": "success" if raw_result.get("status") == "success" else "partial",
        "raw_events": raw_result,
        "issues": issue_result,
        "total_deleted": total_deleted,
    }
