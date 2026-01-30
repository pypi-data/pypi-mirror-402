"""Check if the source column types match between the manifest and the catalog."""

from utils.check_abc import ManifestVsCatalogComparison
from utils.artifact_data import get_json_artifact_data, get_sources_from_manifest
from utils.check_failure_messages import (
    manifest_vs_catalog_column_type_mismatch_message,
)


class SourceColumnTypesMatchManifestVsCatalog(ManifestVsCatalogComparison):
    """Check if the source column types match between the manifest and the catalog.

    Attributes:
        manifest_items: dict of column names and types from the manifest
        catalog_items: dict of column names and types from the catalog
        check_name: name of the check
        additional_arguments: arguments required in addition to the global arguments
    """

    manifest_items: dict[str, str] = {}
    catalog_items: dict[str, str] = {}
    check_name: str = "source-column-types-match-manifest-vs-catalog"
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
        eligible_sources = {
            node["unique_id"]: node
            for node in get_sources_from_manifest(
                manifest_dir=self.args.manifest_dir,
                filter_conditions=self.filter_conditions,
            )
            if node.get("config", {}).get("enabled", True)
        }
        self.manifest_items = {
            f"{node_name}.{column['name']}": column.get("data_type")
            for node_name, node in eligible_sources.items()
            for column in node["columns"].values()
        }
        self.catalog_items = {
            f"{source.get('unique_id')}.{column_name}": column_data["type"]
            for source in get_json_artifact_data(
                self.args.catalog_dir / "catalog.json"
            )["sources"].values()
            if source["unique_id"] in eligible_sources.keys()
            for column_name, column_data in source["columns"].items()
        }

    @property
    def failure_message(self) -> str:
        """Compile a failure log message."""
        return manifest_vs_catalog_column_type_mismatch_message(
            manifest_columns=self.manifest_items,
            catalog_columns=self.catalog_items,
        )


if __name__ == "__main__":
    SourceColumnTypesMatchManifestVsCatalog()
