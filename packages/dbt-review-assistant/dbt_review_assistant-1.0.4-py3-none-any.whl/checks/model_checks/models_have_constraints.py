"""Check if models have constraints."""

from typing import Collection

from utils.check_failure_messages import (
    object_missing_attribute_message,
    object_missing_values_from_set_message,
)
from utils.check_abc import ManifestCheck
from utils.artifact_data import get_models_from_manifest


class ModelsHaveConstraints(ManifestCheck):
    """Check if models have constraints.

    Attributes:
        check_name: name of the check
        additional_arguments: arguments required in addition to the global arguments
    """

    check_name: str = "models-have-constraints"
    additional_arguments = [
        "must_have_all_constraints_from",
        "must_have_any_constraint_from",
        "include_materializations",
        "include_tags",
        "include_packages",
        "include_node_paths",
        "exclude_materializations",
        "exclude_tags",
        "exclude_packages",
        "exclude_node_paths",
    ]

    def perform_check(self) -> None:
        """Execute the check logic."""
        failures: dict[str, set[str]] = {}
        for model in get_models_from_manifest(
            manifest_dir=self.args.manifest_dir,
            filter_conditions=self.filter_conditions,
        ):
            constraints = {
                constraint["type"] for constraint in model.get("constraints", [])
            }
            constraints.update(
                {
                    constraint["type"]
                    for column_data in model.get("columns", {}).values()
                    for constraint in column_data.get("constraints", [])
                }
            )
            if any(
                [
                    # No specific constraints required
                    (
                        not (
                            self.args.must_have_all_constraints_from
                            or self.args.must_have_any_constraint_from
                        )
                        and not constraints
                    ),
                    # Full set of constraints required
                    (
                        self.args.must_have_all_constraints_from
                        and not set(self.args.must_have_all_constraints_from).issubset(
                            constraints
                        )
                    ),
                    # At least one constraint from set required
                    (
                        self.args.must_have_any_constraint_from
                        and not set(
                            self.args.must_have_any_constraint_from
                        ).intersection(constraints)
                    ),
                ]
            ):
                failures[model["unique_id"]] = constraints
        self.failures: dict[str, set[str]] = failures

    @property
    def failure_message(self) -> str:
        """Compile a failure log message."""
        return object_missing_values_from_set_message(
            objects=self.failures,
            object_type="model",
            attribute_type="constraint",
            must_have_all_from=self.args.must_have_all_constraints_from,
            must_have_any_from=self.args.must_have_any_constraint_from,
        )


if __name__ == "__main__":
    ModelsHaveConstraints()
