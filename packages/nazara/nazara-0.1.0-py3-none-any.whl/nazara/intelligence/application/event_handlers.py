import logging

from nazara.intelligence.domain.events import DomainProfileUpdatedEvent
from nazara.shared.event_bus.registry import register_handler
from nazara.signals.domain.events import SignalCreatedEvent, SignalUpdatedEvent

logger = logging.getLogger(__name__)


def handle_signal_created(event: SignalCreatedEvent) -> None:
    from nazara.intelligence.infrastructure.messaging.tasks import (
        enrich_customer_case_task,
        enrich_incident_task,
        enrich_technical_issue_task,
    )

    if event.signal_type == "Incident":
        enrich_incident_task.delay(incident_id=str(event.signal_id))
    elif event.signal_type == "CustomerCase":
        enrich_customer_case_task.delay(case_id=str(event.signal_id))
    elif event.signal_type == "TechnicalIssue":
        enrich_technical_issue_task.delay(issue_id=str(event.signal_id))


def handle_signal_updated(event: SignalUpdatedEvent) -> None:
    from nazara.intelligence.infrastructure.messaging.tasks import (
        enrich_customer_case_task,
        enrich_incident_task,
        enrich_technical_issue_task,
    )

    content_fields = {"title", "description", "summary"}
    if content_fields.intersection(event.changed_fields):
        if event.signal_type == "Incident":
            enrich_incident_task.delay(incident_id=str(event.signal_id), force=True)
        elif event.signal_type == "CustomerCase":
            enrich_customer_case_task.delay(case_id=str(event.signal_id), force=True)
        elif event.signal_type == "TechnicalIssue":
            enrich_technical_issue_task.delay(issue_id=str(event.signal_id), force=True)


def handle_domain_profile_updated(event: DomainProfileUpdatedEvent) -> None:
    """
    Reconcile EnrichmentFlow filters when a DomainProfile is updated.

    Removes filter values that no longer exist in the profile's
    categories, severities, or services.
    """
    from nazara.intelligence.domain.models import DomainProfile

    try:
        profile = DomainProfile.objects.get(id=event.profile_id)
    except DomainProfile.DoesNotExist:
        logger.warning(f"DomainProfile {event.profile_id} not found for reconciliation")
        return

    # Get current valid keys from profile
    valid_categories = set(profile.categories.values_list("key", flat=True))
    valid_severities = set(profile.severities.values_list("key", flat=True))
    valid_services = set(profile.systems.filter(entry_type="service").values_list("key", flat=True))

    flows_updated = 0
    categories_removed = 0
    severities_removed = 0
    services_removed = 0

    # Reconcile each flow's filters
    for flow in profile.enrichment_flows.all():
        updated = False

        # Reconcile category_filter
        if flow.category_filter:
            original_count = len(flow.category_filter)
            flow.category_filter = [c for c in flow.category_filter if c in valid_categories]
            removed = original_count - len(flow.category_filter)
            if removed > 0:
                categories_removed += removed
                updated = True

        # Reconcile severity_filter
        if flow.severity_filter:
            original_count = len(flow.severity_filter)
            flow.severity_filter = [s for s in flow.severity_filter if s in valid_severities]
            removed = original_count - len(flow.severity_filter)
            if removed > 0:
                severities_removed += removed
                updated = True

        # Reconcile service_filter
        if flow.service_filter:
            original_count = len(flow.service_filter)
            flow.service_filter = [s for s in flow.service_filter if s in valid_services]
            removed = original_count - len(flow.service_filter)
            if removed > 0:
                services_removed += removed
                updated = True

        if updated:
            flow.save(update_fields=["category_filter", "severity_filter", "service_filter"])
            flows_updated += 1

    if flows_updated > 0:
        logger.info(
            f"Reconciled filters for profile {profile.name}: "
            f"{flows_updated} flow(s) updated, "
            f"{categories_removed} category filter(s) removed, "
            f"{severities_removed} severity filter(s) removed, "
            f"{services_removed} service filter(s) removed"
        )


register_handler("SignalCreatedEvent", handle_signal_created)
register_handler("SignalUpdatedEvent", handle_signal_updated)
register_handler("DomainProfileUpdatedEvent", handle_domain_profile_updated)
