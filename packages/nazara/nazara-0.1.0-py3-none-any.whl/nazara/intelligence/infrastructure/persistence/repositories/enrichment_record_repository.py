from uuid import UUID

from nazara.intelligence.domain.contracts.enrichment_record_repository import (
    EnrichmentRecordRepository,
)
from nazara.intelligence.domain.models import EnrichmentRecord


class DjangoEnrichmentRecordRepository(EnrichmentRecordRepository):
    def get(
        self,
        target_type: str,
        target_id: UUID,
        enrichment_type: str,
    ) -> EnrichmentRecord | None:
        return EnrichmentRecord.objects.filter(
            target_type=target_type,
            target_id=target_id,
            enrichment_type=enrichment_type,
        ).first()

    def list(
        self,
        target_type: str,
        target_id: UUID,
        status: str | None = "success",
    ) -> list[EnrichmentRecord]:
        qs = EnrichmentRecord.objects.filter(
            target_type=target_type,
            target_id=target_id,
        )
        if status:
            qs = qs.filter(status=status)
        return list(qs)

    def save(self, record: EnrichmentRecord) -> EnrichmentRecord:
        record.save()
        return record
