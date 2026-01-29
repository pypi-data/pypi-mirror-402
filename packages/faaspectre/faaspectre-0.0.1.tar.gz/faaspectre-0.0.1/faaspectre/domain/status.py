"""Pipeline status enumeration."""

from enum import Enum


class PipelineStatus(str, Enum):
    """Pipeline execution status values."""

    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
