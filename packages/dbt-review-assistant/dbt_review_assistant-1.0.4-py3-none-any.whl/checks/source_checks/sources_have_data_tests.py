"""Check sources have data tests."""

from utils.check_failure_messages import object_missing_values_from_set_message
from utils.check_abc import ManifestCheck
from utils.artifact_data import (
    get_json_artifact_data,
    get_sources_from_manifest,
    MANIFEST_FILE_NAME,
)


class SourcesHaveDataTests(ManifestCheck):
    """Check sources have data tests.

    Attributes:
        check_name: name of the check
        additional_arguments: arguments required in addition to the global arguments
    """

    check_name: str = "sources-have-data-tests"
    additional_arguments = [
        "must_have_all_data_tests_from",
        "must_have_any_data_test_from",
        "include_tags",
        "include_packages",
        "include_node_paths",
        "exclude_tags",
        "exclude_packages",
        "exclude_node_paths",
    ]

    def perform_check(self) -> None:
        """Execute the check logic."""
        sources = (
            node["unique_id"]
            for node in get_sources_from_manifest(
                manifest_dir=self.args.manifest_dir,
                filter_conditions=self.filter_conditions,
            )
        )
        failures: dict[str, set[str]] = {}
        manifest_data = get_json_artifact_data(
            self.args.manifest_dir / MANIFEST_FILE_NAME
        )
        for source in sources:
            data_tests = set()
            for child_id in manifest_data["child_map"][source]:
                node_data = manifest_data["nodes"].get(child_id, {})
                if node_data.get("resource_type") == "test":
                    data_tests.add(node_data.get("test_metadata", {}).get("name"))
            if any(
                [
                    # No specific data_tests required
                    (
                        not (
                            self.args.must_have_all_data_tests_from
                            or self.args.must_have_any_data_test_from
                        )
                        and not data_tests
                    ),
                    # Full set of data_tests required
                    (
                        self.args.must_have_all_data_tests_from
                        and not set(self.args.must_have_all_data_tests_from).issubset(
                            data_tests
                        )
                    ),
                    # At least one data_test from set required
                    (
                        self.args.must_have_any_data_test_from
                        and not set(
                            self.args.must_have_any_data_test_from
                        ).intersection(data_tests)
                    ),
                ]
            ):
                failures[source] = data_tests
        self.failures: dict[str, set[str]] = failures

    @property
    def failure_message(self) -> str:
        """Compile a failure log message."""
        return object_missing_values_from_set_message(
            objects=self.failures,
            object_type="source",
            attribute_type="data test",
            must_have_all_from=self.args.must_have_all_data_tests_from,
            must_have_any_from=self.args.must_have_any_data_test_from,
        )


if __name__ == "__main__":
    SourcesHaveDataTests()
