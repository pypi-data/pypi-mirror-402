"""Check if models have at least one unit test."""

from utils.check_failure_messages import object_missing_attribute_message
from utils.check_abc import ManifestCheck
from utils.artifact_data import (
    get_models_from_manifest,
    get_json_artifact_data,
    MANIFEST_FILE_NAME,
)


class ModelsHaveUnitTests(ManifestCheck):
    """Check if models have at least one unit test.

    Attributes:
        check_name: name of the check
        additional_arguments: arguments required in addition to the global arguments
    """

    check_name: str = "models-have-unit-tests"
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
        models = (
            node["unique_id"]
            for node in get_models_from_manifest(
                manifest_dir=self.args.manifest_dir,
                filter_conditions=self.filter_conditions,
            )
        )
        models_without_required_unit_tests: set[str] = set()
        unit_tests = {}
        manifest_data = get_json_artifact_data(
            self.args.manifest_dir / MANIFEST_FILE_NAME
        )
        for model in models:
            unit_tests[model] = False
            for child_id in manifest_data["child_map"][model]:
                unit_test_data = manifest_data["unit_tests"].get(child_id)
                if unit_test_data:
                    unit_tests[model] = True
            if not unit_tests[model]:
                models_without_required_unit_tests.add(model)
        self.failures = models_without_required_unit_tests

    @property
    def failure_message(self) -> str:
        """Compile a failure log message."""
        return object_missing_attribute_message(
            missing_attributes=self.failures,
            object_type="model",
            attribute_type="unit test",
        )


if __name__ == "__main__":
    ModelsHaveUnitTests()
