import logging
import sys
from argparse import Namespace
from contextlib import nullcontext
from pathlib import Path
import re
from unittest.mock import patch, Mock

import pytest

from checks.entrypoint import (
    run_check,
    entrypoint,
    parse_cli_entrypoint_args,
    UnknownCheck,
)
from utils.console_formatting import check_status_header


@pytest.mark.parametrize(
    ids=[
        "unknown check",
        "check passes",
        "check fails",
    ],
    argnames=["arguments", "side_effect", "expected_result"],
    argvalues=[
        (
            [
                "not-a-real-check-id",
                "--project-dir",
                "path/to/project",
            ],
            None,
            pytest.raises(UnknownCheck, match="Unknown check not-a-real-check-id"),
        ),
        (
            [
                "test-check",
                "--project-dir",
                "path/to/project",
            ],
            SystemExit(0),
            nullcontext(True),
        ),
        (
            [
                "test-check",
                "--project-dir",
                "path/to/project",
            ],
            SystemExit("test error"),
            nullcontext(False),
        ),
    ],
)
def test_run_check(
    arguments: list[str], side_effect: SystemExit | None, expected_result
):
    mock_check = Mock(side_effect=side_effect)
    with (
        expected_result as e,
        patch("checks.entrypoint.ALL_CHECKS_MAP", {"test-check": mock_check}),
        patch.object(logging, "error") as mock_logging_error,
    ):
        assert e == run_check(arguments)
        mock_check.assert_called()
        if not e and side_effect:
            mock_logging_error.assert_called_with(side_effect.code)
        assert sys.argv == arguments


@pytest.mark.parametrize(
    ids=[
        "check with config_dir",
        "check without config_dir",
        "check with extra args",
    ],
    argnames=["arguments", "expected_result"],
    argvalues=[
        (
            [
                "test",
                "models-have-descriptions",
                "--config-dir",
                "path/to/project",
            ],
            (
                Namespace(
                    check_id="models-have-descriptions",
                    config_dir=Path("path/to/project"),
                ),
                [],
            ),
        ),
        (
            [
                "test",
                "models-have-descriptions",
            ],
            (
                Namespace(
                    check_id="models-have-descriptions",
                    config_dir=None,
                ),
                [],
            ),
        ),
        (
            [
                "test",
                "models-have-constraints",
                "--config-dir",
                "path/to/project",
                "--constraints",
                "primary_key",
            ],
            (
                Namespace(
                    check_id="models-have-constraints",
                    config_dir=Path("path/to/project"),
                ),
                [
                    "--constraints",
                    "primary_key",
                ],
            ),
        ),
    ],
)
def test_parse_cli_entrypoint_args(
    arguments: list[str], expected_result: tuple[Namespace, list[str]]
):
    with patch.object(sys, "argv", arguments):
        assert parse_cli_entrypoint_args() == expected_result


@pytest.mark.parametrize(
    ids=[
        "one pass, one fail",
        "two fail",
        "two pass",
        "one pass",
        "one fail",
    ],
    argnames=["arguments", "checks", "config_data", "expected_result"],
    argvalues=[
        (
            ["test", "all-checks", "-c", "."],
            {
                "all-models-have-descriptions": True,
                "all-models-have-constraints": False,
            },
            {
                "per_check_arguments": [
                    {"check_id": "all-models-have-descriptions"},
                    {"check_id": "all-models-have-constraints"},
                ]
            },
            pytest.raises(
                SystemExit,
                match=re.escape(check_status_header("1/2 checks failed", False)),
            ),
        ),
        (
            ["test", "all-checks", "-c", "."],
            {
                "all-models-have-descriptions": False,
                "all-models-have-constraints": False,
            },
            {
                "per_check_arguments": [
                    {"check_id": "all-models-have-descriptions"},
                    {"check_id": "all-models-have-constraints"},
                ]
            },
            pytest.raises(
                SystemExit,
                match=re.escape(check_status_header("2/2 checks failed", False)),
            ),
        ),
        (
            ["test", "all-checks", "-c", "."],
            {
                "all-models-have-descriptions": True,
                "all-models-have-constraints": True,
            },
            {
                "per_check_arguments": [
                    {"check_id": "all-models-have-descriptions"},
                    {"check_id": "all-models-have-constraints"},
                ]
            },
            pytest.raises(
                SystemExit,
                match="0",
            ),
        ),
        (
            ["test", "all-checks", "-c", "."],
            {
                "all-models-have-descriptions": True,
            },
            {
                "per_check_arguments": [
                    {"check_id": "all-models-have-descriptions"},
                ]
            },
            pytest.raises(
                SystemExit,
                match="0",
            ),
        ),
        (
            ["test", "all-checks", "-c", "."],
            {
                "all-models-have-descriptions": False,
            },
            {
                "per_check_arguments": [
                    {"check_id": "all-models-have-descriptions"},
                ]
            },
            pytest.raises(
                SystemExit,
                match=re.escape(check_status_header("1/1 checks failed", False)),
            ),
        ),
    ],
)
def test_entrypoint(
    arguments,
    checks,
    config_data,
    expected_result,
):
    def mock_run_check(check_arguments: list[str]) -> bool:
        return checks[check_arguments[0]]

    with (
        expected_result,
        patch.object(sys, "argv", arguments),
        patch("checks.entrypoint.run_check", mock_run_check),
        patch("checks.entrypoint.load_config", return_value=config_data),
    ):
        entrypoint()
