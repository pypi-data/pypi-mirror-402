"""CHeck if models have a description."""

from utils.check_failure_messages import (
    object_missing_values_from_set_message,
)
from utils.check_abc import ManifestCheck
from utils.artifact_data import get_models_from_manifest, get_tags_for_manifest_object


class ModelsHaveTags(ManifestCheck):
    """CHeck if models have tags.

    Attributes:
        check_name: name of the check
        additional_arguments: arguments required in addition to the global arguments
    """

    check_name: str = "models-have-tags"
    additional_arguments = [
        "must_have_all_tags_from",
        "must_have_any_tag_from",
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
            tags = get_tags_for_manifest_object(model)
            if any(
                [
                    # No specific tags required
                    (
                        not (
                            self.args.must_have_all_tags_from
                            or self.args.must_have_any_tag_from
                        )
                        and not tags
                    ),
                    # Full set of tags required
                    (
                        self.args.must_have_all_tags_from
                        and not set(self.args.must_have_all_tags_from).issubset(tags)
                    ),
                    # At least one tag from set required
                    (
                        self.args.must_have_any_tag_from
                        and not set(self.args.must_have_any_tag_from).intersection(tags)
                    ),
                ]
            ):
                failures[model["unique_id"]] = tags
        self.failures: dict[str, set[str]] = failures

    @property
    def failure_message(self) -> str:
        """Compile a failure log message."""
        return object_missing_values_from_set_message(
            objects=self.failures,
            object_type="model",
            attribute_type="tag",
            must_have_all_from=self.args.must_have_all_tags_from,
            must_have_any_from=self.args.must_have_any_tag_from,
        )
