import logging
import time
from typing import Any
from uuid import UUID

from nazara.intelligence.domain.contracts.enrichment_record_repository import (
    EnrichmentRecordRepository,
)
from nazara.intelligence.domain.contracts.step import EnrichmentStep
from nazara.intelligence.domain.models import (
    DomainProfile,
    EnrichmentFlow,
    EnrichmentRecord,
    EnrichmentStatusChoices,
)

logger = logging.getLogger(__name__)


class EnrichmentError(Exception):
    pass


class SignalNotFoundError(EnrichmentError):
    pass


class NoActiveProfileError(EnrichmentError):
    pass


class NoActiveFlowError(EnrichmentError):
    pass


class BaseEnrichService:
    def __init__(
        self,
        steps: dict[str, EnrichmentStep],
        enrichment_repository: EnrichmentRecordRepository,
    ):
        self._steps = steps
        self._enrichment_repo = enrichment_repository

    def _get_step(self, enrichment_type: str) -> EnrichmentStep | None:
        base_key = enrichment_type.split(".")[0]
        return self._steps.get(base_key)

    def _execute_flow(
        self,
        signal: Any,
        flow: EnrichmentFlow,
        force: bool = False,
    ) -> dict[str, Any]:
        """
        Execute enrichment flow for a signal.

        Iterates flow steps in order, passing dependent_outputs between steps.
        This enables sequential execution where embedding uses summary output.
        """
        results: dict[str, Any] = {}
        dependent_outputs: dict[str, dict[str, Any]] = {}

        flow_steps = flow.flow_steps.order_by("order")

        for flow_step in flow_steps:
            enrichment_type = flow_step.enrichment_type

            step = self._get_step(enrichment_type)
            if step is None or not step.is_available():
                results[enrichment_type] = {"skipped": "step unavailable"}
                continue

            context = {
                "enrichment_type": enrichment_type,
                "dependent_outputs": dependent_outputs,
                "input_source": flow_step.input_source,
            }

            record = self._get_or_create_record(
                signal_id=signal.id,
                target_type=flow.target_type,
                enrichment_type=enrichment_type,
            )

            should_run, reason = step.should_run(signal, record, context, force)
            if not should_run:
                results[enrichment_type] = {"skipped": reason}
                if record.result:
                    dependent_outputs[enrichment_type] = record.result
                continue

            step_result = self._execute_step(
                step=step,
                signal=signal,
                profile=flow.profile,
                record=record,
                context=context,
            )

            results[enrichment_type] = step_result

            if step_result.get("status") == "success" and record.result:
                dependent_outputs[enrichment_type] = record.result

        return results

    def _get_or_create_record(
        self,
        signal_id: UUID,
        target_type: str,
        enrichment_type: str,
    ) -> EnrichmentRecord:
        record = self._enrichment_repo.get(target_type, signal_id, enrichment_type)
        if record is None:
            record = EnrichmentRecord(
                target_type=target_type,
                target_id=signal_id,
                enrichment_type=enrichment_type,
                input_hash="",
                status=EnrichmentStatusChoices.FAILED,
                attempts=0,
            )
        return record

    def _execute_step(
        self,
        step: EnrichmentStep,
        signal: Any,
        profile: DomainProfile,
        record: EnrichmentRecord,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "enrichment_type": context["enrichment_type"],
            "status": "pending",
        }

        start_time = time.time()
        record.attempts += 1
        record.input_hash = step.compute_input_hash(signal, context)

        try:
            step_result = step.execute(signal, profile, context)
            duration_ms = int((time.time() - start_time) * 1000)

            if step_result.success:
                record.status = EnrichmentStatusChoices.SUCCESS
                record.error = ""

                if step_result.output:
                    record.result = step_result.output

                if step_result.embedding:
                    record.embedding = step_result.embedding

                result["status"] = "success"
            else:
                record.status = EnrichmentStatusChoices.FAILED
                record.error = step_result.error or "Unknown error"
                result["status"] = "failed"
                result["error"] = step_result.error

            record.duration_ms = duration_ms
            result["duration_ms"] = duration_ms

            self._enrichment_repo.save(record)

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            record.status = EnrichmentStatusChoices.FAILED
            record.duration_ms = duration_ms
            record.error = str(e)
            self._enrichment_repo.save(record)

            result["status"] = "failed"
            result["error"] = str(e)
            logger.error(f"Step execution failed for {signal.id}: {e}")

        return result


class EnrichIncident(BaseEnrichService):
    def enrich(self, incident_id: UUID, force: bool = False) -> dict[str, Any]:
        from nazara.signals.domain.models import Incident

        logger.info(f"Starting enrichment for Incident:{incident_id} (force={force})")

        results: dict[str, Any] = {
            "target_type": "Incident",
            "target_id": str(incident_id),
            "enrichments": {},
            "status": "success",
        }

        try:
            incident = Incident.objects.get(id=incident_id)
        except Incident.DoesNotExist:
            logger.warning(f"Incident not found: {incident_id}")
            results["status"] = "failed"
            results["error"] = "Incident not found"
            return results

        flow = self._get_active_flow(incident)
        if flow is None:
            logger.info(f"No active enrichment flow for Incident:{incident_id}")
            results["status"] = "skipped"
            results["reason"] = "no_active_flow"
            return results

        results["enrichments"] = self._execute_flow(incident, flow, force)
        return results

    def _get_active_flow(self, incident: Any) -> EnrichmentFlow | None:
        profile = DomainProfile.objects.filter(is_active=True).first()
        if profile is None:
            return None

        flows = EnrichmentFlow.objects.filter(
            profile=profile,
            target_type="Incident",
            enabled=True,
        ).order_by("-priority")

        for flow in flows:
            if flow.matches(
                category=getattr(incident, "category", None),
                severity=getattr(incident, "severity", None),
                service=getattr(incident, "service", None),
            ):
                logger.info(
                    f"Incident {incident.id} matched flow '{flow.name}' (priority={flow.priority})"
                )
                return flow

        logger.info(f"No matching flow for Incident:{incident.id}")
        return None


class EnrichCustomerCase(BaseEnrichService):
    def enrich(self, case_id: UUID, force: bool = False) -> dict[str, Any]:
        from nazara.signals.domain.models import CustomerCase

        logger.info(f"Starting enrichment for CustomerCase:{case_id} (force={force})")

        results: dict[str, Any] = {
            "target_type": "CustomerCase",
            "target_id": str(case_id),
            "enrichments": {},
            "status": "success",
        }

        try:
            case = CustomerCase.objects.get(id=case_id)
        except CustomerCase.DoesNotExist:
            logger.warning(f"CustomerCase not found: {case_id}")
            results["status"] = "failed"
            results["error"] = "CustomerCase not found"
            return results

        flow = self._get_active_flow(case)
        if flow is None:
            logger.info(f"No active enrichment flow for CustomerCase:{case_id}")
            results["status"] = "skipped"
            results["reason"] = "no_active_flow"
            return results

        results["enrichments"] = self._execute_flow(case, flow, force)
        return results

    def _get_active_flow(self, case: Any) -> EnrichmentFlow | None:
        profile = DomainProfile.objects.filter(is_active=True).first()
        if profile is None:
            return None

        flows = EnrichmentFlow.objects.filter(
            profile=profile,
            target_type="CustomerCase",
            enabled=True,
        ).order_by("-priority")

        for flow in flows:
            if flow.matches(
                category=getattr(case, "category", None),
                severity=getattr(case, "severity", None),
                service=getattr(case, "service", None),
            ):
                logger.info(
                    f"CustomerCase {case.id} matched flow '{flow.name}' (priority={flow.priority})"
                )
                return flow

        logger.info(f"No matching flow for CustomerCase:{case.id}")
        return None


class EnrichTechnicalIssue(BaseEnrichService):
    def enrich(self, issue_id: UUID, force: bool = False) -> dict[str, Any]:
        from nazara.signals.domain.models import TechnicalIssue

        logger.info(f"Starting enrichment for TechnicalIssue:{issue_id} (force={force})")

        results: dict[str, Any] = {
            "target_type": "TechnicalIssue",
            "target_id": str(issue_id),
            "enrichments": {},
            "status": "success",
        }

        try:
            issue = TechnicalIssue.objects.get(id=issue_id)
        except TechnicalIssue.DoesNotExist:
            logger.warning(f"TechnicalIssue not found: {issue_id}")
            results["status"] = "failed"
            results["error"] = "TechnicalIssue not found"
            return results

        flow = self._get_active_flow(issue)
        if flow is None:
            logger.info(f"No active enrichment flow for TechnicalIssue:{issue_id}")
            results["status"] = "skipped"
            results["reason"] = "no_active_flow"
            return results

        results["enrichments"] = self._execute_flow(issue, flow, force)
        return results

    def _get_active_flow(self, issue: Any) -> EnrichmentFlow | None:
        profile = DomainProfile.objects.filter(is_active=True).first()
        if profile is None:
            return None

        flows = EnrichmentFlow.objects.filter(
            profile=profile,
            target_type="TechnicalIssue",
            enabled=True,
        ).order_by("-priority")

        for flow in flows:
            if flow.matches(
                category=getattr(issue, "category", None),
                severity=getattr(issue, "severity", None),
                service=getattr(issue, "service", None),
            ):
                logger.info(
                    f"TechnicalIssue {issue.id} matched flow '{flow.name}' "
                    f"(priority={flow.priority})"
                )
                return flow

        logger.info(f"No matching flow for TechnicalIssue:{issue.id}")
        return None
