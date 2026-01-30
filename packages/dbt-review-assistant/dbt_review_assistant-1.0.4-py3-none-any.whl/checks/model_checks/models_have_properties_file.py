"""Check if models have a properties YAML file."""

from utils.check_failure_messages import object_missing_attribute_message
from utils.artifact_data import get_models_from_manifest
from utils.check_abc import ManifestCheck


class ModelsHavePropertiesFile(ManifestCheck):
    """Check if models have a properties YAML file.

    Attributes:
        check_name: name of the check
        additional_arguments: arguments required in addition to the global arguments
    """

    check_name: str = "models-have-properties-file"
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

    def perform_check(self):
        """Execute the check logic."""
        self.failures = {
            node["unique_id"]
            for node in get_models_from_manifest(
                manifest_dir=self.args.manifest_dir,
                filter_conditions=self.filter_conditions,
            )
            if not node.get("patch_path")
        }

    @property
    def failure_message(self) -> str:
        """Compile a failure log message."""
        return object_missing_attribute_message(
            missing_attributes=self.failures,
            object_type="model",
            attribute_type="properties YAML file",
        )


if __name__ == "__main__":
    ModelsHavePropertiesFile()
