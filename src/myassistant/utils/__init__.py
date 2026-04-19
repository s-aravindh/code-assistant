"""Utility functions."""

from myassistant.utils.logger import create_logger
from myassistant.utils.slash_commands import SlashCommandHandler
from myassistant.utils.cost import (
    format_cost_display,
)


def safe_str(value, max_len: int | None = None) -> str:
    """Safely convert any value to a string.

    Args:
        value: The value to convert.
        max_len (int | None): Optional max length; truncates with '...' if exceeded.

    Returns:
        str: String representation, or '' if value is None.
    """
    if value is None:
        return ""
    try:
        s = repr(value) if isinstance(value, (dict, list, tuple)) else str(value)
        return s[:max_len] + "..." if max_len and len(s) > max_len else s
    except Exception:
        return "<error>"


__all__ = [
    "create_logger",
    "SlashCommandHandler",
    "format_cost_display",
    "safe_str",
]
