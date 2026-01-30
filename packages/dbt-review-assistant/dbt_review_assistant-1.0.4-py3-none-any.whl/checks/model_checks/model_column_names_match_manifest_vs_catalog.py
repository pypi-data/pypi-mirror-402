"""Check if the model column names match between the manifest and the catalog."""

from utils.check_failure_messages import (
    manifest_vs_catalog_column_name_mismatch_message,
)
from utils.check_abc import ManifestVsCatalogComparison
from utils.artifact_data import get_json_artifact_data, get_models_from_manifest


class ModelColumnNamesMatchManifestVsCatalog(ManifestVsCatalogComparison):
    """Check if the model column names match between the manifest and the catalog.

    Attributes:
        manifest_items: set of column names from the manifest
        catalog_items: set of column names from the catalog
        check_name: name of the check
        additional_arguments: arguments required in addition to the global arguments
    """

    manifest_items: set[str] = set()
    catalog_items: set[str] = set()
    check_name: str = "model-column-names-match-manifest-vs-catalog"
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
        eligible_models = {
            node["unique_id"]: node
            for node in get_models_from_manifest(
                manifest_dir=self.args.manifest_dir,
                filter_conditions=self.filter_conditions,
            )
            if node.get("config", {}).get("enabled", True)
        }
        self.manifest_items: set[str] = {
            f"{node_name}.{column['name']}"
            for node_name, node in eligible_models.items()
            for column in node["columns"].values()
        }
        self.catalog_items = {
            f"{node['unique_id']}.{column}"
            for node in get_json_artifact_data(self.args.catalog_dir / "catalog.json")[
                "nodes"
            ].values()
            if node["unique_id"] in eligible_models.keys()
            for column in node["columns"]
        }

    @property
    def failure_message(self) -> str:
        """Compile a failure log message."""
        return manifest_vs_catalog_column_name_mismatch_message(
            manifest_columns=self.manifest_items,
            catalog_columns=self.catalog_items,
        )


if __name__ == "__main__":
    ModelColumnNamesMatchManifestVsCatalog()
