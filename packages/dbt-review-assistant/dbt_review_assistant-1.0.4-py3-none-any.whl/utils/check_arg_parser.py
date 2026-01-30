"""Argument parsing utilities."""

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence, Type, Any, Callable


class RequiredArgumentMissing(Exception):
    """Exception raised when a required argument is missing."""

    pass


@dataclass
class CliArgument:
    """A Command Line Interface argument.

    Attributes:
        name: Name of the argument
        help: Description of the argument
        type: Type of the argument
        required: Whether the argument is required
        nargs: How to handle multiple values
        default: Default value
    """

    name: str
    help: str
    type: Type | Callable
    required: bool = False
    nargs: str | None = None
    default: Any | None = None

    @property
    def cli_name(self) -> str:
        """Name of the CLI argument."""
        return f"--{self.name.replace('_', '-')}"


UNIVERSAL_ARGUMENTS: tuple[CliArgument, ...] = (
    CliArgument(
        name="project_dir",
        help="Path to the dbt project directory where the dbt_project.yml file is located."
        "Defaults to the current directory.",
        type=Path,
    ),
    CliArgument(
        name="manifest_dir",
        help="Path to the directory containing the dbt manifest.yml file."
        "Defaults to the the 'target' directory underneath the dbt project path.",
        type=Path,
    ),
    CliArgument(
        name="catalog_dir",
        help="Path to the directory containing the dbt catalog.yml file."
        "Defaults to the the 'target' directory underneath the dbt project path.",
        type=Path,
    ),
)
ADDITIONAL_ARGUMENTS: tuple[CliArgument, ...] = (
    CliArgument(
        name="must_have_all_constraints_from",
        help="List of constraint names, from which objects must have all values.",
        type=str,
        nargs="+",
        required=False,
        default=None,
    ),
    CliArgument(
        name="must_have_any_constraint_from",
        help="List of constraint names, from which objects must have at least one value.",
        type=str,
        nargs="+",
        required=False,
        default=None,
    ),
    CliArgument(
        name="must_have_all_data_tests_from",
        help="List of data test names, from which objects must have all values.",
        type=str,
        nargs="+",
        required=False,
        default=None,
    ),
    CliArgument(
        name="must_have_any_data_test_from",
        help="List of data test names, from which objects must have at least one value.",
        type=str,
        nargs="+",
        required=False,
        default=None,
    ),
    CliArgument(
        name="must_have_all_tags_from",
        help="List of tags, from which objects must have all values.",
        type=str,
        nargs="+",
        required=False,
        default=None,
    ),
    CliArgument(
        name="must_have_any_tag_from",
        help="List of values, from which objects must at least one value.",
        type=str,
        nargs="+",
        required=False,
        default=None,
    ),
    CliArgument(
        name="include_materializations",
        help="List of materialization types to include. Models with other materialization types will be ignored.",
        type=str,
        nargs="+",
        required=False,
        default=None,
    ),
    CliArgument(
        name="include_packages",
        help="List of packages to include. Nodes not in these packages will be ignored.",
        type=str,
        nargs="+",
        required=False,
        default=None,
    ),
    CliArgument(
        name="include_tags",
        help="List of tags to include. Nodes that do not have at least one of these tags will be ignored.",
        type=str,
        nargs="+",
        required=False,
        default=None,
    ),
    CliArgument(
        name="exclude_materializations",
        help="List of materialization types to exclude. Models with these materialization types will be ignored."
        " Supersedes the 'include_materializations' argument.",
        type=str,
        nargs="+",
        required=False,
        default=None,
    ),
    CliArgument(
        name="exclude_packages",
        help="List of packages to exclude. Nodes in these packages will be ignored."
        " Supersedes the 'include_packages' argument.",
        type=str,
        nargs="+",
        required=False,
        default=None,
    ),
    CliArgument(
        name="exclude_tags",
        help="List of tags to exclude. Nodes that have any of these tags will be ignored."
        " Supersedes the 'include_tags' argument.",
        type=str,
        nargs="+",
        required=False,
        default=None,
    ),
    CliArgument(
        name="include_node_paths",
        help="List of node paths to include. Nodes not under one of these paths will be ignored.",
        type=Path,
        nargs="+",
        required=False,
        default=None,
    ),
    CliArgument(
        name="exclude_node_paths",
        help="List of node paths to exclude. Nodes under one of these paths will be ignored.",
        type=Path,
        nargs="+",
        required=False,
        default=None,
    ),
)
ARGUMENTS_DICT = {arg.name: arg for arg in UNIVERSAL_ARGUMENTS + ADDITIONAL_ARGUMENTS}


@dataclass
class CheckArgParser:
    """Argument parser for checks.

    Attributes:
        program_name: Name of the check
        additional_arguments: Additional arguments,
            on top of the standard global arguments
        parser: an argparse.ArgumentParser instance
    """

    program_name: str
    additional_arguments: Sequence[str] = field(default_factory=list)
    parser: argparse.ArgumentParser = field(init=False)

    def __post_init__(self) -> None:
        """Post initialization."""
        self.parser = argparse.ArgumentParser(prog=self.program_name)
        self.add_arguments()

    def add_arguments(self) -> None:
        """Add arguments to the parser."""
        arguments = list(UNIVERSAL_ARGUMENTS) + [
            ARGUMENTS_DICT[additional_argument]
            for additional_argument in self.additional_arguments
        ]
        for argument in arguments:
            self.parser.add_argument(
                argument.cli_name,
                type=argument.type,
                help=argument.help,
                nargs=argument.nargs,
                required=argument.required,
                default=argument.default,
            )

    def parse_args(self) -> argparse.Namespace:
        """Parse CLI arguments.

        Returns:
            an argparse.Namespace instance
        """
        args = self.parser.parse_args(sys.argv[1:])
        if not getattr(args, "project_dir"):
            args.project_dir = Path.cwd()
        if not getattr(args, "manifest_dir"):
            args.manifest_dir = args.project_dir / "target"
        if not getattr(args, "catalog_dir"):
            args.catalog_dir = args.manifest_dir
        return args
