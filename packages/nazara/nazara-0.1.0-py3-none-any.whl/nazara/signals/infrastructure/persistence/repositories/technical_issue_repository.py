from datetime import datetime
from uuid import UUID

from django.db import IntegrityError, transaction

from nazara.signals.domain.contracts.technical_issue_repository import TechnicalIssueRepository
from nazara.signals.domain.models import TechnicalIssue


class DjangoTechnicalIssueRepository(TechnicalIssueRepository):
    def save(self, issue: TechnicalIssue) -> tuple[TechnicalIssue, int]:
        events_saved = 0
        pending_events = issue.get_pending_events()
        is_new_issue = issue._state.adding

        with transaction.atomic():
            # Save the aggregate root first (to get ID for new issues)
            issue.save()

            # Save pending events
            for event in pending_events:
                event.issue = issue  # Ensure FK is set
                try:
                    event.save()
                    events_saved += 1
                except IntegrityError:
                    # Duplicate event (unique constraint violation)
                    # Skip silently - idempotent behavior
                    pass

            # Update counter based on actually-saved events (for existing issues)
            if events_saved > 0 and not is_new_issue:
                issue.occurrences_total += events_saved
                issue.save(update_fields=["occurrences_total", "updated_at"])

            issue.clear_pending_events()

        return issue, events_saved

    def get_by_identity(
        self,
        provider: str,
        issue_key: str,
        environment: str,
        service: str,
    ) -> TechnicalIssue | None:
        return TechnicalIssue.objects.filter(
            provider=provider,
            issue_key=issue_key,
            environment=environment,
            service=service,
        ).first()

    def get(self, issue_id: UUID) -> TechnicalIssue | None:
        return TechnicalIssue.objects.filter(id=issue_id).first()

    def delete(self, issue_id: UUID) -> bool:
        deleted, _ = TechnicalIssue.objects.filter(id=issue_id).delete()
        return deleted > 0

    def delete_stale_before(self, before: datetime) -> int:
        deleted, _ = TechnicalIssue.objects.filter(last_seen_at__lt=before).delete()
        return deleted

    def count(
        self,
        provider: str | None = None,
        environment: str | None = None,
        service: str | None = None,
        status: str | None = None,
    ) -> int:
        qs = TechnicalIssue.objects.all()
        if provider:
            qs = qs.filter(provider=provider)
        if environment:
            qs = qs.filter(environment=environment)
        if service:
            qs = qs.filter(service=service)
        if status:
            qs = qs.filter(status=status)
        return qs.count()
