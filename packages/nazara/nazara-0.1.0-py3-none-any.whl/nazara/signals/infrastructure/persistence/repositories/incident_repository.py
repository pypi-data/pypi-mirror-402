from uuid import UUID

from nazara.signals.domain.contracts.incident_repository import IncidentRepository
from nazara.signals.domain.models import Incident


class DjangoIncidentRepository(IncidentRepository):
    def save(self, incident: Incident) -> tuple[Incident, bool]:
        new_hash = incident.compute_content_hash()

        # Skip if content unchanged (existing record with same hash)
        if not incident._state.adding and incident.content_hash == new_hash:
            return incident, False

        incident.content_hash = new_hash
        incident.save()
        return incident, True

    def get(self, incident_id: UUID) -> Incident | None:
        return Incident.objects.filter(id=incident_id).first()

    def delete(self, incident_id: UUID) -> bool:
        deleted, _ = Incident.objects.filter(id=incident_id).delete()
        return deleted > 0

    def count(
        self,
        status: str | None = None,
        severity: str | None = None,
    ) -> int:
        qs = Incident.objects.all()
        if status:
            qs = qs.filter(status=status)
        if severity:
            qs = qs.filter(severity=severity)
        return qs.count()

    def get_by_source(
        self,
        source_system: str,
        source_identifier: str,
    ) -> Incident | None:
        return Incident.objects.filter(
            source_system=source_system,
            source_identifier=source_identifier,
        ).first()
