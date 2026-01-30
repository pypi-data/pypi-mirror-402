"""Check if model columns have descriptions."""

from utils.check_failure_messages import (
    object_missing_attribute_message,
    inconsistent_column_descriptions_message,
)
from utils.check_abc import Check
from utils.artifact_data import get_models_from_manifest


class ModelColumnsDescriptionsAreConsistent(Check):
    """Check if column descriptions are consistent across different models.

    Attributes:
        descriptions: dict mapping column names to a list of occurrence instance dicts,
        including the name of the model and the description in that model
        check_name: name of the check
        additional_arguments: arguments required in addition to the global arguments
    """

    descriptions: dict[str, list[dict[str, str]]] = {}
    check_name: str = "model-column-descriptions-are-consistent"
    additional_arguments = [
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
        all_descriptions: dict[str, list[dict[str, str]]] = {}
        models = get_models_from_manifest(
            manifest_dir=self.args.manifest_dir,
            filter_conditions=self.filter_conditions,
        )
        for model in models:
            for column in model.get("columns", {"_": {}}).values():
                if not all_descriptions.get(column["name"]):
                    all_descriptions[column["name"]] = []
                all_descriptions[column["name"]].append(
                    {
                        "description": column.get("description"),
                        "model": model["unique_id"],
                    }
                )
        self.descriptions = {
            column_name: sorted(column_instances, key=lambda x: x["model"])
            for column_name, column_instances in all_descriptions.items()
            if len({instance["description"] for instance in column_instances}) > 1
        }

    @property
    def has_failures(self) -> bool:
        """Determine whether any entities failed the check."""
        return bool(self.descriptions)

    @property
    def failure_message(self) -> str:
        """Compile a failure log message."""
        return inconsistent_column_descriptions_message(
            descriptions=self.descriptions,
        )


if __name__ == "__main__":
    ModelColumnsDescriptionsAreConsistent()
