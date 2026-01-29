"""Tests for domain validators."""

import pytest
from faaspectre.domain.validators import (
    validate_uuid_v4,
    validate_iso8601_utc,
    validate_time_ordering,
)


class TestUUIDValidation:
    """Tests for UUID-v4 validation."""

    def test_valid_uuid_v4(self):
        """Test valid UUID-v4 format."""
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        assert validate_uuid_v4(valid_uuid) is True

    def test_invalid_uuid_format(self):
        """Test invalid UUID format."""
        assert validate_uuid_v4("not-a-uuid") is False
        assert validate_uuid_v4("12345") is False
        assert validate_uuid_v4("") is False

    def test_uuid_v3_not_valid(self):
        """Test that UUID-v3 is not valid (must be v4)."""
        uuid_v3 = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
        assert validate_uuid_v4(uuid_v3) is False


class TestISO8601Validation:
    """Tests for ISO 8601 UTC validation."""

    def test_valid_iso8601_utc_with_z(self):
        """Test valid ISO 8601 UTC with Z suffix."""
        assert validate_iso8601_utc("2026-01-16T10:30:00Z") is True

    def test_valid_iso8601_utc_with_offset(self):
        """Test valid ISO 8601 UTC with +00:00 offset."""
        assert validate_iso8601_utc("2026-01-16T10:30:00+00:00") is True

    def test_invalid_iso8601_missing_time(self):
        """Test invalid ISO 8601 (missing time component)."""
        assert validate_iso8601_utc("2026-01-16") is False

    def test_invalid_iso8601_not_utc(self):
        """Test invalid ISO 8601 (not UTC)."""
        assert validate_iso8601_utc("2026-01-16T10:30:00+05:00") is False

    def test_invalid_format(self):
        """Test invalid format."""
        assert validate_iso8601_utc("not-a-date") is False
        assert validate_iso8601_utc("") is False


class TestTimeOrderingValidation:
    """Tests for time ordering validation."""

    def test_valid_time_ordering(self):
        """Test valid time ordering (end >= start)."""
        assert validate_time_ordering(1000.0, 2000.0) is True
        assert validate_time_ordering(1000.0, 1000.0) is True  # Equal is valid

    def test_invalid_time_ordering(self):
        """Test invalid time ordering (end < start)."""
        assert validate_time_ordering(1000.0, 500.0) is False

    def test_none_end_time(self):
        """Test None end_time is valid."""
        assert validate_time_ordering(1000.0, None) is True
