from __future__ import annotations

import json
from argparse import ArgumentParser
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from nazara.intelligence.domain.models import (
    DomainCategory,
    DomainProfile,
    EnrichmentFlow,
    EnrichmentFlowStep,
    EnrichmentTypeChoices,
    GlossaryTerm,
    InputSourceChoices,
    OperationalPolicy,
    SeverityLevel,
    SystemCatalogEntry,
    SystemTypeChoices,
    TargetTypeChoices,
)


class ValidationError(Exception):
    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__(f"Validation failed with {len(errors)} error(s)")


class Command(BaseCommand):
    help = "Import a DomainProfile from a JSON file"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "json_file",
            type=str,
            help="Path to the JSON file containing the domain profile",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate JSON without importing",
        )
        parser.add_argument(
            "--update",
            action="store_true",
            help="Update existing profile if name matches (default: fail on conflict)",
        )
        parser.add_argument(
            "--activate",
            action="store_true",
            help="Set profile as active after import",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Skip confirmation prompts",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        json_file = Path(options["json_file"])
        dry_run = options["dry_run"]
        update = options["update"]
        activate = options["activate"]
        force = options["force"]

        # Load and parse JSON
        try:
            data = self._load_json(json_file)
        except FileNotFoundError as e:
            raise CommandError(f"File not found: {json_file}") from e
        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid JSON: {e}") from e

        # Validate structure
        try:
            self._validate(data)
        except ValidationError as e:
            self.stderr.write(self.style.ERROR("Validation errors:"))
            for error in e.errors:
                self.stderr.write(self.style.ERROR(f"  - {error}"))
            raise CommandError("Validation failed") from e

        # Check for existing profile
        profile_name = data["name"]
        existing = DomainProfile.objects.filter(name=profile_name).first()

        if existing and not update:
            raise CommandError(
                f"Profile '{profile_name}' already exists. Use --update to replace it."
            )

        # Show preview
        self._show_preview(data, existing is not None, dry_run)

        # Confirm if not forced
        if not dry_run and not force:
            action = "update" if existing else "create"
            confirm = input(f"\nProceed to {action} profile? [y/N]: ")
            if confirm.lower() != "y":
                self.stdout.write(self.style.WARNING("Aborted."))
                return

        # Dry run stops here
        if dry_run:
            self.stdout.write(self.style.SUCCESS("\n✓ Validation passed (dry run)"))
            return

        # Import
        try:
            profile = self._import_profile(data, existing, activate)
            self.stdout.write(
                self.style.SUCCESS(f"\n✓ Profile '{profile.name}' imported successfully")
            )
            if activate:
                self.stdout.write(self.style.SUCCESS("  Profile set as active"))
        except Exception as e:
            raise CommandError(f"Import failed: {e}") from e

    def _load_json(self, path: Path) -> dict[str, Any]:
        with open(path, encoding="utf-8") as f:
            result: dict[str, Any] = json.load(f)
            return result

    def _validate(self, data: dict[str, Any]) -> None:
        errors: list[str] = []

        # Required fields
        if "name" not in data or not data["name"]:
            errors.append("'name' is required and cannot be empty")

        # Validate severities
        severities = data.get("severities", [])
        seen_ranks: set[int] = set()
        seen_severity_keys: set[str] = set()
        for i, sev in enumerate(severities):
            if "key" not in sev:
                errors.append(f"severities[{i}]: 'key' is required")
            elif sev["key"] in seen_severity_keys:
                errors.append(f"severities[{i}]: duplicate key '{sev['key']}'")
            else:
                seen_severity_keys.add(sev["key"])

            if "rank" not in sev:
                errors.append(f"severities[{i}]: 'rank' is required")
            elif not isinstance(sev["rank"], int) or sev["rank"] < 0:
                errors.append(f"severities[{i}]: 'rank' must be a non-negative integer")
            elif sev["rank"] in seen_ranks:
                errors.append(f"severities[{i}]: duplicate rank {sev['rank']}")
            else:
                seen_ranks.add(sev["rank"])

        # Validate categories
        seen_category_keys: set[str] = set()
        for i, cat in enumerate(data.get("categories", [])):
            if "key" not in cat:
                errors.append(f"categories[{i}]: 'key' is required")
            elif cat["key"] in seen_category_keys:
                errors.append(f"categories[{i}]: duplicate key '{cat['key']}'")
            else:
                seen_category_keys.add(cat["key"])

        # Validate systems
        valid_entry_types = {c.value for c in SystemTypeChoices}
        seen_system_keys: set[str] = set()
        for i, sys in enumerate(data.get("systems", [])):
            if "key" not in sys:
                errors.append(f"systems[{i}]: 'key' is required")
            elif sys["key"] in seen_system_keys:
                errors.append(f"systems[{i}]: duplicate key '{sys['key']}'")
            else:
                seen_system_keys.add(sys["key"])

            entry_type = sys.get("entry_type", "service")
            if entry_type not in valid_entry_types:
                errors.append(
                    f"systems[{i}]: invalid entry_type '{entry_type}'. "
                    f"Valid: {sorted(valid_entry_types)}"
                )

        # Validate glossary
        seen_terms: set[str] = set()
        for i, term in enumerate(data.get("glossary", [])):
            if "term" not in term:
                errors.append(f"glossary[{i}]: 'term' is required")
            elif term["term"] in seen_terms:
                errors.append(f"glossary[{i}]: duplicate term '{term['term']}'")
            else:
                seen_terms.add(term["term"])

            if "definition" not in term:
                errors.append(f"glossary[{i}]: 'definition' is required")

        # Validate operational policies
        seen_policy_keys: set[str] = set()
        for i, policy in enumerate(data.get("operational_policies", [])):
            if "key" not in policy:
                errors.append(f"operational_policies[{i}]: 'key' is required")
            elif policy["key"] in seen_policy_keys:
                errors.append(f"operational_policies[{i}]: duplicate key '{policy['key']}'")
            else:
                seen_policy_keys.add(policy["key"])

            if "statement" not in policy:
                errors.append(f"operational_policies[{i}]: 'statement' is required")

        # Validate enrichment flows
        valid_target_types = {c.value for c in TargetTypeChoices}
        valid_enrichment_types = {c.value for c in EnrichmentTypeChoices}
        valid_input_sources = {c.value for c in InputSourceChoices}
        seen_flow_combos: set[tuple[str, str]] = set()  # (target_type, name)
        seen_priority_combos: set[tuple[str, int]] = set()  # (target_type, priority)

        for i, flow in enumerate(data.get("enrichment_flows", [])):
            target_type = flow.get("target_type")
            flow_name = flow.get("name")
            priority = flow.get("priority", 0)

            if not target_type:
                errors.append(f"enrichment_flows[{i}]: 'target_type' is required")
            elif target_type not in valid_target_types:
                errors.append(
                    f"enrichment_flows[{i}]: invalid target_type '{target_type}'. "
                    f"Valid: {sorted(valid_target_types)}"
                )

            if not flow_name:
                errors.append(f"enrichment_flows[{i}]: 'name' is required")

            if target_type and flow_name:
                combo = (target_type, flow_name)
                if combo in seen_flow_combos:
                    errors.append(
                        f"enrichment_flows[{i}]: duplicate flow name '{flow_name}' "
                        f"for target_type '{target_type}'"
                    )
                else:
                    seen_flow_combos.add(combo)

            if target_type:
                priority_combo = (target_type, priority)
                if priority_combo in seen_priority_combos:
                    errors.append(
                        f"enrichment_flows[{i}]: duplicate priority {priority} "
                        f"for target_type '{target_type}'"
                    )
                else:
                    seen_priority_combos.add(priority_combo)

            # Validate steps
            steps = flow.get("steps", [])
            if not steps:
                errors.append(f"enrichment_flows[{i}]: 'steps' is required and cannot be empty")
            else:
                seen_step_types: set[str] = set()
                for j, step in enumerate(steps):
                    enrichment_type = step.get("enrichment_type")
                    input_source = step.get("input_source", "raw")

                    if not enrichment_type:
                        errors.append(
                            f"enrichment_flows[{i}].steps[{j}]: 'enrichment_type' is required"
                        )
                    elif enrichment_type not in valid_enrichment_types:
                        errors.append(
                            f"enrichment_flows[{i}].steps[{j}]: invalid enrichment_type "
                            f"'{enrichment_type}'. Valid: {sorted(valid_enrichment_types)}"
                        )
                    elif enrichment_type in seen_step_types:
                        errors.append(
                            f"enrichment_flows[{i}].steps[{j}]: duplicate enrichment_type "
                            f"'{enrichment_type}' in flow"
                        )
                    else:
                        seen_step_types.add(enrichment_type)

                    if input_source not in valid_input_sources:
                        errors.append(
                            f"enrichment_flows[{i}].steps[{j}]: invalid input_source "
                            f"'{input_source}'. Valid: {sorted(valid_input_sources)}"
                        )

        if errors:
            raise ValidationError(errors)

    def _show_preview(self, data: dict[str, Any], is_update: bool, dry_run: bool) -> None:
        """Display preview of what will be imported."""
        prefix = "[DRY RUN] Would import:" if dry_run else "Importing:"
        action = "update" if is_update else "create"

        flows = data.get("enrichment_flows", [])
        total_steps = sum(len(f.get("steps", [])) for f in flows)

        self.stdout.write(f"\n{prefix}")
        self.stdout.write(f"  Profile: {data['name']} ({action})")
        self.stdout.write(f"    - {len(data.get('categories', []))} categories")
        self.stdout.write(f"    - {len(data.get('severities', []))} severities")
        self.stdout.write(f"    - {len(data.get('systems', []))} systems")
        self.stdout.write(f"    - {len(data.get('glossary', []))} glossary terms")
        self.stdout.write(f"    - {len(data.get('operational_policies', []))} operational policies")
        self.stdout.write(f"    - {len(flows)} enrichment flows ({total_steps} total steps)")

    @transaction.atomic
    def _import_profile(
        self,
        data: dict[str, Any],
        existing: DomainProfile | None,
        activate: bool,
    ) -> DomainProfile:
        if existing:
            # Update existing - delete all children first
            existing.categories.all().delete()
            existing.severities.all().delete()
            existing.systems.all().delete()
            existing.glossary.all().delete()
            existing.operational_policies.all().delete()
            existing.enrichment_flows.all().delete()

            # Update profile fields
            existing.description = data.get("description", "")
            if activate:
                existing.activate()  # Deactivates others first
            existing.save()
            profile = existing
        else:
            # Create new profile (always inactive initially)
            profile = DomainProfile.objects.create(
                name=data["name"],
                description=data.get("description", ""),
                is_active=False,
            )
            if activate:
                profile.activate()  # Deactivates others first
                profile.save()

        # Create children using bulk_create for efficiency
        self._create_categories(profile, data.get("categories", []))
        self._create_severities(profile, data.get("severities", []))
        self._create_systems(profile, data.get("systems", []))
        self._create_glossary(profile, data.get("glossary", []))
        self._create_operational_policies(profile, data.get("operational_policies", []))
        self._create_enrichment_flows(profile, data.get("enrichment_flows", []))

        return profile

    def _create_categories(self, profile: DomainProfile, items: list[dict[str, Any]]) -> None:
        if not items:
            return
        DomainCategory.objects.bulk_create(
            [
                DomainCategory(
                    profile=profile,
                    key=item["key"],
                    label=item.get("label", item["key"]),
                    description=item.get("description", ""),
                )
                for item in items
            ]
        )

    def _create_severities(self, profile: DomainProfile, items: list[dict[str, Any]]) -> None:
        if not items:
            return
        SeverityLevel.objects.bulk_create(
            [
                SeverityLevel(
                    profile=profile,
                    key=item["key"],
                    label=item.get("label", item["key"]),
                    rank=item["rank"],
                    description=item.get("description", ""),
                )
                for item in items
            ]
        )

    def _create_systems(self, profile: DomainProfile, items: list[dict[str, Any]]) -> None:
        if not items:
            return
        SystemCatalogEntry.objects.bulk_create(
            [
                SystemCatalogEntry(
                    profile=profile,
                    key=item["key"],
                    label=item.get("label", item["key"]),
                    entry_type=item.get("entry_type", SystemTypeChoices.SERVICE),
                    description=item.get("description", ""),
                )
                for item in items
            ]
        )

    def _create_glossary(self, profile: DomainProfile, items: list[dict[str, Any]]) -> None:
        if not items:
            return
        GlossaryTerm.objects.bulk_create(
            [
                GlossaryTerm(
                    profile=profile,
                    term=item["term"],
                    definition=item["definition"],
                    aliases=item.get("aliases", []),
                )
                for item in items
            ]
        )

    def _create_operational_policies(
        self, profile: DomainProfile, items: list[dict[str, Any]]
    ) -> None:
        if not items:
            return
        OperationalPolicy.objects.bulk_create(
            [
                OperationalPolicy(
                    profile=profile,
                    key=item["key"],
                    statement=item["statement"],
                )
                for item in items
            ]
        )

    def _create_enrichment_flows(self, profile: DomainProfile, items: list[dict[str, Any]]) -> None:
        if not items:
            return

        for item in items:
            # Create the flow
            flow = EnrichmentFlow.objects.create(
                profile=profile,
                target_type=item["target_type"],
                name=item["name"],
                priority=item.get("priority", 0),
                enabled=item.get("enabled", True),
                category_filter=item.get("category_filter", []),
                severity_filter=item.get("severity_filter", []),
                service_filter=item.get("service_filter", []),
            )

            # Create steps for the flow
            steps = item.get("steps", [])
            if steps:
                EnrichmentFlowStep.objects.bulk_create(
                    [
                        EnrichmentFlowStep(
                            flow=flow,
                            enrichment_type=step["enrichment_type"],
                            order=step.get("order", idx),
                            input_source=step.get("input_source", InputSourceChoices.RAW),
                        )
                        for idx, step in enumerate(steps)
                    ]
                )
