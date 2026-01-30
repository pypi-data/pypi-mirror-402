"""Utilities for fetching dbt artifact data."""

import json
from pathlib import Path
from typing import Iterable, Any, Collection, Generator
from functools import lru_cache

from utils.console_formatting import colour_message, ConsoleEmphasis


MANIFEST_FILE_NAME = "manifest.json"


class ManifestFilterConditions:
    """Conditions to filter manifest objects by.

    Attributes:
        include_materializations: materialization types to be included. Only applicable to models.
        exclude_materializations: materialization types to be excluded. Only applicable to models.
        include_packages: dbt packages to be included.
        exclude_packages: dbt packages to be excluded.
        include_tags: tags to be included.
        exclude_tags: tags to be excluded.
        include_node_paths: node paths to be included.
        exclude_node_paths: node paths to be excluded.
    """

    def __init__(
        self,
        include_materializations: Collection[str] | None = None,
        include_tags: Collection[str] | None = None,
        include_packages: Collection[str] | None = None,
        include_node_paths: Collection[Path] | None = None,
        exclude_materializations: Collection[str] | None = None,
        exclude_tags: Collection[str] | None = None,
        exclude_packages: Collection[str] | None = None,
        exclude_node_paths: Collection[Path] | None = None,
    ) -> None:
        """Initialize the instance.

        Args:
            include_materializations: materialization types to be included. Only applicable to models.
            exclude_materializations: materialization types to be excluded. Only applicable to models.
            include_packages: dbt packages to be included.
            exclude_packages: dbt packages to be excluded.
            include_tags: tags to be included.
            exclude_tags: tags to be excluded.
            include_node_paths: node paths to be included.
            exclude_node_paths: node paths to be excluded.
        """
        self.include_materializations = (
            set(include_materializations) if include_materializations else None
        )
        self.include_tags = set(include_tags) if include_tags else None
        self.include_packages = set(include_packages) if include_packages else None
        self.include_node_paths = (
            set(include_node_paths) if include_node_paths else None
        )
        self.exclude_materializations = (
            set(exclude_materializations) if exclude_materializations else None
        )
        self.exclude_tags = set(exclude_tags) if exclude_tags else None
        self.exclude_packages = set(exclude_packages) if exclude_packages else None
        self.exclude_node_paths = (
            set(exclude_node_paths) if exclude_node_paths else None
        )

    @property
    def summary(self) -> str:
        """Summarise all the filter conditions in a block of text."""
        includes: list[str] = []
        excludes: list[str] = []
        if self.include_materializations:
            includes.append(
                f"materialized: {', '.join(sorted(self.include_materializations))}"
            )
        if self.include_tags:
            includes.append(f"tags: {', '.join(sorted(self.include_tags))}")
        if self.include_packages:
            includes.append(f"packages: {', '.join(sorted(self.include_packages))}")
        if self.include_node_paths:
            includes.append(
                f"node paths: {', '.join(sorted(path.as_posix() for path in self.include_node_paths))}"
            )
        if self.exclude_materializations:
            excludes.append(
                f"materialized: {', '.join(sorted(self.exclude_materializations))}"
            )
        if self.exclude_tags:
            excludes.append(f"tags: {', '.join(sorted(self.exclude_tags))}")
        if self.exclude_packages:
            excludes.append(f"packages: {', '.join(sorted(self.exclude_packages))}")
        if self.exclude_node_paths:
            excludes.append(
                f"node paths: {', '.join(sorted(path.as_posix() for path in self.exclude_node_paths))}"
            )
        return colour_message(
            ""
            + ("Including:\n\t" + "\n\t".join(includes) if includes else "")
            + ("\nExcluding:\n\t" + "\n\t".join(excludes) if excludes else ""),
            emphasis=ConsoleEmphasis.ITALIC,
        )

    def __eq__(self, other: Any) -> bool:
        """Test for equality of ManifestFilterConditions instances."""
        if not isinstance(other, ManifestFilterConditions):
            return False
        return all(
            getattr(self, attr) == getattr(other, attr)
            for attr in [
                "include_materializations",
                "include_tags",
                "include_packages",
                "include_node_paths",
                "exclude_materializations",
                "exclude_tags",
                "exclude_packages",
                "exclude_node_paths",
            ]
        )


@lru_cache
def get_json_artifact_data(artifact_path: Path) -> dict:
    """Load data from a dbt JSON artifact.

    Args:
        artifact_path: Path to the dbt JSON artifact

    Returns:
        dbt artifact data as a dictionary

    Raises:
        FileNotFoundError: If artifact path does not exist
    """
    if not artifact_path.exists():
        raise FileNotFoundError(f"Path {artifact_path.absolute()} does not exist.")
    with open(artifact_path, "r") as file_handler:
        data = json.load(file_handler)
    return data


def filter_nodes_by_package(
    nodes: Iterable[dict[str, Any]],
    include_packages: Collection[str] | None = None,
    exclude_packages: Collection[str] | None = None,
) -> Generator[dict[str, Any], None, None]:
    """Filter nodes by package name.

    Args:
        nodes: Sequence of nodes dictionaries from the manifest
        include_packages: Collection of package names to be included
        exclude_packages: Collection of package names to be excluded

    Returns:
        Generator of node dictionaries from the manifest
    """
    yield from (
        node
        for node in nodes
        if (include_packages is None or node.get("package_name") in include_packages)
        and (
            exclude_packages is None or node.get("package_name") not in exclude_packages
        )
    )


def get_tags_for_manifest_object(manifest_object: dict[str, Any]) -> set[str]:
    """Get all tags for a given manifest object.

    Args:
        manifest_object: dict of dbt manifest object data

    Returns:
        set of tag values
    """
    manifest_tags = manifest_object.get("tags", [])
    if isinstance(manifest_tags, str):
        manifest_tags = [manifest_tags]
    config_tags = manifest_object.get("config", {}).get("tags", [])
    if isinstance(config_tags, str):
        config_tags = [config_tags]
    return set(manifest_tags + config_tags)


def filter_nodes_by_tag(
    nodes: Iterable[dict[str, Any]],
    include_tags: Collection[str] | None = None,
    exclude_tags: Collection[str] | None = None,
) -> Generator[dict[str, Any], None, None]:
    """Filter nodes by tag values.

    Args:
        nodes: Sequence of nodes dictionaries from the manifest
        include_tags: Collection of tag values to be included
        exclude_tags: Collection of tag values to be excluded

    Returns:
        Generator of node dictionaries from the manifest
    """
    yield from (
        node
        for node in nodes
        if (
            include_tags is None
            or set(get_tags_for_manifest_object(node)).intersection(set(include_tags))
        )
        and (
            exclude_tags is None
            or not set(get_tags_for_manifest_object(node)).intersection(
                set(exclude_tags)
            )
        )
    )


def filter_models_by_materialization_type(
    models: Iterable[dict[str, Any]],
    include_materializations: Collection[str] | None = None,
    exclude_materializations: Collection[str] | None = None,
) -> Generator[dict[str, Any], None, None]:
    """Filter nodes by materialization.

    Args:
        models: Sequence of nodes dictionaries from the manifest
        include_materializations: Collection of materializations to be included
        exclude_materializations: Collection of materializations to be excluded

    Returns:
        Generator of model dictionaries from the manifest
    """
    yield from (
        model
        for model in models
        if (
            include_materializations is None
            or model.get("config", {}).get("materialized") in include_materializations
        )
        and (
            exclude_materializations is None
            or model.get("config", {}).get("materialized")
            not in exclude_materializations
        )
    )


def filter_nodes_by_path(
    nodes: Iterable[dict[str, Any]],
    include_paths: Collection[Path] | None = None,
    exclude_paths: Collection[Path] | None = None,
) -> Generator[dict[str, Any], None, None]:
    """Filter nodes by the original filepath, relative to the dbt project directory.

    Args:
        nodes: Sequence of node dictionaries from the manifest
        include_paths: Collection of node paths to be included. Nodes under any of these paths are included.
        exclude_paths: Collection of node paths to be excluded. Nodes under any of these paths are excluded.

    Returns:
        Generator of node dictionaries from the manifest
    """
    yield from (
        node
        for node in nodes
        if (
            include_paths is None
            or any(
                Path(node["original_file_path"]).is_relative_to(path)
                for path in include_paths
            )
        )
        and (
            exclude_paths is None
            or not any(
                Path(node["original_file_path"]).is_relative_to(path)
                for path in exclude_paths
            )
        )
    )


def filter_nodes_by_resource_type(
    nodes: Iterable[dict[str, Any]],
    include_resource_types: Collection[str] | None = None,
    exclude_resource_types: Collection[str] | None = None,
) -> Generator[dict[str, Any], None, None]:
    """Filter nodes by resource type.

    Args:
        nodes: Sequence of nodes dictionaries from the manifest
        include_resource_types: Collection of resource types to be included
        exclude_resource_types: Collection of resource types to be included

    Returns:
        Generator of node dictionaries from the manifest
    """
    yield from (
        node
        for node in nodes
        if (
            include_resource_types is None
            or node["resource_type"] in include_resource_types
        )
        and (
            exclude_resource_types is None
            or node["resource_type"] not in exclude_resource_types
        )
    )


def get_macros_from_manifest(
    manifest_dir: Path,
    filter_conditions: ManifestFilterConditions,
) -> Generator[dict[str, Any], None, None]:
    """Get macros from the dbt manifest file.

    Args:
        manifest_dir: Path to the directory containing the dbt manifest.json
        filter_conditions: ManifestFilterConditions object to filter by

    Yields:
        dictionary of manifest macro data
    """
    return filter_nodes_by_package(
        get_json_artifact_data(manifest_dir / MANIFEST_FILE_NAME)["macros"].values(),
        include_packages=filter_conditions.include_packages,
        exclude_packages=filter_conditions.exclude_packages,
    )


def get_sources_from_manifest(
    manifest_dir: Path,
    filter_conditions: ManifestFilterConditions,
) -> Generator[dict[str, Any], None, None]:
    """Get sources from the dbt manifest file.

    Args:
        manifest_dir: Path to the directory containing the dbt manifest.json
        filter_conditions: ManifestFilterConditions object to filter by

    Yields:
        dictionary of manifest source data
    """
    return filter_nodes_by_path(
        filter_nodes_by_tag(
            filter_nodes_by_package(
                get_json_artifact_data(manifest_dir / MANIFEST_FILE_NAME)[
                    "sources"
                ].values(),
                include_packages=filter_conditions.include_packages,
                exclude_packages=filter_conditions.exclude_packages,
            ),
            include_tags=filter_conditions.include_tags,
            exclude_tags=filter_conditions.exclude_tags,
        ),
        include_paths=filter_conditions.include_node_paths,
        exclude_paths=filter_conditions.exclude_node_paths,
    )


def get_nodes_from_manifest(
    manifest_dir: Path,
    filter_conditions: ManifestFilterConditions,
) -> Generator[dict[str, Any], None, None]:
    """Get nodes from the dbt manifest file.

    Args:
        manifest_dir: Path to the directory containing the dbt manifest.json
        filter_conditions: ManifestFilterConditions object to filter by

    Yields:
        dictionary of manifest node data
    """
    return filter_nodes_by_path(
        filter_nodes_by_tag(
            filter_nodes_by_package(
                get_json_artifact_data(manifest_dir / MANIFEST_FILE_NAME)[
                    "nodes"
                ].values(),
                include_packages=filter_conditions.include_packages,
                exclude_packages=filter_conditions.exclude_packages,
            ),
            include_tags=filter_conditions.include_tags,
            exclude_tags=filter_conditions.exclude_tags,
        ),
        include_paths=filter_conditions.include_node_paths,
        exclude_paths=filter_conditions.exclude_node_paths,
    )


def get_models_from_manifest(
    manifest_dir: Path, filter_conditions: ManifestFilterConditions
) -> Generator[dict[str, Any], None, None]:
    """Get model nodes from the dbt manifest file.

    Args:
        manifest_dir: Path to the directory containing the dbt manifest.json
        filter_conditions: ManifestFilterConditions object to filter by

    Yields:
        model dictionaries
    """
    return filter_models_by_materialization_type(
        filter_nodes_by_resource_type(
            get_nodes_from_manifest(
                manifest_dir=manifest_dir,
                filter_conditions=filter_conditions,
            ),
            include_resource_types=["model"],
        ),
        include_materializations=filter_conditions.include_materializations,
        exclude_materializations=filter_conditions.exclude_materializations,
    )
