"""Check configuration utilities."""

import logging
from argparse import Namespace
from pathlib import Path
from typing import Any

import yaml
from jsonschema import validate

CONFIG_YAML_SCHEMA = """
type: object
properties:
    global_arguments:
        type: object
        additionalProperties: false
        properties:
            arguments:
                type: array
        
    per_check_arguments:
        type: array
        items:
            type: object
            required: ["check_id"]
            additionalProperties: false
            properties:
                check_id:
                    type: string
                arguments:
                    type: array
                    items:
                        type: string
                description:
                    type: string
"""

PROJECT_NAME = "dbt-review-assistant"


def load_config(config_dir: Path) -> dict[str, Any]:
    """Load configuration data from the YAML file.

    Args:
        config_dir: Path to the directory where the configuration file is located

    Returns:
        a dictionary of configuration data

    Raises:
        FileNotFoundError: if an unknown hook is called,
    """
    file_path = config_dir / f".{PROJECT_NAME}.yaml"
    if not file_path.is_file():
        raise FileNotFoundError(f"{file_path} not found.")
    with open(file_path) as f:
        loader = yaml.SafeLoader
        config_data = yaml.load(f, Loader=loader)
        validate(config_data, yaml.load(CONFIG_YAML_SCHEMA, Loader=loader))
    return config_data


def configure_checks(
    config_data: dict | None, known_args: Namespace, extra_args: list[str]
) -> list[list[str]]:
    """Configure checks using CLI arguments or the config file data, if found.

    Args:
        config_data: Optional, configuration data from the config file.
            Defaults to None
        known_args: CLI arguments from the main entrypoint command
        extra_args: CLI arguments not parsed by the main entrypoint command

    Returns:
        list of check arguments to be run
    """
    if config_data:
        if extra_args:
            logging.warning(
                f"Check configuration will be read from"
                f" {known_args.config_dir.absolute() / f'.{PROJECT_NAME}.yaml'},"
                f" therefore the following extra CLI arguments will be ignored: {extra_args}"
            )
        global_options = config_data.get("global_arguments", {}).get("arguments", [])
        check_instances: list[list[str]] = [
            # Allow per-check options to override the global options
            [check_instance["check_id"]]
            + global_options
            + check_instance.get("arguments", [])
            for check_instance in config_data.get("per_check_arguments", [])
            if check_instance["check_id"] == known_args.check_id
            or known_args.check_id == "all-checks"
        ]
        # if check instance not found in config, run it without any arguments
        if not check_instances:
            logging.warning(
                f"Check '{known_args.check_id}' not found in "
                f"{known_args.config_dir.absolute() / f'.{PROJECT_NAME}.yaml'}.\n"
                "Running without arguments..."
            )
            check_instances = [[known_args.check_id]]
    elif known_args.check_id == "all-checks" and not config_data:
        raise RuntimeError("Check id 'all-checks' requires a config file.")
    else:
        # Get the config from the CLI args if no config provided
        check_instances = [[known_args.check_id] + extra_args]
    return check_instances
