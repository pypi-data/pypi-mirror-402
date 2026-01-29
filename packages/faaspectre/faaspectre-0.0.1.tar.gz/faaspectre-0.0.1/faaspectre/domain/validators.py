"""Reusable validation functions for domain models."""

import re
from typing import Optional
from datetime import datetime

from .exceptions import ValidationError


def validate_uuid_v4(value: str) -> bool:
    """Validate UUID-v4 format.

    Args:
        value: String to validate

    Returns:
        True if valid UUID-v4 format, False otherwise
    """
    uuid_v4_pattern = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
        re.IGNORECASE,
    )
    return bool(uuid_v4_pattern.match(value))


def validate_iso8601_utc(value: str) -> bool:
    """Validate ISO 8601 UTC format.

    Args:
        value: String to validate

    Returns:
        True if valid ISO 8601 UTC format, False otherwise
    """
    try:
        # Try parsing as ISO 8601
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        # Check if it's UTC (ends with Z or +00:00)
        return value.endswith("Z") or value.endswith("+00:00")
    except (ValueError, AttributeError):
        return False


def validate_time_ordering(start: float, end: Optional[float]) -> bool:
    """Validate time ordering (end >= start).

    Args:
        start: Start time epoch
        end: Optional end time epoch

    Returns:
        True if valid ordering (end >= start or end is None), False otherwise
    """
    if end is None:
        return True
    return end >= start


def raise_validation_error(message: str, correlation_id: str = None, job_id: str = None):
    """Raise ValidationError with message.

    Args:
        message: Error message
        correlation_id: Optional correlation ID
        job_id: Optional job ID

    Raises:
        ValidationError: Always raises
    """
    raise ValidationError(message, correlation_id=correlation_id, job_id=job_id)
