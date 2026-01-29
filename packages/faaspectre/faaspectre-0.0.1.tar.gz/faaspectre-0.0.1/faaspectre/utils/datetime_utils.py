"""DateTime utility functions."""

from datetime import datetime, timezone


def to_iso8601_utc(dt: datetime) -> str:
    """Convert datetime to UTC ISO 8601 string.

    Args:
        dt: Datetime object (assumed to be UTC or will be converted)

    Returns:
        ISO 8601 UTC string (e.g., "2026-01-16T10:30:00Z")
    """
    # Ensure UTC timezone
    if dt.tzinfo is None:
        # Assume naive datetime is UTC
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        # Convert to UTC
        dt = dt.astimezone(timezone.utc)

    # Format as ISO 8601 with Z suffix
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
