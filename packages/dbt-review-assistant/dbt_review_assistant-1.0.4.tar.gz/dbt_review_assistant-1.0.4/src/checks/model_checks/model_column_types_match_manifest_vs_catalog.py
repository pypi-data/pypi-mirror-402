"""Check if the model column types match between the manifest and the catalog."""

from utils.check_failure_messages import (
    manifest_vs_catalog_column_type_mismatch_message,
)
from utils.check_abc import ManifestVsCatalogComparison
from utils.artifact_data import get_json_artifact_data, get_models_from_manifest


class ModelColumnTypesMatchManifestVsCatalog(ManifestVsCatalogComparison):
    """Check if the model column types match between the manifest and the catalog.

    Attributes:
        manifest_items: dict of column names and types from the manifest
        catalog_items: dict of column names and types from the catalog
        check_name: name of the check
        additional_arguments: arguments required in addition to the global arguments
    """

    manifest_items: dict[str, str] = {}
    catalog_items: dict[str, str] = {}
    check_name: str = "model-column-types-match-manifest-vs-catalog"
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
        self.filter_conditions.exclude_materializations = (
            set(self.args.exclude_materializations + ["ephemeral"])
            if self.args.exclude_materializations
            else {"ephemeral"}
        )
        eligible_models = {
            node["unique_id"]: node
            for node in get_models_from_manifest(
                manifest_dir=self.args.manifest_dir,
                filter_conditions=self.filter_conditions,
            )
            if node.get("config", {}).get("enabled", True)
        }
        self.manifest_items = {
            f"{node_name}.{column_name}": column_data.get("data_type")
            for node_name, node in eligible_models.items()
            for column_name, column_data in node["columns"].items()
        }
        self.catalog_items = {
            f"{node['unique_id']}.{column_name}": column_data["type"]
            for node in get_json_artifact_data(self.args.catalog_dir / "catalog.json")[
                "nodes"
            ].values()
            if node["unique_id"] in eligible_models.keys()
            for column_name, column_data in node["columns"].items()
        }

    @property
    def failure_message(self) -> str:
        """Compile a failure log message."""
        return manifest_vs_catalog_column_type_mismatch_message(
            manifest_columns=self.manifest_items,
            catalog_columns=self.catalog_items,
        )


if __name__ == "__main__":
    ModelColumnTypesMatchManifestVsCatalog()
