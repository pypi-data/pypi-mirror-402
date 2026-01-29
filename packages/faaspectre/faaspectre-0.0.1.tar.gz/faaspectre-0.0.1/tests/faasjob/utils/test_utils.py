"""Tests for utility functions."""

import pytest
from datetime import datetime, timezone

from faaspectre.utils.datetime_utils import to_iso8601_utc
from faaspectre.utils.error_formatter import format_error_summary


class TestDateTimeUtils:
    """Tests for datetime utilities."""

    def test_to_iso8601_utc_naive_datetime(self):
        """Test conversion of naive datetime (assumed UTC)."""
        dt = datetime(2026, 1, 16, 10, 30, 0)
        result = to_iso8601_utc(dt)
        assert result == "2026-01-16T10:30:00Z"

    def test_to_iso8601_utc_with_timezone(self):
        """Test conversion of datetime with timezone."""
        dt = datetime(2026, 1, 16, 10, 30, 0, tzinfo=timezone.utc)
        result = to_iso8601_utc(dt)
        assert result == "2026-01-16T10:30:00Z"

    def test_to_iso8601_utc_converts_to_utc(self):
        """Test conversion of non-UTC datetime to UTC."""
        # Create datetime with offset
        from datetime import timedelta
        tz = timezone(timedelta(hours=5))
        dt = datetime(2026, 1, 16, 10, 30, 0, tzinfo=tz)
        result = to_iso8601_utc(dt)
        # Should convert to UTC (5 hours earlier)
        assert result.endswith("Z")
        assert "2026-01-16T05:30:00Z" == result


class TestErrorFormatter:
    """Tests for error formatting utilities."""

    def test_format_error_summary(self):
        """Test formatting of exception."""
        exception = ValueError("Test error message")
        result = format_error_summary(exception)
        assert "ValueError" in result
        assert "Test error message" in result

    def test_format_error_summary_truncates_long_messages(self):
        """Test truncation of long error messages."""
        long_message = "A" * 1000
        exception = ValueError(long_message)
        result = format_error_summary(exception, max_length=100)
        assert len(result) <= 100
        assert result.endswith("...")

    def test_format_error_summary_with_custom_max_length(self):
        """Test custom max_length parameter."""
        exception = ValueError("Short message")
        result = format_error_summary(exception, max_length=20)
        assert len(result) <= 20
