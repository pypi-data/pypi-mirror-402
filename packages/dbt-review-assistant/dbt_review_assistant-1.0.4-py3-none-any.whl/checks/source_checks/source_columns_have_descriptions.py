"""Check if source columns have descriptions."""

from utils.check_failure_messages import object_missing_attribute_message
from utils.check_abc import ManifestCheck
from utils.artifact_data import get_sources_from_manifest


class SourceColumnsHaveDescriptions(ManifestCheck):
    """Check if source columns have descriptions.

    Attributes:
        check_name: name of the check
        additional_arguments: arguments required in addition to the global arguments
    """

    check_name: str = "source-columns-have-descriptions"
    additional_arguments = [
        "include_tags",
        "include_packages",
        "include_node_paths",
        "exclude_tags",
        "exclude_packages",
        "exclude_node_paths",
    ]

    def perform_check(self) -> None:
        """Execute the check logic."""
        self.failures = {
            f"{node['unique_id']}.{column['name']}"
            for node in get_sources_from_manifest(
                manifest_dir=self.args.manifest_dir,
                filter_conditions=self.filter_conditions,
            )
            for column in node.get("columns", {"_": {}}).values()
            if not column.get("description")
        }

    @property
    def failure_message(self) -> str:
        """Compile a failure log message."""
        return object_missing_attribute_message(
            missing_attributes=self.failures,
            object_type="source column",
            attribute_type="description",
        )


if __name__ == "__main__":
    SourceColumnsHaveDescriptions()
