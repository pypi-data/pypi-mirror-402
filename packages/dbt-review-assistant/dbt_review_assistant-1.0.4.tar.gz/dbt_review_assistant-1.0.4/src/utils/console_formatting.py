"""Utilities for console message formatting."""

from enum import Enum


class ConsoleTextColour(Enum):
    """Standard ANSII colour codes for console output text colour."""

    BRIGHT_WHITE = "\033[97m"
    WHITE = "\033[37m"
    BRIGHT_MAGENTA = "\033[95m"
    MAGENTA = "\033[35m"
    BRIGHT_BLUE = "\033[94m"
    BLUE = "\033[34m"
    BRIGHT_CYAN = "\033[96m"
    CYAN = "\033[36m"
    BRIGHT_GREEN = "\033[92m"
    GREEN = "\033[32m"
    BRIGHT_YELLOW = "\033[93m"
    YELLOW = "\033[33m"
    BRIGHT_RED = "\033[91m"
    RED = "\033[31m"
    BRIGHT_BLACK = "\033[90m"
    BLACK = "\033[30m"
    BRIGHT_DEFAULT = "\033[99m"
    DEFAULT = "\033[39m"


class ConsoleBackgroundColour(Enum):
    """Standard ANSII colour codes for console output background colour."""

    BRIGHT_WHITE = "\033[107m"
    WHITE = "\033[47m"
    BRIGHT_MAGENTA = "\033[105m"
    MAGENTA = "\033[45m"
    BRIGHT_BLUE = "\033[104m"
    BLUE = "\033[46m"
    BRIGHT_CYAN = "\033[106m"
    CYAN = "\033[46m"
    BRIGHT_GREEN = "\033[102m"
    GREEN = "\033[42m"
    BRIGHT_YELLOW = "\033[103m"
    YELLOW = "\033[43m"
    BRIGHT_RED = "\033[101m"
    RED = "\033[41m"
    BRIGHT_BLACK = "\033[100m"
    BLACK = "\033[40m"
    BRIGHT_DEFAULT = "\033[109m"
    DEFAULT = "\033[49m"
    CROSSED = "\033[9m"
    NEGATIVE = "\033[7m"


class ConsoleEmphasis(Enum):
    """Standard ANSII emphasis type codes for console output text emphasis."""

    BOLD = "\033[1m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    FAINT = "\033[2m"
    NEGATIVE = "\033[7m"
    ENDC = "\033[0m"


# Code to reset text to default
ENDC = "\033[0m"


def colour_message(
    msg: str,
    text_colour: ConsoleTextColour = ConsoleTextColour.DEFAULT,
    background_colour: ConsoleBackgroundColour = ConsoleBackgroundColour.DEFAULT,
    emphasis: ConsoleEmphasis = ConsoleEmphasis.ENDC,
) -> str:
    """Format a string with a given colour.

    Args:
        msg: string message to be formatted.
        text_colour: text colour to apply
        background_colour: background colour to apply
        emphasis: emphasis type to apply to text

    Returns:
        string formatted with given colour and emphasis
    """
    return emphasis.value + text_colour.value + background_colour.value + msg + ENDC


def check_status_header(message: str, status: bool) -> str:
    """Compile a header string to display check status.

    Args:
        message: message to display
        status: whether the check passed or failed

    Returns:
        message formatted for emphasis, with the appropriate colours
    """
    coloured_message = colour_message(
        message,
        ConsoleTextColour.WHITE if status else ConsoleTextColour.BLACK,
        ConsoleBackgroundColour.GREEN if status else ConsoleBackgroundColour.RED,
        ConsoleEmphasis.BOLD,
    )
    return f"{coloured_message}"
