"""Abstract Base Classes for checks."""

import logging
from abc import ABC, abstractmethod
from argparse import Namespace
from typing import Collection

from utils.check_arg_parser import CheckArgParser
from utils.artifact_data import ManifestFilterConditions
from utils.console_formatting import (
    check_status_header,
    colour_message,
    ConsoleEmphasis,
)


class Check(ABC):
    """Abstract base class for generic checks.

    Attributes:
        args: check arguments
    """

    def __init__(self) -> None:
        """Initialise and call the instance."""
        self.args: Namespace = self.parse_args()
        self()

    def parse_args(self) -> Namespace:
        """Parse command line arguments."""
        return CheckArgParser(
            program_name=self.check_name,
            additional_arguments=self.additional_arguments,
        ).parse_args()

    @property
    @abstractmethod
    def check_name(self) -> str:
        """Name of the check."""
        ...

    @property
    @abstractmethod
    def additional_arguments(self) -> list[str]:
        """Arguments required in addition to the global arguments."""
        ...

    @property
    def filter_conditions(self) -> ManifestFilterConditions:
        """Filter conditions for filtering objects from the manifest."""
        return ManifestFilterConditions(
            include_materializations=getattr(
                self.args, "include_materializations", None
            ),
            include_tags=getattr(self.args, "include_tags", None),
            include_packages=getattr(self.args, "include_packages", None),
            include_node_paths=getattr(self.args, "include_node_paths", None),
            exclude_materializations=getattr(
                self.args, "exclude_materializations", None
            ),
            exclude_tags=getattr(self.args, "exclude_tags", None),
            exclude_packages=getattr(self.args, "exclude_packages", None),
            exclude_node_paths=getattr(self.args, "exclude_node_paths", None),
        )

    @abstractmethod
    def perform_check(self) -> None:
        """Execute the check logic."""
        ...

    @property
    @abstractmethod
    def failure_message(self) -> str:
        """Compile a failure log message."""
        ...

    @property
    @abstractmethod
    def has_failures(self) -> bool:
        """Determine whether any entities failed the check."""
        ...

    def __call__(self) -> None:
        """Run the check end-to-end.

        Raises:
             SystemExit with the result of the check
        """
        logging.info(
            f"""{
                colour_message(
                    f"Performing check: {self.check_name}",
                    emphasis=ConsoleEmphasis.BOLD,
                )
            }\n\n{self.filter_conditions.summary}\n"""
        )
        self.perform_check()
        if self.has_failures:
            raise SystemExit(
                f"{check_status_header(f'{self.check_name}: FAIL', False)}\n\n{self.failure_message}\n\n{80 * '_'}\n"
            )
        logging.info(
            f"{check_status_header(f'{self.check_name}: PASS', True)}\n\n{80 * '_'}\n"
        )
        raise SystemExit(0)


class ManifestCheck(Check, ABC):
    """Abstract base class for manifest-based checks.

    Attributes:
        failures: Collection of check failure items
    """

    failures: Collection = ()

    @property
    def has_failures(self) -> bool:
        """Determine whether any entities failed the check."""
        return bool(self.failures)


class ManifestVsCatalogComparison(Check, ABC):
    """Abstract base class for manifest vs. catalog comparison checks.

    Attributes:
        manifest_items: Collection of manifest items for comparison
        catalog_items: Collection of catalog items for comparison
    """

    manifest_items: set[str] | dict[str, str]
    catalog_items: set[str] | dict[str, str]

    @property
    def has_failures(self) -> bool:
        """Determine whether any entities failed the check."""
        return bool(self.manifest_items != self.catalog_items)
