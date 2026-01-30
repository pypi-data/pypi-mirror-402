from uuid import UUID

from nazara.signals.domain.contracts.customer_case_repository import CustomerCaseRepository
from nazara.signals.domain.models import CustomerCase


class DjangoCustomerCaseRepository(CustomerCaseRepository):
    def save(self, case: CustomerCase) -> tuple[CustomerCase, bool]:
        new_hash = case.compute_content_hash()

        # Skip if content unchanged (existing record with same hash)
        if not case._state.adding and case.content_hash == new_hash:
            return case, False

        case.content_hash = new_hash
        case.save()
        return case, True

    def delete(self, case_id: UUID) -> bool:
        deleted, _ = CustomerCase.objects.filter(id=case_id).delete()
        return deleted > 0

    def count(
        self,
        status: str | None = None,
        severity: str | None = None,
    ) -> int:
        qs = CustomerCase.objects.all()
        if status:
            qs = qs.filter(status=status)
        if severity:
            qs = qs.filter(severity=severity)
        return qs.count()

    def get_by_source(
        self,
        source_system: str,
        source_identifier: str,
    ) -> CustomerCase | None:
        return CustomerCase.objects.filter(
            source_system=source_system,
            source_identifier=source_identifier,
        ).first()
