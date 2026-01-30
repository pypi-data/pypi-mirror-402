from nazara.intelligence.domain.step_registry import get_step_class


class FlowValidationError(Exception):
    """Raised when flow configuration is invalid."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__(f"Flow validation failed: {errors}")


def validate_flow_steps(steps: list[str]) -> list[str]:
    """
    Validate that flow step order satisfies intrinsic dependencies.

    Called at EnrichmentFlow save time to catch misconfiguration early.

    Args:
        steps: Ordered list of enrichment_type keys (e.g., ["summary.v1", "embedding.v1"])

    Returns:
        List of validation error messages (empty if valid)
    """
    errors: list[str] = []
    seen_base_keys: set[str] = set()

    for enrichment_type in steps:
        base_key = enrichment_type.split(".")[0]

        step_cls = get_step_class(base_key)
        if step_cls is None:
            errors.append(f"Unknown step type: {enrichment_type}")
            continue

        # requires is a class variable, so we can access it directly on the class
        for req in step_cls.requires:
            if req not in seen_base_keys:
                errors.append(f"'{enrichment_type}' requires '{req}' to run before it")

        seen_base_keys.add(base_key)

    return errors
