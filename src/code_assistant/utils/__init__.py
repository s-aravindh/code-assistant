"""Utility functions."""

from code_assistant.utils.diff import generate_diff, format_diff_rich, format_file_change
from code_assistant.utils.logger import create_logger
from code_assistant.utils.slash_commands import SlashCommandHandler
from code_assistant.utils.cost import (
    calculate_cost,
    calculate_session_cost,
    format_cost,
    format_cost_display,
    get_pricing,
    is_free_model,
)

__all__ = [
    "generate_diff",
    "format_diff_rich",
    "format_file_change",
    "create_logger",
    "SlashCommandHandler",
    "calculate_cost",
    "calculate_session_cost",
    "format_cost",
    "format_cost_display",
    "get_pricing",
    "is_free_model",
]
