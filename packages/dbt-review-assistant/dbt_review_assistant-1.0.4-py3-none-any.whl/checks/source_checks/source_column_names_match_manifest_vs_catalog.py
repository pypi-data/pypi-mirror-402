"""Check if the source column names match between the manifest and the catalog."""

from pathlib import Path

from utils.check_abc import ManifestVsCatalogComparison
from utils.artifact_data import get_json_artifact_data, get_sources_from_manifest
from utils.check_failure_messages import (
    manifest_vs_catalog_column_name_mismatch_message,
)


class SourceColumnNamesMatchManifestVsCatalog(ManifestVsCatalogComparison):
    """Check if the source column names match between the manifest and the catalog.

    Attributes:
        manifest_items: set of column names from the manifest
        catalog_items: set of column names from the catalog
        check_name: name of the check
        additional_arguments: arguments required in addition to the global arguments
    """

    manifest_items: set[str] = set()
    catalog_items: set[str] = set()
    check_name: str = "source-column-names-match-manifest-vs-catalog"
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
            f"{node_name}.{column}"
            for node_name, node in eligible_sources.items()
            for column in node["columns"].keys()
        }
        self.catalog_items = {
            f"{source.get('unique_id')}.{column}"
            for source in get_json_artifact_data(
                self.args.catalog_dir / "catalog.json"
            )["sources"].values()
            if source["unique_id"] in eligible_sources.keys()
            for column in source["columns"].keys()
        }

    @property
    def failure_message(self) -> str:
        """Compile a failure log message."""
        return manifest_vs_catalog_column_name_mismatch_message(
            manifest_columns=self.manifest_items,
            catalog_columns=self.catalog_items,
        )


if __name__ == "__main__":
    SourceColumnNamesMatchManifestVsCatalog()
