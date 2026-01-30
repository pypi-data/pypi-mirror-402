"""Entrypoint for the CLI."""

import argparse
import logging
import sys
from argparse import Namespace
from pathlib import Path

from checks import ALL_CHECKS_MAP
from utils.config import load_config, configure_checks
from utils.console_formatting import (
    check_status_header,
)


class UnknownCheck(Exception):
    """Exception raised when an unknown check is found."""

    pass


def run_check(arguments: list[str]) -> bool:
    """Run a check script.

    Args:
        arguments: list script arguments

    Returns:
        check result as a boolean

    Raises:
        UnknownCheck: if check_id is not recognised
        SystemExit: with the result of the check
    """
    check_id = arguments[0]
    sys.argv = arguments
    try:
        check = ALL_CHECKS_MAP[check_id]
    except KeyError:
        raise UnknownCheck(f"Unknown check {check_id}")
    try:
        check()
        return True
    except SystemExit as e:
        if e.code == 0:
            return True
        logging.error(e.code)
        return False


def parse_cli_entrypoint_args() -> tuple[Namespace, list[str]]:
    """Parse CLI arguments for the entrypoint script.

    This argument parser only accepts 'check_id' and 'config_dir'.
    Additional arguments are returned as a list for individual hooks
    to use, unless check_id=='all', in which case they are ignored.

    Returns:
        Namespace of parsed CLI arguments and list of additional arguments
    """
    valid_check_ids = list(ALL_CHECKS_MAP.keys())
    parser = argparse.ArgumentParser(
        prog="dbt-review-assistant",
        description="Please choose a check to run, or input 'all-checks' to run every check specified in the config file.",
    )
    parser.add_argument(
        dest="check_id",
        help="name of the check to execute",
        choices=valid_check_ids + ["all-checks"],
    )
    parser.add_argument(
        "-c",
        "--config-dir",
        dest="config_dir",
        help="Path to the directory where the config file is located.",
        type=Path,
    )
    return parser.parse_known_args(sys.argv[1:])


def entrypoint() -> None:
    """Entrypoint for the CLI.

    Determines which checks to run and how they are configured.

    Raises:
        SystemExit: with the overall status of all checks
    """
    known_args, extra_args = parse_cli_entrypoint_args()
    logging.basicConfig(format="%(message)s", level=logging.INFO)
    config_data = load_config(known_args.config_dir) if known_args.config_dir else None
    all_check_arguments = configure_checks(
        config_data=config_data, known_args=known_args, extra_args=extra_args
    )
    failed_hooks = sum(
        0 if run_check(check_arguments) else 1
        for check_arguments in all_check_arguments
    )
    if failed_hooks:
        raise SystemExit(
            check_status_header(
                f"{failed_hooks}/{len(all_check_arguments)} checks failed",
                False,
            )
        )
    logging.info(
        check_status_header(
            f"{len(all_check_arguments)}/{len(all_check_arguments)} checks passed", True
        )
    )
    raise SystemExit(0)


if __name__ == "__main__":
    entrypoint()
