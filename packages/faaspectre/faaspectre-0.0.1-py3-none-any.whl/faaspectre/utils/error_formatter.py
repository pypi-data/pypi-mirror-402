"""Error formatting utilities."""

import traceback
from typing import Optional


def format_error_summary(exception: Exception, max_length: int = 500) -> str:
    """Extract and format exception details as error summary.

    Args:
        exception: Exception to format
        max_length: Maximum length of error summary (default: 500)

    Returns:
        Formatted error summary string
    """
    error_type = type(exception).__name__
    error_message = str(exception)

    # Create summary: "ErrorType: error message"
    summary = f"{error_type}: {error_message}"

    # Truncate if too long
    if len(summary) > max_length:
        summary = summary[: max_length - 3] + "..."

    return summary
